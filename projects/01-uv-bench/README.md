# Project 01: UV LED bench board (Rev B: simple version with its own MCU)

> **Start here: [`docs/rev-b-simple.md`](docs/rev-b-simple.md)**, the simplified Rev B (2026-10-13): 21 parts
> (knob included), one schematic sheet, 58 × 32 mm board, every block explained. KiCad: [`hardware/`](hardware/README.md).
> The requirements below are Rev A's; Rev B drops R6 (UART), most of R7 (only current and light are
> monitored) and the synchronous ambient rejection of R4. The Rev A design is in
> [`docs/design-synthesis.md`](docs/design-synthesis.md) and [`hardware/archive/rev-a/`](hardware/archive/rev-a/).

A self-contained UV source: you **ask for an optical power, and the board holds it**. A small
STM32 on the board runs the photodiode feedback loop, the LED drive and the safety logic. The
main board (or a PC) only sends short commands: *power = 120 mW, ON / OFF, read status*.

- 365 nm UV LED, ~1 W electrical (≈ 300 mA), for **fluorescence excitation**
- Powered with 5 V over the same cable that carries the commands
- **I2C** link to the main board (the board is an I2C *target*), plus a **UART header** so a
  PC can drive it directly with a €3 USB-serial cable. That makes the board usable on its own.

> 2026-10-09: architecture changed from "I2C DAC + ADC, no MCU" to "local MCU". The reasons
> are in §2.

## 1. Requirements

| ID | Requirement | Notes |
|---|---|---|
| R1 | Supply: 5 V, ≤ 2 W total | From the main board connector or the UART/FTDI cable |
| R2 | 365 nm LED, constant-current drive 0–300 mA | Linear current sink (no switching noise) |
| R3 | **Closed-loop optical power**: the MCU holds the photodiode reading at the requested value | Open-loop current mode also available |
| R4 | **Ambient-light rejection without an optical filter**: housing + LED on/off synchronous measurement | See §4 |
| R5 | I2C target, register map in [`docs/interface-spec.md`](docs/interface-spec.md): set power, ON/OFF, mode, read measurements/status. **Cable: 4 wires** (GND, 5 V, SDA, SCL) | The main board polls STATUS; no interrupt wire |
| R6 | UART text console (same SCPI-like commands as [`docs/host-protocol.md`](docs/host-protocol.md)) on an FTDI-style header | Standalone use from a PC, debugging |
| R7 | Monitoring: LED current, LED temperature, driver headroom, supply voltage, ambient level | Reported over I2C/UART |
| R8 | Hardware enable: a manual latching **UV ARM switch** that cuts the LED independently of the MCU (replaces the lid switch, 2026-10-12). Firmware watchdog: LED off if commands stop (optional timeout) | [`learning/uv-safety.md`](../../learning/uv-safety.md) |
| R10 | LED + photodiode on the same PCB under a light-tight housing with a side pocket for the photodiode | Mechanics in FreeCAD from the STEP export |
| R11 | SWD programming header; firmware update over UART/I2C later (STM32 built-in bootloader) | |
| R12 | Input protection (reverse polarity, TVS, soft inrush); test points on all key nodes | Design for test |

## 2. Why a local MCU (and why it's a good idea)

| | No MCU (previous plan) | **Local MCU (now)** |
|---|---|---|
| Who runs the feedback loop | Main board, over the cable | **The UV board itself**, so the loop is fast and local |
| What the main board has to do | Drive the DAC, read the ADC, run a PI loop, do the PWM timing | **Write one register** ("120 mW, ON") |
| Cable | 14 wires incl. PWM and analogue | **4 wires**: GND, 5 V, SDA, SCL |
| Usable without the main board | No | **Yes**, through the UART header from a PC |
| Parts | DAC chip + ADC chip | One ~€0.50 MCU replaces both (it has a 12-bit ADC with hardware oversampling, timers for PWM, I2C, UART) |
| Effort | Simple hardware, firmware on the main board | Firmware on a second MCU, which is excellent STM32 practice (timer-triggered ADC + DMA, I2C target, control loop) |

## 3. Architecture

