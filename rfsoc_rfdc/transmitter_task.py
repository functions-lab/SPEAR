import numpy as np

from .waveform_generator import WaveFormGenerator

from .overlay_task import OverlayTask

from pynq import allocate

from pynq.lib import AxiGPIO
from pynq import DefaultIP


class TransmitterTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="TransmitterTask")
        # Channels
        self.tx_dma = self.ol.dac_datapath.t230_dac0.axi_dma

        # FIFO control
        self.fifo_count = AxiGPIO(
            self.ol.ip_dict['dac_datapath/t230_dac0/fifo_count']).channel1

        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

        self.fifo_full = AxiGPIO(
            self.ol.ip_dict['dac_datapath/t230_dac0/fifo_full']).channel2
        self.fifo_full.setdirection("in")
        self.fifo_full.setlength(1)

        # Initialize WaveForm class
        self.wg = WaveFormGenerator()

        # Generate testing waveform (e.g., sine wave)
        self.seq = self.wg.generate_sine_wave(
            repeat_time=1000, sample_pts=1000)

    def get_fifo_status(self):
        a = self.fifo_count.read()
        b = self.fifo_full.read()
        return a, b

    def run(self):

        self.tx_buff = allocate(shape=(self.seq.shape[0],), dtype=np.int16)
        self.tx_buff[:] = self.seq

        while True:
            count, status = self.get_fifo_status()
            # print("FIFO count: ", count, "FIFO is_full: ", status)
            self.tx_dma.sendchannel.transfer(self.tx_buff)
            self.tx_dma.sendchannel.wait()  # blocking wait
