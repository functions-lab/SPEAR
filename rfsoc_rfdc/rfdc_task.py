from rfsoc_rfdc.clocks import set_custom_lmclks
from rfsoc_rfdc.overlay_task import OverlayTask
from rfsoc_rfdc.rfdc import MyRFdc

from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class RfdcTask(OverlayTask):
    """Task for configuring RF data converters."""

    def __init__(self, overlay):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.rfdc = MyRFdc(overlay, debug_mode=True)

    def run(self):
        """Run the task."""
        if not self.rfdc.is_ready():
            # Configure external PLL clocks
            set_custom_lmclks()
            # Initialize RF data converters
            self.rfdc.init()
        # Config DAC/ADC to target GSPS & Interp/Decim Factor
        self.rfdc.setup()


class RfdcMultiBandTask(RfdcTask):

    def set_nco(self):
        # Additional configuration for DAC NCO
        dac_nco_mhz = ZCU216_CONFIG['DACNCO']
        dac_nco_offset = ZCU216_CONFIG['DACSampleRate'] / \
            ZCU216_CONFIG['DACInterpolationRate'] + 50
        tile = self.rfdc.dac_tiles[2]  # Use 2nd tile only
        self.rfdc.config_dac_nco(tile, 0, dac_nco_mhz)  # Set 1st DAC NCO
        for block_id in [1, 2, 3]:
            dac_nco_mhz += dac_nco_offset
            self.rfdc.config_dac_nco(tile, block_id, dac_nco_mhz)
        # Additional configuration for ADC NCO
        adc_nco_mhz = ZCU216_CONFIG['ADCNCO']
        adc_nco_offset = ZCU216_CONFIG['ADCSampleRate'] / \
            ZCU216_CONFIG['ADCInterpolationRate'] - 50
        tile = self.rfdc.adc_tiles[2]  # Use 2nd tile only
        self.rfdc.config_adc_nco(tile, 0, adc_nco_mhz)  # Set 1st ADC NCO
        for block_id in [1, 2, 3]:
            adc_nco_mhz -= adc_nco_offset
            self.rfdc.config_adc_nco(tile, block_id, adc_nco_mhz)

    def run(self):
        super().run()
        # Customly set DAC/ADC NCO
        self.set_nco()
