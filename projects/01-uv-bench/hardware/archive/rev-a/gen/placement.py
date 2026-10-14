"""Placement for the UV bench PCB (called by gen_pcb.py).

Method (see docs/design-notes.md §Layout):
1. Board outline 70 x 55 mm with the Ø22 mm LED-star cut-out, 4 M3 holes.
2. FIXED parts: connectors on the edges, ICs where the signal flow wants them, the photodiode
   at the cut-out edge (facing the reflector side port), the MOSFET far from the photodiode.
3. AUTO parts (passives, test points): greedy, net-aware. Each part goes to the free spot closest
   to the pads it connects to (power nets ignored, decoupling caps get an explicit pin to hug).
"""
import math
import pcbnew

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
X0, Y0, W, H = 100.0, 100.0, 70.0, 55.0
HX, HY, HR = 122.0, 127.5, 11.0            # cut-out centre / radius
PD_POS = (136.5, 127.5)                    # photodiode: 14.5 mm from the LED axis
POWER = {"GND", "+3V3", "+5V"}
SPACING = 0.6     # mm kept free around auto-placed parts: routing channels for the 2-layer autorouter

FIXED = {  # ref: (x, y, rotation)
    "J1": (166.5, 109.5, 270),   # main board connector, right edge
    "J2": (127.0, 102.8, 90),   # FTDI header along the top edge
    "U1": (152.0, 104.0, 0), "U2": (146.0, 104.0, 0),
    "F1": (149.0, 109.0, 0), "D1": (140.5, 110.0, 90), "U3": (149.0, 114.0, 0),
    "U4": (159.5, 114.0, 0),
    "C4": (112.0, 106.0, 0),    # 220 uF reservoir, close to the LED loop
    "J5": (105.5, 122.0, 90),   # LED star wires, at the cut-out edge
    "J6": (105.5, 133.0, 90),   # NTC wires
    "Q1": (111.0, 146.0, 90),   # MOSFET (0.5 W) in the corner far from the photodiode
    "R14": (117.0, 149.5, 90),  # current sense, right next to Q1 source
    "U8": (123.0, 149.5, 180),    # current-loop op-amp next to the sense resistor
    "U6": (133.5, 146.5, 0), "U7": (141.0, 146.5, 0),
    "J4": (157.0, 151.5, 0),    # UV ARM switch connector, bottom edge
    "U5": (157.0, 128.0, 0),    # MCU
    "J3": (166.0, 128.0, 90),   # SWD, right edge
    "D3": (PD_POS[0], PD_POS[1], 90),
    "U9": (142.5, 127.5, 90),   # TIA right next to the photodiode
    "D4": (137.0, 118.5, 90),   # alternative detector (DNP)
}
HUG = {  # decoupling / local parts: ref -> (ref, pad) to sit next to
    "C1": ("U1", "1"), "C2": ("U2", "1"), "C3": ("F1", "2"), "C6": ("U3", "1"), "C7": ("U3", "5"),
    "C5": ("C4", "1"), "C8": ("U5", "4"), "C9": ("U5", "4"), "C10": ("U5", "6"), "C14": ("U8", "8"),
    "C17": ("U9", "5"), "TP4": ("U4", "2"), "TP14": ("U9", "2"), "TP3": ("U3", "5"), "TP1": ("F1", "2"),
    "R13": ("Q1", "1"), "R20": ("U9", "3"),
}
HOLES = [(X0 + 3.5, Y0 + 3.5), (X0 + W - 3.5, Y0 + 3.5), (X0 + 3.5, Y0 + H - 3.5), (X0 + W - 3.5, Y0 + H - 3.5)]


def outline(board):
    for d in list(board.GetDrawings()):
        if d.GetLayer() in (pcbnew.Edge_Cuts, pcbnew.Dwgs_User) or (
                d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_TEXT)):
            board.Remove(d)

    def shape(kind, layer, w=0.1):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(kind); s.SetLayer(layer); s.SetWidth(mm(w)); board.Add(s); return s
    r = shape(pcbnew.SHAPE_T_RECT, pcbnew.Edge_Cuts); r.SetStart(V(X0, Y0)); r.SetEnd(V(X0 + W, Y0 + H))
    c = shape(pcbnew.SHAPE_T_CIRCLE, pcbnew.Edge_Cuts); c.SetCenter(V(HX, HY)); c.SetEnd(V(HX + HR, HY))
    c2 = shape(pcbnew.SHAPE_T_CIRCLE, pcbnew.Dwgs_User); c2.SetCenter(V(HX, HY)); c2.SetEnd(V(HX + 10, HY))
    for txt, x, y, layer, size in (("LED star Ø20 on the Al plate", HX, HY - 2, pcbnew.Dwgs_User, 1.0),
                                   ("reflector side port faces D3 ->", HX, HY + 2, pcbnew.Dwgs_User, 1.0),
                                   ("UV BENCH rev A", 128.0, 153.0, pcbnew.F_SilkS, 1.0)):
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


def on_board(b):
    if b[0] < X0 + 0.4 or b[1] < Y0 + 0.4 or b[2] > X0 + W - 0.4 or b[3] > Y0 + H - 0.4:
        return False
    nx, ny = min(max(HX, b[0]), b[2]), min(max(HY, b[1]), b[3])   # closest box point to the hole centre
    return math.hypot(nx - HX, ny - HY) > HR + 0.5


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)
    q = fp.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)


def place(board, fps):
    outline(board)
    boxes = {}
    for fp in board.GetFootprints():
        if fp.IsBoardOnly():
            boxes[fp.GetReference()] = bbox(fp)
    for ref, (x, y, rot) in FIXED.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(rot); fp.SetPosition(V(x, y))
        boxes[ref] = bbox(fp)
    # net tie on the sense-resistor pad: pad 1 of NT1 sits on R14 pad 1 (Kelvin connection point)
    nt, rs = fps["NT1"], fps["R14"]
    px, py = pad_xy(rs, "1")
    nt.SetOrientationDegrees(0)
    nt.SetPosition(V(px + 1.2, py))          # NT1 pads are at x = -0.5 / +0.5 -> pad 1 overlaps R14 pad 1 edge
    boxes["NT1"] = (px + 0.4, py - 0.5, px + 2.0, py + 0.5)

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
        todo.sort(key=lambda r: -(len(links(r)) + (100 if r in HUG and HUG[r][0] in placed else 0)))
        ref = todo.pop(0)
        fp = fps[ref]
        if ref in HUG and HUG[ref][0] in placed:
            tx, ty = pad_xy(fps[HUG[ref][0]], HUG[ref][1]); targets = None
        else:
            l = links(ref)
            if l:
                tx, ty = sum(a[1] for a in l) / len(l), sum(a[2] for a in l) / len(l); targets = l
            else:
                tx, ty, targets = 150.0, 140.0, None
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
