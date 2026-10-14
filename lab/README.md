# Lab: instruments and purchase plan

Already owned: oscilloscope and basic tools. Prices are rough 2025–26 street prices.

## Priority 1: needed for project 01 bring-up

| Instrument | Why | Example class | ~Price |
|---|---|---|---|
| Logic analyser 8 ch | Decode I2C/SPI/UART, debug timing | Saleae-clone 24 MHz + sigrok/PulseView (start), DSLogic / Saleae Logic 8 (later) | 15 € / 150–500 € |
| Current-limited bench PSU | Safe first power-up; the most important habit | Programmable 0–30 V / 0–5 A (Korad KA3005P, Riden RD6006 class) | 70–150 € |
| Good DMM | Accurate current/voltage, calibration of the LED driver | Brymen BM235 / BM869s class | 60–200 € |
| USB-C power meter | V/I/energy on USB, PD trigger | FNIRSI FNB58 class | 30–40 € |
| ST-LINK V3 MINIE + Nucleo board(s) | SWD programmer for our own boards; Nucleos for prototyping firmware | **Nucleo-C031C6** (same family as the UV bench MCU, for M1) and later Nucleo-G474RE (project 03 candidate) | 10–25 € each |
| USB-serial cable/adapter, **3.3 V logic**, FTDI 6-pin pinout | Talk to the UV bench's UART console from the PC | FTDI TTL-232R-3V3 (genuine) or CP2102/CH340 adapter with a 3.3 V jumper | 5–25 € |
| Soldering station + hot air + flux, paste, tweezers | SMD assembly and rework | Pinecil / TS101 + cheap hot-air station | 100–200 € |
| Magnification | Inspecting solder joints | Stereo microscope (best) or USB microscope | 50–300 € |

## Priority 2: characterisation quality

| Instrument | Why | ~Price |
|---|---|---|
| Thermal camera (USB-C phone type) | Hot spots, MOSFET/LED temperature check (test step 9) | 250–350 € (InfiRay P2 Pro class) |
| Electronic DC load | Test power stages and supplies | 40 € (module) to 300 € (bench) |
| Function generator (if the scope lacks one) | TIA/filter frequency response | 100–300 € |
| LCR meter | Check passives, inductors, cable parasitics | 50–150 € |
| UV radiometer or calibrated UV sensor | Absolute optical power reference for the bench | 100–500 € depending on the wavelength |

## Priority 3: later (project 03, mixed-signal, EMC)

- Current probe for the scope (stepper motor current)
- Near-field probe set + scope FFT, for basic pre-compliance EMC
- Isolated / differential scope probe

## Safety
- UV-blocking glasses rated for the LED wavelength (365–405 nm) **before** the first light test. A few tens of euros.
