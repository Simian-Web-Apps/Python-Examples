"""Simian image processing web app.

Modify parts of the images provided by the user.
"""

import os
import shutil
from pathlib import Path

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
    # Prepare output locations.
    temp_target_folder = Path(utils.getSessionFolder(meta_data)) / "processed_temp"
    os.makedirs(temp_target_folder, exist_ok=True)

    # Get the full and relative path and extension of the image file.
    selected_figure, _ = utils.getSubmissionData(payload, "inputFile")
    full_fig = Path(utils.getSessionFolder(meta_data)) / selected_figure[0]["name"]
    name, ext = os.path.splitext(selected_figure[0]["originalName"])
    plot_obj, _ = utils.getSubmissionData(payload, "image")
    fig = name + "_mod_" + ext

    im = Image.open(full_fig)

    new_image = Image.new("1", im.size, 0)
    mask_image = ImageDraw.Draw(new_image)
    shapes = plot_obj.getShapes()

    for shape in shapes:
        if shape["type"] == "rect":
            mask_image.rectangle(list(zip(sorted(shape["x"]), sorted(shape["y"]))), 1, 1)
        elif shape["type"] == "circle":
            mask_image.ellipse(list(zip(sorted(shape["x"]), sorted(shape["y"]))), 1, 1)
        elif shape["type"] == "path":
            mask_image.polygon(list(zip(shape["x"], shape["y"])), 1, 1)

    # Prepare output locations.
    target_fig = str(temp_target_folder / fig)
    new_image.save(target_fig)
    apply_action(payload, full_fig, target_fig)

    # Put the created file in the ResultFile component for the user to download.
    image_comp.upload_and_show_figure(meta_data, payload, target_fig, fig)

    # Clear session folder to remove temp figures again.
    shutil.rmtree(temp_target_folder, ignore_errors=True)

    return payload
