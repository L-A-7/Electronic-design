"""Schematic drawing layout (how the circuit is *drawn*; design.py says what it *is*).

Coordinates are in grid units of 2.54 mm (KiCad's default schematic grid); halves are allowed.
  AT[sheet]    ref or ref:unit -> (pin, (x, y), rotation, mirror): the named pin lands on (x, y)
  WIRES[sheet] (net, [points])  points = (x, y) or "REF.PIN"; consecutive points must be aligned
  POWER[sheet] (net, (x, y), direction)   power symbol at a wire point (direction = where it points)
  LABELS[sheet](net, (x, y), direction)   net label at a wire point
Pins that no wire reaches get the automatic treatment: short stub + label or power symbol.
Parts not listed in AT are placed automatically in rows at the bottom of the sheet.
Rotation is counter-clockwise (KiCad convention): a resistor at 90 has pin 1 on the left.
"""

AT, WIRES, POWER, LABELS = {}, {}, {}, {}

# ----------------------------------------------------------------------------------------- Power
AT["Power"] = {
    "J1": ("1", (22, 30), 0, "y"),          # main-board connector, pins facing right
    "#FLG1": ("1", (26, 31), 0, None),
    "C1": ("1", (28, 31), 0, None),
    "U1": ("1", (30, 31), 0, None),         # LM66100: VIN at (30,31)
    "J2": ("1", (22, 44), 0, "y"),          # FTDI header
    "#FLG2": ("1", (26, 46), 0, None),
    "C2": ("1", (29, 46), 0, None),
    "U2": ("1", (30, 46), 0, None),
    "F1": ("1", (40, 31), 90, None),        # polyfuse, horizontal
    "#FLG4": ("1", (45, 31), 0, None),
    "D1": ("1", (47, 31), 270, None),       # TVS, cathode (pin 1) up on +5V
    "C3": ("1", (50, 31), 0, None),
    "TP1": ("1", (54, 31), 0, None),
    "FB1": ("1", (58, 31), 90, None),
    "C4": ("1", (64, 31), 0, None),
    "C5": ("1", (67, 31), 0, None),
    "TP2": ("1", (69, 31), 0, None),
    "U3": ("1", (55, 41), 0, None),         # LDO: IN at (55,41)
    "C6": ("1", (50, 41), 0, None),
    "C7": ("1", (64, 41), 0, None),
    "TP3": ("1", (67, 41), 0, None),
}
WIRES["Power"] = [
    ("5V_MAIN", ["J1.2", "U1.1"]),
    ("GND", ["U1.3", (30, 35), "U1.2"]), ("GND", ["U1.2", (33, 36)]),
    ("5V_FTDI", ["J2.3", "U2.1"]),
    ("GND", ["U2.3", (30, 50), "U2.2"]), ("GND", ["U2.2", (33, 51)]),
    ("5V_OR", ["U1.6", (38, 31), "F1.1"]), ("5V_OR", ["U2.6", (38, 46), (38, 31)]),
    ("+5V", ["F1.2", "FB1.1"]),
    ("5V_LED", ["FB1.2", (72, 31)]),
    ("+5V", [(52, 31), (52, 41), "U3.1"]), ("+5V", [(52, 41), (52, 42), "U3.3"]), ("+5V", [(52, 41), "C6.1"]),
    ("+3V3", ["U3.5", (70, 41)]),
]
POWER["Power"] = [("GND", (33, 36), "down"), ("GND", (33, 51), "down"), ("+5V", (56, 31), "up"),
                  ("+3V3", (70, 41), "up")]
LABELS["Power"] = [("5V_LED", (72, 31), "right")]

# ----------------------------------------------------------------------------------------- MCU
AT["MCU"] = {
    "U5": ("4", (60, 41), 0, None),         # VDD pin at (60,41); origin (60,50)
    "C8": ("1", (56, 34), 0, None),
    "C9": ("1", (52, 34), 0, None),
    "C10": ("1", (43, 44), 0, None),
    "J3": ("10", (35, 42), 0, None),        # SWD: nRESET pin at (35,42)
    "R3": ("1", (70, 54), 90, None),        # status LED chain on PA12 (pin 17)
    "D2": ("2", (75, 54), 180, None),       # LED anode left, cathode right
}
WIRES["MCU"] = [
    ("+3V3", ["U5.4", (60, 34), "C8.1"]), ("+3V3", ["C8.1", "C9.1"]),
    ("NRST", ["U5.6", "C10.1"]), ("NRST", ["C10.1", (41, 44), (41, 42), "J3.10"]),
    ("STATUS_LED", ["U5.17", "R3.1"]),
    ("LED_STAT_A", ["R3.2", "D2.2"]),
]
POWER["MCU"] = [("+3V3", (60, 34), "up")]
LABELS["MCU"] = []

