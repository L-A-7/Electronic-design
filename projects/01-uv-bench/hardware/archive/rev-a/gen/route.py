#!/usr/bin/env python3
"""Route the UV bench PCB (KiCad 10 Python + Freerouting), then pour and stitch the ground.

Method (docs/design-notes.md §Routing):
1. A keepout ring around the LED cut-out, then export to Specctra DSN (the autorouter format).
2. Freerouting routes everything else, honouring the net-class widths (Power 0.6 mm) and clearances.
3. The session file (SES) is imported back. GND zones (pours) are added on F.Cu and B.Cu on top of the
   routed GND tracks, plus a grid of stitching vias that ties the two pours together.
4. Zones are filled and the board is saved; run kicad-check.sh afterwards (DRC must be clean).
Run with KiCad closed:  ~/Applications/kicad-10.0.7/bin/python3.11 route.py
"""
import os, re, subprocess, sys, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "uv-bench", "uv-bench.kicad_pcb")
DSN, SES = os.path.join(HERE, "uv-bench.dsn"), os.path.join(HERE, "uv-bench.ses")
FREEROUTING = os.path.expanduser("~/Applications/freerouting/freerouting-2.1.0.jar")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
GND = "GND"


def export_dsn(board):
    assert pcbnew.ExportSpecctraDSN(board, DSN)
    s = open(DSN).read()
    # +10 um on every clearance: Freerouting rounds coordinates, KiCad then sees 0.148 instead of 0.150
    s = re.sub(r"\(clearance (\d+(?:\.\d+)?)\)", lambda m: f"(clearance {float(m.group(1)) + 10:g})", s)
    open(DSN, "w").write(s)


def autoroute(passes=100):
    if os.path.exists(SES):
        os.remove(SES)
    cmd = ["java", "-jar", FREEROUTING, "-de", DSN, "-do", SES, "-mp", str(passes), "-mt", "4", "--gui.enabled=false"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=HERE)
    if not os.path.exists(SES):
        raise SystemExit("Freerouting produced no session file")


def gnd_zone(board, layer, net):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(net)
    z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pts = [(100, 100), (170, 100), (170, 155), (100, 155)]
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(x), mm(y))
    z.SetAssignedPriority(0)
    board.Add(z)
    return z


def free_spot(board, x, y, r_via, avoid):
    for rad in [0.9 + 0.3 * k for k in range(10)]:
        for k in range(16):
            a = 2 * math.pi * k / 16
            px, py = x + rad * math.cos(a), y + rad * math.sin(a)
            if all(math.hypot(px - ax, py - ay) > ar + r_via + 0.25 for ax, ay, ar in avoid):
                return px, py
    return None


def obstacles(board):
    """Copper on any layer that a GND via must avoid: (x, y, radius) approximations."""
    obs = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            obs.append((MM(bb.Centre().x), MM(bb.Centre().y), max(MM(bb.GetWidth()), MM(bb.GetHeight())) / 2,
                        p.GetNetname()))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            obs.append((MM(t.GetPosition().x), MM(t.GetPosition().y), MM(t.GetWidth(pcbnew.F_Cu)) / 2, t.GetNetname()))
        else:
            a, b = t.GetStart(), t.GetEnd()
            n = max(1, int(MM((b - a).EuclideanNorm()) / 0.3))
            for i in range(n + 1):
                obs.append((MM(a.x + (b.x - a.x) * i / n), MM(a.y + (b.y - a.y) * i / n), MM(t.GetWidth()) / 2,
                            t.GetNetname()))
    return obs


def inside(x, y, margin=1.0):
    if not (100 + margin < x < 170 - margin and 100 + margin < y < 155 - margin):
        return False
    return math.hypot(x - 122, y - 127.5) > 11 + margin


def stitch(board, net):
    """A via next to every GND SMD pad (short path to the bottom plane), plus a stitching grid."""
    added = 0
    obs = obstacles(board)
    avoid = [(x, y, r) for x, y, r, n in obs if n != GND]
    holes = [(MM(f.GetPosition().x), MM(f.GetPosition().y), 3.6) for f in board.GetFootprints() if f.IsBoardOnly()]

    def add_via(x, y):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net)
        board.Add(v)
        avoid.append((x, y, 0.3))
    for gx in range(103, 170, 5):
        for gy in range(103, 155, 5):
            if inside(gx, gy, 1.5) and all(math.hypot(gx - ax, gy - ay) > ar + 1.0 for ax, ay, ar in avoid + holes):
                add_via(gx, gy); added += 1
    return added


def hole_keepout(board):
    """Rule area (keepout) around the LED cut-out: no tracks/vias within 0.8 mm of its edge.
    The autorouter sees keepouts in the DSN, but not the 0.3 mm copper-to-edge rule of the inner cut-out."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    ol = z.Outline(); ol.NewOutline()
    for k in range(48):
        a = 2 * math.pi * k / 48
        ol.Append(mm(122 + 11.8 * math.cos(a)), mm(127.5 + 11.8 * math.sin(a)))
    z.SetZoneName("cut-out keepout")
    board.Add(z)
    # same along the outer edge: 0.5 mm strip (the router's own edge clearance is smaller than 0.3 mm)
    for x0, y0, x1, y1 in ((100, 100, 170, 100.5), (100, 154.5, 170, 155), (100, 100, 100.5, 155), (169.5, 100, 170, 155)):
        e = pcbnew.ZONE(board)
        e.SetIsRuleArea(True); e.SetDoNotAllowTracks(True); e.SetDoNotAllowVias(True)
        e.SetDoNotAllowZoneFills(False); e.SetDoNotAllowPads(False); e.SetDoNotAllowFootprints(False)
        e.SetLayerSet(pcbnew.LSET.AllCuMask())
        ol = e.Outline(); ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mm(x), mm(y))
        e.SetZoneName("edge keepout")
        board.Add(e)


def unrouted(board):
    board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(False)


PLACED = os.path.join(HERE, "placed.kicad_pcb")     # written by gen_pcb.py: placed, no tracks, no zones


def main():
    # Always start from the placed board. (Removing tracks/zones from a loaded board is unreliable
    # in the KiCad 10 Python API, so nothing is ever removed: we reload clean copies instead.)
    import shutil
    shutil.copy(PLACED, PCB)
    board = pcbnew.LoadBoard(PCB)
    hole_keepout(board)
    pcbnew.SaveBoard(PCB, board)
    KEEP = PCB.replace(".kicad_pcb", "-keepout.kicad_pcb")
    shutil.copy(PCB, KEEP)
    export_dsn(board)
    autoroute()
    for attempt in range(3):
        shutil.copy(KEEP, PCB)                 # placed board + keepouts, no tracks (loaded under the
        board = pcbnew.LoadBoard(PCB)          # project's own name so its net classes apply)
        assert pcbnew.ImportSpecctraSES(board, SES)
        left = unrouted(board)
        print(f"after pass {attempt + 1}: {left} unrouted connections")
        if left == 0 or attempt == 2:
            break
        # second chance: the DSN now contains the existing wiring, Freerouting only completes the rest
        export_dsn(board)
        autoroute(passes=40)
    net = board.FindNet(GND)
    n = stitch(board, net)
    gnd_zone(board, pcbnew.F_Cu, net); gnd_zone(board, pcbnew.B_Cu, net)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    os.remove(KEEP)
    print(f"routed ({left} unrouted), {n} GND stitching vias, zones filled -> {PCB}")


if __name__ == "__main__":
    main()
