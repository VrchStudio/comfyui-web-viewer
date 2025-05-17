from .nodes.web_viewer_nodes import *
from .nodes.image_nodes import *
from .nodes.audio_nodes import *
from .nodes.text_nodes import *
from .nodes.key_control_nodes import *
from .nodes.osc_control_nodes import *
from .nodes.websocket_nodes import *
from .nodes.gamepad_nodes import *
from .nodes.logic_nodes import *
from .nodes.midi_nodes import *

__version__ = "1.0.32"

NODE_CLASS_MAPPINGS = {
    "VrchAnyOSCControlNode": VrchAnyOSCControlNode,
    "VrchAudioChannelLoaderNode": VrchAudioChannelLoaderNode,
    "VrchAudioGenresNode": VrchAudioGenresNode,
    "VrchAudioRecorderNode": VrchAudioRecorderNode,
    "VrchAudioSaverNode": VrchAudioSaverNode,
    "VrchAudioWebViewerNode": VrchAudioWebViewerNode,
    "VrchMicLoaderNode": VrchMicLoaderNode,
    "VrchBooleanKeyControlNode": VrchBooleanKeyControlNode,
    "VrchChannelOSCControlNode": VrchChannelOSCControlNode,
    "VrchChannelX4OSCControlNode": VrchChannelX4OSCControlNode,
    "VrchDelayOSCControlNode": VrchDelayOscControlNode,
    "VrchFloatKeyControlNode": VrchFloatKeyControlNode,
    "VrchFloatOSCControlNode": VrchFloatOSCControlNode,
    "VrchFloatRemapNode": VrchFloatRemapNode,
    "VrchGamepadLoaderNode": VrchGamepadLoaderNode,
    "VrchImageChannelLoaderNode": VrchImageChannelLoaderNode,
    "VrchImageFlipBookWebViewerNode": VrchImageFlipBookWebViewerNode,
    "VrchImagePreviewBackgroundNode": VrchImagePreviewBackgroundNode,
    "VrchImagePreviewBackgroundNewNode": VrchImagePreviewBackgroundNewNode,
    "VrchImageSaverNode": VrchImageSaverNode,
    "VrchImageSwitchOSCControlNode": VrchImageSwitchOSCControlNode,
    "VrchImageWebSocketChannelLoaderNode": VrchImageWebSocketChannelLoaderNode,
    "VrchImageWebSocketWebViewerNode": VrchImageWebSocketWebViewerNode,
    "VrchImageWebViewerNode": VrchImageWebViewerNode,
    "VrchInstantQueueKeyControlNode": VrchInstantQueueKeyControlNode,
    "VrchIntKeyControlNode": VrchIntKeyControlNode,
    "VrchIntOSCControlNode": VrchIntOSCControlNode,
    "VrchIntRemapNode": VrchIntRemapNode,
    "VrchJsonUrlLoaderNode": VrchJsonUrlLoaderNode,
    "VrchJsonWebSocketChannelLoaderNode": VrchJsonWebSocketChannelLoaderNode,
    "VrchJsonWebSocketSenderNode": VrchJsonWebSocketSenderNode,
    "VrchMidiDeviceLoaderNode": VrchMidiDeviceLoaderNode,
    "VrchModelWebViewerNode": VrchModelWebViewerNode,
    "VrchOSCControlSettingsNode": VrchOSCControlSettingsNode,
    "VrchSwitchOSCControlNode": VrchSwitchOSCControlNode,
    "VrchTextConcatOSCControlNode": VrchTextConcatOSCControlNode,
    "VrchTextKeyControlNode": VrchTextKeyControlNode,
    "VrchTextSrtPlayerNode": VrchTextSrtPlayerNode,
    "VrchTextSwitchOSCControlNode": VrchTextSwitchOSCControlNode,
    "VrchTriggerToggleNode": VrchTriggerToggleNode,
    "VrchTriggerToggleX4Node": VrchTriggerToggleX4Node,
    "VrchTriggerToggleX8Node": VrchTriggerToggleX8Node,
    "VrchVideoWebViewerNode": VrchVideoWebViewerNode,
    "VrchWebSocketServerNode": VrchWebSocketServerNode,
    "VrchWebViewerNode": VrchWebViewerNode,
    "VrchXboxControllerNode": VrchXboxControllerNode,
    "VrchXYOSCControlNode": VrchXYOSCControlNode,
    "VrchXYZOSCControlNode": VrchXYZOSCControlNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VrchAnyOSCControlNode": "ANY Value OSC Control @ vrch.ai",
    "VrchAudioChannelLoaderNode": "AUDIO Web Viewer Channel Loader @ vrch.ai",
    "VrchAudioGenresNode": "AUDIO Get Genres @ vrch.ai",
    "VrchAudioRecorderNode": "AUDIO Recorder @ vrch.ai",
    "VrchAudioSaverNode": "AUDIO Saver @ vrch.ai",
    "VrchAudioWebViewerNode": "AUDIO Web Viewer @ vrch.ai",
    "VrchMicLoaderNode": "Microphone Loader @ vrch.ai",
    "VrchBooleanKeyControlNode": "BOOLEAN Key Control @ vrch.ai",
    "VrchChannelOSCControlNode": "CHANNEL OSC Control @ vrch.ai",
    "VrchChannelX4OSCControlNode": "CHANNEL x4 OSC Control @ vrch.ai",
    "VrchDelayOscControlNode": "Delay OSC Control @ vrch.ai",
    "VrchFloatKeyControlNode": "FLOAT Key Control @ vrch.ai",
    "VrchFloatOSCControlNode": "FLOAT OSC Control @ vrch.ai",
    "VrchFloatRemapNode": "FLOAT Remap @ vrch.ai",
    "VrchGamepadLoaderNode": "Gamepad Loader @ vrch.ai",
    "VrchImageChannelLoaderNode": "IMAGE Web Viewer Channel Loader @ vrch.ai",
    "VrchImageFlipBookWebViewerNode": "IMAGE Flipbook Web Viewer @ vrch.ai",
    "VrchImagePreviewBackgroundNode": "IMAGE Preview in Background (Legacy) @ vrch.ai",
    "VrchImagePreviewBackgroundNewNode": "IMAGE Preview in Background @ vrch.ai",
    "VrchImageSaverNode": "IMAGE Saver @ vrch.ai",
    "VrchImageSwitchOSCControlNode": "IMAGE Switch OSC Control @ vrch.ai",
    "VrchImageWebSocketChannelLoaderNode": "IMAGE WebSocket Channel Loader @ vrch.ai",
    "VrchImageWebSocketWebViewerNode": "IMAGE WebSocket Web Viewer @ vrch.ai",
    "VrchImageWebViewerNode": "IMAGE Web Viewer @ vrch.ai",
    "VrchInstantQueueKeyControlNode": "Instant Queue Key Control @ vrch.ai",
    "VrchIntKeyControlNode": "INT Key Control @ vrch.ai",
    "VrchIntOSCControlNode": "INT OSC Control @ vrch.ai",
    "VrchIntRemapNode": "INT Remap @ vrch.ai",
    "VrchJsonUrlLoaderNode": "JSON URL Loader @ vrch.ai",
    "VrchJsonWebSocketChannelLoaderNode": "JSON WebSocket Channel Loader @ vrch.ai",
    "VrchJsonWebSocketSenderNode": "JSON WebSocket Sender @ vrch.ai",
    "VrchMidiDeviceLoaderNode": "MIDI Device Loader @ vrch.ai",
    "VrchModelWebViewerNode": "3D MODEL Web Viewer @ vrch.ai",
    "VrchOSCControlSettingsNode": "OSC Control Settings @ vrch.ai",
    "VrchSwitchOSCControlNode": "SWITCH OSC Control @ vrch.ai",
    "VrchTextConcatOSCControlNode": "TEXT Concat OSC Control @ vrch.ai",
    "VrchTextKeyControlNode": "TEXT Key Control @ vrch.ai",
    "VrchTextSrtPlayerNode": "TEXT SRT Player @ vrch.ai",
    "VrchTextSwitchOSCControlNode": "TEXT Switch OSC Control @ vrch.ai",
    "VrchTriggerToggleNode": "Trigger Toggle @ vrch.ai",
    "VrchTriggerToggleX4Node": "Trigger Toggle x4 @ vrch.ai",
    "VrchTriggerToggleX8Node": "Trigger Toggle x8 @ vrch.ai",
    "VrchVideoWebViewerNode": "VIDEO Web Viewer @ vrch.ai",
    "VrchWebSocketServerNode": "WebSocket Server @ vrch.ai",
    "VrchWebViewerNode": "Web Viewer @ vrch.ai",
    "VrchXboxControllerNode": "Xbox Controller Mapper @ vrch.ai",
    "VrchXYOSCControlNode": "XY OSC Control @ vrch.ai",
    "VrchXYZOSCControlNode": "XYZ OSC Control @ vrch.ai",
}

# WEB_DIRECTORY is the comfyui nodes directory that ComfyUI will link and auto-load.
WEB_DIRECTORY = "./web/comfyui"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

