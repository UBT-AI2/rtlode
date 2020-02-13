from dataclasses import dataclass

from myhdl import block, SignalType, always_seq, instances, Signal, intbv

from generator import num
from generator.ccip import CcipRx, CcipTx, CcipC0ReqMmioHdr
from generator.config import Config
from generator.runge_kutta import rk_solver, RKInterface
from generator.utils import clone_signal
from generator.flow import FlowControl


csr_addresses = {
    'h': 0x0020,
    'n': 0x0030,
    'x_start': 0x0040,
    'y_start_addr': 0x0050,
    'y_start_val': 0x0060,
    'x': 0x0070,
    'y_addr': 0x0080,
    'y_val': 0x0090,
    'enb': 0x00A0,
    'fin': 0x00B0,
}


@dataclass
class AfuInterface:
    """
    Defines the afu interface.
    """
    clk: SignalType
    reset: SignalType
    cp2af_sRxPort: SignalType
    af2cp_sTxPort: SignalType


@block
def afu(config: Config, interface: AfuInterface):
    """
    Wrapper logic to port internally solver interface to external afu interface.

    :param config: configuration parameters for the solver
    :param interface: external afu interface
    :return: myhdl instances of the afu
    """
    rk_interface = RKInterface(
        FlowControl(
            interface.clk,
            interface.reset,
            Signal(bool(0)),
            Signal(bool(0))
        ),
        Signal(num.default()),
        Signal(num.integer()),
        Signal(num.default()),
        [clone_signal(Signal(num.default())) for _ in range(config.system_size)],
        Signal(num.default()),
        [clone_signal(Signal(num.default())) for _ in range(config.system_size)]
    )
    y_start_addr = Signal(num.integer())
    y_addr = Signal(num.integer())

    cp2af = CcipRx.create_read_instance(interface.cp2af_sRxPort)
    mmio_hdr = CcipC0ReqMmioHdr.create_read_instance(cp2af.c0.hdr)

    @always_seq(interface.clk.posedge, reset=interface.reset)
    def handle_writes():
        if cp2af.c0.mmioWrValid:
            if mmio_hdr.address == csr_addresses['h']:
                rk_interface.h.next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_addresses['n']:
                rk_interface.n.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_addresses['x_start']:
                rk_interface.x_start.next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_addresses['y_start_addr']:
                y_start_addr.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_addresses['y_start_val']:
                for index in range(config.system_size):
                    if y_start_addr == index:
                        rk_interface.y_start[index].next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_addresses['y_addr']:
                y_addr.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_addresses['enb']:
                rk_interface.flow.enb.next = cp2af.c0.data[1:]

    feature_header = intbv(0)[64:]
    feature_header[64:60] = 0b0001  # Feature type = AFU
    feature_header[60:52] = 0b0  # reserved
    feature_header[52:48] = 0b0  # AFU minor revision = 0
    feature_header[48:41] = 0b0  # reserved
    feature_header[40] = True  # end of DFH list = 1
    feature_header[40:16] = 0b0  # next DFH offset = 0
    feature_header[16:12] = 0b0  # afu major revision = 0
    feature_header[12:0] = 0b0  # feature ID = 0

    af2cp = CcipTx.create_write_instance()
    interface.af2cp_sTxPort.assign(af2cp.packed())

    @always_seq(interface.clk.posedge, reset=None)
    def handle_reads():
        if interface.reset:
            af2cp.c0.hdr.next = 0
            af2cp.c0.valid.next = 0
            af2cp.c1.hdr.next = 0
            af2cp.c1.valid.next = 0
            af2cp.c2.hdr.next = 0
            af2cp.c2.mmioRdValid.next = 0
        else:
            if cp2af.c0.mmioRdValid:
                # Copy tid for request response mapping
                af2cp.c2.hdr.tid.next = mmio_hdr.tid
                # Send response
                af2cp.c2.mmioRdValid.next = 1
                # Necessary registers
                if mmio_hdr.address == 0x0000:  # AFU_HEADER
                    af2cp.c2.data.next = feature_header
                elif mmio_hdr.address == 0x0002:  # AFU_ID_L
                    af2cp.c2.data.next = 0x9865c0c8e45e3ec7  # TODO load AFU ID from config
                elif mmio_hdr.address == 0x0004:  # AFU_ID_H
                    af2cp.c2.data.next = 0x2280d43c553d4c44
                elif mmio_hdr.address == 0x0006:  # DFH_RSVD0
                    af2cp.c2.data.next = intbv(0)[64:]
                elif mmio_hdr.address == 0x0008:  # DFH_RSVD1
                    af2cp.c2.data.next = intbv(0)[64:]
                # Custom AFU CSR
                if mmio_hdr.address == csr_addresses['h']:
                    af2cp.c2.data.next = rk_interface.h[64:]
                elif mmio_hdr.address == csr_addresses['n']:
                    af2cp.c2.data.next = rk_interface.n[32:]
                elif mmio_hdr.address == csr_addresses['x_start']:
                    af2cp.c2.data.next = rk_interface.x_start[64:]
                elif mmio_hdr.address == csr_addresses['y_start_addr']:
                    af2cp.c2.data.next = y_start_addr[32:]
                elif mmio_hdr.address == csr_addresses['y_start_val']:
                    for index in range(config.system_size):
                        if y_start_addr == index:
                            af2cp.c2.data.next = rk_interface.y_start[index][64:]
                elif mmio_hdr.address == csr_addresses['x']:
                    af2cp.c2.data.next = rk_interface.x[64:]
                elif mmio_hdr.address == csr_addresses['y_addr']:
                    af2cp.c2.data.next = y_addr[32:]
                elif mmio_hdr.address == csr_addresses['y_val']:
                    for index in range(config.system_size):
                        if y_addr == index:
                            af2cp.c2.data.next = rk_interface.y[index][64:]
                elif mmio_hdr.address == csr_addresses['enb']:
                    af2cp.c2.data.next = rk_interface.flow.enb[1:]
                elif mmio_hdr.address == csr_addresses['fin']:
                    af2cp.c2.data.next = rk_interface.flow.fin[1:]
                # Catch all
                else:
                    af2cp.c2.data.next = intbv(0)[64:]
            else:
                # Reset valid marker from previous response
                af2cp.c2.mmioRdValid.next = 0

    rk_insts = rk_solver(config, rk_interface)

    return instances()
