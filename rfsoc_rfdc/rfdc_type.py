from enum import Enum, auto

TileState = Enum('TileState', {'POWERED_DOWN': 0, 'POWERED_UP': 15})
EnableState = Enum('EnableState', {'DISABLED': 0, 'ENABLED': 1})
PowerUpState = Enum('PowerUpState', {'STATE_A': 0,  'STATE_B': 1})
PLLState = Enum('PLLState', {'STATE_A': 0,  'STATE_B': 1})
BlockStatusMask = Enum('getBlockStatusMask', {'DAC1': 2,  'DAC01': 3,  'DAC12': 6,  'DAC012': 7, 'DAC123': 14, 'DAC0123': 15})

class TileStatus:
    def __init__(self, status):
        self.dict = status

    def getEnbStatus(self):
        return EnableState(self.dict['IsEnabled'])

    def getTileState(self):
        return TileState(self.dict['TileState'])

    def getBlockStatusMask(self):
        return BlockStatusMask(self.dict['BlockStatusMask'])

    def getPowerUpState(self):
        return PowerUpState(self.dict['PowerUpState'])

    def getPLLState(self):
        return PLLState(self.dict['PLLState'])

    def __str__(self):
        return str(self.dict)

class CoarseMixFreq(Enum):
    OFF = 0x0
    SAMPLE_FREQ_BY_TWO = 0x2
    SAMPLE_FREQ_BY_FOUR = 0x4
    MIN_SAMPLE_FREQ_BY_FOUR = 0x8
    BYPASS = 0x10  # xrfdc.COARSE_MIX_BYPASS

class EventSource(Enum):
    IMMEDIATE = 0x00000000
    SLICE = 0x00000001
    TILE = 0x00000002  # xrfdc.EVNT_SRC_TILE
    SYSREF = 0x00000003
    MARKER = 0x00000004
    PL = 0x00000005

class FineMixerScale(Enum):
    AUTO = 0x0
    SCALE_1P0 = 0x1  # xrfdc.MIXER_SCALE_1P0
    SCALE_0P7 = 0x2

class MixerMode(Enum):
    OFF = 0x0
    C2C = 0x1
    C2R = 0x2  # xrfdc.MIXER_MODE_R2C
    R2C = 0x3
    R2R = 0x4

class MixerType(Enum):
    COARSE = 0x1
    FINE = 0x2  # xrfdc.MIXER_TYPE_FINE
    OFF = 0x3

class MixerSettings:
    def __init__(self, coarse_mix_freq, event_source, fine_mixer_scale, freq, mixer_mode, mixer_type, phase_offset):
        self.coarse_mix_freq = coarse_mix_freq
        self.event_source = event_source
        self.fine_mixer_scale = fine_mixer_scale
        self.freq = freq
        self.mixer_mode = mixer_mode
        self.mixer_type = mixer_type
        self.phase_offset = phase_offset