#!/usr/bin/env python3
"""Generate the UV bench schematic (KiCad 10) from design.py.

Style: each functional block is drawn with real wires (layout.py: positions + wire paths), the way a
person draws a schematic. Pins that no drawn wire reaches get a short stub with a net label (global
when the net crosses sheets) or a power symbol. After writing, the netlist KiCad extracts is compared
pin by pin with design.py, so the drawing can never change the circuit.
Run with KiCad closed:  python3 gen_sch.py   (from this folder)
"""
import os, re, sys, uuid, datetime, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../tools"))
from kisym import load_symbol, pins, units, find, first, prop, dump, Sym
import design

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "uv-bench")
PROJECT = "uv-bench"
TODAY = datetime.date.today().isoformat()
POWER_NETS = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V"}
GRID = 2.54
STUB = 2.54
PAGE_W, PAGE_H = 420.0, 297.0          # A3 landscape

U = lambda: str(uuid.uuid4())
NS = uuid.UUID("6f1c2d3e-0a1b-4c5d-8e9f-a0b1c2d3e4f5")
SU = lambda key: str(uuid.uuid5(NS, key))   # stable UUIDs: re-running keeps the PCB links valid
S = Sym
f = lambda v: S(("%.4f" % v).rstrip("0").rstrip("."))
snap = lambda v: round(v / GRID) * GRID


def eff(size=1.27, justify=None, hide=False):
    e = [S("effects"), [S("font"), [S("size"), f(size), f(size)]]]
    if justify:
        e.append([S("justify")] + [S(j) for j in justify.split()])
    if hide:
        e.append([S("hide"), S("yes")])
    return e


def text_width(s, size=1.27):
    return len(s) * size * 0.8 + 1.0


# --------------------------------------------------------------------------- annotate
counters = collections.Counter()
instances = []        # one entry per placed symbol unit
for si, sh in enumerate(design.SHEETS):
    for part in sh["parts"]:
        prefix, lib_id, value, fp, pinmap, extra = part
        if extra.get("same_as_prev"):
            ref = instances[-1]["ref"]
        else:
            counters[prefix] += 1
            ref = ("#FLG" if prefix == "PWR" else prefix) + "%d" % counters[prefix]
        instances.append(dict(sheet=si, ref=ref, lib_id=lib_id, value=value, fp=fp, pinmap=pinmap,
                              unit=extra.get("unit", 1), dnp=extra.get("DNP", False),
                              mpn=extra.get("MPN", ""), power_flag=prefix == "PWR",
                              in_bom=extra.get("in_bom", prefix not in ("PWR", "TP", "JP", "NT"))))   # nothing to buy for these

# net -> sheets, to decide local vs global labels
net_sheets = collections.defaultdict(set)
for inst in instances:
    for n in inst["pinmap"].values():
        if n:
            net_sheets[n].add(inst["sheet"])

symcache = {}


def symdef(lib_id):
    if lib_id not in symcache:
        lib, name = lib_id.split(":")
        symcache[lib_id] = load_symbol(lib, name)
    return symcache[lib_id]


def graphic_extent(sd, unit):
    """Bounding box of the body graphics of one unit (lib coords, y up)."""
    xs, ys = [], []
    base = sd[1].split(":", 1)[1]

    def walk(n):
        if isinstance(n, list) and n:
            if n[0] in ("xy", "start", "end", "center", "mid") and len(n) >= 3:
                xs.append(float(n[1])); ys.append(float(n[2]))
            for c in n:
                walk(c)
    for sub in find(sd, "symbol"):
        tail = sub[1][len(base) + 1:]
        u = int(tail.split("_")[0])
        if u in (0, unit):
            for g in sub:
                if isinstance(g, list) and g and g[0] != "pin":
                    walk(g)
    return (min(xs), max(xs), min(ys), max(ys)) if xs else (-1, 1, -1, 1)


