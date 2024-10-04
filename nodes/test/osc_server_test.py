import argparse
from pythonosc import dispatcher, osc_server
import threading

def handle_osc_message(address, args, value):
    debug = args[0].get("debug", False) if isinstance(args[0], dict) else False
    if debug:
        print(f"Received OSC message: addr={address}, value={value}")
    print(f"{address}: {value}")

def setup_osc_server(ip, port, path, debug=False):
    dispatcher_instance = dispatcher.Dispatcher()
    dispatcher_instance.map(f"{path}", handle_osc_message, {"debug": debug})

    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher_instance)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    print(f"OSC server is running at {ip}:{port} and listening on path {path}")
    return server, server_thread

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSC Server Test Script (Press CTRL+C to exit)")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--path", type=str, required=True, help="OSC path to listen to (required)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    server, server_thread = setup_osc_server(args.ip, args.port, args.path, args.debug)

    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        print("\nShutting down OSC server...")
        server.shutdown()
        server.server_close()
        server_thread.join()
        print("OSC server shut down.")