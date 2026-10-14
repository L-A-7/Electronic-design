# UV bench Rev B: review guide (before ordering)

How to check the board yourself, step by step. Each step says **what to do**, **what you
should see**, and **what happens if it's wrong**. That last part is the real lesson: it tells
you which mistakes are fatal and which are harmless.

Files for the review (regenerate with `tools/kicad-check.sh`; the `review/` PDFs were exported once):

- [`board-1to1.pdf`](../hardware/uv-bench/output/review/board-1to1.pdf): top copper, silkscreen, fab layer and outline.
- [`schematic.pdf`](../hardware/uv-bench/output/review/schematic.pdf).
- [`parts-list.md`](parts-list.md): every part with its pin → net map.

Write your findings in the last column of each table (✔ / ✘ + a note), then we go through them together.

---

## 1. Pinouts against the datasheets

**Why:** KiCad only checks that the schematic and the board agree with *each other*. If a
symbol's pin numbers don't match the real part, ERC and DRC both pass, and the board is still
wrong. Only you, with the datasheet, can catch that.

**How, for each part:**

1. **Open the datasheet's package drawing.** Search "<part number> datasheet" on the maker's
   site: Microchip, Alpha & Omega, ams OSRAM, Bourns. Use the maker's own PDF, not a reseller
   summary.
2. **Check whether the drawing is a top view or a bottom view.** This is the classic trap: a
   bottom view is mirrored.
3. **Find the pin numbers on the board.** In the PCB editor, hover over a pad: the status bar
   shows its number and net. Or double-click a pad: the Properties window shows number and net.
4. **Compare** with the table below. I filled in what the board has (read from the PCB file);
   you fill in what the datasheet says.

| Part | Pad on the board → net | What the datasheet must say | Your check |
|---|---|---|---|
| U1 MCP1700T-3302E/TT (SOT-23) | 1 → GND, 2 → +3V3 (out), 3 → +5V (in) | Pin 1 GND, pin 2 V_OUT, pin 3 V_IN for the "TT" (SOT-23-3) package. Note: other LDOs in SOT-23 often use another order | ✔ 2026-10-13: datasheet (top view) 1 GND, 2 V_OUT, 3 V_IN |
| Q1 AO3400A (SOT-23) | 1 → GATE, 2 → I_MON (source), 3 → LED_K (drain) | 1 = G, 2 = S, 3 = D | ✔ 2026-10-13: datasheet (top view) 1 G, 2 S, 3 D |
| D1 SFH 2401 | pad 1 (the larger pad, nearer the bottom edge) → +3V3 = **cathode**; pad 2 → PD = anode | Find the cathode mark on the drawing (a notch, a bevelled corner, or a longer lead), then check that it is the lead landing on the *larger* pad of the KiCad footprint. Open the footprint (PCB editor → select D1 → E → Edit footprint) to see the pad shapes | ✔ 2026-10-13: footprint pad 1 (large) = K; SFH 2401 datasheet: large pad = K, same solder pads as the BPW 34 S |
| D2 green LED 0805 | pad 1 → GND = **cathode**, pad 2 → anode | The cathode mark on the part (green line, or a "T" on the underside) goes on pad 1. The silkscreen shows a mark on that side | |
| SW1 PEC09 encoder | A, C, B in a row on the right (C in the middle → GND); S1 → BTN, S2 → GND on the left | Drawing "PC board layout": A–C–B on one side, the 2 switch pins on the other. Also check which way the shaft points (here: to the right, off the board edge) | ✔ 2026-10-13: A–C–B order, C in the middle, switch row opposite; no mounting tabs (footprint has none either) |
| J1 JST-PH 4 | 1 → GND (square pad, left), 2 → +5V, 3 → SDA, 4 → SCL | Same numbering as the main board's connector, and the cable must be "straight": pin 1 to pin 1 | |

**What happens if it's wrong:**

- **U1 reversed:** 5 V goes into the regulator's output. It and probably the MCU die. **Fatal.**
- **Q1 wrong:** the LED never turns on, or turns on fully and can't be controlled. R1 still
  limits the current, so nothing burns, but the board doesn't work.
- **D1 reversed:** the photodiode becomes forward-biased. The ADC sees a constant ~2.7 V
  whatever the light. Nothing burns, but the regulation is impossible. You could fix it by
  turning the part around.
- **D2 reversed:** the LED just stays dark. Harmless.
- **Encoder A and B swapped:** the knob turns "the wrong way". Fixed in one line of firmware.
- **J1 pin 1 at the wrong end:** 5 V lands on the main board's SDA. **Fatal for the main board's pin.**

---

## 2. Print the board 1:1 and lay the parts on it

> **Deferred (2026-10-13):** no parts and no printer yet. Do it before ordering the board.