OUTWARD = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # screen direction away from the body
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
G = GRID


def xform(dx, dy, rot, mirror):
    """Screen offset (y down) of a symbol-local point after rotation (counter-clockwise) and mirror."""
    rot %= 360
    if rot == 90:
        dx, dy = dy, -dx
    elif rot == 180:
        dx, dy = -dx, -dy
    elif rot == 270:
        dx, dy = -dy, dx
    if mirror == "y":
        dx = -dx
    elif mirror == "x":
        dy = -dy
    return dx, dy


def unit_pins(sd, unit):
    return [p for p in pins(sd) if p["unit"] in (0, unit)]


def check_pins(inst):
    sd = symdef(inst["lib_id"])
    for p in unit_pins(sd, inst["unit"]):
        if p["number"] not in inst["pinmap"] and p["type"] != "no_connect":
            raise SystemExit(f'{inst["ref"]} pin {p["number"]} ({p["name"]}) missing in design.py')


def geometry(inst, origin, rot=0, mirror=None):
    """Pins (world mm): list of dict(number, net, pos, out) and the body box."""
    sd = symdef(inst["lib_id"])
    ox, oy = origin
    out = []
    for p in unit_pins(sd, inst["unit"]):
        if p["number"] not in inst["pinmap"]:
            continue
        dx, dy = xform(p["x"], -p["y"], rot, mirror)
        odx, ody = xform(*OUTWARD[int(p["angle"]) % 360], rot, mirror)
        out.append(dict(number=p["number"], net=inst["pinmap"][p["number"]], pos=(round(ox + dx, 3), round(oy + dy, 3)),
                        out=(int(round(odx)), int(round(ody)))))
    gx0, gx1, gy0, gy1 = graphic_extent(sd, inst["unit"])
    cs = [xform(x, -y, rot, mirror) for x in (gx0, gx1) for y in (gy0, gy1)]
    box = (ox + min(c[0] for c in cs), oy + min(c[1] for c in cs), ox + max(c[0] for c in cs), oy + max(c[1] for c in cs))
    return out, box


def auto_extent(inst):
    """Bounding box (local, rot 0) including auto stubs and labels, for automatic row placement."""
    pl, box = geometry(inst, (0, 0))
    xs, ys = [box[0], box[2]], [box[1], box[3]]
    for p in pl:
        (ex, ey), (dx, dy) = p["pos"], p["out"]
        xs.append(ex); ys.append(ey)
        if p["net"] is None:
            continue
        sx, sy = ex + dx * STUB, ey + dy * STUB
        xs.append(sx); ys.append(sy)
        if p["net"] in POWER_NETS:
            xs += [sx + dx * 3.5, sx - 2.5, sx + 2.5]; ys += [sy + dy * 3.5, sy - 2, sy + 2]
        else:
            w = text_width(p["net"]) + (3.0 if len(net_sheets[p["net"]]) > 1 else 0)
            xs.append(sx - w if dx < 0 else sx + w); ys += [sy - 1.5, sy + 1.0]
    return min(xs) - 2, max(xs) + 2, min(ys) - 4, max(ys) + 4


def on_segment(pt, a, b):
    (x, y), (x0, y0), (x1, y1) = pt, a, b
    if abs(x0 - x1) < 1e-6:
        return abs(x - x0) < 1e-6 and min(y0, y1) - 1e-6 <= y <= max(y0, y1) + 1e-6
    if abs(y0 - y1) < 1e-6:
        return abs(y - y0) < 1e-6 and min(x0, x1) - 1e-6 <= x <= max(x0, x1) + 1e-6
    return False


TWO_PIN = ("Device:R", "Device:C", "Device:C_Polarized", "Device:FerriteBead", "Device:Polyfuse", "Device:LED",
           "Diode:SMAJ5.0A", "Device:NetTie_2", "Jumper:SolderJumper_2_Open", "Sensor_Optical:BPW34-SMD")


