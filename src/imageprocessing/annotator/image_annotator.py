"""Simian image annotator.

Select a folder with images (local mode) or upload a set of images (deployed) to annotate.

When running locally or when deploying this app:

- prepare a "registered_labels.csv" file and put it next to this file. It must contain the column
  header "Labels". Its rows are used as the default annotation options. New labels defined in the
  app are not added to this file.

  For instance:
  ```
  Labels
  rainbow
  unicorn
  ```


When running locally:
- prepare a csv file to write the annotations to with the following column headers:

```
Name;Labels;Types;Coordinates (in pixels, w.r.t. top-left)
```

The image annotations are written to the annotations csv file. The file will be appended with one
line per image containing the following information:

image name;[Shape label];[Shape types];[Shape image coordinates]
str       ;list[str]    ;list[str]    ;list[dict[list[int]]]
image.jpg;['rainbow'];['rect'];[{{'x': [68, 818], 'y': [162, 589]}]
"""

import glob
import os
import pandas as pd
from pathlib import Path
from PIL import Image
import plotly.graph_objects as go

from simian.gui import Form, component, utils

import imageprocessing.generic

# Local mode bookkeeping to improve performance
LOCAL_FILE_LIST = dict()

DESCR_LOCAL_MODE = """
Select a folder with images to annotate and the annotations .csv file to write to.

Note that on each iteration the result is written to the annotation file. So, you can close the app at any moment without losing submitted progress.
"""

DESCR_DEPLOYED_MODE = "Upload images to annotate. The annotations file can be downloaded once all figures are annotated."

DESCR_APPEND = """

Optionally, you can select a .csv file with extra label definitions. The file must have one column: 'Labels'.
You can define and add extra labels in the session, but these are not saved and will not be available the next time.
"""


