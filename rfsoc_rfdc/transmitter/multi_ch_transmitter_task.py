from rfsoc_rfdc.throughput_timer import ThroughputTimer
from rfsoc_rfdc.waveform_generator import WaveFormGenerator
from rfsoc_rfdc.overlay_task import OverlayTask
from .tx_channel import TxChannel
from pynq.lib import AxiGPIO
import numpy as np
import time

class MultiChTransmitterTask(OverlayTask):

    def __init__(self, overlay, channel_count=4):
        super().__init__(overlay, name="MultiChTransmitterTask")
        # Throughput timer
        self.timer = ThroughputTimer()
        # Number of DACs controlled by a DMA
        self.channel_count = channel_count
        # Hardware IPs
        self.channel_dma = [
            self.ol.dac_datapath.t230.axi_dma
        ]
        self.channel_fifo_count_ip = [
            AxiGPIO(self.ol.ip_dict['dac_datapath/t230/fifo_count']).channel1
        ]
        # Initialize Tx channels
        self.tx_channels = []

        for ch_idx, _ in enumerate(self.channel_dma):
            self.tx_channels.append(
                TxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.channel_dma[ch_idx],
                    fifo_count_ip=self.channel_fifo_count_ip[ch_idx],
                    debug_mode=True
                )
            )

        # Generate iq samples for a tone
        q_samples = WaveFormGenerator.generate_sine_wave(
            repeat_time=1000, sample_pts=1000)
        i_samples = WaveFormGenerator.generate_no_wave(
            repeat_time=1000, sample_pts=1000)

        # Generate binary sequence
        # q_samples = WaveFormGenerator.generate_binary_seq(
        #     repeat_time=1000, sample_pts=1000)
        # i_samples = WaveFormGenerator.generate_binary_seq(
        #     repeat_time=1000, sample_pts=1000)

        self.multi_ch_iq_samples = self.gen_multi_ch_iq_layout(
            q_samples, i_samples)

    def gen_multi_ch_iq_layout(self, q_samples, i_samples, repeat_times=4):
        multi_ch_q = np.repeat(q_samples, repeat_times)
        multi_ch_i = np.repeat(i_samples, repeat_times)
        multi_ch_layout = np.vstack((multi_ch_q, multi_ch_i))
        multi_ch_layout = multi_ch_layout.T.flatten()
        return multi_ch_layout

    def run(self):
        # Perform data copy
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(self.multi_ch_iq_samples)

        while True:
            # Start timer
            t = time.time_ns()
            # Transfer iq samples for each channel
            for dma in self.tx_channels:
                dma.transfer()
            for dma in self.tx_channels:
                dma.wait()
            # End timer
            elapse = time.time_ns() - t
            self.timer.append(elapse)
            # Calculate average DMA transfer time
            if len(self.timer) > 1000:
                self.timer.get_throughput()