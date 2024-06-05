import logging
import time
from rfsoc_rfdc.overlay_task import OverlayTask


class CmacTask(OverlayTask):
    """Task for configuring CMAC 100G transceiver."""

    def __init__(self, overlay):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.cmac = overlay.cmac_usplus_0

        # Put CMAC in internal Loopback Mode
        self.cmac.internal_loopback = 0

        # Bring up the CMAC Core
        self.cmac.start()

    def run(self):
        while True:
            time.sleep(1)
            logging.info(self.cmac.getStats(False))
