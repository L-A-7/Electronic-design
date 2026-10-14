# Verification plan: simulate, review, then measure

> **Rev A document, kept for reference (2026-10-13).** The board was simplified to Rev B:
> [`rev-b-simple.md`](rev-b-simple.md). Tests on the removed parts (TIA, current loop, NTC, UART) no longer apply; the light/I2C tests do.

## 1. Simulation (M2), in KiCad's ngspice simulator; files in `../simulation/`

| # | What | Analysis | Pass criterion |
|---|---|---|---|
| S1 | Current-sink DC operating point | `.op` + `.dc` sweep of V_in 4.5–5.25 V and Vf min/max | Regulation holds down to V_in = 4.75 V at I_max |
| S2 | **Current-loop stability** (op-amp driving the MOSFET's Ciss is a classic oscillator) | `.ac` loop gain (break the loop with a large L / C, or use Middlebrook) + `.tran` setpoint step | Phase margin ≥ 45°, step overshoot < 10 %, no ringing |
| S3 | Gate switching + PWM setpoint filter | `.tran`: GATE on/off edges; 47 kHz PWM through the 2-pole RC filter | Current rise/fall < 5 µs; setpoint ripple < 0.1 % of full scale |
| S4 | Photodiode TIA (on/off sampling) | `.ac` noise gain with the photodiode capacitance; choose R_f/C_f; `.tran` with a 50 µs dark gap; `.noise` | Stable (PM ≥ 45°); settles to < 0.5 % within 10 µs after an LED edge, so on/off samples are valid |
| S5 | Thermal | Python calculation: P_FET over the full V_in/Vf/I range → T_j with the pad's θ_JA | T_j < 100 °C at 40 °C ambient |
| S6 | Monte Carlo on resistor tolerances | `.step` / Python sweep | Current accuracy budget ±5 % before calibration |
| S7 | Control loop (Python model) | Discrete PI loop with the measured LED/photodiode response and sample timing; ambient + 100 Hz flicker added | Settles < 50 ms without overshoot; ambient rejection > 40 dB |

Use **vendor SPICE models** (TI, ADI, Onsemi, Vishay) for the op-amp and MOSFET. Generic
models hide exactly the stability problems we want to see.

## 2. Pre-fabrication checks (M3)

Automated: `tools/kicad-check.sh projects/01-uv-bench/hardware/uv-bench`, which runs ERC,
DRC with schematic parity, and the exports.

Manual review checklist:
- [ ] Fab house design rules (clearance, minimum track, drill, annular ring) loaded in Board Setup *before* routing
- [ ] Every symbol has a footprint verified against the datasheet land pattern; pin 1 marked; MPN field filled
- [ ] LED current loop (5 V → LED → FET → R_sense → GND) is short, wide and away from the TIA
- [ ] R_sense uses a Kelvin connection to the op-amp and ADC
- [ ] TIA: short input node, guard ring around the op-amp's inverting input, C_f right at the op-amp
- [ ] Solid ground plane on layer 2 (4-layer) or bottom (2-layer), with no splits under signals
- [ ] Decoupling cap next to each IC power pin, via straight to the plane
- [ ] MOSFET copper area sized from S5; thermal vias if needed
- [ ] Test points: 5V_IN, 5V_LED, 3V3, SETPOINT (filtered), GATE, R_SENSE, TIA_OUT, SDA, SCL, GND loops
- [ ] MCU: decoupling (100 nF + 1 µF on VDD/VDDA), NRST cap, BOOT0 handling per the datasheet, SWD + UART headers reachable with the housing fitted
- [ ] Photodiode + side pocket geometry checked in FreeCAD against the housing (baffle, hole)
- [ ] Silkscreen: connector pin 1, polarity, signal names on test points, board name + revision + date
- [ ] Mounting holes; STEP export checked in FreeCAD against the heatsink / enclosure
- [ ] 3D viewer check: component collisions, connector orientation, cable exit
- [ ] Gerbers checked in the KiCad Gerber viewer (or the fab's online viewer)

## 3. Bring-up and characterisation (M5)

Do these in order. Don't skip ahead.

1. Visual inspection under a magnifier/microscope: solder bridges, part orientation.
2. Unpowered: resistance 5V→GND and 3V3→GND (should be > 1 kΩ; a short means stop).
3. Power from a **current-limited bench supply** (5.0 V, 100 mA limit), not from USB. Check the idle current.
4. Check the 3V3 rail and its ripple on the scope.
5. Connect the ST-LINK over SWD: the MCU is detected. Flash a blink + UART "hello" firmware.
6. UART console via the USB-serial cable: `*IDN?` answers. Then I2C from a Nucleo acting as controller: WHO_AM_I = 0xA5. Capture both on the logic analyser.
7. With the LED replaced by a power resistor or diode string, in open-loop current mode: sweep `LED:CURR` and measure I with a DMM in series. Fit gain/offset.
8. Scope GATE, R_sense and TIA_OUT on a setpoint step and on on/off edges: compare with S2/S3/S4 (ringing? TIA settling?).
9. Fit the real LED: log the photodiode (on − off) against current → linearity curve. Turn on a desk lamp / phone torch near the housing and check that MEAS:POW doesn't move (ambient rejection).
10. Thermal camera at I_max, 15 min: FET and LED temperatures vs S5.
11. Interlock: turn the UV ARM switch off at full power. The LED must be off within 1 ms (scope). Turn it back on: the LED must stay off until a new ENABLE. Unplug J6: the LED must be off.
12. Regulated mode: step the target, measure settling, then drift over 1 h while the LED heats up (an independent sensor in front of the window should read constant).
13. Calibration against a reference UV power meter → `CAL:GAIN`, `CAL:SAVE`.
14. Write the results in `../test/` with dates, instrument settings and photos.