# --------------------------------------------------------------------------- emit
pwr_count = [0]
root_uuid = SU("root")
sheet_uuids = [SU("sheet/" + s["file"]) for s in design.SHEETS]


def sym_instance(lib_id, ref, value, at, unit, sheet_idx, fp="", mpn="", dnp=False, rot=0, mirror=None,
                 in_bom=True, hide_ref=False, box=None, horizontal=False, text_side="right"):
    sd = symdef(lib_id)
    x, y = at
    node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), f(x), f(y), S(str(rot))]]
    if mirror:
        node.append([S("mirror"), S(mirror)])
    node += [[S("unit"), S(str(unit))],
             [S("body_style"), S("1")], [S("exclude_from_sim"), S("no")],
             [S("in_bom"), S("yes" if in_bom else "no")], [S("on_board"), S("yes")],
             [S("in_pos_files"), S("yes" if in_bom else "no")], [S("dnp"), S("yes" if dnp else "no")],
             [S("uuid"), SU(f"sym/{ref}/{unit}") if not ref.startswith("#PWR") else U()]]
    two_pin = lib_id in TWO_PIN and box is not None
    for name, val, hide in (("Reference", ref, hide_ref), ("Value", value, False),
                            ("Footprint", fp, True), ("Datasheet", None, True), ("Description", None, True)):
        lp = prop(sd, name)
        if val is None:
            val = lp[2] if lp else ""
        if two_pin and name in ("Reference", "Value"):
            bx0, by0, bx1, by1 = box
            if not horizontal:      # vertical part: text beside the body
                xt = bx1 + 0.8 if text_side == "right" else bx0 - 0.8
                at_ = (xt, (by0 + by1) / 2 + (-0.7 if name == "Reference" else 1.3))
                just = "left" if text_side == "right" else "right"
            else:                   # horizontal part: reference above, value below
                at_ = ((bx0 + bx1) / 2, by0 - 0.9 if name == "Reference" else by1 + 1.9); just = None
            # field angles are relative to the symbol: cancel its rotation so the text reads horizontally
            p = [S("property"), name, val, [S("at"), f(at_[0]), f(at_[1]), S(str((360 - rot) % 360))],
                 eff(justify=just, hide=hide)]
        else:
            px, py, pa = (float(lp[3][1]), float(lp[3][2]), lp[3][3]) if lp else (0, 0, S("0"))
            dx, dy = xform(px, -py, rot, mirror)
            le = first(lp, "effects") if lp else None
            just = " ".join(str(j) for j in first(le, "justify")[1:]) if le and first(le, "justify") else None
            if mirror == "y" and just:
                just = just.replace("left", "@").replace("right", "left").replace("@", "right")
            p = [S("property"), name, val, [S("at"), f(x + dx), f(y + dy), S("0") if rot else pa],
                 eff(justify=just, hide=hide or (lp is not None and first(lp, "hide") is not None
                                                 and name not in ("Reference", "Value")))]
        node.append(p)
    if mpn:
        node.append([S("property"), "MPN", mpn, [S("at"), f(x), f(y), S("0")], eff(hide=True)])
    for p in unit_pins(sd, unit):
        node.append([S("pin"), p["number"], [S("uuid"), U()]])
    node.append([S("instances"), [S("project"), PROJECT,
                 [S("path"), f"/{root_uuid}/{sheet_uuids[sheet_idx]}", [S("reference"), ref], [S("unit"), S(str(unit))]]]])
    return node


def wire(a, b):
    return [S("wire"), [S("pts"), [S("xy"), f(a[0]), f(a[1])], [S("xy"), f(b[0]), f(b[1])]],
            [S("stroke"), [S("width"), S("0")], [S("type"), S("default")]], [S("uuid"), U()]]


