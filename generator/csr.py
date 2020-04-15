import uuid

from dataclasses import dataclass, field
from myhdl import block, always_seq, concat, SignalType, Signal, intbv, instances

from generator.ccip import CcipC0ReqMmioHdr, CcipClAddr
from utils import num

csr_addresses = {
    'input_addr': 0x0020,
    'input_ack_id': 0x0030,
    'output_addr': 0x0040,
    'output_ack_id': 0x0050,
    'enb': 0x00A0,
}


class CsrHeader:
    def __init__(self, uuid_str):
        feature_hdr = intbv(0)[64:]
        feature_hdr[64:60] = 0b0001  # Feature type = AFU
        feature_hdr[60:52] = 0b0  # reserved
        feature_hdr[52:48] = 0b0  # AFU minor revision = 0
        feature_hdr[48:41] = 0b0  # reserved
        feature_hdr[40] = True  # end of DFH list = 1
        feature_hdr[40:16] = 0b0  # next DFH offset = 0
        feature_hdr[16:12] = 0b0  # afu major revision = 0
        feature_hdr[12:0] = 0b0  # feature ID = 0
        self.feature = int(feature_hdr)
        afu_id = uuid.UUID(uuid_str).bytes
        self.afu_id_h = int.from_bytes(afu_id[0:8], 'big')
        self.afu_id_l = int.from_bytes(afu_id[8:16], 'big')


@dataclass
class CsrSignals:
    input_addr: SignalType = field(default_factory=CcipClAddr.create_instance)
    input_ack_id: SignalType = field(default_factory=lambda: Signal(num.integer(0)))
    output_addr: SignalType = field(default_factory=CcipClAddr.create_instance)
    output_ack_id: SignalType = field(default_factory=lambda: Signal(num.integer(0)))
    enb: SignalType = field(default_factory=lambda: Signal(bool(0)))


@block
def csr_handler(header: CsrHeader, clk, reset, cp2af, af2cp, data: CsrSignals):
    """
    Logic to handle the control and status register of the afu.
    :param header: static csr configuration
    :param clk: ccip clk
    :param reset: ccip rst
    :param cp2af: cpu to afu interface
    :param af2cp: afu to cpu interface
    :param data: csr data signals
    :return: myhdl instances
    """
    # Remapping of addresses required because of myhdl constraints
    csr_address_input_addr = csr_addresses['input_addr']
    csr_address_input_ack_id = csr_addresses['input_ack_id']
    csr_address_output_addr = csr_addresses['output_addr']
    csr_address_output_ack_id = csr_addresses['output_ack_id']
    csr_address_enb = csr_addresses['enb']

    # Reinterpret header as mmio header
    mmio_hdr = CcipC0ReqMmioHdr.create_read_instance(cp2af.c0.hdr)

    @always_seq(clk.posedge, reset=reset)
    def handle_mmio_writes():
        if cp2af.c0.mmioWrValid:
            if mmio_hdr.address == csr_address_input_addr:
                data.input_addr.next = concat(cp2af.c0.data)[len(CcipClAddr):]
            elif mmio_hdr.address == csr_address_output_addr:
                data.output_addr.next = concat(cp2af.c0.data)[len(CcipClAddr):]
            elif mmio_hdr.address == csr_address_output_ack_id:
                data.output_ack_id.next = concat(cp2af.c0.data)[64:]
            elif mmio_hdr.address == csr_address_enb:
                data.enb.next = concat(cp2af.c0.data)[1:]

    @always_seq(clk.posedge, reset=None)
    def handle_mmio_reads():
        if reset:
            af2cp.c2.hdr.tid.next = 0
            af2cp.c2.mmioRdValid.next = 0
        else:
            if cp2af.c0.mmioRdValid:
                # Copy tid for request response mapping
                af2cp.c2.hdr.tid.next = mmio_hdr.tid
                # Send response
                af2cp.c2.mmioRdValid.next = 1
                # Necessary registers
                if mmio_hdr.address == 0x0000:  # AFU_HEADER
                    af2cp.c2.data.next = header.feature
                elif mmio_hdr.address == 0x0002:  # AFU_ID_L
                    af2cp.c2.data.next = header.afu_id_l
                elif mmio_hdr.address == 0x0004:  # AFU_ID_H
                    af2cp.c2.data.next = header.afu_id_h
                elif mmio_hdr.address == 0x0006:  # DFH_RSVD0
                    af2cp.c2.data.next = 0
                elif mmio_hdr.address == 0x0008:  # DFH_RSVD1
                    af2cp.c2.data.next = 0
                # Custom AFU CSR
                elif mmio_hdr.address == csr_address_input_addr:
                    af2cp.c2.data.next = data.input_addr
                elif mmio_hdr.address == csr_address_input_ack_id:
                    af2cp.c2.data.next = data.input_ack_id
                elif mmio_hdr.address == csr_address_output_addr:
                    af2cp.c2.data.next = data.output_addr
                elif mmio_hdr.address == csr_address_output_ack_id:
                    af2cp.c2.data.next = data.output_ack_id
                elif mmio_hdr.address == csr_address_enb:
                    af2cp.c2.data.next = data.enb
                # Catch all
                else:
                    af2cp.c2.data.next = intbv(0)[64:]
            else:
                # Reset valid marker from previous response
                af2cp.c2.mmioRdValid.next = 0

    return instances()
