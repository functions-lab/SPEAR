import logging
from pynq import Overlay
import os
import re

RFDC_INSTANCE_NAME = 'usp_rf_data_converter'


class RFSoCOverlay(Overlay):

    def __init__(self, path_to_bitstream=None, **kwargs):

        # Generate default bitfile name
        if path_to_bitstream is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            bitstream_fname, hwh_fname = self._find_matching_files(curr_dir)
            logging.info(f'"Writing bitstream {bitstream_fname} to RFSoC."')
            path_to_bitstream = os.path.join(curr_dir, bitstream_fname)
        # Create Overlay
        super().__init__(path_to_bitstream, **kwargs)

        # Print out all IPs in bit stream file
        for i in self.ip_dict:
            print(i)

    def _find_matching_files(self, directory):
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
