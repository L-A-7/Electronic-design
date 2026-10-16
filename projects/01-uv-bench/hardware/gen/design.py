"""UV bench Rev B: the circuit as data (single source of truth).

Every component is one line: reference prefix, library symbol, value, footprint, pin→net map,
and optional fields (MPN, DNP, unit). The generator `gen_sch.py` turns this into the KiCad
schematic, `gen_pcb.py` into the board. Why each block and value: ../../docs/rev-b-simple.md.
Rev A (71 parts, 4 sheets) is kept in ../archive/rev-a/.

Net naming rules (they drive the net classes in uv-bench.kicad_pro):
  +5V, LED_K, I_MON  -> Power class (wide tracks: they carry the LED current)
  PD                 -> Analog class (kept away from power tracks)
  GND, +3V3, +5V     -> power symbols; everything else is a net label
"""

REV = "C"
PAPER = "A4"

FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"

R = lambda v, a, b, **k: ("R", "Device:R", v, FP_R, {"1": a, "2": b}, k)
C = lambda v, a, b, **k: ("C", "Device:C", v, FP_C, {"1": a, "2": b}, k)
NC = None   # pin intentionally not connected (gets a no-connect flag)

SHEETS = []


def sheet(title, filename, note, parts):
    SHEETS.append(dict(title=title, file=filename, note=note, parts=parts))


