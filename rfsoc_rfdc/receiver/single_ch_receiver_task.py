from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.receiver.rx_channel_real2iq import RxChannelReal2Iq
from rfsoc_rfdc.plotter.signal_plotter import ComplexSignalPlotter
from rfsoc_rfdc.plotter.fft_plotter import FFTPlotter
from pynq.lib import AxiGPIO
import numpy as np
# Don't skip this! You need this line of have PacketGenerator to work
from .packet_generator import PacketGenerator


class SingleChReceiverTask(OverlayTask):
    """Single-Channel ADC"""

    def __init__(self, overlay, samples_per_axis_stream=8, fifo_size=32768):
        super().__init__(overlay, name="SingleChReceiverTask")
        # Receiver datapath parameters
        self.fifo_size = fifo_size
        self.samples_per_axis_stream = samples_per_axis_stream
        self.packet_size_ratio = 0.66
        self.packet_size = int(self.fifo_size * self.packet_size_ratio)
        # Initialize plotters
        self.complex_plotter = ComplexSignalPlotter()
        self.fft_plotter = FFTPlotter(sample_rate=100e6)

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
            # Initiate DMA transfer
            self.rx_channels[0].transfer()
            self.rx_channels[0].wait()
            # Receive iq samples
            iq_data = self.rx_channels[0].data
            # Update the complex signal plotter
            self.complex_plotter.update_plot(iq_data, plot_ratio=0.1)
            # Update the FFT plotter
            self.fft_plotter.update_plot(iq_data)
