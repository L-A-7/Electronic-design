"""Board of the photodiode head (called by gen_pcb.py with UVB_DESIGN=design_head).

12 x 21 mm. The diode at the top, its sensitive face up (it looks at the lamp through the filter).
The wire pads below, with strain-relief holes at the bottom edge: the wires pass through the big hole
first, so a pull on the cable doesn't reach the solder joints. Two short tracks; no ground plane
(the node impedance is set on the main board, and there's nothing else on this board).
"""
import pcbnew

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
X0, Y0, W, H = 100.0, 100.0, 12.0, 21.0
TRACK = 0.4
CORNER_R = 1.5     # rounded corners (set by hand in KiCad 2026-10-15, then copied here). Max ~2 mm:
                   # the strain-relief holes are 1.9 mm from the bottom corners


def text(board, s, x, y, layer, size=0.8):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15))
    t.SetMirrored(layer == pcbnew.B_SilkS)          # back-side text is mirrored, so it reads right from behind
    board.Add(t)


def track(board, pts, net):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2))
        t.SetWidth(mm(TRACK)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); board.Add(t)


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)


def place(board, fps):
    r = pcbnew.PCB_SHAPE(board); r.SetShape(pcbnew.SHAPE_T_RECT); r.SetLayer(pcbnew.Edge_Cuts)
    r.SetWidth(mm(0.1)); r.SetStart(V(X0, Y0)); r.SetEnd(V(X0 + W, Y0 + H))
    r.SetCornerRadius(mm(CORNER_R)); board.Add(r)
    cx = X0 + W / 2
    d1, j1 = fps["D1"], fps["J1"]
    d1.SetOrientationDegrees(0); d1.SetPosition(V(cx, Y0 + 3.0))          # pads at cx -/+ 3.05: K left, A right
    j1.SetOrientationDegrees(0); j1.SetPosition(V(cx - 2.1, Y0 + 8.0))    # wire pads at cx -/+ 2.1, reliefs 10.2 below
    for num in ("1", "2"):
        (xa, ya), (xb, yb) = pad_xy(d1, num), pad_xy(j1, num)
        track(board, [(xa, ya), (xa, ya + 3.5), (xb, ya + 3.5 + abs(xb - xa)), (xb, yb)],
              next(p.GetNet() for p in d1.Pads() if p.GetNumber() == num))
    # references on the fab layer (no room on silk), polarity and wiring on silk
    for fp in (d1, j1):
        fp.Reference().SetLayer(pcbnew.F_Fab)
    k, a = pad_xy(j1, "1"), pad_xy(j1, "2")
    text(board, "K", k[0] - 2.3, k[1], pcbnew.F_SilkS)
    text(board, "A", a[0] + 2.3, a[1], pcbnew.F_SilkS)
    # the front is full (the wire-pad footprint draws the wire paths on silk): labels go on the back
    text(board, "UV BENCH PD HEAD", cx, Y0 + 4.0, pcbnew.B_SilkS, 0.8)
    text(board, "to J4: K=1 A=2", cx, Y0 + 13.0, pcbnew.B_SilkS, 0.8)
    text(board, "ZWB2 filter over D1", cx, Y0 - 1.5, pcbnew.Dwgs_User, 0.8)
