#!/usr/bin/env python3
"""Tests for websocket_nodes.py.

This suite validates helper handlers and node/client integration behavior.
"""

import asyncio
import io
import json
import socket
import struct
import sys
import time
import unittest
from pathlib import Path

import numpy as np
import websockets
from PIL import Image

# Import package as module to keep relative imports in websocket_nodes working.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes import websocket_nodes as ws_nodes  # noqa: E402
from nodes.utils.websocket_server import (  # noqa: E402
    SimpleWebSocketServer,
    get_global_server,
    _port_servers,
    _server_lock,
)


class TestWebSocketNodesUnit(unittest.TestCase):
    def test_01_json_state_merger(self):
        merger = ws_nodes.JsonStateMerger(max_keys=2, clear_key="__clear__", debug=False)

        self.assertEqual(merger('{"a":1}'), {"a": 1})
        self.assertEqual(merger('{"b":2}'), {"a": 1, "b": 2})

        # max_keys should prevent adding a third key.
        self.assertEqual(merger('{"c":3}'), {"a": 1, "b": 2})

        # clear key should reset state.
        self.assertEqual(merger('{"__clear__": true, "z":9}'), {"z": 9})

    def test_02_audio_data_handler(self):
        valid = json.dumps({"base64_data": "abc", "meta": 1})
        self.assertEqual(ws_nodes.audio_data_handler(valid), {"base64_data": "abc", "meta": 1})

        valid_bytes = valid.encode("utf-8")
        self.assertEqual(ws_nodes.audio_data_handler(valid_bytes), {"base64_data": "abc", "meta": 1})

        self.assertIsNone(ws_nodes.audio_data_handler("not-json"))
        self.assertIsNone(ws_nodes.audio_data_handler(json.dumps({"no_base64": True})))

    def test_03_image_data_handler(self):
        img = Image.new("RGB", (2, 2), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        batch_id = 7
        frame_index = 1
        frame_total = 2
        meta = (batch_id << 16) | (frame_index << 8) | frame_total
        payload = struct.pack(">II", 1, meta) + buf.getvalue()

        tensor = ws_nodes.image_data_handler(payload)

        self.assertIsNotNone(tensor)
        self.assertEqual(tuple(tensor.shape), (1, 2, 2, 3))
        self.assertTrue(hasattr(tensor, "_metadata"))
        self.assertEqual(tensor._metadata["batch_id"], batch_id)
        self.assertEqual(tensor._metadata["frame_index"], frame_index)
        self.assertEqual(tensor._metadata["frame_total"], frame_total)

        self.assertIsNone(ws_nodes.image_data_handler("text"))
        self.assertIsNone(ws_nodes.image_data_handler(b"123"))

    def test_04_latent_data_handler(self):
        samples = np.zeros((1, 4, 2, 2), dtype=np.float32).tolist()
        payload = json.dumps({"samples": samples, "shape": [1, 4, 2, 2]})

        latent = ws_nodes.latent_data_handler(payload)
        self.assertIsNotNone(latent)
        self.assertIn("samples", latent)
        self.assertEqual(tuple(latent["samples"].shape), (1, 4, 2, 2))
        self.assertEqual(latent.get("channels"), 4)

        self.assertIsNone(ws_nodes.latent_data_handler("not-json"))


class TestWebSocketNodesIntegration(unittest.TestCase):
    def setUp(self):
        self.host = "127.0.0.1"

        ws_nodes.stop_all_websocket_clients()
        with _server_lock:
            for server in list(_port_servers.values()):
                try:
                    if hasattr(server, "stop"):
                        server.stop()
                except Exception:
                    pass
            _port_servers.clear()

    def tearDown(self):
        ws_nodes.stop_all_websocket_clients()
        with _server_lock:
            for server in list(_port_servers.values()):
                try:
                    if hasattr(server, "stop"):
                        server.stop()
                except Exception:
                    pass
            _port_servers.clear()
        time.sleep(0.2)

    @staticmethod
    def _wait_for(predicate, timeout=3.0, interval=0.05):
        end = time.time() + timeout
        while time.time() < end:
            value = predicate()
            if value:
                return value
            time.sleep(interval)
        return None

    @staticmethod
    def _find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def test_05_client_cache_reuse_and_refresh(self):
        port = self._find_free_port()
        server = SimpleWebSocketServer(self.host, port, debug=False)
        server.register_path("/json")
        time.sleep(1.0)

        client1 = ws_nodes.get_websocket_client(
            self.host,
            port,
            "/json",
            1,
            data_handler=ws_nodes.make_json_state_handler(debug=False),
            debug=False,
        )
        client2 = ws_nodes.get_websocket_client(
            self.host,
            port,
            "/json",
            1,
            data_handler=ws_nodes.make_json_state_handler(debug=False),
            debug=False,
        )
        self.assertIs(client1, client2)

        connected = self._wait_for(
            lambda: len(server.clients.get("/json", {}).get(1, [])) >= 1,
            timeout=3.0,
        )
        self.assertTrue(connected, "WebSocket client did not connect in time")

        server.send_to_channel("/json", 1, json.dumps({"a": 1}))

        data = self._wait_for(lambda: client1.get_latest_data(), timeout=3.0)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("a"), 1)

        client1.stop()
        time.sleep(0.3)

        client3 = ws_nodes.get_websocket_client(
            self.host,
            port,
            "/json",
            1,
            data_handler=ws_nodes.make_json_state_handler(debug=False),
            debug=False,
        )
        self.assertIsNot(client3, client1)

        connected2 = self._wait_for(
            lambda: len(server.clients.get("/json", {}).get(1, [])) >= 1,
            timeout=3.0,
        )
        self.assertTrue(connected2, "Replacement WebSocket client did not connect in time")

        server.send_to_channel("/json", 1, json.dumps({"b": 2}))
        data2 = self._wait_for(lambda: client3.get_latest_data(), timeout=3.0)
        self.assertIsInstance(data2, dict)
        self.assertEqual(data2.get("b"), 2)

    def test_06_json_sender_and_loader_integration(self):
        port = self._find_free_port()
        server = get_global_server(self.host, port, path="/json", debug=False)
        running = self._wait_for(lambda: server.is_running(), timeout=3.0)
        self.assertTrue(running, "Managed WebSocket server did not start in time")

        sender = ws_nodes.VrchJsonWebSocketSenderNode()

        async def send_and_receive():
            uri = f"ws://{self.host}:{port}/json?channel=1"
            async with websockets.connect(uri) as ws:
                await asyncio.sleep(0.1)
                sent = sender.send_json(
                    json_string='{"hello":"world"}',
                    channel="1",
                    server=f"{self.host}:{port}",
                    debug=False,
                )
                message = await asyncio.wait_for(ws.recv(), timeout=6.0)
                return sent, message

        sent, received = asyncio.run(send_and_receive())
        self.assertEqual(sent[0], {"hello": "world"})
        self.assertEqual(json.loads(received), {"hello": "world"})

        loader = ws_nodes.VrchJsonWebSocketChannelLoaderNode()
        # Prime loader to create its internal websocket client first.
        loader.receive_json(
            channel="1",
            server=f"{self.host}:{port}",
            debug=False,
            default_json_string='{}',
        )
        connected_loader = self._wait_for(
            lambda: len(server.clients.get("/json", {}).get(1, [])) >= 1,
            timeout=3.0,
        )
        self.assertTrue(connected_loader, "Loader websocket client did not connect in time")

        server.send_to_channel("/json", 1, json.dumps({"state": 123}))

        loaded = self._wait_for(
            lambda: loader.receive_json(
                channel="1",
                server=f"{self.host}:{port}",
                debug=False,
                default_json_string='{}',
            )[0],
            timeout=3.0,
        )

        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("state"), 123)


def run_all_tests():
    print("🧪 WebSocket Nodes Test Suite")
    print("=" * 60)

    loader = unittest.TestLoader()
    unit_suite = loader.loadTestsFromTestCase(TestWebSocketNodesUnit)
    integration_suite = loader.loadTestsFromTestCase(TestWebSocketNodesIntegration)
    combined = unittest.TestSuite([unit_suite, integration_suite])

    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(combined)
    return result.wasSuccessful()


if __name__ == "__main__":
    ok = run_all_tests()
    if ok:
        print("\n🎉 All websocket_nodes tests passed!")
    else:
        print("\n❌ websocket_nodes tests failed!")
    sys.exit(0 if ok else 1)
