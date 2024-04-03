from .overlay_task import OverlayTask
from .real2iq_rx_channel import Real2IqRxChannel
from .adc_data_plotter import AdcDataPlotter
from pynq.lib import AxiGPIO
# Don't skip this! You need this line of have PacketGenerator to work
from .packet_generator import PacketGenerator
import time


class ReceiverTask(OverlayTask):
    def __init__(self, overlay, buffer_size=1024):
        super().__init__(overlay, name="ReceiverTask")
        self.buffer_size = buffer_size

        # Hardware IPs
        self.t226_dma_ips = [
            self.ol.adc_datapath.t226_adc0.axi_dma
        ]
        self.t226_pkt_generator_ips = [
            self.ol.adc_datapath.t226_adc0.axis_packet_generator
        ]
        self.t226_fifo_count_ips = [
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226_adc0/fifo_count']).channel1
        ]

        # Initialize Rx channels
        self.t226_rx_channels = []

        for ch_idx, _ in enumerate(self.t226_dma_ips):
            self.t226_rx_channels.append(
                Real2IqRxChannel(
                    channel_id=ch_idx,
                    dma_ip=self.t226_dma_ips[ch_idx],
                    fifo_count_ip=self.t226_fifo_count_ips[ch_idx],
                    buff_size=self.buffer_size,
                    debug_mode=True
                )
            )

        # Initialize plotter
        self.plotter = AdcDataPlotter()

    def run(self):
        for pkg_gen in self.t226_pkt_generator_ips:
            pkg_gen.packetsize = 128
        pkg_gen.enable()

        while True:
            # Receive data and convert to I/Q format
            self.t226_rx_channels[0].transfer()
            self.t226_rx_channels[0].wait()
            i_data = self.t226_rx_channels[0].i_data
            q_data = self.t226_rx_channels[0].q_data
            # # Update the plot with I/Q data
            self.plotter.update_plot(i_data, q_data)

            pkg_count_ip = AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226_adc0/fifo_count']).channel2

            counter = pkg_count_ip.read()

            pkt_gen_ip = self.ol.adc_datapath.t226_adc0.axis_packet_generator
            count, status = pkt_gen_ip._count, pkt_gen_ip.status()
            print(
                f"accumulate count {count}, status {status}, counter {counter}")

            time.sleep(1)
