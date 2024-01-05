# from pynq import allocate, DefaultIP
# import numpy as np
# from .async_radio import AsyncRadioRx


# class Receiver():
#     def __init__(self, rx_dma, buff_size=100):
#         """Create a Receiver object that controls the receiver
#         and corresonding AXI DMA for data movement between PS and PL."""
#         """Member initialisation"""
#         super().__init__()
#         # Create AXI DMA object
#         self.rx_dma = rx_dma
#         self.rx_dma.set_up_rx_channel()
#         # Receive buffer size
#         self.buff_size = buff_size
#         # AXI DMA Buffer initialisation
#         self._rx_buff = allocate(shape=(self.buff_size), dtype=np.int16)
#         # Create asynchronous radio receiver
#         self.monitor = AsyncRadioRx(irq=self.rx_dma,
#                                     irq_callback=self._transfer, callback=[])

#     def _transfer(self):
#         """Perform sync data transfer"""
#         # Create new recv buffer for message
#         self._rx_buff.freebuffer()
#         self._rx_buff = allocate(shape=(self.buff_size,), dtype=np.int16)
#         """Receive the message"""
#         self.rx_dma.recvchannel.transfer(self._rx_buff)
#         self.rx_dma.recvchannel.wait()  # blocking wait

#     def _recv_callback(self):
#         for h in self._rx_buff:
#             print(hex(h))

# class ReceiverCore(DefaultIP):
#     """Driver for Receiver's core logic IP
#     Exposes all the configuration registers by name via data-driven properties
#     """
#     def __init__(self, description):
#         super().__init__(description=description)

#     bindto = ['UoS:RFSoC:receiver:1.0']

# # LUT of property addresses for our data-driven properties
# _receiver_props = [("reset_time_sync", 0),
#                    ("reset_phase_sync", 4),
#                    ("reset_frame_sync", 8),
#                    ("threshold", 12),
#                    ("transfer", 28),
#                    ("observation_point", 36),
#                    ("fifo_count", 32),
#                    ("receive_size", 20),
#                    ("packet_count_qpsk", 24),
#                    ("coarse_passthrough", 44),
#                    ("freq_offset", 40),
#                    ("modulation", 48),
#                    ("packet_count_bpsk", 52),
#                    ("global_reset_sync", 56)]

# # Function to return a MMIO Getter and Setter based on a relative address
# def _create_mmio_property(addr):
#     def _get(self):
#         value = self.read(addr)
#         if addr == 40:
#             data = -((value-(2**32)*int(str((value)>>32-1)))*2**-10)
#         else:
#             data = value
#         return data

#     def _set(self, value):
#         self.write(addr, value)

#     return property(_get, _set)

# # Generate getters and setters based on _receiver_props
# for (name, addr) in _receiver_props:
#     setattr(ReceiverCore, name, _create_mmio_property(addr))
