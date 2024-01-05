from .waveform_generator import WaveFormGenerator

from .overlay_task import OverlayTask
from .iq2real_tx_channel import Iq2RealTxChannel
from pynq.lib import AxiGPIO


class TransmitterTask(OverlayTask):
    """
    A class representing a transmitter task.

    This class is responsible for performing data copy and multi-channel transmission
    using the specified hardware IPs.

    Attributes:
        mode (str): The operating mode of the transmitter task. Can be "repeater" or "real_time".
        dma_ips (list): A list of hardware IPs for data transfer.
        fifo_count_ips (list): A list of hardware IPs for FIFO count.
        fifo_status_ips (list): A list of hardware IPs for FIFO status.
        tx_channels (list): A list of Tx channels for data transfer.
        i_data (numpy.ndarray): The I data for generating IQ samples.
        q_data (numpy.ndarray): The Q data for generating IQ samples.
    """

    def __init__(self, overlay):
        super().__init__(overlay, name="TransmitterTask")
        # Operating mode
        self.mode = "repeater"  # or "real_time"
        # Hardware IPs
        self.dma_ips = [
            self.ol.dac_datapath.t230_dac0.axi_dma,
            self.ol.dac_datapath.t230_dac1.axi_dma,
            self.ol.dac_datapath.t230_dac2.axi_dma,
            self.ol.dac_datapath.t230_dac3.axi_dma
        ]
        self.fifo_count_ips = [
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac0/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac1/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac2/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['dac_datapath/t230_dac3/fifo_count']).channel1
        ]
        self.fifo_status_ips = [
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
        self.tx_channels = []
        for ch_idx, _ in enumerate(self.dma_ips):
            self.tx_channels.append(
                Iq2RealTxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.dma_ips[ch_idx],
                    fifo_count_ip=self.fifo_count_ips[ch_idx],
                    fifo_status_ip=self.fifo_status_ips[ch_idx]
                )
            )
        # Generate iq samples
        self.i_data = WaveFormGenerator.generate_sine_wave(
            repeat_time=1000, sample_pts=1000)
        self.q_data = WaveFormGenerator.generate_cosine_wave(
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
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(self.q_data, self.i_data)

        # Perform multi-channel transmission
        if self.mode == "repeater":
            while True:
                # self.tx_channels[0].transfer()
                # self.tx_channels[1].transfer()
                # self.tx_channels[0].wait()
                # self.tx_channels[1].wait()
                for tx_ch in self.tx_channels:
                    tx_ch.transfer()
                for tx_ch in self.tx_channels:
                    tx_ch.wait()
        else:
            raise ValueError(f"Unrecognized mode: {self.mode}")
