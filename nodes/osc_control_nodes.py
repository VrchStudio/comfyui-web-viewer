from pythonosc import dispatcher, osc_server
import threading

class VrchXYOSCControlNode:
    def __init__(self):
        self.x, self.y = 0.0, 0.0
        self.server_thread = None
        self.server = None
        self.dispatcher = None
        self.initialized = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ip_address": ("STRING", {"multiline": False, "default": "127.0.0.1"}),
                "port": ("INT", {"default": 8000}),
                "path": ("STRING", {"default": "/xy"}),
                "x_output_min": ("INT", {"default": 0}),
                "x_output_max": ("INT", {"default": 100}),
                "y_output_min": ("INT", {"default": 0}),
                "y_output_max": ("INT", {"default": 100}),
                "debug": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("X", "Y")
    FUNCTION = "load_xy_osc"
    CATEGORY = "vrch.io/control"

    def load_xy_osc(self, ip_address, port, path, x_output_min, x_output_max, y_output_min, y_output_max, debug):
        self.shut_down_existing()
        if debug:
            print("Loading OSC server with", ip_address, port, path)
        
        if not self.initialized or not self.server_thread.is_alive():
            self.setup_osc_server(ip_address, port, path, debug)

        x_mapped = self.remap(self.x, -1.0, 1.0, x_output_min, x_output_max)
        y_mapped = self.remap(self.y, -1.0, 1.0, y_output_min, y_output_max)

        if debug:
            print("Current XY data:", "X", self.x, "Y", self.y)
            print("Remapped XY data:", "X", round(x_mapped), "Y", round(y_mapped))

        return int(x_mapped), int(y_mapped)

    def handle_osc_message(self, unused_addr, args, x, y):
        if args['debug']:
            print(f"Received OSC message: addr={unused_addr}, x={x}, y={y}")
        self.x, self.y = x, y

    def setup_osc_server(self, ip, port, path, debug):
        if self.server_thread and self.server_thread.is_alive():
            self.server.shutdown()
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map(path, self.handle_osc_message, {"debug": debug})
        self.server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.initialized = True
        if debug:
            print(f"OSC server is running at {ip}:{port} and listening on path {path}")

    def remap(self, value, in_min, in_max, out_min, out_max):
        if (in_max - in_min) == 0:
            return out_min
        return out_min + ((value - in_min) / (in_max - in_min)) * (out_max - out_min)

    def shut_down_existing(self):
        if self.server:
            print("Shutting down existing OSC server...")
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join()
            self.server_thread = None
        self.server = None
        self.initialized = False