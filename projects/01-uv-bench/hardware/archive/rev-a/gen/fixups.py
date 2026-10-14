#!/usr/bin/env python3
"""Hand-routed finishing touches after the autorouter (run after route.py, before silk.py).

Autorouters usually leave a few connections for a human. Each fix here is one explicit track,
with the reason, so it can be reviewed like any other design decision. After adding tracks the
GND pours are refilled (they must flow around the new copper).
Run:  ~/Applications/kicad-10.0.7/bin/python3.11 fixups.py
"""
import os, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "uv-bench", "uv-bench.kicad_pcb")
mm, MM = pcbnew.FromMM, pcbnew.ToMM


def pad(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    return next(p for p in fp.Pads() if p.GetNumber() == num)


def finish_to_pad(board, ref, num, width=0.4, reach=3.0):
    """Connect the nearest dangling track end of the pad's net (same layer) straight to the pad."""
    p = pad(board, ref, num)
    c, net = p.GetPosition(), p.GetNet()
    for t in board.GetTracks():                     # already fixed (script re-run)? nothing to do
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == net.GetNetCode() and c in (t.GetStart(), t.GetEnd()):
            return f"{ref}.{num}: already connected"
    best = None
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetCode() != net.GetNetCode() or t.GetLayer() != pcbnew.F_Cu:
            continue
        for e in (t.GetStart(), t.GetEnd()):
            d = MM((e - c).EuclideanNorm())
            if 0.05 < d < reach and (best is None or d < best[0]):
                best = (d, e)
    if best is None:
        return f"{ref}.{num}: no track end within {reach} mm"
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(best[1]); tr.SetEnd(c); tr.SetWidth(mm(width)); tr.SetLayer(pcbnew.F_Cu); tr.SetNet(net)
    board.Add(tr)
    return f"{ref}.{num}: added {best[0]:.2f} mm track, {width} mm wide"


FIXES = [
    # U8 pin 8 (+5V supply of the dual op-amp): Freerouting brought +5V to 1.5 mm of the pin but
    # never closed it. 0.4 mm instead of the Power-class 0.6 mm so it clears pin 7 (0.65 mm pitch);
    # it carries only the op-amp's ~2 mA.
    ("U8", "8", 0.4),
]

def heatsink_zone(board, ref="Q1", grow=2.5):
    """Copper area on the MOSFET tab (drain), higher priority than GND, on both layers + vias.
    SOT-223 on its bare pad is ~100+ K/W; a few cm2 of copper brings it to ~60 K/W."""
    tab = max(board.FindFootprintByReference(ref).Pads(), key=lambda p: p.GetBoundingBox().GetArea())
    bb = tab.GetBoundingBox()
    x0, y0 = max(MM(bb.GetLeft()) - grow, 100.6), max(MM(bb.GetTop()) - grow, 100.6)
    x1, y1 = MM(bb.GetRight()) + grow, MM(bb.GetBottom()) + 0.2
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(tab.GetNet()); z.SetAssignedPriority(5)
        z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mm(x), mm(y))
        z.SetZoneName(f"{ref} heatsink")
        board.Add(z)
    # thermal vias to the bottom copper, just beside the tab (not in the pad: vias in a pad wick the
    # solder away and make hand soldering harder)
    cx = (MM(bb.GetLeft()) + MM(bb.GetRight())) / 2
    for dx in (-2.0, 0.0, 2.0):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(cx + dx), mm(MM(bb.GetTop()) - 1.1)))
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(tab.GetNet())
        board.Add(v)
    # GND stitching vias that fall inside the heatsink area become extra thermal vias
    moved = 0
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND":
            px, py = MM(t.GetPosition().x), MM(t.GetPosition().y)
            if x0 - 0.6 < px < x1 + 0.6 and y0 - 0.6 < py < y1 + 0.6:
                t.SetNet(tab.GetNet()); moved += 1
    return f"{ref}: heatsink zone {x1 - x0:.1f} x {y1 - y0:.1f} mm on F.Cu and B.Cu, 3 thermal vias (+{moved} re-netted)"


if __name__ == "__main__":
    board = pcbnew.LoadBoard(PCB)
    for ref, num, w in FIXES:
        print(finish_to_pad(board, ref, num, w))
    if not any(z.GetZoneName() == "Q1 heatsink" for z in board.Zones()):
        print(heatsink_zone(board))
    else:                                            # re-run: only re-net GND vias inside the area
        print(heatsink_zone.__name__, "already present")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
