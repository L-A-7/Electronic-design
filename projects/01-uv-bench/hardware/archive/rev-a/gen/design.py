"""UV bench Rev A: the circuit as data (single source of truth).

Every component is one line: reference prefix, library symbol, value, footprint, pin→net map,
and optional fields (MPN, DNP, unit). The generator `gen_sch.py` turns this into the KiCad
schematic, `gen_pcb.py` into the board. Reasons for each value: ../../docs/design-notes.md.

Net naming rules (they drive the net classes in uv-bench.kicad_pro):
  *5V*, DRAIN          -> Power class (wide tracks)
  PD_*, TIA_*, SET_*, I_MON*, T_LED, V_HEAD, V_IN -> Analog class (kept away from power)
  GND, +3V3, +5V       -> power symbols; everything else is a label
A net that appears on more than one sheet becomes a global label automatically.
"""

FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SOT23_5 = "Package_TO_SOT_SMD:SOT-23-5_HandSoldering"
FP_TP = "TestPoint:TestPoint_Pad_D1.5mm"

R = lambda v, a, b, **k: ("R", "Device:R", v, FP_R, {"1": a, "2": b}, k)
C = lambda v, a, b, **k: ("C", "Device:C", v, FP_C, {"1": a, "2": b}, k)
TP = lambda net: ("TP", "Connector:TestPoint", net, FP_TP, {"1": net}, {})
NC = None   # pin intentionally not connected (gets a no-connect flag)

SHEETS = []


def sheet(title, filename, note, parts):
    SHEETS.append(dict(title=title, file=filename, note=note, parts=parts))


# --------------------------------------------------------------------------- power
sheet("Power", "power.kicad_sch",
      "POWER & CONNECTORS. J1 = main board (spec v1.3), J2 = FTDI console. Two LM66100 ideal diodes OR the two\n"
      "5 V inputs with ~25 mV drop (a Schottky would cost 350 mV of LED headroom). F1 protects the cable,\n"
      "D1 clamps surges, FB1 + C2 keep the LED current steps on the board. U3 makes 3.3 V (also the ADC reference).",
      [
    ("J", "Connector_Generic:Conn_01x04", "MAIN JST-PH 4", "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
     {"1": "GND", "2": "5V_MAIN", "3": "SDA", "4": "SCL"}, {"MPN": "JST B4B-PH-K-S"}),
    ("J", "Connector_Generic:Conn_01x06", "FTDI 3V3", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
     {"1": "GND", "2": NC, "3": "5V_FTDI", "4": "UART_RX", "5": "UART_TX", "6": NC}, {}),
    ("U", "Power_Management:LM66100DCK", "LM66100DCK", "Package_TO_SOT_SMD:SOT-363_SC-70-6",
     {"1": "5V_MAIN", "2": "GND", "3": "GND", "4": NC, "5": NC, "6": "5V_OR"}, {"MPN": "TI LM66100DCKR"}),
    ("U", "Power_Management:LM66100DCK", "LM66100DCK", "Package_TO_SOT_SMD:SOT-363_SC-70-6",
     {"1": "5V_FTDI", "2": "GND", "3": "GND", "4": NC, "5": NC, "6": "5V_OR"}, {"MPN": "TI LM66100DCKR"}),
    C("1u", "5V_MAIN", "GND"),
    C("1u", "5V_FTDI", "GND"),
    ("F", "Device:Polyfuse", "1.1A hold", "Fuse:Fuse_1812_4532Metric_Pad1.30x3.40mm_HandSolder",
     {"1": "5V_OR", "2": "+5V"}, {"MPN": "Bourns MF-MSMF110-2"}),
    ("D", "Diode:SMAJ5.0A", "SMAJ5.0A", "Diode_SMD:D_SMA_Handsoldering",
     {"1": "+5V", "2": "GND"}, {"MPN": "Littelfuse SMAJ5.0A"}),
    C("10u", "+5V", "GND"),
    ("FB", "Device:FerriteBead", "220R@100MHz 2A", "Inductor_SMD:L_0805_2012Metric_Pad1.05x1.20mm_HandSolder",
     {"1": "+5V", "2": "5V_LED"}, {"MPN": "Murata BLM21PG221SN1D"}),
    ("C", "Device:C_Polarized", "220u 10V", "Capacitor_SMD:CP_Elec_6.3x7.7",
     {"1": "5V_LED", "2": "GND"}, {"MPN": "Panasonic EEE-FK1A221P"}),
    C("10u", "5V_LED", "GND"),
    ("U", "Regulator_Linear:TLV75533PDBV", "TLV75533PDBV", FP_SOT23_5,
     {"1": "+5V", "2": "GND", "3": "+5V", "4": NC, "5": "+3V3"}, {"MPN": "TI TLV75533PDBVR"}),
    C("1u", "+5V", "GND"),
    C("1u", "+3V3", "GND"),
    ("U", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6_Handsoldering",
     {"1": "SDA", "6": "SDA", "3": "SCL", "4": "SCL", "2": "GND", "5": "+3V3"}, {"MPN": "ST USBLC6-2SC6"}),
    R("4k7", "SDA", "+3V3", DNP=True),
    R("4k7", "SCL", "+3V3", DNP=True),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "5V_MAIN"}, {}),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "5V_FTDI"}, {}),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "GND"}, {}),
    ("PWR", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "+5V"}, {}),
    TP("+5V"), TP("5V_LED"), TP("+3V3"), TP("GND"), TP("SDA"), TP("SCL"),
])