def label(net, at, d, is_global):
    ang = {(1, 0): "0", (-1, 0): "180", (0, -1): "90", (0, 1): "270"}[d]
    just = "left" if ang in ("0", "90") else "right"
    if is_global:
        return [S("global_label"), net, [S("shape"), S("bidirectional")], [S("at"), f(at[0]), f(at[1]), S(ang)],
                [S("fields_autoplaced"), S("yes")], eff(justify=just), [S("uuid"), U()],
                [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [S("at"), f(at[0]), f(at[1]), S("0")],
                 eff(justify="left", hide=True)]]
    return [S("label"), net, [S("at"), f(at[0]), f(at[1]), S(ang)],
            eff(justify=just + " bottom"), [S("uuid"), U()]]


def power_symbol(net, at, d, sheet_idx):
    pwr_count[0] += 1
    lib_id = POWER_NETS[net]
    # default bodies: GND points down, +3V3/+5V point up. Rotate so the body points away (outward).
    want = {(0, 1): 0, (0, -1): 180, (-1, 0): 270, (1, 0): 90} if net == "GND" else \
           {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}
    return sym_instance(lib_id, "#PWR%03d" % pwr_count[0], net, at, 1, sheet_idx, rot=want[d], in_bom=False,
                        hide_ref=True)


def text(s, at, size=1.5):
    return [S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), f(at[0]), f(at[1]), S("0")],
            eff(size=size, justify="left top"), [S("uuid"), U()]]


def title_block(title):
    return [S("title_block"), [S("title"), title], [S("date"), TODAY], [S("rev"), "A"],
            [S("company"), "UV bench - project 01"],
            [S("comment"), S("1"), "Generated by hardware/gen/gen_sch.py from design.py + layout.py - edit those, not this file"],
            [S("comment"), S("2"), "Design notes: docs/design-notes.md"]]


def header(paper, title):
    return [S("kicad_sch"), [S("version"), S("20260101")], [S("generator"), "eeschema"],
            [S("generator_version"), "10.0"], [S("uuid"), U()], [S("paper"), paper], title_block(title)]


def write(path, tree):
    open(path, "w").write(dump(tree) + "\n")


