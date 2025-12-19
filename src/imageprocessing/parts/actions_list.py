"""Action list module that defines an actions list that can be reused by other apps.

Other apps may include this module by defining a placeholder container, where the components of this
module can be added by using the 'initialize_actions' function as component initializer of the
container.

The 'apply_action' function can be used to apply actions on an input figure and write to a target
figure.
"""

import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from simian.gui import Form, component, composed_component, utils
from simian.gui.component import Component
from simian.gui.composed_component import PropertyEditor

ACTION_CLASSES = []  # Is filled at the bottom of the module.
DOC = """
It also contains a custom <code>Composed</code> Component `actions_list` with:
- an actions <code>Select</code> component with the image modifications that can be selected, and
- a Simian <code>PropertyEditor</code> Composed Component for modifying the settings of the selected actions.
"""


def _refill_actions():
    if len(ACTION_CLASSES) == 0:
        # Ensure all ImageAction subclasses are imported once.
        ACTION_CLASSES.extend(ImageAction.get_subclasses())


class ActionList(composed_component.Builder):
    def __init__(self, parent: component.Composed):
        """ActionList constructor."""
        _refill_actions()

        super().__init__()

        # Add components from JSON definition.
        parent.addFromJson(__file__.replace(".py", ".json"))


def initialize_actions(process_input_image: bool):
    """Initialize function meant for the container that is to receive the action list components."""
    # Initialize components.
    Form.componentInitializer(
        actionList=fill_action_list,
        actionList2=fill_no_image_input_action_list,
        actionSettings=PropertyEditor.get_initializer(column_label="Parameters"),
        hasAStartingImage=set_default_init(process_input_image),
    )

    def inner(parent_component: Component) -> None:
        # Fill files list component with files that are registered in the database.
        pass

    return inner


def set_default_init(value) -> Callable[[Component], None]:
    def inner(comp: Component) -> None:
        # Fill files list component with files that are registered in the database.
        comp.defaultValue = value

    return inner


def fill_action_list(action_list_comp: Component) -> None:
    """Fill the list of available actions."""
    # Assuming no subclasses of ImageAction subclasses.
    action_list_comp.defaultValue = [
        {"label": x.label, "value": x.__name__} for x in ACTION_CLASSES if x.nr_image_inputs > 0
    ]


def fill_no_image_input_action_list(action_list_comp: Component) -> None:
    """Fill the list of available actions."""
    # Assuming no subclasses of ImageAction subclasses.
    action_list_comp.defaultValue = [
        {"label": x.label, "value": x.__name__} for x in ACTION_CLASSES if x.nr_image_inputs == 0
    ]


def action_changed(_meta_data: dict, payload: dict) -> dict:
    # An action selection has changed.
    _refill_actions()
    action_param_list = {x.__name__: x.parameters for x in ACTION_CLASSES}

    image_actions = utils.getSubmissionData(payload, "imageProcessingActions")[0]

    # Changed action row bookkeeping. Get the values, and register the changed action in the data.
    changed_row_nr, action = utils.getSubmissionData(payload, "changedActionRow")[0]

    if changed_row_nr == -1:
        # Invalid selection from front-end.
        pass
    else:
        row = image_actions[changed_row_nr]["action1"]
        row["registeredAction"] = action

        if action == [""] or action == "":
            params = []
        else:
            params = action_param_list[action]

        for p in params:
            default_value = p.get("defaultValue", None)
            if (
                hasattr(default_value, "__iter__")
                and not isinstance(default_value, str)
                and all(k not in p for k in ["minLength", "maxLength"])
            ):
                # Default value is iterable, but no min or max length set. Use size of default.
                p["minLength"] = len(default_value)
                p["maxLength"] = len(default_value)

        row["actionSettings"] = PropertyEditor.prepare_values(params)

        utils.setSubmissionData(payload, "imageProcessingActions", image_actions)

    return payload


def apply_action(payload: dict, full_fig: str, target_fig: str, parent_key: str = "") -> str:
    """Applies the selected actions on the figure.

    Args:
        payload:        Event payload of the form.
        full_fig:       Full name of the figure to modify.
        target_fig:     Full name of the figure to write to.
        parent_key:     Key of container containing the actions list.

    Returns:
        A summary of the performed actions.
    """
    _refill_actions()

    # Process the action information.
    image_actions = utils.getSubmissionData(payload, "imageProcessingActions", parent=parent_key)[0]

    actions = []
    action_inputs = []
    for inp in image_actions:
        inp = inp["action1"]
        actions += [inp["action"]]
        action_inputs += [PropertyEditor.get_values(inp["actionSettings"])]

    action_dict = {cl.__name__: cl for cl in ACTION_CLASSES}
    action_summary = "; ".join(
        [action_dict[action].get_summary(*inp) for action, inp in zip(actions, action_inputs)]
    )

    # Ensure intermediate folders are also created.
    os.makedirs(os.path.split(target_fig)[0], exist_ok=True)

    for action, inp in zip(actions, action_inputs):
        try:
            action_dict[action].perform_action(full_fig, target_fig, *inp)
        except Exception as exc:
            utils.addAlert(payload, f'Unable to apply action "{action}".', "danger")
            logging.error(exc)
        full_fig = target_fig

    return action_summary


