from .rx_channel import RxChannel


class RxChannelReal2Iq(RxChannel):

    def __init__(self, channel_id, dma_ip, fifo_count_ip, buff_size=1024, debug_mode=False):
        super().__init__(channel_id, dma_ip, fifo_count_ip, buff_size, debug_mode)

    @property
    def i_data(self):
        return self.rx_buff[0::2]  # Even indices

    @property
    def q_data(self):
        return self.rx_buff[1::2]  # Odd indices
