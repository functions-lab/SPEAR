import numpy as np
import threading
from abc import ABC, abstractmethod
from rfsoc_rfdc.rfsoc_overlay import RFSoCOverlay
from pynq import allocate
import os
import time
from pynq.lib import AxiGPIO

TASK_STATE = {
    "IDLE": 0,
    "RUNNING": 1,
    "PAUSE": 2,
    "STOP": 3
}


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
        self.task_state = TASK_STATE['IDLE']
        self.thread = threading.Thread(target=self.run)

    @abstractmethod
    def run(self):
        """
        Abstract method that defines the task's behavior. Must be implemented by subclasses.
        """
        pass

    def start(self):
        """Starts the task's thread, causing it to run concurrently"""
        self.thread.start()
        self.task_state = TASK_STATE['RUNNING']

    def pause(self):
        """Pause task execution by changing task state"""
        if self.task_state != TASK_STATE['RUNNING']:
            raise Exception(f"Task is not running")
        self.task_state = TASK_STATE['PAUSE']

    def resume(self):
        """Resume task execution by changing task state"""
        if self.task_state != TASK_STATE['PAUSE']:
            raise Exception(f"Task is not paused")
        self.task_state = TASK_STATE['RUNNING']

    def stop(self):
        """Stop task execution"""
        self.task_state = TASK_STATE['STOP']
        self.thread.join()

    def join(self):
        """Blocks until the task's thread terminates"""
        self.thread.join()


class DaemonTask(ABC):

    @abstractmethod
    def generate_memory(self):
        pass


class BlinkLedTask(OverlayTask):
    """
    A task that blinks LEDs on an RFSoCOverlay.

    Inherits from OverlayTask.

    Attributes:
        green_leds (AxiGPIO): AxiGPIO instance for controlling green LEDs.
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
        self.green_leds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel1
        self.red_leds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel2
        for leds in [self.red_leds, self.green_leds]:
            leds.setdirection("out")
            leds.setlength(8)

    def run(self):
        """
        Runs the LED blinking task. Alternates the LEDs between on and off states at a fixed interval.
        """
        interval = 0.3
        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                self.green_leds.write(0xff, 0xff)  # Turn on all green LEDs
                time.sleep(interval)
                self.green_leds.write(0x00, 0xff)  # Turn off all green LEDs
                time.sleep(interval)
