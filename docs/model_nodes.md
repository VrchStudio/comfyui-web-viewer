# Model Nodes

The model nodes support TensorRT workflows without forcing an unused PyTorch
UNet to remain resident on the GPU. They are backend nodes and do not require
custom frontend JavaScript.

## Checkpoint CLIP-only Loader @ vrch.ai

Loads only the CLIP text encoder from a checkpoint. Use it when TensorRT owns
the diffusion model but prompts must remain editable during a live session.

### Inputs

- **`ckpt_name`** (`CHECKPOINT`, required): checkpoint selected from ComfyUI's
  registered `checkpoints` paths. The node does not hard-code a default; a new
  node uses the first option exposed by ComfyUI.

### Outputs

- **`CLIP`**: the checkpoint's CLIP text encoder.

### Behavior

- Requests CLIP with `output_clip=True` while explicitly disabling MODEL, VAE,
  and CLIP Vision output.
- Uses ComfyUI's configured embeddings directories.
- Keeps ordinary ComfyUI node caching. Changing prompt text re-runs downstream
  CLIP encoding without reconstructing the checkpoint loader.
- Fails the prompt when the checkpoint contains no supported CLIP encoder.

The node does not expose device, dtype, cache, VAE, UNet, or CLIP Vision
controls. Device and offload behavior remain under ComfyUI model management.

## ControlNet Loader (CPU Offload) @ vrch.ai

Loads a ControlNet checkpoint through ComfyUI while forcing construction onto
CPU. This prevents `--highvram` from constructing another large model directly
on CUDA before ComfyUI can offload or stream it beside a resident TensorRT
Engine.

### Inputs

- **`control_net_name`** (`CONTROL_NET`, required): checkpoint selected from
  ComfyUI's registered `controlnet` paths. There is no hard-coded default.

### Outputs

- **`CONTROL_NET`**: the loaded ControlNet object.

### Behavior

- Temporarily overrides ComfyUI's UNet offload device only for the synchronous
  ControlNet load call, then restores the original function even on failure.
- Serializes loads through a process lock so concurrent calls cannot observe
  the temporary device override.
- Uses ComfyUI's ordinary ControlNet loader and therefore supports any
  ControlNet checkpoint that the installed ComfyUI version supports. Union
  type selection, strength, start/end percentages, and conditioning remain in
  downstream nodes.
- Fails the prompt when the checkpoint contains no supported ControlNet model.

## TAESD Memory Profile @ vrch.ai

Overrides ComfyUI's full-VAE memory estimate with a fixed estimate appropriate
for a TAESD VAE. It does not change VAE math, reserve GPU memory, or unload
CLIP.

### Inputs

- **`vae`** (`VAE`, required): a TAESD VAE.
- **`memory_mib`** (`INT`): reported encode/decode memory requirement.
  - default: `256`
  - minimum: `64`
  - maximum: `1024`
  - step: `64`

### Outputs

- **`VAE`**: the same VAE object with the memory profile applied.

### Behavior

- Applies the configured fixed estimate to both encode and decode scheduling.
- Adds `vrch_memory_profile` metadata for diagnostics.
- Fails the prompt when the input is not a TAESD VAE.

`64 MiB` is the validated Simple workflow value. The node default remains the
more conservative `256 MiB`; lower values should be qualified with the actual
resolution and live workload before deployment.

## TensorRT Auto Loader @ vrch.ai

Loads a selected local TensorRT Engine and exposes the actual backend and
status. PyTorch inputs are lazy, so a healthy TensorRT path does not construct
an unused checkpoint UNet.

### Required inputs

- **`load_mode`**: backend policy. Default: `auto`.
  - `auto`: try TensorRT; return a PyTorch fallback when Engine loading is
    unavailable or fails.
  - `tensorrt`: require TensorRT and fail the prompt instead of falling back.
  - `pytorch`: bypass TensorRT.
- **`engine_name`**: basename of an `.engine` file from ComfyUI's registered
  TensorRT paths, including `output/tensorrt`. There is no hard-coded Engine
  default; `No TensorRT Engine Found` is shown when none are registered.
