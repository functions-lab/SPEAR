from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.transmitter.tx_channel import TxChannel
from pynq.lib import AxiGPIO
import numpy as np
import time

from rfsoc_rfdc.rfdc import MyRFdcType
from rfsoc_rfdc.iq_loader import MatlabIqLoader


class MultiChTxTask(OverlayTask):

    def __init__(self, overlay, channel_count=4):
        super().__init__(overlay, name="MultiChTxTask")
        # Number of DACs controlled by a DMA
        self.channel_count = channel_count
        # Hardware IPs
        self.channel_dma = [
            self.ol.dac_datapath.t230.data_mover_ctrl
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
                    debug_mode=False
                )
            )

        # Initialize MatlabIqLoader
        self.matlab_loader = MatlabIqLoader(
            file_path="./wave_files/Tx_1.mat", key="wave")
        self.matlab_loader.load_matlab_waveform()

        # Scale the waveform
        self.matlab_loader.scale_waveform(
            MyRFdcType.DAC_MIN_SCALE, MyRFdcType.DAC_MAX_SCALE)
        i_samples, q_samples = self.matlab_loader.get_iq_samples(
            repeat_times=1)

        # Generate iq samples for a tone
        # q_samples = WaveFormGenerator.generate_sine_wave(
        #     repeat_time=1000, sample_pts=1000)
        # i_samples = WaveFormGenerator.generate_no_wave(
        #     repeat_time=1000, sample_pts=1000)

        # Generate binary sequence
        # q_samples = WaveFormGenerator.generate_binary_seq(
        #     repeat_time=1000, sample_pts=1000)
        # i_samples = WaveFormGenerator.generate_binary_seq(
        #     repeat_time=1000, sample_pts=1000)

        # Generate iq samples for a Zadoff-Chu sequence
        # i_samples, q_samples = WaveFormGenerator.generate_zadoff_chu_wave(
        #     repeat_time=1000, sample_pts=1000)

        self.multi_ch_iq_samples = self.gen_multi_ch_iq_layout(
            i_samples, q_samples, repeat_times=self.channel_count)

    def gen_multi_ch_iq_layout(self, i_samples, q_samples, repeat_times=4):
        multi_ch_i = np.repeat(i_samples, repeat_times)
        multi_ch_q = np.repeat(q_samples, repeat_times)
        multi_ch_layout = np.vstack((multi_ch_i, multi_ch_q))
        multi_ch_layout = multi_ch_layout.T.flatten()
        return multi_ch_layout

    def run(self):
        # Perform data copy
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(self.multi_ch_iq_samples)

        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                # Transfer iq samples for each channel
                for dma in self.tx_channels:
                    dma.transfer()
                time.sleep(1)
            else:
                for dma in self.tx_channels:
                    dma.tx_dma.stop()
                time.sleep(1)
