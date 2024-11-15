import os
import xrfclk
import logging
from abc import ABC, abstractmethod


class ExternalClkConfig(ABC):
    def __init__(self, chip, freq_in, freq_out):
        self.chip = chip
        self.freq_in, self.freq_out = freq_in, freq_out
        self.file = None
        self.loc = None
        self.reg = None

    @abstractmethod
    def find_matching_file(self, config_dir):
        pass

    def read_registers(self):
        if not self.loc:
            raise ValueError("File location not set")
        with open(self.loc, 'r') as file:
            reg = [line.rstrip("\n") for line in file]
            self.reg = [int(r.split('\t')[-1], 16) for r in reg]

    def program_clock(self):
        if not self.reg:
            raise ValueError("Registers not loaded")

        if isinstance(self, LMK04828ClkConfig):
            devices = xrfclk.lmk_devices
            write_func = xrfclk.xrfclk._write_LMK_regs
        elif isinstance(self, LMX2594ClkConfig):
            devices = xrfclk.lmx_devices
            write_func = xrfclk.xrfclk._write_LMX_regs
        else:
            raise ValueError("Unknown clock type")

        for device in devices:
            write_func(self.reg, device)

    @abstractmethod
    def to_dict(self):
        pass


class LMK04828ClkConfig(ExternalClkConfig):
    def __init__(self, chip, freq_in, freq_out, mts_pl_clk_freq=0.0, mts_pl_sysref_freq=0.0):
        super().__init__(chip, freq_in, freq_out)
        self.mts_pl_clk_freq = mts_pl_clk_freq
        self.mts_pl_sysref_freq = mts_pl_sysref_freq

    def find_matching_file(self, config_dir):
        expected_filename = f"{self.chip}_{self.freq_in}_{self.freq_out}_{self.mts_pl_clk_freq}_{self.mts_pl_sysref_freq}.txt"
        for filename in os.listdir(config_dir):
            if filename == expected_filename:
                self.file = filename
                self.loc = os.path.join(config_dir, filename)
                return True
        return False

    def to_dict(self):
        return {
            'file': self.file,
            'loc': self.loc,
            'chip': self.chip,
            'freq_in': self.freq_in,
            'freq_out': self.freq_out,
            'mts_pl_clk_freq': self.mts_pl_clk_freq,
            'mts_pl_sysref_freq': self.mts_pl_sysref_freq,
            'reg': self.reg
        }


class LMX2594ClkConfig(ExternalClkConfig):
    def __init__(self, chip, freq_in, freq_out):
        super().__init__(chip, freq_in, freq_out)

    def find_matching_file(self, config_dir):
        expected_filename = f"{self.chip}_{self.freq_in}_{self.freq_out}.txt"
        for filename in os.listdir(config_dir):
            if filename == expected_filename:
                self.file = filename
                self.loc = os.path.join(config_dir, filename)
                return True
        return False

    def to_dict(self):
        return {
            'file': self.file,
            'loc': self.loc,
            'chip': self.chip,
            'freq_in': self.freq_in,
            'freq_out': self.freq_out,
            'reg': self.reg
        }


def find_and_program_clocks(lmk_config, lmx_config, config_dir):
    """
    Find matching configuration files and program the clocks.

    :param lmk_config: LMK04828ClkConfig object
    :param lmx_config: LMX2594ClkConfig object
    :param config_dir: Directory containing clock configuration files
    :return: Dictionary containing updated LMK and LMX configurations
    """
    # Ensure LMK and LMX devices are known
    if not xrfclk.lmk_devices and not xrfclk.lmx_devices:
        xrfclk.xrfclk._find_devices()

    # Find matching files
    if not lmk_config.find_matching_file(config_dir):
        raise FileNotFoundError(
            "Could not find matching LMK configuration file.")
    if not lmx_config.find_matching_file(config_dir):
        raise FileNotFoundError(
            "Could not find matching LMX configuration file.")

    # Read registers
    lmk_config.read_registers()
    lmx_config.read_registers()

    # Program clocks
    lmk_config.program_clock()
    lmx_config.program_clock()

    # Return configurations as a dictionary
    return lmk_config.to_dict(), lmx_config.to_dict()
