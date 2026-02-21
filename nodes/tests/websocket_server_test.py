#!/usr/bin/env python3
"""
WebSocket Server Tests

Combined unit tests and integration tests for the SimpleWebSocketServer class.
Includes both safe tests (no real servers) and integration tests (real WebSocket connections).
"""

import asyncio
import struct
import sys
import time
import unittest
import websockets
from pathlib import Path

# Add parent directory to path to import websocket_server
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.websocket_server import SimpleWebSocketServer, get_global_server, _port_servers, _server_lock
    print("✓ Successfully imported websocket_server module")
except ImportError as e:
    print(f"✗ Failed to import websocket_server module: {e}")
    sys.exit(1)


class TestWebSocketServerUnit(unittest.TestCase):
    """Unit tests for WebSocket server functionality (safe, no real servers)"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_host = "127.0.0.1"
        self.base_port = 8970
        
        # Clean up any existing global servers
        with _server_lock:
            _port_servers.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        with _server_lock:
            for server in _port_servers.values():
                try:
                    if hasattr(server, 'stop') and server.is_running():
                        server.stop()
                except Exception:
                    pass
            _port_servers.clear()
    
    def test_01_module_imports(self):
        """Test that all required modules and functions can be imported"""
        self.assertIsNotNone(SimpleWebSocketServer)
        self.assertIsNotNone(get_global_server)
        self.assertIsNotNone(_port_servers)
        self.assertIsNotNone(_server_lock)
        print("✓ Module imports test passed")
    
    def test_02_server_class_structure(self):
        """Test server class can be instantiated and has correct structure"""
        port = self.base_port + 1
        server = SimpleWebSocketServer.__new__(SimpleWebSocketServer)
        
        # Initialize attributes manually to avoid starting real server
        server.host = self.test_host
        server.port = port
        server.debug = False
        server.paths = set()
        server.clients = {}
        server._is_running = False
        server.server = None
        server.loop = None
        server.thread = None
        
        # Test attributes
        self.assertEqual(server.host, self.test_host)
        self.assertEqual(server.port, port)
        self.assertFalse(server.debug)
        self.assertIsInstance(server.paths, set)
        self.assertIsInstance(server.clients, dict)
        print("✓ Server class structure test passed")
    
    def test_03_path_registration(self):
        """Test path registration and channel initialization"""
        server = SimpleWebSocketServer.__new__(SimpleWebSocketServer)
        server.host = self.test_host
        server.port = self.base_port + 2
        server.debug = False
        server.paths = set()
        server.clients = {}
        
        # Test single path registration
        test_path = "/test"
        SimpleWebSocketServer.register_path(server, test_path)
        
        self.assertIn(test_path, server.paths)
        self.assertIn(test_path, server.clients)
        
        # Verify channels 1-8 are initialized
        channels = server.clients[test_path]
        self.assertEqual(len(channels), 8)
        for i in range(1, 9):
            self.assertIn(i, channels)
            self.assertIsInstance(channels[i], list)
        
        # Test multiple paths
        additional_paths = ["/image", "/json", "/audio"]
        for path in additional_paths:
            SimpleWebSocketServer.register_path(server, path)
        
        for path in additional_paths:
            self.assertIn(path, server.paths)
            self.assertIn(path, server.clients)
            self.assertEqual(len(server.clients[path]), 8)
        
        print("✓ Path registration test passed")
    
    def test_04_send_to_channel_safety(self):
        """Test send_to_channel method handles empty clients gracefully"""
        server = SimpleWebSocketServer.__new__(SimpleWebSocketServer)
        server.host = self.test_host
        server.port = self.base_port + 3
        server.debug = False
        server.paths = set()
        server.clients = {}
        
        SimpleWebSocketServer.register_path(server, "/test")
        
        # Test sending to empty channels doesn't crash
        try:
            SimpleWebSocketServer.send_to_channel(server, "/test", 1, "test message")
            SimpleWebSocketServer.send_to_channel(server, "/test", 2, b"binary data")
            SimpleWebSocketServer.send_to_channel(server, "/nonexistent", 1, "test")
        except Exception as e:
            self.fail(f"send_to_channel raised an exception: {e}")
        
        print("✓ Send to channel safety test passed")
    
    def test_05_global_server_management(self):
        """Test global server registry and get_global_server function"""
        # Test registry is initially empty
        with _server_lock:
            self.assertEqual(len(_port_servers), 0)
        
        # Test function signature
        self.assertTrue(callable(get_global_server))
        import inspect
        sig = inspect.signature(get_global_server)
        params = list(sig.parameters.keys())
        
        expected_params = ['host', 'port', 'path']
        for param in expected_params:
            self.assertIn(param, params)
        
        print("✓ Global server management test passed")
    
    def test_06_server_methods_exist(self):
        """Test that all required methods exist and are callable"""
        required_methods = ['register_path', 'send_to_channel', 'is_running', 'start', 'stop']
        
        for method_name in required_methods:
            self.assertTrue(hasattr(SimpleWebSocketServer, method_name))
            self.assertTrue(callable(getattr(SimpleWebSocketServer, method_name)))
        
        print("✓ Server methods existence test passed")

    def test_07_realtime_slow_client_drop_frame_without_disconnect(self):
        """Realtime path should drop frames for busy client without removing connection"""

        class SlowClient:
            def __init__(self):
                self.closed = False

            async def send(self, _data):
                await asyncio.sleep(0.25)

        class FailingClient:
            def __init__(self):
                self.closed = False

            async def send(self, _data):
                raise RuntimeError("send failed")

        async def run_case():
            server = SimpleWebSocketServer.__new__(SimpleWebSocketServer)
            server.host = self.test_host
            server.port = self.base_port + 9
            server.debug = False
            server.paths = {"/image"}
            server.clients = {"/image": {i: [] for i in range(1, 9)}}
            server._is_running = True
            server._connection_tasks = set()
            server._realtime_pending = {}
            server._realtime_send_tasks = {}

            slow_client = SlowClient()
            failing_client = FailingClient()
            server.clients["/image"][1] = [slow_client, failing_client]

            await server._broadcast_channel("/image", 1, b"frame-1")
            await server._broadcast_channel("/image", 1, b"frame-2")
            await asyncio.sleep(0.05)

            # Slow client should remain connected while busy (frame dropped for it).
            self.assertIn(slow_client, server.clients["/image"][1])
            # Failing client should be removed.
            self.assertNotIn(failing_client, server.clients["/image"][1])

            await asyncio.sleep(0.30)
            await server._broadcast_channel("/image", 1, b"frame-3")
            await asyncio.sleep(0.05)
            self.assertIn(slow_client, server.clients["/image"][1])

        asyncio.run(run_case())
        print("✓ Realtime slow client handling test passed")

    def test_08_image_payload_realtime_detection(self):
        """Only single-frame image payload should use realtime drop policy."""
        server = SimpleWebSocketServer.__new__(SimpleWebSocketServer)

        # frame_total = 1 => realtime path enabled
        meta_single = (0 << 16) | (0 << 8) | 1
        single = struct.pack(">II", 1, meta_single) + b"x" * 32
        self.assertTrue(server._is_realtime_payload("/image", single))

        # frame_total = 4 => must be reliable (no frame dropping)
        meta_multi = (0 << 16) | (0 << 8) | 4
        multi = struct.pack(">II", 1, meta_multi) + b"x" * 32
        self.assertFalse(server._is_realtime_payload("/image", multi))

        # /image text settings should also be reliable
        self.assertFalse(server._is_realtime_payload("/image", '{"settings":true}'))

        # /video still uses realtime behavior
        self.assertTrue(server._is_realtime_payload("/video", b"12345678"))
        print("✓ Image payload realtime detection test passed")


class TestWebSocketServerIntegration(unittest.TestCase):
    """Integration tests with real WebSocket servers and connections"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_host = "127.0.0.1"
        self.base_port = 9100  # Different port range from unit tests
        self.servers = []
        self.clients = []
        
        with _server_lock:
            _port_servers.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        # Close all clients
        for client in self.clients:
            try:
                if hasattr(client, 'close'):
                    asyncio.run(self._close_client(client))
            except Exception:
                pass
        
        # Stop all servers
        for server in self.servers:
            try:
                if hasattr(server, '_is_running'):
                    server._is_running = False
                if hasattr(server, 'server') and server.server:
                    server.server.close()
            except Exception:
                pass
        
        with _server_lock:
            _port_servers.clear()
        
        time.sleep(0.2)  # Allow cleanup
    
    async def _close_client(self, client):
        """Safely close a WebSocket client"""
        try:
            await client.close()
        except Exception:
            pass
    
    def test_07_server_lifecycle(self):
        """Test real server startup and shutdown"""
        port = self.base_port + 1
        server = SimpleWebSocketServer(self.test_host, port, debug=False)
        self.servers.append(server)
        
        # Wait for server to start
        time.sleep(1.5)
        
        # Test server is running
        self.assertTrue(server.is_running())
        
        # Test server can stop
        server.stop()
        time.sleep(1)
        
        # Test server is stopped
        self.assertFalse(server.is_running())
        print("✓ Server lifecycle test passed")
    
    def test_08_client_connection(self):
        """Test real client connections and disconnections"""
        port = self.base_port + 2
        server = SimpleWebSocketServer(self.test_host, port, debug=True)  # Enable debug for this test
        self.servers.append(server)
        server.register_path("/test")
        
        time.sleep(2.0)  # Give more time for server to start
        
        async def test_connection():
            uri = f"ws://{self.test_host}:{port}/test?channel=1"
            client = None
            try:
                client = await websockets.connect(uri)
                self.clients.append(client)
                
                # Give more time for connection to be registered
                await asyncio.sleep(1.0)
                
                # Check client is tracked
                tracked_clients = server.clients.get("/test", {}).get(1, [])
                print(f"DEBUG: Found {len(tracked_clients)} tracked clients")
                self.assertGreater(len(tracked_clients), 0, "Client should be tracked after connection")
                
                # Send a simple ping to keep connection alive
                await client.ping()
                await asyncio.sleep(0.2)
                
                await client.close()
                await asyncio.sleep(0.5)  # Give time for cleanup
                
                # Check client is removed
                tracked_clients = server.clients.get("/test", {}).get(1, [])
                self.assertEqual(len(tracked_clients), 0, "Client should be removed after disconnection")
                
                return True
            except Exception as e:
                if client:
                    try:
                        await client.close()
                    except:
                        pass
                self.fail(f"Connection test failed: {e}")
                return False
        
        result = asyncio.run(test_connection())
        self.assertTrue(result)
        print("✓ Client connection test passed")
    
    def test_09_message_broadcasting(self):
        """Test message broadcasting to multiple clients"""
        port = self.base_port + 3
        server = SimpleWebSocketServer(self.test_host, port, debug=True)  # Enable debug
        self.servers.append(server)
        server.register_path("/broadcast")
        
        time.sleep(2.0)  # Give more time for server to start
        
        async def test_broadcast():
            clients = []
            messages_received = []
            
            try:
                # Connect 2 clients to same channel
                for i in range(2):
                    uri = f"ws://{self.test_host}:{port}/broadcast?channel=1"
                    client = await websockets.connect(uri)
                    clients.append(client)
                    self.clients.append(client)
                
                # Give more time for connections to be established
                await asyncio.sleep(1.0)
                
                # Verify clients are tracked
                tracked_clients = server.clients.get("/broadcast", {}).get(1, [])
                print(f"DEBUG: Found {len(tracked_clients)} tracked clients after connection")
                
                # Set up message listeners
                async def listen_for_message(client, client_id):
                    try:
                        # Send a ping first to ensure connection is alive
                        await client.ping()
                        message = await asyncio.wait_for(client.recv(), timeout=3.0)
                        messages_received.append((client_id, message))
                        print(f"DEBUG: Client {client_id} received: {message}")
                    except asyncio.TimeoutError:
                        print(f"DEBUG: Client {client_id} timeout - no message received")
                        pass
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"DEBUG: Client {client_id} connection closed: {e}")
                        pass
                
                listeners = [
                    asyncio.create_task(listen_for_message(client, i))
                    for i, client in enumerate(clients)
                ]
                
                # Give a moment for listeners to be set up
                await asyncio.sleep(0.2)
                
                # Send message
                test_message = "Hello from test!"
                print(f"DEBUG: Sending message to /broadcast channel 1")
                server.send_to_channel("/broadcast", 1, test_message)
                
                # Give more time for messages to be received
                await asyncio.sleep(1.0)
                
                # Wait for all listeners to complete
                await asyncio.gather(*listeners, return_exceptions=True)
                
                # Check messages received
                print(f"DEBUG: Total messages received: {len(messages_received)}")
                self.assertGreater(len(messages_received), 0, "At least one client should receive the message")
                for client_id, message in messages_received:
                    self.assertEqual(message, test_message, f"Client {client_id} should receive correct message")
                
                # Cleanup
                for client in clients:
                    await client.close()
                
                return True
                
            except Exception as e:
                # Cleanup on error
                for client in clients:
                    try:
                        await client.close()
                    except:
                        pass
                self.fail(f"Broadcast test failed: {e}")
                return False
        
        result = asyncio.run(test_broadcast())
        self.assertTrue(result)
        print("✓ Message broadcasting test passed")
    
    def test_10_channel_isolation(self):
        """Test that different channels work independently"""
        port = self.base_port + 4
        server = SimpleWebSocketServer(self.test_host, port, debug=True)  # Enable debug
        self.servers.append(server)
        server.register_path("/channels")
        
        time.sleep(2.0)  # Give more time for server to start
        
        async def test_channels():
            client1 = None
            client2 = None
            try:
                client1_uri = f"ws://{self.test_host}:{port}/channels?channel=1"
                client2_uri = f"ws://{self.test_host}:{port}/channels?channel=2"
                
                client1 = await websockets.connect(client1_uri)
                client2 = await websockets.connect(client2_uri)
                self.clients.extend([client1, client2])
                
                # Give more time for connections and send pings to keep alive
                await asyncio.sleep(1.0)
                await client1.ping()
                await client2.ping()
                await asyncio.sleep(0.2)
                
                # Verify clients are tracked
                tracked_clients_1 = server.clients.get("/channels", {}).get(1, [])
                tracked_clients_2 = server.clients.get("/channels", {}).get(2, [])
                print(f"DEBUG: Channel 1 has {len(tracked_clients_1)} clients, Channel 2 has {len(tracked_clients_2)} clients")
                
                # Send to channel 1 only
                print("DEBUG: Sending message to channel 1")
                server.send_to_channel("/channels", 1, "Message for channel 1")
                
                # Give time for message to be delivered
                await asyncio.sleep(0.5)
                
                # Client1 should receive, client2 should not
                try:
                    message1 = await asyncio.wait_for(client1.recv(), timeout=2.0)
                    self.assertEqual(message1, "Message for channel 1", "Client1 should receive the message")
                    print("DEBUG: Client1 received expected message")
                except asyncio.TimeoutError:
                    self.fail("Client1 did not receive message within timeout")
                except websockets.exceptions.ConnectionClosed as e:
                    self.fail(f"Client1 connection closed unexpectedly: {e}")
                
                # Client2 should NOT receive the message
                try:
                    message2 = await asyncio.wait_for(client2.recv(), timeout=1.0)
                    self.fail(f"Client2 should not have received a message, but got: {message2}")
                except asyncio.TimeoutError:
                    print("DEBUG: Client2 correctly did not receive message (timeout)")
                    pass  # Expected - client2 should not receive the message
                except websockets.exceptions.ConnectionClosed:
                    print("DEBUG: Client2 connection closed - this is acceptable")
                    pass  # Also acceptable
                
                await client1.close()
                await client2.close()
                
                return True
                
            except Exception as e:
                # Cleanup on error
                if client1:
                    try:
                        await client1.close()
                    except:
                        pass
                if client2:
                    try:
                        await client2.close()
                    except:
                        pass
                self.fail(f"Channel isolation test failed: {e}")
                return False
        
        result = asyncio.run(test_channels())
        self.assertTrue(result)
        print("✓ Channel isolation test passed")
    
    def test_11_global_server_functionality(self):
        """Test get_global_server with real server instances"""
        port = self.base_port + 5
        
        # Create first server
        server1 = get_global_server(self.test_host, port, "/path1", debug=False)
        self.servers.append(server1)
        
        time.sleep(1.5)
        
        self.assertTrue(server1.is_running())
        
        # Create second server with same host:port
        server2 = get_global_server(self.test_host, port, "/path2", debug=False)
        
        # Should be same instance
        self.assertIs(server1, server2)
        
        # Both paths should be registered
        self.assertIn("/path1", server1.paths)
        self.assertIn("/path2", server1.paths)
        
        print("✓ Global server functionality test passed")
    
    def test_12_port_sharing_across_processes(self):
        """Test port sharing scenario where another process tries to use same port"""
        port = self.base_port + 6
        
        # First process creates a server
        server1 = SimpleWebSocketServer(self.test_host, port, debug=True)
        self.servers.append(server1)
        server1.register_path("/shared")
        
        time.sleep(2.0)  # Wait for server to start
        self.assertTrue(server1.is_running())
        
        # Simulate second process trying to use same port
        # This should detect existing server and create client proxy
        shared_server = get_global_server(self.test_host, port, "/shared", debug=True)
        
        # Should be able to send data through shared connection
        async def test_shared_communication():
            # Set up a client to receive messages
            uri = f"ws://{self.test_host}:{port}/shared?channel=1"
            client = await websockets.connect(uri)
            self.clients.append(client)
            
            # Give time for connection
            await asyncio.sleep(0.5)
            
            # Send message through shared server interface
            shared_server.send_to_channel("/shared", 1, "shared message")
            
            # Receive message
            message = await asyncio.wait_for(client.recv(), timeout=3.0)
            self.assertEqual(message, "shared message")
            
            await client.close()
        
        # Test the shared communication
        asyncio.run(test_shared_communication())
        
        print("✓ Port sharing across processes test passed")

    def test_13_send_call_latency_under_load(self):
        """Test send_to_channel call latency under moderate concurrent load"""
        port = self.base_port + 7
        server = SimpleWebSocketServer(self.test_host, port, debug=False)
        self.servers.append(server)
        server.register_path("/perf")

        time.sleep(1.5)

        async def run_perf_case():
            clients = []
            call_latencies = []
            message_count = 20
            client_count = 10

            try:
                uri = f"ws://{self.test_host}:{port}/perf?channel=1"
                for _ in range(client_count):
                    client = await websockets.connect(uri)
                    clients.append(client)
                    self.clients.append(client)

                await asyncio.sleep(0.5)

                for idx in range(message_count):
                    payload = f"perf-{idx}"
                    recv_tasks = [
                        asyncio.create_task(asyncio.wait_for(client.recv(), timeout=3.0))
                        for client in clients
                    ]

                    t0 = time.perf_counter()
                    server.send_to_channel("/perf", 1, payload)
                    t1 = time.perf_counter()
                    call_latencies.append((t1 - t0) * 1000.0)

                    recv_results = await asyncio.gather(*recv_tasks, return_exceptions=True)
                    for received in recv_results:
                        if isinstance(received, Exception):
                            self.fail(f"Expected payload '{payload}', but receive failed: {received}")
                        self.assertEqual(received, payload)

                sorted_lat = sorted(call_latencies)
                p95_index = max(0, int(len(sorted_lat) * 0.95) - 1)
                p95_ms = sorted_lat[p95_index]

                # Keep threshold conservative to reduce test flakiness.
                self.assertLess(p95_ms, 10.0, f"send_to_channel p95 too high: {p95_ms:.3f} ms")
            finally:
                for client in clients:
                    try:
                        await client.close()
                    except Exception:
                        pass

        asyncio.run(run_perf_case())
        print("✓ Send call latency under load test passed")


def run_all_tests():
    """Run both unit tests and integration tests"""
    print("🧪 WebSocket Server Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suites
    unit_loader = unittest.TestLoader()
    integration_loader = unittest.TestLoader()
    
    unit_suite = unit_loader.loadTestsFromTestCase(TestWebSocketServerUnit)
    integration_suite = integration_loader.loadTestsFromTestCase(TestWebSocketServerIntegration)
    
    # Combine suites
    combined_suite = unittest.TestSuite([unit_suite, integration_suite])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(combined_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        print("✅ WebSocket server is working correctly with both unit and integration tests.")
    else:
        print("\n❌ Some tests failed!")
        
    sys.exit(0 if success else 1)