# ----------------------------------------------------------------------------------------- LED driver
AT["LED driver"] = {
    "R4": ("1", (20, 30), 90, None),
    "C11": ("1", (25, 30), 0, None),
    "R5": ("1", (27, 30), 90, None),
    "R6": ("1", (32, 30), 0, None),
    "C12": ("1", (35, 30), 0, None),
    "TP7": ("1", (37, 30), 0, None),
    "U6:1": ("1", (40, 30), 0, None),       # analog switch: in (40,30), out (49,30), control (40,33)
    "R7": ("1", (52, 30), 0, None),
    "TP8": ("1", (54, 30), 0, None),
    "U8:1": ("3", (57, 30), 0, None),       # current-loop op-amp: + (57,30), - (57,32), out (63,31)
    "R11": ("1", (64, 31), 90, None),
    "R13": ("1", (67, 33), 0, None),
    "Q1": ("1", (68, 31), 0, None),         # gate (68,31), drain (71,29), source (71,33)
    "C15": ("1", (64, 35), 270, None),      # GATE_DRV (pin 1) right, FB_I (pin 2) left
    "R12": ("2", (55, 43), 270, None),      # FB_I (pin 2) left, ISENSE_K (pin 1) right
    "TP10": ("1", (71, 35), 270, None),     # body to the right, clear of Q1
    "R14": ("1", (71, 37), 0, None),        # sense resistor, pin 1 at the top
    "NT1": ("1", (73, 37), 0, None),        # Kelvin net tie taken at the top of R14
    "TP11": ("1", (74, 26), 180, None),     # body below the wire
    "J5": ("2", (79, 26), 0, None),         # LED star wire pads: pin 2 = DRAIN
    "U8:2": ("5", (81, 43), 0, None),       # current monitor: + (81,43), - (81,45), out (87,44)
    "R16": ("1", (78, 49), 0, None),
    "R15": ("2", (78, 47), 270, None),
    "R17": ("1", (89, 44), 90, None),
    "C16": ("1", (94, 44), 0, None),
    "U7": ("1", (24, 44), 0, None),         # AND gate: in1 (24,44), in2 (24,46), out (35,45)
    "R9": ("1", (38, 47), 0, None),
    "R8": ("1", (18, 40), 0, None),
    "TP9": ("1", (20, 40), 0, None),
    "J4": ("2", (12, 46), 0, "y"),          # UV ARM switch connector, pins facing right
    "R10": ("1", (15, 46), 0, None),
    "C13": ("1", (19, 46), 0, None),
}
WIRES["LED driver"] = [
    ("SET_PWM", [(18, 30), "R4.1"]),
    ("SET_RC1", ["R4.2", "R5.1"]),
    ("SET_F", ["R5.2", "U6.1"]),
    ("SET_G", ["U6.2", "U8.3"]),
    ("GATE_DRV", ["U8.1", "R11.1"]), ("GATE_DRV", ["R11.1", "C15.1"]),
    ("Q1_G", ["R11.2", "Q1.1"]), ("Q1_G", ["R11.2", "R13.1"]),
    ("FB_I", ["U8.2", (55, 32), "R12.2"]), ("FB_I", ["C15.2", (55, 35)]),
    ("DRAIN", ["Q1.2", (71, 26), "J5.2"]), ("DRAIN", [(71, 26), (66, 26)]),
    ("ISENSE", ["Q1.3", "R14.1"]), ("ISENSE", ["R14.1", "NT1.1"]),
    ("ISENSE_K", ["NT1.2", (77, 37), (77, 43), "R12.1"]), ("ISENSE_K", [(77, 43), "U8.5"]),
    ("FB_M", ["U8.6", (78, 45), "R16.1"]),
    ("I_MON_RAW", ["U8.7", (88, 44), "R17.1"]), ("I_MON_RAW", ["R15.1", (88, 47), (88, 44)]),
    ("I_MON", ["R17.2", (97, 44)]),
    ("EN_LED", ["U7.4", (38, 45), (38, 33), "U6.4"]), ("EN_LED", [(38, 45), "R9.1"]),
    ("GATE", [(14, 40), (23, 40), (23, 44), "U7.1"]),
    ("ARM_OK", ["J4.2", "U7.2"]), ("ARM_OK", [(21, 46), (21, 49)]),
]
POWER["LED driver"] = []
LABELS["LED driver"] = [("SET_PWM", (18, 30), "left"), ("DRAIN", (66, 26), "left"), ("I_MON", (97, 44), "right"),
                        ("GATE", (14, 40), "left"), ("ARM_OK", (21, 49), "down")]

