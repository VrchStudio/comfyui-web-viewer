import hashlib
import json
import requests
import srt
from datetime import timedelta
import traceback

CATEGORY="vrch.ai/text"

class VrchJsonUrlLoaderNode:
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
    CATEGORY = CATEGORY
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
    
    
class VrchTextSrtPlayerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "srt_text": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
                "placeholder_text": ("STRING", {"default": "", "multiline": False, "dynamicPrompts": False}),
                "loop": ("BOOLEAN", {"default": False}),
                "current_selection": ("INT", {"default": 1}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("TEXT",)
    CATEGORY = CATEGORY
    FUNCTION = "play_srt_text"

    def play_srt_text(self, 
                      srt_text: str, 
                      placeholder_text: str="",
                      loop: bool=False, 
                      current_selection: int=0, 
                      debug: bool=False):
        try:
            if debug:
                print("Playing SRT Text:", srt_text)
                
            # use -1 as a flag for no selection output
            if current_selection == -1:
                return (placeholder_text,)
                
            # Use srt python lib to parse srt text
            srt_entries = list(srt.parse(srt_text))
            
            if current_selection < 1 or current_selection > len(srt_entries):
                raise IndexError("Current selection index out of range")
            
            selected_text = srt_entries[current_selection-1].content
            
            return (selected_text,)
        
        except Exception as e:
            callsite = traceback.extract_stack()[-2]
            error_message = f"[VrchTextSrtPlayerNode] An error occurred when calling play_srt_text(): {str(e)} at {callsite.filename.split('/')[-1]}:{callsite.lineno}"
            print(error_message)
            raise ValueError(error_message)
    