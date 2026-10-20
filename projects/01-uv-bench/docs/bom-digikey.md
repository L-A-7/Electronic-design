# UV bench Rev B: shopping list (DigiKey France)

One distributor for everything except the UV LED star, the aluminium plate and the PCB itself
(the PCB comes from the board house, e.g. JLCPCB, with the Gerbers from `kicad-check`).

- **Why DigiKey:** I checked it stocks *every* line, including the two brands that are often
  missing elsewhere: Alpha & Omega (Q1) and JST (J1, cable). Amazon sells no exact part
  numbers, only look-alikes.
- **Checked on digikey.fr on 2026-10-14.** Prices are excl. VAT, quantity 1, and will move.
- **Quantities are for 2 boards plus spares.** A spare MCU, regulator and MOSFET cost ~€2.50
  together, and one lifted pad or overheated part otherwise stops the build.
- Upload file: [`bom-digikey.csv`](bom-digikey.csv) (see "How to order" below).

## Board parts

| Ref | Part | Manufacturer part number | Qty | ~€/pc | Why this one |
|---|---|---|---|---|---|
| U2 | MCU | STMicroelectronics **STM32C031F6P6** | 3 | 1.56 | The design's MCU, TSSOP-20 |
| U1 | 3.3 V LDO | Microchip **MCP1702T-3302E/CB** | 3 | ~0.5 | The MCP1700T-3302E/TT was out of stock (2026-10-14, 3 expected on 2026-10-26). The MCP1702 is its big brother: same pinout (1 GND, 2 V_OUT, 3 V_IN), same 1 µF+ ceramic-cap stability, 13.2 V max input instead of 6 V. **Check the pinout table in its datasheet before soldering** (SOT-23A = "CB"). Waiting for the MCP1700 is the other option |
| Q1 | N-MOSFET | Alpha & Omega **AO3400A** | 3 | 0.46 | Pick the **Alpha & Omega** line: DigiKey also lists UMW and GOODWORK copies under the same name |
| D1 + head | Photodiode | ams OSRAM **SFH 2401** | 4 | 1.45 | Successor of the BPW 34 BS, same pads. One on the board, one on the remote sensor head (Rev C), two spares |
| D2 | Green LED 0805 | Kingbright **APT2012SGC** | 5 | 0.18 | 2.2 V typ: with R5 = 1 k it runs at ~1 mA, plenty for an indicator |
| SW1 | Encoder + push | Bourns **PEC09-2220F-S0012** | 2 | 3.69 | See below |
| R1 | 3.9 Ω 1 W 2512 | Vishay **CRCW25123R90FKEG** | 3 | 0.30 | 1 %, 1 W, in stock. The Yageo in the parts list (RC2512FK-073R9L) was out of stock |
| C1 C2 C3 C7 | 10 µF 0805 | Taiyo Yuden **TMK212BBJ106KG-T** (DigiKey 587-2985-1-ND) | 10 | ~0.16 | **25 V** X5R: a higher rating loses less capacitance at 5 V (DC bias). Third choice, after the Samsung CL21A106KAYNNNE (only 2 left, 2026-10-14) and the Murata GRM21BR61E106KA73L (unavailable, 2026-10-20). Other equivalent: TDK C2012X5R1E106K125AB (backordered, 16 weeks, as of 2026-10-20). Any 10 µF / 25 V / X5R or X7R / 0805 fits the footprint |
| C4 C5 C6 C8 | 100 nF 0805 | Samsung **CL21B104KBCNNNC** | 10 | 0.09 | 50 V X7R, the standard decoupling cap |
| R2 R5 R6 R7 | 1 kΩ 0805 1 % | Yageo **RC0805FR-071KL** | 10 | 0.03 at 10 | |
| R8 | 10 kΩ 0805 1 % | Yageo **RC0805FR-0710KL** | 10 | ~0.03 at 10 | Remote photodiode load (Rev C). A first guess: you may re-stuff it after measuring, so 10 is handy |
| R3 R4 | 100 kΩ 0805 1 % | Yageo **RC0805FR-07100KL** | 10 | 0.03 at 10 | |
| J1 | JST PH 4-pin, vertical | JST **B4B-PH-K-S** | 3 | 0.18 | |
| J4 | JST PH 2-pin, vertical | JST **B2B-PH-K-S** | 3 | ~0.15 | Remote photodiode (Rev C) |
| J3 | Debug header STDC14, 2×7 1.27 mm SMD, keyed | Samtec **FTSH-107-01-L-DV-K** | 3 | 2.16 | Plugs straight into the V3MINIE's cable, see "The debug cable". Not the "-A" version (its alignment pins need holes) |

**The encoder code**, decoded from the Bourns datasheet, `PEC09 - 2 2 20 F - S 0012`:
- `2`: PC pins, side exit (our horizontal footprint).
- `2`: 24 detents for 12 pulses, so one click = half a quadrature cycle = 2 counts in
  CubeMX's "TI1 and TI2" mode. (`1` would be 12 clicks per turn: coarser.)
- `20`: 20 mm shaft, of which 7 mm is the M7 threaded bushing.
- `F`: 6 mm flatted ("D") shaft, which takes a standard push-on D knob.
- `S`: push switch, 0.5 mm stroke.
- `0012`: 12 pulses per turn.

Two things from the same datasheet:
- **An M7 nut and washer come with each encoder.** Screw the encoder through a 7 mm hole in
  the housing wall: the housing then takes the force of turning and pushing, not the 5 solder
  joints.
- **Bourns says "hand soldering not recommended":** the plastic body can soften. Solder each
  leg in 2–3 s and let it cool between legs. Everyone hand-solders these; just don't linger.

## Cable, knob and mechanics