```
 Connector (4 pins) ──► 5V ──► [rev-pol + TVS + LC filter] ──┬──► 5V_LED ─► UV LED ─► MOSFET ─► Rsense ─► GND
   SDA/SCL ◄──────────────────────┐                          └──► LDO 3.3 V ─► MCU + analogue          ▲
                                  │                                                                    │ gate
                                  │      ┌──────────────── STM32C0 / G0 ─────────────────┐              │
                                  └──────┤ I2C target (regs)       UART ◄─► FTDI header   │      op-amp current loop
                                         │ GPIO                                           │              ▲
                                         │ TIM PWM ch1 ─► RC filter ─► current SETPOINT ──┼──► [AND: GATE · ARM_OK] ─┘
                                         │ TIM PWM ch2 ─► GATE (on/off, dark gaps) ───────┘
                                         │ ADC (timer-triggered, DMA):                    │
   Photodiode ─► TIA ────────────────────┤   PD (sampled LED-on AND LED-off)              │
   Rsense ─► ×10 amp ────────────────────┤   I_LED                                         │
   NTC (near LED) ───────────────────────┤   T_LED                                         │
   MOSFET drain ÷ ───────────────────────┤   V_HEADROOM, V_IN, + internal VREFINT & temp   │
   UV ARM switch ────────────────────────┤ GPIO (and the hardware AND gate)               │
                                         └────────────────────────────────────────────────┘
```

**How "send a power, it adjusts itself" works:**
1. The main board writes `SETPOINT_POWER = 120.0 mW` and `CTRL = ENABLE | REGULATED`.
2. Every few hundred µs the MCU samples the photodiode **with the LED on and with it off**. The difference is the LED's light only (§4).
3. A PI controller (running at ~1 kHz) adjusts the current setpoint until the measured power matches the request.
4. If the target can't be reached (current at maximum, or no headroom), the MCU sets `STATUS.SATURATED`. The main board sees it at its next STATUS poll.

**Two notes for beginners:**
- **"Power" needs a calibration.** The photodiode measures *relative* light. To show real
  milliwatts, measure the output once with a reference (a UV power meter, or a calibrated
  sensor borrowed from a lab) and store the factor in the MCU's flash (`CAL_*` registers).
  Until then, power is given in % of full scale.
- **Regulation holds the photodiode reading, nothing more.** If the geometry changes (the
  housing moves, the window gets dirty), the board holds the wrong value faithfully. That is
  why the photodiode and LED share one rigid PCB + housing.

## 4. Ambient light without a filter: three cheap layers

1. **Geometry (housing): "scatter spot + dark chamber".** A small PTFE patch inside the
   housing catches a few wide-angle LED rays (outside the useful beam). A cheap silicon
   photodiode in a closed dark chamber looks at that patch through a 0.5–1 mm pinhole. A lip
   hides the patch from the exit window, so outside light and UV reflected by the sample
   can't reach it. The photodiode receives only ~10 µW and sits ≥ 15 mm from the LED, behind
   a milled thermal slot in the PCB, so it stays cool. Details and the light budget are in
   [`docs/photodiode-selection.md`](docs/photodiode-selection.md). Use black matte housing
   material: white and coloured plastics fluoresce and degrade under UV.
2. **Synchronous on/off measurement (electronic filter, free).** Ambient light changes slowly
   (DC, or 100 Hz flicker from mains lighting). The LED can be switched in microseconds. So:
   `PD(LED on) − PD(LED off)` = LED light only. Average over many on/off pairs and both the DC
   ambient and the 100 Hz flicker cancel.
   - The MCU inserts a short dark gap (~50 µs every 10 ms, a 0.5 % dip). If
     that dip is a problem for an experiment, rely on the housing alone and measure ambient only while the LED is OFF.
   - This needs a photodiode amplifier fast enough to settle in a few µs (bandwidth ≈ 100 kHz). It's checked in simulation S4.
3. **Cheap photodiode.** A blue-enhanced silicon **Osram BPW 34 B** (rated 350–1100 nm, ~€1–2). GaP UV photodiodes (~€70) were rejected on cost. The M1 test compares it with a GUVA-S12SD and a 385–395 nm LED used as a detector.

## 5. MCU choice

**STM32C031F6P6** (TSSOP-20; was C031K6T6 LQFP-32 until 2026-10-12. Cortex-M0+ 48 MHz, 32 KB flash, 12 KB RAM, ~€0.60–1.00). It's
the same family as the Nucleo-C031C6 used for prototyping, its 20 pins take all 16 signals
with one spare (pin map: [`docs/design-synthesis.md`](docs/design-synthesis.md) §5), and it needs no crystal. Background, alternatives
and schematic rules: [`docs/mcu-selection.md`](docs/mcu-selection.md).

- **No DAC is needed.** A timer PWM at ~47 kHz, 10 bit, through a 2-pole RC filter gives the
  analogue current setpoint. The control loop dithers between steps, which gives finer effective resolution.
- **ADC accuracy = regulation accuracy.** The ADC reference is the 3.3 V supply, so use a
  low-drift LDO and correct with the internal reference (VREFINT).

## 6. Power budget and headroom (unchanged)

