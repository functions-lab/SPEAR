from rfsoc_rfdc.receiver.rx_channel import RxChannel


class RxChannelReal2Iq(RxChannel):
    """
    A real to iq Rx channel.
    """
    def __init__(self, channel_id, dma_ip, fifo_count_ip, buff_size=1024, debug_mode=False):
        super().__init__(channel_id, dma_ip, fifo_count_ip, buff_size, debug_mode)

    # TODO: Check if this is correcet! ADC shall sent samples in Q/iq/I ... format
    @property
    def data(self):
        # Real samples in even indices and imag samples in odd indices
        return self.rx_buff[0::2] + 1j * self.rx_buff[1::2]