# UV bench ↔ main board interface specification (v2.2)

This file is the contract between the UV bench board (project 01, which has its own MCU) and
whatever controls it: the main board (project 03), a Nucleo, or a PC through the UART
console. Any change to it bumps the version and is recorded at the bottom.

> v1.0 replaces v0.x (the 14-pin "DAC + ADC chips" interface). The board now has a local MCU
> and acts as an **I2C target with a register map**.
>
> **v2.0 (2026-10-13) follows the simplified Rev B board** ([`rev-b-simple.md`](rev-b-simple.md)):
> same connector and register layout, but no temperature/voltage monitors, no UART console and a
> fixed address. The removed registers are marked *reserved* so the addresses of the others don't move.

## 1. I2C in 60 seconds (what actually happens on the wires)

- Two wires plus ground: **SCL** (clock, driven by the controller, i.e. the main board) and
  **SDA** (data, both directions). Both are *open drain*: chips only pull them low, and
  pull-up resistors bring them back high.
- Every transfer starts with the **7-bit address** of the target + a R/W bit. The target answers ACK.
- **Register model**, like most I2C sensors. The controller first writes a *register number*,
  then either writes data bytes or (after a "repeated start") reads data bytes. The register
  pointer auto-increments, so one transfer reads several registers.

```
Write 120.0 mW to SETPOINT_POWER (reg 0x04, value 1200 = 0x04B0, little-endian):
  [S] 0x2A+W [A] 0x04 [A] 0xB0 [A] 0x04 [A] [P]

Read STATUS and MEAS_POWER (regs 0x02…0x11 in one go would also work):
  [S] 0x2A+W [A] 0x10 [A] [Sr] 0x2A+R [A] lo [A] hi [N] [P]
S = start, Sr = repeated start, A = ACK, N = NACK (controller: "last byte"), P = stop
```

On the main board's STM32 (HAL) these are two calls:
`HAL_I2C_Mem_Write(&hi2c1, 0x2A<<1, 0x04, I2C_MEMADD_SIZE_8BIT, buf, 2, 10)` and
`HAL_I2C_Mem_Read(...)`.

## 2. Physical layer

**Main-board connector: JST-PH 2.0 mm, 4 pins, keyed. Only 4 wires: power + I2C.**
Cable ≤ 50 cm, ideally a 4-core cable with SDA and SCL not next to each other's long runs of 5 V.

| Pin | Signal | Dir (from bench) | Type | Notes |
|---|---|---|---|---|
| 1 | GND | – | power | |
| 2 | +5V | in | power | ≤ 400 mA, mostly DC (see below) |
| 3 | SDA | bidir | I2C, 3.3 V open drain | |
| 4 | SCL | in | I2C, 3.3 V open drain | |

Same signal order as Grove/Qwiic, but deliberately on a **JST-PH** connector. Qwiic/STEMMA QT
(JST-SH) carries 3.3 V, and plugging a 3.3 V sensor into our 5 V cable would destroy it, so
the connectors must not be interchangeable.

**Why the earlier nINT and SYNC wires were dropped (v1.1):**

| Wire | What it did | Replacement |
|---|---|---|
| nINT (interrupt) | Told the main board "something changed" without waiting to be asked | **Polling.** The main board reads STATUS every 10–100 ms (a 3-byte I2C transfer, ~0.3 ms at 100 kHz). Safety never depended on it: the bench MCU turns the LED off by itself |
| SYNC | Exact timing of the LED modulation, for lock-in detection on the main board | **Not needed:** lock-in detection isn't planned (decision D2). The LED GATE signal has a test point for scope work |

**Shared ground and LED current.** With only one GND wire, the up to 0.33 A LED current returns
through the same wire as I2C. A cable of ~0.1 Ω gives a ~30 mV ground offset, harmless for
I2C (noise margin ~1 V). In Rev B the LED current is **DC** (filtered PWM drives a linear
MOSFET stage, no dark gaps), and the firmware ramps it, so 2 × 10 µF on the bench are enough.

