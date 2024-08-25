import os
import torch
import numpy as np
from PIL import Image
import folder_paths

class ImageSaverNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename": ("STRING", {"default": "web_viewer_image"}),
                "path": ("STRING", {"default": "web_viewer"}),
                "extension": (["jpeg", "png", "webp"], {"default": "jpeg"}),
            },
            "optional": {
                "quality_jpeg_or_webp": ("INT", {"default": 85, "min": 1, "max": 100}),
                "optimize_png": ("BOOLEAN", {"default": False}),
                "lossless_webp": ("BOOLEAN", {"default": True}),
                "enable_preview": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def __init__(self):
        self.output_dir = folder_paths.output_directory

    def save_images(self, images, filename, path, extension, quality_jpeg_or_webp=85, optimize_png=False, lossless_webp=True, enable_preview=False):
        output_path = os.path.join(self.output_dir, path)
        os.makedirs(output_path, exist_ok=True)

        results = []
        for i, image in enumerate(images):
            if isinstance(image, torch.Tensor):
                image = image.cpu().numpy()
            img = Image.fromarray(np.clip(image * 255.0, 0, 255).astype(np.uint8))
            
            file_name = f"{filename}_{i:02d}.{extension}" if len(images) > 1 else f"{filename}.{extension}"
            full_path = os.path.join(output_path, file_name)
            
            if extension == "png":
                img.save(full_path, optimize=optimize_png)
            elif extension == "webp":
                img.save(full_path, quality=quality_jpeg_or_webp, lossless=lossless_webp)
            else:  # jpeg
                img.save(full_path, quality=quality_jpeg_or_webp, optimize=True)
            
            results.append({"filename": file_name, "subfolder": path, "type": "output"})

        if enable_preview:
            return {"ui": {"images": results}}
        else:
            return {}