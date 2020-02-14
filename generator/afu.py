from dataclasses import dataclass

from myhdl import block, SignalType, always_seq, instances, Signal, intbv, always_comb

from generator import num
from generator.ccip import CcipRx, CcipTx, CcipC0ReqMmioHdr
from generator.config import Config
from generator.runge_kutta import rk_solver, RKInterface
from generator.utils import clone_signal
from generator.flow import FlowControl


csr_address_h = 0x0020
csr_address_n = 0x0030
csr_address_x_start = 0x0040
csr_address_y_start_addr = 0x0050
csr_address_y_start_val = 0x0060
csr_address_x = 0x0070
csr_address_y_addr = 0x0080
csr_address_y_val = 0x0090
csr_address_enb = 0x00A0
csr_address_fin = 0x00B0


@block
def afu(config: Config, clk: SignalType, reset: SignalType, cp2af_port: SignalType, af2cp_port: SignalType):
    """
    Wrapper logic to port internally solver interface to external afu interface.

    :param config: configuration parameters for the solver
    :param clk: clk signal
    :param reset: active high reset signal
    :param cp2af_port: cci cpu to afu interface
    :param af2cp_port: cci afu to cpu interface
    :return: myhdl instances of the afu
    """
    rk_interface = RKInterface(
        FlowControl(
            clk,
            reset,
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

    cp2af = CcipRx.create_read_instance(cp2af_port)
    mmio_hdr = CcipC0ReqMmioHdr.create_read_instance(cp2af.c0.hdr)

    @always_seq(clk.posedge, reset=reset)
    def handle_writes():
        if cp2af.c0.mmioWrValid:
            if mmio_hdr.address == csr_address_h:
                rk_interface.h.next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_address_n:
                rk_interface.n.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_address_x_start:
                rk_interface.x_start.next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_address_y_start_addr:
                y_start_addr.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_address_y_start_val:
                for index in range(config.system_size):
                    if y_start_addr == index:
                        rk_interface.y_start[index].next = cp2af.c0.data[64:]
            elif mmio_hdr.address == csr_address_y_addr:
                y_addr.next = cp2af.c0.data[32:]
            elif mmio_hdr.address == csr_address_enb:
                rk_interface.flow.enb.next = cp2af.c0.data[1:]

    af2cp = CcipTx.create_write_instance()
    af2cp_sig = af2cp.packed()

    @always_comb
    def assign_af2cp():
        af2cp_port.next = af2cp_sig

    @always_seq(clk.posedge, reset=None)
    def handle_reads():
        if reset:
            af2cp.c0.hdr.vc_sel.next = 0
            af2cp.c0.hdr.rsvd1.next = 0
            af2cp.c0.hdr.cl_len.next = 0
            af2cp.c0.hdr.req_type.next = 0
            af2cp.c0.hdr.rsvd0.next = 0
            af2cp.c0.hdr.address.next = 0
            af2cp.c0.hdr.mdata.next = 0
            af2cp.c0.valid.next = 0

            af2cp.c1.hdr.rsvd2.next = 0
            af2cp.c1.hdr.vc_sel.next = 0
            af2cp.c1.hdr.sop.next = 0
            af2cp.c1.hdr.rsvd1.next = 0
            af2cp.c1.hdr.cl_len.next = 0
            af2cp.c1.hdr.req_type.next = 0
            af2cp.c1.hdr.rsvd0.next = 0
            af2cp.c1.hdr.address.next = 0
            af2cp.c1.hdr.mdata.next = 0
            af2cp.c1.data.next = 0
            af2cp.c1.valid.next = 0

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
                    feature_header = intbv(0)[64:]
                    feature_header[64:60] = 0b0001  # Feature type = AFU
                    feature_header[60:52] = 0b0  # reserved
                    feature_header[52:48] = 0b0  # AFU minor revision = 0
                    feature_header[48:41] = 0b0  # reserved
                    feature_header[40] = True  # end of DFH list = 1
                    feature_header[40:16] = 0b0  # next DFH offset = 0
                    feature_header[16:12] = 0b0  # afu major revision = 0
                    feature_header[12:0] = 0b0  # feature ID = 0
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
                elif mmio_hdr.address == csr_address_h:
                    af2cp.c2.data.next = rk_interface.h[64:]
                elif mmio_hdr.address == csr_address_n:
                    af2cp.c2.data.next = rk_interface.n[32:]
                elif mmio_hdr.address == csr_address_x_start:
                    af2cp.c2.data.next = rk_interface.x_start[64:]
                elif mmio_hdr.address == csr_address_y_start_addr:
                    af2cp.c2.data.next = y_start_addr[32:]
                elif mmio_hdr.address == csr_address_y_start_val:
                    for index in range(config.system_size):
                        if y_start_addr == index:
                            af2cp.c2.data.next = rk_interface.y_start[index][64:]
                elif mmio_hdr.address == csr_address_x:
                    af2cp.c2.data.next = rk_interface.x[64:]
                elif mmio_hdr.address == csr_address_y_addr:
                    af2cp.c2.data.next = y_addr[32:]
                elif mmio_hdr.address == csr_address_y_val:
                    for index in range(config.system_size):
                        if y_addr == index:
                            af2cp.c2.data.next = rk_interface.y[index][64:]
                elif mmio_hdr.address == csr_address_enb:
                    af2cp.c2.data.next = rk_interface.flow.enb[1:]
                elif mmio_hdr.address == csr_address_fin:
                    af2cp.c2.data.next = rk_interface.flow.fin[1:]
                # Catch all
                else:
                    af2cp.c2.data.next = intbv(0)[64:]
            else:
                # Reset valid marker from previous response
                af2cp.c2.mmioRdValid.next = 0

    rk_insts = rk_solver(config, rk_interface)

    return instances()
