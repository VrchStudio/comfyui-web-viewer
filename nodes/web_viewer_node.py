import webbrowser

class WebViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {
                    "default": "https://vrch.ai/dev/vrch-image-instant-viewer?u=vrch",
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

    def dummy_function(self, url):
        # This function does nothing, it's just a placeholder
        return ()

    @classmethod
    def IS_CHANGED(s, **kwargs):
        return False

    @classmethod
    def UI(s):
        return {"widget": {"open_viewer": ("button", "Open Web Viewer")}}