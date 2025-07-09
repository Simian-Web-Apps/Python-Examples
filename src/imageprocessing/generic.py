"""Image processing generic functions."""

import os
from pathlib import Path

from simian.gui import utils


def get_css() -> str:
    """Get the custom css from the css folder."""
    with open(Path(__file__).parents[0] / "css" / "style.css", "r") as css:
        custom_css = css.read()

    return custom_css


def get_tasti_logo() -> str:
    """Get the TASTI logo."""
    return (utils.encodeImage(os.path.join(Path(__file__).parents[0] / "logo_tasti_light.png")),)
