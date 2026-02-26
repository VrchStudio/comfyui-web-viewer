import hashlib
import json
import math
import os
import traceback
from pathlib import PurePosixPath

import folder_paths


CATEGORY = "vrch.ai/workflow"
VRCH_WORKFLOWS_API_DIR = "/basedir/user/default/workflows_api"


class VrchWorkflowApiExportNode:
    _last_export_hash_by_path: dict[str, str] = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "enable_save": ("BOOLEAN", {"default": True}),
                "disable_save_in_exported_api": ("BOOLEAN", {"default": True}),
                "workflow_folder": ("STRING", {"default": "", "multiline": False, "dynamicPrompts": False}),
                "workflow_name": ("STRING", {"default": "workflow_api", "multiline": False, "dynamicPrompts": False}),
                "output_dir_option": (
                    ["vrch_workflows_api_dir", "comfyui_output_dir", "comfyui_input_dir", "comfyui_temp_dir", "custom_dir"],
                    {"default": "vrch_workflows_api_dir"},
                ),
                "custom_dir": ("STRING", {"default": "", "multiline": False, "dynamicPrompts": False}),
                "pretty_json": ("BOOLEAN", {"default": True}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("saved_path", "saved")
    FUNCTION = "export_api_workflow"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force execution on every queue run for reliable export.
        return float("nan")

    def export_api_workflow(
        self,
        enable_save: bool,
        workflow_folder: str,
        workflow_name: str,
        output_dir_option: str,
        custom_dir: str,
        disable_save_in_exported_api: bool = True,
        pretty_json: bool = True,
        debug: bool = False,
        prompt=None,
    ):
        if not enable_save:
            if debug:
                print("[VrchWorkflowApiExportNode] Export disabled; skip export.")
            return ("", False)

        if not isinstance(prompt, dict):
            if debug:
                print("[VrchWorkflowApiExportNode] Prompt is empty or invalid; skip export.")
            return ("", False)

        try:
            base_dir = self._resolve_base_dir(output_dir_option, custom_dir)
            folder_rel = self._sanitize_folder(workflow_folder)
            filename = self._sanitize_filename(workflow_name)
            output_dir = os.path.join(base_dir, folder_rel) if folder_rel else base_dir
            os.makedirs(output_dir, exist_ok=True)
            prompt_safe = self._normalize_json_value(prompt)
            prompt_safe = self._strip_runtime_fields(prompt_safe)
            if disable_save_in_exported_api:
                prompt_safe = self._disable_export_node_save(prompt_safe)

            output_path = os.path.join(output_dir, filename)
            content_key = json.dumps(prompt_safe, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)
            content_hash = hashlib.sha1(content_key.encode("utf-8")).hexdigest()
            last_hash = self._last_export_hash_by_path.get(output_path)
            if last_hash == content_hash:
                if debug:
                    print(f"[VrchWorkflowApiExportNode] Workflow unchanged; skip save: {output_path}")
                return (output_path, True)

            with open(output_path, "w", encoding="utf-8") as f:
                if pretty_json:
                    json.dump(prompt_safe, f, ensure_ascii=False, indent=2, allow_nan=False)
                else:
                    json.dump(prompt_safe, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            self._last_export_hash_by_path[output_path] = content_hash

            if debug:
                print(f"[VrchWorkflowApiExportNode] Exported API workflow to: {output_path}")

            return (output_path, True)
        except Exception as e:
            print("[VrchWorkflowApiExportNode] Export failed.")
            print(
                "[VrchWorkflowApiExportNode] "
                f"output_dir_option={output_dir_option}, workflow_folder={workflow_folder!r}, "
                f"workflow_name={workflow_name!r}, custom_dir={custom_dir!r}"
            )
            traceback.print_exc()
            return ("", False)

    def _resolve_base_dir(self, output_dir_option: str, custom_dir: str) -> str:
        if output_dir_option == "vrch_workflows_api_dir":
            return os.path.abspath(VRCH_WORKFLOWS_API_DIR)
        if output_dir_option == "comfyui_output_dir":
            return os.path.abspath(getattr(folder_paths, "output_directory", folder_paths.get_output_directory()))
        if output_dir_option == "comfyui_input_dir":
            input_dir = getattr(folder_paths, "input_directory", None)
            if input_dir is None and hasattr(folder_paths, "get_input_directory"):
                input_dir = folder_paths.get_input_directory()
            if not input_dir:
                raise ValueError("ComfyUI input directory is not available")
            return os.path.abspath(input_dir)
        if output_dir_option == "comfyui_temp_dir":
            temp_dir = getattr(folder_paths, "temp_directory", None)
            if temp_dir is None and hasattr(folder_paths, "get_temp_directory"):
                temp_dir = folder_paths.get_temp_directory()
            if not temp_dir:
                raise ValueError("ComfyUI temp directory is not available")
            return os.path.abspath(temp_dir)
        if output_dir_option == "custom_dir":
            custom_dir = (custom_dir or "").strip()
            if not custom_dir:
                raise ValueError("custom_dir cannot be empty when output_dir_option is custom_dir")
            return os.path.abspath(os.path.expanduser(custom_dir))
        raise ValueError(f"Unsupported output_dir_option: {output_dir_option}")

    def _sanitize_folder(self, folder: str) -> str:
        raw = (folder or "").strip().replace("\\", "/")
        if not raw:
            return ""
        path = PurePosixPath(raw)
        if path.is_absolute():
            raise ValueError("workflow_folder must be a relative path")
        parts = []
        for part in path.parts:
            if part in ("", ".", ".."):
                raise ValueError("workflow_folder contains invalid path segments")
            parts.append(part)
        return os.path.join(*parts) if parts else ""

    def _sanitize_filename(self, name: str) -> str:
        filename = (name or "").strip()
        if not filename:
            raise ValueError("workflow_name cannot be empty")
        if "/" in filename or "\\" in filename:
            raise ValueError("workflow_name must not contain path separators")
        if filename in (".", ".."):
            raise ValueError("workflow_name is invalid")
        if not filename.lower().endswith(".json"):
            filename = f"{filename}.json"
        return filename

    def _normalize_json_value(self, value):
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return value
        if isinstance(value, dict):
            return {k: self._normalize_json_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize_json_value(v) for v in value]
        if isinstance(value, tuple):
            return [self._normalize_json_value(v) for v in value]
        return value

    def _strip_runtime_fields(self, workflow):
        if not isinstance(workflow, dict):
            return workflow
        for node in workflow.values():
            if isinstance(node, dict):
                node.pop("is_changed", None)
        return workflow

    def _disable_export_node_save(self, workflow):
        if not isinstance(workflow, dict):
            return workflow
        for node in workflow.values():
            if not isinstance(node, dict):
                continue
            if node.get("class_type") != "VrchWorkflowApiExportNode":
                continue
            inputs = node.get("inputs")
            if not isinstance(inputs, dict):
                inputs = {}
                node["inputs"] = inputs
            inputs["enable_save"] = False
        return workflow
