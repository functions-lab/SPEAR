from .waveform_generator import WaveFormGenerator

from .overlay_task import OverlayTask
from .iq2real_tx_channel import Iq2RealTxChannel
from pynq.lib import AxiGPIO
import scipy.io
import numpy as np
from .rfdc import RfDataConverterType


class TransmitterTask(OverlayTask):
    """
    A class representing a transmitter task.

    This class is responsible for performing data copy and multi-channel transmission
    using the specified hardware IPs.
    """

    def __init__(self, overlay):
        super().__init__(overlay, name="TransmitterTask")
        # Operating mode
        self.mode = "repeater"  # or "real_time"
        # Hardware IPs
        self.t230_dma_ips = [
            self.ol.dac_datapath.t230_dac0.axi_dma,
            self.ol.dac_datapath.t230_dac1.axi_dma,
            self.ol.dac_datapath.t230_dac2.axi_dma,
            self.ol.dac_datapath.t230_dac3.axi_dma
        ]

        self.t230_fifo_count_ips = [
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac0/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac1/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac2/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac3/fifo_count']).channel1
        ]

        self.t230_fifo_status_ips = [
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac0/fifo_full']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac1/fifo_full']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac2/fifo_full']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac3/fifo_full']).channel1
        ]
        # Initialize Tx channels
        self.t230_tx_channels = []

        for ch_idx, _ in enumerate(self.t230_dma_ips):
            self.t230_tx_channels.append(
                Iq2RealTxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.t230_dma_ips[ch_idx],
                    fifo_count_ip=self.t230_fifo_count_ips[ch_idx],
                    fifo_status_ip=self.t230_fifo_status_ips[ch_idx]
                )
            )

        # Read from matlab waveform
        wave = scipy.io.loadmat('./wifi_wave.mat')['wave']
        real = wave.real / 4 * (2**15 - 1)
        imag = wave.imag / 4 * (2**15 - 1)
        self.i = np.repeat(imag.astype(RfDataConverterType.DATA_PATH_DTYPE), 1)
        self.r = np.repeat(real.astype(RfDataConverterType.DATA_PATH_DTYPE), 1)

        # Generate iq samples
        self.i_data = WaveFormGenerator.generate_cosine_wave(
            repeat_time=1000, sample_pts=1000)
        self.q_data = WaveFormGenerator.generate_sine_wave(
            repeat_time=1000, sample_pts=1000)

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
            tx_ch.data_copy(self.q_data, self.i_data)

        # Perform multi-channel transmission
        if self.mode == "repeater":
            while True:
                self.t230_tx_channels[0].transfer()
                self.t230_tx_channels[1].transfer()
                self.t230_tx_channels[2].transfer()
                self.t230_tx_channels[3].transfer()

                self.t230_tx_channels[0].wait()
                self.t230_tx_channels[1].wait()
                self.t230_tx_channels[2].wait()
                self.t230_tx_channels[3].wait()

        else:
            raise ValueError(f"Unrecognized mode: {self.mode}")
