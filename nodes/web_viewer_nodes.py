import os
import torch
import hashlib
import numpy as np
from PIL import Image
import folder_paths
from .image_nodes import VrchImageSaverNode

CATEGORY = "vrch.ai/viewer"

class VrchWebViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (["image", "flipbook", "audio", "depthmap"], {"default": "image"}),
                "server": ("STRING", {"default": "127.0.0.1:8188", "multiline": False, "dynamicPrompts": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "filename": ("STRING", {"default": "web_viewer_image.jpeg", "multiline": False, "dynamicPrompts": False}),
                "path": ("STRING", {"default": "web_viewer", "multiline": False, "dynamicPrompts": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url":("BOOLEAN", {"default": False}),
                "url": ("STRING", {
                    "default": "https://vrch.ai/viewer",
                    "multiline": True,
                    "dynamicPrompts": False
                }),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "dummy_function"
    CATEGORY = CATEGORY
    
    OUTPUT_NODE = True

    DESCRIPTION = "Opens the specified Web Viewer URL in a new browser tab when button is clicked."

    def dummy_function(self, **kwargs):
        return ()

    @classmethod
    def IS_CHANGED(s, **kwargs):
        return False

class VrchImageWebViewerNode(VrchImageSaverNode):

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": "127.0.0.1:8188", "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_and_view_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # The output directory where images will be saved
        self.output_dir = folder_paths.output_directory

    def save_and_view_images(self, images, channel, server, ssl, window_width, window_height, show_url, url):
        # Save the image into "web_viewer" directory with filename "{channel}.jpeg"
        output_path = os.path.join(self.output_dir, "web_viewer")
        os.makedirs(output_path, exist_ok=True)

        filename = f"channel_{channel}"
        self.save_images(
            images=images,
            filename=filename,
            path="web_viewer",
            extension="jpeg",
            quality_jpeg_or_webp=85
        )

        # No need to return anything; UI handling is done via JavaScript
        return ()

    @classmethod
    def IS_CHANGED(cls, images, **kwargs):
        m = hashlib.sha256()
        for image in images:
            # Convert image to bytes and update the hash
            if isinstance(image, torch.Tensor):
                image_bytes = image.cpu().numpy().tobytes()
            elif isinstance(image, np.ndarray):
                image_bytes = image.tobytes()
            else:
                # Handle other types if necessary
                image_bytes = bytes()
            m.update(image_bytes)
        return m.hexdigest()
