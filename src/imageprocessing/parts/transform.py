"""Transform composed component.

PyTorch Vision Transforms setup component.
"""

import enum
import inspect
import importlib
import json
import re
from typing import List, Tuple, Sequence
import torch
from simian.gui import Form, component, composed_component, utils


TRANSFORMERS = {}
# Class constructor, probabilities
CONTAINERS = {
    "PyTorch_Vision v2": {
        # Name: (Constructor, probabilities type.)
        "Compose": [None, "None"],
        "RandomApply": [None, "Overall"],
        "RandomChoice": [None, "PerTransform"],
        "RandomOrder": [None, "None"],
    }
}

TORCH_TYPES = [
    "torch." + x
    for x in [
        "float64",
        "float32",
        "float16",
        "bfloat16",
        "complex128",
        "complex64",
        "uint8",
        "int64",
        "int32",
        "int8",
        "bool",
    ]
]


class TransformList(composed_component.Builder):
    """TransformList composed component.

    DataGrid with Transform selection and inputs selection.
    """

    def __init__(self, parent: component.Composed):
        super().__init__()

        # Import the available PyTorch Vision Transform classes.
        get_transformers()

        # Ensure the composed component' components are filled with the appropriate Torch classes.
        Form.componentInitializer(
            availableTransforms=fill_transform_list,
            availableMethods=fill_methods_list,
            parameters=composed_component.PropertyEditor.get_initializer(
                column_label="Parameters", addAnother="Add value"
            ),
        )

        # Add components from JSON definition.
        parent.addFromJson(__file__.replace(".py", ".json"))


def get_composed_transform(payload: dict):
    """Create a Transform combination from the selected property values.

    Returns:
        Combination of Transforms, or None.
    """
    combo_method, _ = utils.getSubmissionData(payload, "combinationMethod")
    overall_prob, _ = utils.getSubmissionData(payload, "overallProbability")
    transform_table, _ = utils.getSubmissionData(payload, "tranforms")
    trans_list = []
    trans_probs = []

    for transform_row in transform_table:
        row = transform_row["transform"]
        name = row["registeredTransform"]
        transformer = TRANSFORMERS["PyTorch_Vision v2"][name]
        values = composed_component.PropertyEditor.get_values(row["parameters"])

        # Get the probability per Transform row.
        trans_probs.append(row["applicationProbability"])

        # Build the Transform instances based on the constructors and selected inputs.
        values, _ = convert_values(transformer, values)
        try:
            trans_list += [transformer(*values)]
        except Exception as exc:
            utils.addAlert(payload, f"Failed to create Transform {name}: {exc}", "danger")

    if len(trans_list) == 0 or combo_method is None:
        ct = None
    else:
        combo_constructor, prob_type = CONTAINERS["PyTorch_Vision v2"][combo_method]

        if prob_type == "PerTransform":
            probs = [trans_probs]
        elif prob_type == "Overall":
            probs = [overall_prob]
        else:
            probs = []

        # Create the combination of Transforms.
        ct = combo_constructor(trans_list, *probs)

    return ct


def get_transformers(version_nr: int = 2):
    """Import the available PyTorch Vision Transform classes."""
    "torch.nn.Module"
    from torchvision.transforms.v2 import Transform  # 'Delay' import: future support older versions

    v2_classes = _get_transformers("torchvision.transforms.v2", Transform)

    for skip_mod in ["_container", "_deprecated"]:  # "_type_conversion",
        skip_classes = _get_transformers(f"torchvision.transforms.v2.{skip_mod}", Transform)

        for name in skip_classes.keys():
            v2_classes.pop(name, None)

    TRANSFORMERS.update({"PyTorch_Vision v2": v2_classes})

    # Get the PyTorch Vision combination classes and put the constructors in the list.
    containers = _get_transformers("torchvision.transforms.v2._container", Transform)
    containers.pop("Transform")

    for key, constr in containers.items():
        CONTAINERS["PyTorch_Vision v2"][key][0] = constr


def fill_methods_list(comp: component.Select) -> None:
    """Fill the available combination method list."""
    comp.defaultValue = [{"label": x, "value": x} for x in CONTAINERS["PyTorch_Vision v2"].keys()]


def fill_transform_list(comp: component.Select) -> None:
    """Fill the available Transforms list."""
    comp.defaultValue = [{"label": x, "value": x} for x in TRANSFORMERS["PyTorch_Vision v2"].keys()]


def _get_transformers(module_name: str, super_class: str) -> dict[str, callable]:
    """Return the subclasses of the super class that are available in the given module."""
    try:
        mod = importlib.import_module(module_name)
        members = inspect.getmembers(mod)
        classes = {
            member[0]: member[1]
            for member in members
            if inspect.isclass(member[1]) and issubclass(member[1], super_class)
        }

    except ImportError:
        classes = {}
    return classes


