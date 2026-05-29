#!/usr/bin/env python3
"""Tests for websocket_nodes.py.

This suite validates helper handlers and node/client integration behavior.
"""

import asyncio
import base64
import io
import json
import socket
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import torch
import websockets
from PIL import Image

# Import package as module to keep relative imports in websocket_nodes working.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from nodes import websocket_nodes as ws_nodes  # noqa: E402
from nodes.midi_websocket_protocol import encode_definition_frame, encode_state_frame  # noqa: E402
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
        self.assertIsNone(ws_nodes.audio_data_handler(json.dumps({
            "type": "vrch_audio_player_track",
            "target": "audio_player_playlist",
            "audio": {"base64": "abc", "mime_type": "audio/webm"},
        })))

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

    def test_05_midi_state_handler(self):
        handler = ws_nodes.make_midi_state_handler(debug=False)
        state = handler(encode_definition_frame([{"key": "brightness", "number": 22}], definition_seq=1, seq=1))
        self.assertTrue(state["definition_ready"])
        self.assertIn("brightness", state["index_by_key"])

        state = handler(
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 96}],
                control_values=[{"control_index": 0, "value": 96}],
                definition_seq=1,
                seq=2,
            )
        )
        self.assertEqual(state["values_by_index"][0], 96)
        self.assertEqual(state["cc_values"]["1"][22], 96)

    def test_06_default_websocket_paths_include_midi(self):
        self.assertIn("/midi", ws_nodes.DEFAULT_WEBSOCKET_PATHS)

    def test_07_audio_sender_quality_presets(self):
        self.assertEqual(ws_nodes._normalize_audio_quality("compact"), ("compact", 64))
        self.assertEqual(ws_nodes._normalize_audio_quality("standard"), ("standard", 128))
        self.assertEqual(ws_nodes._normalize_audio_quality("high"), ("high", 192))
        self.assertEqual(ws_nodes._normalize_audio_quality("unknown"), ("standard", 128))

    def test_08_audio_sender_payload_shape(self):
        audio = {
            "waveform": torch.zeros(1, 1, 2205),
            "sample_rate": 44100,
        }
        try:
            payload = ws_nodes._build_audio_player_track_payload(
                audio=audio,
                title="Test Clip",
                quality="compact",
                autoplay_request=True,
            )
        except ValueError as err:
            self.skipTest(f"ffmpeg WebM/Opus unavailable: {err}")

        self.assertEqual(payload["type"], "vrch_audio_player_track")
        self.assertEqual(payload["target"], "audio_player_playlist")
        self.assertEqual(payload["source"], "comfyui_audio_sender")
        self.assertNotIn("base64_data", payload)
        self.assertEqual(payload["audio"]["mime_type"], "audio/webm")
        self.assertEqual(payload["audio"]["encoding"], "webm-opus")
        self.assertTrue(payload["audio"]["base64"])
        self.assertEqual(payload["audio"]["bitrate_bps"], 64000)
        self.assertEqual(payload["audio"]["sample_rate"], 44100)
        self.assertEqual(payload["audio"]["channels"], 1)
        self.assertEqual(payload["playlist"]["display_name"], "Test Clip")
        self.assertTrue(payload["playlist"]["filename"].endswith(".webm"))
        self.assertTrue(payload["playlist"]["autoplay_request"])

    def test_09_image_loader_prefers_websocket_image_over_default_image(self):
        received_image = torch.ones((1, 2, 2, 3), dtype=torch.float32)

        class FakeClient:
            def get_latest_data(self):
                return received_image

        original_get_client = ws_nodes.get_websocket_client
        self.addCleanup(lambda: setattr(ws_nodes, "get_websocket_client", original_get_client))
        ws_nodes.get_websocket_client = lambda *args, **kwargs: FakeClient()

        node = ws_nodes.VrchImageWebSocketChannelLoaderNode()
        default_image = torch.zeros((1, 2, 2, 3), dtype=torch.float32)

        image, is_default = node.receive_image("1", "127.0.0.1:8001", "image", False, default_image)

        self.assertIs(image, received_image)
        self.assertFalse(is_default)

    def test_10_image_loader_keeps_cached_websocket_image_for_ignored_messages(self):
        received_image = torch.ones((1, 2, 2, 3), dtype=torch.float32)

        class FakeClient:
            def __init__(self):
                self.values = [received_image, None]

            def get_latest_data(self):
                return self.values.pop(0) if self.values else None

        fake_client = FakeClient()
        original_get_client = ws_nodes.get_websocket_client
        self.addCleanup(lambda: setattr(ws_nodes, "get_websocket_client", original_get_client))
        ws_nodes.get_websocket_client = lambda *args, **kwargs: fake_client

        node = ws_nodes.VrchImageWebSocketChannelLoaderNode()
        default_image = torch.zeros((1, 2, 2, 3), dtype=torch.float32)

        first_image, first_is_default = node.receive_image("1", "127.0.0.1:8001", "image", False, default_image)
        second_image, second_is_default = node.receive_image("1", "127.0.0.1:8001", "image", False, default_image)

        self.assertIs(first_image, received_image)
        self.assertFalse(first_is_default)
        self.assertIs(second_image, received_image)
        self.assertFalse(second_is_default)


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

    def test_07_client_cache_reuse_and_refresh(self):
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

    def test_08_json_sender_and_loader_integration(self):
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

    def test_09_midi_loader_integration(self):
        port = self._find_free_port()
        server = get_global_server(self.host, port, path="/midi", debug=False)
        running = self._wait_for(lambda: server.is_running(), timeout=3.0)
        self.assertTrue(running, "Managed WebSocket server did not start in time")

        loader = ws_nodes.VrchMidiWebSocketChannelLoaderNode()
        empty = loader.receive_midi(channel="1", server=f"{self.host}:{port}", debug=False)[0]
        self.assertFalse(empty["definition_ready"])

        connected_loader = self._wait_for(
            lambda: len(server.clients.get("/midi", {}).get(1, [])) >= 1,
            timeout=3.0,
        )
        self.assertTrue(connected_loader, "MIDI loader websocket client did not connect in time")

        server.send_to_channel(
            "/midi",
            1,
            encode_definition_frame([{"key": "brightness", "label": "Brightness", "number": 22}], definition_seq=1, seq=1),
        )
        server.send_to_channel(
            "/midi",
            1,
            encode_state_frame(
                raw_cc=[{"midi_channel": 0, "number": 22, "value": 96}],
                control_values=[{"control_index": 0, "value": 96}],
                definition_seq=1,
                seq=2,
            ),
        )

        def receive_ready_midi():
            data = loader.receive_midi(channel="1", server=f"{self.host}:{port}", debug=False)[0]
            if data.get("definition_ready") and data.get("values_by_index", {}).get(0) == 96:
                return data
            return None

        loaded = self._wait_for(receive_ready_midi, timeout=3.0)

        self.assertTrue(loaded["definition_ready"])
        self.assertEqual(loaded["index_by_key"]["brightness"], 0)
        self.assertEqual(loaded["values_by_index"][0], 96)

    def test_10_audio_sender_integration(self):
        port = self._find_free_port()
        server = get_global_server(self.host, port, path="/audio", debug=False)
        running = self._wait_for(lambda: server.is_running(), timeout=3.0)
        self.assertTrue(running, "Managed WebSocket server did not start in time")

        sender = ws_nodes.VrchAudioWebSocketSenderNode()
        audio = {
            "waveform": torch.zeros(1, 1, 2205),
            "sample_rate": 44100,
        }

        async def send_and_receive():
            uri = f"ws://{self.host}:{port}/audio?channel=1"
            async with websockets.connect(uri) as ws:
                await asyncio.sleep(0.1)
                try:
                    sent_audio, sent_payload = sender.send_audio(
                        audio=audio,
                        channel="1",
                        server=f"{self.host}:{port}",
                        title="WebSocket Test",
                        autoplay_request=False,
                        quality="compact",
                        debug=False,
                    )
                except ValueError as err:
                    return None, None, err
                message = await asyncio.wait_for(ws.recv(), timeout=6.0)
                return sent_audio, sent_payload, message

        sent_audio, sent_payload, received = asyncio.run(send_and_receive())
        if isinstance(received, ValueError):
            self.skipTest(f"ffmpeg WebM/Opus unavailable: {received}")

        self.assertIs(sent_audio, audio)
        self.assertIsInstance(sent_payload, dict)
        self.assertNotIn("base64", sent_payload.get("audio", {}))
        payload = json.loads(received)
        self.assertEqual(payload["type"], "vrch_audio_player_track")
        self.assertEqual(payload["target"], "audio_player_playlist")
        self.assertEqual(payload["audio"]["mime_type"], "audio/webm")
        self.assertTrue(payload["audio"]["base64"])
        self.assertFalse(payload["playlist"]["autoplay_request"])

        with tempfile.TemporaryDirectory(prefix="vrch-audio-sender-test-") as tmpdir:
            webm_path = Path(tmpdir) / "received.webm"
            webm_path.write_bytes(base64.b64decode(payload["audio"]["base64"]))
            try:
                probe = ws_nodes.ffmpeg.probe(str(webm_path))
            except Exception as err:
                self.skipTest(f"ffprobe unavailable for WebM duration check: {err}")
            duration = float((probe.get("format") or {}).get("duration") or 0)
            self.assertGreater(duration, 0, "WebM sender output should include seekable duration metadata")

    def test_11_large_audio_text_payload_is_supported(self):
        port = self._find_free_port()
        server = get_global_server(self.host, port, path="/audio", debug=False)
        running = self._wait_for(lambda: server.is_running(), timeout=3.0)
        self.assertTrue(running, "Managed WebSocket server did not start in time")

        client = ws_nodes.get_websocket_client(
            self.host,
            port,
            "/audio",
            1,
            data_handler=None,
            debug=False,
        )
        connected = self._wait_for(
            lambda: len(server.clients.get("/audio", {}).get(1, [])) >= 1,
            timeout=3.0,
        )
        self.assertTrue(connected, "Large-payload websocket client did not connect in time")

        large_message = "x" * (1024 * 1024 + 4096)
        server.send_to_channel("/audio", 1, large_message)
        received = self._wait_for(lambda: client.get_latest_data(), timeout=3.0)
        self.assertEqual(received, large_message)


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
