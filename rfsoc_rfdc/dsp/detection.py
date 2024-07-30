import matplotlib.pyplot as plt
import numpy as np
import os
import shutil

from rfsoc_rfdc.dsp.ofdm import OFDM
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class Detection:

    def __init__(self, sample_rate=1e9):
        super(Detection, self).__init__()
        # Check path to waveform
        file_dir = os.path.dirname(__file__)
        self.path2wave = os.path.join(
            os.path.dirname(file_dir), "../wave_files")
        if os.path.exists(self.path2wave):
            shutil.rmtree(self.path2wave)
        os.mkdir(self.path2wave, mode=777)
        # Tx/Rx file name
        self.tx_file = os.path.join(self.path2wave, 'Tx.npy')
        self.rx_file = os.path.join(self.path2wave, 'Rx.npy')
        # Preamble detection
        self.detection_file = os.path.join(self.path2wave, 'detection.png')
        self.base_band_gain = 5
        self.sample_rate = sample_rate
        # DSP-related
        self.zadoff_set = [139, 839]  # ascent

    def _check_saturation(self, packet, threshold=1):
        """Check if the packet is saturated."""
        ratio = np.sum(np.abs(packet) > threshold) / np.shape(packet)[0]
        if ratio > 0:
            print(f'Warning: Packet Saturated for {ratio*100:.2f}%')

    def _zadoff_detection(self, wave, win_len, delta_len, threshold):
        """Perform Zadoff-Chu sequence detection."""
        wave_len = np.shape(wave)[0]
        neighbor = 10

        corr_all = np.ones((wave_len - delta_len - win_len + 1)) * np.nan

        zadoff_1 = wave[:win_len]
        zadoff_2 = wave[delta_len:delta_len + win_len]
        product = np.sum(zadoff_1 * np.conj(zadoff_2))
        sum_1 = np.sum(zadoff_1)
        sum_2 = np.sum(zadoff_2)
        energy_1 = np.sum(np.abs(zadoff_1)**2)
        energy_2 = np.sum(np.abs(zadoff_2)**2)
        corr_all[0] = (
            np.abs(product - sum_1 * np.conj(sum_2) / win_len) /
            np.sqrt((energy_1 - np.abs(sum_1)**2 / win_len) *
                    (energy_2 - np.abs(sum_2)**2 / win_len))
        )

        for offset in range(wave_len - delta_len - win_len):
            iq_in_1 = wave[offset + win_len]
            iq_in_2 = wave[offset + delta_len + win_len]
            iq_out_1 = wave[offset]
            iq_out_2 = wave[offset + delta_len]

            sum_1 = sum_1 - iq_out_1 + iq_in_1
            sum_2 = sum_2 - iq_out_2 + iq_in_2
            product = (product - iq_out_1 * np.conj(iq_out_2) +
                       iq_in_1 * np.conj(iq_in_2))
            energy_1 = energy_1 - np.abs(iq_out_1)**2 + abs(iq_in_1)**2
            energy_2 = energy_2 - np.abs(iq_out_2)**2 + abs(iq_in_2)**2
            corr = (
                np.abs(product - sum_1 * np.conj(sum_2) / win_len) /
                np.sqrt((energy_1 - np.abs(sum_1)**2 / win_len) *
                        (energy_2 - np.abs(sum_2)**2 / win_len))
            )
            corr_all[offset + 1] = corr

        offset_list = []
        corr_list = []
        for offset in range(neighbor, wave_len - delta_len - win_len + 1 - neighbor):
            corr = corr_all[offset]
            if corr > threshold:
                if corr < np.max(corr_all[offset - neighbor - 1:offset - 1]):
                    continue
                if corr < np.max(corr_all[offset:offset + neighbor]):
                    continue
                offset_list.append(offset)
                corr_list.append(corr)

        return offset_list, corr_list

    def _get_energy(self, wave):
        """Calculate the energy of the wave."""
        wave_cal = wave  # - np.mean(wave)
        energy = np.mean(np.abs(wave_cal)**2)
        return energy

    def proc_tx(self, packet_tx):
        """Pad preamble to Tx packet"""
        self._check_saturation(packet_tx)
        self.packet_len = np.shape(packet_tx)[0]
        # int(max(1e-3*self.sample_rate, round(0.1*self.packet_len)))
        self.pad_len = 10000

        head_tx = np.zeros((sum(self.zadoff_set) * 3), dtype=np.complex64)
        offset = 0
        for zadoff_len in self.zadoff_set:
            zadoff_single = np.exp(
                1j * 2 * np.pi * np.random.rand(1, zadoff_len))
            zadoff_double = np.tile(zadoff_single, 2)
            head_tx[offset:offset + 2 * zadoff_len] = zadoff_double
            offset += 3 * zadoff_len
        pad_tx = np.zeros((self.pad_len))
        wave_tx = np.concatenate((pad_tx, head_tx, packet_tx, pad_tx), axis=0)

        return wave_tx

    def proc_rx(self, wave_rx):
        """Detect preamble received packet"""
        cap_num = 3
        noise_num = 1000
        head_len = sum(self.zadoff_set) * 3
        wave_len = 2 * self.pad_len + head_len + self.packet_len

        while True:
            wave_rx = wave_rx[-cap_num * wave_len:]
            offset_list, corr_list = self._zadoff_detection(
                wave_rx[:wave_len], self.zadoff_set[-1], self.zadoff_set[-1], 0.7)
            offset_list_after, _ = self._zadoff_detection(
                wave_rx[wave_len:2 * wave_len], self.zadoff_set[-1], self.zadoff_set[-1], 0.7)
            if (not offset_list) or (not offset_list_after):
                continue
            offset_idx = np.argmax(np.array(corr_list))
            offset_zadoff = offset_list[offset_idx] - \
                3 * sum(self.zadoff_set[:-1])
            offset_packet = offset_zadoff + head_len
            if offset_zadoff <= 0:
                continue
            break

        cfo_set = []
        offset = offset_zadoff
        for zadoff_len in self.zadoff_set:
            zadoff_1 = wave_rx[offset:offset + zadoff_len]
            zadoff_2 = wave_rx[offset + zadoff_len:offset + 2 * zadoff_len]

            cfo_temp = (-self.sample_rate / zadoff_len *
                        np.angle(np.sum(zadoff_1 * np.conj(zadoff_2))) / 2 / np.pi)
            cfo_set.append(cfo_temp)
            offset += 3 * zadoff_len

            wave_rx[offset_zadoff:offset_zadoff + head_len] = (
                wave_rx[offset_zadoff:offset_zadoff + head_len] *
                np.exp(-1j * 2 * np.pi * np.arange(head_len) /
                       self.sample_rate * cfo_temp)
            )
        cfo = sum(cfo_set)
        packet_rx = wave_rx[offset_packet:offset_packet + self.packet_len]
        packet_rx = packet_rx * \
            np.exp(-1j * 2 * np.pi * np.arange(self.packet_len) /
                   self.sample_rate * cfo)

        noise_list = []
        for noise_idx in range(noise_num):
            start_idx = round(cap_num * wave_len / noise_num * noise_idx)
            end_idx = round(cap_num * wave_len / noise_num *
                            noise_idx) + int(np.ceil(100))
            noise_sym = wave_rx[start_idx:end_idx]
            noise = self._get_energy(noise_sym)
            noise_list.append(noise)
        noise = np.percentile(noise_list, 10)
        signal = self._get_energy(packet_rx) - noise
        snr = 10 * np.log10(signal / noise)

        plt.ioff()
        fig, ax = plt.subplots()
        ax.plot(np.arange(cap_num * wave_len), 20 *
                np.log10(np.abs(wave_rx) + 1e-10))
        ax.vlines(offset_zadoff, ymin=-1e10, ymax=+1e10)
        ax.vlines(offset_packet, ymin=-1e10, ymax=+1e10)
        ax.vlines(offset_packet + self.packet_len, ymin=-1e10, ymax=+1e10)
        ax.set_ylim(bottom=0, top=100)
        ax.set_title(f'SNR: {snr:.2f}dB CFO:{cfo:.2f}Hz')
        fig.savefig(self.detection_file)
        plt.close()

        return packet_rx, snr, cfo


WIFI_OFDM_SCHEME = OFDM(sym_num=100, fft_size=64, sub_num=48,
                        modu='16QAM', cp_rate=0.25)

iq_samp_rate = ZCU216_CONFIG['DACSampleRate'] / \
    ZCU216_CONFIG['DACInterpolationRate'] * 1e6

DETECTION_SCHEME = Detection(sample_rate=iq_samp_rate)

if __name__ == "__main__":
    np.random.seed(0)

    ofdm = OFDM(sym_num=100, fft_size=64, sub_num=48,
                modu='16QAM', cp_rate=0.25)
    packet_tx = ofdm.generate()

    det = Detection(sample_rate=1.25e9)

    wave_tx = det.proc_tx(packet_tx * det.base_band_gain)

    np.save(det.tx_file, wave_tx)

    wave_rx = np.load(det.rx_file)

    packet_rx, snr, cfo = det.proc_rx(wave_rx)

    evm, ber = ofdm.analyze(
        packet_rx, plot='../../wave_files/constellation.png')

    print(snr, cfo)
    print(evm, ber)
    print('Done!')
