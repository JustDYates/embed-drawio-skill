#!/usr/bin/env python3
"""Build a self-contained draw.io viewer page with AWS4 icons and an embedded diagram.

Usage:
  python3 build_viewer.py [--diagram FILE] [--title TITLE] [--out FILE] [--packs default,aws,azure,kubernetes]

With no --diagram, the bundled three-page sample (AWS, and Kubernetes on Azure) is embedded.
Prints the output path, its size, the pages found, and any shape types the
viewer will not be able to draw (those fall back to plain rectangles).
"""
import argparse, base64, gzip, html, json, os, re, stat, sys, tempfile, urllib.parse, zlib
import xml.parsers.expat
# ElementTree only ever parses through parse_xml(), which rejects entity declarations first.
import xml.etree.ElementTree as ET  # nosec B405

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

# Shapes plain mxGraph 4.2.2 draws natively
BUILTIN = {
    "rectangle", "ellipse", "doubleEllipse", "rhombus", "line", "image", "arrow",
    "arrowConnector", "label", "cylinder", "swimlane", "connector", "actor", "cloud",
    "triangle", "hexagon",
}

# Each pack: shape scripts (assets/shapes), stencil sets (assets/stencils/*.xml.gz),
# image libraries (assets/images/*.json.gz, keyed by draw.io's img/lib/... path)
PACKS = {
    "default": {
        "label": "General",
        "scripts": ["Shapes.js", "mxBasic.js", "mxArrows.js", "mxFlowchart.js"],
        "stencils": ["basic", "arrows", "flowchart"],
        "images": [],
    },
    "aws": {"label": "AWS", "scripts": ["mxAWS4.js"], "stencils": ["aws4"], "images": []},
    "azure": {"label": "Azure", "scripts": [], "stencils": ["azure"], "images": ["azure2"]},
    "kubernetes": {"label": "Kubernetes", "scripts": ["mxKubernetes.js"], "stencils": ["kubernetes", "kubernetes2"], "images": []},
}
PR_ICON_PACKAGE = {"mxgraph.kubernetes.icon": "mxgraph.kubernetes.", "mxgraph.kubernetes.icon2": "mxgraph.kubernetes2."}

SANDBOX_OUTPUTS = "/mnt/user-data/outputs"


def private_dir(path):
    """Returns path if it is an existing directory owned by this user that nobody else can
    write to, else None. Temp locations are only trusted when they pass this check, so a
    shared, world-writable /tmp is never an allowed root."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    if not stat.S_ISDIR(st.st_mode) or st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        return None
    if hasattr(os, "getuid") and st.st_uid != os.getuid():
        return None
    return path


# Claude Code keeps each session's scratchpad under a per-user directory, /tmp/claude-<uid>.
# It is only trusted when private_dir() confirms it belongs to this user and is not shared.
CLAUDE_CODE_TMP = f"/tmp/claude-{os.getuid()}" if hasattr(os, "getuid") else None  # nosec B108 # NOSONAR(S5443)

# Directories --diagram and --out may point into: the directory the script is run from,
# Claude's sandbox upload/output area and working directory, and, when they are private to
# this user, the system temp directory and Claude Code's scratchpad area.
ALLOWED_ROOTS = [os.getcwd(), "/mnt/user-data", "/home/claude"] + [
    d for d in (tempfile.gettempdir(), CLAUDE_CODE_TMP) if d and private_dir(d)
]
DIAGRAM_EXTS = (".drawio", ".dio", ".xml", ".svg")
OUTPUT_EXTS = (".html", ".htm")


def safe_path(path, exts, what):
    """Canonicalise a CLI-supplied path and reject it unless it sits inside an allowed root
    and has one of the expected extensions."""
    resolved = os.path.realpath(path)
    if not resolved.lower().endswith(exts):
        raise ValueError(f"{what} {path!r} must end with one of: {', '.join(exts)}")
    for root in ALLOWED_ROOTS:
        base = os.path.realpath(root)
        if resolved.startswith(base.rstrip(os.sep) + os.sep):
            return resolved
    raise ValueError(f"{what} {path!r} is outside the allowed directories: {', '.join(ALLOWED_ROOTS)}")


def asset(name, mode="r"):
    return open(os.path.join(ASSETS, name), mode, **({} if "b" in mode else {"encoding": "utf-8"}))


def decompress(data):
    raw = zlib.decompress(base64.b64decode(re.sub(r"\s+", "", data)), -15).decode("utf-8")
    try:
        return urllib.parse.unquote(raw)
    except Exception:
        return raw


def parse_xml(text):
    """Parses untrusted diagram XML, refusing entity declarations.

    Python's ElementTree expands internal entities, so a crafted file ("billion laughs") could
    use up memory. A first pass with expat raises at the first entity declaration, before any
    expansion, which is the check defusedxml makes; draw.io files and SVG exports never declare
    entities. The script stays standard-library only, so defusedxml itself isn't used."""
    def forbid(*_):
        raise ValueError("XML entity declarations are not allowed in a diagram.")

    scan = xml.parsers.expat.ParserCreate()
    scan.EntityDeclHandler = forbid
    scan.UnparsedEntityDeclHandler = forbid
    scan.Parse(text.encode("utf-8"), True)
    return ET.fromstring(text)  # nosec B314 - entity declarations were rejected above


