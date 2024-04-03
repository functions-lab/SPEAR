from .waveform_generator import WaveFormGenerator

from .overlay_task import OverlayTask
from .iq2real_tx_channel import Iq2RealTxChannel
from pynq.lib import AxiGPIO
import numpy as np
from .rfdc import RfDataConverterType
from .matlab_iq_loader import MatlabIqLoader


class TransmitterTask(OverlayTask):
    """
    A class representing a transmitter task.

    This class is responsible for performing data copy and multi-channel transmission
    using the specified hardware IPs.
    """

    def __init__(self, overlay, file_path="./wifi_wave.mat"):
        super().__init__(overlay, name="TransmitterTask")
        # Waveform file name
        self.file_path = file_path
        # Operating mode
        self.mode = "repeater"  # or "real_time"
        # Hardware IPs
        self.t230_dma_ips = [
            self.ol.dac_datapath.t230_dac0.axi_dma
        ]

        self.t230_fifo_count_ips = [
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac0/fifo_count']).channel1
        ]

        # Initialize Tx channels
        self.t230_tx_channels = []

        for ch_idx, _ in enumerate(self.t230_dma_ips):
            self.t230_tx_channels.append(
                Iq2RealTxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.t230_dma_ips[ch_idx],
                    fifo_count_ip=self.t230_fifo_count_ips[ch_idx],
                    debug_mode=False
                )
            )

        # Initialize MatlabIqLoader
        self.matlab_loader = MatlabIqLoader(
            file_path=self.file_path, key="wave")
        self.matlab_loader.load_matlab_waveform()

        # Set the range for full scale
        range_min, range_max = RfDataConverterType.DAC_MIN_SCALE, RfDataConverterType.DAC_MAX_SCALE

        # Scale the waveform
        self.matlab_loader.scale_waveform(range_min, range_max)
        self.i_samples, self.q_samples = self.matlab_loader.get_iq_samples()

        # Generate I/Q samples for a tone
        # self.i_samples = WaveFormGenerator.generate_sine_wave(
        #     repeat_time=1000, sample_pts=10000)
        # self.q_samples = WaveFormGenerator.generate_no_wave(
        #     repeat_time=1000, sample_pts=10000)

        # Generate I/Q samples for a Zadoff-Chu sequence
        # self.i_samples, self.q_samples = WaveFormGenerator.generate_zadoff_chu_wave(
        #     repeat_time=1000, sample_pts=1000)

    def run(self):
        """
        Run the transmitter task.

        This method performs data copy and multi-channel transmission based on the
        specified operating mode.

        Raises:
            ValueError: If the operating mode is unrecognized.
        """

        # Perform data copy
        for tx_ch in self.t230_tx_channels:
            tx_ch.data_copy(i_buff=self.i_samples, q_buff=self.q_samples)

        # Perform multi-channel transmission
        if self.mode == "repeater":
            while True:
                self.t230_tx_channels[0].transfer()
                self.t230_tx_channels[0].wait()
        else:
            raise ValueError(f"Unrecognized mode: {self.mode}")
