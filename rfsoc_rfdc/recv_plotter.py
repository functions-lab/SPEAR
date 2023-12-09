import matplotlib.pyplot as plt
import numpy as np


class RecvDataPlotter:
    def __init__(self, num_of_pts_plotted=512):
        self.num_of_pts_plotted = num_of_pts_plotted
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.line, = self.ax.plot([], [], lw=2)
        self.setup_plot()

    def setup_plot(self):
        self.ax.set_title("Data Segment Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.ax.set_xlim(0, self.num_of_pts_plotted)
        self.ax.set_ylim(0, 65535)
        plt.show()

    def update_plot(self, data):
        plot_range = min(self.num_of_pts_plotted, len(data))
        self.line.set_data(np.arange(plot_range), data[:plot_range])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
