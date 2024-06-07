DESIGN_DIR := $(shell pwd)/block_designs
SCRIPT_DIR := $(shell pwd)/scripts
DESIGNS := $(notdir $(wildcard $(DESIGN_DIR)/*))

.PHONY: all $(DESIGNS) clean clean_all

all: $(DESIGNS)

$(DESIGNS):
	$(MAKE) bd DESIGN=$@
	$(MAKE) bit DESIGN=$@

bd:
	cd $(DESIGN_DIR)/$(DESIGN); \
	vivado -mode batch -source $(SCRIPT_DIR)/make_bd.tcl -notrace -nojournal -nolog -tclargs $(DESIGN)

bit:
	cd $(DESIGN_DIR)/$(DESIGN); \
	vivado -mode batch -source $(SCRIPT_DIR)/make_bit.tcl -notrace -nojournal -nolog -tclargs $(DESIGN)

clean:
	find $(DESIGN_DIR)/$(DESIGN) -type d -name "*_proj" -exec rm -rf {} +
