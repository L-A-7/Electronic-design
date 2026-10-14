# Serial protocols: the essentials

| | UART | I2C | SPI |
|---|---|---|---|
| Wires | TX, RX (+GND) | SDA, SCL (+GND) | SCLK, MOSI, MISO, CS per device |
| Clock | None (both sides agree on a baud rate, e.g. 115200) | Controller drives SCL | Controller drives SCLK |
| Topology | Point to point | Bus, 7-bit addresses, up to ~100 devices | Bus, one CS line per device |
| Speed | ~10 kbit/s–few Mbit/s | 100 k / 400 k / 1 MHz | 1–50+ MHz |
| Electrical | Push-pull | **Open drain + pull-ups** (R sets the rise time with bus capacitance) | Push-pull |
| Typical use | Debug console, GPS, TMC2209 config, PC link via USB-serial | Sensors, DAC/ADC, EEPROM, config chips | Fast ADC/DAC, displays, flash, MAX31865 |
| Failure modes | Baud mismatch, TX/RX swapped, no common GND | Missing pull-ups, address clash, slow edges, bus stuck low (recovery: clock out 9 pulses) | Wrong CPOL/CPHA mode, CS timing, long wires ringing |

## How to learn them (hands-on, with a Nucleo + logic analyser)

1. **UART:** printf over the Nucleo's ST-LINK virtual COM port. Capture TX on the analyser and decode it (start bit, 8 data bits, stop bit).
2. **I2C:** read an ADS1115 / MCP4725 breakout. Look at START, the address + R/W bit, ACK/NACK, repeated START. Try 10 kΩ vs 2.2 kΩ pull-ups on the scope and watch the rise time change.
3. **SPI:** read a MAX31865 or an SPI flash. Try the 4 modes and see which one works and why.
4. Each project board brings a protocol into real use: project 01 uses I2C, project 03 uses SPI (temperature / fast ADC) and UART (stepper driver), and USB CDC replaces UART towards the PC.

Key references: NXP UM10204 (I2C specification), TI SLVA704 (I2C pull-up calculation), the STM32 reference manual chapters on USART/I2C/SPI.
