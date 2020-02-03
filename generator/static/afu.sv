// ***************************************************************************
// Copyright (c) 2013-2018, Intel Corporation
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// * Redistributions of source code must retain the above copyright notice,
// this list of conditions and the following disclaimer.
// * Redistributions in binary form must reproduce the above copyright notice,
// this list of conditions and the following disclaimer in the documentation
// and/or other materials provided with the distribution.
// * Neither the name of Intel Corporation nor the names of its contributors
// may be used to endorse or promote products derived from this software
// without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// ***************************************************************************
//
// Module Name:  afu.sv
// Project:      Hello AFU
// Description:  Hello AFU supports MMIO Writes and Reads.
//
// Hello_AFU is provided as a starting point for developing AFUs.
//
// It is strongly recommended:
// - register all AFU inputs and outputs
// - output registers should be initialized with a reset
// - Host Writes and Reads must be sent on Virtual Channel (VC): VH0 - PCIe0 link
// - MMIO addressing must be QuardWord Aligned (Quadword = 8 bytes)
// - AFU_ID must be re-generated for new AFUs.
//
// Please see the CCI-P specification for more information about the CCI-P interfaces.
// AFU template provides 4 AFU CSR registers required by the CCI-P protocol(see
// specification for more information) and a scratch register to issue MMIO Writes and Reads.
//
// Scratch_Reg[63:0] @ Byte Address 0x0080 is provided to test MMIO Reads and Writes to the AFU.
//

`include "platform_if.vh"
`include "afu_json_info.vh"

module afu
   (
    input  clk,    // Core clock. CCI interface is synchronous to this clock.
    input  reset,  // CCI interface ACTIVE HIGH reset.

    // CCI-P signals
    input  t_if_ccip_Rx cp2af_sRxPort,
    output t_if_ccip_Tx af2cp_sTxPort
    );

    // The AFU must respond with its AFU ID in response to MMIO reads of
    // the CCI-P device feature header (DFH).  The AFU ID is a unique ID
    // for a given program.  Here we generated one with the "uuidgen"
    // program and stored it in the AFU's JSON file.  ASE and synthesis
    // setup scripts automatically invoke the OPAE afu_json_mgr script
    // to extract the UUID into afu_json_info.vh.
    logic [127:0] afu_id = `AFU_ACCEL_UUID;

    // Solver subsystem
    logic solver_enb;
    logic solver_fin;
    logic [63:0] solver_h;
    logic [31:0] solver_n;
    logic [63:0] solver_x_start;
    logic [31:0] solver_y_start_addr;
    logic [63:0] solver_y_start_val;
    logic [63:0] solver_x;
    logic [31:0] solver_y_addr;
    logic [63:0] solver_y_val;
    solver solver0(
        clk,
        reset,
        solver_enb,
        solver_fin,
        solver_h,
        solver_n,
        solver_x_start,
        solver_y_start_addr,
        solver_y_start_val,
        solver_x,
        solver_y_addr,
        solver_y_val
    );

    // The c0 header is normally used for memory read responses.
    // The header must be interpreted as an MMIO response when
    // c0 mmmioRdValid or mmioWrValid is set.  In these cases the
    // c0 header is cast into a ReqMmioHdr.
    t_ccip_c0_ReqMmioHdr mmioHdr;
    assign mmioHdr = t_ccip_c0_ReqMmioHdr'(cp2af_sRxPort.c0.hdr);

    //
    // Receive MMIO writes
    //
    always_ff @(posedge clk)
    begin
        if (reset)
        begin
            solver_h <= '0;
            solver_n <= '0;
            solver_x_start <= '0;
            solver_y_start_addr <= '0;
            solver_y_start_val <= '0;
            solver_y_addr <= '0;
            solver_enb <= '0;
        end
        else
        begin
            // set the registers on MMIO write request
            // these are user-defined AFU registers at offset 0x40.
            if (cp2af_sRxPort.c0.mmioWrValid == 1)
            begin
                case (mmioHdr.address)
                    16'h0020: solver_h <= cp2af_sRxPort.c0.data[63:0];
                    16'h0030: solver_n <= cp2af_sRxPort.c0.data[31:0];
                    16'h0040: solver_x_start <= cp2af_sRxPort.c0.data[63:0];
                    16'h0050: solver_y_start_addr <= cp2af_sRxPort.c0.data[31:0];
                    16'h0060: solver_y_start_val <= cp2af_sRxPort.c0.data[63:0];
                    16'h0070: solver_y_addr <= cp2af_sRxPort.c0.data[31:0];
                    16'h0080: solver_enb <= 1'b1;
                endcase
            end
        end
    end

    //
    // Handle MMIO reads.
    //
    always_ff @(posedge clk)
    begin
        if (reset)
        begin
            af2cp_sTxPort.c1.hdr <= '0;
            af2cp_sTxPort.c1.valid <= '0;
            af2cp_sTxPort.c0.hdr <= '0;
            af2cp_sTxPort.c0.valid <= '0;
            af2cp_sTxPort.c2.hdr <= '0;
            af2cp_sTxPort.c2.mmioRdValid <= '0;
        end
        else
        begin
            // Clear read response flag in case there was a response last cycle.
            af2cp_sTxPort.c2.mmioRdValid <= 0;

            // serve MMIO read requests
            if (cp2af_sRxPort.c0.mmioRdValid == 1'b1)
            begin
                // Copy TID, which the host needs to map the response to the request
                af2cp_sTxPort.c2.hdr.tid <= mmioHdr.tid;

                // Post response
                af2cp_sTxPort.c2.mmioRdValid <= 1;

                case (mmioHdr.address)
                    // AFU header
                    16'h0000: af2cp_sTxPort.c2.data <= {
                        4'b0001, // Feature type = AFU
                        8'b0,    // reserved
                        4'b0,    // afu minor revision = 0
                        7'b0,    // reserved
                        1'b1,    // end of DFH list = 1
                        24'b0,   // next DFH offset = 0
                        4'b0,    // afu major revision = 0
                        12'b0    // feature ID = 0
                        };

                    // AFU_ID_L
                    16'h0002: af2cp_sTxPort.c2.data <= afu_id[63:0];

                    // AFU_ID_H
                    16'h0004: af2cp_sTxPort.c2.data <= afu_id[127:64];

                    // DFH_RSVD0 and DFH_RSVD1
                    16'h0006: af2cp_sTxPort.c2.data <= 64'h0;
                    16'h0008: af2cp_sTxPort.c2.data <= 64'h0;

                    // Custom AFU registers
                    16'h0020: af2cp_sTxPort.c2.data <= solver_x;
                    16'h0030: af2cp_sTxPort.c2.data <= solver_y_val;
                    16'h0040: af2cp_sTxPort.c2.data <= solver_fin;

                    default:  af2cp_sTxPort.c2.data <= 64'h0;
                endcase
            end
        end
    end
endmodule
