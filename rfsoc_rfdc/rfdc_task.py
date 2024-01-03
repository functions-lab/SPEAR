import logging
import xrfdc
from .clocks import set_custom_lmclks
from .overlay_task import OverlayTask
from .rfdc_type import RfDcType

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class RfdcTask(OverlayTask):
    """Task for configuring RF data converters."""

    def __init__(self, overlay):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.rf = self.ol.usp_rf_data_converter

    def run(self):
        """Run the task."""
        set_custom_lmclks()
        # Configure DAC tiles
        dac_pll_settings = {
            'PLLFreq': 409.6,
            'SampleFreq': 1024
        }
        dac_mixer_settings = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': 0,
            'MixerMode': xrfdc.MIXER_MODE_C2R,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0
        }
        self.configure_tiles(
            self.rf.dac_tiles, 'DACTileStatus', dac_pll_settings, dac_mixer_settings)

        # Configure ADC tiles
        adc_pll_settings = {
            'PLLFreq': 409.6,
            'SampleFreq': 1024
        }
        adc_mixer_settings = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': 0,
            'MixerMode': xrfdc.MIXER_MODE_R2C,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0
        }
        self.configure_tiles(
            self.rf.adc_tiles, 'ADCTileStatus', adc_pll_settings, adc_mixer_settings)

    def configure_tiles(self, tiles, tile_status_key, pll_settings, mixer_settings):
        """Configure all tiles."""
        for tile_idx, tile in enumerate(tiles):
            status = self.rf.IPStatus[tile_status_key][tile_idx]
            if status['IsEnabled'] == 1:
                self.configure_tile(
                    tile, pll_settings['PLLFreq'], pll_settings['SampleFreq'])
                # Check tile status
                for step in RfDcType.POWER_ON_SEQUENCE_STEPS:
                    if status['TileState'] == step['Sequence Number']:
                        if step['Sequence Number'] != 15:
                            err_msg = f"Tile {tile_idx} is NOT fully powered up! Stuck at Step: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"Tile {tile_idx} is fully powered up!")
                        break
                self.configure_blocks(
                    tile, status['BlockStatusMask'], mixer_settings)

    def configure_tile(self, tile, pll_freq, freq_sample):
        """Configure a single tile."""
        tile.DynamicPLLConfig(1, pll_freq, freq_sample)
        tile.SetupFIFO(True)

    def configure_blocks(self, tile, block_status, mixer_settings):
        """Configure all blocks within a tile."""
        block_mask = 0x1
        for block in tile.blocks:
            block_id = (block_mask & -block_mask).bit_length() - 1  # ctz
            if block_status & block_mask != 0:
                self.configure_block(block, block_id, mixer_settings)
            else:
                logging.info(f"Block {block_id} is NOT enabled!")
            block_mask = block_mask << 1

    def configure_block(self, block, block_id, mixer_settings):
        """Configure a single block."""
        block.NyquistZone = 1
        block.MixerSettings = mixer_settings
        block.UpdateEvent(xrfdc.EVENT_MIXER)
        logging.info(f"Block {block_id} is enabled!")
