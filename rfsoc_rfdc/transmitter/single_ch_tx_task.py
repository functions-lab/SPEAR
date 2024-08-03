from rfsoc_rfdc.waveform_generator import WaveFormGenerator
from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.transmitter.tx_channel_iq2real import TxChannelIq2Real
from pynq.lib import AxiGPIO
import numpy as np
import time
from rfsoc_rfdc.rfdc import MyRFdcType
from rfsoc_rfdc.iq_loader import MatlabIqLoader, NumpyIqLoader

from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class SingleChTxTask(OverlayTask):
    """Single-Channel DAC"""

    def __init__(self, overlay, tx_file=None):
        super().__init__(overlay, name="SingleChTxTask")
        # Hardware IPs
        self.dma_ip = [
            self.ol.dac_datapath.t230.data_mover_ctrl
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
                    target_device=self.ol.PSDDR,
                    debug_mode=False
                )
            )

        if tx_file is None:
            np.random.seed(0)  # Fix random seed
            ofdm_scheme = ZCU216_CONFIG['OFDM_SCHEME']
            detect_scheme = ZCU216_CONFIG['DETECTION_SCHEME']
            ofdm_atten = ZCU216_CONFIG['OFDM_ATTEN_DB']
            packet_tx = ofdm_scheme.generate(amp=0.5/(10**(ofdm_atten/20)))
            wave_tx = detect_scheme.proc_tx(
                packet_tx * detect_scheme.base_band_gain)
            np.save(detect_scheme.tx_file, wave_tx)
            self.path_to_tx_file = detect_scheme.tx_file
        else:
            self.path_to_tx_file = tx_file

        # Load IQ samples from a .npy or .mat file
        if self.path_to_tx_file.endswith('.npy'):
            loader = NumpyIqLoader(self.path_to_tx_file)
            self.i_samples, self.q_samples = loader.get_iq()
        elif self.path_to_tx_file.endswith('.mat'):
            loader = MatlabIqLoader(self.path_to_tx_file, key='wave')
            self.i_samples, self.q_samples = loader.get_iq()
        else:
            raise Exception(f"File {self.path_to_tx_file} is not supported.")

    def run(self):
        # Perform data copy
        for tx_ch in self.tx_channels:
            tx_ch.data_copy(i_buff=self.i_samples, q_buff=self.q_samples)

        while self.task_state != TASK_STATE["STOP"]:
            if self.task_state == TASK_STATE["RUNNING"]:
                # Streaming IQ samples
                self.tx_channels[0].stream()
                time.sleep(1)
            else:
                self.tx_channels[0].tx_dma.stop()
                time.sleep(1)