# --------------------------------------------------------------------------- MCU
sheet("MCU", "mcu.kicad_sch",
      "MCU STM32C031F6P6 (TSSOP-20). Pin map: docs/design-synthesis.md §5. Pin 16 = PA9 (TIM1_CH2, GATE) and\n"
      "pin 17 = PA12 (status LED) need the SYSCFG remap (CubeMX). J3 = 10-pin Cortex debug (ST-LINK).\n"
      "JP1 open = I2C address 0x2A, closed = 0x2B. C at VDD: 100 nF right at the pin + 4.7 uF bulk.",
      [
    ("U", "MCU_ST_STM32C0:STM32C031F6Px", "STM32C031F6P6", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
     {"4": "+3V3", "5": "GND", "6": "NRST", "7": "PD_ADC", "8": "I_MON", "9": "UART_TX", "10": "UART_RX",
      "11": "T_LED", "12": "V_HEAD", "13": "V_IN", "14": "ARM_OK", "15": "SET_PWM", "16": "GATE",
      "17": "STATUS_LED", "18": "SWDIO", "19": "SWCLK", "20": "SCL", "1": "SDA", "2": "ADDR_SEL", "3": NC},
     {"MPN": "ST STM32C031F6P6"}),
    C("100n", "+3V3", "GND"),
    C("4u7", "+3V3", "GND"),
    C("100n", "NRST", "GND"),
    ("J", "Connector:Conn_ARM_JTAG_SWD_10", "SWD", "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD",
     {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND", "6": NC, "7": NC, "8": NC, "9": "GND",
      "10": "NRST"}, {}),
    ("JP", "Jumper:SolderJumper_2_Open", "ADDR 0x2B", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "ADDR_SEL", "2": "GND"}, {}),
    R("1k", "STATUS_LED", "LED_STAT_A"),
    ("D", "Device:LED", "green", "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder",
     {"1": "GND", "2": "LED_STAT_A"}, {}),
])

