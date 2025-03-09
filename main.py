import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Haystack - Search Arista device configurations from CVaaS")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Fetch configs command
    fetch_parser = subparsers.add_parser("fetch-configs", help="Fetch device configurations from CVaaS")
    fetch_parser.add_argument("--apiserver", required=True, help="CVaaS API server URL")
    fetch_parser.add_argument("--access-token", required=True, help="CVaaS access token")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search device configurations")
    search_parser.add_argument("--query", required=True, help="Search query")

    args = parser.parse_args()
    print(args)