# ----------------------------------------------------------------------------------------- Photodiode
AT["Photodiode and monitors"] = {
    "U9": ("3", (37, 29), 0, None),         # TIA: + (37,29), - (37,31), out (43,30)
    "D3": ("1", (30, 31), 270, None),       # photodiode, cathode up
    "D4": ("1", (25, 31), 0, "y"),          # alternative detector pads (pin 1 = cathode)
    "R18": ("2", (38.5, 36), 270, None),    # Rf: TIA_IN (pin 2) left, PD_OUT (pin 1) right
    "C18": ("2", (38.5, 39), 270, None),    # Cf
    "TP12": ("1", (47, 30), 0, None),
    "R21": ("1", (48, 30), 90, None),
    "C20": ("1", (53, 30), 0, None),
    "R19": ("2", (28, 24), 0, None),        # V_REF divider
    "R20": ("1", (25, 24), 0, None),
    "C19": ("1", (22, 24), 0, None),
    "J6": ("1", (25, 50), 0, "y"),          # NTC wire pads
    "R22": ("2", (29, 50), 0, None),
    "C21": ("1", (32, 50), 0, None),
    "R23": ("1", (24, 59), 0, None),        # V_HEAD = DRAIN / 2
    "R24": ("1", (24, 64), 0, None),
    "C22": ("1", (28, 63), 0, None),
    "R25": ("1", (40, 59), 0, None),        # V_IN = 5V_LED / 2
    "R26": ("1", (40, 64), 0, None),
    "C23": ("1", (44, 63), 0, None),
}
WIRES["Photodiode and monitors"] = [
    ("TIA_IN", ["D4.1", "D3.1"]), ("TIA_IN", ["D3.1", (35, 31), "U9.4"]),
    ("TIA_IN", [(35, 31), (35, 36), "R18.2"]), ("TIA_IN", [(35, 36), (35, 39), "C18.2"]),
    ("PD_OUT", ["U9.1", (45, 30), "R21.1"]), ("PD_OUT", [(45, 30), (45, 36), "R18.1"]),
    ("PD_OUT", [(45, 36), (45, 39), "C18.1"]),
    ("PD_ADC", ["R21.2", "C20.1"]), ("PD_ADC", ["C20.1", (56, 30)]),
    ("PD_VREF", ["U9.3", (35, 29), (35, 24), "R19.2"]), ("PD_VREF", ["R19.2", "R20.1"]),
    ("PD_VREF", ["R20.1", "C19.1"]),
    ("T_LED", ["J6.1", "R22.2"]), ("T_LED", ["R22.2", "C21.1"]), ("T_LED", ["C21.1", (36, 50)]),
    ("V_HEAD", ["R23.2", "R24.1"]), ("V_HEAD", [(24, 63), "C22.1"]), ("V_HEAD", ["C22.1", (31, 63)]),
    ("V_IN", ["R25.2", "R26.1"]), ("V_IN", [(40, 63), "C23.1"]), ("V_IN", ["C23.1", (47, 63)]),
]
POWER["Photodiode and monitors"] = []
LABELS["Photodiode and monitors"] = [("PD_ADC", (56, 30), "right"), ("T_LED", (36, 50), "right"),
                                     ("V_HEAD", (31, 63), "right"), ("V_IN", (47, 63), "right")]


def _shift(sheet, xmin, dx):
    """Move everything right of x = xmin by dx grid units (used to make room on a sheet)."""
    mv = lambda p: (p[0] + dx, p[1]) if isinstance(p, tuple) and p[0] >= xmin else p
    AT[sheet] = {k: (v[0], mv(v[1])) + tuple(v[2:]) for k, v in AT[sheet].items()}
    WIRES[sheet] = [(n, [mv(p) for p in pts]) for n, pts in WIRES[sheet]]
    POWER[sheet] = [(n, mv(p), d) for n, p, d in POWER[sheet]]
    LABELS[sheet] = [(n, mv(p), d) for n, p, d in LABELS[sheet]]


_shift("Power", 29, 4)     # input capacitors C1/C2 get room for their text before U1/U2
AT["Power"]["C1"] = ("1", (31, 31), 0, None)
AT["Power"]["C2"] = ("1", (31, 46), 0, None)
AT["Power"]["C5"] = ("1", (73, 31), 0, None)        # clear of C4's value text
AT["Power"]["TP2"] = ("1", (76, 31), 0, None)
WIRES["Power"] = [(n, [(80, 31) if p == (76, 31) else p for p in pts]) for n, pts in WIRES["Power"]]
LABELS["Power"] = [("5V_LED", (80, 31), "right")]
AT["Power"]["C3"] = ("1", (55, 31), 0, None)         # clear of D1's value text
WIRES["Power"] = [(n, [(57, p[1]) if isinstance(p, tuple) and p[0] == 56 else p for p in pts])
                  for n, pts in WIRES["Power"]]       # +5V branch to the LDO moves with it
