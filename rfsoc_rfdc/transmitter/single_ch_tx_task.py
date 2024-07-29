from rfsoc_rfdc.waveform_generator import WaveFormGenerator
from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.transmitter.tx_channel_iq2real import TxChannelIq2Real
from pynq.lib import AxiGPIO
import numpy as np
import time
from rfsoc_rfdc.rfdc import MyRFdcType
from rfsoc_rfdc.iq_loader import MatlabIqLoader, NumpyIqLoader

from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class SingleChTxTask(OverlayTask):
    """Single-Channel DAC"""

    def __init__(self, overlay, file_path="./wifi_wave.mat"):
        super().__init__(overlay, name="SingleChTxTask")
        # Waveform file name
        self.file_path = file_path
        # Hardware IPs
        self.dma_ip = [
            self.ol.dac_datapath.t230.data_mover_ctrl
        ]
        self.fifo_count_ip = [
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230/fifo_count']).channel1
        ]

        # Initialize Tx channels
        self.tx_channels = []

        for ch_idx, _ in enumerate(self.dma_ip):
            self.tx_channels.append(
                TxChannelIq2Real(
                    channel_id=ch_idx,
                    dma_ip=self.dma_ip[ch_idx],
                    fifo_count_ip=self.fifo_count_ip[ch_idx],
                    debug_mode=False
                )
            )

        # Load IQ samples from a .npy or .mat file
        if self.file_path.endswith('.npy'):
            loader = NumpyIqLoader(self.file_path)
            self.i_samples, self.q_samples = loader.get_iq()
        elif self.file_path.endswith('.mat'):
            loader = MatlabIqLoader(self.file_path, key='wave')
            self.i_samples, self.q_samples = loader.get_iq()
        else:
            raise Exception(f"File {self.file_path} is not supported.")

        # Generate testing sequence
        # ten_peaks = WaveFormGenerator.generate_ten_sine()
        # self.i_samples, self.q_samples = ten_peaks, ten_peaks

    def run(self):
        # Perform data copy
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(i_buff=self.i_samples, q_buff=self.q_samples)

        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                # Streaming IQ samples
                self.tx_channels[0].stream()
                time.sleep(1)
            else:
                self.tx_channels[0].tx_dma.stop()
                time.sleep(1)
