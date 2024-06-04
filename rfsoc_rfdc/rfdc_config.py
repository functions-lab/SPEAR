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

ZCU216_DEMO3_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 4000.0,
    "DACInterpolationRate": 4,
    "DACNCO": 1000,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 2,
    "ADCNCO": -1000
}

ZCU216_DEMO2_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 5000.0,
    "DACInterpolationRate": 20,
    "DACNCO": 425,
    "ADCSampleRate": 2500.0,
    "ADCInterpolationRate": 10,
    "ADCNCO": -425
}

ZCU216_DEMO1_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 4000.0,
    "DACInterpolationRate": 40,
    "DACNCO": 350,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 20,
    "ADCNCO": -350
}

ZCU216_PKT_MODE_CONFIG = {
    "RefClockForPLL": 500.0,
    "DACSampleRate": 2000.0,
    "DACInterpolationRate": 2,
    "DACNCO": 0,
    "ADCSampleRate": 2000.0,
    "ADCInterpolationRate": 2,
    "ADCNCO": -0
}

GLOBAL_VAR = {
    "DAC_SCALING_FACTOR": 1.0,
    "ADC_SCALING_FACTOR": 1.0
}

ZCU216_CONFIG = merge_dict(ZCU216_MIN_MAX_CONFIG, ZCU216_PKT_MODE_CONFIG)
ZCU216_CONFIG = merge_dict(ZCU216_CONFIG, GLOBAL_VAR)