**No separate PC / UART header in Rev B.** For control from a PC, use the main board, a Nucleo,
or a USB-I2C adapter as the I2C controller. A debug UART does exist on the debug header (below).

**Debug header J3 (v2.2):** ST's 14-pin **STDC14**, 1.27 mm, keyed (Samtec FTSH-107-01-L-DV-K):
the connector of the STLINK-V3MINIE's own cable. Pins 3–12 are the standard Cortex 10-pin SWD
layout; pins 13–14 carry USART2 (PA2 = TX → pin 13 VCP_RX, PA3 = RX ← pin 14 VCP_TX), which the
probe shows on the PC as a virtual COM port.

## 3. Electrical

- Logic levels: 3.3 V (I2C inputs on the STM32C0/G0 are 5 V tolerant, but we stay at 3.3 V).
- I2C pull-ups: 4.7 kΩ on the **main board** (Rev B has no pull-ups at all; for a bench test with short wires, a Nucleo's internal pull-ups are usually enough at 100 kHz).
- I2C speed: 100 kHz guaranteed, 400 kHz supported (to verify on the scope with the real cable).
- I2C address: **0x2A** (no address jumper in Rev B; a second bench on the same bus gets another address stored in flash). 0x2A doesn't clash with common parts: EEPROM 0x50, OLED 0x3C, ADS1115 0x48, TMP117 0x48–0x4B.
- The MCU may stretch SCL briefly (clock stretching) while preparing read data. The main board's I2C must allow it, which STM32 I2C does by default.

## 4. Register map

8-bit register addresses, auto-increment. 16-bit values are **little-endian** (low byte first).
Multi-byte values are latched on the first byte read, so lo/hi always belong together.

| Reg | Name | R/W | Type | Meaning |
|---|---|---|---|---|
| 0x00 | WHO_AM_I | R | u8 | Fixed 0xA5 |
| 0x01 | FW_VERSION | R | u8 | major << 4 \| minor |
| 0x02 | STATUS | R | u8 | bit0 LED_ON, bit1 LOCKED (power within ±1 % of target), bit2 SATURATED (target unreachable), bit3 ARM_OFF (UV ARM switch off: drive applied but I_MON ≈ 0; LED disabled in hardware), bit4 MANUAL (front-panel knob in control: set/cleared by a short push on the knob, green LED off; I2C setpoint writes are stored but not applied until the board is back in I2C mode. v1.x: OVERTEMP), bit5 FAULT (latched), bit6 CAL_VALID, bit7 AMBIENT_HIGH |
| 0x03 | CTRL | R/W | u8 | bit0 ENABLE, bit1 MODE (0 = regulated current, loop on I_MON; 1 = regulated optical power, loop on the photodiode), bit6 SAVE_CONFIG (write 1 → store config in flash), bit7 CLEAR_FAULT (write 1) |
| 0x04 | SETPOINT_POWER | R/W | u16 | Regulated modes: 0.1 mW units if CAL_VALID, else 0.01 % of full scale |
| 0x06 | SETPOINT_CURRENT | R/W | u16 | Current mode: 0.1 mA units (0–3300). In power mode: current *limit* |
| 0x0A | RAMP_RATE | R/W | u16 | Max setpoint change, %/s (soft start; 0 = instant) |
| 0x0C | WATCHDOG | R/W | u8 | Seconds without any I2C write before the LED turns off (0 = disabled) |
| 0x10 | MEAS_POWER | R | u16 | Same units as SETPOINT_POWER (photodiode on − off, calibrated) |
| 0x12 | MEAS_CURRENT | R | u16 | 0.1 mA |
| 0x14–0x19 | *reserved* | | | v1.x: MEAS_T_LED, MEAS_V_HEADROOM, MEAS_V_IN (no such hardware in Rev B). Read as 0 |
| 0x1A | MEAS_PD_RAW | R | u16 | ADC counts (minus the dark reading taken at switch-on), for calibration |
| 0x1C | MEAS_AMBIENT | R | u16 | ADC counts, LED off, measured at each switch-on |
| 0x20 | CAL_GAIN | R/W | u32 | µW per 1000 raw counts. Written by the calibration procedure |
| 0x24 | CAL_SAVE | W | u8 | Write 0xC5 to store CAL_GAIN in flash (sets CAL_VALID) |
| 0x30 | *reserved* | | | v1.x: T_LIMIT (no temperature sensor in Rev B) |

Minimal usage from the main board:
1. Read WHO_AM_I and check it is 0xA5.
2. Write SETPOINT_POWER, then CTRL = 0x03 (ENABLE, regulated).
3. Poll STATUS (every 10–100 ms) until LOCKED. Read MEAS_* when needed.
4. Write CTRL = 0x00 for OFF.

## 5. Safety rules (enforced by the bench MCU, on top of the hardware interlock)

- ARM_OFF (UV ARM switch turned off): LED off in hardware, ENABLE cleared. **Not** a fault. Switching it back on does not restart the LED: ENABLE must be written again.
- A hardware fault (no light while current flows, or current with zero drive): LED off, FAULT latched (visible in STATUS at the next poll). It restarts only after CLEAR_FAULT **and** ENABLE written again.
- Watchdog expiry (if enabled): LED off, ENABLE cleared.
- At power-up the LED is **always off**. Setpoints come back from flash, ENABLE never does.
- Current is never above SETPOINT_CURRENT, nor above the hardware maximum ((5 V − V_f) / 3.9 Ω ≈ 330 mA, set by R1).

## 6. UART console

Rev B has a UART only through the debug probe (J3 pins 13–14, USART2, ST-LINK virtual COM port),
from v2.2. It is meant for **debug messages** (`printf`) during development, not as a control
interface: the bench is controlled over I2C. If a console is ever added on it, the SCPI-like
protocol of [`host-protocol.md`](host-protocol.md) is the model. Default: 115200 baud, 8N1.

## Change log
- v0.1 (2026-10-08): first draft (no MCU, 14-pin, DAC + ADC chips).
- v0.2 (2026-10-09): PD_OUT bandwidth note.
- v1.0 (2026-10-09): local MCU on the bench. 6-pin JST-PH, I2C target at 0x2A/0x2B, register map, FTDI-style UART header.
- v1.1 (2026-10-09): 4-pin JST-PH (GND, 5V, SDA, SCL). nINT replaced by polling; SYNC moved to a test pad.
- v1.2 (2026-10-09): no lock-in. Modulated mode and MOD_FREQ removed (0x08 reserved); SYNC not needed.
- v1.3 (2026-10-12): lid switch replaced by a manual UV ARM switch. STATUS bit3 LID_OPEN → ARM_OFF, not latched as FAULT; ENABLE must be rewritten after re-arming.
- v2.0 (2026-10-13): Rev B board. FTDI/UART header, address jumper (0x2B), DNP pull-ups, temperature and voltage monitors removed (registers 0x14–0x19 and 0x30 reserved, STATUS bit4 reserved). MODE 0 is now regulated current (firmware loop on I_MON). ARM_OFF detected from I_MON. LED current is DC: the 220 µF + LC requirement is dropped.
- v2.1 (2026-10-13): front-panel knob (rotary encoder + push) and green mode LED. STATUS bit4 = MANUAL. The knob and the I2C board share one setpoint, so switching modes doesn't make the light jump. Power-up mode: I2C.
- **v2.2 (2026-10-14): debug header J3 is now the 14-pin STDC14 (keyed, plugs straight into the STLINK-V3MINIE cable) instead of the 2×5 Cortex 10-pin. Its pins 13–14 bring USART2 (PA2/PA3) to the probe's virtual COM port, for debug messages. The I2C interface and the register map are unchanged.**
