import logging
import xrfdc
import numpy as np
import time

from xrfdc import RFdcDacTile, RFdcAdcTile


class RfDataConverterStatus:
    """
    Class for fetching the status of RF Data Converter tiles (both DAC and ADC).

    Attributes:
        dac_tiles_status: Status of DAC tiles.
        adc_tiles_status: Status of ADC tiles.
    """
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
    """
    Class representing a DAC tile in the RF Data Converter.

    Inherits from RFdcDacTile.

    Attributes:
        tile_id: The ID of the DAC tile.
        tile_phy_id: The physical ID of the DAC tile.
    """

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
    """
    Class representing an ADC tile in the RF Data Converter.

    Inherits from RFdcAdcTile.

    Attributes:
        tile_id: The ID of the ADC tile.
        tile_read_id: The read ID of the ADC tile.
    """

    def __init__(self, tile_id, rfdc_adc_tile=None):
        if rfdc_adc_tile is not None:
            self.__dict__.update(rfdc_adc_tile.__dict__)
        self._tile_id = tile_id
        self._tile_phy_id = tile_id + 224

    @property
    def tile_id(self):
        return self._tile_id

    @property
    def tile_phy_id(self):
        return self._tile_phy_id


class RfDataConverter:
    """
    Main class for controlling the RF Data Converter, including both DAC and ADC tiles.

    Attributes:
        rfdc: The RF data converter overlay instance.
        rfdc_status: Instance of RfDataConverterStatus for status monitoring.
        dac_tiles: List of RfDataConverterDACTile.
        adc_tiles: List of RfDataConverterADCTile.
        clock_src: Type of clock source for the RF data converter. Default to PLL clock.
    """

    def __init__(self, overlay, clock_src=xrfdc.CLK_SRC_PLL, debug_mode=False):
        self.rfdc = overlay.usp_rf_data_converter
        self.rfdc_status = RfDataConverterStatus(overlay)
        self.dac_tiles = [RfDataConverterDACTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.dac_tiles)]
        self.adc_tiles = [RfDataConverterADCTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.adc_tiles)]
        self.clock_src = clock_src
        self.debug_mode = debug_mode

    def __del__(self):
        """Shutdown RF data converters safely."""
        self.shutdown_tiles()

    def init_setup(self, dac_samp_rate=2e9, adc_samp_rate=2e9, carrier_freq=0.5e9):
        """Perform initial setup for RF data converters."""
        carrier_freq_mhz = carrier_freq / 1e6

        self.dac_tile_config = {
            'RefClkMhz': 500.0,
            'SampleFreqMhz': dac_samp_rate / 1e6,  # On-chip PLL ranges from 500M-6.8G
            'SampleFreqGHz': dac_samp_rate / 1e9,
        }
        self.dac_block_config = {
            'InterpolationFactor': 20,  # 1x,2x,3x,4x,5x,6x,8x,10x,12x,16x,20x,24x,40x
            'NyquistZone': 1,
            'UpdateEvent': xrfdc.EVENT_MIXER,
        }
        self.dac_block_mixer_config = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': carrier_freq_mhz,
            'MixerMode': xrfdc.MIXER_MODE_C2R,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0,
        }

        self.adc_tile_config = {
            'RefClkMhz': 500.0,
            'SampleFreqMhz': adc_samp_rate / 1e6,  # On-chip PLL ranges from 500M-2.5G
            'SampleFreqGHz': adc_samp_rate / 1e9,
        }
        self.adc_block_config = {
            'DecimationFactor': 20,  # 1x,2x,3x,4x,5x,6x,8x,10x,12x,16x,20x,24x,40x
            'NyquistZone': 1,
            'UpdateEvent': xrfdc.EVENT_MIXER,
        }
        self.adc_block_mixer_config = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': -carrier_freq_mhz,
            'MixerMode': xrfdc.MIXER_MODE_R2C,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0
        }

        def gen_nco_warning(samp_mhz, carrier_mhz):
            return f"NCO frequency shall range from -{samp_mhz/2} MHz to {samp_mhz/2} MHz while you set {carrier_mhz} MHz"

        # NCO freq checker: -Fs/2 to Fs/2
        dac_samp_rate = self.dac_tile_config['SampleFreqMhz']
        adc_samp_rate = self.adc_tile_config['SampleFreqMhz']

        if carrier_freq_mhz > dac_samp_rate / 2:
            logging.info(
                "DAC " + gen_nco_warning(dac_samp_rate, carrier_freq_mhz))
        if carrier_freq_mhz > adc_samp_rate / 2:
            logging.info(
                "ADC " + gen_nco_warning(adc_samp_rate, carrier_freq_mhz))

        self.config_dac_tiles()  # Configure DAC tiles
        self.config_adc_tiles()  # Configure ADC tiles

    def shutdown_tiles(self):
        """Safely shutdown all tiles."""
        for tile in self.dac_tiles:
            tile.Shutdown()
        for tile in self.adc_tiles:
            tile.Shutdown()
        logging.info(f"All tiles has been safely shutdown!")

    def dump_dac_clk(self, tile_id):
        logging.info(
            f"IPStatus: {self.rfdc.IPStatus['DACTileStatus'][tile_id]}")
        logging.info(
            f"ClkDistribution: {self.rfdc.ClkDistribution['DAC'][tile_id]}")

    def dump_adc_clk(self, tile_id):
        logging.info(
            f"IPStatus: {self.rfdc.IPStatus['ADCTileStatus'][tile_id]}")
        logging.info(
            f"ClkDistribution: {self.rfdc.ClkDistribution['ADC'][tile_id]}")

    def config_dac_tiles(self):
        """Configure DAC tiles."""
        for tile in self.dac_tiles:
            if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
                # Configure a single tile
                tile.DynamicPLLConfig(
                    self.clock_src, self.dac_tile_config['RefClkMhz'], self.dac_tile_config['SampleFreqMhz'])
                time.sleep(1)
                tile.SetupFIFO(True)
                # Check tile state
                tile_state = self.rfdc_status.get_dac_tile_state(tile.tile_id)
                for step in RfDataConverterType.POWER_ON_SEQUENCE_STEPS:
                    if tile_state == step['Sequence Number']:
                        clock_dist_fail = (10 >= step['Sequence Number'] >= 6)
                        if clock_dist_fail and self.debug_mode:
                            self.dump_dac_clk(tile.tile_id)
                        if step['Sequence Number'] != 15:
                            err_msg = f"DAC tile {tile.tile_id} ({tile.tile_phy_id}) is NOT fully powered up! Stuck at Step {tile_state}: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"DAC tile {tile.tile_id} ({tile.tile_phy_id}) is fully powered up!")
                        break
                self.config_dac_blocks(tile)

    def config_adc_tiles(self):
        """Configure ADC tiles."""
        for tile in self.adc_tiles:
            if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
                # Configure a single tile
                tile.DynamicPLLConfig(
                    self.clock_src, self.adc_tile_config['RefClkMhz'], self.adc_tile_config['SampleFreqMhz'])
                time.sleep(1)
                tile.SetupFIFO(True)
                # Check tile state
                tile_state = self.rfdc_status.get_adc_tile_state(tile.tile_id)
                for step in RfDataConverterType.POWER_ON_SEQUENCE_STEPS:
                    if tile_state == step['Sequence Number']:
                        clock_dist_fail = (10 >= step['Sequence Number'] >= 6)
                        if clock_dist_fail and self.debug_mode:
                            self.dump_adc_clk(tile.tile_id)
                        if step['Sequence Number'] != 15:
                            err_msg = f"ADC tile {tile.tile_id} ({tile.tile_phy_id}) is NOT fully powered up! Stuck at Step {tile_state}: {step['State']} Description: {step['Description']}"
                            raise Exception(err_msg)
                        else:
                            logging.info(
                                f"ADC tile {tile.tile_id} ({tile.tile_phy_id}) is fully powered up!")
                        break
                self.config_adc_blocks(tile)

    def config_dac_blocks(self, tile):
        """Configure all DAC blocks within a tile."""
        block_mask = 0x1
        for block_id, block in enumerate(tile.blocks):
            block_enabled = self.rfdc_status.get_dac_block_enb(
                tile.tile_id, block_id)
            if block_enabled:
                # Configure a single block
                block.NyquistZone = self.dac_block_config['NyquistZone']
                block.MixerSettings = self.dac_block_mixer_config
                block.InterpolationFactor = self.dac_block_config['InterpolationFactor']
                block.UpdateEvent(self.dac_block_config['UpdateEvent'])
                logging.info(
                    f"DAC tile {tile.tile_id} DAC block {block_id} is enabled!")
            else:
                logging.info(
                    f"DAC tile {tile.tile_id} DAC block {block_id} is NOT enabled!")
            block_mask = block_mask << 1

    def config_adc_blocks(self, tile):
        """Configure all ADC blocks within a tile."""
        block_mask = 0x1
        for block_id, block in enumerate(tile.blocks):
            block_enabled = self.rfdc_status.get_adc_block_enb(
                tile.tile_id, block_id)
            if block_enabled:
                # Configure a single block
                block.NyquistZone = self.adc_block_config['NyquistZone']
                block.MixerSettings = self.adc_block_mixer_config
                block.DecimationFactor = self.adc_block_config['DecimationFactor']
                block.UpdateEvent(self.adc_block_config['UpdateEvent'])
                logging.info(
                    f"ADC tile {tile.tile_id} ADC block {block_id} is enabled!")
            else:
                logging.info(
                    f"ADC tile {tile.tile_id} ADC block {block_id} is NOT enabled!")
            block_mask = block_mask << 1


class RfDataConverterType:

    DATA_PATH_DTYPE = np.int16

    DAC_MIN_SCALE = -2**13
    DAC_MAX_SCALE = (2**13 - 1)

    # Power-on Sequence Steps from page 163 of PG269: Zynq UltraScale+ RFSoC RF Data Converter v2.4 Gen 1/2/3
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
