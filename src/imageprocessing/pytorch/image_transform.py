"""Simian - PyTorch image transforming web app.

Uses the Python TorchVision and Pillow libraries to modify images provided by the user.
"""

import os
from pathlib import Path
from PIL import Image
import traceback

from simian.gui import Form, component, utils
import imageprocessing.parts.image_panel

if __name__ == "__main__":
    from simian.local import run

    run("imageprocessing.pytorch.transform_app", show_refresh=True, debug=True)


def gui_init(meta_data: dict) -> dict:
    """Initialize the app."""
    # Initialize components.
    Form.componentInitializer(
        image_panel=imageprocessing.parts.image_panel.initialize_images(user_image_io=True)
    )
    form = Form(from_file=__file__)

    with open(Path(__file__).parents[1] / "css" / "style.css", "r") as css:
        form.addCustomCss(css.read())

    return {
        "form": form,
        "navbar": {
            "title": "PyTorch Vision Transforms",
            "subtitle": "<small>Simian demo</small>",
            "logo": utils.encodeImage(
                os.path.join(Path(__file__).parents[1] / "logo_tasti_light.png")
            ),
        },
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Process app events."""
    Form.eventHandler(
        ApplyTransform=apply_transform,
        FileSelectionChange=file_selection_change,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


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
    plot_obj, _ = utils.getSubmissionData(payload, "image")
    imageprocessing.parts.image_panel.image_to_plotly(plot_obj, selected_figure)
    utils.setSubmissionData(payload, key="image", data=plot_obj)

    # Remove any images from the Result Plotly component.
    plot_obj, _ = utils.getSubmissionData(payload, "resultFigure")
    imageprocessing.parts.image_panel.image_to_plotly(plot_obj, "")
    utils.setSubmissionData(payload, key="resultFigure", data=plot_obj)
    utils.setSubmissionData(payload, "hasResult", False)

    return payload


def apply_transform(meta_data: dict, payload: dict) -> dict:
    """Apply the transformations to the input image."""
    import imageprocessing.parts.transform

    selected_figure, _ = utils.getSubmissionData(payload, "inputFile")
    sessionFolder = Path(utils.getSessionFolder(meta_data))
    full_fig = sessionFolder / selected_figure[0]["name"]
    name, ext = os.path.splitext(selected_figure[0]["originalName"])
    plot_obj, _ = utils.getSubmissionData(payload, "image")
    fig = name + "_mod_" + ext
    im = Image.open(full_fig)

    # Create the PyTorch Vision Transform chain.
    composed_transform = imageprocessing.parts.transform.get_composed_transform(payload)

    if composed_transform:
        try:
            # Apply the Transform to the image.
            new_image = composed_transform(im)

            if isinstance(new_image, tuple):
                new_image = new_image[0]
            elif not isinstance(new_image, Image.Image):
                utils.addAlert(
                    payload,
                    "Transform sequence should return a Pillow image. Add a ToPILImage Transform.",
                    "warning",
                )

            # Save the created figure in the session folder. and put it in the ResultFile.
            target_fig = str(sessionFolder / fig)
            new_image.save(target_fig)

            if os.path.isfile(target_fig):
                component.ResultFile.upload(
                    file_paths=[target_fig],
                    mime_types=["image/*"],
                    meta_data=meta_data,
                    payload=payload,
                    key="resultFile",
                    file_names=[fig],
                )

            # Show the processed file in the web app.
            plot_obj, _ = utils.getSubmissionData(payload, "resultFigure")
            imageprocessing.parts.image_panel.image_to_plotly(plot_obj, target_fig)
            utils.setSubmissionData(payload, "resultFigure", plot_obj)
            utils.setSubmissionData(payload, "hasResult", True)

        except Exception as exc:
            # An error occurred. Notify the user.
            utils.addAlert(payload, f"Failed to transform the input image: {exc}", "danger")
            traceback.print_exception(exc)

    return payload
