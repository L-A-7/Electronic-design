"""Remote photodiode head (sensor head for J4 of the UV bench, Rev C): the circuit as data.

Same format as design.py; build it with UVB_DESIGN=design_head (see ../README.md).
An SFH 2401 (the same part as D1 on the main board) on a 12 x 21 mm board. It lies on the target,
under a ZWB2 filter like the lamp's, and two twisted wires (~50 cm) go to J4 on the main board.
The load resistor and filter are on the main board (R8, C8): this board carries only the diode.
Pin 1 of the wire pads = cathode = J4 pin 1 (the bias, +3V3 through R6); pin 2 = anode = signal.
"""

REV = "A"
PAPER = "A4"
PROJECT = "pd-head"
TITLE = "UV bench remote photodiode head"
LAYOUT = "layout_head"
PLACEMENT = "placement_head"
PARTS_LIST = None          # two parts: described in docs/rev-b-simple.md, block 8
MOUNTING_HOLES = 0         # the head is held by its cable and a clip/3D-printed cap, not screws

SHEETS = [dict(
    title="PD head", file="pd-head.kicad_sch",
    note="Remote photodiode for the UV bench (J4). Lies on the target under a ZWB2 filter.\n"
         "Wire pad 1 = cathode -> J4 pin 1 (bias); pad 2 = anode -> J4 pin 2 (signal). Twist the pair.",
    parts=[
        ("D", "Sensor_Optical:BPW34-SMD", "SFH 2401", "OptoDevice:Osram_BPW34S-SMD", {"1": "PD_K", "2": "PD_A"},
         {"MPN": "ams OSRAM SFH 2401", "ref": "D1"}),
        ("J", "Connector_Generic:Conn_01x02", "cable to J4",
         "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm_Relief", {"1": "PD_K", "2": "PD_A"},
         {"in_bom": False, "ref": "J1"}),
    ])]
