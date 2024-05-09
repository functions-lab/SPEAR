from rfsoc_rfdc.rfdc import RfDataConverterType
from pynq import allocate
from rfsoc_rfdc.transmitter.tx_channel import TxChannel


class TxChannelIq2Real(TxChannel):
    """
    A iq to real Tx channel.
    """
    def __init__(self, channel_id, dma_ip, fifo_count_ip, debug_mode=False):
        super().__init__(channel_id, dma_ip, fifo_count_ip, debug_mode)

    def data_copy(self, i_buff, q_buff):
        if i_buff.size != q_buff.size:
            raise ValueError("i/q_buff must have the same size")
        self.data_type_check(i_buff)
        self.data_type_check(q_buff)
        # Buffer copy
        self.tx_buff = allocate(shape=(i_buff.size+q_buff.size,),
                                dtype=RfDataConverterType.DATA_PATH_DTYPE)
        # iq samples shall be interleaved, i samples for even indices and q samples for odd indices
        self.tx_buff[0::2] = i_buff  
        self.tx_buff[1::2] = q_buff
