"""Image Panel module that defines an input and result image panel that can be reused by other apps.

Other apps may include this module by defining a placeholder container, where the components of this
module can be added.
"""

import os.path
from pathlib import Path
from typing import Callable

from PIL import Image
import plotly.graph_objects as go
from simian.gui import Form, component, composed_component, utils


class ImagePanel(composed_component.Builder):
    def __init__(self, parent: component.Composed):
        """ImagePanel constructor."""
        super().__init__()

        # Add components from JSON definition.
        parent.addFromJson(__file__.replace(".py", ".json"))

        # Add the Image slider CSS and javascript code to the Form.
        folder = Path(__file__).parents[0] / "slider"
        with open(folder / "styles.css", "r") as css:
            Form.addCustomCss(css.read())

        for name in ["index.js", "simian-imageslider-extension.js"]:
            with open(folder / name, "r") as js:
                Form.addCustomJavaScript(js.read())


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
        image=_setup_plotly(draw_input),
        resultFigure=_setup_plotly(),
        imageComparison=_setup_slider,
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


def _setup_plotly(allow_draw: bool = False) -> Callable:
    """Setup Plotly components."""

    def inner(plot_obj):
        plot_obj.figure = go.Figure()
        plot_obj.figure.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, dragmode=False)
        plot_obj.defaultValue["config"].update(
            {"modeBarButtonsToRemove": ["pan", "zoom", "zoomin", "zoomout"]}
        )

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


def _setup_slider(slider):
    """Setup the image slider component."""
    slider.content = """
<img-comparison-slider class="img-comparison-slider w-100">
    <figure slot="first" class="before">
        <img class="w-100">
        <figcaption>Before</figcaption>
    </figure>
    <figure slot="second" class="after">
        <img class="w-100">
        <figcaption>After</figcaption>
    </figure>
</img-comparison-slider>
"""

    slider.defaultValue = {
        "sliderValue": 50,
        "direction": "horizontal",
        "img1Url": None,
        "img2Url": None,
    }


def file_selection_change(meta_data: dict, payload: dict) -> dict:
    """Process file selection change.

    When a figure is selected, show it in the app. Otherwise notify none selected.
    """
    payload, selected_figure = component.File.storeUploadedFiles(meta_data, payload, "inputFile")
    has_image = len(selected_figure) != 0
    utils.setSubmissionData(payload, "hasImage", has_image)

    if has_image:
        selected_figure = selected_figure[0]

    # Show the selected image in the input Plotly component.
    show_figure(payload, selected_figure, input=True)

    # Remove any images from the Result Plotly component.
    show_figure(payload, "", input=False)

    return payload


def show_figure(payload, selected_figure: str, input: bool = True):
    if input:
        plot_key = "image"
    else:
        plot_key = "resultFigure"

    plot_obj, _ = utils.getSubmissionData(payload, plot_key)
    image_to_plotly(plot_obj, selected_figure)
    utils.setSubmissionData(payload, key=plot_key, data=plot_obj)

    if not input:
        utils.setSubmissionData(payload, "hasResult", os.path.isfile(selected_figure))


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
