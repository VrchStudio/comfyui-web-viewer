"""Model loading and fallback nodes for ComfyUI workflows."""

import threading
from pathlib import Path

import folder_paths


CATEGORY = "vrch.ai/model"
NO_ENGINE_OPTION = "No TensorRT Engine Found"
NO_CHECKPOINT_OPTION = "No PyTorch Fallback Checkpoint Found"
LOAD_MODES = ["auto", "tensorrt", "pytorch"]
CONTROLNET_CAPABILITY = "vrch-tensorrt-controlnet-residual-v1"

print(f"[comfyui-web-viewer] TensorRT capability consumer {CONTROLNET_CAPABILITY}")

_TENSORRT_MODEL_TYPES = {
    "SDXL": "sdxl_base",
    "SDXLRefiner": "sdxl_refiner",
    "SD15": "sd1.x",
    "SD20": "sd2.x-768v",
    "SVD_img2vid": "svd",
    "SD3": "sd3",
    "AuraFlow": "auraflow",
    "Flux": "flux_dev",
    "FluxSchnell": "flux_schnell",
}
_TENSORRT_MODEL_TYPE_OPTIONS = [
    "auto",
    *dict.fromkeys(_TENSORRT_MODEL_TYPES.values()),
]

_CONTROLNET_CPU_LOAD_LOCK = threading.Lock()


