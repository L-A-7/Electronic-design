# UV bench: MCU selection

> **Rev A document, kept for reference (2026-10-13).** The board was simplified to Rev B:
> [`rev-b-simple.md`](rev-b-simple.md). The MCU choice (STM32C031F6P6, TSSOP-20) is unchanged.

> **Update 2026-10-12: switched to the STM32C031F6P6 (TSSOP-20), same chip in the smaller package.** A pin-by-pin check against the KiCad symbol showed all 16 signals fit, with 1 spare. TIM1_CH2 is available on the shared PA9/PA11 pad, which the table below didn't account for. The pin map is in [`design-synthesis.md`](design-synthesis.md) §5. The analysis below is kept for reference.

**Original recommendation: STM32C031K6T6** (LQFP-32). Cortex-M0+ at 48 MHz, 32 KB flash, 12 KB RAM,
about €0.60–1.00 in single quantities. It's the **same chip family as the Nucleo-C031C6**
used at M1, so the firmware moves from the Nucleo to our board with only a pin-mapping change.

Values below come from the ST product pages / datasheets as I know them. **Confirm each one
in the STM32C031 datasheet and errata sheet before the schematic (M2).** That's part of the job.

## 1. What the MCU has to do

| Task | Peripheral needed | Load |
|---|---|---|
| Set the LED current (analogue setpoint) | 1 timer PWM channel at ~47 kHz, 10 bit → RC filter | Hardware |
| Switch the LED on/off for ambient measurement (dark gap ~50 µs every 10 ms) | 1 timer channel or GPIO | Hardware |
| Sample photodiode with LED on and off, plus current, temperature, headroom, V_in | 12-bit ADC, 5 external channels + internal VREFINT and temperature, timer-triggered, DMA | Hardware |
| PI control loop at ~1 kHz | CPU | ~10–20 µs per update in software float (no FPU), < 2 % CPU |
| I2C target with register map | I2C1 (target mode, clock stretching) | Interrupts |
| UART text console 115200 baud | USART | Interrupts / DMA |
| Store calibration + settings | Flash (last page) | Rare writes |
| Safety: UV ARM switch input, over-temperature, watchdog | GPIO, IWDG | |
| Programming / update | SWD; built-in UART bootloader (through the FTDI header, no ST-LINK needed) | |

Nothing here is demanding. The real constraints are **pin count**, **ADC quality** and
**staying in the familiar STM32 / CubeIDE toolchain**.

## 2. Pin budget

| # | Signal | Type |
|---|---|---|
| 1–2 | I2C SDA, SCL | I2C1, 5 V tolerant pins |
| 3–4 | UART TX, RX | USART1 or USART2 (the bootloader needs a specific USART; check AN2606) |
| 5–6 | SWDIO, SWCLK | Debug (SWCLK shares the BOOT0 function on C0) |
| 7 | SETPOINT_PWM | TIM1 channel |
| 8 | GATE | TIM1 channel (synchronised with the ADC trigger) |
| 9 | PD (TIA output) | ADC |
| 10 | I_LED (×10 sense amp) | ADC |
| 11 | T_LED (NTC divider) | ADC |
| 12 | V_HEADROOM (MOSFET drain divider) | ADC |
| 13 | V_IN (5 V divider) | ADC |
| 14 | UV ARM switch sense | GPIO input + EXTI |
| 15 | Status LED | GPIO |
| 16 | I2C address jumper (0x2A / 0x2B) | GPIO, read at boot |
| + | NRST | Dedicated pin + 100 nF |
| | **16 I/O needed** | |

| Package | Usable I/O (approx.) | Verdict |
|---|---|---|
| **STM32C031F6, TSSOP-20 (chosen 2026-10-12)** | 17 (including SWD) | **Fits all 16 with 1 spare.** The mapping works, checked against the KiCad symbol |
| **STM32C031K6, LQFP-32** (0.8 mm pitch) | ~29–30 | **Comfortable**: ~12 spare pins for debug, future features, test GPIOs. Easy to hand-solder |
| STM32C031C6, LQFP-48 | ~44 | The Nucleo's chip. Larger than needed |

## 3. Key specifications (STM32C031K6T6)

