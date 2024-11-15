import logging
import xrfdc
import numpy as np
import time

from xrfdc import RFdcDacTile, RFdcAdcTile

from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class MyRFdcStatus:
    """Status of RF Data Converter"""

    def __init__(self, rfdc):
        self.dac_tile_status = rfdc.IPStatus['DACTileStatus']
        self.adc_tile_status = rfdc.IPStatus['ADCTileStatus']
        self.dac_clk_dist_status = rfdc.ClkDistribution['DAC']
        self.adc_clk_dist_status = rfdc.ClkDistribution['ADC']

    def get_dac_tile_enb(self, tile_id):
        return self.dac_tile_status[tile_id]['IsEnabled']

    def get_dac_tile_state(self, tile_id):
        return self.dac_tile_status[tile_id]['TileState']

    def get_dac_powerup_state(self, tile_id):
        return self.dac_tile_status[tile_id]['PowerUpState']

    def get_dac_pll_state(self, tile_id):
        return self.dac_tile_status[tile_id]['PLLState']

    def get_dac_block_enb(self, tile_id, block_id):
        return self.dac_tile_status[tile_id]['BlockStatusMask'] & (1 << block_id)

    def get_dac_clk_dist(self, tile_id):
        return self.dac_clk_dist_status[tile_id]

    def get_adc_tile_enb(self, tile_id):
        return self.adc_tile_status[tile_id]['IsEnabled']

    def get_adc_tile_state(self, tile_id):
        return self.adc_tile_status[tile_id]['TileState']

    def get_adc_powerup_state(self, tile_id):
        return self.adc_tile_status[tile_id]['PowerUpState']

    def get_adc_pll_state(self, tile_id):
        return self.adc_tile_status[tile_id]['PLLState']

    def get_adc_block_enb(self, tile_id, block_id):
        return self.adc_tile_status[tile_id]['BlockStatusMask'] & (1 << block_id)

    def get_adc_clk_dist(self, tile_id):
        return self.adc_clk_dist_status[tile_id]


class MyRFdcDACTile(RFdcDacTile):
    """New DAC tile class that inherits everything from Xilinx's RFdcDacTile class"""

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


class MyRFdcADCTile(RFdcAdcTile):
    """New ADC tile class that inherits everything from Xilinx's RFdcAdcTile class"""

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


