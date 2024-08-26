from .nodes.web_viewer_node import WebViewerNode
from .nodes.image_nodes import *
from .nodes.audio_nodes import *
from .nodes.text_nodes import *

__version__ = "1.0.2"

NODE_CLASS_MAPPINGS = {
    "AudioGenresNode": AudioGenresNode,
    "AudioSaverNode": AudioSaverNode,
    "JsonUrlLoaderNode": JsonUrlLoaderNode,
    "ImageSaverNode": ImageSaverNode,
    "WebViewerNode": WebViewerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioSaverNode": "Audio Saver by vrch.io",
    "AudioGenresNode": "Get Audio Genres by vrch.io",
    "JsonUrlLoaderNode": "JSON URL Loader by vrch.io",
    "ImageSaverNode": "Image Saver by vrch.io",
    "WebViewerNode": "Web Viewer by vrch.io",
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

