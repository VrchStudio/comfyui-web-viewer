# Model Nodes

## TensorRT Auto Loader @ vrch.ai

Loads a selected local TensorRT Engine when available while keeping the original ComfyUI `MODEL` as a fallback.

### Inputs

- **`model`** (`MODEL`): Original model used by `pytorch` mode and by `auto` fallback.
- **`load_mode`**:
  - `auto`: Load the selected TensorRT Engine; use the original model if loading is unavailable or fails.
  - `tensorrt`: Require the selected TensorRT Engine and stop the prompt if it cannot be loaded.
  - `pytorch`: Bypass TensorRT and use the original model.
- **`engine_name`**: TensorRT Engine from the host's ComfyUI `output/tensorrt` directory or another registered TensorRT model path.
- **`debug`**: Print concise loader, cache, and fallback diagnostics to the ComfyUI server console.

### Outputs

- **`model`** (`MODEL`): TensorRT model or the original model selected by `load_mode`.
- **`backend`** (`STRING`): Actual backend, `tensorrt` or `pytorch`.
- **`status`** (`STRING`): Loading result or fallback reason.

### Behavior

The node is independent of Live Console Maintenance and does not require custom frontend JavaScript. Engine choices use ComfyUI's native dropdown. Refresh the ComfyUI frontend after adding a new Engine so the dropdown is rebuilt.

An Engine name saved by another host or removed later is accepted by the workflow. In `auto` mode it safely falls back to the input model; in `tensorrt` mode it reports an error. TensorRT inference errors that occur after the model has loaded are not retried with PyTorch.

The current implementation infers the TensorRT model family from the input `MODEL`. The installed `TensorRTLoader` remains responsible for Engine deserialization and compatibility.
