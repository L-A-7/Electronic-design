"""Placement for the UV bench PCB, Rev B (called by gen_pcb.py).

Method (see docs/rev-b-simple.md §8):
1. Board outline 58 x 32 mm with the Ø22 mm LED-star cut-out on the left, 4 M3 holes in the corners.
   The board geometry lives here only; route.py and silk.py import it.
2. FIXED parts, given by the centre of their courtyard: knob (encoder) on the right edge, connectors on the top edge, MCU in the
   middle, photodiode at the cut-out edge (facing the reflector side port), LED pads under the
   cut-out, MOSFET + power resistor along the bottom edge, far from the photodiode.
3. AUTO parts (passives): greedy, net-aware. Each part goes to the free spot closest to the pads it
   connects to (power nets ignored); decoupling/filter parts get an explicit pad to hug,
   placed in the order of the HUG table (the MCU decoupling capacitor first).
"""
import math
import pcbnew

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
X0, Y0, W, H = 100.0, 100.0, 58.0, 32.0
HX, HY, HR = 113.0, 116.0, 11.0            # cut-out centre / radius (Ø22 for the Ø20 star)
HOLE_INSET = 3.5
CORNER_R = 3.5     # rounded corners (set by hand in KiCad 2026-10-15): = HOLE_INSET, so each corner arc is
                   # centred on its mounting hole. The GND pours keep a rectangular outline; their fill is
                   # clipped to the rounded edge
HOLES = [(X0 + HOLE_INSET, Y0 + HOLE_INSET), (X0 + W - HOLE_INSET, Y0 + HOLE_INSET),
         (X0 + HOLE_INSET, Y0 + H - HOLE_INSET), (X0 + W - HOLE_INSET, Y0 + H - HOLE_INSET)]
POWER = {"GND", "+3V3", "+5V"}
SPACING = 0.5     # mm kept free around auto-placed parts: routing channels for the autorouter

FIXED = {  # ref: (courtyard centre x, y, rotation)
    "SW1": (150.6, 116.0, 0),    # knob: encoder body on the right edge, shaft sticking out to the right
    "D2": (153.5, 123.3, 0),     # mode LED just below the knob, visible next to it
    "J1": (144.6, 103.3, 0),     # JST-PH on the top edge, cable leaves upwards
    "U1": (139.4, 108.4, 0),     # LDO right below the connector
    "J4": (122.2, 103.1, 0),     # remote photodiode JST-PH 2, top edge between the cut-out and J3 (analog side)
    "J3": (130.5, 105.57, 0),    # STDC14 debug header on the top edge (14 pins: 1.27 mm lower than the 10-pin)
    "U2": (137.5, 115.5, 0),     # MCU in the middle
    "D1": (127.4, 116.0, 90),    # photodiode at the cut-out edge, 14.4 mm from the LED axis
    "J2": (118.5, 130.0, 0),     # LED wire pads under the cut-out: 2 short wires to the star
    "Q1": (130.5, 129.6, 0),     # MOSFET, bottom edge
    "R1": (139.5, 129.3, 0),     # 3.9 R 1 W, bottom edge, ~13 mm from the photodiode
}
HUG = {  # local parts: ref -> (ref, pad) to sit next to
    "C4": ("U2", "4"), "C5": ("U2", "6"),
    "C1": ("J1", "2"), "C2": ("U1", "3"), "C3": ("U1", "2"), "R5": ("D2", "2"),
    "C6": ("U2", "7"), "R4": ("D1", "2"),       # PD node: filter cap at the ADC pin, load at the diode
    "R3": ("Q1", "1"), "C7": ("Q1", "1"), "R2": ("U2", "15"),
    "C8": ("J4", "2"), "R8": ("J4", "2"), "R6": ("J4", "1"), "R7": ("U2", "17"),   # remote PD: C8 at the connector
}


def outline(board):
    def shape(kind, layer, w=0.1):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(kind); s.SetLayer(layer); s.SetWidth(mm(w)); board.Add(s); return s
    r = shape(pcbnew.SHAPE_T_RECT, pcbnew.Edge_Cuts); r.SetStart(V(X0, Y0)); r.SetEnd(V(X0 + W, Y0 + H))
    r.SetCornerRadius(mm(CORNER_R))
    c = shape(pcbnew.SHAPE_T_CIRCLE, pcbnew.Edge_Cuts); c.SetCenter(V(HX, HY)); c.SetEnd(V(HX + HR, HY))
    c2 = shape(pcbnew.SHAPE_T_CIRCLE, pcbnew.Dwgs_User); c2.SetCenter(V(HX, HY)); c2.SetEnd(V(HX + 10, HY))
    for txt, x, y, layer, size in (("LED star Ø20 on the Al plate", HX, HY - 2, pcbnew.Dwgs_User, 1.0),
                                   ("reflector side port faces D1 ->", HX, HY + 2, pcbnew.Dwgs_User, 1.0),
                                   ("UV BENCH rev C", 148.6, 131.0, pcbnew.F_SilkS, 0.8)):
        t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetPosition(V(x, y)); t.SetLayer(layer)
        t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15)); board.Add(t)
    holes = [fp for fp in board.GetFootprints() if fp.IsBoardOnly()]
    for fp, (x, y) in zip(sorted(holes, key=lambda f: f.GetReference()), HOLES):
        fp.SetPosition(V(x, y))


