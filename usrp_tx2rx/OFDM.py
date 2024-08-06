import matplotlib.pyplot as plt
import numpy as np


class OFDM():
    def __init__(self, symNum=14, fftSize=1024, subNum=768, modu='16QAM', cpRate=0.0714):
        super(OFDM, self).__init__()

        self.symNum = symNum
        self.fftSize = fftSize
        self.subNum = subNum
        self.modu = modu
        self.cpRate = cpRate

        constelMapHead, _ = self.__GetConstelMap__('QPSK')
        self.constelMapHead = constelMapHead
        self.bitHead = np.random.randint(low=0, high=2, size=(subNum, 2))

        constelMap, speed = self.__GetConstelMap__(modu)
        self.constelMap = constelMap
        self.speed = speed
        self.bitData = np.random.randint(
            low=0, high=2, size=(symNum, subNum, speed))

    def __bin2dec__(self, bin):
        dec = 0
        for digit in reversed(list(bin)):
            dec = dec * 2 + digit
        return dec

    def __dec2bin__(self, dec, binLen=None):
        decTemp = dec
        bin = []
        while decTemp > 0:
            bin.append(decTemp % 2)
            decTemp //= 2
        if binLen is not None:
            while len(bin) < binLen:
                bin.append(0)
        bin = np.array(bin)
        return bin

    def __GreyCode__(self, bit):
        if bit == 1:
            grey = np.array([0, 1])
        else:
            greyLow = self.__GreyCode__(bit=bit-1)
            grey_1 = greyLow
            grey_2 = np.flip(greyLow) + 2 ** (bit-1)
            grey = np.concatenate((grey_1, grey_2))
        return grey

    def __GetConstelMap__(self, modu):
        if modu == 'QPSK':
            level = 1
        elif 'QAM' in modu:
            num = int(modu[:-3])
            level = int(np.log2(num)/2)
        greyLen = 2 ** level
        grey = self.__GreyCode__(bit=level)
        constelMap = np.ones((greyLen*greyLen), dtype=complex) * np.nan
        for i in range(greyLen):
            for j in range(greyLen):
                constelMap[grey[i]*greyLen+grey[j]] = np.complex(i, j)
        constelMap = (constelMap - np.mean(constelMap)) * 2
        constelMapNorm = constelMap / np.sqrt(np.mean(np.abs(constelMap)**2))
        speed = 2 * level
        return constelMapNorm, speed

    def __bit2constel__(self, bit, constelMap):
        dec = self.__bin2dec__(bit)
        constel = constelMap[dec]
        return constel

    def __constel2bit__(self, constel, constelMap, bitLen):
        evm = np.min(np.abs(constelMap-constel))
        dec = np.argmin(np.abs(constelMap-constel))
        bin = self.__dec2bin__(dec, binLen=bitLen)
        return bin, evm

    def Generate(self, amp=0.5):
        symNum = self.symNum
        fftSize = self.fftSize
        subNum = self.subNum
        cpRate = self.cpRate

        constelMapHead = self.constelMapHead
        constelMap = self.constelMap

        cpLen = int(np.round(cpRate * fftSize))
        symLen = fftSize + cpLen
        subOffset = int(np.floor((fftSize - subNum) / 2))

        bitHead = self.bitHead
        constelHead = np.ones((1, subNum), dtype=complex) * np.nan
        for subIdx in range(subNum):
            constelHead[0, subIdx] = self.__bit2constel__(
                bitHead[subIdx, :], constelMap=constelMapHead)
        bitData = self.bitData
        constelData = np.zeros((symNum, subNum), dtype=complex)
        for symIdx in range(symNum):
            for subIdx in range(subNum):
                constelData[symIdx, subIdx] = self.__bit2constel__(
                    bitData[symIdx, subIdx, :], constelMap=constelMap)
        constelBoth = np.concatenate(
            (constelHead, constelData, constelHead), axis=0)

        wave = np.ones(((symNum+2)*symLen), dtype=complex) * np.nan
        for symIdx in range(symNum+2):
            startIdx = symIdx * symLen
            endIdx = (symIdx+1) * symLen

            constelPad = np.zeros((fftSize), dtype=complex)
            constelPad[subOffset: subOffset+subNum] = constelBoth[symIdx, :]
            waveOrig = np.fft.ifft(np.roll(constelPad, shift=fftSize//2))
            waveCP = waveOrig[: cpLen]
            waveBoth = np.concatenate((waveOrig, waveCP), axis=0)
            wave[startIdx: endIdx] = waveBoth
        wave = amp * wave / np.std(wave)

        self.constelBoth = constelBoth
        return wave

    def Analyze(self, wave, plot=None):
        symNum = self.symNum
        fftSize = self.fftSize
        subNum = self.subNum
        cpRate = self.cpRate

        constelMapHead = self.constelMapHead
        speed = self.speed
        constelMap = self.constelMap

        cpLen = int(np.round(cpRate * fftSize))
        symLen = fftSize + cpLen
        subOffset = int(np.floor((fftSize - subNum) / 2))

        constelBoth = np.ones((symNum+2, subNum), dtype=complex) * np.nan
        for symIdx in range(symNum+2):
            startIdx = symIdx * symLen
            endIdx = (symIdx+1) * symLen

            waveBoth = wave[startIdx: endIdx]
            waveOrig = waveBoth[cpLen//2: cpLen//2+fftSize]
            constelPad = np.roll(np.fft.fft(waveOrig), shift=-fftSize//2)
            constelBoth[symIdx, :] = constelPad[subOffset: subOffset+subNum]

        bitHead = self.bitHead
        constelHeadGt = np.ones((subNum), dtype=complex) * np.nan
        for subIdx in range(subNum):
            constelHeadGt[subIdx] = self.__bit2constel__(
                bitHead[subIdx, :], constelMap=constelMapHead)
        constelHead_1 = constelBoth[0]
        constelHead_2 = constelBoth[-1]
        csi_1 = constelHead_1 / constelHeadGt
        csi_2 = constelHead_2 / constelHeadGt
        csiAmp = np.tile((csi_1 + csi_2) / 2, (symNum, 1))

        constelData = constelBoth[1: -1, :] / csiAmp
        subOffset = int(np.floor((fftSize - subNum) / 2))
        bitData = np.ones((symNum, subNum, speed)) * np.nan
        evmAll = []
        for symIdx in range(symNum):
            for subIdx in range(subNum):
                bit, evm = self.__constel2bit__(
                    constelData[symIdx, subIdx], constelMap=constelMap, bitLen=speed)
                bitData[symIdx, subIdx] = bit
                evmAll.append(evm)
        evmAll = np.array(evmAll)
        EVM = np.sqrt(np.mean(np.abs(evmAll) ** 2))
        bitDataGt = self.bitData
        BER = np.sum(np.logical_xor(bitData, bitDataGt)) / symNum/subNum/speed

        if plot is not None:
            fig, ax = plt.subplots()
            ax.scatter(
                np.real(constelData.flatten()),
                np.imag(constelData.flatten()), marker='o', s=10)
            ax.scatter(np.real(constelMap), np.imag(
                constelMap), marker='+', s=100)
            ax.set_title('EVM: '+str(EVM)+' BER:'+str(BER))
            fig.savefig(plot)
            plt.close(fig)

        return EVM, BER


if __name__ == "__main__":
    ofdm = OFDM(modu='4096QAM')
    wave = ofdm.Generate()
    wave = wave + 0.01 * \
        (np.random.randn((np.shape(wave)[0])) +
         1j*np.random.randn((np.shape(wave)[0])))
    EVM, BER = ofdm.Analyze(wave, plot='Constel.png')
    print(EVM)
    print(BER)
