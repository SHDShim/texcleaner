import argparse
import os

from .server import run_server
from version import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="texcleaner",
        description=f"TeXCleaner v{__version__} - LaTeX Track Changes Cleaner",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--server",
        action="store_true",
        help="Run in API server mode (default: Tkinter GUI)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Server port (used with --server, default: 8765)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server host (used with --server, default: 127.0.0.1)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        help="Server log level (used with --server, default: info)",
    )

    parser.add_argument(
        "--auth-token",
        default=os.environ.get("TEXCLEANER_AUTH_TOKEN"),
        help="Bearer token for API clients (defaults to TEXCLEANER_AUTH_TOKEN)",
    )

    args = parser.parse_args()

    if args.server:
        run_server(
            port=args.port,
            host=args.host,
            log_level=args.log_level,
            auth_token=args.auth_token,
        )
    else:
        from .app import main as app_main

        app_main()


if __name__ == "__main__":
    main()
