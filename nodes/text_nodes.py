import hashlib
import json
import re
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
    

class VrchTextWordReplacerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
                "rules": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
                "match_mode": (["whole_word", "literal"], {"default": "whole_word"}),
                "case_sensitive": ("BOOLEAN", {"default": False}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "JSON")
    RETURN_NAMES = ("TEXT", "REPLACE_REPORT")
    CATEGORY = CATEGORY
    FUNCTION = "replace_text"

    def __init__(self):
        self._rules_cache_key = None
        self._rules_cache_value = None

    @staticmethod
    def _rule_key(source: str, case_sensitive: bool):
        return source if case_sensitive else source.casefold()

    @classmethod
    def _parse_replacement_rules(cls, rules: str, case_sensitive: bool=False):
        parsed = {}
        ignored_count = 0
        for raw_line in (rules or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=>" not in line:
                ignored_count += 1
                continue

            source, target = line.split("=>", 1)
            source = source.strip()
            target = target.strip()
            if not source:
                ignored_count += 1
                continue

            parsed[cls._rule_key(source, case_sensitive)] = {
                "source": source,
                "target": target,
            }

        return list(parsed.values()), ignored_count

    @classmethod
    def _compile_replacement_rules(cls, rules: str, match_mode: str, case_sensitive: bool=False):
        parsed_rules, ignored_count = cls._parse_replacement_rules(rules, case_sensitive)
        if not parsed_rules:
            return None, {}, [], ignored_count

        sorted_rules = sorted(parsed_rules, key=lambda rule: len(rule["source"]), reverse=True)
        pattern_body = "|".join(re.escape(rule["source"]) for rule in sorted_rules)
        if match_mode == "whole_word":
            pattern_text = rf"(?<!\w)({pattern_body})(?!\w)"
        else:
            pattern_text = rf"({pattern_body})"

        flags = 0 if case_sensitive else re.IGNORECASE
        replacement_map = {
            cls._rule_key(rule["source"], case_sensitive): rule
            for rule in sorted_rules
        }
        return re.compile(pattern_text, flags), replacement_map, sorted_rules, ignored_count

    def _get_compiled_rules(self, rules: str, match_mode: str, case_sensitive: bool):
        cache_key = (rules or "", match_mode, bool(case_sensitive))
        if self._rules_cache_key == cache_key:
            return self._rules_cache_value

        compiled = self._compile_replacement_rules(rules, match_mode, case_sensitive)
        self._rules_cache_key = cache_key
        self._rules_cache_value = compiled
        return compiled

    def replace_text(self,
                     text: str,
                     rules: str,
                     match_mode: str="whole_word",
                     case_sensitive: bool=False,
                     debug: bool=False):
        text = text or ""
        if match_mode not in {"whole_word", "literal"}:
            match_mode = "whole_word"

        pattern, replacement_map, parsed_rules, ignored_count = self._get_compiled_rules(
            rules, match_mode, bool(case_sensitive)
        )

        matched = {}
        replaced_count = 0

        if not pattern:
            report = {
                "rules_count": 0,
                "ignored_rules_count": ignored_count,
                "replaced_count": 0,
                "matched": {},
                "match_mode": match_mode,
                "case_sensitive": bool(case_sensitive),
            }
            return (text, report)

        def replace_match(match):
            nonlocal replaced_count
            source = match.group(0)
            key = self._rule_key(source, bool(case_sensitive))
            rule = replacement_map.get(key)
            if not rule:
                return source
            matched_source = rule["source"]
            target = rule["target"]
            matched[matched_source] = matched.get(matched_source, 0) + 1
            replaced_count += 1
            return target

        output_text = pattern.sub(replace_match, text)
        report = {
            "rules_count": len(parsed_rules),
            "ignored_rules_count": ignored_count,
            "replaced_count": replaced_count,
            "matched": matched,
            "match_mode": match_mode,
            "case_sensitive": bool(case_sensitive),
        }

        if debug:
            print(f"[VrchTextWordReplacerNode] Report: {json.dumps(report, ensure_ascii=False)}")

        return (output_text, report)

    
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
                print("[VrchTextSrtPlayerNode] Playing SRT Text:", srt_text)
                
            # use -1 as a flag for no selection output
            if current_selection == -1:
                return (placeholder_text,)
                
            # Use srt python lib to parse srt text
            srt_entries = list(srt.parse(srt_text))
            
            if current_selection < 1 or current_selection > len(srt_entries):
                raise IndexError("Current selection index out of range")
            
            selected_text = srt_entries[current_selection-1].content
            
            if debug:
                print(f"[VrchTextSrtPlayerNode] Selected SRT Entry [{current_selection}]: {selected_text}")
            
            return (selected_text,)
        
        except Exception as e:
            callsite = traceback.extract_stack()[-2]
            error_message = f"[VrchTextSrtPlayerNode] An error occurred when calling play_srt_text(): {str(e)} at {callsite.filename.split('/')[-1]}:{callsite.lineno}"
            print(error_message)
            raise ValueError(error_message)
        
    @classmethod
    def IS_CHANGED(cls, 
                   srt_text: str, 
                   placeholder_text: str, 
                   loop: bool, 
                   current_selection: int, 
                   debug: bool):
        m = hashlib.sha256()
        m.update(srt_text.encode('utf-8'))
        m.update(placeholder_text.encode('utf-8'))
        m.update(str(loop).encode('utf-8'))
        m.update(str(current_selection).encode('utf-8'))
        return m.hexdigest()