class ImageAction(ABC):
    label: str
    summary: str
    parameters: list
    nr_image_inputs = 1

    @staticmethod
    @abstractmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        raise NotImplementedError("ImageAction sub-classes must implement the action method.")

    def get_subclasses() -> list:
        return ImageAction.__subclasses__()

    @classmethod
    def get_summary(cls, *args) -> str:
        return cls.summary


class Rotate(ImageAction):
    label = "Rotate image"
    parameters = [
        {
            "label": "Rotate angle (clockwise) [degrees]",
            "datatype": "numeric",
            "defaultValue": 0,
            "min": -360,
            "max": 360,
            "required": True,
        },
    ]

    def get_summary(*args) -> str:
        return f"Rotated {args[0]:d} degrees"

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            new_image = im.rotate(-args[0], expand=True)
            new_image.save(target_file)


class Filter(ImageAction):
    label = "Filter image"
    filter_options = {
        "Median": ImageFilter.MedianFilter,
        "Min": ImageFilter.MinFilter,
        "Max": ImageFilter.MaxFilter,
        "Mode": ImageFilter.ModeFilter,
    }
    parameters = [
        {
            "label": "Filter type",
            "datatype": "select",
            "allowed": list(filter_options),
            "defaultValue": list(filter_options)[0],
            "required": True,
        },
        {
            "label": "Size [pixels]",
            "datatype": "numeric",
            "defaultValue": 3,
            "min": 1,
            "max": 9,
            "required": True,
        },
    ]

    def get_summary(*args) -> str:
        return f"Filter {args[0]:s}, size: {args[1]:d}"

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        filter_obj = Filter.filter_options[args[0]]
        with Image.open(image_file) as im:
            new_image = im.filter(filter_obj(size=args[1]))
            new_image.save(target_file)


class Rotate90Left(ImageAction):
    label = "Rotate 90 degrees counter-clockwise"
    summary = "Rotated -90 degrees"
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            new_images = im.rotate(90, expand=True)
            new_images.save(target_file)


class Rotate90Right(ImageAction):
    label = "Rotate 90 degrees clockwise"
    summary = "Rotated +90 degrees"
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            new_image = im.rotate(-90, expand=True)
            new_image.save(target_file)


class Brightness(ImageAction):
    label = "Adjust brightness."

    def get_summary(*args) -> str:
        return f"Brightness factor {args[0]:f} "

    parameters = [
        {
            "label": "Adjustment factor",
            "datatype": "numeric",
            "defaultValue": 1,
            "min": 0,
            "tooltip": "Brightness adjustment factor. 0 gives a black image, 1 is no adjustment, and higher values increase brightness.",
            "required": True,
        }
    ]

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as image:
            enhancer = ImageEnhance.Brightness(image)
            new_image = enhancer.enhance(args[0])
            new_image.save(target_file)


class Contrast(ImageAction):
    label = "Adjust contrast."

    def get_summary(*args) -> str:
        return f"Contrast factor {args[0]:f} "

    parameters = [
        {
            "label": "Adjustment factor",
            "datatype": "numeric",
            "defaultValue": 1,
            "min": 0,
            "tooltip": "Contrast adjustment factor. 0 gives a gray image, 1 is no adjustment, and higher values increase contrast.",
            "required": True,
        }
    ]

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as image:
            enhancer = ImageEnhance.Contrast(image)
            new_image = enhancer.enhance(args[0])
            new_image.save(target_file)


class Sharpness(ImageAction):
    label = "Adjust sharpness."

    def get_summary(*args) -> str:
        return f"Contrast factor {args[0]:f} "

    parameters = [
        {
            "label": "Adjustment factor",
            "datatype": "numeric",
            "defaultValue": 1,
            "tooltip": "Contrast adjustment factor. 0 gives a blurred image, 1 is no adjustment, and higher values increase sharpness.",
            "required": True,
        }
    ]

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as image:
            enhancer = ImageEnhance.Sharpness(image)
            new_image = enhancer.enhance(args[0])
            new_image.save(target_file)


class EdgeEnhance(ImageAction):
    label = "Enhance edges"
    summary = "Edges enhanced"
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            new_image = im.filter(ImageFilter.EDGE_ENHANCE)
            new_image.save(target_file)


class InvertColours(ImageAction):
    label = "Invert colours"
    summary = "Colour inversion."
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            im = im.convert("RGB")
            new_image = ImageOps.invert(im)
            new_image.save(target_file)


class Mirror(ImageAction):
    label = "Flip image horizontally"
    summary = "Mirrored"
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        with Image.open(image_file) as im:
            new_image = ImageOps.mirror(im)
            new_image.save(target_file)
