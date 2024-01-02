import numpy as np

from .overlay_task import OverlayTask
from .recv_plotter import RecvDataPlotter
import matplotlib.pyplot as plt

from pynq import allocate
import time
from pynq.lib import AxiGPIO


class ReceiverTask(OverlayTask):
    def __init__(self, overlay, num_of_pts_plotted=512, buffer_size=512):
        super().__init__(overlay, name="ReceiverTask")
        self.rx_dma = self.ol.axi_dma_adc2
        self.buffer_size = buffer_size
        self.rx_buff = allocate(shape=(self.buffer_size,), dtype=np.uint16)
        self.plotter = RecvDataPlotter(num_of_pts_plotted)

    def run(self):
        recv_ch = self.rx_dma.recvchannel
        while True:
            try:
                prev_time = time.time_ns()

                recv_ch.transfer(self.rx_buff)
                recv_ch.wait()

                # Update the plot using the new DataPlotter class
                self.plotter.update_plot(self.rx_buff)

                plt.pause(0.001)  # Still needed to update the plot

            except Exception as e:
                print("Get the info from DMA registers",
                      self.rx_dma.register_map)
                print(e)
