import logging
import xrfdc

from xrfdc import RFdcDacTile, RFdcAdcTile

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class RfDataConverterStatus:

    DAC_TILE_STATUS_KEY = 'DACTileStatus'
    ADC_TILE_STATUS_KEY = 'ADCTileStatus'

    def __init__(self, overlay):
        self.dac_tiles_status = overlay.usp_rf_data_converter.IPStatus[self.DAC_TILE_STATUS_KEY]
        self.adc_tiles_status = overlay.usp_rf_data_converter.IPStatus[self.ADC_TILE_STATUS_KEY]

    def get_dac_tile_enb(self, tile_id):
        return self.dac_tiles_status[tile_id]['IsEnabled']

    def get_dac_tile_state(self, tile_id):
        return self.dac_tiles_status[tile_id]['TileState']

    def get_dac_powerup_state(self, tile_id):
        return self.dac_tiles_status[tile_id]['PowerUpState']

    def get_dac_pll_state(self, tile_id):
        return self.dac_tiles_status[tile_id]['PLLState']

    def get_dac_block_enb(self, tile_id, block_id):
        return self.dac_tiles_status[tile_id]['BlockStatusMask'] & (1 << block_id)

    def get_adc_tile_enb(self, tile_id):
        return self.adc_tiles_status[tile_id]['IsEnabled']

    def get_adc_tile_state(self, tile_id):
        return self.adc_tiles_status[tile_id]['TileState']

    def get_adc_powerup_state(self, tile_id):
        return self.adc_tiles_status[tile_id]['PowerUpState']

    def get_adc_pll_state(self, tile_id):
        return self.adc_tiles_status[tile_id]['PLLState']

    def get_adc_block_enb(self, tile_id, block_id):
        return self.adc_tiles_status[tile_id]['BlockStatusMask'] & (1 << block_id)


class RfDataConverterDACTile(RFdcDacTile):
    def __init__(self, tile_id, rfdc_dac_tile=None):
        if rfdc_dac_tile is not None:
            # The __dict__ of an instance holds all instance attributes, the above merely copies over all of those attributes to the new instance.
            self.__dict__.update(rfdc_dac_tile.__dict__)
        self._tile_id = tile_id
        self._tile_phy_id = tile_id + 228

    @property
    def tile_id(self):
        return self._tile_id

    @property
    def tile_phy_id(self):
        return self._tile_phy_id


class RfDataConverterADCTile(RFdcAdcTile):
    def __init__(self, tile_id, rfdc_adc_tile=None):
        if rfdc_adc_tile is not None:
            self.__dict__.update(rfdc_adc_tile.__dict__)
        self._tile_id = tile_id
        self._tile_read_id = tile_id + 224

    @property
    def tile_id(self):
        return self._tile_id

    @property
    def tile_phy_id(self):
        return self._tile_phy_id


