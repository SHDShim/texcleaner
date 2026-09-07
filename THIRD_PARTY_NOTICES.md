# Third-Party Notices

This file records the provenance and licensing of third-party software used by
TeXCleaner. It is informational and does not replace the applicable license
texts. TeXCleaner as a whole is distributed under `GPL-3.0-or-later`; the full
text is in [LICENSE](LICENSE).

## Source code included in this repository

### accept.py / acceptchanges3.py

- Original author and copyright: Copyright © 2006 Felix Salfner
  (`salfner@informatik.hu-berlin.de`)
- Original work: `accept.py` version 0.2, distributed with the historical
  `trackchanges.sty` package
- Original license: `GPL-2.0-or-later`
- Included file:
  `texcleaner/scripts/trackchanges-py3/acceptchanges3.py`
- Modifications: converted to Python 3; replaced line-oriented parsing with
  recursive parsing for multiline and nested commands; added reject mode and
  UTF-8-safe batch behavior

The modified file is distributed under `GPL-3.0-or-later`, which is permitted
by the original license's later-version option. The original copyright notice
and a prominent modification notice are retained in the source file.

### pyMergeChanges.py

- Original author and copyright: Copyright © 2018 Yvon Cui
- Upstream project: [the LaTeX changes package](https://gitlab.com/ekleinod/changes)
- Upstream file: `scripts/changes/pyMergeChanges.py`
- Original license: `GPL-3.0-or-later`
- Included file: `texcleaner/scripts/changes/pyMergeChanges.py`
- Modifications: replaced line-oriented parsing with recursive parsing for
  multiline and nested commands; added comment and escaped-brace handling;
  improved validation and error handling

The modified file remains under `GPL-3.0-or-later`. The original copyright
notice and a prominent modification notice are retained in the source file.

## Dependencies installed separately

The following direct dependencies are declared in `pyproject.toml`. Their
source is not copied into this repository; normal Python package installation
retrieves them separately with their own metadata and license files.

### CustomTkinter

- Copyright © 2023 Tom Schimansky
- Source: [TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- License: MIT License

### arxiv-latex-cleaner

- Copyright © Google LLC
- Source: [google-research/arxiv-latex-cleaner](https://github.com/google-research/arxiv-latex-cleaner)
- License: Apache License 2.0
- Note: the project states that it is not an officially supported Google
  product

Python and Tk/Tkinter are provided by the selected Python distribution rather
than copied into this repository. Their license information is supplied with
that distribution.

## Distribution checklist

For a GitHub source release:

1. Include `LICENSE`, this notice file, and all source files.
2. Preserve copyright, SPDX, attribution, and modification notices in the two
   bundled cleaner scripts.
3. Mark future modifications to bundled third-party files clearly.
4. Do not describe TeXCleaner as endorsed by any upstream author or project.

If binaries or installers are distributed later, review the exact dependency
versions included in that artifact and bundle their complete license and
notice texts. Also provide the corresponding source in the manner required by
GPL-3.0-or-later. This repository currently does not build or distribute such
artifacts.
