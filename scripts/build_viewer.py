#!/usr/bin/env python3
"""Build a self-contained draw.io viewer page with AWS4 icons and an embedded diagram.

Usage:
  python3 build_viewer.py [--diagram FILE] [--title TITLE] [--out FILE] [--packs default,aws,azure,kubernetes]

With no --diagram, the bundled two-page AWS sample is embedded.
Prints the output path, its size, the pages found, and any shape types the
viewer will not be able to draw (those fall back to plain rectangles).
"""
import argparse, base64, gzip, html, json, os, re, sys, urllib.parse, zlib
import xml.etree.ElementTree as ET

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


def asset(name, mode="r"):
    return open(os.path.join(ASSETS, name), mode, **({} if "b" in mode else {"encoding": "utf-8"}))


def decompress(data):
    raw = zlib.decompress(base64.b64decode(re.sub(r"\s+", "", data)), -15).decode("utf-8")
    try:
        return urllib.parse.unquote(raw)
    except Exception:
        return raw


def pages_of(text):
    """Returns [(name, model_xml)] using the same rules as the viewer page."""
    text = text.strip()
    if not text.startswith("<"):
        text = decompress(text)
    root = ET.fromstring(text)
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
    for cls, body in re.findall(r"(\w+)\.prototype\.cst\s*=\s*\{([^}]*)\}", js):
        consts[cls] = dict(re.findall(r"([A-Z0-9_]+)\s*:\s*['\"]([^'\"]+)['\"]", body))
    names = set()
    for arg in re.findall(r"registerShape\(\s*([^,]+),", js):
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
    ap.add_argument("--out", help="Output HTML path (default: /mnt/user-data/outputs/<name>-viewer.html)")
    a = ap.parse_args()

    if a.diagram:
        diagram = open(a.diagram, encoding="utf-8").read()
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
            scripts.append(f"<script>\n/* ===== {f} (jgraph/drawio v24.7.17) ===== */\n{js}\n</script>")
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

    out = a.out or f"/mnt/user-data/outputs/{re.sub(r'[^A-Za-z0-9_-]+', '-', base).strip('-') or 'drawio'}-viewer.html"
    out = os.path.abspath(out)
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
