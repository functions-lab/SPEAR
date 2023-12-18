import numpy as np
import threading
from abc import ABC, abstractmethod

import xrfclk
import xrfdc

from .recv_plotter import RecvDataPlotter
import matplotlib.pyplot as plt

from .waveform_generator import WaveFormGenerator

from .clocks import set_custom_lmclks
from .rfsoc_overlay import RFSoCOverlay

from pynq import allocate

import os
import time
from pynq.lib import AxiGPIO
from pynq import DefaultIP


class OverlayTask(ABC):
    def __init__(self, overlay, name="OverlayTask"):
        if not isinstance(overlay, RFSoCOverlay):
            raise TypeError("This task is not an RFSoCOverlay instance.")
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
    def __init__(self, overlay, num_of_pts_plotted=512, buffer_size=512):
        super().__init__(overlay, name="ReceiverTask")
        self.rx_dma = self.ol.axi_dma_adc2
        self.buffer_size = buffer_size
        self.rx_buff = allocate(shape=(self.buffer_size,), dtype=np.uint16)
        self.plotter = RecvDataPlotter(num_of_pts_plotted)

    def run(self):
        recv_ch = self.rx_dma.recvchannel
        while True:
            try:
                prev_time = time.time_ns()

                recv_ch.transfer(self.rx_buff)
                recv_ch.wait()

                # Update the plot using the new DataPlotter class
                self.plotter.update_plot(self.rx_buff)

                plt.pause(0.001)  # Still needed to update the plot

            except Exception as e:
                print("Get the info from DMA registers",
                      self.rx_dma.register_map)
                print(e)


class TransmitterTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="TransmitterTask")
        # DMA
        self.tx_dma = self.ol.t230_dac0.axi_dma
        # FIFO control
        self.fifo_wr_count = AxiGPIO(
            self.ol.ip_dict['t230_dac0/fifo_status']).channel1
        self.fifo_wr_count.setdirection("in")
        self.fifo_wr_count.setlength(32)

        self.fifo_full = AxiGPIO(
            self.ol.ip_dict['t230_dac0/fifo_status']).channel2
        self.fifo_full.setdirection("in")
        self.fifo_full.setlength(1)

        # Initialize WaveForm class
        self.wg = WaveFormGenerator()

        # Generate testing waveform (e.g., sine wave)
        self.seq = self.wg.generate_sine_wave(
            repeat_time=1000, sample_pts=1000)

    def get_fifo_status(self):
        a = self.fifo_wr_count.read()
        b = self.fifo_full.read()
        return a, b

    def run(self):

        self.tx_buff = allocate(shape=(self.seq.shape[0],), dtype=np.int16)
        self.tx_buff[:] = self.seq

        while True:
            count, status = self.get_fifo_status()
            # print("FIFO count: ", count, "FIFO is_full: ", status)
            self.tx_dma.sendchannel.transfer(self.tx_buff)
            self.tx_dma.sendchannel.wait()  # blocking wait


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
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_0P7,
            'Freq': 3,
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
            'Freq': 0,
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
