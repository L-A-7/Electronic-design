#!/usr/bin/env python3
"""Build the UV bench PCB from the schematic netlist (KiCad 10 Python).

Steps: (1) kicad-cli exports the netlist; (2) every component gets its footprint, value, fields,
schematic link (path) and pad nets, which is what "Update PCB from Schematic" does in the GUI;
(3) footprints are placed from placement.py; (4) zones and the outline are (re)created.
Routing is a separate step (route.py: Freerouting + checks).
Run with KiCad closed:  ~/Applications/kicad-10.0.7/bin/python3.11 gen_pcb.py [--area]
"""
import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../tools"))
import pcbnew
import importlib
design = importlib.import_module(os.environ.get("UVB_DESIGN", "design"))   # see gen_sch.py
from kisym import parse, find, first

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = getattr(design, "PROJECT", "uv-bench")
PRJ = os.environ.get("UVB_PRJ", os.path.join(HERE, "..", PROJECT))   # UVB_PRJ: build a copy elsewhere
SCH = os.path.join(PRJ, PROJECT + ".kicad_sch")
PCB = os.path.join(PRJ, PROJECT + ".kicad_pcb")
KICAD = os.path.expanduser("~/Applications/kicad-10.0.7")
CLI = os.path.join(KICAD, "bin/kicad-cli")
FPDIR = os.path.join(KICAD, "share/kicad/footprints")
NET = os.path.join(HERE, PROJECT + ".net")

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))


def netlist():
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET, SCH], check=True,
                   stdout=subprocess.DEVNULL)
    t = parse(open(NET).read())
    comps = {}
    for c in find(first(t, "components"), "comp"):
        ref = str(first(c, "ref")[1])
        fields = {str(first(fl, "name")[1]) if isinstance(fl[1], list) else "": "" for fl in []}
        props = {str(first(p, "name")[1]): str(first(p, "value")[1]) if first(p, "value") else ""
                 for p in find(c, "property")}
        flds = first(c, "fields")
        extra = {}
        if flds:
            for fl in find(flds, "field"):
                name = first(fl, "name")[1]
                extra[str(name)] = str(fl[-1]) if not isinstance(fl[-1], list) else ""
        sp = first(c, "sheetpath")
        g = lambda k: str(first(c, k)[1]) if first(c, k) else ""
        comps[ref] = dict(ref=ref, value=str(first(c, "value")[1]), fp=str(first(c, "footprint")[1]),
                          datasheet=g("datasheet"), description=g("description"),
                          path=str(first(sp, "tstamps")[1]) + str(first(c, "tstamps")[1]),
                          dnp="dnp" in props, mpn=extra.get("MPN", ""),
                          sheetname=str(first(sp, "names")[1]), sheetfile=props.get("Sheetfile", ""))
    nets = {}
    for n in find(first(t, "nets"), "net"):
        name = str(first(n, "name")[1])
        for node in find(n, "node"):
            nets[(str(first(node, "ref")[1]), str(first(node, "pin")[1]))] = name
    return comps, nets


def load_fp(fpid):
    lib, name = fpid.split(":")
    try:
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
    except AttributeError as e:
        raise SystemExit(f"FootprintLoad failed for {fpid}: {e}")
    if fp is None:
        raise SystemExit("footprint not found: " + fpid)
    return fp


def build(board, comps, nets):
    # Load every footprint first: removing items from the board before loading confuses the
    # footprint plugin cache in KiCad 10's Python API.
    loaded = {ref: load_fp(c["fp"]) for ref, c in comps.items()}
    for i in range(getattr(design, "MOUNTING_HOLES", 4)):   # M3 mounting holes (board-only, not in the schematic)
        h = load_fp("MountingHole:MountingHole_3.2mm_M3")
        h.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        h.SetReference(f"H{i + 1}"); h.SetBoardOnly(True)
        h.SetExcludedFromBOM(True); h.SetExcludedFromPosFiles(True)
        board.Add(h)
    netinfo = {}
    for name in sorted(set(nets.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    placed = {}
    for ref, c in sorted(comps.items()):
        fp = loaded[ref]
        lib, name = c["fp"].split(":")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        for fld in fp.GetFields():                 # copy the schematic fields (parity check)
            if fld.GetName() == "Datasheet":
                fld.SetText(c["datasheet"])
            elif fld.GetName() == "Description":
                fld.SetText(c["description"])
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetSheetname(c["sheetname"])
        fp.SetSheetfile(c["sheetfile"])
        if c["mpn"]:
            fld = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, "MPN")
            fld.SetText(c["mpn"]); fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab)
            fp.Add(fld)
        fp.SetDNP(c["dnp"])
        for pad in fp.Pads():
            n = nets.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        board.Add(fp)
        placed[ref] = fp
    return placed


def courtyard_area(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False)
    return pcbnew.ToMM(bb.GetWidth()) * pcbnew.ToMM(bb.GetHeight())


if __name__ == "__main__":
    comps, nets = netlist()
    # Start from an empty board each time (settings live in uv-bench.kicad_pro), so a re-run
    # never leaves stale items behind. Removing items from a loaded board is unreliable in the API.
    board = pcbnew.NewBoard(PCB)
    board.SetCopperLayerCount(2)
    tb = board.GetTitleBlock()
    tb.SetTitle(f'{getattr(design, "TITLE", "UV bench")} Rev {design.REV}'); tb.SetRevision(design.REV); tb.SetCompany("UV bench - project 01")
    tb.SetComment(0, "Generated by hardware/gen (design.py -> gen_sch.py -> gen_pcb.py -> route.py)")
    placed = build(board, comps, nets)
    if "--area" in sys.argv:
        board.BuildConnectivity()
        tot = 0
        for ref, fp in sorted(placed.items()):
            a = courtyard_area(fp); tot += a
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            print(f"{ref:6} {pcbnew.ToMM(bb.GetWidth()):5.1f} x {pcbnew.ToMM(bb.GetHeight()):5.1f}  {fp.GetFPID().GetUniStringLibItemName()}")
        print(f"{len(placed)} footprints, courtyard area {tot:.0f} mm2")
        sys.exit()
    placement = importlib.import_module(getattr(design, "PLACEMENT", "placement"))
    placement.place(board, placed)
    pcbnew.SaveBoard(PCB, board)
    import shutil
    if PROJECT == "uv-bench":
        shutil.copy(PCB, os.path.join(HERE, "placed.kicad_pcb"))   # pristine copy: route.py starts from it
    print("saved", PCB)
