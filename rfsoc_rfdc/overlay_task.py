import numpy as np
import threading
from abc import ABC, abstractmethod

import xrfclk
import xrfdc

from .clocks import set_custom_lmclks
from .rfsoc_overlay import RFSoCOverlay
from pynq import allocate

import os
import time
from pynq.lib import AxiGPIO


class OverlayTask(ABC):
    def __init__(self, overlay, name="OverlayTask"):
        if not isinstance(overlay, RFSoCOverlay):
            raise TypeError("Overlay passed is not an RFSoCOverlay instance.")
        self.ol = overlay
        self.task_name = name
        self.thread = threading.Thread(target=self.run)

    @abstractmethod
    def run(self):
        pass

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()


class ReceiverTask(OverlayTask):

    def __init__(self, overlay):
        super().__init__(overlay, name="ReceiverTask")
        self.rx_dma = self.ol.axi_dma_adc2

    def run(self):
        self.rx_buff = allocate(shape=(8,), dtype=np.uint16)
        cnt = 0
        recv_ch = self.rx_dma.recvchannel
        while True:
            try:
                prev_time = time.time_ns()

                recv_ch.transfer(self.rx_buff)
                recv_ch.wait()  # blocking wait

                delay = (time.time_ns() - prev_time)
                print(f"Delay: {delay} ns")
            except:
                print("Get the info from DMA registers", self.rx_dma.register_map)
            print(self.rx_buff)

    def __del__(self):
        try:
            if self.rx_buff is not None:
                self.rx_buff.freebuffer()
                print("rx buffer freed")
        except:
            pass


class TransmitterTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="TransmitterTask")
        self.tx_dma = self.ol.axi_dma_dac2
        self.pts_count = 1000

        # Generate waveforms
        amplitude = 2**13
        # Generate the time points
        t = np.ones(self.pts_count, dtype=np.int16)
        for idx, elem in enumerate(t):
            if idx % 2 == 0:
                elem = 0
        t = t * amplitude / 2
        self.seq = t

    def run(self):

        self.tx_buff = allocate(shape=(self.pts_count,), dtype=np.int16)
        self.tx_buff[:] = self.seq

        cnt = 0
        while True:
            cnt = cnt + 1
            self.tx_dma.sendchannel.transfer(self.tx_buff)
            self.tx_dma.sendchannel.wait()  # blocking wait

    def __del__(self):
        super().__del__()
        try:
            if self.tx_buff is not None:
                self.tx_buff.freebuffer()
                print("tx buffer freed")
        except:
            pass


class RfdcTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="RfdcTask")
        self.rf = self.ol.usp_rf_data_converter

    def self_check(self):
        data = self.rf.IPStatus
        for item in data['DACTileStatus']:
            print("DAC IsEnabled: ", item['IsEnabled'], "TileState: ", item['TileState'], "BlockStatusMask: ",
                  item['BlockStatusMask'], "PowerUpState: ", item['PowerUpState'], "PLLState: ", item['PLLState'])
        for item in data['ADCTileStatus']:
            print("ADC IsEnabled: ", item['IsEnabled'], "TileState: ", item['TileState'], "BlockStatusMask: ",
                  item['BlockStatusMask'], "PowerUpState: ", item['PowerUpState'], "PLLState: ", item['PLLState'])

    def run(self):

        # Determine board
        board = os.environ['BOARD']

        # Extract friendly dataconverter names
        if board == 'RFSoC4x2':
            self.dac_tile = self.rf.dac_tiles[2]
            self.dac_block = self.dac_tile.blocks[0]
            self.adc_tile = self.rf.adc_tiles[2]
            self.adc_block = self.adc_tile.blocks[1]
        elif board in ['ZCU208', 'ZCU216']:
            self.dac_tile = self.rf.dac_tiles[2]
            self.dac_block = self.dac_tile.blocks[0]
            # Change from tile 1 (ADC 225) to tile 2 (ADC 226)
            self.adc_tile = self.rf.adc_tiles[2]
            self.adc_block = self.adc_tile.blocks[0]
        elif board == 'RFSoC2x2':
            self.dac_tile = self.rf.dac_tiles[1]
            self.dac_block = self.dac_tile.blocks[0]
            self.adc_tile = self.rf.adc_tiles[2]
            self.adc_block = self.adc_tile.blocks[0]
        elif board == 'ZCU111':
            self.dac_tile = self.rf.dac_tiles[1]
            self.dac_block = self.dac_tile.blocks[2]
            self.adc_tile = self.rf.adc_tiles[0]
            self.adc_block = self.adc_tile.blocks[0]
        else:
            raise RuntimeError('Unknown error occurred.')  # shouldn't get here

        # Start up LMX clock
        set_custom_lmclks()

        # Set DAC defaults
        self.dac_tile.DynamicPLLConfig(1, 409.6, 1024)
        self.dac_block.NyquistZone = 1
        self.dac_block.MixerSettings = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_IMMEDIATE,
            'FineMixerScale': xrfdc.MIXER_SCALE_0P7,
            'Freq': 1,
            'MixerMode': xrfdc.MIXER_MODE_C2R,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0.0
        }
        self.dac_block.UpdateEvent(xrfdc.EVENT_MIXER)
        self.dac_tile.SetupFIFO(True)

        # Set ADC defaults
        self.adc_tile.DynamicPLLConfig(1, 409.6, 1024)
        self.adc_block.NyquistZone = 1
        self.adc_block.MixerSettings = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': -1,
            'MixerMode': xrfdc.MIXER_MODE_R2C,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0.0
        }
        self.adc_block.UpdateEvent(xrfdc.EVENT_MIXER)
        self.adc_tile.SetupFIFO(True)

        # Perform self checking
        self.self_check()


class BlinkLedTask(OverlayTask):

    def __init__(self, overlay):
        super().__init__(overlay, name="BlinkLedTask")
        self.gleds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel1
        self.red_leds = AxiGPIO(self.ol.ip_dict['axi_gpio_led']).channel2
        for leds in [self.red_leds, self.gleds]:
            leds.setdirection("out")
            leds.setlength(8)

    def run(self):
        interval = 0.3
        while True:
            self.gleds.write(0xff, 0xff)
            time.sleep(interval)
            self.gleds.write(0x00, 0xff)
            time.sleep(interval)
