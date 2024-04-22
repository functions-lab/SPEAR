import plotly.graph_objs as go
import numpy as np
from .rfdc import RfDataConverterType
from IPython.display import display


class AdcDataPlotter:

    """
    A class for plotting ADC data.

    Attributes:
        fig (go.FigureWidget): The figure widget for displaying the plot.
    """

    def __init__(self):
        """
        Initializes the AdcDataPlotter class.

        Initializes the figure widget with layout settings and adds empty scatter plots for I and Q samples.
        """
        range_min, range_max = RfDataConverterType.DAC_MIN_SCALE, RfDataConverterType.DAC_MAX_SCALE
        self.fig = go.FigureWidget(layout={
            'title': 'Complex Time Plot',
            'xaxis': {'title': 'ADC Sample Index'},
            'yaxis': {'title': 'Amplitude', 'range': [range_min, range_max]}
            # 'yaxis': {'title': 'Amplitude', 'autorange': True}
        })
        # Initialize plots with empty data
        self.fig.add_scattergl(x=[], y=[], name='I Samples')
        self.fig.add_scattergl(x=[], y=[], name='Q Samples')
        # Display the figure once upon initialization
        display(self.fig)

    def config_title(self, title='I/Q Samples'):
        """
        Configures the title of the plot.

        Args:
            title (str): The title to set for the plot. Defaults to 'I/Q Samples'.
        """
        self.fig.layout.title = title

    def update_plot(self, i_data, q_data, display_ratio=1.0):
        """
        Updates the plot with new data.

        Args:
            i_data (array-like): The new I data to update the plot with.
            q_data (array-like): The new Q data to update the plot with.
            display_ratio (float): The ratio of data to display. Defaults to 1.0, which displays all data.
        """
        window_size = int(len(i_data) * display_ratio)
        self.fig.data[0].x = np.arange(0, window_size, 1)
        self.fig.data[0].y = i_data[0:window_size]
        self.fig.data[1].x = np.arange(0, window_size, 1)
        self.fig.data[1].y = q_data[0:window_size]
