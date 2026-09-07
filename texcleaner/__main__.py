"""Command-line entry point for the TeXCleaner desktop application."""

import argparse

from .version import __version__


def main():
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
