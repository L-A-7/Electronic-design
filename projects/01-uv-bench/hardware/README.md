# UV bench: KiCad projects (Rev C + sensor head)

| Folder | Content |
|---|---|
| `uv-bench/` | The main board, KiCad 10: open `uv-bench/uv-bench.kicad_pro`. Rev C = Rev B + the remote-photodiode input J4 |
| `pd-head/` | The remote photodiode head (12 × 21 mm, SFH 2401 + 2 wire pads), its own project and Gerbers |
| `gen/` | The scripts that **generate** the schematic and the board: `design.py` (the circuit), `layout.py` (how the schematic is drawn), `placement.py` (where the parts go on the board). The head has its own three: `design_head.py`, `layout_head.py`, `placement_head.py` |
| `fab/` | The exact Gerbers sent to the board house, one folder per order (`2026-10-15-jlcpcb/`: Rev C + head, tag `uv-bench-revC-ordered`) |
| `archive/rev-a/` | Rev A (71 parts, 4 sheets), project + scripts as they were on 2026-10-13. Self-contained, for reference |

- How and why, block by block, plus the KiCad notes (§8): [`docs/rev-b-simple.md`](../docs/rev-b-simple.md).
- Generated parts list with nets: [`docs/parts-list.md`](../docs/parts-list.md).

## Regenerate (KiCad closed)

```bash
cd projects/01-uv-bench/hardware/gen
python3 gen_sch.py                                      # design.py + layout.py -> schematic (1 sheet), parts list, netlist check
~/Applications/kicad-10.0.7/bin/python3.11 gen_pcb.py   # netlist -> footprints, nets, placement
~/Applications/kicad-10.0.7/bin/python3.11 route.py     # Freerouting (~1 min), spur clean-up, GND pours, stitching vias
~/Applications/kicad-10.0.7/bin/python3.11 silk.py      # reference designators placed legibly
cd ../../../.. && tools/kicad-check.sh projects/01-uv-bench/hardware/uv-bench/uv-bench
```

**The sensor head** uses the same two generators, pointed at its own design module. It has two
hand-placed tracks, so no autorouter:

```bash
cd projects/01-uv-bench/hardware/gen
UVB_DESIGN=design_head python3 gen_sch.py
UVB_DESIGN=design_head ~/Applications/kicad-10.0.7/bin/python3.11 gen_pcb.py
cd ../../../.. && tools/kicad-check.sh projects/01-uv-bench/hardware/pd-head/pd-head
```

- **The autorouter isn't deterministic.** Each run gives a slightly different, equally valid
  routing. Always finish with `kicad-check.sh`.
- **Build a copy without touching the project:** set `UVB_PRJ=/some/dir/uv-bench` (a folder
  holding a copy of the `.kicad_pro`, `.kicad_dru` and lib tables). All scripts honour it.
- **Once you edit the PCB by hand, stop using `gen_pcb.py` and `route.py`.** They rebuild the
  board from scratch. From then on the schematic → PCB path is KiCad's *Update PCB from
  Schematic* (F8).

## Project settings (in `uv-bench.kicad_pro` / `.kicad_dru`)

| Item | Where in KiCad | Value |
|---|---|---|
| Board | Edge.Cuts | 58 × 32 mm, corners rounded R 3.5 mm (centred on the M3 holes), Ø 22 mm cut-out centred at (113, 116) for the LED star, 4 × M3 holes. Sensor head: 12 × 21 mm, R 1.5 mm |
| Design rules | Board Setup → Constraints | JLCPCB 2-layer standard with margin: 0.15 mm track/space, vias 0.6/0.3 mm, copper-to-edge 0.3 mm |
| Custom rules | Board Setup → Custom Rules | PTH annular ≥ 0.2 mm, silkscreen text ≥ 0.8 mm, **PD tracks ≥ 0.5 mm from PWM tracks** |
| Net classes | Board Setup → Net Classes | `Power` 0.5 mm (`+5V`, `LED_K`, `I_MON`); `Analog` (`PD`); `Noisy` (`PWM`, `UART_*`); Default 0.25 mm |
| Zones | F.Cu and B.Cu | GND pours + keepouts around the cut-out and along the edges |

**Never edit these files with a text editor or a script while KiCad has them open.**
