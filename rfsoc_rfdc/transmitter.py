# from pynq import allocate, DefaultIP
# import numpy as np
# # from .async_radio import AsyncRadioTx
# from pynq.lib import AxiGPIO
# import time

# class Transmitter():
#     def __init__(self, tx_dma):
#         """Create a Transmitter object that controls the transmitter
#         and corresponding AXI DMA for data movement between the PS and PL."""
#         super().__init__()
#         self.mode = 'repeat'
#         # Create AXI DMA Object
#         self.tx_dma = tx_dma
#         # Create a new radio transmitter object
#         self.running = False

#     def start(self):
#         """Start data transmission using the message buffer set
#         through Transmitter.data(data). The transmission ends once the
#         entire message has sent or Transmitter.stop() is called.
#         """
#         if self.running is True:
#             raise RuntimeError('Transmitter already started.')
#         else:
#             cnt = 0
#             if self.mode == 'repeat':
#                 while not self.running:
#                     self._transfer()
#                     cnt = cnt + 1
#                     print("cnt=", cnt)
#                     print(self.running)
#             elif self.mode == 'single':
#                 self._transfer()
#             else:
#                 raise ValueError(
#                     'Transmitter mode should be repeat or single.')

#     def data(self, real_data, img_data):
#         """Stored in the buffer awaiting transmission.
#         """
#         if not isinstance(real_data, np.ndarray) or not isinstance(img_data, np.ndarray):
#             raise TypeError('Data must be numpy ndarray.')
#         if not real_data.dtype == 'int16' or not img_data.dtype == 'int16':
#             raise TypeError('Data must be np.int16 type.')
#         self.real_data = real_data
#         self.img_data = img_data
#         # Create new send buffer for message
#         self._tx_buff = self._create_buffer(self.real_data)

#     def stop(self):
#         """Stop data transmission if it is currently underway.
#         """
#         self.running = False

#     def _create_buffer(self, data):
#         """Create a buffer that is loaded user data.
#         """
#         if data.size == 0:
#             raise ValueError('Message size should be greater than 0.')
#         tmp_buf = allocate(shape=(len(data),), dtype=np.int16)
#         tmp_buf[:] = data[:]
#         return tmp_buf

#     def _transfer(self):
#         """Perform sync data transfer"""
#         if self._tx_buff is None:
#             raise("TX buffer not created")
#         """Send the message"""
#         self.tx_dma.sendchannel.transfer(self._tx_buff)
#         print("dma transfered")
#         self.tx_dma.sendchannel.wait()  # blocking wait
#         print("dma wait")

#     def __del__(self):
#         try:
#             if self._tx_buff is not None:
#                 self._tx_buff.freebuffer()
#                 print("buffer freed")
#         except:
#             pass
# # class TransmitterCore(DefaultIP):
# #     """Driver for Transmitter's core logic IP
# #     Exposes all the configuration registers by name via data-driven properties
# #     """
# #     def __init__(self, description):
# #         super().__init__(description=description)

# #     bindto = ['UoS:RFSoC:transmitter:1.0']

# # # LUT of property addresses for our data-driven properties
# # _transmitter_props = [("enable_data", 0),
# #                       ("enable_transmitter", 4),
# #                       ("modulation", 8),
# #                       ("observation_point", 12)]

# # # Function to return a MMIO Getter and Setter based on a relative address
# # def _create_mmio_property(addr):
# #     def _get(self):
# #         return self.read(addr)

# #     def _set(self, value):
# #         self.write(addr, value)

# #     return property(_get, _set)

# # # Generate getters and setters based on _transmitter_props
# # for (name, addr) in _transmitter_props:
# #     setattr(TransmitterCore, name, _create_mmio_property(addr))
