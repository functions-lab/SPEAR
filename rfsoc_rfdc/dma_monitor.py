from abc import ABC, abstractmethod
import pynq
from pynq import DefaultIP


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


class StreamingDmaV1(DefaultIP):

    MASK_32b = 0xFFFFFFFF
    MAX_BTT = 0x7FFFFF
    BTT_MASK = 0x7FFFFF  # 23b
    _FSM_LUT = ['S_IDLE', 'S_STREAM', 'S_ERROR']

    def __init__(self, description):
        super().__init__(description=description)

    bindto = ['user.org:user:data_mover_ctrl:1.0']

    @property
    def _start(self):
        return self.read(0x00)

    @_start.setter
    def _start(self, value):
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
        self._btt = nbytes & self.BTT_MASK

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._start = 1

    def stop(self):
        self._start = 0

    def get_debug_info(self):
        base_addr = ((self._base_addr_upper & self.MASK_32b) <<
                     32) | (self._base_addr_lower & self.MASK_32b)
        debug_info = f"start = {self._start}, btt = {self._btt}, base_addr = {base_addr}, state = {self.state()}"
        return debug_info

    def __del__(self):
        self.stop()


class TxStreamingDmaV2(DefaultIP):

    MASK_32b = 0xFFFFFFFF
    MAX_BTT = 0x7FFFFF
    BTT_MASK = 0x7FFFFF  # 23b
    _FSM_LUT = ['S_IDLE', 'S_STREAM', 'S_HALT', 'S_HALT_RST', 'S_ERROR']

    def __init__(self, description):
        super().__init__(description=description)

    bindto = ['user.org:user:data_mover_ctrl:2.0']

    @property
    def _start(self):
        return self.read(0x00)

    @_start.setter
    def _start(self, value):
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
        self._btt = nbytes & self.BTT_MASK

    def transfer(self, buffer):
        self._config(buffer.physical_address, buffer.nbytes)
        self._start = 1

    def stop(self):
        self._start = 0

    def get_debug_info(self):
        base_addr = ((self._base_addr_upper & self.MASK_32b) <<
                     32) | (self._base_addr_lower & self.MASK_32b)
        debug_info = f"start = {self._start}, btt = {self._btt}, base_addr = {base_addr}, state = {self.state()}"
        return debug_info

    def __del__(self):
        self._start = 0


class TxDmaMonitor(DmaMonitor):
    def transfer(self, buffer):
        self.dma.sendchannel.transfer(buffer)

    def wait(self):
        self.dma.sendchannel.wait()

    def stop(self):
        pass

# Define the class for reception DMA monitor
class RxDmaMonitor(DmaMonitor):
    def transfer(self, buffer):
        self.dma.recvchannel.transfer(buffer)

    def wait(self):
        self.dma.recvchannel.wait()

    def stop(self):
        pass
