from rfsoc_rfdc.throughput_timer import ThroughputTimer
from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.receiver.rx_channel import RxChannel
from rfsoc_rfdc.plotter.signal_plotter import ComplexSignalPlotter
from rfsoc_rfdc.plotter.fft_plotter import FFTPlotter
from pynq.lib import AxiGPIO
# Don't skip this! You need this line of have PacketGenerator to work
from rfsoc_rfdc.receiver.packet_generator import PacketGenerator
import time
import numpy as np


class MultiChReceiverTask(OverlayTask):
    """Multi-Channel ADC"""

    def __init__(self, overlay, samples_per_axis_stream=8, fifo_size=32768, channel_count=4):
        super().__init__(overlay, name="MultiChReceiverTask")
        # Throughput timer
        self.timer = ThroughputTimer()
        # Number of ADCs controlled by a DMA
        self.channel_count = channel_count
        # Receiver datapath parameters
        self.fifo_size = fifo_size
        self.samples_per_axis_stream = samples_per_axis_stream
        self.packet_size_ratio = 0.66
        self.packet_size = int(self.fifo_size * self.packet_size_ratio)
        # Initialize plotter
        # self.complex_plotter = ComplexSignalPlotter()
        # self.fft_plotter = FFTPlotter(sample_rate=300e6)
        # Hardware IPs
        self.channel_dma = [
            self.ol.adc_datapath.t226.axi_dma
        ]
        self.channel_pkt_generator_ip = [
            self.ol.adc_datapath.t226.adc_packet_generator
        ]
        self.channel_fifo_count_ip = [
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226/fifo_count']).channel1
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

    # TODO: Given a memory layout pulled from FIFO, decode per channel iq samples and return them
    # def get_multi_ch_iq(self, data, repeat_times=4):

    def run(self):
        # Set packet size for all ADC channels and enable each of them
        for pkg_gen in self.channel_pkt_generator_ip:
            pkg_gen.packetsize = self.packet_size
            pkg_gen.enable()

        update_counter = 0
        while True:
            # Start timer
            t = time.time_ns()
            # Receive iq samples for each channel
            for dma in self.rx_channels:
                dma.transfer()
            for dma in self.rx_channels:
                dma.wait()
            # End timer
            elapse = time.time_ns() - t
            self.timer.update(elapse)
            # Calculate average DMA transfer time
            if update_counter > 1000:
                update_counter = 0
                self.timer.get_throughput()
            update_counter = update_counter + 1
            # Only fetch iq samples for the first channel
            q_data = self.rx_channels[0].data[0::self.channel_count*2]
            i_data = self.rx_channels[0].data[1::self.channel_count*2]
            iq_data = i_data + 1j * q_data
            # Plot only the first channel
            # self.complex_plotter.update_plot(iq_data, plot_ratio=0.1)
            # Update the FFT plotter
            # self.fft_plotter.update_plot(iq_data)