def pages_of(text):
    """Returns [(name, model_xml)] using the same rules as the viewer page."""
    text = text.strip()
    if not text.startswith("<"):
        text = decompress(text)
    root = parse_xml(text)
    tag = root.tag.split("}")[-1]
    if tag == "svg":
        content = root.get("content")
        if not content:
            raise ValueError("SVG has no embedded draw.io diagram (export with 'Include a copy of my diagram').")
        return pages_of(content)
    if tag == "mxGraphModel":
        return [("Page 1", text)]
    if tag == "mxfile":
        out = []
        for i, d in enumerate(root.iter("diagram")):
            model = d.find("mxGraphModel")
            if model is not None:
                xml = ET.tostring(model, encoding="unicode")
            elif (d.text or "").strip():
                xml = decompress(d.text)
            else:
                continue
            out.append((d.get("name") or f"Page {i + 1}", xml))
        if not out:
            raise ValueError("File has no pages.")
        return out
    raise ValueError(f"Not a draw.io diagram: root element is <{tag}>.")


def unsupported(model_xml, shapes, stencils, images):
    missing = set()
    for style in re.findall(r'style="([^"]*)"', model_xml):
        st = {}
        for part in html.unescape(style).split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                st[k] = v
        sh = st.get("shape")
        if sh and sh not in BUILTIN and sh not in shapes and sh.lower() not in stencils:
            missing.add(sh)
        for k in ("resIcon", "prIcon", "grIcon"):
            v = st.get(k)
            if v:
                full = PR_ICON_PACKAGE[sh] + v if k == "prIcon" and sh in PR_ICON_PACKAGE else v
                if full.lower() not in stencils:
                    missing.add(full)
        img = st.get("image")
        if img and not img.startswith("data:"):
            key = re.sub(r"^\./", "", re.sub(r"^https?://[^/]+/", "", img))
            if key not in images:
                missing.add("image " + key)
    return missing


