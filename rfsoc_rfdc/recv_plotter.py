import matplotlib.pyplot as plt
import numpy as np


class RecvDataPlotter:
    """
    A class for plotting received data.

    Attributes:
        num_of_pts_plotted (int): The number of points to be plotted.
        fig (matplotlib.figure.Figure): The figure object for the plot.
        ax (matplotlib.axes.Axes): The axes object for the plot.
        line (matplotlib.lines.Line2D): The line object representing the plot.
    """

    def __init__(self, num_of_pts_plotted=512):
        self.num_of_pts_plotted = num_of_pts_plotted
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.line, = self.ax.plot([], [], lw=2)
        self.setup_plot()

    def setup_plot(self):
        """
        Set up the plot with appropriate labels, limits, and grid.
        """
        self.ax.set_title("Data Segment Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.ax.set_xlim(0, self.num_of_pts_plotted)
        self.ax.set_ylim(0, 65535)
        plt.show()

    def update_plot(self, data):
        """
        Update the plot with new data.

        Args:
            data (numpy.ndarray): The data to be plotted.
        """
        plot_range = min(self.num_of_pts_plotted, len(data))
        self.line.set_data(np.arange(plot_range), data[:plot_range])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
