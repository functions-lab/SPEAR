import matplotlib.pyplot as plt
import numpy as np

from .rfdc import RfDataConverterType


class WaveFormGenerator:
    """
    A class that generates different types of waveforms.

    Attributes:
        amplitude (int): The amplitude of the waveforms.

    Methods:
        generate_sine_wave: Generates a sine wave.
        generate_square_wave: Generates a square wave.
        generate_triangle_wave: Generates a triangle wave.
        generate_sawtooth_wave: Generates a sawtooth wave.
        generate_cosine_wave: Generates a cosine wave.
    """

    amplitude = (2**15 - 1)  # Class-level attribute

    @staticmethod
    def generate_sine_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a sine wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated sine wave.
        """
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sin(2 * np.pi * t) * WaveFormGenerator.amplitude
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_square_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a square wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated square wave.
        """
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sign(np.sin(2 * np.pi * t)) * WaveFormGenerator.amplitude
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_triangle_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a triangle wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated triangle wave.
        """
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * np.abs(2 * (t - np.floor(t + 0.5))) - 1
        wave *= WaveFormGenerator.amplitude
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_sawtooth_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a sawtooth wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated sawtooth wave.
        """
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * (t - np.floor(0.5 + t))
        wave *= WaveFormGenerator.amplitude
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_cosine_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a cosine wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated cosine wave.
        """
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.cos(2 * np.pi * t) * WaveFormGenerator.amplitude
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)

    @staticmethod
    def generate_no_wave(repeat_time=1, sample_pts=1000):
        """
        Generates a nothing wave.

        Args:
            repeat_time (float): The time period of the waveform.
            sample_pts (int): The number of sample points.

        Returns:
            numpy.ndarray: The generated cosine wave.
        """
        wave = np.zeros(sample_pts * repeat_time)
        return wave.astype(RfDataConverterType.DATA_PATH_DTYPE)


if __name__ == "__main__":
    # Create an instance of the WaveFormGenerator class
    generator = WaveFormGenerator()

    # Generate waveforms
    sine_wave = generator.generate_sine_wave()
    square_wave = generator.generate_square_wave()
    triangle_wave = generator.generate_triangle_wave()
    sawtooth_wave = generator.generate_sawtooth_wave()

    # Plotting
    fig, axs = plt.subplots(4, 1, figsize=(10, 8))

    # Plot sine wave
    axs[0].plot(sine_wave)
    axs[0].set_title("Sine Wave")

    # Plot square wave
    axs[1].plot(square_wave)
    axs[1].set_title("Square Wave")

    # Plot triangle wave
    axs[2].plot(triangle_wave)
    axs[2].set_title("Triangle Wave")

    # Plot sawtooth wave
    axs[3].plot(sawtooth_wave)
    axs[3].set_title("Sawtooth Wave")

    # Display the plot
    plt.tight_layout()
    plt.show()
