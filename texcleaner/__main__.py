"""Command-line entry point for the TeXCleaner desktop application."""

import argparse
import builtins
from pathlib import Path
import runpy
import sys

from .version import __version__


def main():
    bundled_cleaners = {
        "--run-trackchanges-cleaner": Path("scripts") / "trackchanges-py3" / "acceptchanges3.py",
        "--run-changes-cleaner": Path("scripts") / "changes" / "pyMergeChanges.py",
    }
    for marker, relative_script in bundled_cleaners.items():
        if marker in sys.argv:
            marker_index = sys.argv.index(marker)
            script = Path(__file__).resolve().parent / relative_script
            sys.argv = [str(script), *sys.argv[marker_index + 1 :]]
            runpy.run_path(str(script), run_name="__main__")
            return

    if "--run-arxiv-cleaner" in sys.argv:
        marker_index = sys.argv.index("--run-arxiv-cleaner")
        sys.argv = ["arxiv_latex_cleaner", *sys.argv[marker_index + 1 :]]
        # arxiv-latex-cleaner parses arguments at module import time and does
        # not expose a callable CLI function. It also calls site.py's exit()
        # helper, which is absent in PyInstaller builds. Provide that helper
        # only while executing its __main__ module.
        missing = object()
        previous_exit = getattr(builtins, "exit", missing)
        builtins.exit = sys.exit
        try:
            runpy.run_module("arxiv_latex_cleaner", run_name="__main__")
        finally:
            if previous_exit is missing:
                del builtins.exit
            else:
                builtins.exit = previous_exit
        return

    parser = argparse.ArgumentParser(
        prog="texcleaner",
        description=f"TeXCleaner {__version__} - LaTeX track-changes cleaner",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--appearance",
        choices=("system", "light", "dark"),
        default="dark",
        help="GUI appearance mode (default: dark)",
    )
    args = parser.parse_args()

    from .app import main as app_main

    app_main(appearance=args.appearance.capitalize())


if __name__ == "__main__":
    main()