def gui_init(meta_data: dict) -> dict:
    """Initialize the app."""
    Form.componentInitializer(
        loadedImage=setup_plotly,
        isDeployed=setup_deployed(meta_data),
        description=add_description(meta_data),
    )
    form = Form(from_file=__file__)
    form.addCustomCss(imageprocessing.generic.get_css())

    return {
        "form": form,
        "navbar": {
            "title": "Image annotator",
            "subtitle": "<small>Simian demo</small>",
            "logo": imageprocessing.generic.get_tasti_logo(),
        },
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Process app events."""
    Form.eventHandler(
        LoadImage=load_first,
        SubmitAnnotation=submit_and_next,
        RegisterLabel=new_label,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def load_first(meta_data: dict, payload: dict) -> dict:
    """Load the selected figures and label definitions."""
    # Get the labels next to this file.
    label_list = grow_label_list(str(Path(__file__).parent / "registered_labels.csv"))

    # Get the user selected labels file.
    payload, label_file = component.File.storeUploadedFiles(meta_data, payload, "uploadedLabels")

    if len(label_file) == 1:
        # A label file was selected. Get it out of the list.
        label_list = grow_label_list(label_file[0], label_list)

    utils.setSubmissionData(payload, "registeredLabels", label_list)

    # Ensure the correct mode is shown in the figure.
    payload = _select_figure_mode(payload)

    # Show the first of the figures in the plotly component.
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")
    _show_next_figure(meta_data, payload, plot_obj)
    utils.setSubmissionData(payload=payload, key="imageLoaded", data=True)

    return payload


def grow_label_list(label_file: str, label_list: list[str] = []) -> list[str]:
    """Expand label list with definitions in file."""
    if os.path.exists(label_file):
        annotation_table = pd.read_csv(label_file, delimiter=";")
        label_list.extend(list(annotation_table["Labels"]))

    return label_list


def new_label(meta_data: dict, payload: dict) -> dict:
    """Add a new label to the list of available options."""
    labels, _ = utils.getSubmissionData(payload, "registeredLabels")
    labels += [utils.getSubmissionData(payload, "newLabel")[0]]
    utils.setSubmissionData(payload, "registeredLabels", labels)
    utils.setSubmissionData(payload, "newLabel", "")
    return payload


def submit_and_next(meta_data: dict, payload: dict) -> dict:
    """Register the annotations in the annotations file."""
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")
    labels, _ = utils.getSubmissionData(payload, "annotations")
    figure_name, _ = utils.getSubmissionData(payload, "imageName")
    shapes = plot_obj.getShapes()

    if figure_name is None:
        # No figure being shown in the plot. Something wrong with the file. Continue with next file.
        pass
    elif len(shapes) != len(labels):
        utils.addAlert(
            payload,
            f"Number of labels rows ({len(labels)}) must match the number of shapes ({len(shapes)})",
            "danger",
        )
        return payload
    else:
        # Prepare the new label line to write to the csv file.
        label_strs = [",".join(label_dict["labels"]) for label_dict in labels]
        labels = [label.replace("'", '"') for label in label_strs]
        types = [shape["type"] for shape in shapes]
        coords = [
            {"x": [int(x) for x in shape["x"]], "y": [int(y) for y in shape["y"]]}
            for shape in shapes
        ]

        ann_file = _get_annotations_file(meta_data, payload)
        figure_name, _ = utils.getSubmissionData(payload, "imageName")
        figure_name = os.path.split(figure_name)[1]

        with open(ann_file, "a") as f:
            f.write(f"{figure_name};{labels};{types};{coords}\n")

        utils.setSubmissionData(payload, "annotations", [{"labels": []}])

    # Get and show the next figure.
    _show_next_figure(meta_data, payload, plot_obj)

    return payload


def add_description(meta_data):
    """Update the description component based on the mode."""

    def inner(comp):
        if meta_data["mode"] == "deployed":
            txt = DESCR_DEPLOYED_MODE + DESCR_APPEND
        else:  # Local
            txt = DESCR_LOCAL_MODE + DESCR_APPEND

        txt = txt.removeprefix("\n")
        comp.defaultValue = txt.replace("\n", "<br>")

    return inner


def setup_deployed(meta_data):
    """Ensure the default value for the "isDeployed component is set from the Portal."""

    def inner(comp):
        comp.defaultValue = meta_data["mode"] == "deployed"

    return inner


def setup_plotly(plot_obj):
    """Setup the plotly component."""
    plot_obj.figure = go.Figure()
    plot_obj.figure.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})

    # Make the plot as empty as possible
    plot_obj.figure.update_xaxes(showgrid=False, range=(1, 2))
    plot_obj.figure.update_yaxes(showgrid=False, range=(1, 2))


def _show_next_figure(meta_data, payload, plot_obj) -> None:
    """Get the next figure and show it in the plotly component."""
    next_figure, nice_file_name = _get_next_figure(meta_data, payload)
    try:
        _image_to_plotly(plot_obj, next_figure)
    except Exception:
        # File could not be shown, clear the plotly component.
        utils.addAlert(payload, f"Unable to show {nice_file_name}", "danger")
        _image_to_plotly(plot_obj, None)
        nice_file_name = None

    # Remove any shapes.
    plot_obj.figure.layout.shapes = []
    utils.setSubmissionData(payload, "loadedImage", plot_obj)

    # Store the nice name of the figure for use in the annotations file.
    utils.setSubmissionData(payload, "imageName", nice_file_name)


def _get_annotations_file(meta_data, payload) -> str:
    """Get the full name of the annotations file."""
    if meta_data["mode"] == "deployed":  # replace with meta_data
        full_index = os.path.join(utils.getSessionFolder(meta_data), "labels.csv")

        if not os.path.exists(full_index):
            with open(full_index, "a") as f:
                f.write("Name;Labels;Types;Coordinates (in pixels, w.r.t. top-left)\n")

    else:
        # Local mode. Index file is specified via folder and file inputs.
        folder, _ = utils.getSubmissionData(payload, "targetFolder")
        assert os.path.exists(folder), f"The selected folder does not exist: '{folder}'"

        index_file, _ = utils.getSubmissionData(payload, "indexFile")
        full_index = os.path.realpath(os.path.join(folder, index_file))

        assert os.path.exists(full_index), (
            f"Combination of the folder and Index file does not exist yet. {full_index}"
        )
    return full_index


