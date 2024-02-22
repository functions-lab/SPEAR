from .clocks import set_custom_lmclks
from .overlay_task import OverlayTask
from .rfdc import RfDataConverter


class RfdcTask(OverlayTask):
    """Task for configuring RF data converters."""

    def __init__(self, overlay):
        """Initialize the task with the given overlay."""
        super().__init__(overlay, name="RfdcTask")
        self.rfdc = RfDataConverter(overlay, debug_mode=True)

    def run(self):
        """Run the task."""
        # Configure external PLL clocks
        set_custom_lmclks()
        # Configure RF data converters
        self.rfdc.init_setup()
