import os
import numpy as np
import scipy.io


class MatlabIqLoader:
    def __init__(self, file_path='./wave.mat', key='wave'):
        self.file_path = file_path
        self.key = key
        self.wave = None
        self.i_samples = None
        self.q_samples = None

    def load_matlab_waveform(self):
        # Check if the file exists
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(
                f"The specified file does not exist: {self.file_path}")

        try:
            self.wave = scipy.io.loadmat(self.file_path)[self.key]
        except KeyError:
            raise KeyError(
                f"The key '{self.key}' was not found in the MATLAB file {self.file_path}.")

    def scale_waveform(self, range_min, range_max):
        if self.wave is None:
            raise ValueError("Waveform data is not loaded")

        min_real, max_real = np.min(self.wave.real), np.max(self.wave.real)
        min_imag, max_imag = np.min(self.wave.imag), np.max(self.wave.imag)

        scale = np.max([np.abs(max_real), np.abs(min_imag),
                       np.abs(min_real), np.abs(max_imag)])

        self.i_samples = np.int16(
            np.interp(self.wave.real, (-scale, scale), (range_min, range_max)))
        self.q_samples = np.int16(
            np.interp(self.wave.imag, (-scale, scale), (range_min, range_max)))

        self.i_samples = np.squeeze(self.i_samples)
        self.q_samples = np.squeeze(self.q_samples)

    def get_iq_samples(self):
        return self.i_samples, self.q_samples
