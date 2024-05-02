from .waveform_generator import WaveFormGenerator

from .overlay_task import OverlayTask
from .tx_channel import TxChannel
from pynq.lib import AxiGPIO
import numpy as np
import time

from .rfdc import RfDataConverterType


class MultiChannelTransmitterTask(OverlayTask):

    def __init__(self, overlay, channel_count=4):
        super().__init__(overlay, name="MultiChannelTransmitterTask")
        # Running counter
        self.timer = []
        # Number of DACs controlled by a DAC
        self.channel_count = channel_count
        # Hardware IPs
        self.channel_dma = [
            self.ol.dac_datapath.t230.axi_dma
        ]

        self.channel_fifo_count_ip = [
            AxiGPIO(self.ol.ip_dict['dac_datapath/t230/fifo_count']).channel1
        ]

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

        # Generate I/Q samples for a tone
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

        # Perform multi-channel transmission
        while True:
            t = time.time_ns()
            for dma in self.tx_channels:
                dma.transfer()
            for dma in self.tx_channels:
                dma.wait()
            elapse = time.time_ns() - t
            self.timer.append(elapse)

            # Calculate average time
            if len(self.timer) > 1000:
                # Only get the last 3 samples
                avg_time = np.mean(self.timer[-3:]) / 10**9
                freq = 1 / avg_time
                print(
                    f"[MultiChannelTransmitterTask] Average time (s): {avg_time:.3f}, freq (hz) {freq:.3f}")
                self.timer = []
