

set_clock_groups -asynchronous -group [get_clocks {outclk1}] -group [get_clocks {clk1x}]
set_net_delay -from [get_registers {rk_interface_x[*]}] -to [get_registers {af2cp_c2_data[*]}] -max -get_value_from_clock_period dst_clock_period -value_multiplier 0.8
set_max_skew -from [get_keepers {rk_interface_x[*]}] -to [get_keepers {af2cp_c2_data[*]}] -get_skew_value_from_clock_period min_clock_period -skew_value_multiplier 0.8
set_net_delay -from [get_registers {rk_interface_y[*][*]}] -to [get_registers {af2cp_c2_data[*]}] -max -get_value_from_clock_period dst_clock_period -value_multiplier 0.8
set_max_skew -from [get_keepers {rk_interface_y[*][*]}] -to [get_keepers {af2cp_c2_data[*]}] -get_skew_value_from_clock_period min_clock_period -skew_value_multiplier 0.8