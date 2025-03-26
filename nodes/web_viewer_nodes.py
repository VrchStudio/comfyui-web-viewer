import os
import json
import shutil
import torch
import hashlib
import numpy as np
from PIL import Image
import folder_paths
from .image_nodes import VrchImageSaverNode
from .audio_nodes import VrchAudioSaverNode
from .node_utils import VrchNodeUtils

# Define the category for organizational purposes
CATEGORY = "vrch.ai/viewer"
# The default server address
DEFAULT_SERVER = "127.0.0.1:8188"

class VrchWebViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (["image", "flipbook", "audio", "depthmap", "3dmodel"], {"default": "image"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False, "dynamicPrompts": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "filename": ("STRING", {"default": "web_viewer_image.jpeg", "multiline": False, "dynamicPrompts": False}),
                "path": ("STRING", {"default": "web_viewer", "multiline": False, "dynamicPrompts": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url":("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
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
    
class VrchImageChannelLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "load_image"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # Get the output directory (assuming folder_paths.output_directory is defined)
        self.output_dir = folder_paths.output_directory

    def load_image(self, channel):
        # Construct the full path of the target file with .jpg extension
        file_path = os.path.join(self.output_dir, "web_viewer", f"channel_{channel}.jpeg")
        
        if os.path.exists(file_path):
            try:
                # Attempt to open and read the image
                image = Image.open(file_path)
                image = image.convert("RGB")
                image_np = np.array(image).astype(np.float32) / 255.0
            except Exception as e:
                # If any error occurs during loading, return a black placeholder image
                image_np = np.zeros((512, 512, 3), dtype=np.uint8)
        else:
            # If the specified file does not exist, return a black placeholder image
            image_np = np.zeros((512, 512, 3), dtype=np.uint8)
            
        image = torch.from_numpy(image_np)[None,]
        return (image,)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always changed by default
        return float("NaN")

class VrchImageWebViewerNode(VrchImageSaverNode):

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGES",)
    FUNCTION = "save_and_view_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # The output directory where images will be saved
        self.output_dir = folder_paths.output_directory

    def save_and_view_images(self, images, channel, server, ssl, window_width, window_height, extra_params, show_url, url):
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

        return (images,)

    @classmethod
    def IS_CHANGED(cls, images, **kwargs):
        m = hashlib.sha256()
        
        if not isinstance(images, list):
            return False
        
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

class VrchImageFlipBookWebViewerNode(VrchImageSaverNode):

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "number_of_images": ("INT", {"default": 4, "min": 1, "max": 99}),
                "refresh_interval": ("INT", {"default": 5000, "min": 1, "max": 10000}),
                "image_display_duration":("INT", {"default": 1000, "min": 1, "max": 10000}),
                "fade_anim_duration": ("INT", {"default": 200, "min": 1, "max": 10000}),
                "server_messages": ("STRING", {"default": "", "multiline": False}),
                "save_settings": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGES",)
    FUNCTION = "save_and_view_images"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # The output directory where images will be saved
        self.output_dir = folder_paths.output_directory

    def save_and_view_images(self, 
                             images, 
                             channel,
                             server, 
                             ssl, 
                             number_of_images,
                             refresh_interval,
                             image_display_duration,
                             fade_anim_duration,
                             server_messages,
                             save_settings,
                             window_width, 
                             window_height, 
                             show_url,
                             extra_params, 
                             url):
        # Save the images into "web_viewer" directory with filename "channel_{channel}_{index:%02d}.jpeg"
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
        
        if save_settings:
            # Save the settings to a JSON file
            settings = {
                "numberOfImages": number_of_images,
                "refreshInterval": refresh_interval,
                "imageDisplayDuration": image_display_duration,
                "fadeAnimDuration": fade_anim_duration,
                "serverMessages": server_messages,
            }
            settings_filename = f"channel_{channel}_settings.json"
            settings_path = os.path.join(output_path, settings_filename)
            with open(settings_path, "w") as f:
                json.dump(settings, f)
        
        return (images,)

    @classmethod
    def IS_CHANGED(cls, images, **kwargs):
        m = hashlib.sha256()
        
        if not isinstance(images, list):
            return False
        
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
    
class VrchAudioWebViewerNode(VrchAudioSaverNode):
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    FUNCTION = "save_and_view_audio"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # The output directory where audio will be saved
        self.output_dir = folder_paths.output_directory

    def save_and_view_audio(self, audio, channel, server, ssl, window_width, window_height, extra_params, show_url, url):
        # Save the audio into "web_viewer" directory with filename "{channel}.mp3"
        output_path = os.path.join(self.output_dir, "web_viewer")
        os.makedirs(output_path, exist_ok=True)

        filename = f"channel_{channel}"
        self.save_audio(
            audio=audio,
            filename=filename,
            path="web_viewer",
            extension="mp3"
        )

        return (audio,)

    @classmethod
    def IS_CHANGED(cls, audio, **kwargs):
        m = hashlib.sha256()
        # Convert image to bytes and update the hash
        if isinstance(audio, torch.Tensor):
            audio_bytes = audio.cpu().numpy().tobytes()
        elif isinstance(audio, np.ndarray):
            audio_bytes = audio.tobytes()
        else:
            # Handle other types if necessary
            audio_bytes = bytes()
        m.update(audio_bytes)
        return m.hexdigest()
    
class VrchModelWebViewerNode():

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_file": ("STRING", {"forceInput": True}),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("MODEL_FILE",)
    FUNCTION = "save_and_view_3d_model"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # The output directory where audio will be saved
        self.output_dir = folder_paths.output_directory

    def save_and_view_3d_model(self, model_file, channel, server, ssl, window_width, window_height, extra_params, show_url, url):
        # Save the 3d model into "web_viewer" directory with filename "channel_{channel}.glb"
        output_path = self.output_dir
        web_viewer_folder = "web_viewer"
        os.makedirs(os.path.join(output_path, web_viewer_folder), exist_ok=True)
        
        # Construct the source file path (assumed to be in output_path directory)
        src_file = os.path.join(output_path, model_file)
        if not os.path.isfile(src_file):
            raise FileNotFoundError(f"File '{src_file}' not found.")
        
        # Check if the file extension is .glb
        _, ext = os.path.splitext(src_file)
        if ext.lower() != ".glb":
            raise ValueError(f"Unsupported file extension '{ext}'. Expected '.glb'.")
        
        # Define the new file name and destination path
        new_filename = f"channel_{channel}.glb"
        dst_file = os.path.join(output_path, web_viewer_folder, new_filename)
        
        # Overwrite the destination file if it exists
        if os.path.exists(dst_file):
            os.remove(dst_file)
        
        # Move the file to the new destination
        shutil.move(src_file, dst_file)
        
        # Return the new path relative to the output directory
        return (os.path.join(web_viewer_folder, new_filename),)

    @classmethod
    def IS_CHANGED(cls, model_file, **kwargs):
        m = hashlib.sha256()
        output_path = folder_paths.output_directory
        file_path = os.path.join(output_path, model_file)
        
        if not os.path.isfile(file_path):
            return False
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                m.update(chunk)
        return m.hexdigest()
    
class VrchVideoWebViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename": ("STRING", {"forceInput": True}),
                "channel": (["1", "2", "3", "4", "5", "6", "7", "8"], {"default": "1"}),
                "server": ("STRING", {"default": DEFAULT_SERVER, "multiline": False}),
                "ssl": ("BOOLEAN", {"default": False}),
                "window_width": ("INT", {"default": 1280, "min": 100, "max": 10240}),
                "window_height": ("INT", {"default": 960, "min": 100, "max": 10240}),
                "show_url": ("BOOLEAN", {"default": False}),
                "extra_params":("STRING", {"multiline": True, "dynamicPrompts": False}),
                "url": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_and_view_video"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        self.output_dir = folder_paths.output_directory
        self.allowed_extensions = ["mp4"]

    def validate(self, filename):
        if not filename or not os.path.isfile(filename):
            raise FileNotFoundError(f"File '{filename}' not found.")

        ext = os.path.splitext(filename)[1].lower()
        if ext.lstrip('.') not in self.allowed_extensions:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed extensions: {self.allowed_extensions}")

    def save_and_view_video(self, channel, server, ssl, window_width, window_height, extra_params, show_url, url, filename=None):
        self.validate(filename)
        output_path = os.path.join(self.output_dir, "web_viewer")
        os.makedirs(output_path, exist_ok=True)
        dst_file = os.path.join(output_path, f"channel_{channel}.mp4")
        shutil.copyfile(filename, dst_file)
        return ()

    @classmethod
    def IS_CHANGED(cls, channel, server, ssl, window_width, window_height, extra_params, show_url, url, filename=None):
        if not filename or not os.path.isfile(filename):
            return False
        m = hashlib.sha256()
        with open(filename, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()
    