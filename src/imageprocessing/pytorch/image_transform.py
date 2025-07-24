"""Simian - PyTorch image transforming web app.

Uses the Python TorchVision and Pillow libraries to modify images provided by the user.
"""

import os
from pathlib import Path
from PIL import Image
import traceback

from simian.gui import Form, component, utils
import imageprocessing.generic
from imageprocessing.parts.image_panel import show_figure, initialize_images, file_selection_change

if __name__ == "__main__":
    from simian.local import run

    run("imageprocessing.pytorch.transform_app", show_refresh=True, debug=True)


def gui_init(meta_data: dict) -> dict:
    """Initialize the app."""
    # Initialize components.
    Form.componentInitializer(image_panel=initialize_images(user_image_io=True))
    form = Form(from_file=__file__)
    form.addCustomCss(imageprocessing.generic.get_css())

    return {
        "form": form,
        "navbar": {
            "title": "PyTorch Vision Transforms",
            "subtitle": "<small>Simian demo</small>",
            "logo": imageprocessing.generic.get_tasti_logo(),
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

            if not isinstance(new_image, Image.Image):
                # new "Image" cannot be shown in the UI nor saved. Attempt to convert it to Image.
                from imageprocessing.parts.transform import TRANSFORMERS

                mode = [None, "L", None, "RGB", "RGBA"][new_image.size()[0]]

                to_pil_transformer = TRANSFORMERS["PyTorch_Vision v2"]["ToPILImage"](mode)
                new_image = to_pil_transformer(new_image)

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
            show_figure(payload, target_fig, input=False)

        except Exception as exc:
            # An error occurred. Notify the user.
            utils.addAlert(payload, f"Failed to transform the input image: {exc}", "danger")
            traceback.print_exception(exc)

    return payload
