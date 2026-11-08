---
name: "drawio-viewer"
description: Show a draw.io / diagrams.net diagram as a published, interactive viewer page with draw.io's standard shapes (General, Misc, Advanced, UML, Basic, Arrows, Flowchart), AWS4 icons, Azure icons and Kubernetes icons, pages as tabs, zoom and pan. Use this whenever the user uploads or pastes a .drawio, .dio, .xml (mxfile / mxGraphModel) or draw.io SVG export and wants to see, preview, open, render, share or check it; whenever Claude has just produced a .drawio file (for example with the aws-architecture-diagram skill) and the user would benefit from seeing it rendered instead of reading XML; whenever the user asks for "the draw.io viewer", "a drawio viewer", or to view an AWS, Azure, Kubernetes or flowchart diagram in chat; and in Claude Code whenever the user wants to see a diagram (including one from the draw.io MCP server) that can't render inline in the terminal or IDE, or asks for it as a hosted page. Also use it if the user asks why shapes or cloud icons don't render in a plain mxGraph page.
---

# draw.io viewer

Builds one self-contained HTML page that renders draw.io diagrams with mxGraph 4.2.2 and draw.io's own shape libraries, then publishes it as an artifact. It works both in the claude.ai / Claude desktop sandbox and in Claude Code. Everything the page needs is bundled here, so the build needs no network access.

## Shape packs

All packs are embedded by default (page is about 9 MB, well under the 16 MB publish limit). Pass `--packs` to embed fewer, for example `--packs default,aws` (about 5 MB with AWS alone).

| Pack | What it covers | Files |
|---|---|---|
| `default` | draw.io's General, Misc, Advanced and UML shapes (`process`, `note`, `cylinder3`, `umlActor`, `table`…), Basic (`mxgraph.basic.*`), Arrows (`mxgraph.arrows2.*`) and Flowchart (`mxgraph.flowchart.*`) | `shapes/Shapes.js`, `mxBasic.js`, `mxArrows.js`, `mxFlowchart.js`; `stencils/basic`, `arrows`, `flowchart` |
| `aws` | AWS4 icons, groups and resource icons (`mxgraph.aws4.*`) | `shapes/mxAWS4.js`; `stencils/aws4` |
| `azure` | Current Azure icons (`image=img/lib/azure2/...svg`, 581 SVGs) and the older `mxgraph.azure.*` icons | `images/azure2.json.gz`; `stencils/azure` |
| `kubernetes` | `mxgraph.kubernetes.icon` and `icon2` with `prIcon=` | `shapes/mxKubernetes.js`; `stencils/kubernetes`, `kubernetes2` |

Only drop a pack when you're sure the diagram doesn't use it; the build output's `UNSUPPORTED` line tells you if something is missing.

## What's bundled (assets/)