| For | Part | Manufacturer part number | Qty | ~€/pc | Note |
|---|---|---|---|---|---|
| J1 cable | PH 4-pin housing | JST **PHR-4** | 4 | 0.09 | |
| J4 cable | PH 2-pin housing | JST **PHR-2** | 4 | ~0.07 | |
| J1 + J4 cables | Pre-crimped leads, 300 mm, PH socket at both ends | JST **ASPHSPH24K305** | 10 | 0.44 | No crimping tool needed: push the leads into the housing until they click. Cut one in half for 2 bench leads with one free end |
| Knob | Ø 11.4 mm (16 mm skirt), 6 mm D, push-on | CLIFF **CL170827BR** (DigiKey 4654-CL170827BR-ND) | 2 | ~1.04 | "K87" type, black with a blue cap and marker line. Same body and 6 mm D bore as the CL170826BR it replaces (2026-10-20): only the cap colour differs |
| ARM switch | Mini toggle, SPDT on-on, 5 A, solder lugs | E-Switch **100SP1T1B1M1QEH** | 1 | 2.70 | Panel mount in a **6.35 mm** hole (1/4-40 threaded bushing), in the LED+ wire. Solder the middle lug and one outer lug. Take **B1** in the code (threaded): B2/B4 are unthreaded and can't be held by a nut. Replaces the C&K 7101 (€10.83, same job, sturdier than needed) |
| Flux | No-clean tack flux, **lead-free**, 5 cc syringe with tip | Chip Quik **SMD291NL** | 1 | ~11 | For the lead-free (pure Sn) solder: rated for the ~350 °C tip it needs. Not the plain SMD291 (tin-lead version). Price from the US site (~$12), check it on digikey.fr |
| Probe | ST-LINK V3MINIE | ST **STLINK-V3MINIE** | 1 | 22.40 | If not bought yet |

**The leads are all black.** Before the first power-up, mark the GND lead (pin 1, the square
pad on the board) and the +5V lead with a marker or tape. A swapped GND/5V on J1 is the most
destructive mistake possible on this board.

**The J4 cable (remote photodiode, ~50 cm).** JST's pre-crimped leads stop at 305 mm, so:
cut one lead in half (two pigtails, each with a socket), push the sockets into a PHR-2, and
splice them to a 50 cm **twisted pair** of hook-up wire (solder + heat-shrink). Solder the other
end to the head's K and A pads, through the strain-relief holes. Mark the wire going to **pin 1
= K**. Crimping your own contacts (JST SPH-002T-P0.5S) would need a crimp tool.

**The sensor-head PCB** comes from the board house with the main board: its Gerbers are in
`hardware/pd-head/output/`.

## The debug cable (decided 2026-10-14: B)

**A correction to what I said earlier:** the V3MINIE comes with a **14-pin** (STDC14) cable,
not a 10-pin one. ST's 14-pin layout is the ARM 10-pin layout with 2 extra pins at each end:
STDC14 pins 3–12 = ARM pins 1–10. Pins 13–14 carry a UART (the probe's "virtual COM port").
Two ways to connect it:

| | A: keep the 10-pin header | B: change J3 to the 14-pin STDC14 header |
|---|---|---|
| Part | Samtec FTSH-105-01-L-DV, €0.92 (**without** "-K") | Samtec FTSH-107-01-L-DV-K, €2.16 |
| How it plugs | The 14-pin cable socket goes over the 10 pins, centred, with 2 empty holes at each end. Works only with an *unshrouded* header, hence no "-K" | Straight in, keyed: it can't go in wrong |
| Risk | No key: the socket can go on shifted by one position or turned round. Needs a silkscreen outline and care each time | None |
| Board change | None | J3 grows 2.5 mm; re-place and re-route that corner, then `kicad-check` |
| Bonus | | Pins 13–14 can go to PA2/PA3 (USART2, currently unused): `printf` debugging over the ST-LINK's USB, no extra parts |

**Chosen: B.** The board isn't ordered yet, so the change cost one regeneration. You will
plug that cable in hundreds of times. A connector that can't go in wrong, plus a free serial
console for debugging, is worth 2.5 mm. The board now has J3 = STDC14 with USART2 (PA2/PA3) on
pins 13–14, and the CSV lists `FTSH-107-01-L-DV-K`.

## How to order

1. digikey.fr → **BOM Manager** (or "Upload a list"). Upload `bom-digikey.csv` and map the
   columns: *Quantity*, *Manufacturer Part Number*, *Customer Reference*.
2. For each line, check that the match is the **manufacturer** given (Q1: Alpha & Omega) and the
   packaging is **Cut Tape (CT)**, not *Digi-Reel* (that adds a €5.50 reeling fee per line).
3. The *Customer Reference* is printed on each bag, e.g. "R3 R4 100k 0805". Keep the bags
   closed until soldering: 0805 parts all look alike.
4. **Total: about €53 without the probe, €75 with it** (excl. VAT), flux and the Rev C parts included. DigiKey ships free above a
   threshold for France; check it at checkout. DigiKey normally ships to the EU duty-paid, so no
   customs bill on delivery; the checkout page says so.

## Not on this list

- **UV LED star:** as requested.
- **Aluminium plate:** a hardware store, 3–4 mm.
- **Standoffs and screws:** from your stock. 4 M3 standoffs + 8 M3 screws per board. Prefer
  **insulating** (nylon) standoffs: if a THT leg under the board touches one, nothing happens.
  Their length is set in review step 3 (star + LED height, THT legs).
- **PCB:** the board house, 5 boards minimum.
- **Hook-up wire** for the star and the ARM switch: 0.25 mm² (AWG 24). DigiKey sells it in 30 m
  spools at ~€20; a hardware store or your stock is cheaper.
