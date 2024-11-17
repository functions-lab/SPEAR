## SPEAR for ZCU216

The `./block_designs` directory contains the FPGA design we developed over time. The `../ip` directory contains the custom hardware IP that can be shared across different RFSoC boards. The `./scripts` directory contains tcl scripts to generate block designs and compile bitstreams.

The experiments presented in the paper can be reproduced by running the following command at this directory.

- Generate block designs and bitstreams for Config 1
```
make bd DESIGN=rfsoc_rfdc_v39_100M; make bit DESIGN=rfsoc_rfdc_v39_100M;
```
- Generate block designs and bitstreams for Config 2
```
make bd DESIGN=rfsoc_rfdc_v39_NB; make bit DESIGN=rfsoc_rfdc_v39_NB;
```
- Generate block designs and bitstreams for Config 3
```
make bd DESIGN=rfsoc_rfdc_v39; make bit DESIGN=rfsoc_rfdc_v39;
```