**Why:** footprints come from a library, and a wrong variant (vertical vs horizontal, another
pitch) passes every check. Paper costs nothing; a wrong board costs a week.

**How:**

1. **Print [`board-1to1.pdf`](../hardware/uv-bench/output/review/board-1to1.pdf)** with the
   printer scale set to **100 % / "actual size"**, never "fit to page".
   - Alternatively from KiCad: PCB editor → File → Print, layers F.Cu + F.Silkscreen + F.Fab +
     Edge.Cuts, "Approximate scale" = 1.
2. **Measure the outline with a ruler: 58 × 32 mm.** If it's 57 or 59, your printer scaled it:
   fix the setting and reprint.
3. **Glue the print onto a piece of cardboard.** For the through-hole parts (J1, SW1), pierce
   the pad centres with a needle and push the legs through.
4. **Lay every real part on its footprint:**

| Part | What to look at | Your check |
|---|---|---|
| J1 JST-PH | The 4 legs go through the 4 holes; the latch side faces the right way for your cable | |
| SW1 PEC09 | The 5 legs go through; the body sits on the board and the shaft sticks out past the right edge | |
| R1 2512 | The resistor's metal ends cover the two pads | |
| D1 SFH 2401 | Both leads land on the pads, the sensitive area faces up | |
| U2 TSSOP-20 | The leads land on the pads (0.65 mm pitch; use a magnifier) | |
| J3 STDC14 header | Its 14 pins land on the pads (FTSH-107-01-L-DV-K, changed 2026-10-14) | |
| 0805 parts | Pick one resistor: both ends on their pads, with ~0.5 mm of pad visible beyond each end, which is where the soldering iron goes | |

**If something doesn't fit,** tell me the part and what you see. Changing a footprint is a
5-minute fix now.

---

## 3. Mechanics

**Why:** the board is the frame of the lamp head. The LED, the photodiode and the knob must
end up where the housing expects them.

**How:**

1. **Measure the LED star** with calipers: its diameter (nominal 20 mm, hole Ø 22) and its
   thickness. Hold it in the hole of the paper print.
2. **Standoff height.** Measure the star's thickness plus the LED's height above it.
   - Goal: the top of the PCB is level with, or just below, the LED's top face.
   - Note the height here: **____ mm**. That's the standoff length to buy (M3, female–female).
3. **Pins under the board.** Through-hole legs (J1, SW1, J2 wires) stick out ~1.5 mm under the
   board. Either trim them flush after soldering, or make sure the standoffs keep them clear of
   the aluminium plate. A leg touching the plate would short it to whatever the plate touches.
4. **Reflector:**
   - Does its base sit on the star and fit through the hole?
   - The photodiode D1 is **on the right side of the hole, 14.4 mm from its centre**, towards
     the MCU. The reflector's side port (the hole you will drill) must face D1. Mark that
     direction on the reflector.
   - The **light budget** of Rev B needs a bigger port than Rev A: about 2–3 mm (see Block 5 of
     [`rev-b-simple.md`](rev-b-simple.md)). Start small and enlarge: you can't make a hole smaller.
5. **Knob:**
   - The shaft exits at the right edge, at mid-height of the board.
   - Check that a 12–15 mm knob fits your shaft (D-shaped flat or knurled, and its diameter)
     before buying the knob.

| Item | Measured / decided | Your check |
|---|---|---|
| Star diameter / thickness | | |
| Standoff height | | |
| Reflector base vs hole | | |
| Side port direction marked | | |
| Knob fits the shaft | | |

---

## 4. Look at the board in 3D

**How:** open the PCB editor and press **Alt+3**. Rotate with the mouse and look at the top,
the bottom, and each edge.

| What | Why | Your check |
|---|---|---|
| Every part has a 3D body | A missing body is fine for manufacturing, but you can't see collisions. **J1 has none** in KiCad's library (the outline is still correct) | |
| Pin-1 marks match | For U2, U1, Q1 the dot or bevel of the 3D model sits on pad 1 | |
| Nothing overlaps | Especially the knob's body vs the J1 connector above it and the D2 LED below it | |
| The underside is flat | Only THT legs (see 3.3) | |

**Then export the board for FreeCAD,** to design the housing: File → Export → STEP.

---

## 5. Check the pin functions in CubeMX (30 min)

**Why:** each MCU pin can only do certain jobs (*alternate functions*). The design assumes
these; CubeMX confirms they really exist on this exact chip and that two don't clash. The
project you save at the end is the firmware skeleton (milestone M2), so the settings below are
the real ones, not just a test.

### 5.1 Create the project

1. STM32CubeIDE → File → New → STM32 Project. In the *MCU/MPU Selector*, type
   **STM32C031F6P6**, select it, Next.
2. Name `uv-bench-fw`, C, Executable, STM32Cube. Finish. The `.ioc` file opens on the
   *Pinout & Configuration* tab.

