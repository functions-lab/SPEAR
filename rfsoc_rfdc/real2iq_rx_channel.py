import time
import numpy as np
import logging
from .dma_monitor import RxDmaMonitor
from pynq import allocate
from .rfdc import RfDataConverterType


class Real2IqRxChannel:
    """
    A class representing a real to I/Q reception channel on a Quad RF-ADC (gen 3).
    It handles data format conversion, buffer management, and reception control.

    Attributes:
        channel_id (int): Identifier for the reception channel.
        rx_buff (numpy.ndarray): Buffer for holding the received data.
        rx_dma (RxDmaMonitor): DMA monitor object for managing data transfers.
        warning_cnt (int): Counter for the number of warnings issued.

    Args:
        channel_id (int): Identifier for the reception channel.
        dma_ip: DMA IP.
        fifo_count_ip: AXI GPIO IP for FIFO count.
    """

    def __init__(self, channel_id, dma_ip, fifo_count_ip, buff_size=1024, debug_mode=False):
        """
        Initializes the Real2IqRxChannel with specified channel ID and hardware IPs.
        """
        self.channel_id = channel_id
        self.rx_buff_size = buff_size
        self.rx_buff = allocate(shape=(self.rx_buff_size,),
                                dtype=RfDataConverterType.DATA_PATH_DTYPE)
        self.rx_dma = RxDmaMonitor(dma_ip=dma_ip,
                                   fifo_count_ip=fifo_count_ip)
        self.warning_cnt = 0
        self.debug_mode = debug_mode

    def transfer(self):
        # Clear buffer
        self.rx_buff *= 0

        if self.debug_mode:
            fifo_count = self.rx_dma.get_fifo_count()

            # Warning for low FIFO count
            if fifo_count == 0:
                self.warning_cnt += 1
            if self.warning_cnt > 1000:
                self.warning_cnt = 0
                logging.info(
                    f"[Channel {self.channel_id}] Warning: Rx FIFO count {fifo_count} is zero. DMA transfer is too slow!")

        # Trigger DMA transfer
        self.rx_dma.transfer(self.rx_buff)

    def wait(self):
        self.rx_dma.wait()

    @property
    def i_data(self):
        return self.rx_buff[0::2]  # Even indices

    @property
    def q_data(self):
        return self.rx_buff[1::2]  # Odd indices
