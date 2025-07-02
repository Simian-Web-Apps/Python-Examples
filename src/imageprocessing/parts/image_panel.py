"""Image Panel module that defines an input and result image panel that can be reused by other apps.

Other apps may include this module by defining a placeholder container, where the components of this
module can be added.
"""

from typing import Callable

import plotly.graph_objects as go
from PIL import Image
from simian.gui import Form, component, composed_component, utils


class ImagePanel(composed_component.Builder):
    def __init__(self, parent: component.Composed):
        """ImagePanel constructor."""
        super().__init__()

        # Add components from JSON definition.
        parent.addFromJson(__file__.replace(".py", ".json"))


def initialize_images(
    user_image_io: bool = False,
    draw_input: bool = False,
    input_label: str = None,
    use_input_image: bool = True,
) -> Callable:
    """Initialize function for the ImagePanel component.

    Args:
        draw_input:     Allow drawing shapes in the input image.
        input_label:    Change the label of the input image column.
    """
    Form.componentInitializer(
        inputFile=change_props({"hidden": not (user_image_io and use_input_image)}),
        resultFile=change_props({"hidden": not user_image_io}),
        imageName=change_props({"hidden": use_input_image}),
        imageLabel=change_input_label(input_label),
        image=setup_plotly(draw_input),
        resultFigure=setup_plotly(),
    )

    def inner(comp):
        pass

    return inner


def change_props(new_props: dict):
    """Modify component properties."""

    def inner(comp):
        for key, value in new_props.items():
            setattr(comp, key, value)

    return inner


def change_input_label(new_label: str):
    """Change the label shown above the input image."""

    def inner(comp):
        if new_label is not None:
            comp.content = new_label

    return inner


def setup_plotly(allow_draw: bool = False) -> Callable:
    """Setup Plotly components."""

    def inner(plot_obj):
        plot_obj.figure = go.Figure()
        plot_obj.figure.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})

        if allow_draw:
            # Plotly component should have drawing options enabled.
            plot_obj.figure.update_layout(
                dragmode="drawclosedpath",
                newshape_line_color="white",
                newshape_fillcolor="white",
            )

            plot_obj.defaultValue["config"].update(
                {
                    "modeBarButtonsToAdd": [
                        "drawclosedpath",
                        "drawcircle",
                        "drawrect",
                        "eraseshape",
                    ]
                }
            )

        # Make the plot as empty as possible
        plot_obj.figure.update_xaxes(showgrid=False, range=(1, 2))
        plot_obj.figure.update_yaxes(showgrid=False, range=(1, 2))

    return inner


def image_to_plotly(plot_obj, selected_figure: str) -> None:
    """Put image file in Plotly background."""
    if plot_obj.figure is None:
        # When no figure loaded from the backend, insert an empty one for later use.
        plot_obj.figure = go.Figure()

    if len(selected_figure) == 0:
        img_width = img_height = 1
        image_setup = [{"source": None}]
    else:
        base64_image = utils.encodeImage(selected_figure)

        im = Image.open(selected_figure)
        img_width, img_height = im.size

        image_setup = [
            {
                "source": base64_image,
                "xref": "x",
                "yref": "y",
                "xanchor": "left",
                "yanchor": "top",
                "x": 1,
                "y": 1,
                "sizex": img_width,
                "sizey": img_height,
                "layer": "below",
            }
        ]

    plot_obj.figure.update_layout(images=image_setup, margin={"l": 0, "r": 0, "t": 0, "b": 0})
    plot_obj.figure.update_xaxes(showgrid=False, range=(1, img_width + 1))
    plot_obj.figure.update_yaxes(showgrid=False, scaleanchor="x", range=(img_height + 1, 1))
