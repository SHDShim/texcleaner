"""
TeXCleaner - A GUI front-end for cleaning LaTeX track changes.

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
    generate_output_filename
)

__all__ = [
    "clean_trackchanges",
    "clean_changes",
    "clean_arxiv",
    "generate_output_filename",
    "__version__",
]