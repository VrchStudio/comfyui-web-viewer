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
        model_nodes.folder_paths = FakeFolderPaths(self.engine_root)
        self.addCleanup(setattr, model_nodes, "folder_paths", self.original_folder_paths)
        self.addCleanup(setattr, model_nodes, "_get_tensorrt_loader_class", self.original_get_loader)

        self.model = FakeModelPatcher()
        self.tensorrt_model = object()

    def install_loader(self, error=None):
        output_model = self.tensorrt_model

        class FakeLoader:
            calls = []

            def load_unet(self, engine_name, model_type):
                self.calls.append((engine_name, model_type))
                if error is not None:
                    raise error
                return (output_model,)

        model_nodes._get_tensorrt_loader_class = lambda: FakeLoader
        return FakeLoader

    def test_node_contract(self):
        inputs = model_nodes.VrchTensorRTAutoLoaderNode.INPUT_TYPES()["required"]

        self.assertEqual(inputs["model"], ("MODEL",))
        self.assertEqual(inputs["load_mode"][0], ["auto", "tensorrt", "pytorch"])
        self.assertEqual(inputs["engine_name"][0], ["test.engine"])
        self.assertEqual(inputs["debug"], ("BOOLEAN", {"default": False}))
        self.assertEqual(
            model_nodes.VrchTensorRTAutoLoaderNode.RETURN_NAMES,
            ("model", "backend", "status"),
        )

    def test_stale_engine_validation_only_accepts_engine_name(self):
        signature = inspect.signature(model_nodes.VrchTensorRTAutoLoaderNode.VALIDATE_INPUTS)

        self.assertEqual(list(signature.parameters), ["engine_name"])
        self.assertTrue(model_nodes.VrchTensorRTAutoLoaderNode.VALIDATE_INPUTS("removed.engine"))

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

    def test_auto_mode_falls_back_when_engine_is_missing(self):
        result = model_nodes.VrchTensorRTAutoLoaderNode().load_model(
            self.model, "auto", "removed.engine", False
        )

        self.assertIs(result[0], self.model)
        self.assertEqual(result[1], "pytorch")
        self.assertIn("fallback", result[2])

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

    def test_missing_inventory_uses_placeholder(self):
        self.engine_path.unlink()

        options = model_nodes.VrchTensorRTAutoLoaderNode.INPUT_TYPES()["required"]["engine_name"][0]

        self.assertEqual(options, [model_nodes.NO_ENGINE_OPTION])


if __name__ == "__main__":
    unittest.main()