def registered_shapes(js):
    """Shape names a shape script registers, resolving Class.prototype.cst.NAME constants."""
    consts = {}
    for cls, body in re.findall(r"\b(\w+)\.prototype\.cst\s*=\s*\{([^}]*)\}", js):
        consts[cls] = dict(re.findall(r"\b([A-Z0-9_]+)\s*:\s*['\"]([^'\"]+)['\"]", body))
    names = set()
    for arg in re.findall(r"registerShape\(\s*([^,\s][^,]*),", js):
        arg = arg.strip()
        if arg[0] in "'\"":
            names.add(arg.strip("'\""))
            continue
        m = re.match(r"(\w+)\.prototype\.cst\.([A-Z0-9_]+)$", arg)
        if m and m.group(2) in consts.get(m.group(1), {}):
            names.add(consts[m.group(1)][m.group(2)])
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagram", help=".drawio / .xml / draw.io .svg file to embed")
    ap.add_argument("--title", help="Heading shown in the viewer (default: file name)")
    ap.add_argument("--packs", default="default,aws,azure,kubernetes",
                    help="Comma-separated shape packs to embed: default, aws, azure, kubernetes (default: all)")
    ap.add_argument("--out", help="Output HTML path (default: /mnt/user-data/outputs/<name>-viewer.html in "
                                  "Claude's sandbox, otherwise <system temp>/drawio-viewer/<name>-viewer.html)")
    a = ap.parse_args()

    if a.diagram:
        try:
            diagram_path = safe_path(a.diagram, DIAGRAM_EXTS, "--diagram")
        except ValueError as e:
            sys.exit(f"ERROR: {e}")
        with open(diagram_path, encoding="utf-8") as f:
            diagram = f.read()
        base = os.path.splitext(os.path.basename(a.diagram))[0]
        title = a.title or os.path.basename(a.diagram)
        meta = "Embedded diagram"
    else:
        diagram = asset("sample.drawio").read()
        base = "drawio"
        title = a.title or "Sample diagrams"
        meta = "Built-in example"

    try:
        pages = pages_of(diagram)
    except Exception as e:
        sys.exit(f"ERROR: could not read diagram: {e}")

    packs = [p.strip().lower() for p in a.packs.split(",") if p.strip()]
    for p in packs:
        if p not in PACKS:
            sys.exit(f"ERROR: unknown pack '{p}'. Choose from: {', '.join(PACKS)}")

    def no_script_end(name, s):
        if "</script" in s.lower():
            sys.exit(f"ERROR: {name} contains </script and cannot be inlined")
        return s

    scripts, stencil_tags, image_tags = [], [], []
    shapes, stencils, images = set(), set(), {}
    for p in packs:
        cfg = PACKS[p]
        for f in cfg["scripts"]:
            js = no_script_end(f, asset("shapes/" + f).read())
            shapes |= registered_shapes(js)
            scripts.append(f"<script>\n/* ===== {f} (jgraph/drawio v24.7.5) ===== */\n{js}\n</script>")
        for n in cfg["stencils"]:
            xml = no_script_end(n, gzip.decompress(asset(f"stencils/{n}.xml.gz", "rb").read()).decode("utf-8"))
            pkg = re.search(r'<shapes name="([^"]+)"', xml).group(1).lower()
            stencils |= {pkg + "." + s.replace(" ", "_").lower() for s in re.findall(r'<shape [^>]*?name="([^"]+)"', xml)}
            stencil_tags.append(f'<script type="text/xml" class="stencil-set" data-set="{n}">{xml}</script>')
        for n in cfg["images"]:
            lib = json.loads(gzip.decompress(asset(f"images/{n}.json.gz", "rb").read()).decode("utf-8"))
            images.update(lib)
            data = json.dumps(lib, separators=(",", ":")).replace("</", "<\\/")
            image_tags.append(f'<script type="application/json" class="image-lib" data-set="{n}">{data}</script>')

    missing = set()
    for _, xml in pages:
        missing |= unsupported(xml, shapes, stencils, images)

    def js_str(s):
        return json.dumps(s).replace("</", "<\\/")

    page = asset("viewer-template.html").read()
    page = (page.replace("<!--__STYLESHEET__-->", asset("styles/default.xml").read())
                .replace("<!--__SHAPE_SCRIPTS__-->", "\n".join(scripts))
                .replace("<!--__STENCIL_SETS__-->", "\n".join(stencil_tags))
                .replace("<!--__IMAGE_LIBS__-->", "\n".join(image_tags))
                .replace("/*__PACKS_JSON__*/", js_str([PACKS[p]["label"] for p in packs]))
                .replace("/*__DIAGRAM_JSON__*/", js_str(diagram))
                .replace("/*__TITLE_JSON__*/", js_str(title))
                .replace("/*__META_JSON__*/", js_str(meta))
                .replace("__TITLE_HTML__", html.escape(title))
                .replace("__META_HTML__", html.escape(meta)))

    if a.out:
        out = a.out
    else:
        # claude.ai sandbox: the outputs folder. Anywhere else (e.g. Claude Code): the user's
        # private temp dir, or a fresh private directory if the temp dir is shared.
        if os.path.isdir("/mnt/user-data"):
            out_dir = SANDBOX_OUTPUTS
        elif private_dir(tempfile.gettempdir()):
            out_dir = os.path.join(tempfile.gettempdir(), "drawio-viewer")
        else:
            out_dir = tempfile.mkdtemp(prefix="drawio-viewer-")
            ALLOWED_ROOTS.append(out_dir)
        out = os.path.join(out_dir, f"{re.sub(r'[^A-Za-z0-9_-]+', '-', base).strip('-') or 'drawio'}-viewer.html")
    try:
        out = safe_path(out, OUTPUT_EXTS, "--out")
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)

    size = len(page.encode()) / 1e6
    print(f"OUTPUT {out}")
    print(f"SIZE {size:.2f} MB")
    print(f"TITLE {title}")
    print("PACKS " + ", ".join(packs))
    print("PAGES " + " | ".join(n for n, _ in pages))
    print("UNSUPPORTED " + (", ".join(sorted(missing)) if missing else "none"))
    if size > 15.5:
        print("WARNING page is close to the 16 MB publish limit")


if __name__ == "__main__":
    main()
