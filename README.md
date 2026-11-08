# draw.io viewer skill

A [Claude skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns a draw.io / diagrams.net diagram into a single, self-contained, interactive HTML page and publishes it as an artifact. Claude can then show you the diagram itself instead of a wall of XML.

The page renders diagrams with mxGraph 4.2.2 and draw.io's own shape libraries, including AWS, Azure and Kubernetes icons. All shapes, stencils and icons are bundled in this repository, so a build needs no network access.

## Features

- Renders `.drawio`, `.dio`, `.xml` (`mxfile` or `mxGraphModel`) and draw.io SVG exports that include an embedded diagram
- Reads both plain and compressed diagram pages
- Shows each diagram page as a tab, with zoom and pan
- Lets you drag and drop, paste or open other diagram files once the page is open
- Supports light and dark themes
- Warns you about any shapes it can't draw, both in the build output and in the page's status bar

### Shape packs

All packs are embedded by default, which makes a page of about 9 MB (the publish limit is 16 MB). Use `--packs` to embed fewer.

| Pack | Covers |
|---|---|
| `default` | draw.io General, Misc, Advanced and UML shapes, plus Basic (`mxgraph.basic.*`), Arrows (`mxgraph.arrows2.*`) and Flowchart (`mxgraph.flowchart.*`) |
| `aws` | AWS4 icons, groups and resource icons (`mxgraph.aws4.*`) |
| `azure` | Current Azure icons (581 SVGs under `img/lib/azure2/`) and the older `mxgraph.azure.*` icons |
| `kubernetes` | `mxgraph.kubernetes.icon` and `icon2` |

**Not included:** GCP, Cisco, BPMN, network, electrical, mockups and other libraries. Shapes from these draw as plain rectangles. Images loaded from remote URLs won't show either, because published pages block other hosts.

## Repository layout

```
SKILL.md                    Skill definition and the instructions Claude follows
scripts/build_viewer.py     Builds the viewer page (Python 3, standard library only)
assets/
  viewer-template.html      Viewer page template (toolbar, tabs, zoom/pan, warnings)
  styles/default.xml        draw.io default stylesheet
  shapes/*.js               draw.io shape scripts
  stencils/*.xml.gz         draw.io stencil libraries (gzip-compressed)
  images/azure2.json.gz     Azure SVG icons
  sample.drawio             Three example pages, used when you don't supply a diagram
LICENSE                     Licence for this project's own code
LICENSES/                   Full texts of third-party licences
THIRD_PARTY_NOTICES.md      Sources, versions and changes for every bundled file
```

## Installation

### Claude.ai / Claude desktop app

1. Download this repository as a ZIP (**Code → Download ZIP**), or create one yourself. The ZIP must contain the skill folder with `SKILL.md` at its top level:
   ```bash
   git clone https://github.com/JustDYates/embed-drawio-skill.git drawio-viewer
   cd drawio-viewer && zip -r ../drawio-viewer.zip . -x '.git/*' '.DS_Store'
   ```
2. In Claude, open **Settings → Capabilities → Skills**, choose **Upload skill** and select the ZIP. Code execution must be turned on.

### Claude Code

Clone the repository into your personal skills folder, or into a project's `.claude/skills/` folder:

```bash
git clone https://github.com/JustDYates/embed-drawio-skill.git ~/.claude/skills/drawio-viewer
```

## Usage

### Through Claude

Once the skill is installed, Claude uses it on its own when it's relevant. For example, you can:

- Upload a `.drawio` file and ask Claude to show it to you
- Paste draw.io XML and ask for a preview
- Ask Claude to create an architecture diagram and then show it
- Ask for "the draw.io viewer" to get an empty viewer (with the sample diagrams) that you can open your own files in

Claude builds the page, publishes it as an artifact, and tells you which pages it found and whether any shapes are unsupported. If the diagram changes later in the same conversation, Claude rebuilds the page and updates the same artifact.

### Running the build script yourself

The script needs only Python 3, with no extra packages.

```bash
python3 scripts/build_viewer.py --diagram path/to/diagram.drawio --out viewer.html
```

| Option | Description | Default |
|---|---|---|
| `--diagram FILE` | Diagram to embed (`.drawio`, `.dio`, `.xml` or draw.io `.svg`) | The bundled `sample.drawio` |
| `--title TEXT` | Heading shown in the viewer | The file name |
| `--packs LIST` | Comma-separated packs: `default`, `aws`, `azure`, `kubernetes` | All four |
| `--out FILE` | Where to write the HTML | `/mnt/user-data/outputs/<name>-viewer.html` |

The default output path is for Claude's sandbox. When you run the script on your own computer, always pass `--out`.

For safety when an AI agent runs the script, both `--diagram` and `--out` must resolve (after following `..` and symlinks) to a path inside the current working directory, `/mnt/user-data` or `/home/claude` (the last two are Claude's sandbox). `--diagram` must have one of the extensions above, and `--out` must end in `.html` or `.htm`. Run the script from the folder that holds your diagram.

Example output:

```
OUTPUT /path/to/viewer.html
SIZE 8.73 MB
TITLE Sample diagrams
PACKS default, aws, azure, kubernetes
PAGES Serverless API | VPC network | Kubernetes on Azure
UNSUPPORTED none
```

`UNSUPPORTED` lists any shapes or images the page can't draw. If the diagram can't be read, the script prints `ERROR: ...` and exits without writing a page. You can open the resulting HTML directly in a browser. It loads mxGraph, pako and the Schibsted Grotesk font from public CDNs, so the browser needs internet access.

### Limitations

- The viewer is read-only. To change a diagram, edit the `.drawio` file and rebuild the page.
- PNG exports with an embedded diagram aren't supported. Use the `.drawio` file or an SVG export saved with "Include a copy of my diagram".
- Don't edit a built HTML page by hand. Change `assets/viewer-template.html` and rebuild instead.

## Extending

To add another draw.io library:

1. Add its stencil XML (gzip-compressed) to `assets/stencils/`, and any `mx*.js` shape script it needs to `assets/shapes/`. Image-based libraries go in `assets/images/` as a gzip-compressed JSON map of `img/lib/...` path → SVG text.
2. Add an entry to `PACKS` in [`scripts/build_viewer.py`](scripts/build_viewer.py).
3. Take the files from **jgraph/drawio v24.7.5** only (see [Licences](#licences) for why), and record them in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Licences

This repository contains material under several licences. [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) is the full record of sources, versions and changes. Read it before you redistribute the skill or change what's bundled.

### This project's own code

`SKILL.md`, `scripts/build_viewer.py` and the original parts of `assets/viewer-template.html` are licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

### Bundled draw.io material

Every draw.io file comes from **[jgraph/drawio](https://github.com/jgraph/drawio) release v24.7.5** (commit `a2685dd`).

| Material | Licence | Files |
|---|---|---|
| draw.io code: shape scripts, default stylesheet, table helpers in the template | Apache License 2.0, © JGraph Ltd | `assets/shapes/*.js`, `assets/styles/default.xml`, part of `assets/viewer-template.html` |
| draw.io stencil libraries and Azure SVGs | Creative Commons Attribution 4.0, © JGraph Ltd | `assets/stencils/*.xml.gz`, `assets/images/azure2.json.gz` |

The full licence texts are in [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt) and [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt). Some files were modified (line endings normalised, whitespace stripped, gzip-compressed, `default` colours resolved in the stylesheet). `THIRD_PARTY_NOTICES.md` lists each change.

**Why v24.7.5?** Releases from v24.7.8 to v25.x use the "JGraph License 2.0", which adds a restriction on use in Atlassian Confluence and Jira integrations. The current `dev` branch applies a similar restriction to the icon and stencil libraries. Current `dev` code also needs draw.io's own fork of mxGraph and doesn't work with mxGraph 4.2.2. Don't update the bundled files from later releases without checking both the licence and compatibility.

### Product icons and trademarks

These terms come from the icon owners and apply in addition to the licences above:

- **AWS icons:** published by Amazon Web Services for use in architecture diagrams, under the [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) terms. AWS, Amazon and the service names are trademarks of Amazon.com, Inc. or its affiliates.
- **Azure icons:** Microsoft's [Azure architecture icon terms](https://learn.microsoft.com/azure/architecture/icons/) allow their use in architecture diagrams, training materials and documentation. Don't crop, flip, rotate or distort them, and don't use them to represent your own product or service. Microsoft and Azure are trademarks of the Microsoft group of companies.
- **Kubernetes icons:** Kubernetes is a registered trademark of The Linux Foundation. Using the icons doesn't imply endorsement.

### Loaded at runtime (not bundled)

| Library | Source | Licence |
|---|---|---|
| mxGraph 4.2.2 | jsDelivr | Apache License 2.0, © JGraph Ltd |
| pako 2.1.0 | cdnjs | MIT and Zlib |
| Schibsted Grotesk | Google Fonts | SIL Open Font License 1.1 |

### Attribution in built pages

Every page the build script produces shows a credit line in its status bar. It names JGraph (draw.io), CC BY 4.0 and Apache 2.0, and states that the AWS and Azure icons belong to Amazon and Microsoft. The CC BY 4.0 licence requires this attribution, so keep the line if you change the template.

---

This README summarises licence information for convenience. It isn't legal advice. Check the original licences and the icon owners' current terms before you redistribute the skill or the pages it builds.
