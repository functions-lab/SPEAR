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


class SingleChRxTask(OverlayTask):
    """Single-Channel ADC"""

    def __init__(self, overlay, buff_size=2**18):
        super().__init__(overlay, name="SingleChRxTask")
        # TCP socket
        self.server_config = ("server.local", 1234)
        # Make sure to bind this domain name to the IP address of your ADC sample plotting server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make sure the socket is reusable

        # Receiver datapath parameters
        self.buff_size = buff_size
        # Initialize plotters
        self.complex_plotter = ComplexSignalPlotter()
        dac_samp_rate = ZCU216_CONFIG['DACSampleRate'] / \
            ZCU216_CONFIG['DACInterpolationRate'] * 1e6
        self.fft_plotter = FFTPlotter(sample_rate=dac_samp_rate)

        # DSP related
        self.ofdm_scheme = ZCU216_CONFIG['OFDM_SCHEME']
        self.detect_scheme = ZCU216_CONFIG['DETECTION_SCHEME']

        # Hardware IPs
        self.dma_ip = [
            self.ol.adc_datapath.t226.data_mover_ctrl
        ]
        self.fifo_count_ip = [
            AxiGPIO(
                self.ol.ip_dict['adc_datapath/t226/fifo_count']).channel1
        ]

        # Initialize Rx channels
        self.rx_channels = []

        for ch_idx, _ in enumerate(self.dma_ip):
            self.rx_channels.append(
                RxChannelReal2Iq(
                    channel_id=ch_idx,
                    dma_ip=self.dma_ip[ch_idx],
                    fifo_count_ip=self.fifo_count_ip[ch_idx],
                    target_device=self.ol.ddr4_rx,
                    buff_size=self.buff_size,
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
            target=self.data_logging_handler, args=(iq_data, self.detect_scheme.rx_file))
        # TCP real/imag samples thd
        tcp_thd = threading.Thread(target=self.tcp_handler, args=(iq_data,))

        for thd in [fft_thd, plot_thd, log_thd]:
            thd.start()
        for thd in [fft_thd, plot_thd, log_thd]:
            thd.join()

        elapse = time.time_ns() - start_t
        # logging.info(f"packet handler takes {elapse / 1e9} to complete")

    def run(self):
        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                time.sleep(1)
                # Initiate DMA transfer after 1s
                self.rx_channels[0].transfer()  # Single transfer mode
                # self.rx_channels[0].stream() # Streaming transfer mode
                iq_data = self.rx_channels[0].data
                # IQ sample handler
                self.sample_handler(iq_data)
                # Run DSP pipeline
                config_name = ZCU216_CONFIG['CONFIG_NAME']

                wave_rx = np.load(self.detect_scheme.rx_file)
                try:
                    packet_rx, snr, cfo = self.detect_scheme.proc_rx(wave_rx)
                except Exception:
                    logging.error(f"Fail to detect Rx packet")
                    continue
                evm, ber = self.ofdm_scheme.analyze(
                    packet_rx, plot=self.detect_scheme.path2wave+'/'+config_name+"_const_diagram.png")
                logging.info(
                    f"SNR: {snr:.3f}, CFO: {cfo:.3f}, EVM: {evm:.3f}, BER: {ber:.10f}")
                # Write result to a file
                with open(self.detect_scheme.path2wave+'/'+config_name+"_res.log", 'w') as f:
                    f.write(f"{snr:.3f}, {cfo:.3f}, {evm:.3f}, {ber:.10f}")

            else:
                time.sleep(1)
