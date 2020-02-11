from dataclasses import dataclass

from myhdl import block, SignalType, always_seq, instances, Signal, intbv

from generator import num
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
    address: SignalType  # cp2af_sRxPort.c0.hdr
    tid: SignalType  # mmioHdr.tid
    writeValid: SignalType  # cp2af_sRxPort.c0.mmioWrValid
    writeData: SignalType  # cp2af_sRxPort.c0.data
    readValid: SignalType  # cp2af_sRxPort.c0.mmioRdValid
    readResponeTid: SignalType  # af2cp_sTxPort.c2.hdr.tid
    readResponseData: SignalType  # af2cp_sTxPort.c2.data
    readResponseValid: SignalType  # af2cp_sTxPort.c2.mmioRdValid


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

    @always_seq(interface.clk.posedge, reset=interface.reset)
    def handle_writes():
        if interface.writeValid:
            if interface.address == csr_addresses['h']:
                rk_interface.h.next = interface.writeData[64:]
            elif interface.address == csr_addresses['n']:
                rk_interface.n.next = interface.writeData[32:]
            elif interface.address == csr_addresses['x_start']:
                rk_interface.x_start.next = interface.writeData[64:]
            elif interface.address == csr_addresses['y_start_addr']:
                y_start_addr.next = interface.writeData[32:]
            elif interface.address == csr_addresses['y_start_val']:
                for index in range(config.system_size):
                    if y_start_addr == index:
                        rk_interface.y_start[index].next = interface.writeData[64:]
            elif interface.address == csr_addresses['y_addr']:
                y_addr.next = interface.writeData[32:]
            elif interface.address == csr_addresses['enb']:
                rk_interface.flow.enb.next = interface.writeData[1:]

    feature_header = intbv(0)[64:]
    feature_header[64:60] = 0b0001  # Feature type = AFU
    feature_header[60:52] = 0b0  # reserved
    feature_header[52:48] = 0b0  # AFU minor revision = 0
    feature_header[48:41] = 0b0  # reserved
    feature_header[40] = True  # end of DFH list = 1
    feature_header[40:16] = 0b0  # next DFH offset = 0
    feature_header[16:12] = 0b0  # afu major revision = 0
    feature_header[12:0] = 0b0  # feature ID = 0

    @always_seq(interface.clk.posedge, reset=interface.reset)
    def handle_reads():  # TODO reset of ccip may be not correct or missing, fixable when full ccip is handled here
        if interface.readValid:
            # Copy tid for request response mapping
            interface.readResponeTid.next = interface.tid
            # Send response
            interface.readResponseValid.next = 1
            # Necessary registers
            if interface.address == 0x0000:  # AFU_HEADER
                interface.readResponseData.next = feature_header
            elif interface.address == 0x0002:  # AFU_ID_L
                interface.readResponseData.next = 0x9865c0c8e45e3ec7  # TODO load AFU ID from config
            elif interface.address == 0x0004:  # AFU_ID_H
                interface.readResponseData.next = 0x2280d43c553d4c44
            elif interface.address == 0x0006:  # DFH_RSVD0
                interface.readResponseData.next = intbv(0)[64:]
            elif interface.address == 0x0008:  # DFH_RSVD1
                interface.readResponseData.next = intbv(0)[64:]
            # Custom AFU CSR
            if interface.address == csr_addresses['h']:
                interface.readResponseData.next = rk_interface.h[64:]
            elif interface.address == csr_addresses['n']:
                interface.readResponseData.next = rk_interface.n[32:]
            elif interface.address == csr_addresses['x_start']:
                interface.readResponseData.next = rk_interface.x_start[64:]
            elif interface.address == csr_addresses['y_start_addr']:
                interface.readResponseData.next = y_start_addr[32:]
            elif interface.address == csr_addresses['y_start_val']:
                for index in range(config.system_size):
                    if y_start_addr == index:
                        interface.readResponseData.next = rk_interface.y_start[index][64:]
            elif interface.address == csr_addresses['x']:
                interface.readResponseData.next = rk_interface.x[64:]
            elif interface.address == csr_addresses['y_addr']:
                interface.readResponseData.next = y_addr[32:]
            elif interface.address == csr_addresses['y_val']:
                for index in range(config.system_size):
                    if y_addr == index:
                        interface.readResponseData.next = rk_interface.y[index][64:]
            elif interface.address == csr_addresses['enb']:
                interface.readResponseData.next = rk_interface.flow.enb[1:]
            elif interface.address == csr_addresses['fin']:
                interface.readResponseData.next = rk_interface.flow.fin[1:]
            # Catch all
            else:
                interface.readResponseData.next = intbv(0)[64:]
        else:
            # Reset valid marker from previous response
            interface.readResponseValid.next = 0
        pass

    rk_insts = rk_solver(config, rk_interface)

    return instances()
