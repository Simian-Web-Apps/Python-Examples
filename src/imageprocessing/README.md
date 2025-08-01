# Image generation apps

The imageprocessing package contains four Simian web apps for modifying and generating images and supporting modules. All apps allow for downloading the created figure. When an input image is used, this can be uploaded.


## Apps

- `processor.image_processor`

  - Upload an image, select and parametrize `Pillow` image modification actions, and download the processed image.

- `inpainter.image_inpainter`
  
  - Allows for drawing a white mask on the image where the image can be modified. The drawn mask is made available to the processing action as a separate image.

- `generator.image_generator`

  - No input image is used, as the base image is generated based on action settings.
  - The name of the output file must be specified.
  
- `pytorch.image_transform`

  - Upload an image, select the combination method, select and parameterize `PyTorch` vision transforms, and download the processed image.

- `annotator.image_annotator`

  - Upload images and an optional label definitions file, draw shapes on the figures and select from the predefined labels. When all figures are annotated you can download a .csv file with the annotations. The app can be extended with an AI object `detection_model.py` module that runs an object detection algorithm on inputs given by the app and returns the result in the format expected by the app.


## Installation

- `simian.gui`                      [Installation manual](doc.simiansuite.com/simian-gui/setup/python.html)
- `simian.local`                    When running locally.
- requirements.txt                  Dependencies for all apps
- requirements-imagegen.txt         Dependencies for the image generator app.
- pytorch/requirements.txt          PyTorch Transform dependencies.
- annotator/requirements.txt        Optional AI image detection dependencies, incl. [Detectron2](https://github.com/facebookresearch/detectron2).


## Actions

- `parts.actions_list.py`

  - Defines as list of Python Pillow modifications
  - Available in all apps as (post)processing actions.

- `inpainter.inpaint_actions.py`

  - Defines a list of actions where an area of an image is selected for processing.

- `generator.image_gen_actions.py`

  - Defines as list of actions where an image is generated based on the given settings.

## Adding an action

- Create a subclass of the `imageprocessing.parts.actions_list.ImageAction` class.
- Set the `label` attribute that is shown in the actions dropdown list.
- (Optionally) set the `summary` attribute.
- Set the `nr_image_inputs` attribute to:
  - 0 for image generation
  - 1 for modifying an image. The default.
  - 2 for inpainting an image in a masked region.
- Fill the `parameter` attribute with a list of dicts:
  - The keys of the dict must match the `simian.gui.composed_component.PropertyEditor` row properties.
  - extra keys are ignored.
- Implement the `perform_action` method with inputs:
  - `image_file`:  is the full input image name in the session folder.
  - `target_file`: name of the image file that must be saved to in the action. In the `image_inpainter` app the `target_file` contains the drawn mask image.
  - `*args`: A list of values selected in the Parameter list.

### Parameters

The modify action's parameters' definitions may contain the following keys:

| Key          | Example             | Extra                                              |
|--------------|---------------------|----------------------------------------------------|
| datatype     | "numeric"           | Mandatory                                          |
| label        | "Property name"     | Mandatory                                          |
| tooltip      | "Tooltip text"      |                                                    |
| required     | False               |                                                    |
| defaultValue | "Default value"     | Defaults to a minLength long list of Nones.        |
| min          | 0                   | Numeric                                            |
| max          | 2                   | Numeric                                            |
| decimalLimit | 2                   | Numeric                                            |
| allowed      | ["A", "B", "C"]     | Select component data source values definition.    |
| minLength    | 1                   | {1} Scalar, or minimum array length of 0 or more.  |
| maxLength    | 1                   | {1} Scalar, or maximum array length of 0 or more.  |

The supported data types are: "boolean", "numeric", "select", and "text".

The following example defines a numeric parameter, allowing a two decimal value between zero and one to be selected.

```python
{
    "label": "Strength",
    "datatype": "numeric",
    "defaultValue": 0.9,
    "min": 0,
    "max": 1,
    "numberOfDecimals": 2,
    "tooltip": "The extent to transform the reference image.",
    "required": True,
},
```
