"""
TeXCleaner - Cleaning LaTeX track changes.

Supports cleaning track changes from:
- trackchanges.sty
- changes.sty
- arXiv submission preparation
"""

from .version import __version__
from .wrapper import (
    clean_trackchanges,
    clean_changes,
    clean_arxiv,
    generate_output_filename,
    detect_cleaning_module
)

__all__ = [
    "clean_trackchanges",
    "clean_changes",
    "clean_arxiv",
    "generate_output_filename",
    "detect_cleaning_module",
    "__version__",
]
