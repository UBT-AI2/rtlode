import random
from typing import List

from myhdl import block, Signal, ResetSignal, always, delay, instance, SignalType, always_seq, always_comb, instances

from framework import data_desc
from framework.data_desc import unpack_output_data
from generator.afu import afu
from generator.config import Config
from framework.packed_struct import BitVector
from generator import csr
from generator.ccip import CcipTx, CcipRx, CcipC0ReqMmioHdr, CcipC0RspMemHdr
from generator.generator import _load_config
from generator.sim.cosim import afu_cosim
from utils import num
from utils.dict_update import deep_update


class Fim:
    def __init__(self, config: Config):
        self._config = config
        self._current_input_id = 0
        self._csr_write_buffer = []

        self._mem_read_request_buffer = []

        self._mem_input = bytearray(4096)
        self._mem_input_chunk_offset = 0
        self._mem_input_data_offset = 0
        self._mem_output = bytearray(4096)
        self._mem_output_chunk_offset = 0
        self._mem_output_data_offset = 0
        self._mem_last_write_addr = 0

    def add_input(self, x_start: float, y_start: List[float], h: int, n: int) -> int:
        self._current_input_id = self._current_input_id + 1

        packed_data = data_desc.pack_input_data(self._config.system_size, {
            'id': int(self._current_input_id),
            'x_start': num.get_default_type().create_constant(x_start),
            'y_start': list(map(num.get_default_type().create_constant, reversed(y_start))),
            'h': num.get_default_type().create_constant(h),
            'n': int(n)
        })
        print(packed_data)
        packed_data_len = len(packed_data)

        offset = self._mem_input_chunk_offset + self._mem_input_data_offset
        self._mem_input[offset:offset + packed_data_len] = packed_data

        self._mem_input_data_offset += packed_data_len
        if 256 - self._mem_input_data_offset < packed_data_len:
            self._mem_input_chunk_offset += 256
            self._mem_input_data_offset = 0

        return self._current_input_id

    def get_output(self) -> int:
        packed_data_len = len(data_desc.get_output_desc(self._config.system_size)) // 8

        offset = self._mem_output_chunk_offset + self._mem_output_data_offset
        packed_data = self._mem_output[offset:offset + packed_data_len]

        unpacked_data = unpack_output_data(self._config.system_size, bytes(packed_data))

        self._mem_output_data_offset += packed_data_len
        if 256 - self._mem_output_data_offset < packed_data_len:
            self._mem_output_chunk_offset += 256
            self._mem_output_data_offset = 0

        return {
            'x': num.get_default_type().value_of(unpacked_data['x']),
            'y': list(map(num.get_default_type().value_of, reversed(unpacked_data['y']))),
            'id': unpacked_data['id']
        }

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

                    yield delay(random.randrange(3, 10, 1) * 45)

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
                if write['sop']:
                    self._mem_last_write_addr = write['addr']
                    addr = write['addr'] * 64
                else:
                    addr = (self._mem_last_write_addr + write['addr']) * 64
                self._mem_output[addr:addr + 64] = int(write['data']._val).to_bytes(64, 'little', signed=False)

        return instances()


def sim_manager(*config_files, trace=False, runtime_config=None):
    config_dict = _load_config(*config_files)
    if runtime_config is not None:
        deep_update(config_dict, runtime_config)
    config = Config.from_dict(config_dict)

    default_factory = num.NumberType.from_config(config_dict.get('numeric', {}))
    num.set_default_type(default_factory)

    @block
    def sim():
        clk = Signal(bool(0))
        usr_clk = Signal(bool(0))
        reset = ResetSignal(True, True, False)

        cp2af_port = BitVector(len(CcipRx)).create_instance()
        af2cp_port = BitVector(len(CcipTx)).create_instance()

        afu_inst = afu(config, clk, usr_clk, reset, cp2af_port, af2cp_port)

        fim = Fim(config)
        fim_inst = fim.instance(clk, cp2af_port, af2cp_port)

        @always(delay(5))
        def clk_driver():
            """
            Rising clk edge every 10 steps.
            """
            clk.next = not clk

        @always(delay(20))
        def usr_clk_driver():
            """
            Rising usr_clk edge every 40 steps.
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
            fim.queue_csr_write(csr.csr_addresses['buffer_size'], 15)
            yield delay(20)
            for i in range(100):
                fim.add_input(
                    config_dict['problem']['x'],
                    config_dict['problem']['y'],
                    config_dict['problem']['h'],
                    config_dict['problem']['n']
                )
            yield delay(40)
            fim.queue_csr_write(csr.csr_addresses['enb'], 1)
            yield delay(1000000)
            for i in range(107):
                print(fim.get_output())

        return instances()

    tb = sim()
    tb.config_sim(trace=trace)
    tb.run_sim(1001000)
