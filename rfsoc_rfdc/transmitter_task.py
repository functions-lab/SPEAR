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

        # Initialize Tx channels
        self.t230_tx_channels = []

        for ch_idx, _ in enumerate(self.t230_dma_ips):
            self.t230_tx_channels.append(
                Iq2RealTxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.t230_dma_ips[ch_idx],
                    fifo_count_ip=self.t230_fifo_count_ips[ch_idx],
                    debug_mode=True
                )
            )

        # Read from matlab waveform
        wave = scipy.io.loadmat('./wifi_wave.mat')['wave']

        # Find the min and max of the real and imaginary parts
        min_real, max_real, min_imag, max_imag = np.min(wave.real), np.max(
            wave.real), np.min(wave.imag), np.max(wave.imag)

        # Find a proper scale factor to fit the real and imaginary parts within the range of np.int16
        scale = np.max([np.abs(max_real), np.abs(max_imag),
                       np.abs(min_real), np.abs(min_imag)])

        # Set the proper range for full scale
        range_min, range_max = RfDataConverterType.DAC_MIN_SCALE, RfDataConverterType.DAC_MAX_SCALE

        # Scaling the real and imaginary parts to fit within the range of np.int16
        scaled_real = np.int16(
            np.interp(wave.real, (-scale, scale), (range_min, range_max)))
        scaled_imag = np.int16(
            np.interp(wave.imag, (-scale, scale), (range_min, range_max)))

        scaled_real = np.squeeze(scaled_real)
        scaled_imag = np.squeeze(scaled_imag)

        self.i_samples = scaled_real
        self.q_samples = scaled_imag

        # Generate I/Q samples for a tone
        # self.i_samples = WaveFormGenerator.generate_cosine_wave(
        #     repeat_time=1000, sample_pts=1000)
        # self.q_samples = WaveFormGenerator.generate_sine_wave(
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
                self.t230_tx_channels[1].transfer()
                self.t230_tx_channels[2].transfer()
                self.t230_tx_channels[3].transfer()

                self.t230_tx_channels[0].wait()
                self.t230_tx_channels[1].wait()
                self.t230_tx_channels[2].wait()
                self.t230_tx_channels[3].wait()

        else:
            raise ValueError(f"Unrecognized mode: {self.mode}")
