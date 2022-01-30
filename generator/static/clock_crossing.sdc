set_clock_groups -asynchronous -group [get_clocks "*\|outclk1"] -group [get_clocks "*\|clk1x"]
# TODO clks are not found, maybe because created after this

set_net_delay -from [get_registers "*\|solver\|async_fifo*_p_wr_addr_gray\[*\]"] -to [get_registers "*\|solver\|async_fifo1_ff_synchronizer4_assign8_out_val\[*\]"] -max -get_value_from_clock_period dst_clock_period -value_multiplier 0.8
set_max_skew -from [get_keepers "*\|solver\|async_fifo*_p_wr_addr_gray\[*\]"] -to [get_keepers "*\|solver\|async_fifo1_ff_synchronizer4_assign8_out_val\[*\]"] -get_skew_value_from_clock_period min_clock_period -skew_value_multiplier 0.8
