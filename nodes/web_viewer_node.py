import os
import server
from aiohttp import web

class WebViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "display_image"
    CATEGORY = "vrch.io/web"

    def display_image(self, image):
        # Save the image to a temporary file
        temp_path = os.path.join(os.path.dirname(__file__), "web", "temp_image.png")
        # Implement image saving logic here
        
        # Start web server to display the image
        app = web.Application()
        app.router.add_static('/', os.path.join(os.path.dirname(__file__), "web"))
        server.PromptServer.instance.app.add_subapp("/web_viewer", app)
        
        print("Web viewer is available at: http://localhost:8188/web_viewer")
        return ()