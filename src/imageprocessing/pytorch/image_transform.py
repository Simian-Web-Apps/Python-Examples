"""Simian - PyTorch image transforming web app.

Uses the Python TorchVision and Pillow libraries to modify images provided by the user.
"""

from PIL import Image
import traceback

from simian.gui import Form, utils
import imageprocessing.generic
import imageprocessing.parts.image_panel as image_comp
import imageprocessing.parts.transform as transform_comp


if __name__ == "__main__":
    from simian.local import run

    run("imageprocessing.pytorch.transform_app", show_refresh=True, debug=True)


def gui_init(meta_data: dict) -> dict:
    """Initialize the app."""
    # Initialize components.
    Form.componentInitializer(
        image_panel=image_comp.initialize_images(user_image_io=True),
        description=extend_description,
    )
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
        FileSelectionChange=image_comp.file_selection_change,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def extend_description(comp):
    """Append the description with the ImagePanel and ActionList DOCs."""
    comp.content = (comp.content + image_comp.DOC).replace("\n", "<br>")


def apply_transform(meta_data: dict, payload: dict) -> dict:
    """Apply the transformations to the input image."""
    _, new_name, target_fig, orig_figure = image_comp.get_image_names(meta_data, payload)

    im = Image.open(orig_figure)

    # Create the PyTorch Vision Transform chain.
    composed_transform = transform_comp.get_composed_transform(payload)

    if composed_transform:
        try:
            # Apply the Transform to the image.
            new_image = composed_transform(im)

            if isinstance(new_image, tuple):
                new_image = new_image[0]

            if not isinstance(new_image, Image.Image):
                # new "Image" cannot be shown in the UI nor saved. Attempt to convert it to Image.
                mode = [None, "L", None, "RGB", "RGBA"][new_image.size()[0]]

                to_pil_transformer = transform_comp.get_transform("ToPILImage")(mode)
                new_image = to_pil_transformer(new_image)

            # Save the created figure in the session folder. and put it in the ResultFile.
            new_image.save(target_fig)

            # Put the created file in the ResultFile component for the user to download.
            image_comp.upload_and_show_figure(meta_data, payload, target_fig, new_name)

        except Exception as exc:
            # An error occurred. Notify the user.
            utils.addAlert(payload, f"Failed to transform the input image: {exc}", "danger")
            traceback.print_exception(exc)

    return payload
