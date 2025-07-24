"""Simian image processing web app.

Modify parts of the images provided by the user.
"""

import imageprocessing.generic
from imageprocessing.parts.actions_list import ACTION_CLASSES, apply_action, initialize_actions
import imageprocessing.parts.image_panel as image_comp
from PIL import Image, ImageDraw
from simian.gui import Form, utils


def gui_init(_meta_data: dict) -> dict:
    """Initialize the app."""
    # Initialize components.
    Form.componentInitializer(
        actionGrid=initialize_actions(process_input_image=True),
        image_panel=image_comp.initialize_images(user_image_io=True, draw_input=True),
    )
    form = Form(from_file=__file__)
    form.addCustomCss(imageprocessing.generic.get_css())

    # Prepend the actions list with the Inpainting actions.
    from imageprocessing.inpainter.inpaint_actions import ShowInpaintMask, StableDiffusion2Inpaint

    ACTION_CLASSES.insert(0, StableDiffusion2Inpaint)
    ACTION_CLASSES.insert(0, ShowInpaintMask)

    return {
        "form": form,
        "navbar": {
            "title": "Image inpainting",
            "subtitle": "<small>Simian demo</small>",
            "logo": imageprocessing.generic.get_tasti_logo(),
        },
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Process app events."""
    Form.eventHandler(
        FileSelectionChange=image_comp.file_selection_change,
        ProcessFiles=process_files,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def process_files(meta_data: dict, payload: dict) -> dict:
    """Process the selected files."""
    _, new_name, target_fig, orig_figure = image_comp.get_image_names(meta_data, payload)

    im = Image.open(orig_figure)

    new_image = Image.new("1", im.size, 0)
    mask_image = ImageDraw.Draw(new_image)
    plot_obj, _ = utils.getSubmissionData(payload, "image")
    shapes = plot_obj.getShapes()

    for shape in shapes:
        if shape["type"] == "rect":
            mask_image.rectangle(list(zip(sorted(shape["x"]), sorted(shape["y"]))), 1, 1)
        elif shape["type"] == "circle":
            mask_image.ellipse(list(zip(sorted(shape["x"]), sorted(shape["y"]))), 1, 1)
        elif shape["type"] == "path":
            mask_image.polygon(list(zip(shape["x"], shape["y"])), 1, 1)

    # Prepare output locations.
    new_image.save(target_fig)
    apply_action(payload, orig_figure, target_fig)

    # Put the created file in the ResultFile component for the user to download.
    image_comp.upload_and_show_figure(meta_data, payload, target_fig, new_name)

    return payload