| Parameter | Value | Why it matters here |
|---|---|---|
| Core | Arm Cortex-M0+, 48 MHz, no FPU | Plenty for a 1 kHz PI loop; use float sparingly or fixed-point |
| Flash / RAM | 32 KB / 12 KB | Firmware estimate: 15–22 KB with HAL (less with LL drivers), 2–4 KB RAM. Avoid `printf` with float (+8 KB) |
| Flash page | 2 KB | One page reserved for calibration/config. Write only on explicit SAVE (limited write endurance) |
| Clock | Internal HSI48 RC, ±1 % | Good enough for I2C (the controller provides the clock) and UART (tolerates ~±2 %). **No crystal needed** now that lock-in is dropped |
| ADC | 12 bit, ~0.4 µs conversion, up to ~19 channels, **hardware oversampling** (up to 256×, giving 14–16 bit effective), DMA | The heart of the regulation. Oversampling the on/off samples reduces noise for free |
| ADC reference | VREF+ tied to VDD internally on these packages | **ADC accuracy = 3.3 V supply accuracy.** Use a low-drift LDO and correct with VREFINT (factory-calibrated value in system memory). Expect ~0.5–1 % stability over temperature, enough for steady fluorescence excitation |
| Timers | TIM1 (advanced, 16 bit), TIM3 (16 bit), TIM14, TIM16, TIM17 | TIM1: setpoint PWM + GATE + ADC trigger, all phase-locked. TIM3: loop tick |
| Communication | I2C1 (up to 1 MHz, target mode, dual address), USART1 + USART2, SPI1 | I2C to the main board, USART to the PC |
| DMA | 3 channels + DMAMUX | ADC → RAM, optionally UART |
| Safety | IWDG (independent watchdog), WWDG, brown-out reset | Watchdog resets the MCU if firmware hangs. At reset, GATE goes low, so the LED is off |
| Supply | 2.0–3.6 V, a few mA at 48 MHz | Runs from the 3.3 V LDO |
| Temperature | −40…85 °C (suffix 6) or …125 °C (suffix 3) | Suffix 6 is fine |
| Bootloader | Built-in ROM bootloader (USART, I2C) | Firmware update with STM32CubeProgrammer through the FTDI cable, or later from the main board over I2C |

## 4. Alternatives considered

| MCU | For | Against |
|---|---|---|
| STM32C011F6 (TSSOP-20) | Cheapest (~€0.40), same family | Pin budget too tight (see §2), 6 KB RAM |
| STM32G031K8 (LQFP-32) | 64 MHz, 64 KB flash, 8 KB RAM, similar price | Different family from the Nucleo-C031 (also fine: a Nucleo-G031K8 exists). Nothing we need that the C031 lacks |
| STM32F030 / F103 ("Blue Pill" class) | Lots of tutorials | Older, more expensive, F103 clones are common |
| ATtiny / AVR, RP2040, ESP32 | — | Leaves the STM32/CubeIDE toolchain you're building up. ESP32/RP2040 are oversized, and RP2040 has a weak ADC |

## 4b. Wider view: breadboard-friendly and smaller options

STM32 chips don't come in DIP packages, so on a breadboard you use one of these instead:
a **module** with pins at 2.54 mm, or an SMD chip soldered on a **DIP adapter**.

### Breadboard-pluggable boards

| Board | MCU | Breadboard? | ~Price | Comment |
|---|---|---|---|---|
| **NUCLEO-G031K8** (Nucleo-32, Arduino-Nano footprint) | STM32G031K8T6, **LQFP-32, the same package as our target** | **Yes, plugs straight in** | ~€11 | Built-in ST-LINK (programming + virtual COM port over one USB cable). The strongest breadboard option |
| Other Nucleo-32 boards (L031K6, F031K6, F042K6, G431KB…) | Various | Yes | €11–15 | Same format; G431KB is the project 03 family (much bigger) |
| NUCLEO-C031C6 (Nucleo-64) | STM32C031C6T6 (LQFP-48) | No, it's too wide. Use jumper wires to the breadboard | ~€11 | The current plan. Fine with jumper wires |
| **STM32C0116-DK** discovery kit | STM32C011F6P6, TSSOP-20, on a small **DIL-20 plug-in module** (check the product page) | The DIL-20 module can go on a breadboard | ~€10 | The cheapest C0, in the 20-pin package. Good for trying the "small" option |
| TSSOP-20 / LQFP-32 → DIP adapter PCB + bare chip | Any (C011F6, C031K6, G031K8…) | Yes | €1–2 + chip | You solder the chip yourself (good SMD practice) and add a 100 nF cap + an SWD header. Program with an ST-LINK |
| "Blue Pill" (F103C8) / "Black Pill" (F401/F411) third-party boards | Older F1 / larger F4 | Yes | €3–10 | Popular and cheap, but F103 clones/counterfeits are common and these chips are far bigger than needed. Not recommended for this board |

