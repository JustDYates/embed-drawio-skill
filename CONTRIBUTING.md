# Contributing

Thanks for your interest in improving the draw.io viewer skill. This guide explains how to set up, test and submit a change.

**Security problems:** please don't open an issue. Follow [SECURITY.md](SECURITY.md) instead.

## Before you start

For anything bigger than a small fix, open an issue first to discuss it. This matters most for:

- adding a shape pack
- changing what's bundled in `assets/`
- changing the workflow in `SKILL.md`

## Setting up

You only need Python 3.9 or later. The build script uses the standard library only, so there's nothing to install, and contributions must keep it that way.

```bash
git clone https://github.com/JustDYates/embed-drawio-skill.git
cd embed-drawio-skill
python3 scripts/build_viewer.py --out viewer.html
```

## Testing your change

Before you open a pull request:

1. **Build the sample.** Run `python3 scripts/build_viewer.py --out viewer.html` with no diagram. Check that it lists three pages and that the `UNSUPPORTED` line says `none`.
2. **Build a diagram that uses your change,** for example a file with shapes from a pack you've added.
3. **Open the built page in a browser.** Check that the diagram draws correctly, in both light and dark mode.
4. **Delete the built HTML.** Don't commit it.

If you change how paths or XML are handled in `build_viewer.py`, also check that these are still refused:

- paths outside the allowed folders, such as `--out ../x.html`
- files with the wrong extension
- XML that declares entities

Every pull request also runs these automatic checks, and they must pass:

- the [ASH](https://github.com/awslabs/automated-security-helper) security scan, including bandit
- CodeQL
- SonarCloud

## Commits

- **Sign every commit.** The `main` branch only accepts signed commits, so a pull request with unsigned commits can't be merged. GitHub's guide to [signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits) explains how to set this up with GPG, SSH or S/MIME.
- **Use [Conventional Commits](https://www.conventionalcommits.org/)** for commit messages: `feat:`, `fix:`, `docs:`, `ci:`, `chore:` and so on. Add a scope where it helps, for example `fix(build_viewer): ...`.
- **Consider using your GitHub noreply email** if you'd rather not publish your personal email address in the commit history.

## Bundled third-party files

Everything in `assets/shapes/`, `assets/stencils/`, `assets/images/` and `assets/styles/` comes from draw.io release **v24.7.5**. That's deliberate: later releases use a different licence, and much of their code doesn't work with mxGraph 4.2.2. `SKILL.md` and `THIRD_PARTY_NOTICES.md` explain the details.

If you add or change a bundled file:

- take it from v24.7.5 only
- change it as little as possible. Removing whitespace and compressing are fine; anything more needs a good reason
- update `THIRD_PARTY_NOTICES.md` with its source, its licence and any changes you made

## Other guidelines

- **Don't edit a built HTML page by hand.** Change `assets/viewer-template.html` or `build_viewer.py`, then rebuild.
- **Keep `SKILL.md` working in both places the skill runs:** the claude.ai sandbox and Claude Code.
- **Update `README.md`** if your change affects how people install or use the skill.

## Licence

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE), the same licence as this project's own code.
