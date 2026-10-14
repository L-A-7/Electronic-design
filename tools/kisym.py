"""Minimal S-expression reader/writer and KiCad 10 symbol-library access.

Used by the schematic generator. Reads symbols from the KiCad 10 libraries (one file per
symbol in <lib>.kicad_symdir/), resolves `extends` (derived symbols), and returns a flattened
copy ready to embed in a schematic's lib_symbols.
"""
import os, re, copy

KICAD_SHARE = os.environ.get("KICAD_SHARE", os.path.expanduser("~/Applications/kicad-10.0.7/share/kicad"))
SYMDIR = os.path.join(KICAD_SHARE, "symbols")


class Sym(str):
    """An unquoted atom (keyword, number, yes/no)."""


class Raw(str):
    """A quoted string read from a file, kept with its original escapes."""


def parse(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        elif t.startswith('"'):
            cur.append(Raw(t[1:-1]))
        else:
            cur.append(Sym(t))
    return cur[0]


def q(s):
    if isinstance(s, Raw):
        return '"' + s + '"'
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(node, indent=0):
    """Serialise like KiCad: one list per line when it contains sub-lists."""
    if not isinstance(node, list):
        return node if isinstance(node, Sym) else q(node)
    pad = "\t" * indent
    if not any(isinstance(x, list) for x in node):
        return "(" + " ".join(dump(x) for x in node) + ")"
    head = [dump(x) for x in node if not isinstance(x, list)]
    out = "(" + " ".join(head)
    for x in node:
        if isinstance(x, list):
            out += "\n" + pad + "\t" + dump(x, indent + 1)
    return out + "\n" + pad + ")"


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


def prop(node, name):
    for p in find(node, "property"):
        if p[1] == name:
            return p
    return None


def _load_raw(lib, name):
    path = os.path.join(SYMDIR, lib + ".kicad_symdir", name + ".kicad_sym")
    if os.path.exists(path):
        return first(parse(open(path).read()), "symbol")
    path = os.path.join(SYMDIR, lib + ".kicad_sym")          # single-file library
    tree = parse(open(path).read())
    for s in find(tree, "symbol"):
        if s[1] == name:
            return s
    raise KeyError(f"{lib}:{name}")


def load_symbol(lib, name):
    """Return the flattened symbol definition named 'lib:name'."""
    raw = copy.deepcopy(_load_raw(lib, name))
    ext = first(raw, "extends")
    if ext:
        parent = load_symbol(lib, ext[1])
        flat = copy.deepcopy(parent)
        flat[1] = f"{lib}:{name}"
        pname = parent[1].split(":", 1)[1]
        # child properties replace the parent's
        for p in find(raw, "property"):
            old = prop(flat, p[1])
            if old is not None:
                flat[flat.index(old)] = p
            else:
                flat.append(p)
        for sub in find(flat, "symbol"):
            sub[1] = sub[1].replace(pname + "_", name + "_", 1)
        return flat
    raw[1] = f"{lib}:{name}"
    return raw


def pins(symdef):
    """List of dicts: number, name, type, x, y, angle, length, unit."""
    out = []
    base = symdef[1].split(":", 1)[1]
    for sub in find(symdef, "symbol"):
        m = re.match(re.escape(base) + r"_(\d+)_(\d+)$", sub[1])
        unit = int(m.group(1)) if m else 0
        for p in find(sub, "pin"):
            at = first(p, "at")
            out.append(dict(type=str(p[1]), number=first(p, "number")[1], name=first(p, "name")[1],
                            x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                            length=float(first(p, "length")[1]), unit=unit))
    return out


def units(symdef):
    base = symdef[1].split(":", 1)[1]
    us = set()
    for sub in find(symdef, "symbol"):
        m = re.match(re.escape(base) + r"_(\d+)_(\d+)$", sub[1])
        if m and int(m.group(1)) > 0:
            us.add(int(m.group(1)))
    return sorted(us) or [1]


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        lib, name = arg.split(":")
        sd = load_symbol(lib, name)
        print("==", arg, "units", units(sd))
        for p in sorted(pins(sd), key=lambda p: (p["unit"], p["number"].zfill(3))):
            print(f'  u{p["unit"]} {p["number"]:>4} {p["name"]:<14} {p["type"]:<14} ({p["x"]}, {p["y"]}) {p["angle"]}')
