#!/usr/bin/env python3
"""Tests for VrchTensorRTAutoLoaderNode."""

import importlib.util
import inspect
import sys
import tempfile
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FOLDER_PATHS_STUB = types.ModuleType("folder_paths")
FOLDER_PATHS_STUB.models_dir = ""
FOLDER_PATHS_STUB.get_folder_paths = lambda _name: []
FOLDER_PATHS_STUB.get_filename_list = lambda _name: []
FOLDER_PATHS_STUB.get_full_path = lambda _name, _filename: None
sys.modules["folder_paths"] = FOLDER_PATHS_STUB

SPEC = importlib.util.spec_from_file_location(
    "vrch_model_nodes_under_test",
    PROJECT_ROOT / "nodes" / "model_nodes.py",
)
model_nodes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_nodes)


class SDXL:
    pass


class FakeBaseModel:
    def __init__(self):
        self.model_config = SDXL()


class FakeModelPatcher:
    def __init__(self):
        self.model = FakeBaseModel()


class FakeFolderPaths:
    def __init__(self, root):
        self.root = Path(root)
        self.models_dir = str(self.root.parent)
        self.folder_names_and_paths = {"tensorrt": ([str(self.root)], {".engine"})}

    def get_output_directory(self):
        return str(self.root.parent)

    def get_folder_paths(self, folder_name):
        if folder_name != "tensorrt":
            raise KeyError(folder_name)
        return [str(self.root)]

    def get_filename_list(self, folder_name):
        if folder_name == "checkpoints":
            return ["fallback.safetensors"]
        return sorted(path.name for path in self.root.glob("*.engine"))

    def get_full_path(self, folder_name, filename):
        candidate = self.root / filename
        return str(candidate) if candidate.is_file() else None