class MyRFdcFreqConfig:
    """RFDC clock and sampling rate configuration"""

    def __init__(self, ref_clk, dac_samp_rate, dac_nco, dac_interp_rate, adc_samp_rate, adc_nco, adc_interp_rate, clock_src=xrfdc.CLK_SRC_PLL):
        self.ref_clk = ref_clk
        self.clock_src = clock_src
        self.dac_samp_rate = dac_samp_rate
        self.dac_nco = dac_nco
        self.dac_interp_rate = dac_interp_rate
        self.adc_samp_rate = adc_samp_rate
        self.adc_nco = adc_nco
        self.adc_interp_rate = adc_interp_rate
        self.check_config()

    def mandatory_check(self):
        # Check reference clock
        if self.clock_src == xrfdc.CLK_SRC_PLL:
            ref_clk_min, ref_clk_max = ZCU216_CONFIG['RefClockForPLLMin'], ZCU216_CONFIG['RefClockForPLLMax']
            assert self.ref_clk >= ref_clk_min and self.ref_clk <= ref_clk_max, f"Reference clock frequency shall fall between {ref_clk_min}, {ref_clk_max} Hz if on-chip PLL is enabled."
        else:  # xrfdc.CLK_SRC_EXT
            ref_clk_min_for_dac = ZCU216_CONFIG['RefClockNoPLLDacMin']
            ref_clk_max_for_dac = ZCU216_CONFIG['RefClockNoPLLDacMax']
            ref_clk_min_for_adc = ZCU216_CONFIG['RefClockNoPLLAdcMin']
            ref_clk_max_for_dac = ZCU216_CONFIG['RefClockNoPLLAdcMax']
            err_msg = f"Reference clock frequency shall be above DAC:{ref_clk_min_for_dac} or ADC:{ref_clk_min_for_adc} Hz if on-chip PLL is bypassed."
            assert self.ref_clk >= ref_clk_min_for_dac and self.ref_clk >= ref_clk_min_for_adc, err_msg
            err_msg = f"Reference clock frequency shall fall below DAC:{ref_clk_min_for_dac} or ADC:{ref_clk_min_for_adc} Hz if on-chip PLL is bypassed."
            if self.ref_clk > ref_clk_max_for_dac or self.ref_clk > ref_clk_min_for_dac:
                logging.warning(err_msg)
        # Check NCO range
        # err_msg = f"DAC NCO shall fall between -1/2*Fs and 1/2*Fs"
        # assert self.dac_samp_rate / 2 >= self.dac_nco >= -self.dac_samp_rate / 2, err_msg
        # err_msg = f"ADC NCO shall fall between 0 and 1/2*Fs"
        # assert self.adc_samp_rate / 2 >= self.adc_nco >= -self.adc_samp_rate / 2, err_msg

    def comm_sys_check(self):
        # Check NCO diirection
        err_msg = f"DAC NCO is normally > 0 while ADC is normally < 0"
        assert self.dac_nco >= 0 and self.adc_nco <= 0, err_msg

    def filter_check(self):
        # Check whether interpolation/decimator factor is valid
        valid_factor_list = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 40]
        assert self.dac_interp_rate in valid_factor_list and self.adc_interp_rate in valid_factor_list, f"Interpolation or decimation factor does not fall in the valid range."

    def check_config(self):
        self.checker_list = [self.mandatory_check,
                             self.comm_sys_check, self.filter_check]
        for checker in self.checker_list:
            checker()


class MyRFdcConfig:

    def __init__(self):
        self.freq_cfg = MyRFdcFreqConfig(
            ref_clk=ZCU216_CONFIG['RefClockForPLL'],
            dac_samp_rate=ZCU216_CONFIG['DACSampleRate'],
            dac_nco=ZCU216_CONFIG['DACNCO'],
            dac_interp_rate=ZCU216_CONFIG['DACInterpolationRate'],
            adc_samp_rate=ZCU216_CONFIG['ADCSampleRate'],
            adc_nco=ZCU216_CONFIG['ADCNCO'],
            adc_interp_rate=ZCU216_CONFIG['ADCInterpolationRate'],
            clock_src=xrfdc.CLK_SRC_PLL
        )

        self.dac_block_cfg = {
            'InterpolationFactor': self.freq_cfg.dac_interp_rate,
            'NyquistZone': 1,
            'UpdateEvent': xrfdc.EVENT_MIXER,
            'InvSincFIR': ZCU216_CONFIG['InvSincFIR'],
        }
        self.dac_block_mixer_cfg = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': self.freq_cfg.dac_nco,
            'MixerMode': xrfdc.MIXER_MODE_C2R,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0,
        }

        self.adc_block_cfg = {
            'DecimationFactor': self.freq_cfg.adc_interp_rate,
            'NyquistZone': 1,
            'UpdateEvent': xrfdc.EVENT_MIXER,
        }
        self.adc_block_mixer_cfg = {
            'CoarseMixFreq': xrfdc.COARSE_MIX_BYPASS,
            'EventSource': xrfdc.EVNT_SRC_TILE,
            'FineMixerScale': xrfdc.MIXER_SCALE_1P0,
            'Freq': self.freq_cfg.adc_nco,
            'MixerMode': xrfdc.MIXER_MODE_R2C,
            'MixerType': xrfdc.MIXER_TYPE_FINE,
            'PhaseOffset': 0
        }