class RfDataConverter:
    def __init__(self, overlay):
        self.rfdc = overlay.usp_rf_data_converter
        self.rfdc_status = RfDataConverterStatus(overlay)
        self.dac_tiles = [RfDataConverterDACTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.dac_tiles)]
        self.adc_tiles = [RfDataConverterADCTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.adc_tiles)]

    def __del__(self):
        """Shutdown RF data converters safely."""
        self.shutdown_tiles(self.dac_tiles)
        self.shutdown_tiles(self.adc_tiles)

    def init_setup(self):
        """Perform initial setup for RF data converters."""
        update_event = xrfdc.EVENT_MIXER
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
        self.config_dac_tiles(
            self.dac_tiles, dac_pll_settings, dac_mixer_settings, update_event)

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
        self.config_adc_tiles(
            self.adc_tiles, adc_pll_settings, adc_mixer_settings, update_event)

    def shutdown_tiles(self, tiles):
        for tile in tiles:
            tile.Shutdown()
        logging.info(f"All tiles has been safely shutdown!")

    def config_dac_tiles(self, tiles, pll_settings, mixer_settings, event_settings):
        """Configure DAC tiles."""
        for tile in tiles:
            if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
                # Config tile
                self.config_tile(
                    tile, pll_settings['PLLFreq'], pll_settings['SampleFreq'])
                # Check tile status
                tile_state = self.rfdc_status.get_dac_tile_state(tile.tile_id)
                for step in RfDataConverterType.POWER_ON_SEQUENCE_STEPS:
                    if tile_state == step['Sequence Number']:
                        if step['Sequence Number'] != 15:
                            err_msg = f"DAC tile {tile.tile_id} is NOT fully powered up! Stuck at Step: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"DAC tile {tile.tile_id} is fully powered up!")
                        break
                self.config_dac_blocks(tile, mixer_settings, event_settings)

    def config_adc_tiles(self, tiles, pll_settings, mixer_settings, event_settings):
        """Configure ADC tiles."""
        for tile in tiles:
            if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
                # Config tile
                self.config_tile(
                    tile, pll_settings['PLLFreq'], pll_settings['SampleFreq'])
                # Check tile status
                tile_state = self.rfdc_status.get_adc_tile_state(tile.tile_id)
                for step in RfDataConverterType.POWER_ON_SEQUENCE_STEPS:
                    if tile_state == step['Sequence Number']:
                        if step['Sequence Number'] != 15:
                            err_msg = f"ADC tile {tile.tile_id} is NOT fully powered up! Stuck at Step: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"ADC tile {tile.tile_id} is fully powered up!")
                        break
                self.config_adc_blocks(tile, mixer_settings, event_settings)

    def config_tile(self, tile, pll_freq, sample_freq):
        """Configure a single tile."""
        tile.DynamicPLLConfig(1, pll_freq, sample_freq)
        tile.SetupFIFO(True)

    def config_dac_blocks(self, tile, mixer_settings, event_settings):
        """Configure all DAC blocks within a tile."""
        block_mask = 0x1
        for block_id, block in enumerate(tile.blocks):
            block_enabled = self.rfdc_status.get_dac_block_enb(
                tile.tile_id, block_id)
            if block_enabled:
                self.config_block(block, mixer_settings, event_settings)
                logging.info(
                    f"DAC tile {tile.tile_id} DAC block {block_id} is enabled!")
            else:
                logging.info(
                    f"DAC tile {tile.tile_id} DAC block {block_id} is NOT enabled!")
            block_mask = block_mask << 1

    def config_adc_blocks(self, tile, mixer_settings, event_settings):
        """Configure all ADC blocks within a tile."""
        block_mask = 0x1
        for block_id, block in enumerate(tile.blocks):
            block_enabled = self.rfdc_status.get_adc_block_enb(
                tile.tile_id, block_id)
            if block_enabled:
                self.config_block(block, mixer_settings, event_settings)
                logging.info(
                    f"ADC tile {tile.tile_id} ADC block {block_id} is enabled!")
            else:
                logging.info(
                    f"ADC tile {tile.tile_id} ADC block {block_id} is NOT enabled!")
            block_mask = block_mask << 1

    def config_block(self, block, mixer_settings, event_settings):
        """Configure a single block."""
        block.NyquistZone = 1
        block.MixerSettings = mixer_settings
        block.UpdateEvent(event_settings)

# Power-on Sequence Steps from page 163 of PG269: Zynq UltraScale+ RFSoC RF Data Converter v2.4 Gen 1/2/3


class RfDataConverterType:

    POWER_ON_SEQUENCE_STEPS = [
        {
            "Sequence Number": 0,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 1,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 2,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 3,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 4,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 5,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 6,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 7,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 8,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 9,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 10,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 11,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 12,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 13,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 14,
            "State": "[Wait for deassertion of AXI4-Stream reset]",
            "Description": "[The AXI4-Stream reset for the tile should be asserted until the AXI4-Stream clocks are stable. For example, if the clock is provided by a MMCM, the reset should be held until it has achieved lock. The state machine waits in this state until the reset is deasserted.]"
        },
        {
            "Sequence Number": 15,
            "State": "[Done]",
            "Description": "[The state machine has completed the power-up sequence.]"
        }
    ]

    def __init__(self):
        pass
