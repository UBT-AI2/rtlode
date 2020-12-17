-- ------------------------------------------------------------------------- 
-- High Level Design Compiler for Intel(R) FPGAs Version 17.1 (Release Build #273)
-- Quartus Prime development tool and MATLAB/Simulink Interface
-- 
-- Legal Notice: Copyright 2017 Intel Corporation.  All rights reserved.
-- Your use of  Intel Corporation's design tools,  logic functions and other
-- software and  tools, and its AMPP partner logic functions, and any output
-- files any  of the foregoing (including  device programming  or simulation
-- files), and  any associated  documentation  or information  are expressly
-- subject  to the terms and  conditions of the  Intel FPGA Software License
-- Agreement, Intel MegaCore Function License Agreement, or other applicable
-- license agreement,  including,  without limitation,  that your use is for
-- the  sole  purpose of  programming  logic devices  manufactured by  Intel
-- and  sold by Intel  or its authorized  distributors. Please refer  to the
-- applicable agreement for further details.
-- ---------------------------------------------------------------------------

-- VHDL created from multfp_double_altera_fp_functions_171_s7r74ky
-- VHDL created on Thu Dec 17 13:05:41 2020


library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.NUMERIC_STD.all;
use IEEE.MATH_REAL.all;
use std.TextIO.all;
use work.dspba_library_package.all;

LIBRARY altera_mf;
USE altera_mf.altera_mf_components.all;
LIBRARY altera_lnsim;
USE altera_lnsim.altera_lnsim_components.altera_syncram;
LIBRARY lpm;
USE lpm.lpm_components.all;

library twentynm;
use twentynm.twentynm_components.twentynm_fp_mac;

entity multfp_double_altera_fp_functions_171_s7r74ky is
    port (
        a : in std_logic_vector(63 downto 0);  -- float64_m52
        b : in std_logic_vector(63 downto 0);  -- float64_m52
        q : out std_logic_vector(63 downto 0);  -- float64_m52
        clk : in std_logic;
        areset : in std_logic
    );
end multfp_double_altera_fp_functions_171_s7r74ky;

architecture normal of multfp_double_altera_fp_functions_171_s7r74ky is

    attribute altera_attribute : string;
    attribute altera_attribute of normal : architecture is "-name AUTO_SHIFT_REGISTER_RECOGNITION OFF; -name MESSAGE_DISABLE 10036; -name MESSAGE_DISABLE 10037; -name MESSAGE_DISABLE 14130; -name MESSAGE_DISABLE 14320; -name MESSAGE_DISABLE 15400; -name MESSAGE_DISABLE 14130; -name MESSAGE_DISABLE 10036; -name MESSAGE_DISABLE 12020; -name MESSAGE_DISABLE 12030; -name MESSAGE_DISABLE 12010; -name MESSAGE_DISABLE 12110; -name MESSAGE_DISABLE 14320; -name MESSAGE_DISABLE 13410; -name MESSAGE_DISABLE 113007";
    
    signal GND_q : STD_LOGIC_VECTOR (0 downto 0);
    signal VCC_q : STD_LOGIC_VECTOR (0 downto 0);
    signal expX_uid6_fpMulTest_b : STD_LOGIC_VECTOR (10 downto 0);
    signal expY_uid7_fpMulTest_b : STD_LOGIC_VECTOR (10 downto 0);
    signal signX_uid8_fpMulTest_b : STD_LOGIC_VECTOR (0 downto 0);
    signal signY_uid9_fpMulTest_b : STD_LOGIC_VECTOR (0 downto 0);
    signal cstAllOWE_uid10_fpMulTest_q : STD_LOGIC_VECTOR (10 downto 0);
    signal cstZeroWF_uid11_fpMulTest_q : STD_LOGIC_VECTOR (51 downto 0);
    signal cstAllZWE_uid12_fpMulTest_q : STD_LOGIC_VECTOR (10 downto 0);
    signal frac_x_uid14_fpMulTest_b : STD_LOGIC_VECTOR (51 downto 0);
    signal excZ_x_uid15_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal excZ_x_uid15_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal expXIsMax_uid16_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal expXIsMax_uid16_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsZero_uid17_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsZero_uid17_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsNotZero_uid18_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excI_x_uid19_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excN_x_uid20_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal invExpXIsMax_uid21_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal InvExpXIsZero_uid22_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excR_x_uid23_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal frac_y_uid28_fpMulTest_b : STD_LOGIC_VECTOR (51 downto 0);
    signal excZ_y_uid29_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal excZ_y_uid29_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal expXIsMax_uid30_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal expXIsMax_uid30_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsZero_uid31_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsZero_uid31_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal fracXIsNotZero_uid32_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excI_y_uid33_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excN_y_uid34_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal invExpXIsMax_uid35_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal InvExpXIsZero_uid36_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excR_y_uid37_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal ofracX_uid40_fpMulTest_q : STD_LOGIC_VECTOR (52 downto 0);
    signal ofracY_uid43_fpMulTest_q : STD_LOGIC_VECTOR (52 downto 0);
    signal expSum_uid44_fpMulTest_a : STD_LOGIC_VECTOR (11 downto 0);
    signal expSum_uid44_fpMulTest_b : STD_LOGIC_VECTOR (11 downto 0);
    signal expSum_uid44_fpMulTest_o : STD_LOGIC_VECTOR (11 downto 0);
    signal expSum_uid44_fpMulTest_q : STD_LOGIC_VECTOR (11 downto 0);
    signal biasInc_uid45_fpMulTest_q : STD_LOGIC_VECTOR (12 downto 0);
    signal expSumMBias_uid46_fpMulTest_a : STD_LOGIC_VECTOR (14 downto 0);
    signal expSumMBias_uid46_fpMulTest_b : STD_LOGIC_VECTOR (14 downto 0);
    signal expSumMBias_uid46_fpMulTest_o : STD_LOGIC_VECTOR (14 downto 0);
    signal expSumMBias_uid46_fpMulTest_q : STD_LOGIC_VECTOR (13 downto 0);
    signal signR_uid48_fpMulTest_qi : STD_LOGIC_VECTOR (0 downto 0);
    signal signR_uid48_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal normalizeBit_uid49_fpMulTest_b : STD_LOGIC_VECTOR (0 downto 0);
    signal fracRPostNormHigh_uid51_fpMulTest_in : STD_LOGIC_VECTOR (104 downto 0);
    signal fracRPostNormHigh_uid51_fpMulTest_b : STD_LOGIC_VECTOR (52 downto 0);
    signal fracRPostNormLow_uid52_fpMulTest_in : STD_LOGIC_VECTOR (103 downto 0);
    signal fracRPostNormLow_uid52_fpMulTest_b : STD_LOGIC_VECTOR (52 downto 0);
    signal fracRPostNorm_uid53_fpMulTest_s : STD_LOGIC_VECTOR (0 downto 0);
    signal fracRPostNorm_uid53_fpMulTest_q : STD_LOGIC_VECTOR (52 downto 0);
    signal stickyRange_uid54_fpMulTest_in : STD_LOGIC_VECTOR (50 downto 0);
    signal stickyRange_uid54_fpMulTest_b : STD_LOGIC_VECTOR (50 downto 0);
    signal extraStickyBitOfProd_uid55_fpMulTest_in : STD_LOGIC_VECTOR (51 downto 0);
    signal extraStickyBitOfProd_uid55_fpMulTest_b : STD_LOGIC_VECTOR (0 downto 0);
    signal extraStickyBit_uid56_fpMulTest_s : STD_LOGIC_VECTOR (0 downto 0);
    signal extraStickyBit_uid56_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal stickyExtendedRange_uid57_fpMulTest_q : STD_LOGIC_VECTOR (51 downto 0);
    signal stickyRangeComparator_uid59_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal sticky_uid60_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal fracRPostNorm1dto0_uid61_fpMulTest_in : STD_LOGIC_VECTOR (1 downto 0);
    signal fracRPostNorm1dto0_uid61_fpMulTest_b : STD_LOGIC_VECTOR (1 downto 0);
    signal lrs_uid62_fpMulTest_q : STD_LOGIC_VECTOR (2 downto 0);
    signal roundBitDetectionConstant_uid63_fpMulTest_q : STD_LOGIC_VECTOR (2 downto 0);
    signal roundBitDetectionPattern_uid64_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal roundBit_uid65_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal expFracPreRound_uid66_fpMulTest_q : STD_LOGIC_VECTOR (66 downto 0);
    signal roundBitAndNormalizationOp_uid68_fpMulTest_q : STD_LOGIC_VECTOR (54 downto 0);
    signal expFracRPostRounding_uid69_fpMulTest_a : STD_LOGIC_VECTOR (68 downto 0);
    signal expFracRPostRounding_uid69_fpMulTest_b : STD_LOGIC_VECTOR (68 downto 0);
    signal expFracRPostRounding_uid69_fpMulTest_o : STD_LOGIC_VECTOR (68 downto 0);
    signal expFracRPostRounding_uid69_fpMulTest_q : STD_LOGIC_VECTOR (67 downto 0);
    signal fracRPreExc_uid70_fpMulTest_in : STD_LOGIC_VECTOR (52 downto 0);
    signal fracRPreExc_uid70_fpMulTest_b : STD_LOGIC_VECTOR (51 downto 0);
    signal expRPreExcExt_uid71_fpMulTest_b : STD_LOGIC_VECTOR (14 downto 0);
    signal expRPreExc_uid72_fpMulTest_in : STD_LOGIC_VECTOR (10 downto 0);
    signal expRPreExc_uid72_fpMulTest_b : STD_LOGIC_VECTOR (10 downto 0);
    signal expUdf_uid73_fpMulTest_a : STD_LOGIC_VECTOR (16 downto 0);
    signal expUdf_uid73_fpMulTest_b : STD_LOGIC_VECTOR (16 downto 0);
    signal expUdf_uid73_fpMulTest_o : STD_LOGIC_VECTOR (16 downto 0);
    signal expUdf_uid73_fpMulTest_n : STD_LOGIC_VECTOR (0 downto 0);
    signal expOvf_uid75_fpMulTest_a : STD_LOGIC_VECTOR (16 downto 0);
    signal expOvf_uid75_fpMulTest_b : STD_LOGIC_VECTOR (16 downto 0);
    signal expOvf_uid75_fpMulTest_o : STD_LOGIC_VECTOR (16 downto 0);
    signal expOvf_uid75_fpMulTest_n : STD_LOGIC_VECTOR (0 downto 0);
    signal excXZAndExcYZ_uid76_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excXZAndExcYR_uid77_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excYZAndExcXR_uid78_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excZC3_uid79_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excRZero_uid80_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excXIAndExcYI_uid81_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excXRAndExcYI_uid82_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excYRAndExcXI_uid83_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal ExcROvfAndInReg_uid84_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excRInf_uid85_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excYZAndExcXI_uid86_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excXZAndExcYI_uid87_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal ZeroTimesInf_uid88_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal excRNaN_uid89_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal concExc_uid90_fpMulTest_q : STD_LOGIC_VECTOR (2 downto 0);
    signal excREnc_uid91_fpMulTest_q : STD_LOGIC_VECTOR (1 downto 0);
    signal oneFracRPostExc2_uid92_fpMulTest_q : STD_LOGIC_VECTOR (51 downto 0);
    signal fracRPostExc_uid95_fpMulTest_s : STD_LOGIC_VECTOR (1 downto 0);
    signal fracRPostExc_uid95_fpMulTest_q : STD_LOGIC_VECTOR (51 downto 0);
    signal expRPostExc_uid100_fpMulTest_s : STD_LOGIC_VECTOR (1 downto 0);
    signal expRPostExc_uid100_fpMulTest_q : STD_LOGIC_VECTOR (10 downto 0);
    signal invExcRNaN_uid101_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal signRPostExc_uid102_fpMulTest_q : STD_LOGIC_VECTOR (0 downto 0);
    signal R_uid103_fpMulTest_q : STD_LOGIC_VECTOR (63 downto 0);
    signal aboveLeftY_mergedSignalTM_uid111_prod_uid47_fpMulTest_q : STD_LOGIC_VECTOR (26 downto 0);
    signal rightBottomX_mergedSignalTM_uid115_prod_uid47_fpMulTest_q : STD_LOGIC_VECTOR (26 downto 0);
    signal add0_uid129_prod_uid47_fpMulTest_q : STD_LOGIC_VECTOR (107 downto 0);
    signal add1sumAHighB_uid132_prod_uid47_fpMulTest_a : STD_LOGIC_VECTOR (81 downto 0);
    signal add1sumAHighB_uid132_prod_uid47_fpMulTest_b : STD_LOGIC_VECTOR (81 downto 0);
    signal add1sumAHighB_uid132_prod_uid47_fpMulTest_o : STD_LOGIC_VECTOR (81 downto 0);
    signal add1sumAHighB_uid132_prod_uid47_fpMulTest_q : STD_LOGIC_VECTOR (81 downto 0);
    signal add1_uid133_prod_uid47_fpMulTest_q : STD_LOGIC_VECTOR (108 downto 0);
    signal osig_uid134_prod_uid47_fpMulTest_in : STD_LOGIC_VECTOR (107 downto 0);
    signal osig_uid134_prod_uid47_fpMulTest_b : STD_LOGIC_VECTOR (105 downto 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_reset : std_logic;
    type topProd_uid107_prod_uid47_fpMulTest_cma_a0type is array(NATURAL range <>) of UNSIGNED(26 downto 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_a0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve : boolean;
    attribute preserve of topProd_uid107_prod_uid47_fpMulTest_cma_a0 : signal is true;
    attribute altera_attribute of topProd_uid107_prod_uid47_fpMulTest_cma_a0 : signal is "-name allow_synch_ctrl_usage off";
    signal topProd_uid107_prod_uid47_fpMulTest_cma_a1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of topProd_uid107_prod_uid47_fpMulTest_cma_a1 : signal is true;
    attribute altera_attribute of topProd_uid107_prod_uid47_fpMulTest_cma_a1 : signal is "-name allow_synch_ctrl_usage off";
    signal topProd_uid107_prod_uid47_fpMulTest_cma_c0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of topProd_uid107_prod_uid47_fpMulTest_cma_c0 : signal is true;
    attribute altera_attribute of topProd_uid107_prod_uid47_fpMulTest_cma_c0 : signal is "-name allow_synch_ctrl_usage off";
    signal topProd_uid107_prod_uid47_fpMulTest_cma_c1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of topProd_uid107_prod_uid47_fpMulTest_cma_c1 : signal is true;
    attribute altera_attribute of topProd_uid107_prod_uid47_fpMulTest_cma_c1 : signal is "-name allow_synch_ctrl_usage off";
    type topProd_uid107_prod_uid47_fpMulTest_cma_ptype is array(NATURAL range <>) of UNSIGNED(53 downto 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_p : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_u : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_w : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_x : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_y : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_s : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_qq : STD_LOGIC_VECTOR (53 downto 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_q : STD_LOGIC_VECTOR (53 downto 0);
    signal topProd_uid107_prod_uid47_fpMulTest_cma_ena0 : std_logic;
    signal topProd_uid107_prod_uid47_fpMulTest_cma_ena1 : std_logic;
    signal topProd_uid107_prod_uid47_fpMulTest_cma_ena2 : std_logic;
    signal sm0_uid128_prod_uid47_fpMulTest_cma_reset : std_logic;
    signal sm0_uid128_prod_uid47_fpMulTest_cma_a0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of sm0_uid128_prod_uid47_fpMulTest_cma_a0 : signal is true;
    attribute altera_attribute of sm0_uid128_prod_uid47_fpMulTest_cma_a0 : signal is "-name allow_synch_ctrl_usage off";
    signal sm0_uid128_prod_uid47_fpMulTest_cma_a1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of sm0_uid128_prod_uid47_fpMulTest_cma_a1 : signal is true;
    attribute altera_attribute of sm0_uid128_prod_uid47_fpMulTest_cma_a1 : signal is "-name allow_synch_ctrl_usage off";
    signal sm0_uid128_prod_uid47_fpMulTest_cma_c0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of sm0_uid128_prod_uid47_fpMulTest_cma_c0 : signal is true;
    attribute altera_attribute of sm0_uid128_prod_uid47_fpMulTest_cma_c0 : signal is "-name allow_synch_ctrl_usage off";
    signal sm0_uid128_prod_uid47_fpMulTest_cma_c1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 0);
    attribute preserve of sm0_uid128_prod_uid47_fpMulTest_cma_c1 : signal is true;
    attribute altera_attribute of sm0_uid128_prod_uid47_fpMulTest_cma_c1 : signal is "-name allow_synch_ctrl_usage off";
    signal sm0_uid128_prod_uid47_fpMulTest_cma_p : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_u : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_w : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_x : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_y : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_s : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_qq : STD_LOGIC_VECTOR (53 downto 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_q : STD_LOGIC_VECTOR (53 downto 0);
    signal sm0_uid128_prod_uid47_fpMulTest_cma_ena0 : std_logic;
    signal sm0_uid128_prod_uid47_fpMulTest_cma_ena1 : std_logic;
    signal sm0_uid128_prod_uid47_fpMulTest_cma_ena2 : std_logic;
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_reset : std_logic;
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 1);
    attribute preserve of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0 : signal is true;
    attribute altera_attribute of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0 : signal is "-name allow_synch_ctrl_usage off";
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 1);
    attribute preserve of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1 : signal is true;
    attribute altera_attribute of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1 : signal is "-name allow_synch_ctrl_usage off";
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 1);
    attribute preserve of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0 : signal is true;
    attribute altera_attribute of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0 : signal is "-name allow_synch_ctrl_usage off";
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1 : topProd_uid107_prod_uid47_fpMulTest_cma_a0type(0 to 1);
    attribute preserve of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1 : signal is true;
    attribute altera_attribute of multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1 : signal is "-name allow_synch_ctrl_usage off";
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_p : topProd_uid107_prod_uid47_fpMulTest_cma_ptype(0 to 1);
    type multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype is array(NATURAL range <>) of UNSIGNED(54 downto 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_u : multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype(0 to 1);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_w : multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype(0 to 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_x : multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype(0 to 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_y : multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype(0 to 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_s : multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_utype(0 to 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_qq : STD_LOGIC_VECTOR (54 downto 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_q : STD_LOGIC_VECTOR (54 downto 0);
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena0 : std_logic;
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena1 : std_logic;
    signal multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena2 : std_logic;
    signal topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_b : STD_LOGIC_VECTOR (26 downto 0);
    signal topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_c : STD_LOGIC_VECTOR (25 downto 0);
    signal topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_b : STD_LOGIC_VECTOR (26 downto 0);
    signal topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_c : STD_LOGIC_VECTOR (25 downto 0);
    signal lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_b : STD_LOGIC_VECTOR (26 downto 0);
    signal lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_c : STD_LOGIC_VECTOR (80 downto 0);
    signal redist0_expRPreExcExt_uid71_fpMulTest_b_1_q : STD_LOGIC_VECTOR (14 downto 0);
    signal redist1_fracRPreExc_uid70_fpMulTest_b_1_q : STD_LOGIC_VECTOR (51 downto 0);
    signal redist2_stickyRange_uid54_fpMulTest_b_1_q : STD_LOGIC_VECTOR (50 downto 0);
    signal redist3_normalizeBit_uid49_fpMulTest_b_1_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist4_signR_uid48_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist5_expSum_uid44_fpMulTest_q_4_q : STD_LOGIC_VECTOR (11 downto 0);
    signal redist6_fracXIsZero_uid31_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist7_expXIsMax_uid30_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist8_excZ_y_uid29_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist9_fracXIsZero_uid17_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist10_expXIsMax_uid16_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);
    signal redist11_excZ_x_uid15_fpMulTest_q_5_q : STD_LOGIC_VECTOR (0 downto 0);

begin


    -- frac_x_uid14_fpMulTest(BITSELECT,13)@0
    frac_x_uid14_fpMulTest_b <= a(51 downto 0);

    -- cstZeroWF_uid11_fpMulTest(CONSTANT,10)
    cstZeroWF_uid11_fpMulTest_q <= "0000000000000000000000000000000000000000000000000000";

    -- fracXIsZero_uid17_fpMulTest(LOGICAL,16)@0 + 1
    fracXIsZero_uid17_fpMulTest_qi <= "1" WHEN cstZeroWF_uid11_fpMulTest_q = frac_x_uid14_fpMulTest_b ELSE "0";
    fracXIsZero_uid17_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => fracXIsZero_uid17_fpMulTest_qi, xout => fracXIsZero_uid17_fpMulTest_q, clk => clk, aclr => areset );

    -- redist9_fracXIsZero_uid17_fpMulTest_q_5(DELAY,150)
    redist9_fracXIsZero_uid17_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => fracXIsZero_uid17_fpMulTest_q, xout => redist9_fracXIsZero_uid17_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- cstAllOWE_uid10_fpMulTest(CONSTANT,9)
    cstAllOWE_uid10_fpMulTest_q <= "11111111111";

    -- expX_uid6_fpMulTest(BITSELECT,5)@0
    expX_uid6_fpMulTest_b <= a(62 downto 52);

    -- expXIsMax_uid16_fpMulTest(LOGICAL,15)@0 + 1
    expXIsMax_uid16_fpMulTest_qi <= "1" WHEN expX_uid6_fpMulTest_b = cstAllOWE_uid10_fpMulTest_q ELSE "0";
    expXIsMax_uid16_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => expXIsMax_uid16_fpMulTest_qi, xout => expXIsMax_uid16_fpMulTest_q, clk => clk, aclr => areset );

    -- redist10_expXIsMax_uid16_fpMulTest_q_5(DELAY,151)
    redist10_expXIsMax_uid16_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => expXIsMax_uid16_fpMulTest_q, xout => redist10_expXIsMax_uid16_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- excI_x_uid19_fpMulTest(LOGICAL,18)@5
    excI_x_uid19_fpMulTest_q <= redist10_expXIsMax_uid16_fpMulTest_q_5_q and redist9_fracXIsZero_uid17_fpMulTest_q_5_q;

    -- cstAllZWE_uid12_fpMulTest(CONSTANT,11)
    cstAllZWE_uid12_fpMulTest_q <= "00000000000";

    -- expY_uid7_fpMulTest(BITSELECT,6)@0
    expY_uid7_fpMulTest_b <= b(62 downto 52);

    -- excZ_y_uid29_fpMulTest(LOGICAL,28)@0 + 1
    excZ_y_uid29_fpMulTest_qi <= "1" WHEN expY_uid7_fpMulTest_b = cstAllZWE_uid12_fpMulTest_q ELSE "0";
    excZ_y_uid29_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => excZ_y_uid29_fpMulTest_qi, xout => excZ_y_uid29_fpMulTest_q, clk => clk, aclr => areset );

    -- redist8_excZ_y_uid29_fpMulTest_q_5(DELAY,149)
    redist8_excZ_y_uid29_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => excZ_y_uid29_fpMulTest_q, xout => redist8_excZ_y_uid29_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- excYZAndExcXI_uid86_fpMulTest(LOGICAL,85)@5
    excYZAndExcXI_uid86_fpMulTest_q <= redist8_excZ_y_uid29_fpMulTest_q_5_q and excI_x_uid19_fpMulTest_q;

    -- frac_y_uid28_fpMulTest(BITSELECT,27)@0
    frac_y_uid28_fpMulTest_b <= b(51 downto 0);

    -- fracXIsZero_uid31_fpMulTest(LOGICAL,30)@0 + 1
    fracXIsZero_uid31_fpMulTest_qi <= "1" WHEN cstZeroWF_uid11_fpMulTest_q = frac_y_uid28_fpMulTest_b ELSE "0";
    fracXIsZero_uid31_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => fracXIsZero_uid31_fpMulTest_qi, xout => fracXIsZero_uid31_fpMulTest_q, clk => clk, aclr => areset );

    -- redist6_fracXIsZero_uid31_fpMulTest_q_5(DELAY,147)
    redist6_fracXIsZero_uid31_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => fracXIsZero_uid31_fpMulTest_q, xout => redist6_fracXIsZero_uid31_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- expXIsMax_uid30_fpMulTest(LOGICAL,29)@0 + 1
    expXIsMax_uid30_fpMulTest_qi <= "1" WHEN expY_uid7_fpMulTest_b = cstAllOWE_uid10_fpMulTest_q ELSE "0";
    expXIsMax_uid30_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => expXIsMax_uid30_fpMulTest_qi, xout => expXIsMax_uid30_fpMulTest_q, clk => clk, aclr => areset );

    -- redist7_expXIsMax_uid30_fpMulTest_q_5(DELAY,148)
    redist7_expXIsMax_uid30_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => expXIsMax_uid30_fpMulTest_q, xout => redist7_expXIsMax_uid30_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- excI_y_uid33_fpMulTest(LOGICAL,32)@5
    excI_y_uid33_fpMulTest_q <= redist7_expXIsMax_uid30_fpMulTest_q_5_q and redist6_fracXIsZero_uid31_fpMulTest_q_5_q;

    -- excZ_x_uid15_fpMulTest(LOGICAL,14)@0 + 1
    excZ_x_uid15_fpMulTest_qi <= "1" WHEN expX_uid6_fpMulTest_b = cstAllZWE_uid12_fpMulTest_q ELSE "0";
    excZ_x_uid15_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => excZ_x_uid15_fpMulTest_qi, xout => excZ_x_uid15_fpMulTest_q, clk => clk, aclr => areset );

    -- redist11_excZ_x_uid15_fpMulTest_q_5(DELAY,152)
    redist11_excZ_x_uid15_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => excZ_x_uid15_fpMulTest_q, xout => redist11_excZ_x_uid15_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- excXZAndExcYI_uid87_fpMulTest(LOGICAL,86)@5
    excXZAndExcYI_uid87_fpMulTest_q <= redist11_excZ_x_uid15_fpMulTest_q_5_q and excI_y_uid33_fpMulTest_q;

    -- ZeroTimesInf_uid88_fpMulTest(LOGICAL,87)@5
    ZeroTimesInf_uid88_fpMulTest_q <= excXZAndExcYI_uid87_fpMulTest_q or excYZAndExcXI_uid86_fpMulTest_q;

    -- fracXIsNotZero_uid32_fpMulTest(LOGICAL,31)@5
    fracXIsNotZero_uid32_fpMulTest_q <= not (redist6_fracXIsZero_uid31_fpMulTest_q_5_q);

    -- excN_y_uid34_fpMulTest(LOGICAL,33)@5
    excN_y_uid34_fpMulTest_q <= redist7_expXIsMax_uid30_fpMulTest_q_5_q and fracXIsNotZero_uid32_fpMulTest_q;

    -- fracXIsNotZero_uid18_fpMulTest(LOGICAL,17)@5
    fracXIsNotZero_uid18_fpMulTest_q <= not (redist9_fracXIsZero_uid17_fpMulTest_q_5_q);

    -- excN_x_uid20_fpMulTest(LOGICAL,19)@5
    excN_x_uid20_fpMulTest_q <= redist10_expXIsMax_uid16_fpMulTest_q_5_q and fracXIsNotZero_uid18_fpMulTest_q;

    -- excRNaN_uid89_fpMulTest(LOGICAL,88)@5
    excRNaN_uid89_fpMulTest_q <= excN_x_uid20_fpMulTest_q or excN_y_uid34_fpMulTest_q or ZeroTimesInf_uid88_fpMulTest_q;

    -- invExcRNaN_uid101_fpMulTest(LOGICAL,100)@5
    invExcRNaN_uid101_fpMulTest_q <= not (excRNaN_uid89_fpMulTest_q);

    -- signY_uid9_fpMulTest(BITSELECT,8)@0
    signY_uid9_fpMulTest_b <= STD_LOGIC_VECTOR(b(63 downto 63));

    -- signX_uid8_fpMulTest(BITSELECT,7)@0
    signX_uid8_fpMulTest_b <= STD_LOGIC_VECTOR(a(63 downto 63));

    -- signR_uid48_fpMulTest(LOGICAL,47)@0 + 1
    signR_uid48_fpMulTest_qi <= signX_uid8_fpMulTest_b xor signY_uid9_fpMulTest_b;
    signR_uid48_fpMulTest_delay : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => signR_uid48_fpMulTest_qi, xout => signR_uid48_fpMulTest_q, clk => clk, aclr => areset );

    -- redist4_signR_uid48_fpMulTest_q_5(DELAY,145)
    redist4_signR_uid48_fpMulTest_q_5 : dspba_delay
    GENERIC MAP ( width => 1, depth => 4, reset_kind => "ASYNC" )
    PORT MAP ( xin => signR_uid48_fpMulTest_q, xout => redist4_signR_uid48_fpMulTest_q_5_q, clk => clk, aclr => areset );

    -- VCC(CONSTANT,1)
    VCC_q <= "1";

    -- signRPostExc_uid102_fpMulTest(LOGICAL,101)@5
    signRPostExc_uid102_fpMulTest_q <= redist4_signR_uid48_fpMulTest_q_5_q and invExcRNaN_uid101_fpMulTest_q;

    -- GND(CONSTANT,0)
    GND_q <= "0";

    -- ofracX_uid40_fpMulTest(BITJOIN,39)@0
    ofracX_uid40_fpMulTest_q <= VCC_q & frac_x_uid14_fpMulTest_b;

    -- topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select(BITSELECT,138)@0
    topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_b <= ofracX_uid40_fpMulTest_q(52 downto 26);
    topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_c <= ofracX_uid40_fpMulTest_q(25 downto 0);

    -- aboveLeftY_mergedSignalTM_uid111_prod_uid47_fpMulTest(BITJOIN,110)@0
    aboveLeftY_mergedSignalTM_uid111_prod_uid47_fpMulTest_q <= topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_c & GND_q;

    -- rightBottomX_mergedSignalTM_uid115_prod_uid47_fpMulTest(BITJOIN,114)@0
    rightBottomX_mergedSignalTM_uid115_prod_uid47_fpMulTest_q <= topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_c & GND_q;

    -- ofracY_uid43_fpMulTest(BITJOIN,42)@0
    ofracY_uid43_fpMulTest_q <= VCC_q & frac_y_uid28_fpMulTest_b;

    -- topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select(BITSELECT,139)@0
    topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_b <= ofracY_uid43_fpMulTest_q(52 downto 26);
    topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_c <= ofracY_uid43_fpMulTest_q(25 downto 0);

    -- multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma(CHAINMULTADD,137)@0 + 3
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_reset <= areset;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena0 <= '1';
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena1 <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena0;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena2 <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena0;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_p(0) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1(0) * multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1(0);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_p(1) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1(1) * multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1(1);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_u(0) <= RESIZE(multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_p(0),55);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_u(1) <= RESIZE(multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_p(1),55);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_w(0) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_u(0) + multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_u(1);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_x(0) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_w(0);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_y(0) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_x(0);
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_chainmultadd_input: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0 <= (others => (others => '0'));
            multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena0 = '1') THEN
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0(0) <= RESIZE(UNSIGNED(topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_b),27);
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0(1) <= RESIZE(UNSIGNED(aboveLeftY_mergedSignalTM_uid111_prod_uid47_fpMulTest_q),27);
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0(0) <= RESIZE(UNSIGNED(rightBottomX_mergedSignalTM_uid115_prod_uid47_fpMulTest_q),27);
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0(1) <= RESIZE(UNSIGNED(topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_b),27);
            END IF;
        END IF;
    END PROCESS;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_chainmultadd_pipe: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1 <= (others => (others => '0'));
            multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena2 = '1') THEN
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a1 <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_a0;
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c1 <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_c0;
            END IF;
        END IF;
    END PROCESS;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_chainmultadd_output: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_s <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_ena1 = '1') THEN
                multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_s(0) <= multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_y(0);
            END IF;
        END IF;
    END PROCESS;
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_delay : dspba_delay
    GENERIC MAP ( width => 55, depth => 0, reset_kind => "ASYNC" )
    PORT MAP ( xin => STD_LOGIC_VECTOR(multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_s(0)(54 downto 0)), xout => multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_qq, clk => clk, aclr => areset );
    multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_q <= STD_LOGIC_VECTOR(multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_qq(54 downto 0));

    -- add1sumAHighB_uid132_prod_uid47_fpMulTest(ADD,131)@3
    add1sumAHighB_uid132_prod_uid47_fpMulTest_a <= STD_LOGIC_VECTOR("000000000000000000000000000" & multSumOfTwoTS_uid118_prod_uid47_fpMulTest_cma_q);
    add1sumAHighB_uid132_prod_uid47_fpMulTest_b <= STD_LOGIC_VECTOR("0" & lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_c);
    add1sumAHighB_uid132_prod_uid47_fpMulTest_o <= STD_LOGIC_VECTOR(UNSIGNED(add1sumAHighB_uid132_prod_uid47_fpMulTest_a) + UNSIGNED(add1sumAHighB_uid132_prod_uid47_fpMulTest_b));
    add1sumAHighB_uid132_prod_uid47_fpMulTest_q <= add1sumAHighB_uid132_prod_uid47_fpMulTest_o(81 downto 0);

    -- topProd_uid107_prod_uid47_fpMulTest_cma(CHAINMULTADD,135)@0 + 3
    topProd_uid107_prod_uid47_fpMulTest_cma_reset <= areset;
    topProd_uid107_prod_uid47_fpMulTest_cma_ena0 <= '1';
    topProd_uid107_prod_uid47_fpMulTest_cma_ena1 <= topProd_uid107_prod_uid47_fpMulTest_cma_ena0;
    topProd_uid107_prod_uid47_fpMulTest_cma_ena2 <= topProd_uid107_prod_uid47_fpMulTest_cma_ena0;
    topProd_uid107_prod_uid47_fpMulTest_cma_p(0) <= topProd_uid107_prod_uid47_fpMulTest_cma_a1(0) * topProd_uid107_prod_uid47_fpMulTest_cma_c1(0);
    topProd_uid107_prod_uid47_fpMulTest_cma_u(0) <= RESIZE(topProd_uid107_prod_uid47_fpMulTest_cma_p(0),54);
    topProd_uid107_prod_uid47_fpMulTest_cma_w(0) <= topProd_uid107_prod_uid47_fpMulTest_cma_u(0);
    topProd_uid107_prod_uid47_fpMulTest_cma_x(0) <= topProd_uid107_prod_uid47_fpMulTest_cma_w(0);
    topProd_uid107_prod_uid47_fpMulTest_cma_y(0) <= topProd_uid107_prod_uid47_fpMulTest_cma_x(0);
    topProd_uid107_prod_uid47_fpMulTest_cma_chainmultadd_input: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            topProd_uid107_prod_uid47_fpMulTest_cma_a0 <= (others => (others => '0'));
            topProd_uid107_prod_uid47_fpMulTest_cma_c0 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (topProd_uid107_prod_uid47_fpMulTest_cma_ena0 = '1') THEN
                topProd_uid107_prod_uid47_fpMulTest_cma_a0(0) <= RESIZE(UNSIGNED(topRangeX_uid105_prod_uid47_fpMulTest_merged_bit_select_b),27);
                topProd_uid107_prod_uid47_fpMulTest_cma_c0(0) <= RESIZE(UNSIGNED(topRangeY_uid106_prod_uid47_fpMulTest_merged_bit_select_b),27);
            END IF;
        END IF;
    END PROCESS;
    topProd_uid107_prod_uid47_fpMulTest_cma_chainmultadd_pipe: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            topProd_uid107_prod_uid47_fpMulTest_cma_a1 <= (others => (others => '0'));
            topProd_uid107_prod_uid47_fpMulTest_cma_c1 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (topProd_uid107_prod_uid47_fpMulTest_cma_ena2 = '1') THEN
                topProd_uid107_prod_uid47_fpMulTest_cma_a1 <= topProd_uid107_prod_uid47_fpMulTest_cma_a0;
                topProd_uid107_prod_uid47_fpMulTest_cma_c1 <= topProd_uid107_prod_uid47_fpMulTest_cma_c0;
            END IF;
        END IF;
    END PROCESS;
    topProd_uid107_prod_uid47_fpMulTest_cma_chainmultadd_output: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            topProd_uid107_prod_uid47_fpMulTest_cma_s <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (topProd_uid107_prod_uid47_fpMulTest_cma_ena1 = '1') THEN
                topProd_uid107_prod_uid47_fpMulTest_cma_s(0) <= topProd_uid107_prod_uid47_fpMulTest_cma_y(0);
            END IF;
        END IF;
    END PROCESS;
    topProd_uid107_prod_uid47_fpMulTest_cma_delay : dspba_delay
    GENERIC MAP ( width => 54, depth => 0, reset_kind => "ASYNC" )
    PORT MAP ( xin => STD_LOGIC_VECTOR(topProd_uid107_prod_uid47_fpMulTest_cma_s(0)(53 downto 0)), xout => topProd_uid107_prod_uid47_fpMulTest_cma_qq, clk => clk, aclr => areset );
    topProd_uid107_prod_uid47_fpMulTest_cma_q <= STD_LOGIC_VECTOR(topProd_uid107_prod_uid47_fpMulTest_cma_qq(53 downto 0));

    -- sm0_uid128_prod_uid47_fpMulTest_cma(CHAINMULTADD,136)@0 + 3
    sm0_uid128_prod_uid47_fpMulTest_cma_reset <= areset;
    sm0_uid128_prod_uid47_fpMulTest_cma_ena0 <= '1';
    sm0_uid128_prod_uid47_fpMulTest_cma_ena1 <= sm0_uid128_prod_uid47_fpMulTest_cma_ena0;
    sm0_uid128_prod_uid47_fpMulTest_cma_ena2 <= sm0_uid128_prod_uid47_fpMulTest_cma_ena0;
    sm0_uid128_prod_uid47_fpMulTest_cma_p(0) <= sm0_uid128_prod_uid47_fpMulTest_cma_a1(0) * sm0_uid128_prod_uid47_fpMulTest_cma_c1(0);
    sm0_uid128_prod_uid47_fpMulTest_cma_u(0) <= RESIZE(sm0_uid128_prod_uid47_fpMulTest_cma_p(0),54);
    sm0_uid128_prod_uid47_fpMulTest_cma_w(0) <= sm0_uid128_prod_uid47_fpMulTest_cma_u(0);
    sm0_uid128_prod_uid47_fpMulTest_cma_x(0) <= sm0_uid128_prod_uid47_fpMulTest_cma_w(0);
    sm0_uid128_prod_uid47_fpMulTest_cma_y(0) <= sm0_uid128_prod_uid47_fpMulTest_cma_x(0);
    sm0_uid128_prod_uid47_fpMulTest_cma_chainmultadd_input: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            sm0_uid128_prod_uid47_fpMulTest_cma_a0 <= (others => (others => '0'));
            sm0_uid128_prod_uid47_fpMulTest_cma_c0 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (sm0_uid128_prod_uid47_fpMulTest_cma_ena0 = '1') THEN
                sm0_uid128_prod_uid47_fpMulTest_cma_a0(0) <= RESIZE(UNSIGNED(rightBottomX_mergedSignalTM_uid115_prod_uid47_fpMulTest_q),27);
                sm0_uid128_prod_uid47_fpMulTest_cma_c0(0) <= RESIZE(UNSIGNED(aboveLeftY_mergedSignalTM_uid111_prod_uid47_fpMulTest_q),27);
            END IF;
        END IF;
    END PROCESS;
    sm0_uid128_prod_uid47_fpMulTest_cma_chainmultadd_pipe: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            sm0_uid128_prod_uid47_fpMulTest_cma_a1 <= (others => (others => '0'));
            sm0_uid128_prod_uid47_fpMulTest_cma_c1 <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (sm0_uid128_prod_uid47_fpMulTest_cma_ena2 = '1') THEN
                sm0_uid128_prod_uid47_fpMulTest_cma_a1 <= sm0_uid128_prod_uid47_fpMulTest_cma_a0;
                sm0_uid128_prod_uid47_fpMulTest_cma_c1 <= sm0_uid128_prod_uid47_fpMulTest_cma_c0;
            END IF;
        END IF;
    END PROCESS;
    sm0_uid128_prod_uid47_fpMulTest_cma_chainmultadd_output: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            sm0_uid128_prod_uid47_fpMulTest_cma_s <= (others => (others => '0'));
        ELSIF (clk'EVENT AND clk = '1') THEN
            IF (sm0_uid128_prod_uid47_fpMulTest_cma_ena1 = '1') THEN
                sm0_uid128_prod_uid47_fpMulTest_cma_s(0) <= sm0_uid128_prod_uid47_fpMulTest_cma_y(0);
            END IF;
        END IF;
    END PROCESS;
    sm0_uid128_prod_uid47_fpMulTest_cma_delay : dspba_delay
    GENERIC MAP ( width => 54, depth => 0, reset_kind => "ASYNC" )
    PORT MAP ( xin => STD_LOGIC_VECTOR(sm0_uid128_prod_uid47_fpMulTest_cma_s(0)(53 downto 0)), xout => sm0_uid128_prod_uid47_fpMulTest_cma_qq, clk => clk, aclr => areset );
    sm0_uid128_prod_uid47_fpMulTest_cma_q <= STD_LOGIC_VECTOR(sm0_uid128_prod_uid47_fpMulTest_cma_qq(53 downto 0));

    -- add0_uid129_prod_uid47_fpMulTest(BITJOIN,128)@3
    add0_uid129_prod_uid47_fpMulTest_q <= topProd_uid107_prod_uid47_fpMulTest_cma_q & sm0_uid128_prod_uid47_fpMulTest_cma_q;

    -- lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select(BITSELECT,140)@3
    lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_b <= add0_uid129_prod_uid47_fpMulTest_q(26 downto 0);
    lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_c <= add0_uid129_prod_uid47_fpMulTest_q(107 downto 27);

    -- add1_uid133_prod_uid47_fpMulTest(BITJOIN,132)@3
    add1_uid133_prod_uid47_fpMulTest_q <= add1sumAHighB_uid132_prod_uid47_fpMulTest_q & lowRangeB_uid130_prod_uid47_fpMulTest_merged_bit_select_b;

    -- osig_uid134_prod_uid47_fpMulTest(BITSELECT,133)@3
    osig_uid134_prod_uid47_fpMulTest_in <= add1_uid133_prod_uid47_fpMulTest_q(107 downto 0);
    osig_uid134_prod_uid47_fpMulTest_b <= osig_uid134_prod_uid47_fpMulTest_in(107 downto 2);

    -- normalizeBit_uid49_fpMulTest(BITSELECT,48)@3
    normalizeBit_uid49_fpMulTest_b <= STD_LOGIC_VECTOR(osig_uid134_prod_uid47_fpMulTest_b(105 downto 105));

    -- redist3_normalizeBit_uid49_fpMulTest_b_1(DELAY,144)
    redist3_normalizeBit_uid49_fpMulTest_b_1 : dspba_delay
    GENERIC MAP ( width => 1, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => normalizeBit_uid49_fpMulTest_b, xout => redist3_normalizeBit_uid49_fpMulTest_b_1_q, clk => clk, aclr => areset );

    -- roundBitDetectionConstant_uid63_fpMulTest(CONSTANT,62)
    roundBitDetectionConstant_uid63_fpMulTest_q <= "010";

    -- fracRPostNormHigh_uid51_fpMulTest(BITSELECT,50)@3
    fracRPostNormHigh_uid51_fpMulTest_in <= osig_uid134_prod_uid47_fpMulTest_b(104 downto 0);
    fracRPostNormHigh_uid51_fpMulTest_b <= fracRPostNormHigh_uid51_fpMulTest_in(104 downto 52);

    -- fracRPostNormLow_uid52_fpMulTest(BITSELECT,51)@3
    fracRPostNormLow_uid52_fpMulTest_in <= osig_uid134_prod_uid47_fpMulTest_b(103 downto 0);
    fracRPostNormLow_uid52_fpMulTest_b <= fracRPostNormLow_uid52_fpMulTest_in(103 downto 51);

    -- fracRPostNorm_uid53_fpMulTest(MUX,52)@3 + 1
    fracRPostNorm_uid53_fpMulTest_s <= normalizeBit_uid49_fpMulTest_b;
    fracRPostNorm_uid53_fpMulTest_clkproc: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            fracRPostNorm_uid53_fpMulTest_q <= (others => '0');
        ELSIF (clk'EVENT AND clk = '1') THEN
            CASE (fracRPostNorm_uid53_fpMulTest_s) IS
                WHEN "0" => fracRPostNorm_uid53_fpMulTest_q <= fracRPostNormLow_uid52_fpMulTest_b;
                WHEN "1" => fracRPostNorm_uid53_fpMulTest_q <= fracRPostNormHigh_uid51_fpMulTest_b;
                WHEN OTHERS => fracRPostNorm_uid53_fpMulTest_q <= (others => '0');
            END CASE;
        END IF;
    END PROCESS;

    -- fracRPostNorm1dto0_uid61_fpMulTest(BITSELECT,60)@4
    fracRPostNorm1dto0_uid61_fpMulTest_in <= fracRPostNorm_uid53_fpMulTest_q(1 downto 0);
    fracRPostNorm1dto0_uid61_fpMulTest_b <= fracRPostNorm1dto0_uid61_fpMulTest_in(1 downto 0);

    -- extraStickyBitOfProd_uid55_fpMulTest(BITSELECT,54)@3
    extraStickyBitOfProd_uid55_fpMulTest_in <= STD_LOGIC_VECTOR(osig_uid134_prod_uid47_fpMulTest_b(51 downto 0));
    extraStickyBitOfProd_uid55_fpMulTest_b <= STD_LOGIC_VECTOR(extraStickyBitOfProd_uid55_fpMulTest_in(51 downto 51));

    -- extraStickyBit_uid56_fpMulTest(MUX,55)@3 + 1
    extraStickyBit_uid56_fpMulTest_s <= normalizeBit_uid49_fpMulTest_b;
    extraStickyBit_uid56_fpMulTest_clkproc: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            extraStickyBit_uid56_fpMulTest_q <= (others => '0');
        ELSIF (clk'EVENT AND clk = '1') THEN
            CASE (extraStickyBit_uid56_fpMulTest_s) IS
                WHEN "0" => extraStickyBit_uid56_fpMulTest_q <= GND_q;
                WHEN "1" => extraStickyBit_uid56_fpMulTest_q <= extraStickyBitOfProd_uid55_fpMulTest_b;
                WHEN OTHERS => extraStickyBit_uid56_fpMulTest_q <= (others => '0');
            END CASE;
        END IF;
    END PROCESS;

    -- stickyRange_uid54_fpMulTest(BITSELECT,53)@3
    stickyRange_uid54_fpMulTest_in <= osig_uid134_prod_uid47_fpMulTest_b(50 downto 0);
    stickyRange_uid54_fpMulTest_b <= stickyRange_uid54_fpMulTest_in(50 downto 0);

    -- redist2_stickyRange_uid54_fpMulTest_b_1(DELAY,143)
    redist2_stickyRange_uid54_fpMulTest_b_1 : dspba_delay
    GENERIC MAP ( width => 51, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => stickyRange_uid54_fpMulTest_b, xout => redist2_stickyRange_uid54_fpMulTest_b_1_q, clk => clk, aclr => areset );

    -- stickyExtendedRange_uid57_fpMulTest(BITJOIN,56)@4
    stickyExtendedRange_uid57_fpMulTest_q <= extraStickyBit_uid56_fpMulTest_q & redist2_stickyRange_uid54_fpMulTest_b_1_q;

    -- stickyRangeComparator_uid59_fpMulTest(LOGICAL,58)@4
    stickyRangeComparator_uid59_fpMulTest_q <= "1" WHEN stickyExtendedRange_uid57_fpMulTest_q = cstZeroWF_uid11_fpMulTest_q ELSE "0";

    -- sticky_uid60_fpMulTest(LOGICAL,59)@4
    sticky_uid60_fpMulTest_q <= not (stickyRangeComparator_uid59_fpMulTest_q);

    -- lrs_uid62_fpMulTest(BITJOIN,61)@4
    lrs_uid62_fpMulTest_q <= fracRPostNorm1dto0_uid61_fpMulTest_b & sticky_uid60_fpMulTest_q;

    -- roundBitDetectionPattern_uid64_fpMulTest(LOGICAL,63)@4
    roundBitDetectionPattern_uid64_fpMulTest_q <= "1" WHEN lrs_uid62_fpMulTest_q = roundBitDetectionConstant_uid63_fpMulTest_q ELSE "0";

    -- roundBit_uid65_fpMulTest(LOGICAL,64)@4
    roundBit_uid65_fpMulTest_q <= not (roundBitDetectionPattern_uid64_fpMulTest_q);

    -- roundBitAndNormalizationOp_uid68_fpMulTest(BITJOIN,67)@4
    roundBitAndNormalizationOp_uid68_fpMulTest_q <= GND_q & redist3_normalizeBit_uid49_fpMulTest_b_1_q & cstZeroWF_uid11_fpMulTest_q & roundBit_uid65_fpMulTest_q;

    -- biasInc_uid45_fpMulTest(CONSTANT,44)
    biasInc_uid45_fpMulTest_q <= "0001111111111";

    -- expSum_uid44_fpMulTest(ADD,43)@0 + 1
    expSum_uid44_fpMulTest_a <= STD_LOGIC_VECTOR("0" & expX_uid6_fpMulTest_b);
    expSum_uid44_fpMulTest_b <= STD_LOGIC_VECTOR("0" & expY_uid7_fpMulTest_b);
    expSum_uid44_fpMulTest_clkproc: PROCESS (clk, areset)
    BEGIN
        IF (areset = '1') THEN
            expSum_uid44_fpMulTest_o <= (others => '0');
        ELSIF (clk'EVENT AND clk = '1') THEN
            expSum_uid44_fpMulTest_o <= STD_LOGIC_VECTOR(UNSIGNED(expSum_uid44_fpMulTest_a) + UNSIGNED(expSum_uid44_fpMulTest_b));
        END IF;
    END PROCESS;
    expSum_uid44_fpMulTest_q <= expSum_uid44_fpMulTest_o(11 downto 0);

    -- redist5_expSum_uid44_fpMulTest_q_4(DELAY,146)
    redist5_expSum_uid44_fpMulTest_q_4 : dspba_delay
    GENERIC MAP ( width => 12, depth => 3, reset_kind => "ASYNC" )
    PORT MAP ( xin => expSum_uid44_fpMulTest_q, xout => redist5_expSum_uid44_fpMulTest_q_4_q, clk => clk, aclr => areset );

    -- expSumMBias_uid46_fpMulTest(SUB,45)@4
    expSumMBias_uid46_fpMulTest_a <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR("000" & redist5_expSum_uid44_fpMulTest_q_4_q));
    expSumMBias_uid46_fpMulTest_b <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR((14 downto 13 => biasInc_uid45_fpMulTest_q(12)) & biasInc_uid45_fpMulTest_q));
    expSumMBias_uid46_fpMulTest_o <= STD_LOGIC_VECTOR(SIGNED(expSumMBias_uid46_fpMulTest_a) - SIGNED(expSumMBias_uid46_fpMulTest_b));
    expSumMBias_uid46_fpMulTest_q <= expSumMBias_uid46_fpMulTest_o(13 downto 0);

    -- expFracPreRound_uid66_fpMulTest(BITJOIN,65)@4
    expFracPreRound_uid66_fpMulTest_q <= expSumMBias_uid46_fpMulTest_q & fracRPostNorm_uid53_fpMulTest_q;

    -- expFracRPostRounding_uid69_fpMulTest(ADD,68)@4
    expFracRPostRounding_uid69_fpMulTest_a <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR((68 downto 67 => expFracPreRound_uid66_fpMulTest_q(66)) & expFracPreRound_uid66_fpMulTest_q));
    expFracRPostRounding_uid69_fpMulTest_b <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR("00000000000000" & roundBitAndNormalizationOp_uid68_fpMulTest_q));
    expFracRPostRounding_uid69_fpMulTest_o <= STD_LOGIC_VECTOR(SIGNED(expFracRPostRounding_uid69_fpMulTest_a) + SIGNED(expFracRPostRounding_uid69_fpMulTest_b));
    expFracRPostRounding_uid69_fpMulTest_q <= expFracRPostRounding_uid69_fpMulTest_o(67 downto 0);

    -- expRPreExcExt_uid71_fpMulTest(BITSELECT,70)@4
    expRPreExcExt_uid71_fpMulTest_b <= STD_LOGIC_VECTOR(expFracRPostRounding_uid69_fpMulTest_q(67 downto 53));

    -- redist0_expRPreExcExt_uid71_fpMulTest_b_1(DELAY,141)
    redist0_expRPreExcExt_uid71_fpMulTest_b_1 : dspba_delay
    GENERIC MAP ( width => 15, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => expRPreExcExt_uid71_fpMulTest_b, xout => redist0_expRPreExcExt_uid71_fpMulTest_b_1_q, clk => clk, aclr => areset );

    -- expRPreExc_uid72_fpMulTest(BITSELECT,71)@5
    expRPreExc_uid72_fpMulTest_in <= redist0_expRPreExcExt_uid71_fpMulTest_b_1_q(10 downto 0);
    expRPreExc_uid72_fpMulTest_b <= expRPreExc_uid72_fpMulTest_in(10 downto 0);

    -- expOvf_uid75_fpMulTest(COMPARE,74)@5
    expOvf_uid75_fpMulTest_a <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR((16 downto 15 => redist0_expRPreExcExt_uid71_fpMulTest_b_1_q(14)) & redist0_expRPreExcExt_uid71_fpMulTest_b_1_q));
    expOvf_uid75_fpMulTest_b <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR("000000" & cstAllOWE_uid10_fpMulTest_q));
    expOvf_uid75_fpMulTest_o <= STD_LOGIC_VECTOR(SIGNED(expOvf_uid75_fpMulTest_a) - SIGNED(expOvf_uid75_fpMulTest_b));
    expOvf_uid75_fpMulTest_n(0) <= not (expOvf_uid75_fpMulTest_o(16));

    -- invExpXIsMax_uid35_fpMulTest(LOGICAL,34)@5
    invExpXIsMax_uid35_fpMulTest_q <= not (redist7_expXIsMax_uid30_fpMulTest_q_5_q);

    -- InvExpXIsZero_uid36_fpMulTest(LOGICAL,35)@5
    InvExpXIsZero_uid36_fpMulTest_q <= not (redist8_excZ_y_uid29_fpMulTest_q_5_q);

    -- excR_y_uid37_fpMulTest(LOGICAL,36)@5
    excR_y_uid37_fpMulTest_q <= InvExpXIsZero_uid36_fpMulTest_q and invExpXIsMax_uid35_fpMulTest_q;

    -- invExpXIsMax_uid21_fpMulTest(LOGICAL,20)@5
    invExpXIsMax_uid21_fpMulTest_q <= not (redist10_expXIsMax_uid16_fpMulTest_q_5_q);

    -- InvExpXIsZero_uid22_fpMulTest(LOGICAL,21)@5
    InvExpXIsZero_uid22_fpMulTest_q <= not (redist11_excZ_x_uid15_fpMulTest_q_5_q);

    -- excR_x_uid23_fpMulTest(LOGICAL,22)@5
    excR_x_uid23_fpMulTest_q <= InvExpXIsZero_uid22_fpMulTest_q and invExpXIsMax_uid21_fpMulTest_q;

    -- ExcROvfAndInReg_uid84_fpMulTest(LOGICAL,83)@5
    ExcROvfAndInReg_uid84_fpMulTest_q <= excR_x_uid23_fpMulTest_q and excR_y_uid37_fpMulTest_q and expOvf_uid75_fpMulTest_n;

    -- excYRAndExcXI_uid83_fpMulTest(LOGICAL,82)@5
    excYRAndExcXI_uid83_fpMulTest_q <= excR_y_uid37_fpMulTest_q and excI_x_uid19_fpMulTest_q;

    -- excXRAndExcYI_uid82_fpMulTest(LOGICAL,81)@5
    excXRAndExcYI_uid82_fpMulTest_q <= excR_x_uid23_fpMulTest_q and excI_y_uid33_fpMulTest_q;

    -- excXIAndExcYI_uid81_fpMulTest(LOGICAL,80)@5
    excXIAndExcYI_uid81_fpMulTest_q <= excI_x_uid19_fpMulTest_q and excI_y_uid33_fpMulTest_q;

    -- excRInf_uid85_fpMulTest(LOGICAL,84)@5
    excRInf_uid85_fpMulTest_q <= excXIAndExcYI_uid81_fpMulTest_q or excXRAndExcYI_uid82_fpMulTest_q or excYRAndExcXI_uid83_fpMulTest_q or ExcROvfAndInReg_uid84_fpMulTest_q;

    -- expUdf_uid73_fpMulTest(COMPARE,72)@5
    expUdf_uid73_fpMulTest_a <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR("0000000000000000" & GND_q));
    expUdf_uid73_fpMulTest_b <= STD_LOGIC_VECTOR(STD_LOGIC_VECTOR((16 downto 15 => redist0_expRPreExcExt_uid71_fpMulTest_b_1_q(14)) & redist0_expRPreExcExt_uid71_fpMulTest_b_1_q));
    expUdf_uid73_fpMulTest_o <= STD_LOGIC_VECTOR(SIGNED(expUdf_uid73_fpMulTest_a) - SIGNED(expUdf_uid73_fpMulTest_b));
    expUdf_uid73_fpMulTest_n(0) <= not (expUdf_uid73_fpMulTest_o(16));

    -- excZC3_uid79_fpMulTest(LOGICAL,78)@5
    excZC3_uid79_fpMulTest_q <= excR_x_uid23_fpMulTest_q and excR_y_uid37_fpMulTest_q and expUdf_uid73_fpMulTest_n;

    -- excYZAndExcXR_uid78_fpMulTest(LOGICAL,77)@5
    excYZAndExcXR_uid78_fpMulTest_q <= redist8_excZ_y_uid29_fpMulTest_q_5_q and excR_x_uid23_fpMulTest_q;

    -- excXZAndExcYR_uid77_fpMulTest(LOGICAL,76)@5
    excXZAndExcYR_uid77_fpMulTest_q <= redist11_excZ_x_uid15_fpMulTest_q_5_q and excR_y_uid37_fpMulTest_q;

    -- excXZAndExcYZ_uid76_fpMulTest(LOGICAL,75)@5
    excXZAndExcYZ_uid76_fpMulTest_q <= redist11_excZ_x_uid15_fpMulTest_q_5_q and redist8_excZ_y_uid29_fpMulTest_q_5_q;

    -- excRZero_uid80_fpMulTest(LOGICAL,79)@5
    excRZero_uid80_fpMulTest_q <= excXZAndExcYZ_uid76_fpMulTest_q or excXZAndExcYR_uid77_fpMulTest_q or excYZAndExcXR_uid78_fpMulTest_q or excZC3_uid79_fpMulTest_q;

    -- concExc_uid90_fpMulTest(BITJOIN,89)@5
    concExc_uid90_fpMulTest_q <= excRNaN_uid89_fpMulTest_q & excRInf_uid85_fpMulTest_q & excRZero_uid80_fpMulTest_q;

    -- excREnc_uid91_fpMulTest(LOOKUP,90)@5
    excREnc_uid91_fpMulTest_combproc: PROCESS (concExc_uid90_fpMulTest_q)
    BEGIN
        -- Begin reserved scope level
        CASE (concExc_uid90_fpMulTest_q) IS
            WHEN "000" => excREnc_uid91_fpMulTest_q <= "01";
            WHEN "001" => excREnc_uid91_fpMulTest_q <= "00";
            WHEN "010" => excREnc_uid91_fpMulTest_q <= "10";
            WHEN "011" => excREnc_uid91_fpMulTest_q <= "00";
            WHEN "100" => excREnc_uid91_fpMulTest_q <= "11";
            WHEN "101" => excREnc_uid91_fpMulTest_q <= "00";
            WHEN "110" => excREnc_uid91_fpMulTest_q <= "00";
            WHEN "111" => excREnc_uid91_fpMulTest_q <= "00";
            WHEN OTHERS => -- unreachable
                           excREnc_uid91_fpMulTest_q <= (others => '-');
        END CASE;
        -- End reserved scope level
    END PROCESS;

    -- expRPostExc_uid100_fpMulTest(MUX,99)@5
    expRPostExc_uid100_fpMulTest_s <= excREnc_uid91_fpMulTest_q;
    expRPostExc_uid100_fpMulTest_combproc: PROCESS (expRPostExc_uid100_fpMulTest_s, cstAllZWE_uid12_fpMulTest_q, expRPreExc_uid72_fpMulTest_b, cstAllOWE_uid10_fpMulTest_q)
    BEGIN
        CASE (expRPostExc_uid100_fpMulTest_s) IS
            WHEN "00" => expRPostExc_uid100_fpMulTest_q <= cstAllZWE_uid12_fpMulTest_q;
            WHEN "01" => expRPostExc_uid100_fpMulTest_q <= expRPreExc_uid72_fpMulTest_b;
            WHEN "10" => expRPostExc_uid100_fpMulTest_q <= cstAllOWE_uid10_fpMulTest_q;
            WHEN "11" => expRPostExc_uid100_fpMulTest_q <= cstAllOWE_uid10_fpMulTest_q;
            WHEN OTHERS => expRPostExc_uid100_fpMulTest_q <= (others => '0');
        END CASE;
    END PROCESS;

    -- oneFracRPostExc2_uid92_fpMulTest(CONSTANT,91)
    oneFracRPostExc2_uid92_fpMulTest_q <= "0000000000000000000000000000000000000000000000000001";

    -- fracRPreExc_uid70_fpMulTest(BITSELECT,69)@4
    fracRPreExc_uid70_fpMulTest_in <= expFracRPostRounding_uid69_fpMulTest_q(52 downto 0);
    fracRPreExc_uid70_fpMulTest_b <= fracRPreExc_uid70_fpMulTest_in(52 downto 1);

    -- redist1_fracRPreExc_uid70_fpMulTest_b_1(DELAY,142)
    redist1_fracRPreExc_uid70_fpMulTest_b_1 : dspba_delay
    GENERIC MAP ( width => 52, depth => 1, reset_kind => "ASYNC" )
    PORT MAP ( xin => fracRPreExc_uid70_fpMulTest_b, xout => redist1_fracRPreExc_uid70_fpMulTest_b_1_q, clk => clk, aclr => areset );

    -- fracRPostExc_uid95_fpMulTest(MUX,94)@5
    fracRPostExc_uid95_fpMulTest_s <= excREnc_uid91_fpMulTest_q;
    fracRPostExc_uid95_fpMulTest_combproc: PROCESS (fracRPostExc_uid95_fpMulTest_s, cstZeroWF_uid11_fpMulTest_q, redist1_fracRPreExc_uid70_fpMulTest_b_1_q, oneFracRPostExc2_uid92_fpMulTest_q)
    BEGIN
        CASE (fracRPostExc_uid95_fpMulTest_s) IS
            WHEN "00" => fracRPostExc_uid95_fpMulTest_q <= cstZeroWF_uid11_fpMulTest_q;
            WHEN "01" => fracRPostExc_uid95_fpMulTest_q <= redist1_fracRPreExc_uid70_fpMulTest_b_1_q;
            WHEN "10" => fracRPostExc_uid95_fpMulTest_q <= cstZeroWF_uid11_fpMulTest_q;
            WHEN "11" => fracRPostExc_uid95_fpMulTest_q <= oneFracRPostExc2_uid92_fpMulTest_q;
            WHEN OTHERS => fracRPostExc_uid95_fpMulTest_q <= (others => '0');
        END CASE;
    END PROCESS;

    -- R_uid103_fpMulTest(BITJOIN,102)@5
    R_uid103_fpMulTest_q <= signRPostExc_uid102_fpMulTest_q & expRPostExc_uid100_fpMulTest_q & fracRPostExc_uid95_fpMulTest_q;

    -- xOut(GPOUT,4)@5
    q <= R_uid103_fpMulTest_q;

END normal;
