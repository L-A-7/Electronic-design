"""Schematic drawing layout, Rev B (how the circuit is *drawn*; design.py says what it *is*).

Coordinates are in grid units of 2.54 mm (KiCad's default schematic grid); halves are allowed.
  AT[sheet]    ref -> (pin, (x, y), rotation, mirror[, opts]): the named pin lands on (x, y)
  WIRES[sheet] (net, [points])  points = (x, y) or "REF.PIN"; consecutive points must be aligned
  POWER[sheet] (net, (x, y), direction)   power symbol at a wire point (direction = where it points)
  LABELS[sheet](net, (x, y), direction)   net label at a wire point
  TEXTS[sheet] (text, (x, y))             block captions
Pins that no wire reaches get the automatic treatment: short stub + label or power symbol.
Rotation is counter-clockwise (KiCad convention): a resistor at 90 has pin 1 on the left.

One A4 sheet, blocks numbered as in docs/rev-b-simple.md:
  1 power input | 2 regulator | 6 debug | 3 MCU | 4 LED driver (top right) | 5 photodiode (below it)
  7 user controls (below the MCU) | 8 remote photodiode (bottom left)
Rev A's layout (4 sheets) is in ../archive/rev-a/gen/layout.py.
"""

SH = "UV bench"
AT, WIRES, POWER, LABELS, TEXTS = {}, {}, {}, {}, {}

AT[SH] = {
    # 1 power input: J1 pins face right, pin 1 (GND) at the bottom
    "J1": ("1", (16, 25), 180, None),
    "#FLG2": ("1", (17, 27), 270, None),    # GND flag, beside the GND wire
    "C1": ("1", (22, 24), 0, None),
    "C2": ("1", (25, 24), 0, None),
    "#FLG1": ("1", (27, 24), 0, None),      # +5V flag
    # 2 regulator: VI at (29,24), VO at (35,24), GND below
    "U1": ("3", (29, 24), 0, None),
    "C3": ("1", (38, 24), 0, None),
    # 6 debug port: nRST pin at (52,26), signal pins facing the MCU
    "J3": ("12", (52, 26), 0, None),
    # 3 MCU: VDD (pin 4) at (70,23); left pins at x = 63, right pins at x = 77
    "U2": ("4", (70, 23), 0, None),
    "C4": ("1", (66, 18), 0, None),
    "C5": ("1", (58, 26), 0, None),
    # 4 LED driver: PWM -> R2 -> GATE (C7, R3) -> Q1; drain to J2 (LED), source to R1
    "R2": ("1", (87, 34), 90, None),
    "C7": ("1", (92, 34), 0, None),
    "R3": ("1", (96, 34), 0, None),
    "Q1": ("1", (101, 34), 0, None),
    "R1": ("1", (104, 38), 0, None),
    "J2": ("1", (109, 29), 0, None),
    # 5 photodiode: cathode up to +3V3, anode down to the R4 / C6 node
    "D1": ("1", (89, 46), 270, None),
    "R4": ("1", (89, 51), 0, None),
    "C6": ("1", (93, 51), 0, None),
    # 7 user controls: encoder drawn with its pins pointing down (A, C, B) and up (switch S1, S2)
    "SW1": ("C", (60, 53), 90, None),
    "R5": ("1", (71, 50), 90, None),
    "D2": ("2", (78, 50), 0, "y"),         # mirrored: anode left, cathode right (rot 180 would turn its text upside down)
    # 8 remote photodiode: J4 pins face right (pin 1 = cathode/bias at the bottom), R8/C8 at the node, R7 to the ADC
    "J4": ("1", (16, 54), 180, None),
    "R6": ("1", (21, 54), 90, None),
    "R8": ("1", (29, 50), 0, None),
    "C8": ("1", (32, 50), 0, None),
    "R7": ("1", (34, 50), 90, None),
}
WIRES[SH] = [
    ("GND", ["J1.1", (17, 25), (17, 28)]),
    ("+5V", ["J1.2", "C1.1", "C2.1", "U1.3"]),
    ("+3V3", ["U1.2", "C3.1", (41, 24)]),
    ("NRST", ["U2.6", "C5.1", "J3.12"]),
    ("+3V3", ["U2.4", (70, 18), "C4.1"]),
    ("PWM", [(85, 34), "R2.1"]),
    ("GATE", ["R2.2", "C7.1", "R3.1", "Q1.1"]),
    ("LED_K", ["Q1.3", (104, 30), "J2.2"]),
    ("+5V", ["J2.1", (107, 29), (107, 27)]),
    ("I_MON", ["Q1.2", "R1.1"]),
    ("I_MON", [(104, 37), (107, 37)]),
    ("PD", ["D1.2", "R4.1"]),
    ("PD", ["R4.1", "C6.1", (97, 51)]),
    ("GND", ["J3.11", (46, 39), (47, 39), "J3.5"]),    # the three GND pins of J3 share one symbol
    ("ENC_A", ["SW1.A", (59, 56), (55, 56)]),
    ("ENC_B", ["SW1.B", (61, 56), (65, 56)]),
    ("BTN", ["SW1.S1", (59, 45), (55, 45)]),
    ("GND", ["SW1.S2", (61, 45), (64, 45), (64, 46)]),
    ("MODE_LED", [(69, 50), "R5.1"]),
    ("D2_A", ["R5.2", "D2.2"]),
    ("GND", ["D2.1", (84, 50), (84, 51)]),
    ("EXT_PD_K", ["J4.1", "R6.1"]),
    ("+3V3", ["R6.2", (25, 54)]),
    ("EXT_PD", ["J4.2", (17, 53), (17, 50), "R8.1", "C8.1", "R7.1"]),
    ("ADC_EXT_PD", ["R7.2", (39, 50)]),
]
POWER[SH] = [("GND", (17, 28), "down"), ("+5V", (20, 24), "up"), ("+3V3", (41, 24), "up"),
             ("+3V3", (70, 18), "up"), ("+5V", (107, 27), "up"), ("GND", (47, 39), "down"),
             ("GND", (64, 46), "down"), ("GND", (84, 51), "down"),
             ("+3V3", (25, 54), "up")]
LABELS[SH] = [("PWM", (85, 34), "left"), ("I_MON", (107, 37), "right"), ("PD", (97, 51), "right"),
              ("ENC_A", (55, 56), "left"), ("ENC_B", (65, 56), "right"), ("BTN", (55, 45), "left"),
              ("MODE_LED", (69, 50), "left"), ("ADC_EXT_PD", (39, 50), "right")]
TEXTS[SH] = [
    ("1  POWER INPUT", (13, 19)),
    ("2  3.3 V REGULATOR", (28, 19)),
    ("6  DEBUG PORT (SWD + UART)", (43, 19)),
    ("3  MICROCONTROLLER", (62, 15)),
    ("4  LED DRIVER", (85, 24)),
    ("5  PHOTODIODE SENSOR", (85, 42)),
    ("7  USER CONTROLS (knob + push, mode LED)", (53, 42)),
    ("8  REMOTE PHOTODIODE (optional, 50 cm cable)", (13, 46)),
]
