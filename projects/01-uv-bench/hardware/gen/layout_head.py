"""Schematic layout of the photodiode head (format: see layout.py)."""

SH = "PD head"
AT = {SH: {
    "D1": ("1", (24, 16), 270, None),     # cathode on top
    "J1": ("1", (30, 17), 0, None),       # wire pads, pins facing the diode
}}
WIRES = {SH: [
    ("PD_K", ["D1.1", (27, 16), (27, 17), "J1.1"]),
    ("PD_A", ["D1.2", (28, 19), (28, 18), "J1.2"]),
]}
POWER = {SH: []}
LABELS = {SH: []}
TEXTS = {SH: [("REMOTE PHOTODIODE HEAD (UV bench J4)", (20, 11))]}