At 300 mA: `4.75 V − Vf (3.5…4.0) − V_Rsense (0.10) − V_DS (~0.1) = +1.0 … +0.55 V`, so it
works, but the **M1 measurement decides** whether a 5 → 7 V boost is needed. MOSFET ≈ 0.35 W
(DPAK/SOT-223 + copper). LED ≈ 0.7 W of heat on the PCB, so thermal vias to an aluminium
plate under the board. MCU + analogue adds only ~10 mA.

## 7. Milestones

- [x] **M0 Toolchain:** KiCad project ([`hardware/`](hardware/README.md)), fab rules, `tools/kicad-check.sh`
- [ ] **M1 Breadboard proof.** **Nucleo-C031C6** (same family as the target MCU) + current sink on protoboard + candidate photodiodes in a dark box (a cardboard box is fine). Firmware on the Nucleo: PWM setpoint, timer-triggered ADC on/off sampling, PI loop, I2C target, UART console. Measure LED Vf(I, T) to make the boost decision. The same firmware moves to the custom board later
- [ ] **M2 CubeMX pinout + schematic + simulation + housing concept:** [`docs/verification-plan.md`](docs/verification-plan.md) §1
- [ ] **M3 Layout + review:** [`docs/verification-plan.md`](docs/verification-plan.md) §2
- [ ] **M4 Fabrication**
- [ ] **M5 Bring-up + characterisation:** [`docs/verification-plan.md`](docs/verification-plan.md) §3
- [ ] **M6 Calibration, documentation; main-board driver**

## 8. Decisions

| # | Decision | Status |
|---|---|---|
| D1 | 365 nm, ~1 W electrical (300 mA) | Decided 2026-10-09 |
| D2 | Fluorescence excitation, continuous light. **No lock-in** (so no modulation mode, no SYNC, no crystal) | Decided 2026-10-09 |
| D3 | Cheap Si photodiode (BPW 34 B), no filter, PTFE scatter spot + dark chamber | Decided 2026-10-09; final part confirmed by the M1 test |
| D4 | Project 02 (USB controller): later | Less needed now: the UART header + a USB-serial cable gives PC control directly |
| D7 | **Local MCU on the UV board; I2C target to the main board + UART console** | **Decided 2026-10-09** |
| D5 | Boost converter or not | Open, M1 measurement |
| D6 | **Option B: one PCB, LED on a 20 mm copper star in a Ø 22 mm cut-out, screwed to the aluminium plate**. Flashlight reflector (1 mm side port for the photodiode) + ZWB2 window. Photodiode + TIA on the PCB at the cut-out edge | Decided 2026-10-11, see [`docs/design-synthesis.md`](docs/design-synthesis.md) §1 |
| D8 | ~~STM32C031K6T6 (LQFP-32)~~ → **STM32C031F6P6 (TSSOP-20)**: all 16 signals fit with 1 spare, same timer/ADC/I2C/UART pins as the Nucleo. See [`docs/design-synthesis.md`](docs/design-synthesis.md) §5 | Revised 2026-10-12; verify in CubeMX |
| D9 | Lid interlock → manual latching **UV ARM switch** (panel toggle) on J6; LED needs a new ENABLE after re-arming | Decided 2026-10-12, synthesis §3.5 |

## 9. Candidate parts (to confirm against stock and datasheets)

| Function | Candidates |
|---|---|
| MCU | STM32C031F6P6 (TSSOP-20); LQFP-32 C031K6T6 if more pins are ever needed |
| UV LED | 365 nm 3535 LED on 20 mm star, harvested from a Convoy S2 LG 365 nm + ZWB2 flashlight (Nichia NVSU233B as upgrade); final list in [`docs/design-synthesis.md`](docs/design-synthesis.md) §3 |
| Photodiode | Osram BPW 34 B (blue-enhanced Si, 350–1100 nm); M1 comparison with GUVA-S12SD and a 385–395 nm LED-as-detector. Optics: PTFE scatter spot + pinhole dark chamber. See [`docs/photodiode-selection.md`](docs/photodiode-selection.md) |
| Op-amps | Current loop: zero-drift (OPA2333 / TLV2333 class). TIA: fast CMOS RRIO, ~10 MHz GBW (TLV9062 / OPA2376 class). Rsense amp: second half of a dual |
| MOSFET | Logic-level N-FET, DPAK/SOT-223, low Ciss |
| LDO 3.3 V | Low-noise, ±1 %, low tempco (TPS7A20 class) |
| Protection | P-FET reverse polarity, SMAJ5.0A TVS, ferrite + bulk cap |
| Connectors | Main board: JST-PH 4-pin (keyed, pre-crimped leads available). PC: 6-pin 2.54 mm FTDI-style header. SWD: 2×5 1.27 mm (ST-LINK V3 MINIE) |
| Bulk capacitor | ≥ 220 µF low-ESR on 5V_LED, which absorbs the current steps (switch-on, dark gaps) locally |
