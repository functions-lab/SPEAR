import matplotlib.pyplot as plt
import numpy as np
import os
import shutil

from ofdm import OFDM


class Transmission():
    def __init__(self):
        super(Transmission, self).__init__()

    def __CheckSaturation__(self, packet, threshold=1):
        ratio = sum(np.abs(packet) > threshold)/np.shape(packet)[0]
        if ratio > 0:
            print('Warning: Packet Saturated for '+str(ratio*100)+'%')

    def __Wave2File__(self, wave, fileName):
        np.save(fileName, wave)

    def __File2Wave__(self, fileName):
        wave = np.load(fileName)
        return wave

    def __ZadoffDetection__(self, wave, winLen, deltaLen, threshold):
        waveLen = np.shape(wave)[0]
        neighbor = 10

        corrAll = np.ones((waveLen-deltaLen-winLen+1)) * np.nan

        zadoff_1 = wave[: winLen]
        zadoff_2 = wave[deltaLen: deltaLen+winLen]
        product = np.sum(zadoff_1 * np.conj(zadoff_2))
        sum_1 = np.sum(zadoff_1)
        sum_2 = np.sum(zadoff_2)
        energy_1 = np.sum(np.abs(zadoff_1)**2)
        energy_2 = np.sum(np.abs(zadoff_2)**2)
        corrAll[0] = \
            np.abs(product-sum_1*np.conj(sum_2)/winLen) / \
            np.sqrt((energy_1-np.abs(sum_1)**2/winLen)
                    * (energy_2-np.abs(sum_2)**2/winLen))
        for offset in range(waveLen-deltaLen-winLen):
            iqIn_1 = wave[offset+winLen]
            iqIn_2 = wave[offset+deltaLen+winLen]
            iqOut_1 = wave[offset]
            iqOut_2 = wave[offset+deltaLen]

            sum_1 = sum_1 - iqOut_1 + iqIn_1
            sum_2 = sum_2 - iqOut_2 + iqIn_2
            product = product - iqOut_1 * \
                np.conj(iqOut_2) + iqIn_1*np.conj(iqIn_2)
            energy_1 = energy_1 - np.abs(iqOut_1)**2 + abs(iqIn_1)**2
            energy_2 = energy_2 - np.abs(iqOut_2)**2 + abs(iqIn_2)**2
            corr = \
                np.abs(product-sum_1*np.conj(sum_2)/winLen) / \
                np.sqrt((energy_1-np.abs(sum_1)**2/winLen)
                        * (energy_2-np.abs(sum_2)**2/winLen))
            corrAll[offset+1] = corr

        offsetList = []
        corrList = []
        for offset in range(neighbor, waveLen-deltaLen-winLen+1-neighbor):
            corr = corrAll[offset]
            if corr > threshold:
                if corr < np.max(corrAll[offset-neighbor-1: offset-1]):
                    continue
                if corr < np.max(corrAll[offset: offset+neighbor]):
                    continue
                offsetList.append(offset)
                corrList.append(corr)

        return offsetList, corrList

    def __GetEnergy__(self, wave):
        waveCal = wave  # - np.mean(wave)
        energy = np.mean(np.abs(waveCal)**2)
        return energy

    def Tx2Rx(self, packetTx, sampleRate=50e6):
        thisPath = os.getcwd() + '/'

        self.__CheckSaturation__(packetTx)
        packetLen = np.shape(packetTx)[0]
        padLen = 10000  # int(max(1e-3*sampleRate, round(0.1*packetLen)))
        capNum = 3
        noiseNum = 1000
        zadoffSet = [139, 839]  # ascent

        bufferPath = thisPath+"Buffer/"
        if os.path.isdir(bufferPath):
            shutil.rmtree(bufferPath)
        os.mkdir(bufferPath)

        headTx = np.zeros((sum(zadoffSet)*3), dtype=np.complex64)
        offset = 0
        for zadoffLen in zadoffSet:
            zadoffSingle = np.exp(1j*2*np.pi*np.random.rand(1, zadoffLen))
            zadoffDouble = np.tile(zadoffSingle, 2)
            headTx[offset: offset+2*zadoffLen] = zadoffDouble
            offset += 3 * zadoffLen
        headLen = sum(zadoffSet)*3

        padTx = np.zeros((padLen))

        waveTx = np.concatenate((padTx, headTx, packetTx, padTx), axis=0)
        fileTxStr = bufferPath+'Tx.npy'

        self.__Wave2File__(waveTx, fileTxStr)
        waveLen = 2*padLen + headLen + packetLen

        fileRxStr = './iq_data.npy'

        while True:
            waveTemp = self.__File2Wave__(fileRxStr)
            waveRx = waveTemp[-capNum*waveLen:]

            offsetList, corrList = self.__ZadoffDetection__(
                waveRx[: waveLen], zadoffSet[-1], zadoffSet[-1], 0.7)
            offsetListAfter, _ = self.__ZadoffDetection__(
                waveRx[waveLen: 2*waveLen], zadoffSet[-1], zadoffSet[-1], 0.7)
            if (len(offsetList) == 0) or (len(offsetListAfter) == 0):
                continue
            offsetIdx = np.argmax(np.array(corrList))
            offsetZadoff = offsetList[offsetIdx]-3*sum(zadoffSet[: -1])
            offsetPacket = offsetZadoff + headLen
            if offsetZadoff <= 0:
                continue
            break

        cfoSet = []
        offset = offsetZadoff
        for zadoffLen in zadoffSet:
            zadoff_1 = waveRx[offset: offset+zadoffLen]
            zadoff_2 = waveRx[offset+zadoffLen: offset+2*zadoffLen]

            # fig, ax = plt.subplots()
            # ax.plot(np.arange(capNum*waveLen), 20*np.log10(np.abs(waveRx)+1e-10))
            # ax.vlines(offset, ymin=-1e10, ymax=+1e10)
            # ax.vlines(offset+zadoffLen, ymin=-1e10, ymax=+1e10)
            # ax.vlines(offset+2*zadoffLen, ymin=-1e10, ymax=+1e10)
            # ax.set_ylim(bottom=0, top=100)
            # ax.set_xlim(left=0, right=waveLen)
            # fig.savefig(bufferPath+'CFO.png')
            # plt.close(fig)
            # exit()

            cfoTemp = -sampleRate/zadoffLen * \
                np.angle(np.sum(zadoff_1 * np.conj(zadoff_2)))/2/np.pi
            cfoSet.append(cfoTemp)
            offset += 3*zadoffLen

            waveRx[offsetZadoff: offsetZadoff+headLen] = \
                waveRx[offsetZadoff: offsetZadoff+headLen] * \
                np.exp(-1j*2*np.pi*np.arange(headLen)/sampleRate*cfoTemp)
        cfo = sum(cfoSet)
        packetRx = waveRx[offsetPacket: offsetPacket+packetLen]
        packetRx = packetRx * \
            np.exp(-1j*2*np.pi*np.arange(packetLen)/sampleRate*cfo)

        noiseList = []
        for noiseIdx in range(noiseNum):
            startIdx = round(capNum*waveLen/noiseNum*noiseIdx)
            endIdx = round(capNum*waveLen/noiseNum*noiseIdx) + \
                int(np.ceil(100))
            noiseSym = waveRx[startIdx: endIdx]
            noise = self.__GetEnergy__(noiseSym)
            noiseList.append(noise)
        noise = np.percentile(noiseList, 10)
        signal = self.__GetEnergy__(packetRx) - noise
        snr = 10 * np.log10(signal/noise)

        fig, ax = plt.subplots()
        ax.plot(np.arange(capNum*waveLen), 20*np.log10(np.abs(waveRx)+1e-10))
        ax.vlines(offsetZadoff, ymin=-1e10, ymax=+1e10)
        ax.vlines(offsetPacket, ymin=-1e10, ymax=+1e10)
        ax.vlines(offsetPacket+packetLen, ymin=-1e10, ymax=+1e10)
        ax.set_ylim(bottom=0, top=100)
        ax.set_title('SNR: '+str(snr)+'dB CFO:'+str(cfo)+'Hz')
        fig.savefig(bufferPath+'detection.png')
        plt.close(fig)

        return packetRx, snr, cfo


if __name__ == "__main__":
    np.random.seed(0)

    transmission = Transmission()
    ofdm = OFDM(symNum=100, fftSize=64, subNum=48, modu='16QAM', cpRate=0.25)
    packetTx = ofdm.Generate()

    fig, ax = plt.subplots()
    ax.plot(np.arange(np.shape(packetTx)[
            0]), 20*np.log10(np.abs(np.fft.fftshift(np.fft.fft(packetTx)))+1e-10))
    fig.savefig('fft.png')
    plt.close(fig)
    # exit()

    packetRx, SNR, CFO = transmission.Tx2Rx(packetTx*10, sampleRate=1.25e9)
    EVM, BER = ofdm.Analyze(packetRx, plot='Constelno.png')
    print(SNR, CFO)
    print(EVM, BER)
    print('Done!')