- `viewer-template.html` – the viewer page (toolbar, page tabs, zoom/pan, drag-and-drop, paste, open-file, unsupported-shape warnings). Loads mxGraph from jsDelivr and pako 2.1.0 from cdnjs, the only external scripts; both hosts are allowed on published pages. It also contains small compatibility pieces: a stub `Graph` class (Shapes.js expects draw.io's editor) and draw.io's table helpers (`isTable`, `visitTableCells`, `getTableLines`) so table row and column lines draw.
- `styles/default.xml` – draw.io's default stylesheet (light theme, `default` colours resolved to black/white). It defines the named styles diagrams start with (`ellipse;`, `text;`, `image;`, `swimlane;`, `rhombus;`, `label;`…); without it those shapes fall back to rectangles.
- `shapes/`, `stencils/*.xml.gz`, `images/azure2.json.gz` – the pack files above, all from jgraph/drawio release **v24.7.5**. See "Licences" below for why that release and not a later one.
- `sample.drawio` – three example pages (serverless API on AWS; AWS VPC network, stored compressed; Kubernetes on Azure), used when no diagram is given.

Stencils are registered the way draw.io does it: package name + `.` + shape name lowercased with spaces turned into underscores. Azure images are looked up by their app-relative path (`img/lib/azure2/compute/Virtual_Machine.svg`, or the same path behind any `https://host/` prefix) and turned into data URIs at render time.

## Workflow

The skill runs in two environments. Work out which one you're in first, then follow the matching paths below:

- **claude.ai / Claude desktop sandbox:** `/mnt/user-data/` exists. Uploads are in `/mnt/user-data/uploads/`, and your working directory is `/home/claude/`.
- **Claude Code:** you're on the user's own machine, usually inside a project folder, and `/mnt/user-data/` doesn't exist. Diagrams can't render inline in the terminal or IDE, and the draw.io MCP server's `create_diagram` view may not show either, so a published viewer page is how the user gets to see a diagram.

1. **Get the diagram onto disk.**
   - **Uploaded file (sandbox):** it's in `/mnt/user-data/uploads/`.
   - **File in the project (Claude Code):** use its path as it is. Run the script from the project folder.
   - **A diagram Claude made in this conversation**, for example draw.io XML written by hand, returned by the draw.io MCP server's `create_diagram`, or made with the aws-architecture-diagram skill: use the file you wrote if there is one. Otherwise, save the XML as a `.drawio` file: in the sandbox, to `/home/claude/diagram.drawio`; in Claude Code, to your scratchpad directory (or the system temp directory if you have none). Don't save it into the user's project unless they ask for that.
   - **Pasted XML:** save it the same way as a diagram Claude made.
   - **No diagram** (the user just wants the viewer): skip `--diagram`. The sample is embedded, and the user can open their own files from the page.
   - PNG exports with embedded diagrams are not supported. Ask for the .drawio file or an SVG export instead.

2. **Build.**
   ```bash
   # Sandbox
   python3 /path/to/skill/scripts/build_viewer.py --diagram /mnt/user-data/uploads/arch.drawio
   # Claude Code: run from the project folder, write the page to your scratchpad
   python3 /path/to/skill/scripts/build_viewer.py --diagram docs/arch.drawio --out <scratchpad>/arch-viewer.html
   ```
   Options:
   - `--title "Payments platform"` sets the heading. It defaults to the file name.
   - `--packs default,aws,azure,kubernetes` chooses the shape packs. The default is all four; embed only the ones the diagram uses to keep the page small.
   - `--out FILE` sets where the page is written. Without it, the page goes to `/mnt/user-data/outputs/` in the sandbox, and to a `drawio-viewer` folder in the system temp directory elsewhere. In Claude Code, pass `--out` with a path in your scratchpad so the page stays in one known place you can publish from and rebuild over.

   The script prints `OUTPUT`, `SIZE`, `PACKS`, `PAGES` and `UNSUPPORTED`. If it prints `ERROR`, tell the user what was wrong with the file in plain words rather than publishing.

   For safety, the script only reads and writes inside these folders: the current directory, `/home/claude/`, `/mnt/user-data/`, and the system temp directory and Claude Code's scratchpad area (`/tmp/claude-<uid>`) when they belong to the user and nobody else can write to them. It also only reads diagram files (`.drawio`, `.dio`, `.xml`, `.svg`) and only writes `.html`. An `outside the allowed directories` or `must end with` error means the path broke one of these rules: move or rename the file instead of working around the check.

3. **Publish** with the Artifact tool: `action: "publish"`, `file_path` set to the `OUTPUT` path, `icon: "diagram"` on the first publish, and a short `title`. (Older versions of the Artifact tool take `favicon: "🗺️"` instead of `icon`.)
   - **Updating:** if you already published a viewer in this conversation and the diagram changed, rebuild to the same `--out` path and publish that same `file_path` again, so the artifact updates at the same URL. For an artifact from an earlier conversation, pass its `url`.
   - **Sandbox only:** don't call `present_files` on a published page. If the user explicitly wants the HTML as a download instead of a hosted page, use `present_files` and don't publish.
   - **Claude Code only:** if the user wants the HTML file instead of a hosted page, give them the `OUTPUT` path (or build with `--out` into their project) and don't publish.
   - Published pages are private to the user until they share them from the page's Share menu. Say so if the page is meant for someone else.

4. **Report briefly**: the pages it found and, if `UNSUPPORTED` isn't `none`, what will be missing. Shape names there (for example `mxgraph.cisco.*`, `mxgraph.gcp2.*`, `mxgraph.bpmn.*`) are libraries outside these packs and draw as plain rectangles; `image img/lib/...` entries are library icons that aren't bundled and won't show. The page shows the same warning in its status bar.

## Things to know

- Libraries not included: GCP, Cisco, BPMN, network, electrical, mockups and others. Adding one means adding its stencil XML (from the same v24.7.5 release), any `shapes/mx*.js` file it needs, and an entry in `PACKS` in `build_viewer.py`; image-based libraries go in `assets/images/` as a JSON map of path → SVG text.
- Images referenced by remote URL won't show (published pages block other hosts). Data-URI images and the bundled Azure icons do show.
- The viewer is read-only. For edits, change the .drawio XML (or regenerate it), rebuild and republish.
- Don't hand-edit the built HTML: change the template and rebuild. Template placeholders: `<!--__SHAPE_SCRIPTS__-->`, `<!--__STYLESHEET__-->`, `<!--__STENCIL_SETS__-->`, `<!--__IMAGE_LIBS__-->`, `/*__PACKS_JSON__*/`, `/*__DIAGRAM_JSON__*/`, `/*__TITLE_JSON__*/`, `/*__META_JSON__*/`, `__TITLE_HTML__`, `__META_HTML__`.
- draw.io colour keywords (`fillColor=default`, `light-dark(a,b)`) are mapped to plain colours by the page, and compressed pages (base64 + raw deflate + URI encoding) are unpacked with pako.

## Licences

Read `THIRD_PARTY_NOTICES.md` before changing what's bundled. In short:

- draw.io code (`shapes/*.js`, `styles/default.xml`, the table helpers in the template) is Apache License 2.0; the stencil libraries are CC BY 4.0. Full texts are in `LICENSES/`.
- Everything comes from **v24.7.5** on purpose. Releases from v24.7.8 to v25.x use the "JGraph License 2.0", which adds a ban on use in Atlassian Confluence/Jira integrations, and the current `dev` branch moves a similar restriction onto its icon and stencil libraries. Current `dev` code (`Shapes.js` especially) also needs draw.io's own fork of mxGraph and fails on mxGraph 4.2.2. Don't pull files from later releases or `dev` without checking both the licence and compatibility, and update `THIRD_PARTY_NOTICES.md` when you add or change a file.
- AWS and Azure icons are also covered by Amazon's and Microsoft's own icon terms (architecture diagrams, training and documentation). Don't recolour, crop or distort them, and don't present them as the user's own product branding.
- Built pages show a credit line in the status bar (JGraph / draw.io, CC BY 4.0 and Apache 2.0, AWS and Azure icons belong to their owners). Keep it.
- If the user plans to share the skill or built pages outside their own use, point them to `THIRD_PARTY_NOTICES.md` and suggest they check the AWS and Microsoft icon terms themselves; don't present this as legal advice.
