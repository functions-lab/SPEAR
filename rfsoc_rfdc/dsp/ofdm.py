import matplotlib.pyplot as plt
import numpy as np


class OFDM:
    """Orthogonal Frequency-Division Multiplexing (OFDM) implementation."""

    def __init__(self, sym_num=100, fft_size=64, sub_num=48, modu='16QAM', cp_rate=0.25):
        """Initialize OFDM object with given parameters."""
        super(OFDM, self).__init__()

        self.sym_num = sym_num
        self.fft_size = fft_size
        self.sub_num = sub_num
        self.modu = modu
        self.cp_rate = cp_rate

        _, speed = self._get_constel_map(modu)
        self.bit_head = np.random.randint(low=0, high=2, size=(sub_num, 2))
        self.bit_data = np.random.randint(
            low=0, high=2, size=(sym_num, sub_num, speed))

    def _bin2dec(self, bin_num):
        """Convert binary to decimal."""
        dec = 0
        for digit in reversed(list(bin_num)):
            dec = dec * 2 + digit
        return dec

    def _dec2bin(self, dec, bin_len=None):
        """Convert decimal to binary."""
        dec_temp = dec
        bin_num = []
        while dec_temp > 0:
            bin_num.append(dec_temp % 2)
            dec_temp //= 2
        if bin_len is not None:
            while len(bin_num) < bin_len:
                bin_num.append(0)
        bin_num = np.array(bin_num)
        return bin_num

    def _get_constel_map(self, modu):
        """Get constellation map for given modulation."""
        if modu == 'QPSK':
            constel_map = np.array([1+1j, -1+1j, 1-1j, -1-1j])
            speed = 2
        elif modu == '16QAM':
            constel_map = np.array([
                1+1j, 1+3j, 3+1j, 3+3j, 1-1j, 1-3j, 3-1j, 3-3j,
                -1+1j, -1+3j, -3+1j, -3+3j, -1-1j, -1-3j, -3-1j, -3-3j])
            speed = 4
        elif modu == '64QAM':
            constel_map = np.array([])
            speed = 6
        else:
            print('Warning: Modulation NOT Supported!')
        constel_map_norm = constel_map / np.sqrt(np.mean(np.abs(constel_map)**2))
        return constel_map_norm, speed

    def _bit2constel(self, bit, modu):
        """Convert bit to constellation point."""
        dec = self._bin2dec(bit)
        constel_map, _ = self._get_constel_map(modu)
        constel = constel_map[dec]
        return constel

    def _constel2bit(self, constel, modu):
        """Convert constellation point to bit."""
        constel_map, speed = self._get_constel_map(modu)
        evm = np.min(np.abs(constel_map - constel))
        dec = np.argmin(np.abs(constel_map - constel))
        bin_num = self._dec2bin(dec, bin_len=speed)
        return bin_num, evm

    def generate(self):
        """Generate OFDM signal."""
        sym_num = self.sym_num
        fft_size = self.fft_size
        sub_num = self.sub_num
        modu = self.modu
        cp_rate = self.cp_rate

        cp_len = int(np.round(cp_rate * fft_size))
        sym_len = fft_size + cp_len
        sub_offset = int(np.floor((fft_size - sub_num) / 2))

        bit_head = self.bit_head
        constel_head = np.ones((1, sub_num), dtype=complex) * np.nan
        for sub_idx in range(sub_num):
            constel_head[0, sub_idx] = self._bit2constel(
                bit_head[sub_idx, :], modu='QPSK')
        bit_data = self.bit_data
        constel_data = np.zeros((sym_num, sub_num), dtype=complex)
        for sym_idx in range(sym_num):
            for sub_idx in range(sub_num):
                constel_data[sym_idx, sub_idx] = self._bit2constel(
                    bit_data[sym_idx, sub_idx, :], modu=modu)
        constel_both = np.concatenate(
            (constel_head, constel_data, constel_head), axis=0)

        wave = np.ones(((sym_num+2)*sym_len), dtype=complex) * np.nan
        for sym_idx in range(sym_num+2):
            start_idx = sym_idx * sym_len
            end_idx = (sym_idx+1) * sym_len

            constel_pad = np.zeros((fft_size), dtype=complex)
            constel_pad[sub_offset: sub_offset+sub_num] = constel_both[sym_idx, :]
            wave_orig = np.fft.ifft(np.roll(constel_pad, shift=fft_size//2))
            wave_cp = wave_orig[: cp_len]
            wave_both = np.concatenate((wave_orig, wave_cp), axis=0)
            wave[start_idx: end_idx] = wave_both

        self.constel_both = constel_both

        return wave

    def analyze(self, wave, plot=None):
        """Analyze OFDM signal."""
        sym_num = self.sym_num
        fft_size = self.fft_size
        sub_num = self.sub_num
        modu = self.modu
        cp_rate = self.cp_rate

        cp_len = int(np.round(cp_rate * fft_size))
        sym_len = fft_size + cp_len
        sub_offset = int(np.floor((fft_size - sub_num) / 2))

        constel_both = np.ones((sym_num+2, sub_num), dtype=complex) * np.nan
        for sym_idx in range(sym_num+2):
            start_idx = sym_idx * sym_len
            end_idx = (sym_idx+1) * sym_len

            wave_both = wave[start_idx: end_idx]
            wave_orig = wave_both[cp_len//2: cp_len//2+fft_size]
            constel_pad = np.roll(np.fft.fft(wave_orig), shift=-fft_size//2)
            constel_both[sym_idx, :] = constel_pad[sub_offset: sub_offset+sub_num]

        bit_head = self.bit_head
        constel_head_gt = np.ones((sub_num), dtype=complex) * np.nan
        for sub_idx in range(sub_num):
            constel_head_gt[sub_idx] = self._bit2constel(
                bit_head[sub_idx, :], modu='QPSK')
        constel_head_1 = constel_both[0]
        constel_head_2 = constel_both[-1]
        csi_1 = constel_head_1 / constel_head_gt
        csi_2 = constel_head_2 / constel_head_gt
        csi_amp = np.tile((csi_1 + csi_2) / 2, (sym_num, 1))

        constel_data = constel_both[1: -1, :] / csi_amp
        if plot is not None:
            fig, ax = plt.subplots()
            constel_map, speed = self._get_constel_map(modu)
            ax.scatter(
                np.real(constel_data.flatten()),
                np.imag(constel_data.flatten()), marker='o', s=10)
            ax.scatter(np.real(constel_map), np.imag(
                constel_map), marker='+', s=100)
            fig.savefig(plot)
            # plt.close(fig)
        sub_offset = int(np.floor((fft_size - sub_num) / 2))
        bit_data = np.ones((sym_num, sub_num, speed)) * np.nan
        evm_all = []
        for sym_idx in range(sym_num):
            for sub_idx in range(sub_num):
                bit, evm = self._constel2bit(
                    constel_data[sym_idx, sub_idx], modu=modu)
                bit_data[sym_idx, sub_idx] = bit
                evm_all.append(evm)
        evm_all = np.array(evm_all)
        evm = np.sqrt(np.mean(np.abs(evm_all) ** 2))
        bit_data_gt = self.bit_data
        ber = np.sum(np.logical_xor(bit_data, bit_data_gt)) / sym_num / sub_num / speed

        return evm, ber


if __name__ == "__main__":
    ofdm = OFDM()
    wave = ofdm.generate()
    wave = wave + 0.05 * (np.random.randn((np.shape(wave)[0])) +
                          1j * np.random.randn((np.shape(wave)[0])))
    evm, ber = ofdm.analyze(wave, plot='constel.png')
    print(f"EVM: {evm}")
    print(f"BER: {ber}")