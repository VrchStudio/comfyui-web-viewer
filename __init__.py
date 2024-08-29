from .nodes.web_viewer_node import VrchWebViewerNode
from .nodes.image_nodes import *
from .nodes.audio_nodes import *
from .nodes.text_nodes import *

__version__ = "1.0.2"

NODE_CLASS_MAPPINGS = {
    "VrchAudioGenresNode": VrchAudioGenresNode,
    "VrchAudioSaverNode": VrchAudioSaverNode,
    "VrchJsonUrlLoaderNode": VrchJsonUrlLoaderNode,
    "VrchImageSaverNode": VrchImageSaverNode,
    "VrchWebViewerNode": VrchWebViewerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchAudioGenresNode": "Get Audio Genres by vrch.io",
    "VrchAudioSaverNode": "Audio Saver by vrch.io",
    "VrchJsonUrlLoaderNode": "JSON URL Loader by vrch.io",
    "VrchImageSaverNode": "Image Saver by vrch.io",
    "VrchWebViewerNode": "Web Viewer by vrch.io",
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

