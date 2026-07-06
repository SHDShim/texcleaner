# TeXClean - LaTeX Track Changes Cleaning Tool

## Environment

**This project must be operated using the `docflow` conda environment.**

Activate the environment before running any commands:
```bash
conda activate docflow
```

## Project Overview

TeXClean is a GUI front-end for cleaning LaTeX documents of track changes markup from three different LaTeX packages:

1. **TrackChanges** - The `trackchanges.sty` package
2. **Changes** - The `changes.sty` package
3. **arXiv** - Using `arxiv-latex-cleaner` for submission preparation

## Architecture

```
texclean/
├── texclean/
│   ├── __main__.py       # Package entry point
│   ├── app.py            # Main GUI application
│   ├── wrapper.py        # Integration layer for cleaning scripts
│   └── scripts/
│       ├── trackchanges-py3/
│       │   └── acceptchanges3.py # TrackChanges CLI wrapper
│       └── changes/
│           └── pyMergeChanges.py # Changes package cleaner
└── docs/
    └── latex_track_change.md     # Original documentation
```

## Cleaning Operations

### 1. Remove TrackChanges (trackchanges.sty)

Uses `acceptchanges3.py` with flags `-c -n` to accept all changes and remove annotations.

**Command:** `python acceptchanges3.py -c -n --infile=<input> --outfile=<output>`

### 2. Remove Changes (changes.sty)

Uses `pyMergeChanges.py` with flag `-a` to accept all changes.

**Command:** `python pyMergeChanges.py -a <input> <output>`

### 3. arXiv Cleaner

Uses `arxiv-latex_cleaner` to clean and organize LaTeX files for arXiv submission.

**Command:** `arxiv_latex_cleaner <folder> --im_size 500`

## Dependencies

All dependencies must be installed in the `docflow` conda environment:

- Python 3.x (via conda)
- `arxiv-latex_cleaner` package
- Standard library: `tkinter`, `subprocess`, `os`, `shutil`

## Running the Application

```bash
conda activate docflow
python -m texclean
```