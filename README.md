# TeXCleaner

A GUI front-end for cleaning LaTeX documents of track changes markup.

## Features

TeXCleaner supports cleaning track changes from three different LaTeX packages:

1. **TrackChanges** - For documents using `trackchanges.sty`
2. **Changes** - For documents using `changes.sty`
3. **arXiv** - For preparing documents for arXiv submission

## Installation

### From PyPI (Recommended)

```bash
pip install texcleaner
```

After installation, you can run the application with:

```bash
texcleaner
```

### From Source

```bash
git clone https://github.com/yourusername/texcleaner.git
cd texcleaner
pip install -e .
```

## Requirements

- Python 3.10+
- `arxiv-latex-cleaner` (installed automatically with pip)
- Tkinter for the legacy Python GUI, or macOS 13+ and a `docflow` conda
  environment for the native SwiftUI application

## Usage

1. Run the application:

```bash
texcleaner
```

   Or if running from source:

```bash
python -m texcleaner.app
```

2. Select your input file or folder:
   - For **TrackChanges** and **Changes**: Select a `.tex` file
   - For **arXiv**: Select the project folder containing your LaTeX files

3. Choose the cleaning option:
   - **Remove TrackChanges**: Accepts all changes and removes annotations from `trackchanges.sty`
   - **Remove Changes**: Accepts all changes from `changes.sty`
   - **Clean for arXiv**: Removes comments, resizes images, and organizes files for submission

4. Click **Clean** to process the file

### API mode

The backend API requires a bearer token. Pass one explicitly with
`--auth-token` or set `TEXCLEANER_AUTH_TOKEN`; do not expose the server on a
network interface without a protected token.

```bash
texcleaner --server --auth-token "change-me"
```

## Output

- **TrackChanges/Changes**: Creates a new file with the selected suffix
  (default: `-cleaned`)
- **arXiv**: Creates a new folder with the selected suffix (default:
  `-cleaned`)

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

## Acknowledgments

- `acceptchanges3.py` - Felix Salfner (GPL)
- `pyMergeChanges.py` - Y. Cui (GPL)
- `arxiv-latex-cleaner` - Google Research
