# UV bench: reference photodiode and optical sampling (365 nm)

**Constraint (2026-10-09):** no expensive UV photodiode. GaP parts cost ~€70 each, which is
too much. Use a **standard, cheap silicon photodiode** and make the *optics* do the work:
take a small, stable fraction of the UV, keep the photodiode cool, and keep ambient light out.

## 1. Which cheap photodiode

The photodiode only needs to be **stable**: the loop holds its reading constant and a power
meter calibrates it once. There is plenty of light, so low responsivity at 365 nm is fine.

| Part | Spectral range (datasheet) | Package | ~Price | Comment |
|---|---|---|---|---|
| **Osram BPW 34 B / BPW 34 BS** ("blue-enhanced"; BPW 34 BS discontinued 2026, successor **SFH 2401**: same pads, same ~15 % at 365 nm) | **350–1100 nm** | DIP-SMT / SMD, 7 mm² | €1–2 | **First choice.** Same well-known BPW34 body, but specified down to 350 nm |
| Advanced Photonix 019-111-411 | 300–1100 nm | 0805 SMD, 0.18 mm² | €0.30–0.70 | Tiny and UV-capable; small area means less signal; stock varies |
| Genicom GUVA-S12SD (GaN) | 240–370 nm | SMD | €3–6 | Visible-blind, but 365 nm sits on its cut-off edge. Keep it as a comparison candidate |
| Standard BPW34 (clear epoxy) | 420–1100 nm | DIP | €1 | **Avoid**: the clear epoxy absorbs most of the light at 365 nm |
| *Experimental:* a **385–395 nm UV LED used as a photodiode** (clear, UV-rated package, never a white/phosphor LED) | Absorbs everything **shorter** than its emission edge (~400 nm), so 365 nm is detected; blind to visible light | 3/5 mm or SMD | €0.30 | The emission band (e.g. 390–420 nm for a 405 nm LED) is *not* the detection band. Avoid a 365 nm LED as detector (365 nm would sit on its edge). Die area ~0.1–1 mm² → 10–100× less current than the BPW 34 B; needs Rf 10–100 MΩ (slower) or more light. DNP footprint D4 on the board, in parallel with the photodiode |

**Ageing:** plastic packages slowly yellow under UV. The optics below keep the UV reaching the
photodiode at **microwatts**, which makes this negligible, and it's one more reason not to send much light onto it.

**Operating mode:** zero bias (photovoltaic) into a TIA. This gives the lowest dark current
and the least temperature drift, and the speed is still plenty for the on/off sampling.

## 2. Optical sampling arrangement ("scatter spot + dark chamber")

```
                     exit window / aperture
        ────────────┐               ┌────────────   housing (black, matte inside)
                    │  useful beam  │
                    │   ╲  ▲▲▲  ╱   │
             lip ═══╡    ╲ ▲▲▲ ╱    │      the lip hides the PTFE spot from the exit window
          PTFE ▓▓   │     ╲▲▲▲╱     │      (no light from outside or from the sample reaches it)
          spot ▓▓ ◄─┼──── LED ─     │      the spot catches a few wide-angle rays that would
               ╲    └───────────────┘      hit the housing wall anyway
     ┌──────────╲──────┐
     │   pinhole Ø 0.5–1 mm in a baffle wall
     │       ▣ PD      │   dark chamber: its only opening looks at the PTFE spot
 ════╪═════════════════╪══════════╤═══════════════════════  PCB
     │  PD copper island          │ milled slot (thermal break)    LED pad + thermal vias
                                  │                    ▓▓▓▓▓▓ aluminium plate under the LED only
```