class MyRFdc:
    """My class for controlling the RF Data Converter."""

    def __init__(self, rfdc_ip, debug_mode=False):
        self.rfdc = rfdc_ip
        self.rfdc_status = MyRFdcStatus(self.rfdc)
        self.rfdc_cfg = MyRFdcConfig()
        self.dac_tiles = [MyRFdcDACTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.dac_tiles)]
        self.adc_tiles = [MyRFdcADCTile(
            tile_id, tile) for tile_id, tile in enumerate(self.rfdc.adc_tiles)]
        self.clock_src = self.rfdc_cfg.freq_cfg.clock_src
        self.debug_mode = debug_mode

    def debug(self):
        # Attributes for both DAC and ADC blocks
        block_attr = ['BlockStatus', 'MixerSettings', 'QMCSettings',
                      'CoarseDelaySettings', 'NyquistZone', 'EnabledInterrupts', 'PwrMode']
        # Attributes for DAC block only
        dac_only_attr = ['InterpolationFactor', 'DecoderMode',  # 'OutputCurr',
                         'InvSincFIR', 'FabRdVldWords', 'FabWrVldWords', 'DataPathMode', 'IMRPassMode', 'DACCompMode']
        # Attributes for ADC block only
        adc_only_attr = ['DecimationFactor', 'CalibrationMode', 'FabRdVldWords',
                         'FabWrVldWords', 'DecimationFactorObs', 'FabRdVldWordsObs', 'FabWrVldWordsObs', 'Dither', 'CalFreeze', 'DSA']

        for tile in self.dac_tiles:
            if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
                for block_id, block in enumerate(tile.blocks):
                    if self.rfdc_status.get_dac_block_enb(
                            tile.tile_id, block_id):
                        for attr in block_attr:
                            logging.info(attr+": "+str(getattr(block, attr)))
                        for attr in dac_only_attr:
                            logging.info(attr+": "+str(getattr(block, attr)))
        for tile in self.adc_tiles:
            if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
                for block_id, block in enumerate(tile.blocks):
                    if self.rfdc_status.get_adc_block_enb(
                            tile.tile_id, block_id):
                        for attr in block_attr:
                            logging.info(attr+": "+str(getattr(block, attr)))
                        for attr in adc_only_attr:
                            logging.info(attr+": "+str(getattr(block, attr)))

    def init(self):
        """Power on DAC/ADC tiles"""
        # Power on DAC tiles
        for tile in self.dac_tiles:
            self.power_on_dac_tile(tile)
        # Power on ADC tiles
        for tile in self.adc_tiles:
            self.power_on_adc_tile(tile)

    def setup(self):
        """Configure DAC/ADC blocks"""
        # Configure DAC blocks within each tile
        for tile in self.dac_tiles:
            self.config_dac_blocks(tile)
        # Configure ADC blocks within each tile
        for tile in self.adc_tiles:
            self.config_adc_blocks(tile)

    def is_ready(self):
        """Check if all tiles are powered up"""
        for tile in self.dac_tiles:
            if not self.is_dac_tile_ready(tile):
                return False
        for tile in self.adc_tiles:
            if not self.is_adc_tile_ready(tile):
                return False
        return True

    def shutdown_tiles(self):
        """Safely shutdown all tiles."""
        for tile in self.dac_tiles:
            if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
                tile.ShutDown()
        for tile in self.adc_tiles:
            if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
                tile.ShutDown()
        logging.info(f"All tiles has been safely shutdown!")

    def is_dac_tile_ready(self, tile):
        tile_state = self.rfdc_status.get_dac_tile_state(tile.tile_id)
        if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
            return False if tile_state < 15 else True
        else:
            return True

    def power_on_dac_tile(self, tile):
        """Power on DAC tiles."""
        if self.rfdc_status.get_dac_tile_enb(tile.tile_id):
            # Configure a single tile
            tile.DynamicPLLConfig(
                self.clock_src, self.rfdc_cfg.freq_cfg.ref_clk, self.rfdc_cfg.freq_cfg.dac_samp_rate)
            time.sleep(1)
            tile.SetupFIFO(True)
            # Check tile state
            tile_state = self.rfdc_status.get_dac_tile_state(tile.tile_id)
            if tile_state < 15:
                err_msg = f"DAC tile {tile.tile_id} ({tile.tile_phy_id}) is NOT fully powered up! Stuck at Step {tile_state}: {MyRFdcType.POWER_ON_SEQUENCE_STEPS[tile_state]['State']} Description: {MyRFdcType.POWER_ON_SEQUENCE_STEPS[tile_state]['Description']}"
                if 6 <= tile_state <= 10 and self.debug_mode:
                    logging.info(
                        self.rfdc_status.get_dac_clk_dist(tile.tile_id))
                raise Exception(err_msg)
            logging.info(
                f"DAC tile {tile.tile_id} ({tile.tile_phy_id}) is fully powered up!")

    def is_adc_tile_ready(self, tile):
        tile_state = self.rfdc_status.get_adc_tile_state(tile.tile_id)
        if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
            return False if tile_state < 15 else True
        else:
            return True

    def power_on_adc_tile(self, tile):
        """Power on ADC tiles."""
        if self.rfdc_status.get_adc_tile_enb(tile.tile_id):
            # Configure a single tile
            tile.DynamicPLLConfig(
                self.clock_src, self.rfdc_cfg.freq_cfg.ref_clk, self.rfdc_cfg.freq_cfg.adc_samp_rate)
            time.sleep(1)
            tile.SetupFIFO(True)
            # Check tile state
            tile_state = self.rfdc_status.get_adc_tile_state(tile.tile_id)
            if tile_state < 15:
                err_msg = f"ADC tile {tile.tile_id} ({tile.tile_phy_id}) is NOT fully powered up! Stuck at Step {tile_state}: {MyRFdcType.POWER_ON_SEQUENCE_STEPS[tile_state]['State']} Description: {MyRFdcType.POWER_ON_SEQUENCE_STEPS[tile_state]['Description']}"
                if 6 <= tile_state <= 10 and self.debug_mode:
                    logging.info(
                        self.rfdc_status.get_adc_clk_dist(tile.tile_id))
                raise Exception(err_msg)
            logging.info(
                f"ADC tile {tile.tile_id} ({tile.tile_phy_id}) is fully powered up!")

    def config_dac_nco(self, tile, block_id, nco_freq_mhz):
        """Configure the NCO freq of a DAC block"""
        assert nco_freq_mhz >= 0, f"DAC NCO frequency {nco_freq_mhz} shall be >= 0."
        block = tile.blocks[block_id]
        block.MixerSettings['Freq'] = nco_freq_mhz
        block.UpdateEvent(xrfdc.EVENT_MIXER)
        logging.info(
            f"DAC tile {tile.tile_id} DAC block {block_id} NCO frequency is set to {nco_freq_mhz} MHz!")

    def config_dac_block(self, tile, block_id):
        """Configure a single DAC block within a tile."""
        block_enabled = self.rfdc_status.get_dac_block_enb(
            tile.tile_id, block_id)
        if block_enabled:
            block = tile.blocks[block_id]
            block.NyquistZone = self.rfdc_cfg.dac_block_cfg['NyquistZone']
            block.MixerSettings = self.rfdc_cfg.dac_block_mixer_cfg
            block.InterpolationFactor = self.rfdc_cfg.dac_block_cfg['InterpolationFactor']
            block.UpdateEvent(self.rfdc_cfg.dac_block_cfg['UpdateEvent'])
            block.QMCSettings = {'EnablePhase': 0, 'EnableGain': 0, 'GainCorrectionFactor': 0.0,
                                 'PhaseCorrectionFactor': 0.0, 'OffsetCorrectionFactor': 0, 'EventSource': xrfdc.EVNT_SRC_IMMEDIATE}
            block.InvSincFIR = self.rfdc_cfg.dac_block_cfg['InvSincFIR']
            logging.info(
                f"DAC tile {tile.tile_id} DAC block {block_id} is enabled!")
        else:
            logging.info(
                f"DAC tile {tile.tile_id} DAC block {block_id} is NOT enabled!")

    def config_dac_blocks(self, tile):
        """Configure all DAC blocks within a tile."""
        for block_id in range(len(tile.blocks)):
            self.config_dac_block(tile, block_id)

    def config_adc_nco(self, tile, block_id, nco_freq_mhz):
        """Configure the NCO freq of an ADC block"""
        assert nco_freq_mhz <= 0, f"ADC NCO frequency {nco_freq_mhz} shall be <= 0 "
        block = tile.blocks[block_id]
        block.MixerSettings['Freq'] = nco_freq_mhz
        block.UpdateEvent(xrfdc.EVENT_MIXER)
        logging.info(
            f"ADC tile {tile.tile_id} ADC block {block_id} NCO frequency is set to {nco_freq_mhz} MHz!")

    def config_adc_block(self, tile, block_id):
        """Configure a single ADC block within a tile."""
        block_enabled = self.rfdc_status.get_adc_block_enb(
            tile.tile_id, block_id)
        if block_enabled:
            block = tile.blocks[block_id]
            block.NyquistZone = self.rfdc_cfg.adc_block_cfg['NyquistZone']
            block.MixerSettings = self.rfdc_cfg.adc_block_mixer_cfg
            block.DecimationFactor = self.rfdc_cfg.adc_block_cfg['DecimationFactor']
            block.UpdateEvent(self.rfdc_cfg.adc_block_cfg['UpdateEvent'])
            block.QMCSettings = {'EnablePhase': 0, 'EnableGain': 0, 'GainCorrectionFactor': 0.0,
                                 'PhaseCorrectionFactor': 0.0, 'OffsetCorrectionFactor': 0, 'EventSource': xrfdc.EVNT_SRC_IMMEDIATE}
            logging.info(
                f"ADC tile {tile.tile_id} ADC block {block_id} is enabled!")
        else:
            logging.info(
                f"ADC tile {tile.tile_id} ADC block {block_id} is NOT enabled!")

    def config_adc_blocks(self, tile):
        """Configure all ADC blocks within a tile."""
        for block_id in range(len(tile.blocks)):
            self.config_adc_block(tile, block_id)


