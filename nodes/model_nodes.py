"""Model loading and fallback nodes for ComfyUI workflows."""

from pathlib import Path

import folder_paths


CATEGORY = "vrch.ai/model"
NO_ENGINE_OPTION = "No TensorRT Engine Found"
LOAD_MODES = ["auto", "tensorrt", "pytorch"]

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


def _get_tensorrt_loader_class():
    # Resolve the optional node only when this node executes. This keeps the
    # vrch.ai node package loadable on hosts without ComfyUI-TensorRT.
    import nodes as comfy_nodes

    return getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get("TensorRTLoader")


def _one_line_error(error):
    message = " ".join(str(error).split())
    return f"{type(error).__name__}: {message}"[:320]


class VrchTensorRTAutoLoaderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "load_mode": (LOAD_MODES, {"default": "auto"}),
                "engine_name": (_engine_options(),),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("model", "backend", "status")
    FUNCTION = "load_model"
    CATEGORY = CATEGORY

    def __init__(self):
        self._cached_key = None
        self._cached_model = None

    @classmethod
    def VALIDATE_INPUTS(cls, engine_name):
        # Engine choices are host-local. A workflow saved on another host, or
        # before an Engine was removed, must reach load_model() so auto mode can
        # fall back instead of failing ComfyUI's pre-execution COMBO check.
        return True

    @classmethod
    def IS_CHANGED(cls, model, load_mode, engine_name, debug=False):
        if load_mode == "pytorch":
            return "pytorch"
        engine_path = _resolve_engine_path(engine_name)
        if engine_path is None:
            return (load_mode, engine_name, "missing")
        try:
            fingerprint = _engine_fingerprint(engine_path)
        except OSError:
            return (load_mode, engine_name, "unreadable")
        return (load_mode, engine_name, fingerprint)

    def load_model(self, model, load_mode, engine_name, debug=False):
        if load_mode == "pytorch":
            return self._pytorch_result(
                model,
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
            )

        model_type = _infer_tensorrt_model_type(model)
        if model_type is None:
            return self._load_failure(
                model,
                load_mode,
                "the input model type is not supported by TensorRTLoader",
                debug,
            )

        loader_class = _get_tensorrt_loader_class()
        if loader_class is None:
            return self._load_failure(
                model,
                load_mode,
                "TensorRTLoader is not installed or registered",
                debug,
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
            )

        cache_key = (id(model), model_type, engine_name, fingerprint)
        if cache_key == self._cached_key and self._cached_model is not None:
            self._debug(debug, f"cache hit engine={engine_name} model_type={model_type}")
            return (
                self._cached_model,
                "tensorrt",
                f"TensorRT active: {engine_name}",
            )

        self._debug(debug, f"loading engine={engine_name} model_type={model_type}")
        try:
            loaded = loader_class().load_unet(engine_name, model_type)
            if not isinstance(loaded, tuple) or not loaded or loaded[0] is None:
                raise RuntimeError("TensorRTLoader returned no MODEL")
            tensorrt_model = loaded[0]
        except Exception as error:
            self._cached_key = None
            self._cached_model = None
            return self._load_failure(
                model,
                load_mode,
                f"TensorRT load failed: {_one_line_error(error)}",
                debug,
                cause=error,
            )

        self._cached_key = cache_key
        self._cached_model = tensorrt_model
        self._debug(debug, f"TensorRT active engine={engine_name}")
        return (
            tensorrt_model,
            "tensorrt",
            f"TensorRT active: {engine_name}",
        )

    def _load_failure(self, model, load_mode, reason, debug, cause=None):
        self._debug(debug, reason)
        if load_mode == "tensorrt":
            error = RuntimeError(f"TensorRT Auto Loader: {reason}")
            if cause is not None:
                raise error from cause
            raise error
        return self._pytorch_result(model, f"PyTorch fallback: {reason}", debug)

    def _pytorch_result(self, model, status, debug):
        self._debug(debug, status)
        return (model, "pytorch", status)

    @staticmethod
    def _debug(enabled, message):
        if enabled:
            print(f"[VrchTensorRTAutoLoaderNode] {message}")
