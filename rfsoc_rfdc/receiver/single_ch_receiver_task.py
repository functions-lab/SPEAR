from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.receiver.rx_channel_real2iq import RxChannelReal2Iq
from rfsoc_rfdc.plotter.signal_plotter import ComplexSignalPlotter
from rfsoc_rfdc.plotter.fft_plotter import FFTPlotter
from pynq.lib import AxiGPIO
import numpy as np
# Don't skip this! You need this line of have PacketGenerator to work
from .packet_generator import PacketGenerator
import logging
import pickle
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
import socket
import time
import threading


class SingleChReceiverTask(OverlayTask):
    """Single-Channel ADC"""

    def __init__(self, overlay, samples_per_axis_stream=8, fifo_size=32768):
        super().__init__(overlay, name="SingleChReceiverTask")
        # TCP socket
        self.server_config = ("server.local", 1234)
        # Make sure to bind this domain name to the IP address of your ADC sample plotting server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make sure the socket is reusable

        # Receiver datapath parameters
        self.fifo_size = fifo_size
        self.samples_per_axis_stream = samples_per_axis_stream
        self.packet_size = int(32768)
        # Initialize plotters
        self.complex_plotter = ComplexSignalPlotter()
        dac_samp_rate = ZCU216_CONFIG['DACSampleRate'] / \
            ZCU216_CONFIG['DACInterpolationRate'] * 1e6
        self.fft_plotter = FFTPlotter(sample_rate=dac_samp_rate)

        # Hardware IPs
        self.dma_ip = [
            self.ol.adc_datapath.t226.data_mover_ctrl
        ]
        self.pkt_generator_ip = [
            # self.ol.adc_datapath.t226.adc_packet_generator
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
                    debug_mode=False
                )
            )

    def __del__(self):
        self.sock.close()

    def data_logging_handler(self, iq_data, file_name):
        np.save(file_name, iq_data)

    def tcp_reconnect(self, net_config):
        new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make sure the socket is reusable
        try:
            new_sock.connect(net_config)
        except socket.error as e:
            return None
        return new_sock

    def tcp_handler(self, samples):
        samples = np.array(samples, dtype=np.csingle)  # Convert to numpy array
        try:
            byte_data = pickle.dumps(samples)
            self.sock.sendall(byte_data)
        except socket.error as e:
            for _ in range(5):
                s = self.tcp_reconnect(self.server_config)
                if s is not None:
                    self.sock = s
                    break

    def sample_handler(self, iq_data):
        start_t = time.time_ns()

        # Time plot thd
        plot_thd = threading.Thread(
            target=self.complex_plotter.update_plot, args=(iq_data, 0.01))
        # FFT plot thd
        fft_thd = threading.Thread(
            target=self.fft_plotter.update_plot, args=(iq_data,))
        # Save IQ samples to file thd
        log_thd = threading.Thread(
            target=self.data_logging_handler, args=(iq_data, "./iq_data.npy"))
        # TCP real/imag samples thd
        tcp_thd = threading.Thread(target=self.tcp_handler, args=(iq_data,))

        for thd in [fft_thd, plot_thd]:
            thd.start()
        for thd in [fft_thd, plot_thd]:
            thd.join()

        elapse = time.time_ns() - start_t
        # logging.info(f"packet handler takes {elapse / 1e9} to complete")

    def run(self):
        # Set packet size for all ADC channels and enable each of them
        # for pkg_gen in self.pkt_generator_ip:
        #     pkg_gen.packetsize = self.packet_size
        #     pkg_gen.enable()

        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                # Initiate DMA transfer
                self.rx_channels[0].transfer()
                iq_data = self.rx_channels[0].data
                time.sleep(1)
                # IQ sample handler
                self.sample_handler(iq_data)
            else:
                time.sleep(1)