class MyRFdcType:

    DATA_PATH_DTYPE = np.int16

    DAC_MIN_SCALE = -2**13
    DAC_MAX_SCALE = 2**13

    # Power-on Sequence Steps from page 163 of PG269: Zynq UltraScale+ RFSoC RF Data Converter v2.4 Gen 1/2/3
    POWER_ON_STATES = [
        "[Device Power-up and Configuration]",
        "[Power Supply Adjustment]",
        "[Clock Configuration]",
        "[Converter Calibration (ADC only)]",
        "[Wait for deassertion of AXI4-Stream reset]",
        "[Done]"
    ]

    POWER_ON_DESC = [
        "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]",
        "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]",
        "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]",
        "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]",
        "[The AXI4-Stream reset for the tile should be asserted until the AXI4-Stream clocks are stable. For example, if the clock is provided by a MMCM, the reset should be held until it has achieved lock. The state machine waits in this state until the reset is deasserted.]",
        "[The state machine has completed the power-up sequence.]"
    ]

    POWER_ON_SEQUENCE_STEPS = [
        {
            "Sequence Number": 0,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 1,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 2,
            "State": POWER_ON_STATES[0],
            "Description": POWER_ON_DESC[0]
        },
        {
            "Sequence Number": 3,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 4,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 5,
            "State": POWER_ON_STATES[1],
            "Description": POWER_ON_DESC[1]
        },
        {
            "Sequence Number": 6,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 7,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 8,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 9,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 10,
            "State": POWER_ON_STATES[2],
            "Description": POWER_ON_DESC[2]
        },
        {
            "Sequence Number": 11,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 12,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 13,
            "State": POWER_ON_STATES[3],
            "Description": POWER_ON_DESC[3]
        },
        {
            "Sequence Number": 14,
            "State": POWER_ON_STATES[4],
            "Description": POWER_ON_DESC[4]
        },
        {
            "Sequence Number": 15,
            "State": POWER_ON_STATES[5],
            "Description": POWER_ON_DESC[5]
        }
    ]

    def __init__(self):
        pass
