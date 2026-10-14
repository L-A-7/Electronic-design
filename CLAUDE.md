# Context for Claude

- Purpose: a learning and design workspace for electronics and PCB design, with progressive projects (see [README.md](README.md) roadmap).
- User background: physics training. Comfortable with op-amps, passives, Fourier/filters, Python/Matlab, STM32 CubeIDE, Arduino/ESP32, basic KiCad. Goals: master KiCad, design principles, simulation before fab, physical testing, I2C/SPI/UART.
- Tools on this machine: **KiCad 10.0.7**, official AppImage from kicad.org, extracted in `~/Applications/kicad-10.0.7` (launcher `AppRun`, shell alias `kicad10`, `.kicad_pro` files open with it). Its `kicad-cli` is `$KICAD_CLI` (set in ~/.bashrc, used by `tools/kicad-check.sh`); its Python with `pcbnew` is `~/Applications/kicad-10.0.7/bin/python3.11`; libraries (symbols as `.kicad_symdir`), footprints, 3D models and ngspice are bundled under `share/kicad`. The Debian KiCad 9 packages were removed 2026-10-12. FreeCAD, Python (pyenv), git.
- Explain the *why* behind design choices; the user wants to learn, not only to get a result.
- Interface between boards: [`projects/01-uv-bench/docs/interface-spec.md`](projects/01-uv-bench/docs/interface-spec.md) is the contract. Version every change to it.
- Before any board goes to fabrication: `tools/kicad-check.sh <project_basename>` must pass, plus the manual checklist in that project's verification plan.
- KiCad files are S-expressions. Never hand-edit `.kicad_sch`/`.kicad_pcb` while KiCad has them open.
