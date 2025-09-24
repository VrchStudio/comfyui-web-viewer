import io, base64
import os
import re
import torch
import numpy as np
from PIL import Image
import folder_paths

CATEGORY = "vrch.ai/image"

class VrchImageSaverNode:
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
    CATEGORY = CATEGORY

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
        

class VrchImagePreviewBackgroundNode(VrchImageSaverNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "background_display": ("BOOLEAN", {"default": True}),
                "refresh_interval_ms": ("INT", {"default": 300, "min": 50, "max": 10000}),
                "display_option": (["original", "fit", "stretch", "crop"], {"default": "fit"}),
                "batch_display": ("BOOLEAN", {"default": False}),
                "batch_display_interval_ms": ("INT", {"default": 200, "min": 50, "max": 10000}),
                "batch_images_size": ("INT", {"default": 4, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "save_image_to_td_background"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        super().__init__()
        # By default, images are saved into ComfyUI's output directory
        self.output_dir = folder_paths.output_directory

    def save_image_to_td_background(self, 
                                    images, 
                                    channel,
                                    background_display, 
                                    refresh_interval_ms,
                                    display_option,
                                    batch_display,
                                    batch_display_interval_ms,
                                    batch_images_size):
        
        # Save the images into "preview_background" directory with filename "{channel}_{index:%02d}.jpeg"
        filename = f"channel_{channel}"
        path = f"preview_background"

        output_path = os.path.join(self.output_dir, path)
        os.makedirs(output_path, exist_ok=True)
        
        self.save_images(
            images=images,
            filename=filename,
            path=path,
            extension="jpeg",
            quality_jpeg_or_webp=85,
        )

        return ()

class VrchImagePreviewBackgroundNewNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "background_display": ("BOOLEAN", {"default": True}),
                "display_option": (["original", "fit", "stretch", "crop"], {"default": "fit"}),
                "batch_display": ("BOOLEAN", {"default": False}),
                "batch_display_interval_ms": ("INT", {"default": 200, "min": 50, "max": 10000})
            },
        }
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "preview_images_to_ui"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def preview_images_to_ui(self, 
                             images, 
                             background_display=True, 
                             batch_display=False, 
                             batch_display_interval_ms=200, 
                             display_option="fit"):
        
        ui_images = []
        for i, image in enumerate(images):
            if isinstance(image, torch.Tensor):
                image = image.cpu().numpy()
            img = Image.fromarray(np.clip(image * 255.0, 0, 255).astype(np.uint8))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            jpg_bytes = buffer.getvalue()

            # Base64-encode and prepend data-URI header
            b64 = base64.b64encode(jpg_bytes).decode('utf-8')
            ui_images.append(f"data:image/jpeg;base64,{b64}")
        
        # If batch_display is False, only show the first image
        if not batch_display:
            ui_images = [ui_images[0]] if ui_images else []
            
        # Send images, display option and enable flag to UI
        return {
            "ui": {
                "background_images": ui_images,
                "display_option": [display_option],
                "background_display": [background_display],
            }
        }


class VrchImageFallbackNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fallback_option": (["default_image", "placeholder_image", "last_valid_image"], {"default": "placeholder_image"}),
                "placeholder_width": ("INT", {"default": 512, "min": 1, "max": 4096}),
                "placeholder_height": ("INT", {"default": 512, "min": 1, "max": 4096}),
                "placeholder_color": ("STRING", {"default": "#000000"}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
                "default_image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "resolve_image"
    CATEGORY = CATEGORY

    def __init__(self):
        self.last_valid_image = None

    def resolve_image(self, fallback_option, placeholder_width, placeholder_height,
                      placeholder_color, debug=False, image=None, default_image=None):
        resolved_image = self._normalize_image(image)
        if self._is_valid_image(resolved_image):
            self.last_valid_image = resolved_image
            if debug:
                print("[VrchImageFallbackNode] Using provided image")
            return (resolved_image,)

        if debug:
            print("[VrchImageFallbackNode] Input image invalid, applying fallback")

        default_image = self._normalize_image(default_image)

        if fallback_option == "default_image" and not self._is_valid_image(default_image):
            if debug:
                print("[VrchImageFallbackNode] default_image unavailable, switching to placeholder_image")
            fallback_option = "placeholder_image"

        if fallback_option == "last_valid_image" and not self._is_valid_image(self.last_valid_image):
            if debug:
                print("[VrchImageFallbackNode] last_valid_image unavailable, switching to placeholder_image")
            fallback_option = "placeholder_image"

        candidates = self._build_candidate_sequence(
            fallback_option,
            default_image,
        )

        for candidate_name in candidates:
            if candidate_name == "default_image":
                if self._is_valid_image(default_image):
                    if debug:
                        print("[VrchImageFallbackNode] Using default_image fallback")
                    return (default_image,)
            elif candidate_name == "last_valid_image" and self._is_valid_image(self.last_valid_image):
                if debug:
                    print("[VrchImageFallbackNode] Using last_valid_image fallback")
                return (self.last_valid_image,)
            elif candidate_name == "placeholder_image":
                placeholder = self._build_placeholder_tensor(
                    placeholder_width,
                    placeholder_height,
                    placeholder_color,
                    debug,
                )
                if debug:
                    print("[VrchImageFallbackNode] Using placeholder_image fallback")
                return (placeholder,)

        placeholder = self._build_placeholder_tensor(
            placeholder_width,
            placeholder_height,
            placeholder_color,
            debug,
        )
        if debug:
            print("[VrchImageFallbackNode] No fallback successful, using generated placeholder")
        return (placeholder,)

    def _build_candidate_sequence(self, primary_option, default_image):
        order = ["placeholder_image", "default_image", "last_valid_image"]
        if primary_option not in order:
            primary_option = "placeholder_image"

        if primary_option == "default_image" and default_image is None:
            # No default supplied, deprioritize it.
            order.remove("default_image")
            order.append("default_image")

        reordered = [primary_option] + [name for name in order if name != primary_option]
        return reordered

    def _normalize_image(self, image):
        if image is None:
            return None

        if isinstance(image, torch.Tensor):
            tensor = image
        elif isinstance(image, np.ndarray):
            tensor = torch.from_numpy(image)
        else:
            return None

        if tensor.ndim == 3:
            tensor = tensor.unsqueeze(0)
        if tensor.ndim != 4 or tensor.shape[-1] not in (1, 3, 4):
            return None

        tensor = tensor.detach().to(torch.float32)
        if torch.isnan(tensor).any() or torch.isinf(tensor).any():
            return None
        return tensor.contiguous().clone()

    def _is_valid_image(self, image):
        return image is not None and isinstance(image, torch.Tensor) and image.ndim == 4 and image.numel() > 0

    def _build_placeholder_tensor(self, width, height, color_str, debug):
        width = max(1, int(width))
        height = max(1, int(height))
        rgb = self._parse_color_string(color_str)
        placeholder = torch.tensor(rgb, dtype=torch.float32).view(1, 1, 1, 3)
        placeholder = placeholder.expand(1, height, width, 3).contiguous()
        if debug:
            print(f"[VrchImageFallbackNode] Placeholder params width={width} height={height} color={rgb}")
        return placeholder

    def _parse_color_string(self, color_str):
        if not isinstance(color_str, str):
            return [0.0, 0.0, 0.0]

        color_str = color_str.strip()
        if color_str.startswith("#"):
            color_str = color_str[1:]

        if re.fullmatch(r"[0-9a-fA-F]{3}", color_str):
            r, g, b = (int(c * 2, 16) for c in color_str)
            return [r / 255.0, g / 255.0, b / 255.0]

        if re.fullmatch(r"[0-9a-fA-F]{6}", color_str):
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return [r / 255.0, g / 255.0, b / 255.0]

        if re.fullmatch(r"[0-9a-fA-F]{8}", color_str):
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            # Alpha ignored; assumes opaque placeholder.
            return [r / 255.0, g / 255.0, b / 255.0]

        return [0.0, 0.0, 0.0]