# --------------------------------------------------------------------------- LED driver
sheet("LED driver", "led_driver.kicad_sch",
      "LED DRIVER: linear current sink, I_LED = V(SET_G) / R_sense, 0..100 mV -> 0..303 mA (hardware max).\n"
      "PWM 47 kHz -> 2-pole RC (160 Hz) with divider. U6 disconnects the setpoint (dark gaps / off) without\n"
      "disturbing the filter. U7: LED enabled only if GATE (MCU) AND ARM_OK (manual ARM switch on J6).\n"
      "NT1 = net tie: Kelvin sense taken at the R_sense pad. Compensation R/C: tune with simulation S2.",
      [
    R("10k", "SET_PWM", "SET_RC1"),
    C("100n", "SET_RC1", "GND"),
    R("22k", "SET_RC1", "SET_F"),
    R("1k", "SET_F", "GND"),
    C("1u", "SET_F", "GND"),
    ("U", "74xGxx:74LVC1G66", "74LVC1G66", FP_SOT23_5, {"1": "SET_F", "2": "SET_G", "4": "EN_LED"},
     {"MPN": "TI SN74LVC1G66DBVR", "unit": 1}),
    ("U", "74xGxx:74LVC1G66", "74LVC1G66", FP_SOT23_5, {"3": "GND", "5": "+3V3"}, {"unit": 2, "same_as_prev": True}),
    R("100k", "SET_G", "GND"),
    ("U", "74xGxx:74LVC1G08", "74LVC1G08", FP_SOT23_5, {"1": "GATE", "2": "ARM_OK", "3": "GND", "4": "EN_LED",
                                                         "5": "+3V3"}, {"MPN": "TI SN74LVC1G08DBVR"}),
    R("10k", "GATE", "GND"),
    R("100k", "EN_LED", "GND"),
    ("J", "Connector_Generic:Conn_01x02", "UV ARM switch", "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
     {"1": "+3V3", "2": "ARM_OK"}, {"MPN": "JST B2B-PH-K-S"}),
    R("10k", "ARM_OK", "GND"),
    C("100n", "ARM_OK", "GND"),
    ("U", "Amplifier_Operational:OPA2333xxDGK", "OPA2388IDGK", "Package_SO:VSSOP-8_3x3mm_P0.65mm",
     {"3": "SET_G", "2": "FB_I", "1": "GATE_DRV"}, {"MPN": "TI OPA2388IDGKR", "unit": 1}),
    ("U", "Amplifier_Operational:OPA2333xxDGK", "OPA2388IDGK", "Package_SO:VSSOP-8_3x3mm_P0.65mm",
     {"5": "ISENSE_K", "6": "FB_M", "7": "I_MON_RAW"}, {"unit": 2, "same_as_prev": True}),
    ("U", "Amplifier_Operational:OPA2333xxDGK", "OPA2388IDGK", "Package_SO:VSSOP-8_3x3mm_P0.65mm",
     {"8": "+5V", "4": "GND"}, {"unit": 3, "same_as_prev": True}),
    C("100n", "+5V", "GND"),
    R("100", "GATE_DRV", "Q1_G"),
    R("1k", "ISENSE_K", "FB_I"),
    C("4n7", "GATE_DRV", "FB_I"),
    R("100k", "Q1_G", "GND"),
    ("Q", "Transistor_FET:NDT3055L", "NDT3055L", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
     {"1": "Q1_G", "2": "DRAIN", "3": "ISENSE"}, {"MPN": "onsemi NDT3055L"}),
    ("R", "Device:R", "0R33 1% 0.25W", "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder",
     {"1": "ISENSE", "2": "GND"}, {"MPN": "Yageo RL1206FR-070R33L"}),
    ("NT", "Device:NetTie_2", "Kelvin", "NetTie:NetTie-2_SMD_Pad0.5mm", {"1": "ISENSE", "2": "ISENSE_K"}, {}),
    R("24k", "I_MON_RAW", "FB_M"),
    R("1k", "FB_M", "GND"),
    R("100", "I_MON_RAW", "I_MON"),
    C("10n", "I_MON", "GND"),
    ("J", "Connector_Generic:Conn_01x02", "LED star", "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm",
     {"1": "5V_LED", "2": "DRAIN"}, {"in_bom": False}),
    TP("SET_F"), TP("SET_G"), TP("GATE"), TP("ISENSE"), TP("DRAIN"),
])

# --------------------------------------------------------------------------- photodiode + monitors
sheet("Photodiode and monitors", "analog.kicad_sch",
      "PHOTODIODE TIA: V(PD_OUT) = 0.1 V + I_pd x 1 MOhm, bandwidth ~ 1/(2 pi Rf Cf) ~ 70 kHz. The +0.1 V bias\n"
      "keeps the output off the 0 V rail so (LED on - LED off) stays linear. D4 (DNP) = alternative detector\n"
      "(385-395 nm LED as photodiode) in parallel with D3. Dividers /2 for V_HEAD and V_IN; NTC divider for T_LED.",
      [
    ("D", "Sensor_Optical:BPW34-SMD", "BPW 34 BS", "OptoDevice:Osram_BPW34S-SMD", {"1": "TIA_IN", "2": "GND"},
     {"MPN": "ams OSRAM BPW 34 BS"}),
    ("D", "Connector_Generic:Conn_01x02", "ALT DETECTOR (K,A)", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "TIA_IN", "2": "GND"}, {"DNP": True}),
    ("U", "Amplifier_Operational:TLV9061xDBV", "TLV9061IDBV", FP_SOT23_5,
     {"4": "TIA_IN", "3": "PD_VREF", "1": "PD_OUT", "5": "+3V3", "2": "GND"}, {"MPN": "TI TLV9061IDBVR"}),
    C("100n", "+3V3", "GND"),
    R("1M", "PD_OUT", "TIA_IN"),
    C("2p2 C0G", "PD_OUT", "TIA_IN"),
    R("330k", "+3V3", "PD_VREF"),
    R("10k", "PD_VREF", "GND"),
    C("100n", "PD_VREF", "GND"),
    R("100", "PD_OUT", "PD_ADC"),
    C("1n", "PD_ADC", "GND"),
    ("J", "Connector_Generic:Conn_01x02", "NTC 10k", "Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm",
     {"1": "T_LED", "2": "GND"}, {"MPN": "Murata NXFT15XH103FA2B (on the star)", "in_bom": False}),
    R("10k 0.1%", "+3V3", "T_LED"),
    C("100n", "T_LED", "GND"),
    R("100k", "DRAIN", "V_HEAD"),
    R("100k", "V_HEAD", "GND"),
    C("10n", "V_HEAD", "GND"),
    R("100k", "5V_LED", "V_IN"),
    R("100k", "V_IN", "GND"),
    C("10n", "V_IN", "GND"),
    TP("PD_OUT"), TP("GND"),
])
