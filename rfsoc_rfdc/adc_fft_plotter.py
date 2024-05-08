import plotly.graph_objs as go
import numpy as np
from numpy.fft import fft, fftfreq
from IPython.display import display


class AdcFFTPlotter:
    """
    A class for plotting the magnitude of FFT of ADC data.

    Attributes:
        fig (go.FigureWidget): The figure widget for displaying the plot.
    """

    def __init__(self, sample_rate):
        """
        Initializes the AdcFFTPlotter class.

        Args:
            sample_rate (int): The sampling rate of the ADC data.

        Initializes the figure widget with layout settings for magnitude plots.
        """
        self.sample_rate = sample_rate
        self.fig = go.FigureWidget()
        self.fig.update_layout(
            title='FFT Magnitude Plot',
            xaxis_title='Frequency (Hz)',
            yaxis_title='Magnitude',
            xaxis=dict(title='Frequency (Hz)'),
            yaxis=dict(title='Magnitude')
        )
        # Initialize plots with empty data
        self.fig.add_scattergl(x=[], y=[], name='Magnitude', mode='lines')
        # Display the figure once upon initialization
        display(self.fig)

    def update_plot(self, i_data, q_data):
        """
        Updates the plot with FFT results from new I and Q data.

        Args:
            i_data (array-like): The new I data.
            q_data (array-like): The new Q data.
        """
        iq_data = i_data + 1j * q_data  # Form the complex signal
        iq_fft = fft(iq_data)  # Perform FFT
        freq = fftfreq(len(iq_data), d=1/self.sample_rate)  # Frequency axis

        # Calculate magnitude
        magnitude = np.abs(iq_fft)

        # Update magnitude plot
        self.fig.data[0].x = freq
        self.fig.data[0].y = magnitude
