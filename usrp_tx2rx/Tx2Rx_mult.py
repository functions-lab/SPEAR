import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import shutil

from OFDM import OFDM


parser = argparse.ArgumentParser(description='Zhihui\'s 5G Pipeline')
parser.add_argument('--addr', default='192.168.30.2', type=str,
                    help='USRP IP addresses, split by ","')
parser.add_argument('--freq', default=2.0e9, type=float,
                    help='Carrier frequency in Hz')
parser.add_argument('--gain', default=20, type=float,
                    help='Rx gain')
parser.add_argument('--rate', default=100e6, type=float,
                    help='Rx sample rate in Hz')
parser.add_argument('--qam', default='16QAM', type=str,
                    help='Order of QAM')
parser.add_argument('--atten', default=0, type=float,
                    help='Attenuation [dB]')


class Transmission():
    def __init__(self,
                 deviceTx='192.168.70.10', carrierTx=2.0e9, gainTx=20, clockTx=200e6,
                 deviceRx='192.168.30.2', carrierRx=2.0e9, gainRx=20, clockRx=200e6,
                 sync=0):
        super(Transmission, self).__init__()

        self.deviceTx = deviceTx
        self.carrierTx = carrierTx
        self.gainTx = gainTx
        self.clockTx = clockTx

        self.deviceRx = deviceRx
        self.carrierRx = carrierRx
        self.gainRx = gainRx
        self.clockRx = clockRx

        self.sync = sync

    def __CheckSaturation__(self, packet, threshold=1):
        ratio = sum(np.abs(packet) > threshold)/np.shape(packet)[0]
        if ratio > 0:
            print('Warning: Packet Saturated for '+str(ratio*100)+'%')

    def __Wave2File__(self, wave, fileName):
        file = open(fileName, 'wb')
        wave.astype(np.complex64).tofile(file)
        file.close()

    def __File2Wave__(self, fileName):
        file = open(fileName, 'rb')
        wave = np.fromfile(file, dtype=np.complex64)
        file.close()
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
        padLen = int(max(1e-3*sampleRate, round(0.1*packetLen)))
        capNum = 3
        noiseNum = 1000
        zadoffSet = [139, 839]  # ascent

        bufferPath = thisPath+"Buffer/"
        # bufferPath = "/dev/shm/Buffer/"
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
        # fileTxStr = bufferPath+'Tx.bin'
        freqTxStr = str(self.carrierTx)
        gainTxStr = str(self.gainTx)
        # self.__Wave2File__(waveTx, fileTxStr)
        waveLen = 2*padLen + headLen + packetLen
        fileTxStr = bufferPath+'Tx.npy'
        np.save(fileTxStr, waveTx)

        fileRxStr = bufferPath+'Rx.bin'
        freqRxStr = str(self.carrierRx)
        gainRxStr = str(self.gainRx)

        while True:
            os.system('bash '+thisPath+'Tx2Rx_mult.sh ' +
                      str(max(1.0, (capNum+1)*waveLen/sampleRate))+' ' +
                      self.deviceTx+' '+str(sampleRate)+' '+str(self.clockTx)+' ' +
                      fileTxStr+' '+freqTxStr+' '+gainTxStr+' ' +
                      self.deviceRx+' '+str(sampleRate)+' '+str(self.clockRx)+' ' +
                      fileRxStr+' '+freqRxStr+' '+gainRxStr)

            waveTemp = self.__File2Wave__(fileRxStr)
            waveRx = waveTemp[-capNum*waveLen:]

            # fig, ax = plt.subplots()
            # ax.plot(np.arange(capNum*waveLen), 20 *
            #         np.log10(np.abs(waveRx)+1e-10))
            # ax.set_ylim(bottom=-100, top=0)
            # fig.savefig(bufferPath+'detection.png')
            # plt.close(fig)

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
                int(np.ceil(40e-6*sampleRate))
            noiseSym = waveRx[startIdx: endIdx]
            noise = self.__GetEnergy__(noiseSym)
            noiseList.append(noise)
        noise = np.percentile(noiseList, 10)
        signal = self.__GetEnergy__(packetRx) - noise
        snr = 10 * np.log10(signal/noise)

        fig, ax = plt.subplots()
        ax.plot(np.arange(capNum*waveLen), 20*np.log10(np.abs(waveRx)+1e-10))
        ax.vlines(offsetZadoff, ymin=-100, ymax=0)
        ax.vlines(offsetPacket, ymin=-100, ymax=0)
        ax.vlines(offsetPacket+packetLen, ymin=-100, ymax=0)
        ax.set_ylim(bottom=-100, top=0)
        ax.set_title('SNR: '+str(snr)+'dB CFO:'+str(cfo)+'Hz')
        fig.savefig(bufferPath+'detection.png')
        plt.close(fig)

        return packetRx, snr, cfo


if __name__ == "__main__":
    np.random.seed(0)

    opt = parser.parse_args()
    ADDR = opt.addr
    FREQ = opt.freq
    GAIN = opt.gain
    RATE = opt.rate
    QAM = opt.qam
    ATTEN = opt.atten

    inv_sinc = 1

    tag_name = './Tx_100M_BW' + '_' + QAM + '_' + \
        str(FREQ/1e6) + "_" + str(ATTEN) + "_" + str(inv_sinc)

    transmission = Transmission(deviceRx=ADDR, carrierRx=FREQ, gainRx=GAIN)
    ofdm = OFDM(symNum=100, fftSize=64, subNum=48, modu=QAM, cpRate=0.25)
    packetTx = ofdm.Generate(amp=0.5/(10**(ATTEN/20)))
    packetRx, SNR, CFO = transmission.Tx2Rx(packetTx, sampleRate=RATE)
    EVM, BER = ofdm.Analyze(packetRx, plot=tag_name+'_const_diagram.png')

    # Write result to a file
    with open(tag_name+"_res.log", 'w') as f:
        f.write(f"{SNR:.3f}, {CFO:.3f}, {EVM:.3f}, {BER:.10f}")

    print(f"SNR: {SNR:.3f}, CFO: {CFO:.3f}, EVM: {EVM:.3f}, BER: {BER:.10f}")
