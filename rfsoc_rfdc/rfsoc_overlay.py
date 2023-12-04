from pynq import Overlay
import os


class RFSoCOverlay(Overlay):

    def __init__(self, bitfile_name=None, **kwargs):

        # Generate default bitfile name
        if bitfile_name is None:
            this_dir = os.path.dirname(__file__)
            bitfile_name = os.path.join(this_dir, 'abc.bit')

        # Create Overlay
        super().__init__(bitfile_name, **kwargs)
