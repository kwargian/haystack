import argparse
import logging

from fetch_configs import get_configs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Haystack - Search Arista device configurations from CVaaS")
    parser.add_argument(
        "--log-level",
        "-l",
        default="INFO",
        help="Log level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        metavar="LEVEL",
        type=str.upper,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Fetch configs command
    fetch_parser = subparsers.add_parser("fetch-configs", help="Fetch device configurations from CVaaS")
    fetch_parser.add_argument("--apiserver", required=True, help="CVaaS API server URL", metavar="<cluster url>")
    fetch_parser.add_argument(
        "--access-token", required=True, help="CVaaS access token file to read", metavar="cluster.tok"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search device configurations")
    search_parser.add_argument("--query", required=True, help="Search query", action="append", dest="queries")

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    logging.debug(f"Args: {args}")

    if args.command is None:
        parser.print_help()
        exit(1)
    elif args.command == "fetch-configs":
        get_configs(args.apiserver, args.access_token)
    elif args.command == "search":
        search_configs(args.query)