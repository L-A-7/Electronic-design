#!/usr/bin/env python3
"""Silkscreen cleanup: put every reference designator where it is readable and touches nothing.

For each footprint, the reference text (0.8 mm, 0.15 mm stroke = JLC minimum) is tried above,
below, left and right of the part's courtyard. The first spot that overlaps no pad, no other text
and stays on the board wins. If none fits, the reference moves to the F.Fab layer (it stays
visible in KiCad, in the assembly drawing and in the interactive BOM, but isn't printed).
Run after route.py:  ~/Applications/kicad-10.0.7/bin/python3.11 silk.py
"""
import os, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "uv-bench", "uv-bench.kicad_pcb")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
SIZE, THICK, GAP = 0.8, 0.15, 0.15


def box(b, grow=0.0):
    return (MM(b.GetLeft()) - grow, MM(b.GetTop()) - grow, MM(b.GetRight()) + grow, MM(b.GetBottom()) + grow)


def hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def on_board(b):
    if b[0] < 100.3 or b[1] < 100.3 or b[2] > 169.7 or b[3] > 154.7:
        return False
    nx, ny = min(max(122, b[0]), b[2]), min(max(127.5, b[1]), b[3])
    return math.hypot(nx - 122, ny - 127.5) > 11.3


def main():
    board = pcbnew.LoadBoard(PCB)
    pads = [box(p.GetBoundingBox(), 0.1) for fp in board.GetFootprints() for p in fp.Pads()]
    pads += [box(t.GetBoundingBox(), 0.05) for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    taken, moved, fab = [], 0, 0
    for fp in board.GetFootprints():                 # footprint silk drawings (outlines, pin-1 marks)
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and not isinstance(g, pcbnew.PCB_TEXT):
                taken.append(box(g.GetBoundingBox(), 0.1))
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            taken.append(box(d.GetBoundingBox(), 0.1))
    for fp in board.GetFootprints():
        ref = fp.Reference()
        if fp.IsBoardOnly():
            ref.SetVisible(False)
            continue
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetTextSize(pcbnew.VECTOR2I(mm(SIZE), mm(SIZE)))
        ref.SetTextThickness(mm(THICK))
        ref.SetKeepUpright(True)
        ref.SetTextAngleDegrees(0)
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        cb = box(cy.BBox()) if cy.OutlineCount() else box(fp.GetBoundingBox(False))
        cx, cyy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
        w = len(fp.GetReference()) * SIZE * 0.75 + 0.2
        h = SIZE + 0.2
        cands = [(cx, cb[1] - h / 2 - GAP), (cx, cb[3] + h / 2 + GAP),
                 (cb[0] - w / 2 - GAP, cyy), (cb[2] + w / 2 + GAP, cyy),
                 (cx, cb[1] - h / 2 - GAP - 0.6), (cx, cb[3] + h / 2 + GAP + 0.6)]
        done = False
        for x, y in cands:
            tb = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if on_board(tb) and not any(hit(tb, p) for p in pads) and not any(hit(tb, t) for t in taken):
                ref.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                ref.SetVisible(True)
                taken.append(tb); moved += 1; done = True
                break
        if not done:
            ref.SetLayer(pcbnew.F_Fab); fab += 1
    pcbnew.SaveBoard(PCB, board)
    print(f"references on silk: {moved}, moved to F.Fab: {fab}")


if __name__ == "__main__":
    main()
