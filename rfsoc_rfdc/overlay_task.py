import numpy as np
import threading
from abc import ABC, abstractmethod
from rfsoc_rfdc.rfsoc_overlay import RFSoCOverlay
from pynq import allocate
import os
import time
from pynq.lib import AxiGPIO


class OverlayTask(ABC):
    """
    An abstract base class for creating tasks to be run on an RFSoCOverlay.

    Attributes:
        ol (RFSoCOverlay): An instance of RFSoCOverlay to operate on.
        task_name (str): The name of the task.
        thread (threading.Thread): The thread on which the task runs.

    Methods:
        run: An abstract method to define the task's behavior.
        start: Starts the task's thread.
        join: Waits for the task's thread to complete.
    """

    def __init__(self, overlay, name="OverlayTask"):
        """
        Initializes the OverlayTask with a given RFSoCOverlay instance and task name.

        Args:
            overlay (RFSoCOverlay): The RFSoCOverlay instance to operate on.
            name (str): The name of the task. Defaults to "OverlayTask".

        Raises:
            TypeError: If the overlay is not an instance of RFSoCOverlay.
        """
        if not isinstance(overlay, RFSoCOverlay):
            raise TypeError("This task is not an RFSoCOverlay instance.")
        self.ol = overlay
        self.task_name = name
        self.thread = threading.Thread(target=self.run)

    @abstractmethod
    def run(self):
        """
        Abstract method that defines the task's behavior. Must be implemented by subclasses.
        """
        pass

    def start(self):
        """
        Starts the task's thread, causing it to run concurrently.
        """
        self.thread.start()

    def join(self):
        """
        Blocks until the task's thread terminates.
        """
        self.thread.join()


class BlinkLedTask(OverlayTask):
    """
    A task that blinks LEDs on an RFSoCOverlay.

    Inherits from OverlayTask.

    Attributes:
        gleds (AxiGPIO): AxiGPIO instance for controlling green LEDs.
        red_leds (AxiGPIO): AxiGPIO instance for controlling red LEDs.

    Methods:
        run: Implements the LED blinking behavior.
    """

    def __init__(self, overlay):
        """
        Initializes the BlinkLedTask with a given RFSoCOverlay instance.

        Args:
            overlay (RFSoCOverlay): The RFSoCOverlay instance to operate on.
        """
        super().__init__(overlay, name="BlinkLedTask")
        self.gleds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel1
        self.red_leds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel2
        for leds in [self.red_leds, self.gleds]:
            leds.setdirection("out")
            leds.setlength(8)

    def run(self):
        """
        Runs the LED blinking task. Alternates the LEDs between on and off states at a fixed interval.
        """
        interval = 0.3
        while True:
            self.gleds.write(0xff, 0xff)  # Turn on all green LEDs
            time.sleep(interval)
            self.gleds.write(0x00, 0xff)  # Turn off all green LEDs
            time.sleep(interval)