import layout
mmpt = lambda p: (round(p[0] * G, 3), round(p[1] * G, 3))
report, errors = [], []
for si, sh in enumerate(design.SHEETS):
    title = sh["title"]
    AT, WIRES = layout.AT.get(title, {}), layout.WIRES.get(title, [])
    body, used = [], set()
    body.append(text(sh["title"].upper(), (20, 14), 3.0))
    body.append(text(sh["note"], (20, 22), 1.5))
    insts = [i for i in instances if i["sheet"] == si]
    multi = collections.Counter(i["ref"] for i in insts)
    placed, auto = [], []
    for inst in insts:
        check_pins(inst)
        key = inst["ref"] + (f':{inst["unit"]}' if multi[inst["ref"]] > 1 else "")
        if key in AT:
            pin, xy, rot, mirror = AT[key][:4]
            inst["opts"] = AT[key][4] if len(AT[key]) > 4 else {}
            pl0, _ = geometry(inst, (0, 0), rot, mirror)
            off = next(p["pos"] for p in pl0 if p["number"] == pin)
            tx, ty = mmpt(xy)
            placed.append((inst, (round(tx - off[0], 3), round(ty - off[1], 3)), rot, mirror))
        else:
            auto.append(inst)
    # automatic rows below the drawn blocks
    ymax = max([mmpt(v[1])[1] for v in AT.values()] + [40.0])
    x, y, row_h = 20.0, snap(ymax + 25), 0.0
    for inst in auto:
        bx0, bx1, by0, by1 = auto_extent(inst)
        w, h = bx1 - bx0, by1 - by0
        if x + w > PAGE_W - 15:
            x, y, row_h = 20.0, y + row_h + 6, 0.0
        placed.append((inst, (snap(x - bx0), snap(y - by0)), 0, None))
        x += w + 6; row_h = max(row_h, h)
    if y + row_h > PAGE_H - 20:
        report.append(f'WARNING: sheet {title} overflows A3 (bottom at {y + row_h:.0f} mm)')
    # pins of every placed unit
    pinpos, allpins = {}, []
    for inst, org, rot, mirror in placed:
        pl, box = geometry(inst, org, rot, mirror)
        horiz = len(pl) == 2 and abs(pl[0]["pos"][1] - pl[1]["pos"][1]) < 1e-6
        for p in pl:
            pinpos[(inst["ref"], p["number"])] = p["pos"]
            allpins.append((inst["ref"], p))
        used.add(inst["lib_id"])
        body.append(sym_instance(inst["lib_id"], inst["ref"], inst["value"], org, inst["unit"], si,
                                 fp=inst["fp"], mpn=inst["mpn"], dnp=inst["dnp"], in_bom=inst["in_bom"],
                                 hide_ref=inst["power_flag"], rot=rot, mirror=mirror, box=box, horizontal=horiz,
                                 text_side=inst.get("opts", {}).get("text", "right")))
    netof = {(r, p["number"]): p["net"] for r, p in allpins}
    # drawn wires
    segs = []
    for net, pts in WIRES:
        world = []
        for pt in pts:
            if isinstance(pt, str):
                ref, num = pt.split(".")
                if (ref, num) not in pinpos:
                    errors.append(f"{title}: {pt} is not placed on this sheet"); continue
                if netof[(ref, num)] != net:
                    errors.append(f"{title}: wire {net} reaches {pt}, which is {netof[(ref, num)]}")
                world.append(pinpos[(ref, num)])
            else:
                world.append(mmpt(pt))
        for a, b in zip(world, world[1:]):
            if a == b:
                continue
            if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6:
                errors.append(f"{title}: {net} segment {a}->{b} is not horizontal/vertical")
            segs.append((net, a, b))
    explicit = [(n, mmpt(p), DIRS[d], "power") for n, p, d in layout.POWER.get(title, [])] + \
               [(n, mmpt(p), DIRS[d], "label") for n, p, d in layout.LABELS.get(title, [])]
    # pins not reached by a drawn wire: automatic stub + label / power symbol / no-connect flag
    for ref, p in allpins:
        pos, net = p["pos"], p["net"]
        if net is None:
            body.append([S("no_connect"), [S("at"), f(pos[0]), f(pos[1])], [S("uuid"), U()]]); continue
        if any(n == net and on_segment(pos, a, b) for n, a, b in segs):
            continue
        dx, dy = p["out"]
        end = (round(pos[0] + dx * STUB, 3), round(pos[1] + dy * STUB, 3))
        segs.append((net, pos, end))
        explicit.append((net, end, (dx, dy), "power" if net in POWER_NETS else "label"))
    # every drawn net gets its name: a local label sitting on its longest horizontal wire (KiCad style)
    named = {n for n, pt, d, kind in explicit}
    for net in sorted({n for n, a, b in segs} - named - set(POWER_NETS)):
        cand = sorted([(abs(b[0] - a[0]), a, b) for n, a, b in segs if n == net and abs(a[1] - b[1]) < 1e-6],
                      key=lambda c: -c[0])
        if not cand:
            cand = [(0, a, b) for n, a, b in segs if n == net]
        L, a, b = cand[0]
        x0 = min(a[0], b[0])
        pt = (round(x0 + (G if L >= 2 * G else 0), 3), a[1]) if L else a
        explicit.append((net, pt, (1, 0), "label"))
    # split wires at every same-net point lying inside them, then junctions where 3+ wire ends meet
    points = collections.defaultdict(set)
    for n, a, b in segs:
        points[n] |= {a, b}
    for r, p in allpins:
        if p["net"]:
            points[p["net"]].add(p["pos"])
    for n, pt, d, kind in explicit:
        points[n].add(pt)
    split = []
    for n, a, b in segs:
        inner = sorted([q for q in points[n] if q not in (a, b) and on_segment(q, a, b)],
                       key=lambda q: abs(q[0] - a[0]) + abs(q[1] - a[1]))
        chain = [a] + inner + [b]
        split += [(n, u, v) for u, v in zip(chain, chain[1:])]
    ends = collections.Counter()
    for n, a, b in split:
        ends[(n, a)] += 1; ends[(n, b)] += 1
    for (n, pt), k in ends.items():
        if k >= 3:
            body.append([S("junction"), [S("at"), f(pt[0]), f(pt[1])], [S("diameter"), S("0")],
                         [S("color"), S("0"), S("0"), S("0"), S("0")], [S("uuid"), U()]])
    # short check: no point of one net may touch a wire or pin of another net
    for n, pts in points.items():
        for q in pts:
            for m, a, b in split:
                if m != n and on_segment(q, a, b):
                    errors.append(f"{title}: {n} point {q} touches a {m} wire")
            for r, p in allpins:
                if p["net"] and p["net"] != n and p["pos"] == q:
                    errors.append(f"{title}: {n} point {q} sits on {r}.{p['number']} ({p['net']})")
    for n, a, b in split:
        body.append(wire(a, b))
    for n, pt, d, kind in explicit:
        if kind == "power":
            used.add(POWER_NETS[n]); body.append(power_symbol(n, pt, d, si))
        else:
            body.append(label(n, pt, d, len(net_sheets[n]) > 1))
    libs = [S("lib_symbols")] + [symdef(l) for l in sorted(used)]
    tree = header("A3", "UV bench Rev A - " + title) + [libs] + body + [[S("embedded_fonts"), S("no")]]
    write(os.path.join(OUT, sh["file"]), tree)
    report.append(f'{sh["file"]}: {len(insts)} symbol units ({len(insts) - len(auto)} drawn, {len(auto)} auto), '
                  f'{len(split)} wires')
