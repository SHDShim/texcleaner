# TeXCleaner

TeXCleaner is a cross-platform CustomTkinter application for cleaning LaTeX
track-changes markup and preparing projects for arXiv submission.

## Features

- Detects and cleans documents using `trackchanges.sty` or `changes.sty`.
- Keeps either the new or old revision of edited text.
- Optionally removes annotations and comments.
- Runs `arxiv-latex-cleaner` with configurable image, PDF, and bibliography
  options.
- Writes to a new file or folder by default; replacement must be enabled
  explicitly.
- Performs cleaning in a worker thread so the GUI remains responsive.
- Uses the restored TeXCleaner icon artwork on the application window and
  includes a Windows multi-resolution `.ico` for future builds.

## Development

This repository uses the `docflow` conda environment:

```bash
conda activate docflow
python -m texcleaner
```

The appearance can be selected from the command line:

```bash
python -m texcleaner --appearance dark  # default
python -m texcleaner --version
```

Run the tests with:

```bash
conda activate docflow
python -m pytest
```

For editable installation in `docflow`:

```bash
python -m pip install -e .
```

Future PyInstaller and Windows Inno Setup templates are documented in
[`packaging/README.md`](packaging/README.md). They are scaffolding only; no
executable or installer is built during development.

Python 3.10 or newer is required. Runtime dependencies are declared in
`pyproject.toml`.

## Usage

For TrackChanges or Changes documents, select a `.tex` file, choose which
revision to retain, configure the output suffix, and click **Detect & Clean**.
Automatic detection can be overridden with the Cleaner menu.

For arXiv preparation, select the project folder and configure the graphics,
bibliography, logging, and output options before clicking **Clean for arXiv**.

Outputs are created beside the input:

- `manuscript.tex` becomes `manuscript-cleaned.tex` by default.
- `project/` becomes `project-cleaned/` by default.

## License

Copyright © 2026 Dan Shim and TeXCleaner contributors.

TeXCleaner is licensed under the GNU General Public License, version 3 or
later (`GPL-3.0-or-later`). See [LICENSE](LICENSE). Source distributions must
retain the license, copyright notices, source availability, and the notices
for bundled third-party code.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the provenance,
licenses, and modification status of bundled code and direct dependencies.

## Acknowledgments

- `acceptchanges3.py` — based on work by Felix Salfner
- `pyMergeChanges.py` — based on work by Yvon Cui
- `arxiv-latex-cleaner` — Google Research
