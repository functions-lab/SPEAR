import numpy as np


class ThroughputTimer:

    def __init__(self):
        self.timer = []

    def update(self, t):
        self.timer.append(t)

    def get_throughput(self):
        avg_time = np.mean(self.timer[-3:]) / 10**9
        freq = 1 / avg_time
        print(
            f"Average DMA interval (s): {avg_time:.3f}, freq (hz) {freq:.3f}")
        self.timer = []