if errors:
    print("\n".join(sorted(set(errors))))
    raise SystemExit(f"{len(set(errors))} layout errors")

# root sheet
root = header("A4", "UV bench Rev A - top level")
root[4] = [S("uuid"), root_uuid]
root.append([S("lib_symbols")])
root.append(text("UV bench Rev A: 365 nm LED, photodiode-regulated, I2C target 0x2A/0x2B, STM32C031F6P6.\n"
                 "Generated from hardware/gen/design.py. Design notes: docs/design-notes.md", (20, 20), 1.5))
for k, sh in enumerate(design.SHEETS):
    sx, sy = 30 + (k % 2) * 110, 50 + (k // 2) * 60
    root.append([S("sheet"), [S("at"), f(sx), f(sy)], [S("size"), f(80), f(35)],
                 [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
                 [S("dnp"), S("no")], [S("fields_autoplaced"), S("yes")],
                 [S("stroke"), [S("width"), f(0.1524)], [S("type"), S("solid")]],
                 [S("fill"), [S("color"), S("0"), S("0"), S("0"), S("0.0000")]], [S("uuid"), sheet_uuids[k]],
                 [S("property"), "Sheetname", sh["title"], [S("at"), f(sx), f(sy - 0.7), S("0")], eff(justify="left bottom")],
                 [S("property"), "Sheetfile", sh["file"], [S("at"), f(sx), f(sy + 35.6), S("0")], eff(justify="left top")],
                 [S("instances"), [S("project"), PROJECT, [S("path"), f"/{root_uuid}", [S("page"), str(k + 2)]]]]])
root.append([S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]])
root.append([S("embedded_fonts"), S("no")])
write(os.path.join(OUT, PROJECT + ".kicad_sch"), root)

# project file: keep the sheet list in sync
import json
pp = os.path.join(OUT, PROJECT + ".kicad_pro")
pro = json.load(open(pp))
pro["sheets"] = [[root_uuid, "Root"]] + [[u, s["title"]] for u, s in zip(sheet_uuids, design.SHEETS)]
json.dump(pro, open(pp, "w"), indent=2)
print("\n".join(report))
print("nets:", len(net_sheets), " global:", sorted(n for n, s in net_sheets.items() if len(s) > 1 and n not in POWER_NETS))

# reference table for the docs (docs/parts-list.md), generated so it never drifts from the schematic
rows = collections.OrderedDict()
for inst in instances:
    if inst["power_flag"]:
        continue
    r = rows.setdefault(inst["ref"], dict(inst, nets=[]))
    r["nets"] += [f"{p}:{n or 'nc'}" for p, n in sorted(inst["pinmap"].items(), key=lambda kv: kv[0].zfill(3))]
key = lambda ref: (re.match(r"[A-Z]+", ref).group(0), int(re.search(r"\d+", ref).group(0)))
lines = ["# UV bench Rev A: parts list (generated)", "",
         "Generated by `hardware/gen/gen_sch.py` from `hardware/gen/design.py`. Do not edit by hand.",
         "Why each value: [`design-notes.md`](design-notes.md).", "",
         "| Ref | Value | Footprint | MPN | Sheet | Pin: net |", "|---|---|---|---|---|---|"]
for ref in sorted(rows, key=key):
    r = rows[ref]
    fp = r["fp"].split(":")[-1] if r["fp"] else ""
    flags = " **(DNP)**" if r["dnp"] else ""
    lines.append(f'| {ref} | {r["value"]}{flags} | {fp} | {r["mpn"]} | {design.SHEETS[r["sheet"]]["title"]} | '
                 + ", ".join(r["nets"]).replace("|", "/") + " |")
open(os.path.join(HERE, "../../docs/parts-list.md"), "w").write("\n".join(lines) + "\n")

# --------------------------------------------------------------------------- verify
# The drawing must not change the circuit: export KiCad's netlist and compare it, pin by pin, with
# the nets declared in design.py (the same partition of pins into nets, whatever the net names).
import subprocess, tempfile
from kisym import parse
cli = os.path.expanduser("~/Applications/kicad-10.0.7/bin/kicad-cli")
with tempfile.TemporaryDirectory() as td:
    netf = os.path.join(td, "check.net")
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", netf,
                    os.path.join(OUT, PROJECT + ".kicad_sch")], check=True, stdout=subprocess.DEVNULL)
    t = parse(open(netf).read())
