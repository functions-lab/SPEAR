from .overlay_task import OverlayTask
from .rx_channel import RxChannel
from .adc_data_plotter import AdcDataPlotter
from pynq.lib import AxiGPIO
# Don't skip this! You need this line of have PacketGenerator to work
from .packet_generator import PacketGenerator
import time


class MultiChannelReceiverTask(OverlayTask):
    def __init__(self, overlay, samples_per_axis_stream=8, fifo_size=32768):
        super().__init__(overlay, name="MultiChannelReceiverTask")
        # Receiver datapath parameters
        self.fifo_size = fifo_size
        self.samples_per_axis_stream = samples_per_axis_stream
        self.packet_size_ratio = 0.66
        self.packet_size = int(self.fifo_size * self.packet_size_ratio)
        # Initialize plotter
        self.plotter = AdcDataPlotter()
        self.plotter.config_title()

        # Hardware IPs
        self.channel_dma = [
            self.ol.adc_datapath.t226.axi_dma,
            self.ol.adc_datapath.t227.axi_dma
        ]
        self.channel_pkt_generator_ip = [
            self.ol.adc_datapath.t226.adc_packet_generator,
            self.ol.adc_datapath.t227.adc_packet_generator
        ]
        self.channel_fifo_count_ip = [
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226/fifo_count']).channel1,
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t227/fifo_count']).channel1
        ]

        # Initialize Rx channels
        self.rx_channels = []

        for ch_idx, _ in enumerate(self.channel_dma):
            buffer_margin = 50  # Magic number! Necessary
            self.rx_channels.append(
                RxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.channel_dma[ch_idx],
                    fifo_count_ip=self.channel_fifo_count_ip[ch_idx],
                    buff_size=self.packet_size * self.samples_per_axis_stream + buffer_margin,
                    debug_mode=True
                )
            )
    # TODO: Given a memory layout pulled from FIFO, decode per channel I/Q samples and return them
    # def get_multi_ch_iq(self, data, repeat_times=4):

    def run(self):
        # Set packet size for all ADC channels and enable each of them
        for pkg_gen in self.channel_pkt_generator_ip:
            pkg_gen.packetsize = self.packet_size
            pkg_gen.enable()

        while True:
            # Receive data and convert to I/Q format
            for dma in self.rx_channels:
                dma.transfer()
            for dma in self.rx_channels:
                dma.wait()

            # Data plotting
            for ch in self.rx_channels:
                data = ch.data
                # self.plotter.update_plot(i_data, q_data, display_ratio=0.1)
