from abc import ABC, abstractmethod
import pynq
from pynq import DefaultIP
import time


class DmaMonitor(ABC):
    def __init__(self, dma_ip, fifo_count_ip):
        # DMA IP core instance
        self.dma = dma_ip
        # Configure FIFO count IP core
        self.fifo_count = fifo_count_ip
        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

    def get_fifo_count(self):
        return self.fifo_count.read()

    def get_debug_info(self):
        return self.dma.register_map

    @abstractmethod
    def transfer(self, buffer):
        pass

    @abstractmethod
    def wait(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class StreamingDmaBase(DefaultIP):
    """
    This class serves as a base class for StreamingDma. StreamingDma uses a custom IP to control the Xilins's AXI Data Mover IP.
    """
    MASK_32b = 0xFFFFFFFF  # 32-bit binary mask
    # Maximum allowed number of bytes (2^23B = 8MB) to transfer for AXI Data Mover
    MAX_BTT = 0x7FFFFF

    def __init__(self, description, fsm_lut):
        super().__init__(description=description)
        self._FSM_LUT = fsm_lut

    @property
    def _cmd(self):
        return self.read(0x00)

    @_cmd.setter
    def _cmd(self, value):
        self.write(0x00, value)

    @property
    def _base_addr_upper(self):
        return self.read(0x04)

    @_base_addr_upper.setter
    def _base_addr_upper(self, value):
        self.write(0x04, value)

    @property
    def _base_addr_lower(self):
        return self.read(0x08)

    @_base_addr_lower.setter
    def _base_addr_lower(self, value):
        self.write(0x08, value)

    @property
    def _btt(self):
        return self.read(0x0C)

    @_btt.setter
    def _btt(self, value):
        self.write(0x0C, value)

    @property
    def _state(self):
        return self.read(0x10)

    def state(self):
        return self._FSM_LUT[self._state]

    def _config(self, addr, nbytes):
        self._base_addr_lower = addr & self.MASK_32b
        self._base_addr_upper = (addr >> 32) & self.MASK_32b
        if nbytes > self.MAX_BTT:
            raise ValueError(
                f"Number of bytes to transfer is too large. Shall be smaller than {self.MAX_BTT} bytes")
        self._btt = nbytes & self.MAX_BTT

    def get_debug_info(self):
        base_addr = ((self._base_addr_upper & self.MASK_32b) <<
                     32) | (self._base_addr_lower & self.MASK_32b)
        debug_info = f"start = {self._cmd}, btt = {self._btt}, base_addr = {base_addr}, state = {self.state()}"
        return debug_info

    def __del__(self):
        self.stop()


class StreamingDmaV1(StreamingDmaBase):
    """
    Streaming DMA driver v1.0 allows user to start and stop continuously DMA transfer by slipping self._cmd between 0 (stop) and 1 (start).
    """

    def __init__(self, description):
        super().__init__(description, fsm_lut=['S_IDLE', 'S_STREAM', 'S_ERROR'])

    bindto = ['user.org:user:data_mover_ctrl:1.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = 1

    def stop(self):
        self._cmd = 0


class StreamingDmaV2(StreamingDmaBase):
    """
    Streaming DMA driver v2.0 allows user to start and stop continuously DMA transfer by slipping self._cmd between 0 (stop) and 1 (start).
    """

    def __init__(self, description):
        super().__init__(description, fsm_lut=[
            'S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR'])

    bindto = ['user.org:user:data_mover_ctrl:2.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = 1

    def stop(self):
        self._cmd = 0


class StreamingDmaV3(StreamingDmaBase):
    """
    Streaming DMA driver v3.0 allows users to send the following commands. 

    1) IDLE: DMA goes to IDLE state 
    2) SINGLE: DMA make a single data transfer
    3) STREAM: DMA stream data continuously
    """
    _CMD_LUT = {'IDLE': 0x0, 'SINGLE': 0x1, 'STREAM': 0x2}

    def __init__(self, description):
        super().__init__(description, fsm_lut=[
            'S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR', 'S_SINGLE'])

    bindto = ['user.org:user:data_mover_ctrl:3.0']

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = self._CMD_LUT['SINGLE']
        while True:
            if self.state() == 'S_IDLE':
                break  # CPU polling the FSM state
            else:
                time.sleep(0.01)
        self._cmd = self._CMD_LUT['IDLE']

    def stream(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._cmd = self._CMD_LUT['STREAM']

    def stop(self):
        self._cmd = self._CMD_LUT['IDLE']


class TxDmaMonitor(DmaMonitor):
    """
    This is the Tx DMA driver for Xilinx's DMA IP
    """

    def transfer(self, buffer):
        self.dma.sendchannel.transfer(buffer)

    def wait(self):
        self.dma.sendchannel.wait()

    def stop(self):
        pass


class RxDmaMonitor(DmaMonitor):
    """
    This is the Rx DMA driver for Xilinx's DMA IP
    """

    def transfer(self, buffer):
        self.dma.recvchannel.transfer(buffer)

    def wait(self):
        self.dma.recvchannel.wait()

    def stop(self):
        pass
