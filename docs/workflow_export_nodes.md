### Node: `Export Workflow API @ vrch.ai` (vrch.ai/workflow)

Exports the currently executed ComfyUI workflow as **API format JSON** (from hidden `PROMPT`) to a server-side directory.

This node is designed for queue-time export (no extra HTTP route required).
It forces execution on each queue run (`IS_CHANGED = NaN`) to avoid cache-skip on unchanged graphs.

---

### 1. Add the node

Add **`Export Workflow API @ vrch.ai`** into your workflow and connect it into the execution path.

Because this is an `OUTPUT_NODE`, it can be used as an end-stage export step.

---

### 2. Configure parameters

- **`enable_save`** (`BOOLEAN`)
  - Global switch for this node.
  - `False` skips export without errors.

- **`workflow_folder`** (`STRING`)
  - Relative subfolder under the selected target base directory.
  - Default: empty string (`""`, save into target root directly).
  - Example: `TensorRT/live_portrait`

- **`workflow_name`** (`STRING`)
  - Output filename. `.json` is auto-appended if missing.
  - Default: `workflow_api`

- **`output_dir_option`** (`COMBO`)
  - `vrch_workflows_api_dir` (default)
  - `comfyui_output_dir`
  - `comfyui_input_dir`
  - `comfyui_temp_dir`
  - `custom_dir`

- **`custom_dir`** (`STRING`)
  - Used only when `output_dir_option = custom_dir`.
  - Always visible in UI for easier editing.
  - Default: empty string (`""`).

- **`pretty_json`** (`BOOLEAN`)
  - Default: `True`
  - `True`: indented JSON
  - `False`: compact JSON

- **`debug`** (`BOOLEAN`)
  - Prints export diagnostics to ComfyUI server logs.

---

### 3. Target directory behavior

The final path is:

`<base_dir>/<workflow_folder>/<workflow_name>.json`

Base directory resolution:

- `vrch_workflows_api_dir` -> `/basedir/user/default/workflows_api`
- `comfyui_output_dir` -> `folder_paths.output_directory`
- `comfyui_input_dir` -> `folder_paths.input_directory` (or fallback getter)
- `comfyui_temp_dir` -> `folder_paths.temp_directory` (or fallback getter)
- `custom_dir` -> user-provided absolute/expanded path

---

### 4. Safety behavior

- `workflow_name` cannot contain path separators.
- `workflow_folder` must be relative and cannot contain `.` / `..` segments.
- Non-finite numeric values (`NaN`, `Infinity`, `-Infinity`) are normalized to `null` for valid JSON output.
- Existing file is overwritten only when content changed (unchanged content skips write via in-process last-export hash cache).

---

### 5. Runner integration example

If your runner reads:

`~/data/comfyui-lite-workflows/workflows_api`

map it into the container, for example:

```yaml
volumes:
  - ${HOME}/data/comfyui-lite-workflows/workflows_api:/basedir/user/default/workflows_api
```

Then set:

- `output_dir_option = vrch_workflows_api_dir`
- `workflow_folder = ""` (or nested relative folder if needed)

The exported file will be available directly to `comfyui-api-runner`.

---

### 6. Typical usage flow

1. Set `workflow_folder` and `workflow_name`.
2. Choose `output_dir_option`.
3. Optionally disable/enable export with `enable_save`.
4. Queue the workflow.
5. The node writes the API JSON on execution.
6. Use runner workflow switching/listing to load the new file.