def bbox(fp, grow=0.25):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()) - grow, pcbnew.ToMM(bb.GetTop()) - grow,
            pcbnew.ToMM(bb.GetRight()) + grow, pcbnew.ToMM(bb.GetBottom()) + grow)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def on_board(b, edge=0.4):
    if b[0] < X0 + edge or b[1] < Y0 + edge or b[2] > X0 + W - edge or b[3] > Y0 + H - edge:
        return False
    nx, ny = min(max(HX, b[0]), b[2]), min(max(HY, b[1]), b[3])   # closest box point to the hole centre
    return math.hypot(nx - HX, ny - HY) > HR + 0.5


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)
    q = fp.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)


def put_centre(fp, cx, cy, rot):
    """Place so that the courtyard centre lands on (cx, cy): footprint origins are often pin 1."""
    fp.SetOrientationDegrees(rot); fp.SetPosition(V(0, 0))
    b = bbox(fp, 0)
    fp.SetPosition(V(cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2))


def place(board, fps):
    outline(board)
    boxes = {}
    for fp in board.GetFootprints():
        if fp.IsBoardOnly():
            boxes[fp.GetReference()] = bbox(fp)
    for ref, (x, y, rot) in FIXED.items():
        put_centre(fps[ref], x, y, rot)
        boxes[ref] = bbox(fps[ref])
        if not on_board(bbox(fps[ref], 0), 0.3):
            print(f"WARNING: {ref} courtyard leaves the board or enters the cut-out: {bbox(fps[ref], 0)}")
    # polarity marks beside the LED wire pads (pad 1 = LED+ = +5V, pad 2 = LED- = drain)
    for num, txt, dx in (("1", "+", -1.6), ("2", "-", 1.6)):
        x, y = pad_xy(fps["J2"], num)
        t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetPosition(V(x + dx, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(V(1.0, 1.0)); t.SetTextThickness(mm(0.2)); board.Add(t)
    raw = {r: (bbox(fps[r], 0) if r in fps else boxes[r]) for r in boxes}
    for a in raw:
        for b in raw:
            if a < b and overlaps(raw[a], raw[b]):
                print(f"WARNING: {a} overlaps {b}")

    placed = set(boxes)
    todo = [r for r in fps if r not in placed]

    def links(ref):
        out = []
        for p in fps[ref].Pads():
            n = p.GetNetname()
            if not n or n in POWER:
                continue
            for other in placed:
                if other in fps and other != ref:
                    for q in fps[other].Pads():
                        if q.GetNetname() == n:
                            out.append((p.GetNumber(), pcbnew.ToMM(q.GetPosition().x), pcbnew.ToMM(q.GetPosition().y)))
        return out

    while todo:
        # HUG parts first, in the order of the HUG table (most important first: C4 decoupling)
        order = list(HUG)
        todo.sort(key=lambda r: -(len(links(r)) + (1000 - order.index(r) if r in HUG and HUG[r][0] in placed else 0)))
        ref = todo.pop(0)
        fp = fps[ref]
        if ref in HUG and HUG[ref][0] in placed:
            tx, ty = pad_xy(fps[HUG[ref][0]], HUG[ref][1]); targets = None
        else:
            l = links(ref)
            if l:
                tx, ty = sum(a[1] for a in l) / len(l), sum(a[2] for a in l) / len(l); targets = l
            else:
                tx, ty, targets = X0 + 0.75 * W, Y0 + H / 2, None
        best = None
        for r in range(0, 60):
            rad = r * 0.5
            steps = max(1, int(2 * math.pi * rad / 0.5))
            for k in range(steps):
                a = 2 * math.pi * k / steps
                x, y = round((tx + rad * math.cos(a)) * 4) / 4, round((ty + rad * math.sin(a)) * 4) / 4
                for rot in (0, 90, 180, 270):
                    fp.SetOrientationDegrees(rot); fp.SetPosition(V(x, y))
                    b = bbox(fp, SPACING)
                    if not on_board(b) or any(overlaps(b, o) for o in boxes.values()):
                        continue
                    cost = 0.0
                    if targets:
                        for num, qx, qy in targets:
                            px_, py_ = pad_xy(fp, num); cost += math.hypot(px_ - qx, py_ - qy)
                    else:
                        cost = math.hypot(x - tx, y - ty)
                    if best is None or cost < best[0]:
                        best = (cost, x, y, rot)
            if best and rad > 3:
                break
        if best is None:
            raise SystemExit("no room for " + ref)
        _, x, y, rot = best
        fp.SetOrientationDegrees(rot); fp.SetPosition(V(x, y))
        boxes[ref] = bbox(fp); placed.add(ref)
