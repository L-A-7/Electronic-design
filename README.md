# Electronic design: workspace and roadmap

This workspace is for building a reliable, repeatable toolchain for PCB design. Each project
takes one step up in complexity, and each one has to be useful on its own.

## Layout

| Folder | Content |
|---|---|
| `projects/` | One folder per board: `docs/ hardware/ simulation/ firmware/ test/` |
| `library/` | Shared KiCad library (symbols, footprints, 3D models) for parts that aren't in the stock libs |
| `templates/` | KiCad project template (fab design rules, title block, net classes) |
| `tools/` | Scripts: ERC/DRC/fabrication exports through `kicad-cli`, simulation helpers |
| `learning/` | Notes and small exercises: [protocols](learning/protocols/README.md), [UV safety](learning/uv-safety.md), KiCad, circuit topics |
| `resources/` | Datasheets and application notes (stored locally, git-ignored if large) |
| `books/` | Reading notes |
| [`lab/`](lab/README.md) | Instrument inventory, purchase plan, measurement procedures |

## Toolchain

| Step | Tool | Status |
|---|---|---|
| Version control | git (one repo, one commit per meaningful design step) | initialised |
| Schematic / PCB | KiCad 9.0.8 | installed |
| Circuit simulation | ngspice inside the KiCad schematic editor (libngspice present); vendor SPICE models | available |
| Parameter sweeps | Python (`spicelib` or `PySpice`) driving ngspice | to do |
| Automated checks and exports | `tools/kicad-check.sh` (ERC, DRC, Gerbers, drill, BOM, position, PDF, STEP) | written |
| Mechanical fit | STEP export, then FreeCAD (installed) | available |
| Firmware | STM32CubeIDE / CubeMX on a **Nucleo** board until our own controller exists | to do |
| Protocol debugging | Logic analyser + sigrok/PulseView | to buy, see [`lab/`](lab/README.md) |
| Fabrication | JLCPCB / PCBWay (cheap PCBA) or Aisler (EU) | choose at milestone M4 |

## Roadmap

| # | Project | Main new skills | Useful because |
|---|---|---|---|
| 1 | **UV LED bench board** ([`projects/01-uv-bench`](projects/01-uv-bench/README.md)) | Power input protection, linear constant-current driver, photodiode TIA, **small STM32 on board** (control loop, I2C target, UART console), op-amp stability simulation, first full fab-and-test cycle | Self-regulating UV source: ask for a power, it holds it. Driven from a PC (USB-serial cable) now, from the main board over I2C later |
| 2 | *(optional, later)* **Small STM32 USB controller** ([`projects/02-usb-controller`](projects/02-usb-controller/README.md)) | STM32 minimum system, USB-C FS device, SWD, crystal, USB CDC firmware | Drives the UV bench from a PC. Proves the USB + STM32 layout cheaply before the large board |
| 3 | **Main STM32 board** ([`projects/03-main-board`](projects/03-main-board/README.md)) | USB-C PD power, stepper driver, 4 analogue acquisition channels, temperature, DACs, mixed-signal layout | The instrument controller |

Each project goes through the same milestones: **M0** toolchain, **M1** breadboard proof,
**M2** schematic and simulation, **M3** layout and review, **M4** fabrication, **M5** bring-up
and characterisation, **M6** firmware and documentation.

## Conventions

- Projects are numbered: `NN-short-name`.
- Hardware revisions are lettered (Rev A, Rev B). Tag them in git: `uv-bench-revA-fab`.
- Every design decision goes in the project `docs/` with its reasoning.
- Nothing goes to fabrication until `tools/kicad-check.sh` passes and the review checklist is done.
