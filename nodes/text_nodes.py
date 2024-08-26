import json
import requests

class JsonUrlLoaderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {"default": ""}),
            },
            "optional": {
                "print_to_console": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("JSON",)
    CATEGORY = "vrch.io/text"
    FUNCTION = "load_json"

    def load_json(self, url: str, print_to_console=False):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # This will raise an HTTPError for bad responses
        
            res = response.json()  # Attempt to parse JSON
            
            if print_to_console:
                print("JSON content:", json.dumps(res, indent=2, ensure_ascii=False))
                 
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            res = {}
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {str(e)}")
            res = {}
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            res = {}

        return (res,)
    