import matplotlib.pyplot as plt
import numpy as np


class WaveFormGenerator:
    def __init__(self):
        self.amplitude = (2**15 - 1)

    def generate_sine_wave(self, repeat_time=1, sample_pts=1000):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sin(2 * np.pi * t) * self.amplitude
        return wave.astype(np.int16)

    def generate_square_wave(self, repeat_time=1, sample_pts=1000):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = np.sign(np.sin(2 * np.pi * t)) * self.amplitude
        return wave.astype(np.int16)

    def generate_triangle_wave(self, repeat_time=1, sample_pts=1000):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * np.abs(2 * (t - np.floor(t + 0.5))) - 1
        wave *= self.amplitude
        return wave.astype(np.int16)

    def generate_sawtooth_wave(self, repeat_time=1, sample_pts=1000):
        t = np.linspace(0, repeat_time, int(
            sample_pts * repeat_time), endpoint=False)
        wave = 2 * (t - np.floor(0.5 + t))
        wave *= self.amplitude
        return wave.astype(np.int16)


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
