from rfsoc_rfdc.waveform_generator import WaveFormGenerator
from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.transmitter.tx_channel_iq2real import TxChannelIq2Real
from pynq.lib import AxiGPIO
import numpy as np
from rfsoc_rfdc.rfdc import RfDataConverterType
from rfsoc_rfdc.matlab_iq_loader import MatlabIqLoader

class SingleChTransmitterTask(OverlayTask):
    """Single-Channel DAC"""

    def __init__(self, overlay, file_path="./wifi_wave.mat"):
        super().__init__(overlay, name="SingleChTransmitterTask")
        # Waveform file name
        self.file_path = file_path
        # Hardware IPs
        self.dma_ip = [
            self.ol.dac_datapath.t230.axi_dma
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
                    debug_mode=True
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

        # Generate iq samples for a tone
        # self.i_samples = WaveFormGenerator.generate_sine_wave(
        #     repeat_time=1000, sample_pts=1000)
        # self.q_samples = WaveFormGenerator.generate_no_wave(
        #     repeat_time=1000, sample_pts=1000)

        # Generate binary sequence
        # self.i_samples = WaveFormGenerator.generate_binary_seq(
        #     repeat_time=1000, sample_pts=1000)
        # self.q_samples = WaveFormGenerator.generate_no_wave(
        #     repeat_time=1000, sample_pts=1000)

        # Generate iq samples for a Zadoff-Chu sequence
        # self.i_samples, self.q_samples = WaveFormGenerator.generate_zadoff_chu_wave(
        #     repeat_time=1000, sample_pts=1000)

    def run(self):
        # Perform data copy
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(i_buff=self.i_samples, q_buff=self.q_samples)

        while True: 
            # Initiate DMA transfer
            self.tx_channels[0].transfer()
            self.tx_channels[0].wait()