1. **Scatter spot.** A ~2 mm² patch of **PTFE** (white Teflon: a scrap of sheet, or a few
   layers of plumber's PTFE tape) on the inside wall, placed in the LED's **wide-angle edge
   rays**, outside the useful beam cone. PTFE is an excellent diffuse reflector in the UV, is
   UV-stable and barely fluoresces. Avoid white paper (its optical brighteners fluoresce) and
   white plastics (they fluoresce and age).
2. **Dark chamber + pinhole.** The photodiode sits in a closed black chamber whose only
   opening is a 0.5–1 mm pinhole looking at the PTFE spot. A **lip** in the housing hides the
   spot from the exit window. Outside light (and UV reflected back by the sample) would need
   several bounces to reach the photodiode, which attenuates it by roughly 10⁻⁴ or more. The
   electronic on/off subtraction removes the rest.
3. **Thermal isolation.**
   - Photodiode ≥ 15–20 mm from the LED, on its own copper island.
   - A **milled slot** in the PCB between the LED area and the photodiode area (it costs nothing at JLCPCB/PCBWay).
   - The aluminium heat-spreader plate only under the LED.
   - The photodiode receives only ~10 µW of light, so it doesn't heat itself.
4. **Rigidity.** The LED, PTFE spot and photodiode must not move relative to each other.
   They share one PCB, the housing is screwed to it, and the PTFE is glued in.

### Light budget (order of magnitude, to refine at M2)

- LED ~400 mW optical, roughly Lambertian. Radiant intensity at 70° off-axis ≈ (P/π)·cos 70° ≈ 0.04 W/sr.
- A 2 mm² PTFE patch at 10 mm subtends 0.02 sr, so it receives ≈ 0.9 mW and re-emits diffusely (reflectance ~0.9). That's ≈ 0.25 mW/sr.
- A BPW 34 B (7 mm²) at ~10 mm behind the pinhole collects roughly **5–20 µW**.
- Responsivity at 365 nm ~0.1 A/W (read it from the datasheet curve), giving **0.5–2 µA**.

Tuning knobs, if the signal is too high or too low: patch size, pinhole diameter, distances.

## 3. TIA sizing (first estimate; simulation S4 confirms)

| Parameter | Value | Reason |
|---|---|---|
| R_f | 1 MΩ | 1–2 µA → 1–2 V on the 3.3 V ADC |
| Photodiode capacitance | ~70 pF (BPW34 at 0 V) | Datasheet |
| Op-amp | CMOS RRIO, ~10 MHz GBW, pA bias (TLV9061/OPA376 class) | |
| C_f | ~1.5–2.2 pF | Minimum for stability ≈ √(C_pd / (2π R_f GBW)) ≈ 1 pF, plus margin |
| Bandwidth | ≈ 1/(2π R_f C_f) ≈ 70–100 kHz | Settles to 0.5 % in ~8–10 µs, which suits the on/off samples (dark gap 50 µs) |

## 4. M1 test (decides D3)

Build the arrangement in a cardboard or 3D-printed box with a BPW 34 B, a GUVA-S12SD and a 385–395 nm LED-as-detector. Quick check first: LED straight on a multimeter (µA range) under the flashlight, then under a white lamp: a visible-blind detector barely moves.
1. Fixed LED current. Log each detector's (on − off) signal and the LED temperature from a cold start to equilibrium (~15 min).
2. Turn a desk lamp or phone torch on and off next to the box: the (on − off) signal must not move.
3. Heat the photodiode area alone (hair dryer, briefly) to see its own temperature sensitivity.
4. Keep the detector + geometry with the smallest apparent drift.

## Sources
- Osram BPW 34 B datasheet (350–1100 nm, blue-enhanced): [Mouser](https://www.mouser.com/datasheet/2/588/BPW_34_B_EN-3560587.pdf); standard BPW 34 S (420–1120 nm): [ams-osram](https://ams-osram.com/products/photodetectors/photodiodes/osram-dil-smt-bpw-34-s)
- Advanced Photonix 019-111-411 (300–1100 nm, 0805): [LCSC](https://www.lcsc.com/product-detail/C3211130.html)
- GUVA-S12SD datasheet (Genicom): [DigiKey copy](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6128/GUVA-S12SD%20%282%29.pdf)
- GaN absorption edge ≈ 365 nm: [MRS Internet J. Nitride Semicond. Res.](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/S109257830000065X)
