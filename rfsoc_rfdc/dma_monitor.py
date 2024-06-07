from abc import ABC, abstractmethod
import pynq


class DmaMonitor(ABC):
    """
    Monitor the data transfer for a DMA (Direct Memory Access) interface. This class assumes DMA is buffered by AXI4-Stream Data FIFO. Also, we assume the following: 
    1) AXI GPIOs are used to read the axis_wr_data_count[31:0] OR axis_rd_data_count[31:0] port of AXI4-Stream Data FIFO.
    2) AXI GPIOs are used to read the prog_full OR prog_empty port of the AXI4-Stream Data FIFO.
    Based on the reading of the above two ports, we can monitor the data transmission status between DMA and the AXI4-Stream Data FIFO.
    """

    def __init__(self, dma_ip, fifo_count_ip):
        """
        Constructs all the necessary attributes for the PynqDMA object.
        """
        # DMA IP core instance
        self.dma = dma_ip
        # Configure FIFO count IP core
        self.fifo_count = fifo_count_ip
        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

    def get_fifo_count(self):
        """
        Returns the current count of the FIFO.
        """
        return self.fifo_count.read()

    def get_debug_info(self):
        """
        Returns the debug information of the DMA.
        """
        return self.dma.register_map

    @abstractmethod
    def transfer(self, buffer):
        """
        Abstract method for initiating a DMA transfer.
        """
        pass

    @abstractmethod
    def wait(self):
        """
        Abstract method for waiting for the DMA transfer to complete.
        """
        pass

# Define the class for transmission DMA monitor


class TxDmaMonitor(DmaMonitor):
    def transfer(self, buffer):
        """
        Initiates a DMA transfer for transmission.
        """
        self.dma.sendchannel.transfer(buffer)

    def wait(self):
        """
        Waits for the DMA transfer to complete for transmission.
        """
        self.dma.sendchannel.wait()

# Define the class for reception DMA monitor


class RxDmaMonitor(DmaMonitor):
    def transfer(self, buffer):
        """
        Initiates a DMA transfer for reception.
        """
        self.dma.recvchannel.transfer(buffer)

    def wait(self):
        """
        Waits for the DMA transfer to complete for reception.
        """
        self.dma.recvchannel.wait()