def _get_next_figure(meta_data, payload) -> tuple[str, str]:
    """Get the name of the next figure to process."""
    nice_file_name = None

    if meta_data["mode"] == "deployed":
        # Deployed mode: Store small set of files in a Hidden component.
        current_figure, _ = utils.getSubmissionData(payload, "imageName")
        if current_figure is not None and len(current_figure) == 0:
            # No figure shown yet. Load the figures in the File input.
            payload, _ = component.File.storeUploadedFiles(meta_data, payload, "uploadedImages")
            figure_metas, _ = utils.getSubmissionData(payload, "uploadedImages")

        else:
            figure_metas, _ = utils.getSubmissionData(payload, "unprocessedImages")

        if len(figure_metas) == 0:
            next_file = None
        else:
            # Get the next file from the list of unprocessed images.
            figure_meta = figure_metas.pop(0)
            next_file = os.path.join(utils.getSessionFolder(meta_data), figure_meta["name"])
            nice_file_name = figure_meta["originalName"]

            utils.setSubmissionData(payload, "unprocessedImages", figure_metas)
    else:
        # local mode: contains a generator in a variable: could be large set: better performance.
        if len(LOCAL_FILE_LIST) == 0:
            # Get the list of images that are already annotated.
            annotations_file = _get_annotations_file(meta_data, payload)
            annotation_table = pd.read_csv(annotations_file, delimiter=";")
            annotated_files = annotation_table["Name"]

            # Find the list of files that are in the target folder.
            folder, _ = utils.getSubmissionData(payload, "targetFolder")
            folder_files = glob.glob(folder + "/*.*")

            # Create a generator to loop over the non-annotated files.
            LOCAL_FILE_LIST["gen"] = (
                file
                for file in set(folder_files)
                if os.path.split(file)[1] not in list(annotated_files)
            )

        try:
            next_file = next(LOCAL_FILE_LIST["gen"])
            nice_file_name = next_file
        except StopIteration:
            next_file = None
            LOCAL_FILE_LIST.pop("gen", None)

    if next_file is None:
        # No more files to process. Show a message and (when deployed) upload the new csv file.
        utils.addAlert(payload, "No non-annotated figures remaining.", "info")

        if meta_data["mode"] == "deployed":  # replace with meta_data
            annotations_file = _get_annotations_file(meta_data, payload)
            component.ResultFile.upload(
                file_paths=[annotations_file],
                mime_types=["text/*"],
                meta_data=meta_data,
                payload=payload,
                key="annotationsFile",
                file_names=["annotations.csv"],
            )

    return next_file, nice_file_name


def _image_to_plotly(plot_obj, selected_figure: str) -> None:
    """Put image file in Plotly background."""
    if plot_obj.figure is None:
        # When no figure loaded from the backend, insert an empty one for later use.
        plot_obj.figure = go.Figure()

    if selected_figure is None or len(selected_figure) == 0:
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


def _select_figure_mode(payload: dict) -> dict:
    """Update figure draw mode based on selected mode."""
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")
    draw_mode, _ = utils.getSubmissionData(payload, "annotationMode")

    buttons = {
        "freehandDraw": "drawclosedpath",
        "circle": "drawcircle",
        "boundingBox": "drawrect",
        "line": "drawline",
    }
    start_button = "drawrect"

    if draw_mode in buttons:
        # Specific draw mode selected. Only show this option.
        start_button = buttons[draw_mode]
        selected_buttons = [start_button]
    elif draw_mode == "any":
        selected_buttons = list(buttons.values())
    else:
        raise ValueError(f"Unexpected draw mode {draw_mode}")
    selected_buttons += ["eraseshape"]  # Selecting multiple drawn shapes not possible.

    # Plotly component should have drawing options enabled.
    plot_obj.figure.update_layout(dragmode=start_button, newshape_line_color="yellow")

    plot_obj.config.update({"modeBarButtonsToAdd": selected_buttons})
    plot_obj.config.update(
        {"modeBarButtonsToRemove": ["pan", "toImage", "zoom", "zoomin", "zoomout"]}
    )
    utils.setSubmissionData(payload, "loadedImage", plot_obj)

    return payload
