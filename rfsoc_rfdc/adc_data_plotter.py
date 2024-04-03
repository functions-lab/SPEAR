import plotly.graph_objs as go
import numpy as np
# import ipywidgets as ipw
from IPython.display import display


class AdcDataPlotter:

    def __init__(self):
        # Initialize an empty figure with the desired layout upon object creation
        self.fig = go.FigureWidget(layout={'title': 'Complex Time Plot',
                                           'xaxis': {'title': 'Seconds (s)', 'autorange': True},
                                           'yaxis': {'title': 'Amplitude (V)'}})
        # Display the figure once upon initialization
        display(self.fig)

    def update_plot(self, i_data, q_data, title='Complex Time Plot'):
        # Update the title and data of the existing figure
        self.fig.layout.title = title
        self.fig.data = []  # Clear existing data
        self.fig.add_scatter(x=np.arange(0, 100, 1), y=i_data, name='Real')
        self.fig.add_scatter(x=np.arange(0, 100, 1), y=q_data, name='Imag')
