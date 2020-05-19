import random
import struct
from typing import List

from myhdl import block, Signal, ResetSignal, always, delay, instance, SignalType, always_seq, always_comb, instances

from common.config import Config
from common.packed_struct import BitVector
from generator import csr
from generator.afu import afu
from generator.ccip import CcipTx, CcipRx, CcipC0ReqMmioHdr, CcipC0RspMemHdr
from generator.generator import _load_config
from utils import num


class Fim:
    def __init__(self):
        self._current_input_id = 0
        self._csr_write_buffer = []

        self._mem_read_request_buffer = []

        self._mem_input = bytearray(2048)
        self._mem_input_data_offset = 0
        self._mem_output = bytearray(2048)

    def add_input(self, x_start: float, y_start: List[float], h: int, n: int) -> int:
        self._current_input_id = self._current_input_id + 1
        struct.pack_into('<Iq2qqI', self._mem_input, self._mem_input_data_offset,
                         int(n),
                         num.int_from_float(h),
                         *map(num.int_from_float, reversed(y_start)),
                         num.int_from_float(x_start),
                         int(self._current_input_id))
        self._mem_input_data_offset += 40

        return self._current_input_id

    def queue_csr_read(self, addr):
        raise NotImplementedError()

    def queue_csr_write(self, addr, value):
        self._csr_write_buffer.append({
            'addr': addr,
            'data': value
        })

    @block
    def instance(self, clk: SignalType, cp2af_port: SignalType, af2cp_port: SignalType):
        """
        FPGA interface manager - logic implementation for simulation purpose.
        This implementation of ccip is intentionally not complete. Use with care.
        :return: myhdl instances
        """
        cp2af = CcipRx.create_write_instance()
        cp2af_sig = cp2af.packed()
        af2cp = CcipTx.create_read_instance(af2cp_port)

        @always_comb
        def assign_cp2af():
            cp2af_port.next = cp2af_sig

        @always_seq(clk.posedge, reset=None)
        def csr_write_driver():
            if len(self._csr_write_buffer) > 0:
                write = self._csr_write_buffer.pop(0)
                cp2af.c0.mmioWrValid.next = True
                cp2af.c0.data.next = write['data']
                # Create mmio_hdr and fill it
                mmio_hdr = CcipC0ReqMmioHdr.create_write_instance()
                mmio_hdr.address.next = write['addr']
                mmio_hdr.update()
                mmio_hdr_sig = mmio_hdr.packed()
                # Copy values from castet mmio_hdr to CcipC0RspMemHdr
                casted_mmio_hdr = CcipC0RspMemHdr.create_read_instance(mmio_hdr_sig)
                cp2af.c0.hdr.vc_used.next = casted_mmio_hdr.vc_used
                cp2af.c0.hdr.rsvd1.next = casted_mmio_hdr.rsvd1
                cp2af.c0.hdr.hit_miss.next = casted_mmio_hdr.hit_miss
                cp2af.c0.hdr.rsvd0.next = casted_mmio_hdr.rsvd0
                cp2af.c0.hdr.cl_num.next = casted_mmio_hdr.cl_num
                cp2af.c0.hdr.resp_type.next = casted_mmio_hdr.resp_type
                cp2af.c0.hdr.mdata.next = casted_mmio_hdr.mdata

                print('CSR_WRITE: %r' % write)
            else:
                cp2af.c0.mmioWrValid.next = False

        @always_seq(clk.posedge, reset=None)
        def csr_read_response_handler():
            if af2cp.c2.mmioRdValid:
                response = {
                    'tid': af2cp.c2.hdr.tid[:],
                    'data': af2cp.c2.data[:]
                }
                print('CSR_READ_RESPONSE: %r' % response)

        @always_seq(clk.posedge, reset=None)
        def mem_read_request_handler():
            if af2cp.c0.valid:
                request = {
                    'addr': af2cp.c0.hdr.address[:],
                    'cl': af2cp.c0.hdr.cl_len[:],
                }
                self._mem_read_request_buffer.append(request)
                print('MEM_READ_REQUEST: %r' % request)

        @instance
        def mem_read_response_driver():
            while True:
                yield clk.posedge
                if len(self._mem_read_request_buffer) > 0:
                    request = self._mem_read_request_buffer.pop(0)

                    if request['cl'] != 3:
                        raise NotImplementedError()

                    # Prepare responses
                    responses = []
                    for cl in range(4):
                        base_addr = (request['addr'] + cl) * 64
                        responses.append({
                            'cl_num': cl,
                            'data': int.from_bytes(
                                self._mem_input[base_addr:base_addr + 64],
                                'little', signed=False)
                        })
                    random.shuffle(responses)

                    # Send responses
                    for resp in responses:
                        yield clk.posedge
                        cp2af.c0.data.next = resp['data']
                        cp2af.c0.hdr.mdata.next = 0
                        cp2af.c0.hdr.cl_num.next = resp['cl_num']
                        cp2af.c0.rspValid.next = True
                        print('MEM_READ_RESPONSE: %r' % resp)
                    # Deactivate valid
                    yield clk.posedge
                    cp2af.c0.rspValid.next = False

        @always_seq(clk.posedge, reset=None)
        def mem_write_handler():
            if af2cp.c1.valid:
                write = {
                    'addr': af2cp.c1.hdr.address[:],
                    'cl': af2cp.c0.hdr.cl_len[:],
                    'sop': af2cp.c1.hdr.sop[:],
                    'data': af2cp.c1.data[:]
                }
                print('MEM_WRITE: %r' % write)

        return instances()


def sim_manager(*config_files, trace=False, runtime_config=None):
    config_dict = _load_config(*config_files)
    if runtime_config is not None:
        config_dict.update(runtime_config)
    config = Config.from_dict(config_dict)

    @block
    def sim():
        clk = Signal(bool(0))
        usr_clk = Signal(bool(0))
        reset = ResetSignal(True, True, False)

        cp2af_port = BitVector(len(CcipRx)).create_instance()
        af2cp_port = BitVector(len(CcipTx)).create_instance()

        afu_inst = afu(config, clk, usr_clk, reset, cp2af_port, af2cp_port)

        fim = Fim()
        fim_inst = fim.instance(clk, cp2af_port, af2cp_port)

        @always(delay(5))
        def clk_driver():
            """
            Rising clk edge every 10 steps.
            """
            clk.next = not clk

        @always(delay(23))
        def usr_clk_driver():
            """
            Rising usr_clk edge every 46 steps.
            """
            usr_clk.next = not usr_clk

        @instance
        def reset_driver():
            """
            Deactivate reset after 4 rising edges.
            """
            reset.next = True
            yield delay(40)
            reset.next = False

        @instance
        def runtime():
            yield delay(200)
            fim.queue_csr_write(csr.csr_addresses['buffer_size'], 1)
            fim.queue_csr_write(csr.csr_addresses['buffer_unused_bytes'], 176)
            yield delay(20)
            fim.add_input(0, [2, 1], 0.1, 100)
            fim.add_input(0, [2, 1], 0.1, 100)
            yield delay(40)
            fim.queue_csr_write(csr.csr_addresses['enb'], 1)

        return instances()

    tb = sim()
    tb.config_sim(trace=trace)
    tb.run_sim()