class VrchCheckpointClipLoaderNode:
    """Load only the CLIP component from a checkpoint.

    TensorRT workflows do not use the checkpoint's diffusion model. Loading
    the complete checkpoint in ``--highvram`` mode can nevertheless place that
    unused UNet on CUDA and prevent a second TensorRT Engine from fitting.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (
                    folder_paths.get_filename_list("checkpoints"),
                )
            },
        }

    RETURN_TYPES = ("CLIP",)
    FUNCTION = "load_clip"
    CATEGORY = CATEGORY

    def load_clip(self, ckpt_name):
        import comfy.sd

        checkpoint_path = folder_paths.get_full_path_or_raise(
            "checkpoints",
            ckpt_name,
        )
        result = comfy.sd.load_checkpoint_guess_config(
            checkpoint_path,
            output_vae=False,
            output_clip=True,
            output_clipvision=False,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
            output_model=False,
        )
        if result is None or len(result) < 2 or result[1] is None:
            raise RuntimeError(
                "Checkpoint does not contain a supported CLIP text encoder"
            )
        print(
            "[comfyui-web-viewer] Checkpoint CLIP-only load complete: "
            f"{ckpt_name}"
        )
        return (result[1],)


def _register_output_engine_root():
    get_output_directory = getattr(folder_paths, "get_output_directory", None)
    registry = getattr(folder_paths, "folder_names_and_paths", None)
    if not callable(get_output_directory) or not isinstance(registry, dict):
        return

    output_root = str((Path(get_output_directory()) / "tensorrt").resolve())
    if "tensorrt" not in registry:
        registry["tensorrt"] = ([output_root], {".engine"})
        return

    roots, extensions = registry["tensorrt"]
    if output_root not in roots:
        roots.insert(0, output_root)
    extensions.add(".engine")


def _tensorrt_roots():
    _register_output_engine_root()
    try:
        roots = folder_paths.get_folder_paths("tensorrt")
    except (KeyError, ValueError):
        roots = []

    if not roots:
        models_dir = getattr(folder_paths, "models_dir", None)
        if models_dir:
            roots = [str(Path(models_dir) / "tensorrt")]

    return [Path(root).expanduser().resolve() for root in roots]


def _engine_names():
    _register_output_engine_root()
    names = []
    try:
        names = folder_paths.get_filename_list("tensorrt")
    except (KeyError, ValueError):
        for root in _tensorrt_roots():
            if root.is_dir():
                names.extend(path.name for path in root.glob("*.engine") if path.is_file())

    safe_names = {
        name
        for name in names
        if isinstance(name, str)
        and Path(name).name == name
        and Path(name).suffix.lower() == ".engine"
    }
    return sorted(safe_names, key=str.casefold)


def _engine_options():
    engines = _engine_names()
    return engines if engines else [NO_ENGINE_OPTION]


def _checkpoint_options():
    checkpoints = folder_paths.get_filename_list("checkpoints")
    return checkpoints if checkpoints else [NO_CHECKPOINT_OPTION]


def _resolve_engine_path(engine_name):
    _register_output_engine_root()
    if (
        not isinstance(engine_name, str)
        or engine_name == NO_ENGINE_OPTION
        or Path(engine_name).name != engine_name
        or Path(engine_name).suffix.lower() != ".engine"
    ):
        return None

    candidate = None
    try:
        candidate = folder_paths.get_full_path("tensorrt", engine_name)
    except (KeyError, ValueError):
        pass

    if candidate is None:
        for root in _tensorrt_roots():
            possible = root / engine_name
            if possible.is_file():
                candidate = str(possible)
                break

    if candidate is None:
        return None

    resolved = Path(candidate).expanduser().resolve()
    if not resolved.is_file():
        return None
    if not any(resolved.is_relative_to(root) for root in _tensorrt_roots()):
        return None
    return resolved


def _engine_fingerprint(engine_path):
    stat = engine_path.stat()
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
    )


def _infer_tensorrt_model_type(model):
    base_model = getattr(model, "model", None)
    model_config = getattr(base_model, "model_config", None)
    for candidate in (model_config, base_model):
        if candidate is None:
            continue
        model_type = _TENSORRT_MODEL_TYPES.get(type(candidate).__name__)
        if model_type:
            return model_type
    return None


def _load_checkpoint_model(checkpoint_name):
    if (
        not isinstance(checkpoint_name, str)
        or not checkpoint_name
        or checkpoint_name == NO_CHECKPOINT_OPTION
    ):
        raise RuntimeError("no PyTorch fallback checkpoint was configured")

    import comfy.sd

    checkpoint_path = folder_paths.get_full_path_or_raise(
        "checkpoints",
        checkpoint_name,
    )
    result = comfy.sd.load_checkpoint_guess_config(
        checkpoint_path,
        output_vae=False,
        output_clip=False,
        output_clipvision=False,
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
        output_model=True,
    )
    if result is None or not result or result[0] is None:
        raise RuntimeError(
            "fallback checkpoint does not contain a supported diffusion model"
        )
    print(
        "[comfyui-web-viewer] TensorRT lazy PyTorch fallback loaded: "
        f"{checkpoint_name}"
    )
    return result[0]


def _get_tensorrt_loader_class():
    # Resolve the optional node only when this node executes. This keeps the
    # vrch.ai node package loadable on hosts without ComfyUI-TensorRT.
    import nodes as comfy_nodes

    return getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get("TensorRTLoader")


def _one_line_error(error):
    message = " ".join(str(error).split())
    return f"{type(error).__name__}: {message}"[:320]


def _tensorrt_metadata(model):
    base_model = getattr(model, "model", None)
    metadata = getattr(base_model, "tensorrt_metadata", None)
    return metadata if isinstance(metadata, dict) else {}


def _set_tensorrt_control_requirement(model, require_controlnet):
    required = bool(require_controlnet)
    base_model = getattr(model, "model", None)
    diffusion_model = getattr(base_model, "diffusion_model", None)
    if diffusion_model is not None and hasattr(
        diffusion_model,
        "require_controlnet",
    ):
        diffusion_model.require_controlnet = required
    metadata = _tensorrt_metadata(model)
    if metadata:
        metadata["control_required"] = required


class VrchControlNetLoaderNode:
    """Load ControlNet weights on CPU so a resident TRT Engine is not duplicated."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "control_net_name": (
                    folder_paths.get_filename_list("controlnet"),
                )
            },
        }

    RETURN_TYPES = ("CONTROL_NET",)
    FUNCTION = "load_controlnet"
    CATEGORY = CATEGORY

    def load_controlnet(self, control_net_name):
        controlnet_path = folder_paths.get_full_path_or_raise(
            "controlnet",
            control_net_name,
        )

        # ComfyUI's --highvram mode normally constructs ControlNet directly on
        # CUDA. A residual TensorRT Engine can already own most of a 16 GiB
        # device, so construction itself can OOM before model management gets a
        # chance to stream or offload weights. Keep this override scoped to the
        # synchronous load call and restore it even when checkpoint loading
        # fails. ComfyUI executes model-loader nodes on its single prompt worker;
        # the lock also prevents overlapping calls through this node.
        import torch
        import comfy.controlnet
        import comfy.model_management

        cpu_device = torch.device("cpu")
        with _CONTROLNET_CPU_LOAD_LOCK:
            original_offload_device = (
                comfy.model_management.unet_offload_device
            )
            comfy.model_management.unet_offload_device = lambda: cpu_device
            try:
                controlnet = comfy.controlnet.load_controlnet(controlnet_path)
            finally:
                comfy.model_management.unet_offload_device = (
                    original_offload_device
                )

        if controlnet is None:
            raise RuntimeError(
                "ControlNet checkpoint is invalid and contains no supported model"
            )
        print(
            "[comfyui-web-viewer] ControlNet CPU-offload load complete: "
            f"{control_net_name}"
        )
        return (controlnet,)


