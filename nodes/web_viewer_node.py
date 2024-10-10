import webbrowser

class VrchWebViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (["image", "audio", "depthmap"], {"default": "image"}),
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
    CATEGORY = "vrch.io/web"
    
    OUTPUT_NODE = True

    DESCRIPTION = "Opens the specified Web Viewer URL in a new browser tab when button is clicked."

    def dummy_function(self, **kwargs):
        return ()

    @classmethod
    def IS_CHANGED(s, **kwargs):
        return False