class TestTensorRTAutoLoaderNode(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.engine_root = Path(self.temp_dir.name) / "tensorrt"
        self.engine_root.mkdir()
        self.engine_path = self.engine_root / "test.engine"
        self.engine_path.write_bytes(b"engine")

        self.original_folder_paths = model_nodes.folder_paths
        self.original_get_loader = model_nodes._get_tensorrt_loader_class
        self.original_load_checkpoint_model = model_nodes._load_checkpoint_model
        model_nodes.folder_paths = FakeFolderPaths(self.engine_root)
        self.addCleanup(setattr, model_nodes, "folder_paths", self.original_folder_paths)
        self.addCleanup(setattr, model_nodes, "_get_tensorrt_loader_class", self.original_get_loader)
        self.addCleanup(
            setattr,
            model_nodes,
            "_load_checkpoint_model",
            self.original_load_checkpoint_model,
        )

        self.model = FakeModelPatcher()
        self.tensorrt_model = types.SimpleNamespace(
            model=types.SimpleNamespace(
                diffusion_model=types.SimpleNamespace(
                    require_controlnet=False,
                ),
                tensorrt_metadata={},
            )
        )

    def install_loader(self, error=None, capability=None, metadata=None):
        output_model = self.tensorrt_model
        if metadata is not None:
            output_model.model.tensorrt_metadata = metadata

        class FakeLoader:
            CONTROLNET_CAPABILITY = capability
            calls = []

            def load_unet(self, engine_name, model_type, require_controlnet=False):
                if capability is None:
                    self.calls.append((engine_name, model_type))
                else:
                    self.calls.append(
                        (engine_name, model_type, bool(require_controlnet))
                    )
                if error is not None:
                    raise error
                return (output_model,)

        model_nodes._get_tensorrt_loader_class = lambda: FakeLoader
        return FakeLoader

    def test_node_contract(self):
        inputs = model_nodes.VrchTensorRTAutoLoaderNode.INPUT_TYPES()["required"]

        self.assertEqual(inputs["load_mode"][0], ["auto", "tensorrt", "pytorch"])
        self.assertEqual(inputs["engine_name"][0], ["test.engine"])
        self.assertEqual(inputs["debug"], ("BOOLEAN", {"default": False}))
        optional = model_nodes.VrchTensorRTAutoLoaderNode.INPUT_TYPES()["optional"]
        self.assertEqual(optional["model"], ("MODEL", {"lazy": True}))
        self.assertEqual(optional["model_type"][0][0], "auto")
        self.assertIn("sdxl_base", optional["model_type"][0])
        self.assertEqual(
            optional["fallback_checkpoint"][0],
            ["fallback.safetensors"],
        )
        self.assertEqual(
            optional["require_controlnet"],
            ("BOOLEAN", {"default": False}),
        )
        self.assertEqual(
            model_nodes.VrchTensorRTAutoLoaderNode.RETURN_NAMES,
            ("model", "backend", "status"),
        )

    def test_stale_engine_validation_only_accepts_engine_name(self):
        signature = inspect.signature(model_nodes.VrchTensorRTAutoLoaderNode.VALIDATE_INPUTS)

        self.assertEqual(
            list(signature.parameters),
            [
                "engine_name",
                "require_controlnet",
                "model_type",
                "fallback_checkpoint",
            ],
        )
        self.assertTrue(model_nodes.VrchTensorRTAutoLoaderNode.VALIDATE_INPUTS("removed.engine"))

    def test_explicit_model_type_and_checkpoint_keep_model_input_lazy(self):
        node = model_nodes.VrchTensorRTAutoLoaderNode()

        self.assertEqual(
            node.check_lazy_status(
                model=None,
                load_mode="auto",
                engine_name="test.engine",
                model_type="sdxl_base",
                fallback_checkpoint="fallback.safetensors",
            ),
            [],
        )
        self.assertEqual(
            node.check_lazy_status(
                model=None,
                load_mode="auto",
                engine_name="test.engine",
                model_type="auto",
                fallback_checkpoint="fallback.safetensors",
            ),
            ["model"],
        )

    def test_pytorch_mode_bypasses_tensorrt(self):
        loader = self.install_loader()

        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model, "pytorch", "test.engine", False
        )

        self.assertIs(result[0], self.model)
        self.assertEqual(result[1], "pytorch")
        self.assertEqual(loader.calls, [])

    def test_auto_mode_loads_tensorrt_and_reuses_cache(self):
        loader = self.install_loader()
        node = model_nodes.VrchTensorRTAutoLoaderNode()

        first = node.load_model(self.model, "auto", "test.engine", False)
        second = node.load_model(self.model, "auto", "test.engine", False)

        self.assertIs(first[0], self.tensorrt_model)
        self.assertEqual(first[1], "tensorrt")
        self.assertIs(second[0], self.tensorrt_model)
        self.assertEqual(loader.calls, [("test.engine", "sdxl_base")])

    def test_auto_mode_uses_explicit_type_without_loading_fallback(self):
        loader = self.install_loader()
        fallback_calls = []
        model_nodes._load_checkpoint_model = (
            lambda checkpoint: fallback_calls.append(checkpoint)
        )

        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            model=None,
            load_mode="auto",
            engine_name="test.engine",
            model_type="sdxl_base",
            fallback_checkpoint="fallback.safetensors",
        )

        self.assertIs(result[0], self.tensorrt_model)
        self.assertEqual(result[1], "tensorrt")
        self.assertEqual(loader.calls, [("test.engine", "sdxl_base")])
        self.assertEqual(fallback_calls, [])

    def test_auto_mode_falls_back_when_engine_is_missing(self):
        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model, "auto", "removed.engine", False
        )

        self.assertIs(result[0], self.model)
        self.assertEqual(result[1], "pytorch")
        self.assertIn("fallback", result[2])

    def test_auto_mode_lazily_loads_checkpoint_after_engine_failure(self):
        fallback_model = FakeModelPatcher()
        fallback_calls = []

        def load_fallback(checkpoint):
            fallback_calls.append(checkpoint)
            return fallback_model

        model_nodes._load_checkpoint_model = load_fallback
        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            model=None,
            load_mode="auto",
            engine_name="removed.engine",
            model_type="sdxl_base",
            fallback_checkpoint="fallback.safetensors",
        )

        self.assertIs(result[0], fallback_model)
        self.assertEqual(result[1], "pytorch")
        self.assertEqual(fallback_calls, ["fallback.safetensors"])

    def test_tensorrt_mode_fails_when_engine_is_missing(self):
        with self.assertRaisesRegex(RuntimeError, "Engine is unavailable"):
            model_nodes.VrchTensorRTAutoLoaderNode().load_model(
                self.model, "tensorrt", "removed.engine", False
            )

    def test_auto_mode_falls_back_when_loader_fails(self):
        self.install_loader(RuntimeError("incompatible engine"))

        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model, "auto", "test.engine", False
        )

        self.assertIs(result[0], self.model)
        self.assertEqual(result[1], "pytorch")
        self.assertIn("incompatible engine", result[2])

    def test_tensorrt_mode_surfaces_loader_failure(self):
        self.install_loader(RuntimeError("incompatible engine"))

        with self.assertRaisesRegex(RuntimeError, "incompatible engine"):
            model_nodes.VrchTensorRTAutoLoaderNode().load_model(
                self.model, "tensorrt", "test.engine", False
            )

    def test_controlnet_requirement_fails_closed_with_legacy_loader(self):
        self.install_loader()

        with self.assertRaisesRegex(RuntimeError, "lacks the required residual"):
            model_nodes.VrchTensorRTAutoLoaderNode().load_model(
                self.model,
                "tensorrt",
                "test.engine",
                False,
                require_controlnet=True,
            )

    def test_controlnet_auto_mode_falls_back_with_legacy_loader(self):
        self.install_loader()

        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model,
            "auto",
            "test.engine",
            False,
            require_controlnet=True,
        )

        self.assertIs(result[0], self.model)
        self.assertEqual(result[1], "pytorch")
        self.assertIn("required residual", result[2])

    def test_controlnet_requirement_loads_qualified_residual_engine(self):
        loader = self.install_loader(
            capability=model_nodes.CONTROLNET_CAPABILITY,
            metadata={"residual_schema": True},
        )

        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model,
            "tensorrt",
            "test.engine",
            False,
            require_controlnet=True,
        )

        self.assertIs(result[0], self.tensorrt_model)
        self.assertEqual(result[1], "tensorrt")
        self.assertIn("residual_schema=true", result[2])
        self.assertIn("control_required=true", result[2])
        self.assertEqual(loader.calls, [("test.engine", "sdxl_base", True)])

    def test_controlnet_mode_switch_reuses_one_residual_engine(self):
        loader = self.install_loader(
            capability=model_nodes.CONTROLNET_CAPABILITY,
            metadata={"residual_schema": True},
        )
        node = model_nodes.VrchTensorRTAutoLoaderNode()

        off = node.load_model(
            self.model,
            "tensorrt",
            "test.engine",
            False,
            require_controlnet=False,
        )
        on = node.load_model(
            FakeModelPatcher(),
            "tensorrt",
            "test.engine",
            False,
            require_controlnet=True,
        )
        off_again = node.load_model(
            self.model,
            "tensorrt",
            "test.engine",
            False,
            require_controlnet=False,
        )

        self.assertIs(off[0], self.tensorrt_model)
        self.assertIs(on[0], self.tensorrt_model)
        self.assertIs(off_again[0], self.tensorrt_model)
        self.assertEqual(
            loader.calls,
            [("test.engine", "sdxl_base", False)],
        )
        self.assertIn("control_required=true", on[2])
        self.assertIn("control_required=false", off_again[2])
        self.assertFalse(
            self.tensorrt_model.model.diffusion_model.require_controlnet
        )

    def test_controlnet_mode_switch_rejects_cached_plain_engine(self):
        loader = self.install_loader(
            capability=model_nodes.CONTROLNET_CAPABILITY,
            metadata={"residual_schema": False},
        )
        node = model_nodes.VrchTensorRTAutoLoaderNode()
        node.load_model(
            self.model,
            "tensorrt",
            "test.engine",
            False,
            require_controlnet=False,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "ControlNet was required but the TensorRT Engine has no residual bindings",
        ):
            node.load_model(
                self.model,
                "tensorrt",
                "test.engine",
                False,
                require_controlnet=True,
            )

        self.assertEqual(
            loader.calls,
            [("test.engine", "sdxl_base", False)],
        )

    def test_controlnet_requirement_rejects_missing_residual_metadata(self):
        self.install_loader(
            capability=model_nodes.CONTROLNET_CAPABILITY,
            metadata={"residual_schema": False},
        )

        with self.assertRaisesRegex(RuntimeError, "without the required residual"):
            model_nodes.VrchTensorRTAutoLoaderNode().load_model(
                self.model,
                "tensorrt",
                "test.engine",
                False,
                require_controlnet=True,
            )

    def test_missing_inventory_uses_placeholder(self):
        self.engine_path.unlink()

        options = model_nodes.VrchTensorRTAutoLoaderNode.INPUT_TYPES()["required"]["engine_name"][0]

        self.assertEqual(options, [model_nodes.NO_ENGINE_OPTION])