got, names = set(), {}
for n in find(first(t, "nets"), "net"):
    nodes = frozenset((str(first(x, "ref")[1]), str(first(x, "pin")[1])) for x in find(n, "node")
                      if not str(first(x, "ref")[1]).startswith("#"))
    if len(nodes) > 1:
        got.add(nodes)
        names[nodes] = str(first(n, "name")[1]).rsplit("/", 1)[-1]     # "/LED driver/SET_G" -> "SET_G"
wantd = collections.defaultdict(set)
for inst in instances:
    if inst["power_flag"]:
        continue
    for pin, net in inst["pinmap"].items():
        if net:
            wantd[net].add((inst["ref"], pin))
want = {frozenset(v) for v in wantd.values() if len(v) > 1}
bad_names = [(n, names.get(frozenset(v))) for n, v in wantd.items()
             if len(v) > 1 and frozenset(v) in names and names[frozenset(v)] != n]
if bad_names:
    for n, g in bad_names:
        print(f"net {n} is named {g} in KiCad")
    raise SystemExit("net names differ from design.py")
if got != want:
    for s_ in sorted(want - got, key=len):
        print("MISSING/BROKEN net:", sorted(s_))
    for s_ in sorted(got - want, key=len):
        print("UNEXPECTED net    :", sorted(s_))
    raise SystemExit("netlist differs from design.py")
print(f"netlist check: {len(got)} nets identical to design.py (pins and names)")
