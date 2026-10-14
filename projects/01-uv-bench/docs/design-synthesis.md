# UV bench, Rev A: design synthesis

> **Rev A document, kept for reference (2026-10-13).** The board was simplified to Rev B:
> [`rev-b-simple.md`](rev-b-simple.md). The lamp/optics advice (§1) and the mechanics (option B) still apply.

One-page view of project 01 as it will be drawn in KiCad: what the board does, how it is built,
and **every component chosen**. The detailed reasoning is in the other docs (linked in each
section). Status: 2026-10-11, ready for schematic capture. **Layout option B:** one PCB, LED star in a cut-out.

| | |
|---|---|
| Function | 365 nm UV source for fluorescence excitation. **You ask for a power, the board holds it** (photodiode feedback) |
| Control | I2C target (0x2A) on a 4-wire cable: GND, +5 V, SDA, SCL. Same commands as text over a UART header from a PC |
| Brain | **STM32C031F6P6**, TSSOP-20 (Cortex-M0+ 48 MHz, 32 KB flash, 12 KB RAM, no crystal) |
| LED | 365 nm 3535 LED on a 20 mm star (**LG, harvested from a Convoy S2 365 nm flashlight**; Nichia as an upgrade), ~300 mA ≈ 1.1 W electrical |
| Optics | 20 mm aluminium **reflector + ZWB2 filter window** (flashlight parts) |
| Feedback | Osram **BPW 34 BS** silicon photodiode + TIA on the board, at the edge of the cut-out |
| Board | **One PCB**, 70 × 55 mm, 2 layers, with a Ø 22 mm cut-out for the LED star. One KiCad project: [`hardware/uv-bench`](../hardware/README.md) |

Contract with the main board: [`interface-spec.md`](interface-spec.md) v1.3. PC text protocol:
[`host-protocol.md`](host-protocol.md). Tests: [`verification-plan.md`](verification-plan.md).

---

## 1. Consumer UV lamp or separate LED? → **Flashlight optics, our own driver**

The "lens" in a good UV flashlight is actually **an aluminium reflector plus a flat ZWB2 filter
glass**. Both are exactly what we need, and both are sold as cheap spare parts.

