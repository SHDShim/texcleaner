# TeXClean

A GUI front-end for cleaning LaTeX documents of track changes markup.

## Features

TeXClean supports cleaning track changes from three different LaTeX packages:

1. **TrackChanges** - For documents using `trackchanges.sty`
2. **Changes** - For documents using `changes.sty`
3. **arXiv** - For preparing documents for arXiv submission

## Installation

### From PyPI (Recommended)

```bash
pip install texclean
```

After installation, you can run the application with:

```bash
texclean
```

### From Source

```bash
git clone https://github.com/yourusername/texclean.git
cd texclean
pip install -e .
```

## Requirements

- Python 3.8+
- `arxiv-latex-cleaner` (installed automatically with pip)

## Usage

1. Run the application:

```bash
texclean
```

   Or if running from source:

```bash
python -m texclean.app
```

2. Select your input file or folder:
   - For **TrackChanges** and **Changes**: Select a `.tex` file
   - For **arXiv**: Select the project folder containing your LaTeX files

3. Choose the cleaning option:
   - **Remove TrackChanges**: Accepts all changes and removes annotations from `trackchanges.sty`
   - **Remove Changes**: Accepts all changes from `changes.sty`
   - **Clean for arXiv**: Removes comments, resizes images, and organizes files for submission

4. Click **Clean** to process the file

## Output

- **TrackChanges/Changes**: Creates a new file with `_no_track` or `_cleaned` suffix
- **arXiv**: Creates a new folder with `_arXiv` suffix

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

## Acknowledgments

- `acceptchanges3.py` - Felix Salfner (GPL)
- `pyMergeChanges.py` - Y. Cui (GPL)
- `arxiv-latex-cleaner` - Google Research