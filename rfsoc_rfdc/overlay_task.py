import numpy as np
import threading
from abc import ABC, abstractmethod


from .rfsoc_overlay import RFSoCOverlay

from pynq import allocate

import os
import time
from pynq.lib import AxiGPIO


class OverlayTask(ABC):
    def __init__(self, overlay, name="OverlayTask"):
        if not isinstance(overlay, RFSoCOverlay):
            raise TypeError("This task is not an RFSoCOverlay instance.")
        self.ol = overlay
        self.task_name = name
        self.thread = threading.Thread(target=self.run)

    @abstractmethod
    def run(self):
        pass

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()


class BlinkLedTask(OverlayTask):

    def __init__(self, overlay):
        super().__init__(overlay, name="BlinkLedTask")
        self.gleds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel1
        self.red_leds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel2
        for leds in [self.red_leds, self.gleds]:
            leds.setdirection("out")
            leds.setlength(8)

    def run(self):
        interval = 0.3
        while True:
            self.gleds.write(0xff, 0xff)
            time.sleep(interval)
            self.gleds.write(0x00, 0xff)
            time.sleep(interval)
