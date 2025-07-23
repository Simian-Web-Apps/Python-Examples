"""Simian image annotator.

Select a folder with images (local mode) or upload a set of images (deployed) to annotate.


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


To customize this application
 - "registered_labels.csv": with your own set of labels
 - "detection_model.py":    image detection model


- prepare a "registered_labels.csv" file and put it next to this file. It must contain the column
  header "Labels". Its rows are used as the default annotation options. New labels defined in the
  app are not added to this file.

  For instance:
  ```
  Labels
  rainbow
  unicorn
  ```


 - "detection_model.py":    image detection model
    - must have a module docstring to be included in the app description panel.
    - must implement a function `run` that accepts the image file, a threshold in %, and a flag to
        return bounding boxes or segmentations as inputs. It must return per detected object a
        classification string, an object dicts and confidence score. The object dict must contain
        the "type", "x" and "y" coordinates of the shape [in pixels] with respect to the top-left.
        Type may be one of {"rect", "circle", "line", "path"}.
"""

import glob
import importlib.util
import os
import pandas as pd
from pathlib import Path
from PIL import Image
import plotly.graph_objects as go

from simian.gui import Form, component, utils

import imageprocessing.generic


# Local mode bookkeeping to improve performance
LOCAL_FILE_LIST = dict()

DESCR_START = """Simian image annotator app to add shapes to an image and classify with labels.\n\n
"""
DESCR_LOCAL_MODE = """Select a folder with images to annotate and the annotations .csv file to write to.

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
        isDeployed=set_default_value(meta_data["mode"] == "deployed"),
        aiDetected=set_default_value(_check_has_ai()),
        description=add_description(meta_data),
        aiObjectDetectionConfidenceThreshold=setup_threshold,
        registeredLabels=set_default_value([]),
    )
    form = Form(from_file=__file__)

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
        ClearAnnotations=clear_annotations,
        DetectObjects=_detect_objects,
        LoadImage=load_first,
        ShapeNumberUpdated=shape_number,
        SubmitAnnotation=submit_and_next,
        RegisterLabel=new_label,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def load_first(meta_data: dict, payload: dict) -> dict:
    """Load the selected figures and label definitions."""
    # Get the labels next to this file.
    grow_label_list(payload, str(Path(__file__).parent / "registered_labels.csv"))

    # Get the user selected labels file.
    payload, label_file = component.File.storeUploadedFiles(meta_data, payload, "uploadedLabels")
    if len(label_file) == 1:
        # A label file was selected. Get it out of the list.
        grow_label_list(payload, label_file[0])

    # Ensure the correct mode is shown in the figure.
    payload = _select_figure_mode(payload)

    # Show the first of the figures in the plotly component.
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")
    _show_next_figure(meta_data, payload, plot_obj)
    utils.setSubmissionData(payload=payload, key="imageLoaded", data=True)

    return payload


def shape_number(meta_data: dict, payload: dict) -> dict:
    """Remove shape in the plot based on the table row being removed."""
    rowIds, _ = utils.getSubmissionData(payload, "rowId")
    registeredIds, _ = utils.getSubmissionData(payload, "registeredRowIds")
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")

    if rowIds is not None and len(removed_row := set(registeredIds) - set(rowIds)) > 0:
        # A row was removed.
        removed_index = registeredIds.index(list(removed_row)[0])

        if len(plot_obj.figure.layout.shapes) >= (removed_index + 1):
            # Recreate the shapes list, but without the shape corresponding with the removed row.
            plot_obj.figure.layout.shapes = [
                shape
                for ii, shape in enumerate(plot_obj.figure.layout.shapes)
                if ii != removed_index
            ]

    # Update the shape numbers in the plot.
    for nr, shape in enumerate(plot_obj.figure.layout.shapes):
        shape["label"] = new_shape_label(payload, nr)

    utils.setSubmissionData(payload, "loadedImage", plot_obj)
    utils.setSubmissionData(payload, "registeredRowIds", rowIds)
    return payload


def new_shape_label(payload: dict, nr: int) -> dict:
    """Create new Plotly shape label dict with nr + 1."""
    if utils.getSubmissionData(payload, "useBoxes")[0]:
        text_position = "top right"
    else:
        text_position = "middle center"

    return {"text": str(nr + 1), "textposition": text_position, "font": {"color": "yellow"}}


def grow_label_list(payload: dict, label_file: str = None, new_label: str = None) -> None:
    """Expand label list with definitions in file."""
    label_list, _ = utils.getSubmissionData(payload, "registeredLabels")

    if label_file is not None and os.path.exists(label_file):
        annotation_table = pd.read_csv(label_file, delimiter=";")
        label_list.extend(list(annotation_table["Labels"]))
    elif new_label is not None:
        label_list.append(new_label)

    utils.setSubmissionData(payload, "registeredLabels", label_list)


def clear_annotations(meta_data: dict, payload: dict) -> dict:
    # Clear the labels in the table.
    _set_annotations_table(payload, new_table=[])

    # Remove any shapes.
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")
    plot_obj.figure.layout.shapes = []
    utils.setSubmissionData(payload, "loadedImage", plot_obj)
    return payload


def _set_annotations_table(payload, new_table: list[dict]):
    """Set the contents of the annotations table and the corresponding registered row ids."""
    utils.setSubmissionData(payload, "annotations", new_table)
    utils.setSubmissionData(payload, "registeredRowIds", [row["rowId"] for row in new_table])


def new_label(meta_data: dict, payload: dict) -> dict:
    """Add a new label to the list of available options."""
    grow_label_list(payload, new_label=utils.getSubmissionData(payload, "newLabel")[0])
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

        _set_annotations_table(payload, new_table=[])

    # Get and show the next figure.
    _show_next_figure(meta_data, payload, plot_obj)

    return payload


def add_description(meta_data):
    """Update the description component based on the mode."""

    def inner(comp):
        if meta_data["mode"] == "deployed":
            txt = DESCR_START + DESCR_DEPLOYED_MODE + DESCR_APPEND
        else:  # Local
            txt = DESCR_START + DESCR_LOCAL_MODE + DESCR_APPEND

        if _check_has_ai():
            # Add detected AI image detection model description.
            import imageprocessing.annotator.detection_model as model

            txt += (
                """\nObject detection model included:
