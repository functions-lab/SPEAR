from .clocks import set_custom_lmclks
from .overlay_task import OverlayTask
from .rfdc import RfDataConverter


class RfdcTask(OverlayTask):
    """Task for configuring RF data converters."""

    def __init__(self, overlay, dac_samp_rate, adc_samp_rate, carrier_freq):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.rfdc = RfDataConverter(overlay, debug_mode=True)
        self.dac_samp_rate = dac_samp_rate  # Hz
        self.adc_samp_rate = adc_samp_rate  # Hz
        self.carrier_freq = carrier_freq  # Hz

    def run(self):
        """Run the task."""
        # Configure external PLL clocks
        set_custom_lmclks()
        # Configure RF data converters
        self.rfdc.init_setup(self.dac_samp_rate,
                             self.adc_samp_rate, self.carrier_freq)
