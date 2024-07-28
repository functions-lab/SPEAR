import os
import numpy as np
import scipy.io
from abc import ABC, abstractmethod

from rfsoc_rfdc.rfdc import MyRFdcType
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class IqLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.i_samp, self.q_samp = None, None

    def check_file_exist(self):
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(
                f"The specified file does not exist: {self.file_path}")

    def scale_to_int16(self, range_min, range_max, wave_scaling_factor=1.0):

        range_min, range_max = int(
            wave_scaling_factor * range_min), int(wave_scaling_factor * range_max)

        min_real, max_real = np.min(self.i_samp), np.max(self.i_samp)
        min_imag, max_imag = np.min(self.q_samp), np.max(self.q_samp)

        scale = np.max([np.abs(max_real), np.abs(min_imag),
                        np.abs(min_real), np.abs(max_imag)])

        scaled_i = np.int16(
            np.interp(self.i_samp, (-scale, scale), (range_min, range_max)))
        scaled_q = np.int16(
            np.interp(self.q_samp, (-scale, scale), (range_min, range_max)))

        scaled_i = np.squeeze(scaled_i)
        scaled_q = np.squeeze(scaled_q)

        self.i_samp, self.q_samp = scaled_i, scaled_q

    def get_iq(self, repeat_times=1):
        if isinstance(repeat_times, int) and repeat_times != 1:
            return np.tile(self.i_samp, repeat_times), np.tile(self.q_samp, repeat_times)
        return self.i_samp, self.q_samp

    @abstractmethod
    def load_iq(self):
        pass


class NumpyIqLoader(IqLoader):
    def __init__(self, file_path, key='wave'):
        super().__init__(file_path)
        self.check_file_exist()
        self.load_iq()
        self.scale_to_int16(MyRFdcType.DAC_MIN_SCALE, MyRFdcType.DAC_MAX_SCALE,
                            wave_scaling_factor=ZCU216_CONFIG['DAC_SCALING_FACTOR'])

    def load_iq(self):
        try:
            wave = np.load(self.file_path)
            self.i_samp, self.q_samp = wave.real, wave.imag
        except KeyError:
            raise KeyError(
                f"The key '{self.key}' was not found in the MATLAB file {self.file_path}.")


class MatlabIqLoader(IqLoader):
    def __init__(self, file_path, key='wave'):
        super().__init__(file_path)
        self.key = key
        self.check_file_exist()
        self.load_iq()
        self.scale_to_int16(MyRFdcType.DAC_MIN_SCALE, MyRFdcType.DAC_MAX_SCALE,
                            wave_scaling_factor=ZCU216_CONFIG['DAC_SCALING_FACTOR'])

    def load_iq(self):
        try:
            wave = scipy.io.loadmat(self.file_path)[self.key]
            self.i_samp, self.q_samp = wave.real, wave.imag
        except KeyError:
            raise KeyError(
                f"The key '{self.key}' was not found in the MATLAB file {self.file_path}.")