### Smaller packages (same silicon family)

| Package | Size | Pins / usable I/O | Hand soldering | Verdict for our board |
|---|---|---|---|---|
| SO-8 (STM32C011J6, G031J6) | 4.9 × 6 mm | 8 / ~6 | Very easy | Too few pins (we need 13–16) |
| WLCSP-12 (C011) | ~1.7 mm | 12 / ~10 | No (needs reflow + X-ray) | No |
| **TSSOP-20** (C011F6, C031F6, G031F8) | 6.5 × 4.4 mm | 20 / ~17 | Easy (0.65 mm pitch) | **Possible if the design is trimmed** (see below) |
| UFQFPN-20 / 28 / 32 | 3×3 / 4×4 / 5×5 mm | 20 / 28 / 32 | Hot air or a reflow plate, or assembly by the fab | Fine if JLCPCB-style assembly is used |
| **LQFP-32** (C031K6, G031K8) | 7 × 7 mm (9 × 9 with leads) | 32 / ~29 | Easy (0.8 mm pitch) | **Current choice**, comfortable margin |

**Making it fit in 20 pins.** Trim 16 → 13 signals:
- Drop the V_IN measurement (nice to have).
- Drive the status LED from the GATE signal (it shows "LED on", which is the important part).
- Replace the address jumper with an **I2C address stored in flash** (set once over UART). That's even more flexible.

13 signals in ~17 usable pins leaves a small margin. Still verify in CubeMX that the needed
alternate functions (I2C1, USART, TIM1 ch1/ch2, 4 ADC inputs) all land on available pins.

### Comparison of the realistic candidates

| | **STM32C031K6** (current) | STM32G031K8 | STM32C011F6 | STM32C071 |
|---|---|---|---|---|
| Core / clock | M0+ / 48 MHz | M0+ / 64 MHz | M0+ / 48 MHz | M0+ / 48 MHz |
| Flash / RAM | 32 KB / 12 KB | 64 KB / 8 KB | 32 KB / 6 KB | 128 KB / 24 KB |
| Package for us | LQFP-32 | LQFP-32 | TSSOP-20 | LQFP-32/48 |
| Breadboard dev board | Nucleo-64 (jumper wires) | **Nucleo-32 (plugs in)** | DK with DIL-20 module | Nucleo-64 |
| Extra | Cheapest per pin | More flash, faster | Smallest/cheapest | **Crystal-less USB**: the UV board could plug into a PC by USB directly, without the USB-serial cable |
| ~Price (1 pc) | €0.60–1.00 | €0.80–1.30 | €0.40–0.60 | €1.20–1.80 |

**Bottom line:**
- **C031K6 stays a good choice.**
- **G031K8 is equally good, and better if you want to prototype on a breadboard**: its
  Nucleo-32 plugs straight in and carries the exact target chip and package. The firmware
  differences between C0 and G0 are minor (same HAL style, same peripherals).
- **C011F6** if small size and cost matter more than margin.
- **C071** only if you want native USB on the UV board itself.

## 5. Hardware rules around the MCU (for the schematic)

- 100 nF on each VDD pin + 4.7 µF bulk close to the MCU. For the analogue supply, add a ferrite bead + 1 µF if the package has a separate VDDA (check the pinout).
- NRST: 100 nF to GND, routed to the SWD header.
- BOOT: on C0, boot selection is in option bytes and the BOOT0 function shares SWCLK. Read AN2606 + the reference manual's "boot modes" section **before** layout, and keep a way to enter the bootloader (a button or a pad on the right pin).
- I2C pins: series 33 Ω optional; DNP pull-ups (the main board provides them).
- ADC inputs: source impedance low (op-amp outputs) or a 1–10 nF cap at the pin for the dividers. ADC sampling time sized for it (CubeMX).
- SWD header: 2×5 1.27 mm (ST-LINK V3 MINIE); FTDI header for UART + 5 V.
- GATE pin: 10 kΩ pull-down, so the LED stays off during reset/programming.

## 6. Next steps

1. Buy the **Nucleo-C031C6** (M1) and a couple of STM32C031K6T6 for the board.
2. **CubeMX**: create the project for STM32C031K6Tx and assign the 16 signals of §2. Check
   there's no conflict between the I2C, USART, TIM1 channels and ADC inputs, and that the
   bootloader USART lands on the FTDI header pins. Export the pin list for the schematic.
3. Develop the firmware on the Nucleo with the **same peripherals** (I2C1, USARTx, TIM1, ADC)
   so the port is only a pin change.
