import logging
from pynq import Overlay
import os
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class RFSoCOverlay(Overlay):
    """
    Represents an RFSoC overlay.

    This class extends the `Overlay` class and provides additional functionality specific to RFSoC devices.

    Args:
        path_to_bitstream (str): Path to the bitstream file (.bit). If not provided, the default bitstream file in the current directory will be used.
        **kwargs: Additional keyword arguments to be passed to the `Overlay` class constructor.
    """

    def __init__(self, path_to_bitstream=None, **kwargs):
        """
        Initializes the RFSoCOverlay object.

        Args:
            path_to_bitstream (str): Path to the bitstream file (.bit). If not provided, the default bitstream file in the current directory will be used.
            **kwargs: Additional keyword arguments to be passed to the `Overlay` class constructor.
        """

        # Generate default bitfile name
        if path_to_bitstream is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            bitstream_fname, hwh_fname = self._find_matching_files(curr_dir)
            logging.info(f'"Writing bitstream {bitstream_fname} to RFSoC."')
            path_to_bitstream = os.path.join(curr_dir, bitstream_fname)
        # Create Overlay
        super().__init__(path_to_bitstream, ignore_version=True, **kwargs)

        # Print out all IPs in bit stream file
        for i in self.ip_dict:
            print(i)

    def _find_matching_files(self, directory):
        """
        Finds the matching bitstream (.bit) and hardware handoff files (.hwh) in the given directory.

        Args:
            directory (str): Path to the directory containing the files.

        Returns:
            tuple: A tuple containing the names of the matching bitstream and hardware handoff files.

        Raises:
            FileNotFoundError: If no matching bitstream files are found or if a corresponding hardware handoff file is missing.
        """

        # Get all files in the directory and sort them in increasing order
        all_files = sorted(os.listdir(directory))

        # Regex pattern to match the .bit file
        bit_pattern = r"rfsoc_rfdc_v.*\.bit$"

        # Find all .bit files that match the pattern
        bit_files = [f for f in all_files if re.match(bit_pattern, f)]

        for bit_file in bit_files:
            # Extract the prefix from the bit file name
            prefix = bit_file.split('.bit')[0]

            # Construct the corresponding .hwh file name
            hwh_file = prefix + '.hwh'

            # Check if the .hwh file exists in the sorted list
            if hwh_file not in all_files:
                raise FileNotFoundError(f"Missing .hwh file for {bit_file}")

            # Return the matched pair
            return bit_file, hwh_file

        # Raise exception if no .bit files are found
        raise FileNotFoundError(
            f"No matching bit stream files found in {directory}")
