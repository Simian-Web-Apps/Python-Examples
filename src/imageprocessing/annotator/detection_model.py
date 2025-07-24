"""Meta Research - Detectron 2, R-CNN R50-FPN 3x.

https://github.com/facebookresearch/detectron2
"""

from pathlib import Path
import numpy as np
from PIL import Image


def run(
    image_file: str, threshold: float, use_boxes: bool
) -> tuple[list[str], list[dict], list[float]]:
    """Detectron2 model run function.


    Args:
        image_file:     Full name of the image to analyze.
        threshold:      Confidence threshold [%] to filter out less likely objects.
        use_boxes:      Use bounding boxes when True, Segmentation when False.

    Returns:
        found_labels:   Classification label of each detected object.
        found_objects:  Detected object dicts, with fields
            "type":     {"rect", "circle", "line", "path"}
            "x":        list of horizontal coordinates w.r.t. top-left
            "y":        list of vertical coordinates w.r.t. top-left
        scores:         Detection confidence [%] of each object.
    """
    from detectron2 import model_zoo
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg
    from detectron2.data import MetadataCatalog

    cfg = get_cfg()
    # https://github.com/facebookresearch/detectron2/blob/main/MODEL_ZOO.md
    cfg.merge_from_file(
        Path(model_zoo.__file__).parents[2]
        / "configs"
        / "COCO-InstanceSegmentation"
        / "mask_rcnn_R_50_FPN_3x.yaml"
    )

    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold / 100  # set threshold for this model

    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(
        "COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"
    )
    cfg.MODEL.DEVICE = "cpu"
    predictor = DefaultPredictor(cfg)

    try:
        # Run the model on the given image file.
        outputs = predictor(np.asarray(Image.open(image_file)))
    except Exception as exc:
        return f"Unable to run detection model: {exc}", [], []

    # Process the results of the model into something that can be shown in the Simian app.
    pred_class_names = MetadataCatalog.get(cfg.DATASETS.TRAIN[0])
    found_labels = [
        pred_class_names.thing_classes[x] for x in outputs["instances"].pred_classes.tolist()
    ]
    found_objects = []
    scores = outputs["instances"].scores.tolist()

    if use_boxes:
        for box in outputs["instances"].pred_boxes:
            found_objects.append(
                {
                    "type": "rect",
                    "x": box[0::2].tolist(),
                    "y": box[1::2].tolist(),
                }
            )

    else:
        import cv2

        for mask in outputs["instances"].pred_masks:
            mask = np.ascontiguousarray(mask)
            res = cv2.findContours(
                mask.astype("uint8"), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS
            )
            res = cv2.approxPolyDP(res[-2][0], 1, True).flatten()
            found_objects.append(
                {
                    "type": "path",
                    "x": res[0::2],
                    "y": res[1::2],
                }
            )

    return found_labels, found_objects, scores