### 5.2 First look: the shared pins

On a 20-pin package, ST bonds **several pads of the chip to one pin**. In the pinout view
these pins show stacked names (e.g. `PB7 / PB8`). Hover over pins **1, 15 and 20** and note
every name they carry.

- Why it matters: the other ports on the same pin are *physically connected* to ours. They
  must stay unconfigured (analog/input, the reset state), never outputs, or two drivers fight
  on one pin.
- Found 2026-10-14 (from the function lists CubeMX offers on each pin):
  - pin 1 = PB7 + **PB8** (I2C1_SCL and RTC_REFIN appear next to I2C1_SDA)
  - pin 15 = PA8 + **PB0, PB1** (TIM1_CH2N/CH3N, TIM3_CH3/CH4); the datasheet pinout table gives the full list (PB2 too?)
  - pin 20 = PB6 + **PB3, PB4, PB5** (SPI1_SCK/MISO/MOSI, TIM1_CH2/CH3, TIM3_CH1/CH2)
  - Rule for the firmware: never configure the extra ports (PB0–PB5, PB8). They stay in their reset state
    (analog, no driver), so only our pad drives each pin.

### 5.3 Assign the pins

Click a pin in the chip drawing, pick the function from the list, then set the peripheral in
the left column (*Categories*).

| Pin (number) | Click → choose | Then, in the left column | Your check |
|---|---|---|---|
| PA0 (7) | ADC1_IN0 | Analog → ADC1: tick IN0 and IN1 | |
| PA1 (8) | ADC1_IN1 | ADC1 → Parameter Settings: Resolution 12 bits, *Scan Conversion Mode* (sequencer) with 2 ranks: rank 1 = IN0 (PD), rank 2 = IN1 (I_MON) | |
| PA2 (9), PA3 (10) | USART2_TX, USART2_RX | Connectivity → USART2: Mode **Asynchronous**, 115200 baud, 8N1. Check that TX lands on **PA2**: CubeMX can also offer PA14, which is SWCLK. Added 2026-10-14 with the 14-pin debug header | |
| PA4 (11) | GPIO_Output | System Core → GPIO → PA4: push-pull, no pull, *Output level* **High** (power-up mode = I2C = green LED on). User label `MODE_LED` | |
| PA5 (12) | GPIO_EXTI5 | GPIO → PA5: *External interrupt, falling edge*, **Pull-up**. Label `BTN`. System Core → NVIC: enable *EXTI line 4 to 15* | |
| PA6 (13), PA7 (14) | TIM3_CH1, TIM3_CH2 | Timers → TIM3: *Combined Channels* = **Encoder Mode**. Parameters: Encoder Mode *TI1 and TI2*, Counter Period 65535, both *Input Filter* = 10. In GPIO → PA6/PA7: **Pull-up** | |
| PA8 (15) | TIM1_CH1 | Timers → TIM1: Channel1 = *PWM Generation CH1*. Prescaler 0, Counter Period **2399**, Pulse 0 | |
| PB6 (20), PB7 (1) | I2C1_SCL, I2C1_SDA | Connectivity → I2C1: mode I2C. Parameters: *Primary slave address* **0x2A**, 7-bit. Enable the I2C1 event interrupt in its NVIC tab | |
| PA13 (18), PA14 (19) | (automatic) | System Core → SYS: Debug = **Serial Wire**. The two pins turn green | |
| PF2 (6) | NRST | Nothing to do: reset is its default | |

Why these numbers:
- **TIM1 period 2399:** the timer clock is 48 MHz (next step), and 48 MHz / 2400 = 20 kHz,
  the PWM frequency of block 4. That gives 2400 duty steps, about 11 bits of resolution
  before the RC filter.
- **Encoder filter 10:** the timer ignores any pulse shorter than about 3 µs (8 samples at
  3 MHz). That removes electrical spikes, not contact bounce, which lasts milliseconds. Bounce
  is harmless anyway: in encoder mode, a bouncing contact makes the counter go +1, −1, +1…
  and it settles on the right value. So the rotation needs no debouncing; only the push
  button does (in firmware).
- **Pull-ups on PA5, PA6, PA7:** the encoder and button only connect to GND (pin C and S2).
  The internal ~40 kΩ pull-ups give the "high" state. That's why the board has no resistors
  there.
- **Address 0x2A:** CubeMX takes the 7-bit address. In the generated code (`MX_I2C1_Init`)
  you will see `OwnAddress1 = 84`: that's 0x54 = 0x2A shifted left by one bit, because the
  hardware register holds the address next to the read/write bit. Both are correct.

