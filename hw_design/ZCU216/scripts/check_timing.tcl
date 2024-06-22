set iprepo_dir ./../../../ip/iprepo

if { $argc < 1 } {
    puts "Error: design_name not specified."
    exit 1
}
set design_name [lindex $argv 0]
set overlay_name "${design_name}_proj"
set report_path ./${overlay_name}/${overlay_name}.runs/impl_1/${design_name}_wrapper_timing_summary_routed.rpt

# Open timing report
set fd [open ${report_path} r]

set timing_met 0
while { [gets $fd line] >= 0 } {
    if [string match {All user specified timing constraints are met.} $line]  { 
        set timing_met 1
        break
    }
}
if {$timing_met == 0} {
    puts "ERROR: ${overlay_name} bitstream generation does not meet timing."
    exit 1
}
puts "Timing constraints of ${design_name} are met."