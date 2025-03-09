import argparse
import logging
import duckdb
import pathlib

from fetch_configs import get_configs, DeviceInfo
from search import search_configs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Haystack - Search Arista device configurations from CVaaS")
    parser.add_argument(
        "--log-level",
        "-l",
        default="WARNING",
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
    logging.info(f"Args: {args}")

    if args.command is None:
        parser.print_help()
        exit(1)
    elif args.command == "fetch-configs":
        devices = get_configs(args.apiserver, args.access_token)

        # device configs retrieved, time to blow away our current duckdb file and write a new one
        logging.info("Destroying existing duckdb file")
        if pathlib.Path("devices.duckdb").exists():
            pathlib.Path("devices.duckdb").unlink()

        logging.info("Creating new duckdb file")
        with duckdb.connect("devices.duckdb") as conn:
            # create table
            conn.execute("CREATE TABLE devices (hostname TEXT, serial_number TEXT, config TEXT)")

            # prepare data for bulk insert
            device_data = [(device.hostname, device.serial_number, device.config) for device in devices]
            logging.info(f"Inserting {len(device_data)} rows into devices table")
            conn.executemany("INSERT INTO devices (hostname, serial_number, config) VALUES (?, ?, ?)", device_data)

            # create fts index
            conn.execute("PRAGMA create_fts_index('devices', 'serial_number', 'config')")
    elif args.command == "search":
        if not pathlib.Path("devices.duckdb").exists():
            logging.error("devices.duckdb does not exist, please run fetch-configs first")
            exit(1)
        else:
            with duckdb.connect("devices.duckdb") as conn:
                search_configs(args.queries, conn)
