"""Simian image processing web app.

Uses the Python Pillow library to modify images provided by the user.
"""

import imageprocessing.generic
from imageprocessing.parts.actions_list import apply_action, DOC, initialize_actions
import imageprocessing.parts.image_panel as image_comp
from simian.gui import Form, utils


def gui_init(meta_data: dict) -> dict:
    """Initialize the app."""
    # Initialize components.
    Form.componentInitializer(
        actionGrid=initialize_actions(process_input_image=True),
        image_panel=image_comp.initialize_images(user_image_io=True),
        description=extend_description,
    )
    form = Form(from_file=__file__)
    form.addCustomCss(imageprocessing.generic.get_css())

    return {
        "form": form,
        "navbar": {
            "title": "Image processing",
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


def extend_description(comp):
    """Append the description with the ImagePanel and ActionList DOCs."""
    comp.content = (comp.content + "\n" + image_comp.DOC + DOC).replace("\n", "<br>")


def process_files(meta_data: dict, payload: dict) -> dict:
    """Process the selected files."""
    _, new_name, target_fig, orig_figure = image_comp.get_image_names(meta_data, payload)

    # Prepare output locations.
    apply_action(payload, orig_figure, target_fig)

    # Put the created file in the ResultFile component for the user to download.
    image_comp.upload_and_show_figure(meta_data, payload, target_fig, new_name)

    return payload