> **Open (2026-10-14): six settings not yet saved in `uv-bench-fw.ioc`.** The pins are all
> green in the window, but the file on disk (and the generated `main.c`) still has:
> HSI divider /4 (12 MHz instead of 48), TIM3 encoder mode TI1 (not TI1 and TI2), PA5 rising
> edge without pull-up, PA4 starting low, PA6/PA7 without pull-up (TIM3 → GPIO Settings),
> NVIC: EXTI 4–15 and I2C1 not enabled. Plus a seventh, added since: USART2 on PA2/PA3 (row
> above). Fix in CubeIDE, **Ctrl+S → "generate code?" Yes**,
> then check that `Core/Src/main.c` has a new date.

### 5.4 Clock

*Clock Configuration* tab: source **HSI 48 MHz**, SYSCLK **48 MHz**, HCLK and APB **48 MHz**.
If a box turns red, the value isn't allowed: tell me which one.

### 5.5 Result

1. **Pinout view:** the 14 pins we use are green. Nothing orange (half-configured) or red
   (conflict). Unused pins stay grey.
2. **Left column:** no warning triangle next to ADC1, TIM1, TIM3, I2C1, USART2, SYS.
3. **Project → Generate Code** (or save the `.ioc`, which asks). It must finish without errors.
4. Take a screenshot of the pinout view for the record.

**If a function isn't offered on a pin,** tell me which one. Moving a signal to another pin is
easy now; after ordering it means cutting tracks.

---

## 6. Simulate the LED driver (KiCad simulator, ngspice)

**Why:** this checks the numbers of Block 4 before trusting them: the filter ripple, the
response time and the maximum current.

**How:** I will prepare a small simulation schematic (`sim/led-driver.kicad_sch`) with:

- a PWM source;
- R2/C7/R3;
- a MOSFET model;
- R1;
- the LED as a diode with V_f ≈ 3.7 V.

You open it and run **Inspect → Simulator → Run**. Expected:

| Quantity | Expected | Your result |
|---|---|---|
| Gate ripple at 50 % duty | ≤ 5 mV peak-to-peak | |
| LED current at 50 % duty | ~90 mA (depends on the MOSFET model) | |
| Settling after a duty step 30 → 70 % | ~40 ms to 98 % (4 τ, τ ≈ 10 ms) | |
| LED current at 100 % duty | (5 − V_f) / 3.9 Ω ≈ 0.33 A | |

---

## 7. Stock and exact part numbers

**How:** search each part on LCSC, Mouser or DigiKey. Check that it is **in stock** and that
the **package** matches.

Done 2026-10-14 for DigiKey France: [`bom-digikey.md`](bom-digikey.md), with every part number checked.

| Part | What to order | Note | Your check |
|---|---|---|---|
| U1 | MCP1700T-3302E/TT | "TT" = SOT-23-3. Not the "TO" (TO-92) or "MB" (SOT-89) version | |
| U2 | STM32C031F6P6 | "P" = TSSOP-20 | |
| Q1 | AO3400A | Very common; many second sources | |
| D1 | SFH 2401 (SMD, blue-enhanced) | Successor of the discontinued BPW 34 BS. **Not** the plain BPW 34 (clear epoxy, blind at 365 nm) | ✔ 2026-10-13: active part, same pads, ~15 % at 365 nm (as the BPW 34 BS) |
| D2 | Any green LED in 0805 | Choose one rated at ~2 mA or lower ("high efficiency") | |
| SW1 | Bourns PEC09-2xxxF-S…: "S" = with switch | The digits give the shaft length and detents: pick one, and a matching knob | |
| R1 | 3.9 Ω, 2512, **1 W** | Not 0.5 W: check the power rating | |
| R2, R5 / R3, R4 | 1 kΩ / 100 kΩ, 0805, 1 % | Buy 10 of each | |
| C1, C2, C3, C7 | 10 µF, 0805, **X5R or X7R, ≥ 10 V** | At 5 V a 10 µF 0805 keeps only ~50 % of its value (DC bias). That's still enough here | |
| C4, C5, C6 | 100 nF, 0805, X7R, ≥ 16 V | | |
| J1 | JST B4B-PH-K-S + housing PHR-4 + crimps SPH-002T, or a ready-made PH 4-pin cable | Crimping PH needs the right tool; ready-made cables avoid it | |
| J3 | STDC14: 2×7, 1.27 mm SMD, keyed, Samtec **FTSH-107-01-L-DV-K** | Plugs straight into the STLINK-V3MINIE's 14-pin cable. Not "-A" (alignment pins need holes) | ✔ |
| Off board | LED star, ARM toggle switch, M3 standoffs, aluminium plate, knob | | |

---

## When everything is ✔

1. Run the full check one last time: `tools/kicad-check.sh projects/01-uv-bench/hardware/uv-bench/uv-bench`.
2. Upload `output/gerbers.zip` to JLCPCB: 2 layers, 1.6 mm, HASL, any colour.
3. Order the parts, and a few spares of the 0805 parts.
