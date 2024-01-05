# This might  be useful for our design
# import threading
# import asyncio
# import time


# def default_callback():
#     # pass
#     print("This is default callback.")


# class AsyncRadioRx():
#     """Class for monitoring hardware interrupts and executing radio
#     data transfer functions for the receiver.
#     """

#     def __init__(self,
#                  irq,
#                  irq_callback,
#                  callback=[default_callback]):
#         """Create new asynchronous receiver class.
#         """
#         self.irq = irq
#         self._irq_callback = irq_callback
#         self.callback = callback
#         self.is_running = False

#     async def _wait(self):
#         await self._interrupt.wait()  # Wait for IRQ edge trigger
#         self._irq_callback()
#         await self._interrupt.wait()  # Discard the next IRQ assertion

#     def _do(self):
#         while True:
#             self.is_running = True
#             future = asyncio.run_coroutine_threadsafe(
#                 self._wait(), asyncio.get_event_loop())
#             future.result()
#             for i in range(len(self.callback)):
#                 self.callback[i]()

#     def start(self):
#         """Start the async irq routine."""
#         thread = threading.Thread(target=self._do)
#         thread.start()


# class AsyncRadioTx():
#     """Class for executing radio data transfer functions for the transmitter.
#     """

#     def __init__(self,
#                  callback=[default_callback]):
#         """Create new radio transmitter class
#         """
#         self.callback = callback
#         self.is_running = False

#     def _do(self):
#         import time
#         while self.is_running:
#             t1 = time.time_ns()
#             for i in range(len(self.callback)):
#                 self.callback[i]()
#             t2 = time.time_ns()
#             diff = (t2 - t1) / 10e9
#             print(f"Takes {diff} ns to run radio_tx callback")

#     def start(self):
#         if not self.is_running:
#             self.is_running = True
#             self._thread = threading.Thread(target=self._do)
#             self._thread.start()

#     def stop(self):
#         self.is_running = False
