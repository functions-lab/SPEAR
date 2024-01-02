import logging
import xrfdc
from .clocks import set_custom_lmclks
from .overlay_task import OverlayTask
from .rfdc_type import RfDcType

# Basic logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class RfdcTask(OverlayTask):
    def __init__(self, overlay):
        super().__init__(overlay, name="RfdcTask")
        self.rf = self.ol.usp_rf_data_converter

    def run(self):
        # Get board name
        # board_name = os.environ['BOARD']

        # Start up LMX clock
        set_custom_lmclks()

        # Configure all DACs
        for tile_idx, tile in enumerate(self.rf.dac_tiles):
            status = self.rf.IPStatus['DACTileStatus'][tile_idx]

            if status['IsEnabled'] == 1:
                # Configure DAC Tile
                tile.DynamicPLLConfig(1, 409.6, 1024)
                tile.SetupFIFO(True)
                # Check DAC tile enable status
                for step in RfDcType.POWER_ON_SEQUENCE_STEPS:
                    if status['TileState'] == step['Sequence Number']:
                        if step['Sequence Number'] != 15:
                            err_msg = f"DAC Tile {tile_idx} is NOT fully powered up! Stuck at Step: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"DAC Tile {tile_idx} is fully powered up!")
                        break
                # Configure each DAC within a tile
                block_mask = 0x1
                for dac in tile.blocks:
                    block_id = (block_mask & -block_mask).bit_length() - 1
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
                        logging.info(f"DAC block {block_id} is enabled!")
                    else:
                        logging.info(f"DAC block {block_id} is NOT enabled!")
                    block_mask = block_mask << 1

        # Configure all ADCs
        for tile_idx, tile in enumerate(self.rf.adc_tiles):
            status = self.rf.IPStatus['ADCTileStatus'][tile_idx]

            if status['IsEnabled'] == 1:
                # Configure ADC Tile
                tile.DynamicPLLConfig(1, 409.6, 1024)
                tile.SetupFIFO(True)
                # Check ADC tile enable status
                for step in RfDcType.POWER_ON_SEQUENCE_STEPS:
                    if status['TileState'] == step['Sequence Number']:
                        if step['Sequence Number'] != 15:
                            err_msg = f"ADC Tile {tile_idx} is NOT fully powered up! Stuck at Step: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"ADC Tile {tile_idx} is fully powered up!")
                        break
                # Configure each ADC within a tile
                block_mask = 0x1
                for adc in tile.blocks:
                    block_id = (block_mask & -block_mask).bit_length() - 1
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
                        logging.info(f"ADC block {block_id} is enabled!")
                    else:
                        logging.info(f"ADC block {block_id} is NOT enabled!")
                    block_mask = block_mask << 1
