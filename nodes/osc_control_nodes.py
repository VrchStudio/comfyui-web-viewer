from pythonosc import dispatcher, osc_server
import threading
import socket

class VrchXYOSCControlNode:

    @staticmethod
    def get_default_ip_address():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

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
                "ip": ("STRING", {"multiline": False, "default": VrchXYOSCControlNode.get_default_ip_address()}),
                "port": ("INT", {"default": 8000}),
                "path": ("STRING", {"default": "/xy"}),
                "x_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "x_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "y_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "y_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "debug": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("X", "Y")
    FUNCTION = "load_xy_osc"
    CATEGORY = "vrch.io/control"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def remap(self, value, out_min, out_max):
        return out_min + (value * (out_max - out_min))

    def load_xy_osc(self, ip, port, path, x_output_min, x_output_max, y_output_min, y_output_max, debug):
        
        if x_output_min > x_output_max or y_output_min > y_output_max:
            raise ValueError("Output min value cannot be greater than max value.")
        
        self.shut_down_existing()
        if debug:
            print(f"Loading OSC server with IP: {ip}, Port: {port}, Path: {path + '/*'}")

        if not self.initialized or not self.server_thread.is_alive():
            self.setup_osc_server(ip, port, path + '/*', debug)

        x_mapped = int(self.remap(float(self.x), float(x_output_min), float(x_output_max)))
        y_mapped = int(self.remap(float(self.y), float(y_output_min), float(y_output_max)))
        return x_mapped, y_mapped

    def handle_osc_message(self, address, args, value):
        debug = args[0].get("debug", False) if isinstance(args[0], dict) else False
        if debug:
            print(f"Received OSC message: addr={address}, value={value}")
        if address.endswith("/x"):
            self.x = value
        elif address.endswith("/y"):
            self.y = value

    def setup_osc_server(self, ip, port, path, debug):
        if self.server_thread and self.server_thread.is_alive():
            self.server.shutdown()
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map(f"{path}", self.handle_osc_message, {"debug": debug})

        self.server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.initialized = True
        if debug:
            print(f"OSC server is running at {ip}:{port} and listening on path {path}")

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