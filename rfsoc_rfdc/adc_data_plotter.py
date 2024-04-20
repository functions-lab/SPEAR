import plotly.graph_objs as go
import numpy as np
from .rfdc import RfDataConverterType
from IPython.display import display
import logging


class AdcDataPlotter:

    def __init__(self):
        range_min, range_max = RfDataConverterType.DAC_MIN_SCALE, RfDataConverterType.DAC_MAX_SCALE
        self.fig = go.FigureWidget(layout={
            'title': 'Complex Time Plot',
            'xaxis': {'title': 'XXX'},
            'yaxis': {'title': 'Amplitude', 'range': [range_min, range_max]}
        })
        # Initialize plots with empty data
        self.fig.add_scattergl(x=[], y=[], name='I Samples')
        self.fig.add_scattergl(x=[], y=[], name='Q Samples')
        # Display the figure once upon initialization
        display(self.fig)

    def config_title(self, title='I/Q Samples'):
        self.fig.layout.title = title

    def update_plot(self, i_data, q_data):
        self.fig.data[0].x = np.arange(0, len(i_data), 1)
        self.fig.data[0].y = i_data
        self.fig.data[1].x = np.arange(0, len(q_data), 1)
        self.fig.data[1].y = q_data
