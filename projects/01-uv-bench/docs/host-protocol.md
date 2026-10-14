# PC ↔ UV bench text protocol (draft v0.2)

The text command language used to control the UV bench from a PC (Python, a terminal, later
a GUI). It is the companion of [`interface-spec.md`](interface-spec.md), which defines the
connector and the I2C register map.

## 1. The communication paths

The UV bench has its own MCU (since 2026-10-09). The same commands therefore reach it by two routes:

```
 (a) Standalone, now:
 PC ──USB──► USB-serial cable (3.3 V, FTDI pinout) ──UART──► UV bench MCU
              (/dev/ttyUSB0)                                  text parser ─► control functions

 (b) In the instrument, later:
 PC ──USB──► Main board (project 03) ──I2C registers──► UV bench MCU
              USB CDC (/dev/ttyACM0)                      register handler ─► same control functions
              same text commands, translated
              by the main board into register writes
```

**Key point: the PC always sees a serial port and sends the same text commands.** Python
code written for route (a) keeps working for route (b). Only the port name changes.

| Route | PC side | Who parses the text |
|---|---|---|
| (a) USB-serial cable to the UV board's FTDI header | `/dev/ttyUSB0`, 115200 8N1 | UV bench MCU |
| M1 breadboard: Nucleo-C031C6 running the bench firmware | ST-LINK virtual COM port `/dev/ttyACM0` | Nucleo (same firmware) |
| (b) Main board | Native USB CDC `/dev/ttyACM0` | Main board, which forwards `LED:*` commands to the bench as I2C register accesses |

On Linux, add yourself to the `dialout` group for port access.

## 2. Why a text protocol (SCPI-like)

- Readable and typeable from a terminal (`picocom /dev/ttyACM0`), which makes it trivial to debug.
- **SCPI** is the standard command language of lab instruments (oscilloscopes, power
  supplies, generators). The same style and the same Python tools (PyVISA) then work for your instruments and your own boards.
- Data rate is tiny (a few commands per second), so text overhead doesn't matter.
- Later, fast data streams (the 4 acquisition channels of project 03) get a
  separate **binary framed** mode (COBS framing + CRC16). See §6.

## 3. Framing rules

- Line based, ASCII, terminated by `\n` (`\r\n` accepted). Max 128 characters per line.
- Case-insensitive. SCPI short form (upper-case letters) or long form: `LED:CURR` = `LED:CURRENT`.
- **Every command gets exactly one reply line**: the value for a query (`?`), `OK` for a
  setting, or `ERR <code>,"<text>"`. (Strict SCPI is silent on settings; one reply per line
  is easier to debug and keeps the PC and controller in lockstep.)
- Numbers: decimal, SI base units unless noted (mA for LED current, Hz, °C, V).
- Asynchronous lines (streaming) start with `#` so the PC can tell them apart from replies.
- Serial settings: 115200 8N1 on the UART routes. USB CDC (main board) ignores the baud rate.

## 4. Command set v0.2

| Command | Reply | Meaning | I2C register |
|---|---|---|---|
| `*IDN?` | `LAB,UVBENCH,<serial>,<fw-version>` | Identification | WHO_AM_I, FW_VERSION |
| `*RST` | `OK` | LED off, fault cleared, defaults restored | CTRL |
| `SYST:ERR?` | `0,"No error"` or the oldest error | Error queue | – |
| `LED:STAT ON\|OFF` / `LED:STAT?` | `OK` / `ON\|OFF` | Enable (still subject to the interlock) | CTRL.ENABLE |
| `LED:MODE CURR\|POW` / `?` | | CURR = open-loop current, POW = regulated optical power | CTRL.MODE |
| `LED:POW <mW or %>` / `?` | | Optical power target (mW if calibrated, else % of full scale) | SETPOINT_POWER |
| `LED:CURR <mA>` / `?` | | Current in CURR mode; current *limit* in POW/MOD | SETPOINT_CURRENT |
| `LED:RAMP <%/s>` / `?` | | Soft start / ramp rate | RAMP_RATE |
| `SYST:WDOG <s>` / `?` | | Turn the LED off if no command for N s (0 = off) | WATCHDOG |
| `MEAS?` | `<pow>,<i_mA>,<t_C>,<vhead_mV>,<vin_mV>,<status>` | Snapshot | 0x10–0x18, STATUS |
| `MEAS:POW?` / `MEAS:CURR?` / `MEAS:TEMP?` / `MEAS:VHEAD?` / `MEAS:AMB?` / `MEAS:RAW?` | value | Individual measurements | MEAS_* |
| `STAT?` | integer | STATUS bit field (see interface spec §4) | STATUS |
| `CAL:GAIN <uW_per_1000counts>` / `?`, `CAL:SAVE` | | Calibration against a reference power meter | CAL_GAIN, CAL_SAVE |
| `STRM <rate_Hz>` / `STRM 0` | `OK` | Stream `#<t_ms>,<pow>,<i_mA>,<t_C>,<status>` lines (UART route only) | – |

Error codes: `-100` unknown command, `-200` value out of range, `-300` hardware fault /
bench not responding, `-400` interlock open, `-500` busy.

Safety: `LED:STAT ON` is refused (`-400`) while the UV ARM switch is off. Any fault forces the LED off
and latches a `STAT?` bit until `*RST`.

## 5. Example session and minimal Python client

```
> *IDN?
< LAB,UVBENCH,0001,0.1.0
> LED:MODE POW
< OK
> LED:POW 40
< OK
> LED:STAT ON
< OK
> MEAS?
< 40.0,182.4,31.5,820,4975,67
```

```python
import serial

class UVBench:
    def __init__(self, port="/dev/ttyUSB0"):
        self.s = serial.Serial(port, 115200, timeout=1)

    def cmd(self, line: str) -> str:
        self.s.write((line + "\n").encode())
        while True:
            reply = self.s.readline().decode().strip()
            if not reply.startswith("#"):          # skip streamed lines
                break
        if reply.startswith("ERR"):
            raise RuntimeError(f"{line!r}: {reply}")
        return reply

    def measure(self):
        pw, i, t, vh, vin, st = self.cmd("MEAS?").split(",")
        return dict(power=float(pw), i_mA=float(i), t_C=float(t),
                    vhead_mV=float(vh), vin_mV=float(vin), status=int(st))

bench = UVBench()
print(bench.cmd("*IDN?"))
bench.cmd("LED:MODE POW"); bench.cmd("LED:POW 40"); bench.cmd("LED:STAT ON")
print(bench.measure())
```

## 6. Future: binary stream mode (projects 02/03)

For sample streams (> ~1 kSa/s), the text mode switches into a binary mode with `STRM:BIN`:
packets `[type, seq, payload…, CRC16]`, COBS-encoded with a `0x00` delimiter, so the PC can
resynchronise after any lost byte. This is defined when the acquisition chain exists.

## Change log
- v0.1 (2026-10-09): first draft (controller-side regulation).
- v0.2 (2026-10-09): the bench MCU parses the commands itself (UART route); power-based commands; mapping to I2C registers.
