set iprepo_dir ./../../../ip/iprepo

if { $argc < 1 } {
    puts "Error: design_name not specified."
    exit 1
}
set design_name [lindex $argv 0]
set overlay_name "${design_name}_proj"

# Set max thread
set_param general.maxThreads 1

# Create project
create_project ${overlay_name} ./${overlay_name} -part xczu49dr-ffvf1760-2-e
set_property BOARD_PART xilinx.com:zcu216:part0:2.0 [current_project]
set_property target_language Verilog [current_project]

# Set IP repository paths
set_property ip_repo_paths $iprepo_dir [current_project]
update_ip_catalog

# Add constraints
# add_files -fileset constrs_1 -norecurse ./constraints.xdc

# Make block design
source ./${design_name}.tcl
