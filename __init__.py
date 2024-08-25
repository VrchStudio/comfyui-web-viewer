from .nodes.web_viewer_node import WebViewerNode
from .nodes.image_saver_node import ImageSaverNode
from .nodes.audio_genres_node import AudioGenresNode

__version__ = "1.0.0"

NODE_CLASS_MAPPINGS = {
    "WebViewerNode": WebViewerNode,
    "ImageSaverNode": ImageSaverNode,
    "AudioGenresNode": AudioGenresNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WebViewerNode": "Web Viewer by vrch.io",
    "ImageSaverNode": "Image Saver by vrch.io",
    "AudioGenresNode": "Get Audio Genres by vrch.io"
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

