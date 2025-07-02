"""Image generation actions definitions"""

from imageprocessing.parts.actions_list import ImageAction, ACTION_CLASSES
from PIL import Image


class SolidBlue(ImageAction):
    label = "Solid blue"
    summary = "Create a 300x200 solid blue image."
    nr_image_inputs = 0
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        new_image = Image.new("RGB", (300, 200), color=(0, 0, 255))
        new_image.save(target_file)


class StableDiffusion2(ImageAction):
    label = "Stable Diffusion 2"
    summary = """This is a Latent Diffusion model for Text-to-Image Generation. For the purpose of this demo, we leveraged the Stable Diffusion 2.1 model made available by StabilityAI.  

The model takes in a prompt, which is used to guide the denoising diffusion process.  

The guidance scale controls the amount of influence the prompt has on the generated image.  

The number of inference steps controls the number of steps the model takes to generate the image.
"""
    nr_image_inputs = 0
    pipeline = None
    parameters = [
        {
            "pipe_key": "prompt",
            "label": "Prompt",
            "datatype": "text",
            "defaultValue": "A Brown and white cat, high resolution",
            "tooltip": "The prompt to guide the generation of the image, i.e., what you want the model to generate",
            "required": True,
        },
        {
            "pipe_key": "negative_prompt ",
            "label": "Negative prompt",
            "datatype": "text",
            "defaultValue": "",
            "tooltip": "The negative prompt to guide the generation of the image, i.e., what you don't want the model to generate",
            "required": False,
        },
        {
            "pipe_key": "num_inference_steps",
            "label": "Number of Inference Steps",
            "datatype": "numeric",
            "defaultValue": 1,  # 10,
            "min": 1,  # 5,
            "max": 100,
            "decimalLimit": 0,
            "tooltip": "The number of steps the model takes to generate the image. Higher values result in better quality images but take longer to generate.",
            "required": True,
        },
        {
            "pipe_key": "guidance_scale",
            "label": "Guidance Scale",
            "datatype": "numeric",
            "defaultValue": 7.5,
            "min": 0.0,
            "max": 10.0,
            "decimalLimit": 2,
            "tooltip": "The amount of influence the prompt has on the generated image. Higher values result in images that more closely resemble the prompt but can be less diverse.",
            "required": True,
        },
    ]

    @staticmethod
    def perform_action(image_file: str, target_file: str, *args) -> None:
        import torch
        from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

        if StableDiffusion2.pipeline is None:
            pipe = StableDiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-3.5", torch_dtype=torch.float16
            )

            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            StableDiffusion2.pipeline = pipe
        else:
            pipe = StableDiffusionPipeline(**StableDiffusion2.pipeline.components)

        neg_prompt = args[1]
        if neg_prompt == "":
            neg_prompt = None

        new_image = pipe(
            prompt=args[0],
            negative_prompt=neg_prompt,
            num_inference_steps=args[2],
            guidance_scale=args[3],
            width=768,
            height=768,
        ).images[0]

        new_image.save(target_file)


# Extend the list of Action classes with tthe set defined in this module.
ACTION_CLASSES.extend(set(ImageAction.get_subclasses()) - set(ACTION_CLASSES))