class TestCheckpointClipLoaderNode(unittest.TestCase):
    def setUp(self):
        self.original_folder_paths = model_nodes.folder_paths
        self.original_modules = {
            name: sys.modules.get(name)
            for name in ("comfy", "comfy.sd")
        }
        self.addCleanup(self.restore_modules)
        self.addCleanup(
            setattr,
            model_nodes,
            "folder_paths",
            self.original_folder_paths,
        )

    def restore_modules(self):
        for name, module in self.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def install_runtime(self, clip=object()):
        calls = []
        sd_module = types.ModuleType("comfy.sd")

        def load_checkpoint_guess_config(path, **kwargs):
            calls.append((path, kwargs))
            return (None, clip, None, None)

        sd_module.load_checkpoint_guess_config = load_checkpoint_guess_config
        comfy_module = types.ModuleType("comfy")
        comfy_module.sd = sd_module
        sys.modules["comfy"] = comfy_module
        sys.modules["comfy.sd"] = sd_module
        model_nodes.folder_paths = types.SimpleNamespace(
            get_filename_list=lambda _name: ["sdxl.safetensors"],
            get_full_path_or_raise=lambda folder, name: f"/{folder}/{name}",
            get_folder_paths=lambda folder: [f"/{folder}"],
        )
        return calls, clip

    def test_loads_only_clip_without_constructing_checkpoint_unet(self):
        calls, clip = self.install_runtime()

        result = model_nodes.VrchCheckpointClipLoaderNode().load_clip(
            "sdxl.safetensors"
        )

        self.assertIs(result[0], clip)
        self.assertEqual(calls[0][0], "/checkpoints/sdxl.safetensors")
        self.assertFalse(calls[0][1]["output_model"])
        self.assertFalse(calls[0][1]["output_vae"])
        self.assertTrue(calls[0][1]["output_clip"])

    def test_rejects_checkpoint_without_clip(self):
        self.install_runtime(clip=None)

        with self.assertRaisesRegex(RuntimeError, "does not contain"):
            model_nodes.VrchCheckpointClipLoaderNode().load_clip(
                "sdxl.safetensors"
            )


