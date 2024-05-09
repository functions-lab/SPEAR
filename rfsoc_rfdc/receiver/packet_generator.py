from pynq import DefaultIP

_fsm_lut = ['S_IDLE', 'S_INCR', 'S_TLAST']


class PacketGenerator(DefaultIP):

    def __init__(self, description):
        super().__init__(description=description)
        self._packet_size = 4  # Minimum packet size is set to 4 in hardware

    bindto = ['user.org:user:adc_packet_generator:1.0']

    @property
    def _enable(self):
        return self.read(0x00)

    @_enable.setter
    def _enable(self, value):
        self.write(0x00, value)

    @property
    def _packet_size(self):
        return self.read(0x04)

    @_packet_size.setter
    def _packet_size(self, value):
        self.write(0x04, value)

    @property
    def _state(self):
        return self.read(0x08)

    @property
    def packetsize(self):
        return self._packet_size

    @packetsize.setter
    def packetsize(self, value):
        if not isinstance(value, int):
            raise TypeError('Packetsize must be of type integer.')
        if (value < 4) or (value > 2**32-1):
            raise ValueError('Packetsize must be between 2 and 2^32-1')
        self._packet_size = value

    def enable(self):
        self._enable = 1

    def disable(self):
        self._enable = 0

    def state(self):
        return _fsm_lut[self._state]
