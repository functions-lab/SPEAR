# Power-on Sequence Steps from page 163 of PG269: Zynq UltraScale+ RFSoC RF Data Converter v2.4 Gen 1/2/3

class RfDcType:

    POWER_ON_SEQUENCE_STEPS = [
        {
            "Sequence Number": 0,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 1,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 2,
            "State": "[Device Power-up and Configuration]",
            "Description": "[The configuration parameters set in the Vivado® IDE are programmed into the converters. The state machine then waits for the external supplies to be powered up. In hardware this can take up to 25 ms. However this is reduced to 200 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 3,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 4,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 5,
            "State": "[Power Supply Adjustment]",
            "Description": "[The configuration settings are propagated to the analog sections of the converters. In addition the regulators, bias settings in the RF-DAC, and the common-mode output buffer in the RF-ADC are enabled.]"
        },
        {
            "Sequence Number": 6,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 7,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 8,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 9,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 10,
            "State": "[Clock Configuration]",
            "Description": "[The state machine first detects the presence of a good clock into the converter. Then, if the PLL is enabled, it checks for PLL lock. The clocks are then released to the digital section of the converters.]"
        },
        {
            "Sequence Number": 11,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 12,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 13,
            "State": "[Converter Calibration (ADC only)]",
            "Description": "[Calibration is carried out in the RF-ADC. In hardware this can take approximately 10 ms, however this is reduced to 60 µs in behavioral simulations.]"
        },
        {
            "Sequence Number": 14,
            "State": "[Wait for deassertion of AXI4-Stream reset]",
            "Description": "[The AXI4-Stream reset for the tile should be asserted until the AXI4-Stream clocks are stable. For example, if the clock is provided by a MMCM, the reset should be held until it has achieved lock. The state machine waits in this state until the reset is deasserted.]"
        },
        {
            "Sequence Number": 15,
            "State": "[Done]",
            "Description": "[The state machine has completed the power-up sequence.]"
        }
    ]

    def __init__(self):
        pass
