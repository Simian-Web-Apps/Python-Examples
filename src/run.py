"""Run Simian examples."""

import argparse
import logging

logging.getLogger().setLevel(logging.DEBUG)

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

# args = args_parser.parse_args()

# # Start GUI.
# Uiformio(
#     args.namespace,
#     window_title="Simian Examples",
#     size=[1920, 1080],
#     show_refresh=args.show_refresh,
#     debug=args.debug,
# )


import sys

sys.path.append(r"C:\Files\_WebFramework\Github\detectron2")
sys.path.append(r"C:\Files\_webframework\Github\Python-Extension-Component-Examples\src")


if __name__ == "__main__":
    # Uiformio("imageprocessing.annotator.image_annotator", debug=True, show_refresh=True)
    # Uiformio("imageprocessing.pytorch.image_transform", debug=True, show_refresh=True)
    # Uiformio("imageprocessing.generator.image_generator", debug=True, show_refresh=True)
    Uiformio("imageprocessing.processor.image_processor", debug=True, show_refresh=True)
    # Uiformio("imageprocessing.inpainter.image_inpainter", debug=True, show_refresh=True)
    # Uiformio("imagesliderextension.imageslider_ext", debug=True, show_refresh=True)
