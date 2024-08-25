class ImageSaverNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "path": ("STRING", {"default": "output.png"})
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "save_image"
    CATEGORY = "vrch.io/image"

    def save_image(self, image, path):
        # Implement image saving logic here
        print(f"Image saved to: {path}")
        return ()