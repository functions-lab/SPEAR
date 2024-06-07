all: rfsoc4x2 zcu216 tarball

zcu216:
	$(MAKE) -C ZCU216/

rfsoc4x2:
	$(MAKE) -C RFSoC4x2/

tarball:
	tar -czvf hw_design.tar.gz .