class VrchTAESDMemoryProfileNode:
    """Use a TAESD-specific memory estimate instead of the full-VAE estimate."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vae": ("VAE",),
                "memory_mib": (
                    "INT",
                    {
                        "default": 256,
                        "min": 64,
                        "max": 1024,
                        "step": 64,
                    },
                ),
            }
        }

    RETURN_TYPES = ("VAE",)
    FUNCTION = "apply_profile"
    CATEGORY = CATEGORY

    def apply_profile(
        self,
        vae,
        memory_mib=256,
    ):
        first_stage_model = getattr(vae, "first_stage_model", None)
        if type(first_stage_model).__name__ != "TAESD":
            raise RuntimeError(
                "TAESD memory profile requires a TAESD VAE"
            )

        memory_bytes = int(memory_mib) * 1024 * 1024
        vae.memory_used_encode = (
            lambda _shape, _dtype: memory_bytes
        )
        vae.memory_used_decode = (
            lambda _shape, _dtype: memory_bytes
        )
        vae.vrch_memory_profile = {
            "kind": "taesd",
            "memory_mib": int(memory_mib),
        }
        print(
            "[comfyui-web-viewer] TAESD memory profile active: "
            f"{int(memory_mib)} MiB"
        )
        return (vae,)


class VrchTensorRTAutoLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "load_mode": (LOAD_MODES, {"default": "auto"}),
                "engine_name": (_engine_options(),),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "model": ("MODEL", {"lazy": True}),
                "model_type": (
                    _TENSORRT_MODEL_TYPE_OPTIONS,
                    {"default": "auto"},
                ),
                "fallback_checkpoint": (_checkpoint_options(),),
                "require_controlnet": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("model", "backend", "status")
    FUNCTION = "load_model"
    CATEGORY = CATEGORY

    def __init__(self):
        self._cached_key = None
        self._cached_model = None
        self._cached_status = None

    @classmethod
    def VALIDATE_INPUTS(
        cls,
        engine_name,
        require_controlnet=False,
        model_type="auto",
        fallback_checkpoint=None,
    ):
        # Engine choices are host-local. A workflow saved on another host, or
        # before an Engine was removed, must reach load_model() so auto mode can
        # fall back instead of failing ComfyUI's pre-execution COMBO check.
        return True

    def check_lazy_status(
        self,
        model=None,
        load_mode="auto",
        engine_name=NO_ENGINE_OPTION,
        debug=False,
        require_controlnet=False,
        model_type="auto",
        fallback_checkpoint=None,
    ):
        del engine_name, debug, require_controlnet
        if model_type == "auto":
            return ["model"]
        if load_mode in ("auto", "pytorch") and not fallback_checkpoint:
            return ["model"]
        return []

    @classmethod
    def IS_CHANGED(
        cls,
        model=None,
        load_mode="auto",
        engine_name=NO_ENGINE_OPTION,
        debug=False,
        require_controlnet=False,
        model_type="auto",
        fallback_checkpoint=None,
    ):
        del model, debug, fallback_checkpoint
        if load_mode == "pytorch":
            return ("pytorch", model_type, bool(require_controlnet))
        engine_path = _resolve_engine_path(engine_name)
        if engine_path is None:
            return (
                load_mode,
                engine_name,
                model_type,
                bool(require_controlnet),
                "missing",
            )
        try:
            fingerprint = _engine_fingerprint(engine_path)
        except OSError:
            return (
                load_mode,
                engine_name,
                model_type,
                bool(require_controlnet),
                "unreadable",
            )
        return (
            load_mode,
            engine_name,
            model_type,
            bool(require_controlnet),
            fingerprint,
        )

    def load_model(
        self,
        model=None,
        load_mode="auto",
        engine_name=NO_ENGINE_OPTION,
        debug=False,
        require_controlnet=False,
        model_type="auto",
        fallback_checkpoint=None,
    ):
        if load_mode == "pytorch":
            return self._pytorch_result(
                self._fallback_model(model, fallback_checkpoint),
                "PyTorch selected",
                debug,
            )

        engine_path = _resolve_engine_path(engine_name)
        if engine_path is None:
            return self._load_failure(
                model,
                load_mode,
                f"TensorRT Engine is unavailable: {engine_name}",
                debug,
                fallback_checkpoint=fallback_checkpoint,
            )

        resolved_model_type = model_type
        if resolved_model_type == "auto":
            resolved_model_type = _infer_tensorrt_model_type(model)
        if resolved_model_type not in _TENSORRT_MODEL_TYPE_OPTIONS[1:]:
            return self._load_failure(
                model,
                load_mode,
                "the TensorRT model type is unavailable or unsupported",
                debug,
                fallback_checkpoint=fallback_checkpoint,
            )

        loader_class = _get_tensorrt_loader_class()
        if loader_class is None:
            return self._load_failure(
                model,
                load_mode,
                "TensorRTLoader is not installed or registered",
                debug,
                fallback_checkpoint=fallback_checkpoint,
            )

        loader_capability = getattr(loader_class, "CONTROLNET_CAPABILITY", None)
        if require_controlnet and loader_capability != CONTROLNET_CAPABILITY:
            return self._load_failure(
                model,
                load_mode,
                "TensorRTLoader lacks the required residual ControlNet capability "
                f"{CONTROLNET_CAPABILITY}",
                debug,
                fallback_checkpoint=fallback_checkpoint,
            )

        try:
            fingerprint = _engine_fingerprint(engine_path)
        except OSError as error:
            return self._load_failure(
                model,
                load_mode,
                f"TensorRT Engine cannot be read: {_one_line_error(error)}",
                debug,
                cause=error,
                fallback_checkpoint=fallback_checkpoint,
            )

        cache_key = (
            resolved_model_type,
            engine_name,
            fingerprint,
        )
        if cache_key == self._cached_key and self._cached_model is not None:
            metadata = _tensorrt_metadata(self._cached_model)
            residual_schema = bool(metadata.get("residual_schema", False))
            if require_controlnet and not residual_schema:
                return self._load_failure(
                    model,
                    load_mode,
                    "ControlNet was required but the TensorRT Engine has no "
                    "residual bindings",
                    debug,
                    fallback_checkpoint=fallback_checkpoint,
                )
            _set_tensorrt_control_requirement(
                self._cached_model,
                require_controlnet,
            )
            self._cached_status = self._active_status(
                engine_name,
                residual_schema,
                require_controlnet,
            )
            self._debug(
                debug,
                f"cache hit engine={engine_name} model_type={resolved_model_type}",
            )
            return (
                self._cached_model,
                "tensorrt",
                self._cached_status,
            )

        self._debug(
            debug,
            f"loading engine={engine_name} model_type={resolved_model_type}",
        )
        try:
            loader = loader_class()
            if loader_capability == CONTROLNET_CAPABILITY:
                loaded = loader.load_unet(
                    engine_name,
                    resolved_model_type,
                    require_controlnet=bool(require_controlnet),
                )
            else:
                loaded = loader.load_unet(engine_name, resolved_model_type)
            if not isinstance(loaded, tuple) or not loaded or loaded[0] is None:
                raise RuntimeError("TensorRTLoader returned no MODEL")
            tensorrt_model = loaded[0]
            metadata = _tensorrt_metadata(tensorrt_model)
            residual_schema = bool(metadata.get("residual_schema", False))
            if require_controlnet and not residual_schema:
                raise RuntimeError(
                    "TensorRTLoader returned an Engine without the required residual schema"
                )
            _set_tensorrt_control_requirement(
                tensorrt_model,
                require_controlnet,
            )
        except Exception as error:
            self._cached_key = None
            self._cached_model = None
            self._cached_status = None
            return self._load_failure(
                model,
                load_mode,
                f"TensorRT load failed: {_one_line_error(error)}",
                debug,
                cause=error,
                fallback_checkpoint=fallback_checkpoint,
            )

        self._cached_key = cache_key
        self._cached_model = tensorrt_model
        self._cached_status = self._active_status(
            engine_name,
            residual_schema,
            require_controlnet,
        )
        self._debug(debug, f"TensorRT active engine={engine_name}")
        return (
            tensorrt_model,
            "tensorrt",
            self._cached_status,
        )

    def _load_failure(
        self,
        model,
        load_mode,
        reason,
        debug,
        cause=None,
        fallback_checkpoint=None,
    ):
        self._cached_key = None
        self._cached_model = None
        self._cached_status = None
        self._debug(debug, reason)
        if load_mode == "tensorrt":
            error = RuntimeError(f"TensorRT Auto Loader: {reason}")
            if cause is not None:
                raise error from cause
            raise error
        try:
            fallback_model = self._fallback_model(
                model,
                fallback_checkpoint,
            )
        except Exception as fallback_error:
            error = RuntimeError(
                "TensorRT Auto Loader: "
                f"{reason}; PyTorch fallback failed: "
                f"{_one_line_error(fallback_error)}"
            )
            raise error from fallback_error
        return self._pytorch_result(
            fallback_model,
            f"PyTorch fallback: {reason}",
            debug,
        )

    @staticmethod
    def _fallback_model(model, fallback_checkpoint):
        if model is not None:
            return model
        return _load_checkpoint_model(fallback_checkpoint)

    def _pytorch_result(self, model, status, debug):
        self._debug(debug, status)
        return (model, "pytorch", status)

    @staticmethod
    def _active_status(engine_name, residual_schema, require_controlnet):
        return (
            f"TensorRT active: {engine_name}; "
            f"residual_schema={str(bool(residual_schema)).lower()}; "
            f"control_required={str(bool(require_controlnet)).lower()}"
        )

    @staticmethod
    def _debug(enabled, message):
        if enabled:
            print(f"[VrchTensorRTAutoLoaderNode] {message}")
