import numpy as np
from .rfdc import RfDataConverterType
from .dma_monitor import TxDmaMonitor
from pynq import allocate
from .tx_channel import TxChannel


class TxChannelIq2Real(TxChannel):
    """
    A class representing an I/Q to real transmission channel on a Quad RF-DAC (gen 3).
    It handles data format checking, copy data to buffer, and transmission control.
    """

    def __init__(self, channel_id, dma_ip, fifo_count_ip, debug_mode=False):
        super().__init__(channel_id, dma_ip, fifo_count_ip, debug_mode)

    def data_copy(self, i_buff, q_buff):
        if i_buff.size != q_buff.size:
            raise ValueError("i/q_buff must have the same size")
        self.data_type_check(i_buff)
        self.data_type_check(q_buff)

        # Buffer copy
        self.tx_buff = allocate(shape=(2*i_buff.size,),
                                dtype=RfDataConverterType.DATA_PATH_DTYPE)
        self.tx_buff[0::2] = i_buff  # Even indices
        self.tx_buff[1::2] = q_buff  # Odd indices

    # The transfer and wait methods will inherit from TxChannel unless they need specific changes.
