from .overlay_task import OverlayTask
from .rx_channel_real2iq import RxChannelReal2Iq
from .adc_data_plotter import AdcDataPlotter
from .adc_fft_plotter import AdcFFTPlotter
from pynq.lib import AxiGPIO
import numpy as np
# Don't skip this! You need this line of have PacketGenerator to work
from .packet_generator import PacketGenerator


class SingleChReceiverTask(OverlayTask):
    """Single channel ADC"""

    def __init__(self, overlay, samples_per_axis_stream=8, fifo_size=32768):
        super().__init__(overlay, name="SingleChReceiverTask")
        # Receiver datapath parameters
        self.fifo_size = fifo_size
        self.samples_per_axis_stream = samples_per_axis_stream
        self.packet_size_ratio = 0.66
        self.packet_size = int(self.fifo_size * self.packet_size_ratio)
        # Initialize plotter
        self.sample_plotter = AdcDataPlotter()
        self.sample_plotter.config_title()
        self.fft_plotter = AdcFFTPlotter(sample_rate=100e6)

        # Hardware IPs
        self.dma_ip = [
            self.ol.adc_datapath.t226.axi_dma
        ]
        self.pkt_generator_ip = [
            self.ol.adc_datapath.t226.adc_packet_generator
        ]
        self.fifo_count_ip = [
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226/fifo_count']).channel1
        ]

        # Initialize Rx channels
        self.rx_channels = []

        for ch_idx, _ in enumerate(self.dma_ip):
            buffer_margin = 50  # Magic number! Necessary
            self.rx_channels.append(
                RxChannelReal2Iq(
                    channel_id=ch_idx,
                    dma_ip=self.dma_ip[ch_idx],
                    fifo_count_ip=self.fifo_count_ip[ch_idx],
                    buff_size=self.packet_size * self.samples_per_axis_stream + buffer_margin,
                    debug_mode=True
                )
            )

    def run(self):
        # Set packet size for all ADC channels and enable each of them
        for pkg_gen in self.pkt_generator_ip:
            pkg_gen.packetsize = self.packet_size
            pkg_gen.enable()

        while True:
            # Receive data and convert to I/Q format
            self.rx_channels[0].transfer()
            self.rx_channels[0].wait()
            i_data = self.rx_channels[0].i_data
            q_data = self.rx_channels[0].q_data

            # Update the plot with I/Q data, plot only 10% of captured data
            # self.sample_plotter.update_plot(i_data, q_data, display_ratio=0.1)
            self.fft_plotter.update_plot(i_data, q_data)
