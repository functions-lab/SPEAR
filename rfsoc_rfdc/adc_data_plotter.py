import matplotlib.pyplot as plt
import numpy as np


class AdcDataPlotter:
    def __init__(self, num_of_pts_plotted=512):
        self.num_of_pts_plotted = num_of_pts_plotted
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        # Create two line objects, one for each data series
        self.line1, = self.ax.plot([], [], lw=2, color='blue', label='I Data')
        self.line2, = self.ax.plot([], [], lw=2, color='red', label='Q Data')
        self.setup_plot()

    def setup_plot(self):
        self.ax.set_title("Data Segment Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.ax.set_xlim(0, self.num_of_pts_plotted)
        self.ax.set_ylim(0, 65535)
        self.ax.legend()
        plt.show()

    def update_plot(self, i_data, q_data):
        plot_range_i = min(self.num_of_pts_plotted, len(i_data))
        plot_range_q = min(self.num_of_pts_plotted, len(q_data))

        # Update both lines with new data
        self.line1.set_data(np.arange(plot_range_i), i_data[:plot_range_i])
        self.line2.set_data(np.arange(plot_range_q), q_data[:plot_range_q])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
