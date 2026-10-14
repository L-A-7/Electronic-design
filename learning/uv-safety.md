# UV hazard: pocket UV lamps vs the Sun, and what to wear

These are order-of-magnitude estimates against the IEC 62471 / ICNIRP exposure limits. A
real assessment means measuring the actual source (see §6).

## 1. The exposure limits that matter

| Hazard | Spectral range | Limit (8 h day) | Applies to |
|---|---|---|---|
| **Actinic UV** (skin + cornea; photokeratitis / "welder's flash", erythema) | 200–400 nm, weighted by S(λ) | 30 J/m² *effective* | Skin, cornea |
| **UVA eye** (lens; cumulative, cataract) | 315–400 nm, unweighted | 10 kJ/m² for t ≤ 1000 s, i.e. **10 W/m² (1 mW/cm²)** for continuous viewing | Lens |
| **Blue-light retinal** | 300–700 nm, weighted by B(λ) | Radiance limit | Retina; only relevant for staring into a 400–420 nm source |

S(λ) falls very steeply with wavelength. This one curve explains most of the answer:

| λ (nm) | 270 | 300 | 313 | 365 | 395 | 405 |
|---|---|---|---|---|---|---|
| S(λ) | 1 | 0.30 | 0.006 | 1.1·10⁻⁴ | ~4·10⁻⁵ | ~3·10⁻⁵ |

One photon-watt at 300 nm is about **3000× more harmful** than the same power at 365 nm.

## 2. The Sun (summer noon, mid-latitude, clear sky, UV index ~8–10)

- UVA (315–400 nm): ~50–60 W/m² on a horizontal surface, about **5 mW/cm²**
- UVB (280–315 nm): ~1–2 W/m², and it carries **almost all of the actinic dose**
- Skin: fair skin burns in ~15–25 min. The ICNIRP actinic limit is reached in a few minutes.
- Eye: geometry protects you (brow, eyelids, you don't look at the sky). Ocular exposure is
  only ~5–20 % of the horizontal value. Snow, sand and water reflections raise it, hence snow blindness.

## 3. Typical sources compared (irradiance at the eye/skin, beam axis)

| Source | Optical UV power | At 10 cm | Compared with solar UVA | Time to UVA-eye limit (10 kJ/m²) if staring into the beam |
|---|---|---|---|---|
| Keychain 395 nm (one 5 mm LED) | 10–30 mW | ~1–10 W/m² | < sun | No limit (≤ 10 W/m²) |
| 9–51 LED 395 nm torch | 0.1–0.5 W | ~10–100 W/m² | ≈ sun | ~2–15 min |
| "Wood's glass" 365 nm high-power torch (Nichia LED + ZWB2 filter) | 0.5–1.5 W, focused | ~100–1000 W/m² | **2–20× sun** | ~10–100 s |
| Our bench LED, 1 W optical, bare (Lambertian, no optics) | 1 W | ~30 W/m² (~3 W/m² at 30 cm) | ≈ 0.5× sun at 10 cm | ~5 min at 10 cm; none at 30 cm |
| **UVC "steriliser" lamp / LED** (254–280 nm) | 10 mW–1 W | — | S(λ) ≈ 0.5–1 | **Photokeratitis within seconds to minutes. A different category of hazard.** |

Irradiance scales as 1/d² away from the source. Distance is the cheapest protection there is.

## 4. So what is the real hazard?

1. **UVA LEDs (365–405 nm) are not "sunburn" sources.** They emit no UVB, so their actinic
   weight is ~3000× lower. Skin exposure from hands in the beam is minor (UVA does
   contribute to photo-ageing, and a 365 nm torch on skin for tens of minutes can exceed the
   limit, which still has a large safety margin below erythema).
2. **The eye is the organ at risk, and it is mainly the lens (cumulative).** A strong 365 nm
   torch at short range delivers more UVA to the eye than the sun ever does, because you look
   *into* it. Seconds of accidental exposure are harmless. Repeated staring adds up.
3. **UV looks dim.** 365 nm is barely visible, so there is no glare reflex and you don't blink
   or look away. For a 405 nm high-power LED, staring at the die adds a retinal (blue-light) dose.
4. **Specular reflections** (metal, glass, a mirror-like PCB) can redirect a collimated beam into the eye.
5. **Photosensitising drugs** (some antibiotics such as doxycycline, some diuretics,
   isotretinoin, St John's wort…) lower the thresholds a lot.
6. **The bench becomes dangerous if it changes category:** UVC (sterilisation) or focused optics. Both would need a full enclosure, not just glasses.

## 5. Prescription glasses with "UV filtering"

| Lens material / label | Typical UV cut-off | Against 365 nm | Against 395–405 nm |
|---|---|---|---|
| Polycarbonate, high index (1.6/1.67/1.74), photochromic | ~380–400 nm (intrinsic) | Blocks (OD ≥ 2–3) | Partial; most of a 405 nm LED gets through |
| CR-39 (index 1.50) without UV treatment | ~350 nm | **Leaks partially** | Transmits |
| Labelled "UV400" | 400 nm | Blocks | Blocks most of 395, part of 405 |

Limits: clear glasses leave **gaps at the sides and top**. They are fine against a source in
front of you, poor against reflections from the side.

For the bench, buy €10–20 **over-glasses safety goggles** that fit over prescription glasses,
marked **EN 170 (UV filter, code 2 or 2C)** in Europe or **ANSI Z87.1 "U6"**, with a wrap-around shape.
For 395–405 nm work, a yellow/orange lens (EN 170, cut-off ≥ 420 nm) is better.

## 6. Test your glasses (and a first experiment for the bench)

- **Quick test:** shine the UV torch through the lens onto something fluorescent (white
  printer paper, a banknote, tonic water). If the fluorescence disappears behind the lens, it
  blocks that wavelength. Caveat: a 395 nm torch excites fluorescence too, so a lens that
  stops 365 nm can still "fail" with 395 nm. That tells you the cut-off lies between the two.
- **Quantitative:** an optician's UV transmission meter (often free), or, once the bench
  exists, measure the photodiode signal with and without the lens. Transmission T and optical
  density OD = −log₁₀(T) per wavelength makes a good first characterisation experiment.

## 7. Rules for project 01
- Hardware interlock + enclosure (already in the spec). The LED can't be seen directly when it's on.
- Beam pointing down / away from eye level; matte surfaces near the beam.
- Wear the goggles for any open-beam work. Firmware limits current and time in "open lid / test" mode.
- If UVC is ever considered: separate project, full enclosure, no open-beam work at all.
