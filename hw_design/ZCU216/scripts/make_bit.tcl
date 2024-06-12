if { $argc < 1 } {
    puts "Error: design_name not specified."
    exit 1
}
set design_name [lindex $argv 0]
set core_count [lindex $argv 1]
set overlay_name "${design_name}_proj"

# Set max thread
set_param general.maxThreads 1

# Open project
open_project ./${overlay_name}/${overlay_name}.xpr
open_bd_design ./${overlay_name}/${overlay_name}.srcs/sources_1/bd/${design_name}/${design_name}.bd

# Add top wrapper and xdc files
make_wrapper -files [get_files ./${overlay_name}/${overlay_name}.srcs/sources_1/bd/${design_name}/${design_name}.bd] -top
add_files -norecurse ./${overlay_name}/${overlay_name}.srcs/sources_1/bd/${design_name}/hdl/${design_name}_wrapper.v
set_property top ${design_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

# Call implement
launch_runs impl_1 -to_step write_bitstream -jobs ${core_count}
wait_on_run impl_1

# Move and rename bitstream to final location
file mkdir ./${overlay_name}/bitstream
file copy -force ./${overlay_name}/${overlay_name}.runs/impl_1/${design_name}_wrapper.bit ./${overlay_name}/bitstream/${design_name}.bit

# copy hwh files
file copy -force ./${overlay_name}/${overlay_name}.gen/sources_1/bd/${design_name}/hw_handoff/${design_name}.hwh ./${overlay_name}/bitstream/${design_name}.hwh