Select a confidence threshold, whether to draw boxes or segmentations in the plot, and click rerun when needed.\n\n"""
                + model.__doc__
            )

        txt = txt.removeprefix("\n")
        comp.defaultValue = txt.replace("\n", "<br>")

    return inner


def _check_has_ai() -> bool:
    spec = importlib.util.find_spec("imageprocessing.annotator.detection_model")
    return spec is not None


def set_default_value(default_value):
    """Set default value initializer function."""

    def inner(comp):
        comp.defaultValue = default_value

    return inner


def setup_plotly(plot_obj):
    """Setup the plotly component."""
    plot_obj.figure = go.Figure()
    plot_obj.figure.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})

    # Make the plot as empty as possible
    plot_obj.figure.update_xaxes(showgrid=False, range=(1, 2))
    plot_obj.figure.update_yaxes(showgrid=False, range=(1, 2))


def setup_threshold(threshold):
    if _check_has_ai():
        threshold.hidden = False
        threshold.defaultValue = 50  # [%]
    else:
        # AI Object detection module not detected. Defaults are ok.
        pass


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
    use_ai, _ = utils.getSubmissionData(payload, "useAiObjectDetection")

    if next_figure is not None and _check_has_ai() and use_ai:
        payload["followUp"] = "DetectObjects"
        utils.addAlert(payload, "Running object detection", "info")

    # Store the nice name of the figure for use in the annotations file.
    utils.setSubmissionData(payload, "imageName", nice_file_name)
    utils.setSubmissionData(payload, "fullImageName", next_figure)


def _detect_objects(meta_data, payload):
    """Use image object detection model to add shapes to the object."""
    import imageprocessing.annotator.detection_model as model

    # Get the model inputs.
    image_file, _ = utils.getSubmissionData(payload, "fullImageName")
    threshold, _ = utils.getSubmissionData(payload, "aiObjectDetectionConfidenceThreshold")
    use_boxes, _ = utils.getSubmissionData(payload, "useBoxes")

    # Run the object detection model.
    found_labels, found_objects, scores = model.run(image_file, threshold, use_boxes)

    if isinstance(found_labels, str):
        # Run method returned an error message.
        utils.addAlert(payload, found_labels, "error")
        return payload

    clear_annotations(meta_data, payload)
    plot_obj, _ = utils.getSubmissionData(payload, "loadedImage")

    if len(found_labels) == 0:
        # No objects detected. Add a message.
        utils.addAlert(
            payload, "No objects detected with the current model and threshold.", "warning"
        )

    if use_boxes:
        settings = {"line": {"color": "yellow"}}
    else:
        settings = {
            "fillcolor": "hsla(60, 100%, 50%, 90%)",
            "opacity": 0.2,
            "line": {"color": "black"},
        }

    for nr, object in enumerate(found_objects):
        plot_obj.addShape(
            object | settings | {"editable": True, "label": new_shape_label(payload, nr)}
        )

    utils.setSubmissionData(payload, "loadedImage", plot_obj)

    # Add the labels from the model to the allowed values in the labels column of the table.
    label_list, _ = utils.getSubmissionData(payload, "registeredLabels")
    label_list.extend(list(set(found_labels) - set(label_list)))
    utils.setSubmissionData(payload, "registeredLabels", label_list)

    new_annotations = [
        {
            "labels": label,
            "confidenceScore": int(score * 100),
            "shapeNumber": nr + 1,
            "rowId": "gen" + str(nr + 1),
        }
        for nr, (label, score) in enumerate(zip(found_labels, scores))
    ]
    _set_annotations_table(payload, new_table=new_annotations)

    return payload


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
