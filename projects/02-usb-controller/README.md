# Project 02 (optional, later): small STM32 USB controller

> Since 2026-10-09 the UV bench has its own MCU and a UART console, so a €3 USB-serial cable
> already gives PC control. This project stays useful as a cheap rehearsal of USB + STM32
> layout before the main board, and as an I2C controller for several benches.

**Purpose:** drive the UV bench (project 01) from a PC over USB, and prove the risky parts of
the main board on a small, cheap board first.

- STM32 with crystal-less USB (STM32G0B1 / C071 / G431 class), USB-C receptacle (5.1 kΩ CC pull-downs), ESD protection (USBLC6-2), 3.3 V LDO
- SWD header (Tag-Connect or 2×5 1.27 mm), reset button, BOOT0 option, status LEDs
- The 4-pin JST-PH UV bench connector (interface spec v1.3: GND, 5 V, SDA, SCL) with an eFuse / current-limited load switch on its 5 V output
- Firmware: USB CDC (virtual serial port) running the **same SCPI-like protocol** already implemented on the Nucleo, see [`projects/01-uv-bench/docs/host-protocol.md`](../01-uv-bench/docs/host-protocol.md). Only the transport changes, so the Python client is reused unchanged

New skills: MCU minimum system, USB layout (90 Ω differential pair, kept short), firmware USB stack, a PC-side tool.
