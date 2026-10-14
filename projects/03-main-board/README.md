# Project 03: main STM32 instrument board (preliminary notes)

| Block | Preliminary direction |
|---|---|
| MCU | **STM32G474**: 5 ADCs, 7 DAC channels, 6 internal op-amps/PGAs, HRTIM, USB FS. It fits "4 amplified acquisitions + 2 DACs" naturally |
| Power | USB-C **PD sink** (e.g. STUSB4500 / CH224K) to get 9–20 V for the stepper. Buck to 5 V (UV bench) and LDO to 3.3 V; analogue rail filtered separately |
| Stepper | TMC2209 (UART configuration, silent StealthChop) or DRV8825 |
| 4 acquisition channels | Input protection → external precision op-amp gain stage (or the internal PGA) → anti-alias filter → ADC |
| Temperature | PT100/PT1000 + MAX31865 (SPI), or TMP117 (I2C) for board temperature |
| 2 DACs | Internal DAC + output buffer op-amps |
| Interfaces | UV bench connector (interface spec), I2C/SPI expansion header, SWD |
| Layout | 4-layer (signal / GND / power / signal), separate analogue and power zones, careful stepper return currents |

Start this only after project 01 (and preferably 02) has been characterised.