class TestControlNetLoaderNode(unittest.TestCase):
    def setUp(self):
        self.original_folder_paths = model_nodes.folder_paths
        self.original_modules = {
            name: sys.modules.get(name)
            for name in (
                "torch",
                "comfy",
                "comfy.controlnet",
                "comfy.model_management",
            )
        }
        self.addCleanup(self.restore_modules)
        self.addCleanup(
            setattr,
            model_nodes,
            "folder_paths",
            self.original_folder_paths,
        )

    def restore_modules(self):
        for name, module in self.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def install_runtime(self, error=None):
        calls = []
        gpu_device = object()
        cpu_device = object()
        model_management = types.ModuleType("comfy.model_management")
        original_offload = lambda: gpu_device
        model_management.unet_offload_device = original_offload

        controlnet_module = types.ModuleType("comfy.controlnet")

        def load_controlnet(path):
            calls.append((path, model_management.unet_offload_device()))
            if error is not None:
                raise error
            return types.SimpleNamespace(
                control_model_wrapped=types.SimpleNamespace(
                    offload_device=model_management.unet_offload_device()
                )
            )

        controlnet_module.load_controlnet = load_controlnet
        comfy_module = types.ModuleType("comfy")
        comfy_module.controlnet = controlnet_module
        comfy_module.model_management = model_management
        torch_module = types.ModuleType("torch")
        torch_module.device = lambda name: cpu_device if name == "cpu" else name

        sys.modules["torch"] = torch_module
        sys.modules["comfy"] = comfy_module
        sys.modules["comfy.controlnet"] = controlnet_module
        sys.modules["comfy.model_management"] = model_management
        return calls, model_management, original_offload, cpu_device

    def test_loads_controlnet_with_cpu_offload_and_restores_global(self):
        calls, model_management, original_offload, cpu_device = (
            self.install_runtime()
        )
        model_nodes.folder_paths = types.SimpleNamespace(
            get_full_path_or_raise=lambda folder, name: f"/{folder}/{name}",
        )

        result = model_nodes.VrchControlNetLoaderNode().load_controlnet(
            "union.safetensors"
        )

        self.assertEqual(
            calls,
            [("/controlnet/union.safetensors", cpu_device)],
        )
        self.assertIs(
            result[0].control_model_wrapped.offload_device,
            cpu_device,
        )
        self.assertIs(
            model_management.unet_offload_device,
            original_offload,
        )

    def test_restores_global_after_load_failure(self):
        _, model_management, original_offload, _ = self.install_runtime(
            RuntimeError("broken checkpoint")
        )
        model_nodes.folder_paths = types.SimpleNamespace(
            get_full_path_or_raise=lambda _folder, _name: "/broken.safetensors",
        )

        with self.assertRaisesRegex(RuntimeError, "broken checkpoint"):
            model_nodes.VrchControlNetLoaderNode().load_controlnet(
                "broken.safetensors"
            )

        self.assertIs(
            model_management.unet_offload_device,
            original_offload,
        )


class TestTAESDMemoryProfileNode(unittest.TestCase):
    def test_applies_fixed_encode_and_decode_budget(self):
        class TAESD:
            pass

        vae = types.SimpleNamespace(
            first_stage_model=TAESD(),
            memory_used_encode=lambda _shape, _dtype: 1,
            memory_used_decode=lambda _shape, _dtype: 2,
        )

        result = model_nodes.VrchTAESDMemoryProfileNode().apply_profile(
            vae,
            256,
        )

        self.assertIs(result[0], vae)
        self.assertEqual(vae.memory_used_encode(None, None), 256 * 1024 * 1024)
        self.assertEqual(vae.memory_used_decode(None, None), 256 * 1024 * 1024)
        self.assertEqual(
            vae.vrch_memory_profile,
            {"kind": "taesd", "memory_mib": 256},
        )

    def test_rejects_non_taesd_vae(self):
        vae = types.SimpleNamespace(first_stage_model=object())

        with self.assertRaisesRegex(RuntimeError, "requires a TAESD VAE"):
            model_nodes.VrchTAESDMemoryProfileNode().apply_profile(vae, 256)

if __name__ == "__main__":
    unittest.main()
