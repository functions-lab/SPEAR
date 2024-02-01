import time
import numpy as np
import logging
from .dma_monitor import TxDmaMonitor
from pynq import allocate
from .rfdc import RfDataConverterType


class Iq2RealTxChannel:
    """
    A class representing a I/Q to read transmission channel on a Quad RF-DAC (gen 3).
    It handles data format checking, copy data to buffer, and transmission control.

    Attributes:
        channel_id (int): Identifier for the transmission channel.
        tx_buff (numpy.ndarray): Buffer for holding the formatted transmission data.
        tx_dma (TxDmaMonitor): DMA monitor object for managing data transfers.
        fifo_thres (int): Threshold for the FIFO count warning.
        warning_cnt (int): Counter for the number of warnings issued.

    Args:
        channel_id (int): Identifier for the transmission channel.
        dma_ip: DMA IP.
        fifo_count_ip: AXI GPIO IP for FIFO count.
    """

    def __init__(self, channel_id, dma_ip, fifo_count_ip):
        """
        Initializes the Iq2RealTxChannel with specified channel ID and hardware IPs.
        """
        self.channel_id = channel_id
        self.tx_buff = None
        self.tx_dma = TxDmaMonitor(dma_ip=dma_ip,
                                   fifo_count_ip=fifo_count_ip)
        self.fifo_thres = 1000
        self.warning_cnt = 0

    def data_copy(self, i_buff, q_buff):
        """
        Prepares and formats the I/Q data for transmission.

        Args:
            i_buff (numpy.ndarray): Buffer containing I (In-phase) data samples.
            q_buff (numpy.ndarray): Buffer containing Q (Quadrature) data samples.

        Raises:
            TypeError: If i_buff or q_buff is not a numpy.ndarray or not numpy.int16.
        """
        # Validations for input buffers
        if not isinstance(i_buff, np.ndarray) or \
                not isinstance(q_buff, np.ndarray):
            raise TypeError("i/q_buff must be of type numpy.ndarray")
        if i_buff.dtype != RfDataConverterType.DATA_PATH_DTYPE or \
                q_buff.dtype != RfDataConverterType.DATA_PATH_DTYPE:
            raise TypeError("i/q_buff must be of data type numpy.int16")
        if i_buff.size != q_buff.size:
            raise ValueError("i/q_buff must have the same size")

        # Buffer copy
        self.tx_buff = allocate(shape=(2*i_buff.size,),
                                dtype=RfDataConverterType.DATA_PATH_DTYPE)
        self.tx_buff[0::2] = i_buff  # Even indices
        self.tx_buff[1::2] = q_buff  # Odd indices

    def transfer(self):
        """
        Manages the data transfer to the DAC, including handling FIFO statuses and DMA transfer.
        """
        fifo_count = self.tx_dma.get_fifo_count()

        # Warning for low FIFO count
        if fifo_count < self.fifo_thres:
            self.warning_cnt += 1
        if self.warning_cnt > 1000:
            self.warning_cnt = 0
            logging.info(
                f"[Channel {self.channel_id}] Warning: Tx FIFO count {fifo_count} is less than {self.fifo_thres}. DMA transfer is too slow!")

        # Trigger DMA transfer
        self.tx_dma.transfer(self.tx_buff)

    def wait(self):
        """
        Waits for the DMA transfer to complete.
        """
        self.tx_dma.wait()
