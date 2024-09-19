"""Inpainting actions definitions."""

from typing import Union

from imageprocessing.actions_list import ImageAction
from PIL import Image


class ShowInpaintMask(ImageAction):
    label = "Show inpaint mask"
    summary = "Utility for viewing the mask that is created from the web app inputs."
    nr_image_inputs = 2
    parameters = []

    @staticmethod
    def perform_action(image_file: str, target_file: str) -> None:
        return None


class StableDiffusion2Inpaint(ImageAction):
    label = "Stable Diffusion 2 Inpaint"
    summary = """This is a Latent Diffusion model for Text-to-Image Inpainting. For the purpose of this demo, we leveraged the Stable Diffusion 2 Inpainting model made available by StabilityAI.  

The model takes in a prompt and a mask, which are both used to guide the denoising diffusion process.  

The guidance scale controls the amount of influence the prompt has on the generated image and the strength indicates the extent to transform the reference image.  

The number of inference steps controls the number of steps the model takes to generate the image.
"""
    nr_image_inputs = 2
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
            "pipe_key": "strength",
            "label": "Strength",
            "datatype": "numeric",
            "defaultValue": 0.9,
            "min": 0,
            "max": 1,
            "numberOfDecimals": 2,
            "tooltip": "The extent to transform the reference image. When strength is 1, added noise is maximum and the denoising process runs for the full number of iterations specified in num_inference_steps",
            "required": True,
        },
        {
            "pipe_key": "num_inference_steps",
            "label": "Number of Inference Steps",
            "datatype": "numeric",
            "defaultValue": 1,  # 10,
            "min": 1,  # 5,
            "max": 100,
            "numberOfDecimals": 0,
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
            "numberOfDecimals": 2,
            "tooltip": "The amount of influence the prompt has on the generated image. Higher values result in images that more closely resemble the prompt but can be less diverse.",
            "required": True,
        },
    ]

    @staticmethod
    def perform_action(
        image_file: str,
        target_file: str,
        prompt: str,
        neg_prompt: Union[None, str],
        strength: float,
        nr_steps: int,
        scale: float,
    ) -> None:
        import torch
        from diffusers import (
            DPMSolverMultistepScheduler,
            StableDiffusionInpaintPipeline,
        )

        if StableDiffusion2Inpaint.pipeline is None:
            pipe = StableDiffusionInpaintPipeline.from_single_file(
                r"C:\Files\TASTI\Models\512-inpainting-ema.ckpt",
                torch_dtype=torch.float32,
            )

            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            StableDiffusion2Inpaint.pipeline = pipe
        else:
            pipe = StableDiffusionInpaintPipeline(**StableDiffusion2Inpaint.pipeline.components)

        if neg_prompt == "":
            neg_prompt = None

        # Get the original image size to ensure the created figure is not stretched/shrunk.
        image_obj = Image.open(image_file)
        width, height = image_obj.size

        new_image = pipe(
            prompt=prompt,
            negative_prompt=neg_prompt,
            strength=strength,
            num_inference_steps=nr_steps,
            mask_image=Image.open(target_file),
            image=image_obj,
            guidance_scale=scale,
            width=width,
            height=height,
        ).images[0]

        new_image.save(target_file)
