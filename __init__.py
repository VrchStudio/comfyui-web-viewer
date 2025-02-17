from .nodes.web_viewer_nodes import *
from .nodes.image_nodes import *
from .nodes.audio_nodes import *
from .nodes.text_nodes import *
from .nodes.key_control_nodes import *
from .nodes.osc_control_nodes import *

__version__ = "1.0.20"

NODE_CLASS_MAPPINGS = {
    "VrchAnyOSCControlNode": VrchAnyOSCControlNode,
    "VrchAudioGenresNode": VrchAudioGenresNode,
    "VrchAudioRecorderNode": VrchAudioRecorderNode,
    "VrchAudioSaverNode": VrchAudioSaverNode,
    "VrchAudioWebViewerNode": VrchAudioWebViewerNode,
    "VrchBooleanKeyControlNode": VrchBooleanKeyControlNode,
    "VrchChannelOSCControlNode": VrchChannelOSCControlNode,
    "VrchChannelX4OSCControlNode": VrchChannelX4OSCControlNode,
    "VrchDelayOSCControlNode": VrchDelayOscControlNode,
    "VrchFloatKeyControlNode": VrchFloatKeyControlNode,
    "VrchFloatOSCControlNode": VrchFloatOSCControlNode,
    "VrchJsonUrlLoaderNode": VrchJsonUrlLoaderNode,
    "VrchImageChannelLoaderNode": VrchImageChannelLoaderNode,
    "VrchImageFlipBookWebViewerNode": VrchImageFlipBookWebViewerNode,
    "VrchImageSaverNode": VrchImageSaverNode,
    "VrchImageSwitchOSCControlNode": VrchImageSwitchOSCControlNode,
    "VrchImagePreviewBackgroundNode": VrchImagePreviewBackgroundNode,
    "VrchImageWebViewerNode": VrchImageWebViewerNode,
    "VrchIntKeyControlNode": VrchIntKeyControlNode,
    "VrchIntOSCControlNode": VrchIntOSCControlNode,
    "VrchInstantQueueKeyControlNode": VrchInstantQueueKeyControlNode,
    "VrchModelWebViewerNode": VrchModelWebViewerNode,
    "VrchOSCControlSettingsNode": VrchOSCControlSettingsNode,
    "VrchSwitchOSCControlNode": VrchSwitchOSCControlNode,
    "VrchTextConcatOSCControlNode": VrchTextConcatOSCControlNode,
    "VrchTextKeyControlNode": VrchTextKeyControlNode,
    "VrchTextSwitchOSCControlNode": VrchTextSwitchOSCControlNode,
    "VrchVideoWebViewerNode": VrchVideoWebViewerNode,
    "VrchWebViewerNode": VrchWebViewerNode,
    "VrchXYOSCControlNode": VrchXYOSCControlNode,
    "VrchXYZOSCControlNode": VrchXYZOSCControlNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchAnyOSCControlNode": "ANY Value OSC Control @ vrch.ai",
    "VrchAudioGenresNode": "Get Audio Genres @ vrch.ai",
    "VrchAudioRecorderNode": "Audio Recorder @ vrch.ai",
    "VrchAudioSaverNode": "Audio Saver @ vrch.ai",
    "VrchAudioWebViewerNode": "AUDIO Web Viewer @ vrch.ai",
    "VrchBooleanKeyControlNode": "BOOLEAN Key Control @ vrch.ai",
    "VrchChannelOSCControlNode": "CHANNEL OSC Control @ vrch.ai",
    "VrchChannelX4OSCControlNode": "CHANNEL x4 OSC Control @ vrch.ai",
    "VrchDelayOscControlNode": "Delay OSC Control @ vrch.ai",
    "VrchFloatKeyControlNode": "FLOAT Key Control @ vrch.ai",
    "VrchFloatOSCControlNode": "FLOAT OSC Control @ vrch.ai",
    "VrchJsonUrlLoaderNode": "JSON URL Loader @ vrch.ai",
    "VrchImageFlipBookWebViewerNode": "IMAGE Flipbook Web Viewer @vrch.ai",
    "VrchImageSaverNode": "IMAGE Saver @ vrch.ai",
    "VrchImageSwitchOSCControlNode": "IMAGE Switch OSC Control @ vrch.ai",
    "VrchImagePreviewBackgroundNode": "IMAGE Preview in Background @ vrch.ai",
    "VrchImageWebViewerNode": "IMAGE Web Viewer @ vrch.ai",
    "VrchImageChannelLoaderNode": "IMAGE Web Viewer Channel Loader @ vrch.ai",
    "VrchIntKeyControlNode": "INT Key Control @ vrch.ai",
    "VrchIntOSCControlNode": "INT OSC Control @ vrch.ai",
    "VrchInstantQueueKeyControlNode": "Instant Queue Key Control @ vrch.ai",
    "VrchModelWebViewerNode": "3D MODEL Web Viewer @ vrch.ai",
    "VrchOSCControlSettingsNode": "OSC Control Settings @ vrch.ai",
    "VrchSwitchOSCControlNode": "SWITCH OSC Control @ vrch.ai",
    "VrchTextConcatOSCControlNode": "TEXT Concat OSC Control @ vrch.ai",
    "VrchTextKeyControlNode": "TEXT Key Control @ vrch.ai",
    "VrchTextSwitchOSCControlNode": "TEXT Switch OSC Control @ vrch.ai",
    "VrchVideoWebViewerNode": "VIDEO Web Viewer @ vrch.ai",
    "VrchWebViewerNode": "Web Viewer @ vrch.ai",
    "VrchXYOSCControlNode": "XY OSC Control @ vrch.ai",
    "VrchXYZOSCControlNode": "XYZ OSC Control @ vrch.ai",
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

