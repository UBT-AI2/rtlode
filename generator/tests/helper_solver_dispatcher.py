import random
import unittest
from typing import List, Dict, Union

from myhdl import block, Signal, ResetSignal, instances, always, delay, StopSimulation, instance

from framework import data_desc
from framework.fifo import FifoProducer, FifoConsumer, fifo
from framework.packed_struct import BitVector
from generator.cdc_utils import AsyncFifoProducer, AsyncFifoConsumer, async_fifo
from generator.config import Config
from generator.dispatcher import dispatcher
from generator.solver import solver
from utils import num


class SolverDispatcherHelper(unittest.TestCase):
    def run(self, result=None):
        # Run each test for every relevant number type
        previous_type = num.get_default_type()
        for num_type in [
            num.SignedFixedNumberType(37, 16),
            num.FloatingNumberType(num.FloatingPrecision.SINGLE),
            num.FloatingNumberType(num.FloatingPrecision.DOUBLE)
        ]:
            num.set_default_type(num_type)
            random.seed(0)
            super().run(result)
        num.set_default_type(previous_type)

    def check_output(self, data: Dict, reference_data: Union[Dict, List], data_counter):
        """
        Test function to check if data in inside the specification provided by reference_data.
        :param data: data package to check
        :param reference_data: reference data given as a list or dict. If a list is given the order of the output
        packages is checked against the order of the list. If a dict is given the order is not checked.
        :param data_counter: index of current output data package
        :return:
        """
        if isinstance(reference_data, list):
            self.assertEqual(reference_data[data_counter]['id'], data['id'])
            ref_package = reference_data[data_counter]
        elif isinstance(reference_data, dict):
            data_id = int(data['id'])
            self.assertIn(data_id, reference_data.keys())
            ref_package = reference_data[data_id]
            self.assertNotIn('_received', ref_package)
            ref_package['_received'] = True
        else:
            raise ValueError('Parameter output_data of incompatible type.')
        self.assertAlmostEqual(ref_package['x'], data['x'], places=2)
        if 'y' in ref_package:
            for i in range(len(data['y'])):
                self.assertAlmostEqual(ref_package['y'][i], data['y'][i], places=2)

    def run_solver(
            self,
            config_dict: Dict,
            input_data: List[Dict],
            output_data: Union[Dict, List],
            wr_pattern: List[int] = None,
            rd_pattern: List[int] = None):
        """
        Helper function to run tests against a solver unit. Numeric configuration is not used! Instead of that execute
        each test with a different default type set.
        If 'nbr_solver' is provided in the config a dispatcher with the given number of solver units is used. If not,
        one solver unit is directly used as dut.
        :param config_dict: build configuration as dict
        :param input_data: list containing the data packages as dicts to be inputted
        :param output_data: Can either be a list or dictionary with the ids as the keys. If a list is given the order of
        the output packages is checked against the order of the list. If a dict is given the order is not checked.
        :param wr_pattern: pattern to drive the wr signal, starting with false
        :param rd_pattern: pattern to drive the rd signal, starting with false
        """
        if wr_pattern is None or len(wr_pattern) < 1:
            wr_pattern = [20, 1]
        if rd_pattern is None or len(rd_pattern) < 1:
            rd_pattern = [30, 1]

        use_dispatcher = 'nbr_solver' in config_dict

        config = Config.from_dict(config_dict)

        @block
        def testbench():
            clk = Signal(bool(0))
            rst = ResetSignal(False, True, False)

            in_desc = data_desc.get_input_desc(config.system_size)
            in_desc_vec = BitVector(len(in_desc))

            out_desc_vec = BitVector(len(data_desc.get_output_desc(config.system_size)))

            if use_dispatcher:
                in_fifo_p = AsyncFifoProducer(clk=clk, rst=rst, data=in_desc_vec.create_instance())
                in_fifo_c = AsyncFifoConsumer(clk=clk, rst=rst, data=in_desc_vec.create_instance())
                in_fifo = async_fifo(in_fifo_p, in_fifo_c, buffer_size_bits=2)

                out_fifo_p = AsyncFifoProducer(clk=clk, rst=rst, data=out_desc_vec.create_instance())
                out_fifo_c = AsyncFifoConsumer(clk=clk, rst=rst, data=out_desc_vec.create_instance())
                out_fifo = async_fifo(out_fifo_p, out_fifo_c, buffer_size_bits=2)

                dut = dispatcher(config, data_in=in_fifo_c, data_out=out_fifo_p)
            else:
                in_fifo_p = FifoProducer(in_desc_vec.create_instance())
                in_fifo_c = FifoConsumer(in_desc_vec.create_instance())
                in_fifo = fifo(clk, rst, in_fifo_p, in_fifo_c, buffer_size_bits=2)

                out_fifo_p = FifoProducer(out_desc_vec.create_instance())
                out_fifo_c = FifoConsumer(out_desc_vec.create_instance())
                out_fifo = fifo(clk, rst, out_fifo_p, out_fifo_c, buffer_size_bits=2)

                dut = solver(config, clk, rst, data_in=in_fifo_c, data_out=out_fifo_p)

            parsed_out_data = data_desc.get_output_desc(config.system_size).create_read_instance(out_fifo_c.data)
            parsed_out_data_inst = parsed_out_data.instances()

            @always(delay(10))
            def clk_driver():
                clk.next = not clk

            @instance
            def reset_handler():
                rst.next = True
                yield delay(200)
                rst.next = False

            in_counter = Signal(num.UnsignedIntegerNumberType(32).create(1))

            in_fifo_p.data.next = in_desc.create_constant(input_data[0])
            in_fifo_p.data._update()

            in_finished = Signal(bool(0))

            in_counter = 0

            @always(clk.posedge)
            def input_driver():
                if not rst:
                    if in_fifo_p.wr and not in_fifo_p.full and not in_finished:
                        nonlocal in_counter
                        in_counter = in_counter + 1
                        in_fifo_p.data.next = in_desc.create_constant(input_data[min(in_counter, len(input_data) - 1)])
                        if in_counter >= len(input_data):
                            in_finished.next = True

            @instance
            def input_wr_driver():
                yield rst.negedge
                pattern_index = 0
                while True:
                    for _ in range(wr_pattern[pattern_index]):
                        yield clk.posedge, in_finished

                        if in_finished:
                            in_fifo_p.wr.next = False
                            return
                    in_fifo_p.wr.next = not in_fifo_p.wr
                    pattern_index = (pattern_index + 1) % len(wr_pattern)

            out_counter = 0

            @always(clk.posedge)
            def output_driver():
                if not rst and out_fifo_c.rd and not out_fifo_c.empty:
                    # TODO maybe make independent from data_desc
                    data = {
                        'x': num.get_default_type().value_of(parsed_out_data.x),
                        'y': [num.get_default_type().value_of(el) for el in parsed_out_data.y],
                        'id': parsed_out_data.id
                    }

                    print("Out: %r" % data)

                    nonlocal out_counter
                    self.check_output(data, output_data, out_counter)

                    out_counter = out_counter + 1

                    if in_finished and out_counter == in_counter:
                        raise StopSimulation()

            @instance
            def output_rd_driver():
                yield rst.negedge
                pattern_index = 0
                while True:
                    for _ in range(rd_pattern[pattern_index]):
                        yield clk.posedge

                    out_fifo_c.rd.next = not out_fifo_c.rd
                    pattern_index = (pattern_index + 1) % len(rd_pattern)

            return instances()

        tb = testbench()
        # tb.config_sim(trace=True)
        tb.run_sim()
