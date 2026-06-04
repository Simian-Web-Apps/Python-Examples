"""Run Simian examples."""

import argparse

from simian.local import Uiformio

args_parser = argparse.ArgumentParser(
    description="Simian Examples.",
    epilog="https://github.com/Simian-Web-Apps/Python-Examples",
)

args_parser.add_argument(
    "namespace",
    help="the namespace of the Simian app",
)

args_parser.add_argument(
    "-r",
    "--show-refresh",
    action="store_true",
    default=False,
    help="show the refresh button",
)

args_parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    help="open the debugger",
)

args = args_parser.parse_args()

# Start GUI.
Uiformio(
    args.namespace,
    window_title="Simian Examples",
    size=[1920, 1080],
    show_refresh=args.show_refresh,
    debug=args.debug,
)