def NewTransformer(meta_data: dict, payload: dict) -> dict:
    """New transformer has been selected"""

    transform_table, _ = utils.getSubmissionData(payload, "tranforms")
    for row in transform_table:
        row = row["transform"]

        old_sel = row["registeredTransform"]
        if (transform := row["selectedTransformer"]) != old_sel:
            # New Transformer selected in this row.
            row["registeredTransform"] = transform
            if transform == [""] or transform == "":
                params = []
                doc_dict = {}
            else:
                transformer = TRANSFORMERS["PyTorch_Vision v2"][transform]
                params, doc_dict = get_params(transformer)

            row["tranformer_doc"] = doc_dict.get("main", None)
            row["parameters"] = composed_component.PropertyEditor.prepare_values(params)

    utils.setSubmissionData(payload, "tranforms", transform_table)

    return payload


def NewContainer(meta_data: dict, payload: dict) -> dict:
    """A new transformer combination method has been selected."""
    combo_method, _ = utils.getSubmissionData(payload, "combinationMethod")

    if combo_method != "":
        utils.setSubmissionData(
            payload, "probType", CONTAINERS["PyTorch_Vision v2"][combo_method][1]
        )

    return payload


def process_callable(wrapped_func: callable) -> callable:
    """Inspect transform callable to detect expected input parameters."""

    def inner(func, *args) -> Tuple[List[dict], dict]:
        spec = inspect.getfullargspec(func)
        params = []

        # Get the real input parameters and their corresponding docstrings.
        real_args = spec.args
        if "self" in real_args:
            real_args.remove("self")
        doc_dict = _split_docs(func.__doc__, real_args)

        defaults = _ensure_defaults_list(spec.defaults, len(real_args))

        if len(args) == 0:
            ii_args = [[]] * len(real_args)
        else:
            ii_args = list(zip(*args))

        # Process the input arguments of the Transform function.
        for ii in range(0, len(real_args)):
            label = real_args[ii]
            default = defaults[ii]
            annotation = str(spec.annotations.get(label, None))
            par_doc = doc_dict.get(label, "Undocumented")

            params.append(wrapped_func(label, default, annotation, par_doc, *ii_args[ii]))

        return params, doc_dict

    return inner


@process_callable
def convert_values(label, default, annotation, par_doc, value) -> Tuple[List[dict], dict]:
    """Convert values to the expected data types."""
    if isinstance(default, enum.Enum):
        value = default.__class__[value]

    if "float" in annotation:
        # Values are set as text in the app. "1" is converted to int(1), which may cause crashes.
        if isinstance(value, int):
            value = float(value)
        elif hasattr(value, "__iter__"):
            value = [float(val) if isinstance(val, int) else val for val in value]
    elif "dtype" in annotation:
        value = eval(value)  # Value stems from a Select component.

    return value


@process_callable
def get_params(label, default, annotation, par_doc) -> Tuple[List[dict], dict]:
    """Get definition of expected input parameters."""
    extra_options = {}

    if "Sequence" in annotation:
        extra_options = extra_options | {"minLength": 1, "maxLength": 100}
    elif isinstance(default, Sequence):
        extra_options = extra_options | {"minLength": len(default), "maxLength": len(default)}

    if isinstance(default, enum.Enum):
        # Use a Select component with the Enum options.
        type_str = "select"
        extra_options = extra_options | {"allowed": list(default.__class__.__members__.keys())}
        default = default.name
    elif "dtype" in annotation:
        type_str = "select"
        extra_options = extra_options | {"allowed": TORCH_TYPES}
        default = str(default)
    elif "float" in annotation:
        type_str = "numeric"
    elif "int" in annotation:
        type_str = "numeric"
        extra_options = extra_options | {"decimalLimit": 0}
    elif "str" in annotation:
        type_str = "text"
    elif "bool" in annotation:
        type_str = "boolean"
    else:
        type_str = "text"

    try:
        json.dumps(default)
    except TypeError:
        default = "Not settable"

    val = {
        "datatype": type_str,
        "label": label.capitalize(),
        "defaultValue": default,
        "tooltip": par_doc,
        "required": "optional)" not in par_doc and "NoneType" not in annotation,
    } | extra_options

    return val


def _ensure_defaults_list(val, nr_args):
    # Put the default values from the inspected function in a list.
    if isinstance(val, Sequence):
        pass
    else:
        val = [val]

    # If Not all input arguments have a default, assume the first arguments do not have one.
    extra = nr_args - len(val)
    if extra > 0:
        val = [None] * extra + [*val]

    return val


def _split_docs(doc_str: str, arg_names) -> dict:
    """Split docstring into main, and input arguments parts."""
    if doc_str is None:
        return {}

    # Split the docstring on the Args, Returns and Raises keywords. First part is the main docstring
    # The part after Args: contains the input arguments descriptions.
    splits = re.split("(Args:\n|Returns:\n|Raises:\n)", doc_str)
    docs = {"main": splits[0]}

    if "Args:\n" in splits:
        # Split the input arguments docstring block on the names of the input arguments that were
        # identified with the inspect module.
        idxArgs = splits.index("Args:\n")
        arg_strs = re.split(
            "(\n\s+" + "\s+\(|\n\s+".join(arg_names) + "\s+\()",
            "Args:\n" + splits[idxArgs + 1],
        )

        # Update the docs dict with the input arguments' names as keys and their corresponding doc
        # string parts as values.
        docs.update(
            {
                re.search("\w+", k).group(): k.strip() + re.sub("\n", "", v)
                for k, v in zip(arg_strs[1::2], arg_strs[2::2])
            }
        )

    return docs
