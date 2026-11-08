# Security policy

## Reporting a vulnerability

Please report security problems privately. Don't open a public issue or pull request for them.

Report through GitHub's private vulnerability reporting: open the repository's **Security** tab and choose **Report a vulnerability**, or go straight to <https://github.com/JustDYates/embed-drawio-skill/security/advisories/new>.

Please include:

- what the problem is and what an attacker could do with it
- the steps to reproduce it, ideally with a small diagram file that triggers it
- the commit you tested against

You should get a first reply within 7 days. Once the problem is confirmed, a fix is usually released within 30 days, depending on how complex it is. You'll be credited in the advisory unless you'd rather not be.

## Supported versions

This project has no numbered releases yet. Fixes go to the `main` branch only, so make sure you're using the latest `main`.

## What's in scope

This skill builds web pages from diagram files that users upload or paste, so it treats every diagram as untrusted. These are in scope:

- `scripts/build_viewer.py`, for example:
  - reading or writing files outside the allowed folders
  - getting around the file-extension checks
  - XML parsing attacks, such as entity expansion
- `assets/viewer-template.html`, for example script injection through a diagram's title, page names or labels
- `SKILL.md`, for example instructions that could lead Claude to publish something the user didn't intend

## What's out of scope

- **Bugs in the bundled draw.io shapes, stencils and icons** (`assets/shapes/`, `assets/stencils/`, `assets/images/`). These are unmodified files from [jgraph/drawio v24.7.5](https://github.com/jgraph/drawio/tree/v24.7.5), so report those to JGraph. Do tell us if a problem means we should change what's bundled.
- **mxGraph and pako,** which the viewer loads from CDNs at pinned versions. Report problems with them to their maintainers.
- **Anything that only works if the attacker already controls the machine** that runs the build script.
