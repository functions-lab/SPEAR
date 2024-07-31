"""OFDM implementation with signal generation and analysis capabilities."""

import matplotlib.pyplot as plt
import numpy as np


class OFDM:
    """Implements Orthogonal Frequency-Division Multiplexing (OFDM) functionality."""

    def __init__(self, sym_num=14, fft_size=1024, sub_num=768, modu='16QAM', cp_rate=0.0714):
        """Initializes the OFDM object with given parameters."""
        self.sym_num = sym_num
        self.fft_size = fft_size
        self.sub_num = sub_num
        self.modu = modu
        self.cp_rate = cp_rate
        constel_map_head, _ = self._get_constel_map('QPSK')
        self.constel_map_head = constel_map_head
        self.bit_head = np.random.randint(low=0, high=2, size=(sub_num, 2))
        constel_map, speed = self._get_constel_map(modu)
        self.constel_map = constel_map
        self.speed = speed
        self.bit_data = np.random.randint(
            low=0, high=2, size=(sym_num, sub_num, speed))

    def _bin2dec(self, bin_array):
        """Converts binary array to decimal."""
        return int(''.join(map(str, reversed(bin_array))), 2)

    def _dec2bin(self, dec, bin_len=None):
        """Converts decimal to binary array."""
        bin_array = []
        while dec > 0:
            bin_array.append(dec % 2)
            dec //= 2
        if bin_len is not None:
            bin_array.extend([0] * (bin_len - len(bin_array)))
        return np.array(bin_array)

    def _get_constel_map(self, modu):
        """Generates constellation map for given modulation."""
        grey = np.array([
            0, 1, 3, 2, 6, 7, 5, 4,
            12, 13, 15, 14, 10, 11, 9, 8,
            24, 25, 27, 26, 30, 31, 29, 28,
            20, 21, 23, 22, 18, 19, 17, 16])

        grey_len = {
            'QPSK': 2, '16QAM': 4, '64QAM': 8, '256QAM': 16, '1024QAM': 32
        }.get(modu)

        constel_map = np.ones((grey_len * grey_len), dtype=complex) * np.nan
        for i in range(grey_len):
            for j in range(grey_len):
                constel_map[grey[i] * grey_len + grey[j]] = np.complex(i, j)
        constel_map = (constel_map - np.mean(constel_map)) * 2
        constel_map_norm = constel_map / \
            np.sqrt(np.mean(np.abs(constel_map)**2))
        speed = int(2 * np.log2(grey_len))
        return constel_map_norm, speed

    def _bit2constel(self, bit, constel_map):
        """Converts bit sequence to constellation point."""
        dec = self._bin2dec(bit)
        return constel_map[dec]

    def _constel2bit(self, constel, constel_map, bit_len):
        """Converts constellation point to bit sequence."""
        evm = np.min(np.abs(constel_map - constel))
        dec = np.argmin(np.abs(constel_map - constel))
        return self._dec2bin(dec, bin_len=bit_len), evm

    def generate(self, amp=0.5):
        """Generates OFDM signal."""
        cp_len = int(np.round(self.cp_rate * self.fft_size))
        sym_len = self.fft_size + cp_len
        sub_offset = int(np.floor((self.fft_size - self.sub_num) / 2))

        constel_head = np.array([self._bit2constel(self.bit_head[i], self.constel_map_head)
                                 for i in range(self.sub_num)]).reshape(1, -1)

        constel_data = np.array([[self._bit2constel(self.bit_data[i, j], self.constel_map)
                                  for j in range(self.sub_num)]
                                 for i in range(self.sym_num)])

        constel_both = np.vstack((constel_head, constel_data, constel_head))
        wave = np.empty(((self.sym_num + 2) * sym_len), dtype=complex)

        for sym_idx in range(self.sym_num + 2):
            constel_pad = np.zeros(self.fft_size, dtype=complex)
            constel_pad[sub_offset:sub_offset +
                        self.sub_num] = constel_both[sym_idx]
            wave_orig = np.fft.ifft(
                np.roll(constel_pad, shift=self.fft_size // 2))
            wave_cp = wave_orig[:cp_len]
            wave_both = np.concatenate((wave_orig, wave_cp))
            wave[sym_idx * sym_len:(sym_idx + 1) * sym_len] = wave_both

        wave = amp * wave / np.std(wave)
        self.constel_both = constel_both
        return wave

    def analyze(self, wave, plot=None):
        """Analyzes received OFDM signal."""
        cp_len = int(np.round(self.cp_rate * self.fft_size))
        sym_len = self.fft_size + cp_len
        sub_offset = int(np.floor((self.fft_size - self.sub_num) / 2))

        constel_both = np.empty((self.sym_num + 2, self.sub_num), dtype=complex)
        for sym_idx in range(self.sym_num + 2):
            wave_both = wave[sym_idx * sym_len:(sym_idx + 1) * sym_len]
            wave_orig = wave_both[cp_len // 2:cp_len // 2 + self.fft_size]
            constel_pad = np.roll(np.fft.fft(wave_orig),
                                  shift=-self.fft_size // 2)
            constel_both[sym_idx] = constel_pad[sub_offset:sub_offset + self.sub_num]

        constel_head_gt = np.array([self._bit2constel(self.bit_head[i], self.constel_map_head)
                                    for i in range(self.sub_num)])

        csi_1 = constel_both[0] / constel_head_gt
        csi_2 = constel_both[-1] / constel_head_gt
        csi_amp = np.tile((csi_1 + csi_2) / 2, (self.sym_num, 1))
        constel_data = constel_both[1:-1] / csi_amp

        bit_data = np.empty((self.sym_num, self.sub_num, self.speed))
        evm_all = []

        for sym_idx in range(self.sym_num):
            for sub_idx in range(self.sub_num):
                bit, evm = self._constel2bit(constel_data[sym_idx, sub_idx],
                                             self.constel_map, self.speed)
                bit_data[sym_idx, sub_idx] = bit
                evm_all.append(evm)

        evm_all = np.array(evm_all)
        evm = np.sqrt(np.mean(np.abs(evm_all) ** 2))
        ber = np.sum(np.logical_xor(bit_data, self.bit_data)) / \
            (self.sym_num * self.sub_num * self.speed)

        if plot:
            self._plot_constellation(constel_data, evm, ber, plot)

        return evm, ber

    def _plot_constellation(self, constel_data, evm, ber, plot_filename):
        """Plots constellation diagram."""
        fig, ax = plt.subplots()
        ax.scatter(np.real(constel_data.flatten()),
                   np.imag(constel_data.flatten()), marker='o', s=10)
        ax.scatter(np.real(self.constel_map), np.imag(
            self.constel_map), marker='+', s=100)
        ax.set_title(f'EVM: {evm:.4f} BER: {ber:.4f}')
        fig.savefig(plot_filename)
        plt.close(fig)


if __name__ == "__main__":
    ofdm = OFDM(modu='256QAM')
    wave = ofdm.generate()
    noise = 0.01 * \
        (np.random.randn(wave.shape[0]) + 1j * np.random.randn(wave.shape[0]))
    wave_with_noise = wave + noise
    evm, ber = ofdm.analyze(wave_with_noise, plot='Constel.png')
    print(f"EVM: {evm}")
    print(f"BER: {ber}")
