from .nodes.web_viewer_node import WebViewerNode
from .nodes.image_saver_node import ImageSaverNode
from .nodes.audio_genres_node import AudioGenresNode

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