# References are given explicitly (ref=...) so they match docs/rev-b-simple.md block by block.
sheet("UV bench", "uv-bench.kicad_sch",
      "365 nm LED held at constant optical power by a photodiode loop in the MCU. I2C target 0x2A, 5 V in.\n"
      "LED current: I = (V_gate - V_GS) / R1, at most (5 V - V_f) / 3.9 R = 0.33 A (hardware limit).\n"
      "J2 goes to the LED star through the UV ARM toggle switch (in the LED+ wire, on the housing).",
      [
    # --- 1 power input
    ("J", "Connector_Generic:Conn_01x04", "I2C + 5V (JST-PH)", "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
     {"1": "GND", "2": "+5V", "3": "SDA", "4": "SCL"}, {"MPN": "JST B4B-PH-K-S", "ref": "J1"}),
    C("10u", "+5V", "GND", ref="C1"),
    C("10u", "+5V", "GND", ref="C2"),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "+5V"}, {}),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "GND"}, {}),
    # --- 2 3.3 V regulator
    ("U", "Regulator_Linear:MCP1700x-330xxTT", "MCP1700-3.3", "Package_TO_SOT_SMD:SOT-23_Handsoldering",
     {"1": "GND", "2": "+3V3", "3": "+5V"}, {"MPN": "Microchip MCP1700T-3302E/TT", "ref": "U1"}),
    C("10u", "+3V3", "GND", ref="C3"),
    # --- 3 microcontroller
    ("U", "MCU_ST_STM32C0:STM32C031F6Px", "STM32C031F6P6", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
     {"4": "+3V3", "5": "GND", "6": "NRST", "7": "PD", "8": "I_MON", "15": "PWM", "18": "SWDIO", "19": "SWCLK",
      "20": "SCL", "1": "SDA",
      "11": "MODE_LED", "12": "BTN", "13": "ENC_A", "14": "ENC_B",
      "9": "UART_TX", "10": "UART_RX",               # PA2/PA3 = USART2, to the ST-LINK's virtual COM port
      "17": "ADC_EXT_PD",                            # PA12 = ADC1_IN12 (shares pin 17 with PA10): remote photodiode.
      "2": NC, "3": NC, "16": NC},                   #   Not PA11 (pin 16): that pin is next to the PWM (pin 15)
     {"MPN": "ST STM32C031F6P6", "ref": "U2"}),
    C("100n", "+3V3", "GND", ref="C4"),           # decoupling, right at VDD
    C("100n", "NRST", "GND", ref="C5"),
    # --- 4 LED driver
    R("1k", "PWM", "GATE", ref="R2"),             # PWM -> DC filter (with C7)
    C("10u", "GATE", "GND", ref="C7"),
    R("100k", "GATE", "GND", ref="R3"),           # safety pull-down
    ("Q", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23_Handsoldering",
     {"1": "GATE", "2": "I_MON", "3": "LED_K"}, {"MPN": "Alpha & Omega AO3400A", "ref": "Q1"}),
    ("R", "Device:R", "3R9 1W", "Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder",
     {"1": "I_MON", "2": "GND"}, {"MPN": "any 3.9 R 1 W 2512, e.g. Yageo RC2512FK-073R9L", "ref": "R1"}),
    ("J", "Connector_Generic:Conn_01x02", "LED star", "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm",
     {"1": "+5V", "2": "LED_K"}, {"in_bom": False, "ref": "J2"}),
    # --- 5 photodiode sensor
    # SFH 2401 = successor of the discontinued BPW 34 BS: same solder pads (large pad = cathode), same
    # ~15 % relative sensitivity at 365 nm, so the BPW34S footprint and R4 = 100 k are kept.
    ("D", "Sensor_Optical:BPW34-SMD", "SFH 2401", "OptoDevice:Osram_BPW34S-SMD", {"1": "+3V3", "2": "PD"},
     {"MPN": "ams OSRAM SFH 2401", "ref": "D1"}),
    R("100k", "PD", "GND", ref="R4"),
    C("100n", "PD", "GND", ref="C6"),
    # --- 7 user controls: knob (encoder + push) and mode LED. No pull-ups/filters: the MCU's internal
    #     pull-ups, the timer's encoder mode with its input filter, and firmware debouncing do it.
    ("SW", "Device:RotaryEncoder_Switch", "PEC09 + push", "Rotary_Encoder:RotaryEncoder_Bourns_Horizontal_PEC09-2xxxF-Sxxxx",
     {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "BTN", "S2": "GND"},
     {"MPN": "Bourns PEC09-2xxxF-Sxxxx (with switch; pick the shaft length)", "ref": "SW1"}),
    R("1k", "MODE_LED", "D2_A", ref="R5"),
    ("D", "Device:LED", "green", "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder",
     {"1": "GND", "2": "D2_A"}, {"ref": "D2"}),
    # --- 8 remote photodiode (Rev C, optional): an SFH 2401 on a small head PCB at the end of a 50 cm
    #     twisted pair, lying on the target under the same ZWB2 filter as the lamp. It is a current source
    #     (~5.6 uA per mW/cm2 through the filter), so the load and the filter sit HERE, at the ADC:
    #     cable pickup goes into a low impedance. R8 = 10 k reads ~0.5-50 mW/cm2 (swap it after measuring).
    #     R6 limits the current if the cable shorts +3V3 to GND; R7 + C8 protect the ADC pin from ESD when
    #     plugging. Unplugged, R8 pulls the input to 0 V: the firmware sees "no sensor".
    ("J", "Connector_Generic:Conn_01x02", "remote PD (JST-PH)", "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
     {"1": "EXT_PD_K", "2": "EXT_PD"}, {"MPN": "JST B2B-PH-K-S", "ref": "J4"}),
    R("1k", "EXT_PD_K", "+3V3", ref="R6"),        # photodiode bias, short-circuit limit
    R("10k", "EXT_PD", "GND", ref="R8"),          # load: V = I_photo x 10 k
    C("100n", "EXT_PD", "GND", ref="C8"),         # tau = 1 ms with R8; ESD charge sink at the connector
    R("1k", "EXT_PD", "ADC_EXT_PD", ref="R7"),    # series resistor into the ADC pin
    # --- 6 debug port: ST's 14-pin STDC14, the connector of the STLINK-V3MINIE's cable (keyed: it can't go in
    #     the wrong way). Pins 3-12 are the ARM 10-pin layout; 13-14 add a UART, seen on the PC as a COM port
    #     through the probe's USB. Directions are the probe's: VCP_RX (13) receives what the MCU sends (TX).
    #     Pins 1-2 are not connected inside the probe; JTAG-only pins (SWO, JRCLK, JTDI) don't exist on a Cortex-M0+.
    ("J", "Connector:Conn_ST_STDC14", "STDC14 (SWD + VCP)", "Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical_SMD",
     {"1": NC, "2": NC, "3": "+3V3", "4": "SWDIO", "5": "GND", "6": "SWCLK", "7": "GND", "8": NC, "9": NC,
      "10": NC, "11": "GND", "12": "NRST", "13": "UART_TX", "14": "UART_RX"},
     {"MPN": "Samtec FTSH-107-01-L-DV-K", "ref": "J3"}),
])