| What matters at 365 nm | Why |
|---|---|
| **Aluminium reflector**, not a plastic lens | Aluminium reflects ~90 % at 365 nm. Standard PMMA and polycarbonate lenses absorb part of the 365 nm light and turn yellow under it |
| **ZWB2 window** (Wood's glass, like Schott UG1) | It blocks the LED's weak violet–blue tail (400–450 nm). That tail would land in the fluorescence band and show up as background. It also stops visible room light from entering the head |
| **A real 365 nm LED** (Nichia, LG, Seoul Viosys) | Many cheap "UV" lamps are really 395 nm, use 5 mm LEDs and have no filter |

**Recommendation (cheapest good path, prices checked 2026-10-11):**

A good flashlight is the **cheapest way to get all three optical parts**: LED on a 20 mm star,
aluminium reflector and ZWB2 window. Bought separately, a Nichia 365 nm LED alone costs
~€19 bare or ~€37 on a board (Ledrise/Lumitronix).

| Option | ~Price | LED | ZWB2 | Use |
|---|---|---|---|---|
| **Convoy S2 365 nm, LG LED, with ZWB2** (the "S2", not "S2+") | **€15–25** (seen at 55 zł ≈ €13 in a Feb 2026 deal at convoylight.com) | LG 365 nm, 3535 on a 20 mm star | Included | **First choice.** More output and a wider beam than the Nichia version. Driver: 3× or 5× 7135 (1–1.75 A); we drive it at 0.3 A ourselves |
| Convoy S2+ 365 nm, Nichia | €20–30 | Nichia NVSU233A/B | Often **not** included: check, or add a ZWB2 lens (~€3–5) | Tighter, more concentrated beam. Pricier LED |
| Alonefire SV003 "10 W" | €15–25 | Unknown 4-die UV LED | Black filter | Fine as a **cheap test light only**: overheating reports, integrated optics, hard to harvest |
| €5 keychain / 5 mm-LED "UV" lights | €3–8 | Usually 395 nm | No | **Avoid** for this project |

**Plan:**
1. **Buy one Convoy S2 LG 365 nm with ZWB2** (+ an 18650 cell if you want to use it as a torch).
   - Use it intact for the M1 photodiode tests.
   - When the PCB arrives, **harvest it**: unscrew the head, desolder the LED star from the driver, and keep the reflector and ZWB2 lens. Star + reflector + window then go into the bench housing. The leftover body is still a torch host.
2. Optional: a second unit (~€15–20) as a spare LED or an intact reference.
3. Bench parts to buy separately:

   | Part | Choice | ~Price |
   |---|---|---|
   | Thermal | Aluminium plate 3 mm (~60 × 80 mm) as base/heatsink, M3 standoffs + screws, thermal paste | €5–8 |
   | NTC | 10 kΩ wired NTC, B = 3435 (e.g. Murata NXFT15XH103FA2B), glued on the star next to the LED | €1 |
   | PTFE | Small sheet or plumber's tape (scatter disc in the photodiode cap) | €2 |

*Upgrade later if needed:* a Nichia NVSU233B (~€19 bare) or Seoul Viosys CUN6GB1A (367 nm) re-flowed on the same star.

**Mechanical layout: option B, "one board, LED star in a cut-out"** (decided 2026-10-11, D6):

```
                      ZWB2 window (in the housing lid)
        ═════════════════════════════════════════         black housing
                  ╲      reflector      ╱
   black cap  ┌──┐ ╲                   ╱
   PTFE inside│▓ │◄─╲─ 1 mm side port ╱
   PCB  ══════╪[PD]╪═╲══ ┌───────┐ ══╱══════╪═══════════╪════  PCB on 4 standoffs
              TIA     ╲  │  LED  │  ╱   Ø 22 mm cut-out
   standoff ▐          [ 20 mm star ]                   ▐ standoff
   ════════════════════════════════════════════════════════  aluminium plate 3 mm (heatsink, base)
```

- **All the electronics are on one PCB**, photodiode included. The **LED star sits in a Ø 22 mm
  hole** in that PCB, screwed directly onto the aluminium plate with thermal paste. The PCB
  stands on 4 M3 standoffs on the same plate, so the LED and photodiode positions are fixed
  by one rigid part.
- **Heat:** the LED's 0.7 W goes into the plate. An air gap separates the star from the PCB,
  so the photodiode and the analogue parts stay at room temperature. That matters, because
  drift of the photodiode is the one thing the regulation loop can't correct.
- **Wiring:** two short wires from the star to solder pads at the edge of the hole (LED+, LED−),
  and two for the NTC glued on the star. A dead LED means unscrewing the star and replacing it.
- **Light pickup:** the [scatter-spot + dark-chamber idea](photodiode-selection.md) becomes a
  **1 mm side port drilled in the reflector wall near its base**:
  - The photodiode sits on the PCB about 13–15 mm from the LED axis, under a small black 3D-printed cap. A PTFE disc inside the cap scatters the light from the port down onto the photodiode.
  - Room light would have to pass the ZWB2 window and then find the port, so very little gets in.
  - Light budget: about 0.7 mW passes the port. After the PTFE, roughly 5–50 µW reaches the photodiode, giving 0.5–5 µA. M1 confirms this.
- The cap and the housing are designed later in FreeCAD from the PCB STEP export. The PCB only
  fixes the photodiode position and the cut-out.

## 2. Block diagram (main board)

```
 J1 JST-PH 4 ──+5V──► U1 ideal diode ─┐                     ┌─► FB1 ─► 5V_LED ─(C1 220µF)─► J4 LED+ ─► LED (star) ─► J4 LED− 
   (GND,5V,SDA,SCL)                    ├─► F1 ─► 5V_SYS ─(D1 TVS)                                                   │ drain
 J2 FTDI 6 ──+5V──► U2 ideal diode ───┘                     └─► U3 LDO ─► 3V3 (MCU, logic, TIA)                    Q1 NDT3055L
                                                                                                                    │ source = ISENSE
 SDA/SCL ─► U4 ESD ─► MCU PB7/PB6 (I2C1 target)                                                                  R10 0.33 Ω ─► GND
 J2 RX/TX ─────────► MCU PA3/PA2 (USART2)                                                                           ▲
                                                                                                                    │
 MCU PA8 (TIM1_CH1 PWM 47 kHz) ─► 2-pole RC + divider ─► SET_F (0…100 mV) ─► U6 switch ─► SET_G ─► U8A op-amp ──R─┘ gate
 MCU PA9 (TIM1_CH2 GATE) ──┐                                                    ▲ control
 UV ARM switch (J6) ──► ARM_OK ┴─► U7 AND ───────────────────────────────────┘          (switch off or MCU low → LED off)
                         └──► MCU PA7
 ISENSE ─► U8B ×25 ─► I_MON ─► PA1        drain ÷2 ─► V_HEAD ─► PA5        5V_LED ÷2 ─► V_IN ─► PA6
 J5 NTC ─► 10 k divider ─► T_LED ─► PA4   BPW 34 BS ─► TIA (U9) ─► RC ─► PA0
```

**How regulation works:**
- TIM1 makes the PWM setpoint. A short dark gap (~50 µs every 10 ms) on GATE turns the LED off briefly.
- TIM1 also triggers the ADC, and DMA stores PD(on) and PD(off). Their difference is the LED's light only.
- A 1 kHz PI loop moves the PWM until that difference matches SETPOINT_POWER. Details are in the [README §3–4](../README.md).

## 3. Component list (Rev A)

> **Generated design (2026-10-12):** the schematic and PCB are now generated from [`../hardware/gen/design.py`](../hardware/README.md). The reference designators below were the planning names; the **actual** references, values and nets are in [`parts-list.md`](parts-list.md), and the reasoning for every value is in [`design-notes.md`](design-notes.md). The part choices are the same.

KiCad symbol/footprint names are from the stock KiCad 10 libraries (all checked in 10.0.7).
Prices are indicative. **LCSC numbers:** pick them in KiCad with the JLCPCB-tools plugin (§6),
choosing "Basic" parts where possible (cheaper assembly).

### 3.1 Power and connectors

| Ref | Part | Footprint | Why this part |
|---|---|---|---|
| J1 | JST **B4B-PH-K-S** (GND, +5V, SDA, SCL) | `Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | Keyed, locking, spec v1.3. Not Qwiic on purpose (Qwiic = 3.3 V) |
| J2 | 1×6 pin header 2.54 mm, FTDI pinout | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` | PC console with any 3.3 V USB-serial cable |
| J3 | 2×5 1.27 mm SWD header | `Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD` | ST-LINK V3MINIE / Nucleo ST-LINK |
| J4 | 2 solder-wire pads, LED+ / LED− | `Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm` | At the edge of the cut-out. Short AWG24 wires to the star (0.3 A). Mark + on the silkscreen |
| J5 | 2 solder-wire pads, NTC | `Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm` | NTC wires from the star |
| J6 | JST B2B-PH-K-S → panel **UV ARM switch** | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | Manual **latching** switch on the housing (§3.5). Unplugged = off |
| U1, U2 | TI **LM66100DCK** ideal diode | SC-70-6 | Diode-OR of the two 5 V inputs with a ~25 mV drop instead of ~350 mV for a Schottky. That's **headroom we need** (§4) |
| F1 | PTC fuse 1206, 0.75 A hold (or 0 Ω for test) | `Fuse:Fuse_1206_3216Metric` | Protects the cable / main board |
| D1 | **SMAJ5.0A** TVS | `Diode_SMD:D_SMA` | Hot-plug and ESD surges on 5 V |
| FB1 | Ferrite bead 0805, ≥ 1.5 A, DCR < 0.1 Ω | `Inductor_SMD:L_0805_2012Metric` | With C1, keeps LED current steps local. They don't go back down the cable into I2C |
| C1 | 220 µF 10 V low-ESR (polymer or electrolytic) | SMD can 6.3 mm | Bulk reservoir for the LED (spec §2) |
| C2 | 10 µF 0805 X5R | 0805 | Local decoupling 5V_SYS |
| U3 | TI **TLV75533PDBV** LDO 3.3 V 500 mA | SOT-23-5 | The 3.3 V is also the ADC reference: ±1 %, low noise. VREFINT corrects the rest |
| C3, C4 | 1 µF 0603 X7R | 0603 | LDO in/out (datasheet) |
| U4 | ST **USBLC6-2SC6** | SOT-23-6 | ESD on SDA/SCL (the cable is unplugged and handled) |
| R1, R2 | 4.7 kΩ, **DNP** | 0603 | I2C pull-ups for standalone tests only (normally on the main board) |

### 3.2 MCU

| Ref | Part | Footprint | Notes |
|---|---|---|---|
| U5 | **STM32C031F6P6** | `Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm` | Symbol `MCU_ST_STM32C0:STM32C031F6Px`. 0.65 mm pitch: drag-solder with flux, then check for bridges with a magnifier |
| C5, C6 | 100 nF + 4.7 µF | 0603 / 0805 | On VDD/VDDA (pin 4), as close as possible |
| C7 | 100 nF | 0603 | NRST (PF2, pin 6) to GND |
| JP1 | Solder jumper 2-pad | `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm` | Address 0x2A (open) / 0x2B (closed). Internal pull-up |
| D2, R3 | Green LED 0603 + 1 kΩ | 0603 | Status (blink codes) |

### 3.3 LED driver (linear current sink)

| Ref | Part | Value | Why |
|---|---|---|---|
| R4, C8 | PWM filter, 1st pole | 10 kΩ, 100 nF | 160 Hz |
| R5, R6, C9 | 2nd pole **and divider** | 22 kΩ, 1 kΩ, 1 µF (across R6) | 3.3 V × 1/(10+22+1) = **100 mV full scale → 303 mA max**. The hardware current limit is set by the components (spec §5). Residual PWM ripple ≪ 1 µV |
| U6 | TI **SN74LVC1G66DBV** analog switch | SOT-23-5 | Disconnects the setpoint → LED off **without disturbing the filter capacitors**, so the LED comes back to the same current right after a dark gap |
| R7 | 100 kΩ | 0603 | SET_G pull-down (switch open → 0 mA) |
| U7 | TI **SN74LVC1G08DBV** AND gate | SOT-23-5 | GATE · ARM_OK. **Hardware enable**: with the ARM switch off, the LED can't light, whatever the firmware does |
| R8, R9 | 10 kΩ ×2 | 0603 | Pull-downs on GATE and on U7 output: everything is OFF by default |
| U8 | TI **OPA2388IDGKR** dual, zero-drift, 10 MHz, RRIO | VSSOP-8 | A: current loop. B: current monitor. Zero drift (µV offset on a 100 mV signal) **and** fast enough to settle in a few µs after each dark gap. Stock symbol: use `OPA2333xxDGK` (same standard dual pinout) and change Value. Fallback: OPA2333 (slower, then lengthen the dark gap to 200 µs) |
| Q1 | onsemi **NDT3055L** N-MOSFET, logic level | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | Dissipates ≤ 0.5 W in linear mode. SOT-223 + 2 cm² copper is enough. Moderate Ciss, so the loop is easy to stabilise |
| R10 | **0.33 Ω 1 % 1206**, 0.25 W | 1206 | 0.1 V at 300 mA. **Kelvin connection** to U8 |
| R11, C10 | 100 Ω gate resistor + loop compensation (1 kΩ / 10 nF starting values) | 0603 | Values fixed by **simulation S2** in KiCad |
| R12 | 100 kΩ gate pull-down | 0603 | Q1 off if U8 is unpowered |
| R13, R14 | 24 kΩ, 1 kΩ (U8B gain 25) | 0603 1 % | I_MON = 2.5 V at 300 mA → PA1 |
| R15–R18, C11, C12 | 100 kΩ / 100 kΩ ×2, 10 nF ×2 | 0603 | V_HEAD (drain ÷ 2) and V_IN (5V_LED ÷ 2) |
| R19, C13 | 10 kΩ 0.1 %, 100 nF | 0603 | NTC divider → T_LED |
| R20, C14 | 100 Ω, 1 nF | 0603 | Anti-alias / ADC kick-back filter on PD input |
| TP1–TP12 | Test pads | `TestPoint:TestPoint_Pad_D1.5mm` | 5V_SYS, 5V_LED, 3V3, GND×2, SET_F, SET_G, GATE, ISENSE, DRAIN, PD_ADC, SDA/SCL |

### 3.4 Photodiode + TIA (on the main board, at the edge of the cut-out)

| Ref | Part | Value / footprint | Why |
|---|---|---|---|
| D3 | Osram **BPW 34 BS** (blue-enhanced, 350–1100 nm) | `OptoDevice:Osram_BPW34S-SMD`, symbol `Sensor_Optical:BPW34-SMD` | Cheap, specified down to 350 nm, 7 mm² ([selection](photodiode-selection.md)) |
| D4 | **DNP** 2-pad THT, 2.54 mm, in parallel with D3 | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | Alternative detector for M1: a **385–395 nm LED used as a photodiode** (visible-blind), or a GUVA-S12SD on wires |
| U9 | TI **TLV9061IDBVR** | SOT-23-5 | 10 MHz CMOS RRIO, pA bias. Doesn't need zero drift, because the on−off subtraction cancels offsets |
| R21, C15 | **Rf 1 MΩ, Cf 2.2 pF C0G** | 0603 | 1 µA → 1 V, bandwidth ≈ 70 kHz (settles in < 10 µs). Rf is the knob if the light is too strong or too weak |
| R22, R23, C16 | 330 kΩ / 10 kΩ, 100 nF | 0603 | **+100 mV bias** on the op-amp + input: the dark output sits at 0.1 V instead of clipping at the 0 V rail, so (on − off) stays linear |
| C17 | 100 nF | 0603 | Decoupling, right at U9 |

**Layout rule:** D3, U9, R21 and C15 form a tight cluster. The TIA − input is a 1 MΩ node: keep it
a few mm long, with a GND guard around it, and keep 5V_LED / DRAIN traces away from it.

### 3.5 UV ARM switch (replaces the lid interlock, decided 2026-10-12)

A **manual, latching switch** on the housing, wired to J6, replaces the automatic lid switch:

| Part | Choice | Why |
|---|---|---|
| SW1 | Miniature **toggle switch**, SPST or SPDT, panel mount (6 mm bushing, "MTS-101/102" type, ~€1). Or a **key switch** if other people use the bench | It stays where you put it, and you can see and feel its state. Up = ARMED |
| R24, C18 | 10 kΩ pull-down + 100 nF on ARM_OK | A broken wire or unplugged J6 reads as OFF (fail-safe). The capacitor filters contact bounce and noise picked up by the wire |

**How it behaves:**
- **OFF:** the AND gate holds the LED off in hardware, whatever the firmware does. The MCU sees ARM_OK low, clears ENABLE and reports `STATUS.ARM_OFF`.
- **ON:** nothing lights by itself. The LED only comes on after a new ENABLE command (I2C or UART). So **switching it back on never restarts the LED**: no surprise exposure.
- It is wired like the old lid switch (3V3 → switch → ARM_OK), so a lid microswitch can be put in series with it later.

**Not a momentary push button.** A momentary button only conducts while pressed, so it can't hold "armed" in hardware. A
push button is good for a *local ON/OFF command* read by the firmware. The spare pin PC15 could take one later,
on top of the ARM switch.

**Cost:** about €15–20 of parts per board (MCU ~€1, op-amps ~€4), plus ~€15–25 for the Convoy S2 (LED star + reflector + ZWB2) and ~€10 for the plate, NTC and PTFE.

## 4. Power and headroom (worst case)

| | V |
|---|---|
| USB 5 V, worst case (low end of the USB spec) | 4.75 |
| Cable + LM66100 + PTC + bead (0.3 A) | −0.15 |
| LED Vf at 300 mA, cold (365 nm 3535 LEDs typ. ~3.6–3.9, **measure at M1**) | −3.90 |
| Rsense | −0.10 |
| **Left for the MOSFET** (it needs ~0.1–0.2 V) | **+0.6** |

This works with a margin of ~0.4 V. Firmware reports MEAS_V_HEADROOM and sets SATURATED if it
gets too low. D5 (5 → 7 V boost) stays **not needed unless M1 says otherwise**.

Heat: MOSFET ≤ 0.5 W (SOT-223 on copper, +30 K). Place it **away from the photodiode corner**. LED ~0.7 W, into the plate through the cut-out, not into the PCB.

## 5. MCU pin map (from the KiCad symbol `STM32C031F_4-6_Px`, TSSOP-20)

All 16 signals fit, with one spare pad. The timer, ADC, I2C and UART pins are the same as on
the Nucleo-C031C6, so the M1 firmware ports almost unchanged.

| Pin | Port | Function | Net | Notes |
|---|---|---|---|---|
| 4 / 5 | VDD / VSS | power | 3V3 / GND | VDD is also VDDA (ADC reference) |
| 6 | PF2 | NRST | NRST | 100 nF to GND, to SWD pin 10 |
| 7 | PA0 | ADC1_IN0 | PD_ADC | Photodiode (on/off samples) |
| 8 | PA1 | ADC1_IN1 | I_MON | LED current |
| 9 | PA2 | USART2_TX | UART_TX | → J2 pin 5. Same USART as the Nucleo-C031C6 virtual COM port (check in the Nucleo user manual) |
| 10 | PA3 | USART2_RX | UART_RX | ← J2 pin 4 |
| 11 | PA4 | ADC1_IN4 | T_LED | NTC |
| 12 | PA5 | ADC1_IN5 | V_HEAD | MOSFET drain ÷ 2 |
| 13 | PA6 | ADC1_IN6 | V_IN | 5V_LED ÷ 2 |
| 14 | PA7 | GPIO in + EXTI | ARM_OK | UV ARM switch state (the firmware sees it too) |
| 15 | PA8 | **TIM1_CH1** | SET_PWM | 48 MHz / 1024 = 46.9 kHz, 10 bit |
| 16 | **PA9**/PA11 | **TIM1_CH2** | GATE | Shared pad: select PA9 with the SYSCFG remap bit (CubeMX does it). Dark gaps; 10 k pull-down |
| 17 | PA10/**PA12** | GPIO out | STATUS_LED | Shared pad: select PA12 |
| 18 | PA13 | SWDIO | SWDIO | J3 |
| 19 | PA14 | SWCLK (also BOOT0) | SWCLK | J3. Leave it free of extra loads |
| 20 | PB6 | **I2C1_SCL** | SCL | 5 V-tolerant pin, run at 3.3 V |
| 1 | PB7 | **I2C1_SDA** | SDA | |
| 2 | PC14 | GPIO in, pull-up | ADDR_SEL | JP1 to GND → 0x2B |
| 3 | PC15 | (spare) | — | Not connected (no test pad: routing space). Could later take a local ON/OFF push button |

**Verify in CubeMX before layout** (30 min):
- Open a C031F6Px project, assign these pins and check for conflicts, including the PA9/PA11 and PA10/PA12 remaps.
- Check in AN2606 which USART the ROM bootloader uses on the C031, and confirm it isn't the GATE pin.

## 6. KiCad plan: finished PCB in 2 days

The order matters: **schematic → simulate → layout → check → fab files**. Use the tools in **bold**; each one is a skill worth mastering.

**Day 1: schematic + simulation**
1. **Project setup: done.** Open [`hardware/uv-bench`](../hardware/README.md) in KiCad. The JLC rules, net classes, board outline and cut-out are already set.
   Look at them in Board Setup, it's worth knowing where they live.
2. **Hierarchical schematic**, one sheet per §3 block. The 4 sheets already exist (Power, MCU, LED driver, Photodiode and monitors), each with a note listing its parts. This is good KiCad practice: global vs local labels, power symbols.
3. **Assign footprints** with the Footprint Assignment tool (the names are in §3).
4. **ERC** to zero violations.
5. **Simulation in KiCad (ngspice)**. Make a copy of the LED driver sheet with SPICE models: an LED as a diode with Vf ≈ 3.7 V, the MOSFET model, and the TI op-amp model.
   - **S2:** loop stability on a step of SET_G. Tune R11/C10 until there's no overshoot or ringing.
   - **S4:** TIA settling (photodiode C ≈ 70 pF, Rf/Cf).

**Day 2: layout + checks**
1. **Placement first, routing second.**
   - Board outline 70 × 55 mm, Ø 22 mm cut-out and 4× M3 holes (enlarged from 60 × 50 mm: the hand-solder footprints need ~1190 mm²).
   - Connectors on the outer edges, LED/NTC pads at the cut-out edge.
   - The photodiode at the cut-out edge, at the marked position (the side port faces it). Q1 on the opposite side of the board.
   - Q1 + R10 + U8 tightly together. Analog parts (dividers, ADC RC) go on the MCU's PA side. There is no switching regulator to keep away from, by design.
2. **Route.**
   - LED current loop first and wide: 5V_LED → J4 → back → Q1 → R10 → GND.
   - **Kelvin traces** from R10 to U8.
   - Then the MCU, then the rest. A solid **GND pour on both layers**, stitched with vias.
3. **DRC** with schematic parity, then the **3D viewer** (connector orientation, silkscreen).
4. Run `tools/kicad-check.sh` (ERC + DRC + Gerbers + drill + BOM + positions + STEP), which must pass.
5. Export the **JLC BOM + CPL**. Order the boards; M1 tests run while they are in fab.

**Helpers worth installing** (KiCad → Plugin and Content Manager):

| Tool | What it does for you |
|---|---|
| **JLCPCB tools** (Bouni) | Search LCSC parts from inside KiCad, write the LCSC field, generate BOM/CPL for assembly |
| **Interactive HTML BOM** | A clickable page showing where each part goes: very helpful for hand soldering and bring-up |
| **Fabrication Toolkit** | One-click JLC-ready Gerber zip (our `kicad-check.sh` does the same, for scripting) |
| KiCad **simulator** (built in) | S2/S4 before fabrication |
| `kicad-check.sh` + git | Repeatable checks; commit at each milestone so you can always compare revisions |

**Rev A is itself the prototype.** You don't need to wait for M1:
- The design tolerates what M1 might reveal: Rf can be changed, the side-port position is set by the cap and not by the PCB, the headroom is measured on the board, and the alternative detector footprint is there.
- Meanwhile, M1 (the Nucleo-C031C6 + flashlight + photodiode in a box) develops the firmware.

## 7. Open points (none blocks the layout)

| # | Point | When |
|---|---|---|
| D5 | Boost 5 → 7 V: expected **not needed** (§4) | M1 Vf measurement |
| D3 | Photodiode: BPW 34 BS vs 385–395 nm LED-detector | M1 test (the board has both footprints) |
| — | Housing, side-port geometry, PTFE disc | FreeCAD after the PCB STEP export |
| — | Loop compensation values R11/C10 | Simulation S2 (day 1) |
