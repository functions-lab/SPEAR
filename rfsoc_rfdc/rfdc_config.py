def merge_dict(dict1, dict2):
    dict2.update(dict1)
    return dict2


ZCU216_MIN_MAX_CONFIG = {
    "RefClockForPLLMin": 102.40625,
    "RefClockForPLLMax": 615.0,
    "RefClockNoPLLDacMin": 500.0,
    "RefClockNoPLLDacMax": 10000.0,
    "RefClockNoPLLAdcMin": 500.0,
    "RefClockNoPLLAdcMax": 2500.0
}

ZCU216_MULTI_BAND_CONFIG = {
    "RefClockForPLL": 300.0,
    "DACSampleRate": 6000.0,
    "DACInterpolationRate": 20,
    "DACNCO": 0,
    "ADCSampleRate": 2400.0,
    "ADCInterpolationRate": 8,
    "ADCNCO": 0
}

ZCU216_MULTI_CH_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 2000.0,
    "DACInterpolationRate": 20,
    "DACNCO": 0,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 20,
    "ADCNCO": 0
}

ZCU216_CONFIG = merge_dict(ZCU216_MIN_MAX_CONFIG, ZCU216_MULTI_BAND_CONFIG)
