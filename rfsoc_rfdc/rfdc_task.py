import xrfdc
import os
import time
from .clocks import set_custom_lmclks
from .overlay_task import OverlayTask


class RfdcTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="RfdcTask")
        self.rf = self.ol.usp_rf_data_converter

    def run(self):
        # Get board name
        board_name = os.environ['BOARD']

        # Start up LMX clock
        set_custom_lmclks()
        time.sleep(3)

        # Configure DACs
        for tile_idx, tile in enumerate(self.rf.dac_tiles):
            status = self.rf.IPStatus['DACTileStatus'][tile_idx]

            if status['IsEnabled'] == 1:
                # Configure DAC Tile
                tile.DynamicPLLConfig(1, 409.6, 1024)
                tile.SetupFIFO(True)
                # Check DAC tile enable status
                if status['TileState'] != 15:
                    print(status)
                    raise Exception(
                        f"DAC Tile {tile_idx} is not fully powered up!")

                # Configure DAC in a tile
                block_mask = 0x1
                for dac in tile.blocks:
                    if status['BlockStatusMask'] & block_mask != 0:
                        dac.NyquistZone = 1
                        dac.MixerSettings = {
                            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
                            'EventSource': xrfdc.EVNT_SRC_TILE,
                            'FineMixerScale': xrfdc.MIXER_SCALE_0P7,
                            'Freq': 0,
                            'MixerMode': xrfdc.MIXER_MODE_C2R,
                            'MixerType': xrfdc.MIXER_TYPE_FINE,
                            'PhaseOffset': 0.0
                        }
                        dac.UpdateEvent(xrfdc.EVENT_MIXER)
                    block_mask = block_mask << 1

        # Configure ADCs
        for tile_idx, tile in enumerate(self.rf.adc_tiles):
            status = self.rf.IPStatus['ADCTileStatus'][tile_idx]

            if status['IsEnabled'] == 1:
                # Configure ADC Tile
                tile.DynamicPLLConfig(1, 409.6, 1024)
                tile.SetupFIFO(True)
                # Check ADC tile enable status
                if status['TileState'] != 15:
                    print(status)
                    raise Exception(
                        f"ADC Tile {tile_idx} is not fully powered up!")

                # Configure DAC in a tile
                block_mask = 0x1
                for adc in tile.blocks:
                    if status['BlockStatusMask'] & block_mask != 0:
                        adc.NyquistZone = 1
                        adc.MixerSettings = {
                            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
                            'EventSource': xrfdc.EVNT_SRC_TILE,
                            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
                            'Freq': 0,
                            'MixerMode': xrfdc.MIXER_MODE_R2C,
                            'MixerType': xrfdc.MIXER_TYPE_FINE,
                            'PhaseOffset': 0.0
                        }
                        adc.UpdateEvent(xrfdc.EVENT_MIXER)
                    block_mask = block_mask << 1
