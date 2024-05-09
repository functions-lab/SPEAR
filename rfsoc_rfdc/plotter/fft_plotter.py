import plotly.graph_objs as go
import numpy as np
from numpy.fft import fft, fftfreq
from IPython.display import display


class FFTPlotter:
    """Plot complex ADC samples in the frequency domain
    """

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.fig = go.FigureWidget(layout={
            'title':'FFT Magnitude Plot',
            'xaxis':{'title': 'Frequency (Hz)'},
            'yaxis':{'title': 'Magnitude'}
        })
        self.fig.add_scattergl(x=[], y=[], name='Magnitude')        
        display(self.fig)

    def update_plot(self, iq_data):
        iq_fft = fft(iq_data)  
        freq = fftfreq(len(iq_data), d=1/self.sample_rate)
        magnitude = np.abs(iq_fft)
        self.fig.data[0].x = freq
        self.fig.data[0].y = magnitude
