from .nodes.web_viewer_node import VrchWebViewerNode
from .nodes.image_nodes import *
from .nodes.audio_nodes import *
from .nodes.text_nodes import *
from .nodes.key_control_nodes import *
from .nodes.osc_control_nodes import *

__version__ = "1.0.9"

NODE_CLASS_MAPPINGS = {
    "VrchAudioGenresNode": VrchAudioGenresNode,
    "VrchAudioRecorderNode": VrchAudioRecorderNode,
    "VrchAudioSaverNode": VrchAudioSaverNode,
    "VrchBooleanKeyControlNode": VrchBooleanKeyControlNode,
    "VrchFloatKeyControlNode": VrchFloatKeyControlNode,
    "VrchJsonUrlLoaderNode": VrchJsonUrlLoaderNode,
    "VrchImageSaverNode": VrchImageSaverNode,
    "VrchIntKeyControlNode": VrchIntKeyControlNode,
    "VrchTextKeyControlNode": VrchTextKeyControlNode,
    "VrchWebViewerNode": VrchWebViewerNode,
    "VrchXYOSCControlNode": VrchXYOSCControlNode,
    "VrchXYZOSCControlNode": VrchXYZOSCControlNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchAudioGenresNode": "Get Audio Genres by vrch.io",
    "VrchAudioRecorderNode": "Audio Recorder by vrch.io",
    "VrchAudioSaverNode": "Audio Saver by vrch.io",
    "VrchBooleanKeyControlNode": "BOOLEAN Key Control by vrch.io",
    "VrchFloatKeyControlNode": "FLOAT Key Control by vrch.io",
    "VrchJsonUrlLoaderNode": "JSON URL Loader by vrch.io",
    "VrchImageSaverNode": "Image Saver by vrch.io",
    "VrchIntKeyControlNode": "INT Key Control by vrch.io",
    "VrchTextKeyControlNode": "TEXT Key Control by vrch.io",
    "VrchWebViewerNode": "Web Viewer by vrch.io",
    "VrchXYOSCControlNode": "XY OSC Control by vrch.io",
    "VrchXYZOSCControlNode": "XYZ OSC Control by vrch.io",
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

