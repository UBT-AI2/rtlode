from myhdl import block, SignalType, instances, always_comb, ResetSignal

from generator.cdc_utils import async_fifo, FifoProducer, FifoConsumer, areset_synchronizer
from generator.csr import csr_handler, CsrHeader, CsrSignals
from generator.ccip import CcipRx, CcipTx
from generator.config import Config
from generator.dispatcher import dispatcher
from generator.hram import hram_handler
from common.data_desc import get_input_desc, get_output_desc
from generator.packed_struct import BitVector


@block
def afu(config: Config, clk: SignalType, usr_clk: SignalType, reset: SignalType, cp2af_port: SignalType,
        af2cp_port: SignalType):
    """
    Wrapper logic to port internally solver interface to external afu interface.

    :param config: configuration parameters for the solver
    :param clk: clk signal for cci-p
    :param usr_clk: clk signal for logic
    :param reset: active high reset signal
    :param cp2af_port: cci cpu to afu interface
    :param af2cp_port: cci afu to cpu interface
    :return: myhdl instances of the afu
    """
    # Initiating of ccip ports
    cp2af = CcipRx.create_read_instance(cp2af_port)
    af2cp = CcipTx.create_write_instance()
    af2cp_sig = af2cp.packed()

    @always_comb
    def assign_af2cp():
        af2cp_port.next = af2cp_sig

    csr = CsrSignals()
    csr_inst = csr_handler(CsrHeader(config.uuid), clk, reset, cp2af, af2cp, csr)

    usr_reset = ResetSignal(True, True, False)
    cdc_usr_reset = areset_synchronizer(usr_clk, reset, usr_reset)

    input_desc_vec = BitVector(len(get_input_desc(config)))
    output_desc_vec = BitVector(len(get_output_desc(config)))

    in_fifo_p = FifoProducer(clk, reset, input_desc_vec.create_instance())
    in_fifo_c = FifoConsumer(usr_clk, usr_reset, input_desc_vec.create_instance())
    in_fifo = async_fifo(in_fifo_p, in_fifo_c, buffer_size_bits=4)

    out_fifo_p = FifoProducer(usr_clk, usr_reset, output_desc_vec.create_instance())
    out_fifo_c = FifoConsumer(clk, reset, output_desc_vec.create_instance())
    out_fifo = async_fifo(out_fifo_p, out_fifo_c, buffer_size_bits=4)

    # hram_handler, running at clk
    hram_inst = hram_handler(config, cp2af, af2cp, csr, data_out=in_fifo_p, data_in=out_fifo_c)

    # Dispatcher with multiple subsequent solver, running at usr_clk
    disp_inst = dispatcher(config, data_in=in_fifo_c, data_out=out_fifo_p)

    return instances()