- **`debug`** (`BOOLEAN`): concise loader, cache, and fallback diagnostics.
  Default: `false`.

### Optional inputs

- **`model`** (`MODEL`, lazy): an existing PyTorch model used for model-family
  inference or fallback only when required.
- **`model_type`**: TensorRT model family. Default: `auto`.
  - `auto`
  - `sdxl_base`
  - `sdxl_refiner`
  - `sd1.x`
  - `sd2.x-768v`
  - `svd`
  - `sd3`
  - `auraflow`
  - `flux_dev`
  - `flux_schnell`
- **`fallback_checkpoint`**: checkpoint used to load only a diffusion MODEL
  when PyTorch fallback is needed. It does not load CLIP, VAE, or CLIP Vision.
  There is no hard-coded default.
- **`require_controlnet`** (`BOOLEAN`): require the installed TensorRT loader
  and selected Engine to implement the VRCH residual ControlNet contract.
  Default: `false`.

### Outputs

- **`model`** (`MODEL`): TensorRT model or PyTorch fallback.
- **`backend`** (`STRING`): actual backend, `tensorrt` or `pytorch`.
- **`status`** (`STRING`): selected Engine, residual/control state, or fallback
  reason.

### Lazy loading and fallback

- An explicit `model_type` lets the TensorRT path skip the lazy `model` input.
- `model_type=auto` evaluates `model` only to infer the model family.
- `auto` or `pytorch` evaluates `model` when no `fallback_checkpoint` is
  configured. When a fallback checkpoint is configured, fallback loads only
  its diffusion MODEL on demand.
- `tensorrt` mode never hides Engine selection, schema, deserialization, or
  compatibility errors behind a PyTorch fallback.
- `auto` fallback covers loader-time failures. TensorRT inference errors after
  the MODEL has been returned are not retried with PyTorch.

Engine choices are host-local. A workflow may contain an Engine name that was
saved on another host or later removed; runtime validation handles that as a
fallback in `auto` mode or an error in `tensorrt` mode. Engine paths are limited
to safe basenames inside registered TensorRT roots.

### Residual ControlNet contract

`require_controlnet=true` requires all of the following:

1. the installed `TensorRTLoader` advertises
   `vrch-tensorrt-controlnet-residual-v1`;
2. the selected Engine contains the residual input schema; and
3. an upstream ControlNet produces residuals at inference time.

A plain Engine is rejected when ControlNet is required. A residual Engine may
also serve a ControlNet-OFF workflow when `require_controlnet=false`; missing
residuals are zero-filled by the qualified TensorRT loader. Switching the same
residual Engine between required and optional modes reuses the cached Engine
instead of deserializing a second copy.

When ComfyUI's `ControlNetApplyAdvanced` receives exact `strength=0`, it may
produce no control dictionary. A workflow with `require_controlnet=true` then
fails loudly by design instead of silently generating an uncontrolled image.
Product workflows should expose an explicit ControlNet ON/OFF state or keep the
ON strength above zero.

### Cache and diagnostics

The Engine cache key includes model type, Engine name, device/inode identity,
size, and modification time. Replacing an Engine invalidates the cached MODEL.
The `status` output records the Engine name, whether the residual schema is
present, and whether ControlNet is required.

Refresh the ComfyUI frontend after adding or removing Engine files so native
dropdown choices are rebuilt.

## Recommended TensorRT workflow wiring

- Route **Checkpoint CLIP-only Loader** to the prompt encoders.
- Route **TensorRT Auto Loader** `model` to the sampler.
- For ControlNet workflows, route **ControlNet Loader (CPU Offload)** through
  the appropriate Union/specialized ControlNet configuration and conditioning
  nodes.
- Route a TAESD VAE through **TAESD Memory Profile** before VAE encode/decode.
- Use an explicit `model_type` and `fallback_checkpoint` so the healthy
  TensorRT path never evaluates a full checkpoint MODEL.
- Set `require_controlnet=true` only for workflows whose output must be
  controlled; leave it `false` for ordinary VJ workflows.

These nodes do not modify image size, prompt, seed, steps, CFG, denoise,
ControlNet strength, or other generation defaults.
