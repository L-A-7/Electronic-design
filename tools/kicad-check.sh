#!/usr/bin/env bash
# Run ERC + DRC and generate fabrication outputs for a KiCad project.
# Usage: tools/kicad-check.sh projects/01-uv-bench/hardware/uv-bench
#        (path to the project without extension; expects .kicad_sch and .kicad_pcb)
# Exit code is non-zero if ERC or DRC report violations.
set -uo pipefail

# Which kicad-cli to use: $KICAD_CLI if set (e.g. the one inside an extracted KiCad 10 AppImage),
# otherwise the one on PATH. Prints its version so the report says which KiCad checked the board.
KCLI="${KICAD_CLI:-kicad-cli}"
command -v "$KCLI" >/dev/null || { echo "kicad-cli not found (set KICAD_CLI)"; exit 2; }
echo "== Using $KCLI, KiCad $("$KCLI" version)"

base="${1:?usage: $0 path/to/project_basename}"
sch="$base.kicad_sch"
pcb="$base.kicad_pcb"
out="$(dirname "$base")/output"
mkdir -p "$out/gerbers" "$out/reports"

status=0

if [[ -f "$sch" ]]; then
    echo "== ERC"
    "$KCLI" sch erc --severity-all --exit-code-violations \
        -o "$out/reports/erc.rpt" "$sch" || { echo "ERC violations: see $out/reports/erc.rpt"; status=1; }
    "$KCLI" sch export pdf -o "$out/schematic.pdf" "$sch" >/dev/null
    "$KCLI" sch export bom -o "$out/bom.csv" \
        --fields 'Reference,Value,Footprint,MPN,${QUANTITY},${DNP}' \
        --labels 'Refs,Value,Footprint,MPN,Qty,DNP' \
        --group-by 'Value,Footprint,MPN' "$sch" >/dev/null
fi

if [[ -f "$pcb" ]]; then
    echo "== DRC (with schematic parity)"
    "$KCLI" pcb drc --severity-all --schematic-parity --exit-code-violations \
        -o "$out/reports/drc.rpt" "$pcb" || { echo "DRC violations: see $out/reports/drc.rpt"; status=1; }
    echo "== Fabrication outputs"
    rm -f "$out"/gerbers/*
    "$KCLI" pcb export gerbers -o "$out/gerbers/" \
        --layers 'F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts' \
        --subtract-soldermask "$pcb" >/dev/null
    "$KCLI" pcb export drill   -o "$out/gerbers/" "$pcb" >/dev/null
    (cd "$out/gerbers" && rm -f ../gerbers.zip && zip -q ../gerbers.zip ./*) && echo "   gerbers.zip ready for upload"
    "$KCLI" pcb export pos --format csv --units mm -o "$out/positions.csv" "$pcb" >/dev/null
    "$KCLI" pcb export step --subst-models -o "$out/board.step" "$pcb" >/dev/null 2>&1 \
        || echo "(STEP export skipped/failed)"
fi

[[ $status -eq 0 ]] && echo "== All checks passed. Outputs in $out" || echo "== Checks FAILED"
exit $status
