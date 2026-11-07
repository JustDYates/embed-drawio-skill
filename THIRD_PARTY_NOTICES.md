# Third-party notices

This skill bundles material from other projects, and the viewer pages it builds embed that material. Each item keeps its own licence; the skill's own files (`SKILL.md`, `scripts/build_viewer.py`, and the parts of `assets/viewer-template.html` not listed below) carry no third-party terms. The full licence texts are in `LICENSES/`.

All draw.io material comes from **jgraph/drawio release v24.7.5** (commit `a2685dd63e1475fd9aea14ef52ce3f1199f38b1e`), the most recent release before v24.7.8, the point at which the repository switched to the "JGraph License 2.0" with its additional clause about Atlassian Confluence and Jira integrations. At v24.7.5 the code is under the plain Apache License 2.0 and the stencil libraries under Creative Commons Attribution 4.0.

## draw.io code — Apache License 2.0

Copyright JGraph Ltd. Licensed under the Apache License, Version 2.0 (`LICENSES/Apache-2.0.txt`).

| Bundled file | Source path at v24.7.5 | Changes |
|---|---|---|
| `assets/shapes/Shapes.js` | `src/main/webapp/js/grapheditor/Shapes.js` | Line endings normalised to LF |
| `assets/shapes/mxAWS4.js` | `src/main/webapp/shapes/mxAWS4.js` | Line endings normalised to LF |
| `assets/shapes/mxBasic.js` | `src/main/webapp/shapes/mxBasic.js` | Line endings normalised to LF |
| `assets/shapes/mxArrows.js` | `src/main/webapp/shapes/mxArrows.js` | Line endings normalised to LF |
| `assets/shapes/mxFlowchart.js` | `src/main/webapp/shapes/mxFlowchart.js` | Line endings normalised to LF |
| `assets/shapes/mxKubernetes.js` | `src/main/webapp/shapes/mxKubernetes.js` | Line endings normalised to LF |
| `assets/styles/default.xml` | `src/main/webapp/styles/default.xml` | **Modified:** `default` colour values replaced with `#ffffff` / `#000000`; whitespace between tags removed |
| Table helpers inside `assets/viewer-template.html` (`isTable`, `isTableRow`, `isTableCell`, `visitTableCells`, `getTableLines`) | `src/main/webapp/js/grapheditor/Graph.js` | **Modified:** rewritten as functions on `mxGraph.prototype` for mxGraph 4.2.2; null-geometry guard taken from the current `dev` branch (commit `c72c9a98b7a6ce392556ed04c05e0ff19f43f5c3`, also Apache License 2.0) |

## draw.io stencil libraries — Creative Commons Attribution 4.0

Stencil libraries by JGraph Ltd (draw.io), licensed under CC BY 4.0 (`LICENSES/CC-BY-4.0.txt`, https://creativecommons.org/licenses/by/4.0/). Source: `src/main/webapp/stencils/` at v24.7.5.

Bundled as `assets/stencils/<name>.xml.gz`: `aws4`, `azure`, `basic`, `arrows`, `flowchart`, `kubernetes`, `kubernetes2`.

**Modified:** whitespace between tags removed and the files gzip-compressed. No shape geometry was changed.

The CC BY 4.0 licence does not grant trademark rights. Several of these libraries reproduce third-party product icons, which are covered below.

## Product icons and trademarks

These terms come from the icon owners, not from draw.io, and apply in addition to the licences above. Check the owners' current terms before redistributing the skill or a built page beyond your own use.

- **AWS icons** (`aws4` stencils, vector reproductions of the AWS Architecture Icons). Amazon Web Services publishes these icons for use in architecture diagrams under its own terms of use, available from the AWS Architecture Icons page (https://aws.amazon.com/architecture/icons/). AWS, Amazon and the service names are trademarks of Amazon.com, Inc. or its affiliates.
- **Azure icons** (`assets/images/azure2.json.gz`: 581 SVG files from `src/main/webapp/img/lib/azure2/` at v24.7.5, with comments and inter-tag whitespace removed, otherwise unchanged; and the older `azure` stencils). Microsoft's Azure architecture icon terms (https://learn.microsoft.com/azure/architecture/icons/) permit use in architectural diagrams, training materials and documentation, and copying, distributing and displaying them only for that permitted use unless Microsoft grants explicit permission. Microsoft's guidelines also ask that the icons are not cropped, flipped, rotated or distorted, and not used to represent your own product or service. Microsoft and Azure are trademarks of the Microsoft group of companies.
- **Kubernetes icons** (`kubernetes`, `kubernetes2` stencils). Kubernetes is a registered trademark of The Linux Foundation. Use of the icons does not imply endorsement.

## Loaded at runtime, not bundled

The viewer page loads these from public CDNs when it opens; they are not stored in the skill.

- **mxGraph 4.2.2** (jsDelivr, `mxgraph@4.2.2`) — Copyright JGraph Ltd, Apache License 2.0.
- **pako 2.1.0** (cdnjs) — MIT and Zlib licences.
- **Schibsted Grotesk** (Google Fonts) — SIL Open Font License 1.1.

## Attribution in built pages

Every page `build_viewer.py` produces shows a credit line in its status bar naming JGraph (draw.io), CC BY 4.0 and Apache 2.0, noting the material was minified, and stating that the AWS and Azure icons belong to Amazon and Microsoft. Keep that line if you change the template.

This file is a record of sources and licences, not legal advice.
