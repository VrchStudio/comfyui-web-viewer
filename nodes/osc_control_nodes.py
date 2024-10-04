from pythonosc import dispatcher, osc_server
import threading
import socket

# Define the category for organizational purposes
CATEGORY = "vrch.io/control/osc"

class VrchNodeUtils:
    
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
        
    @staticmethod
    def remap(value, out_min, out_max):
        return out_min + (value * (out_max - out_min))

class VrchOSCServerManager:
    _instances = {}

    def __init__(self, ip, port, debug=False):
        self.ip = ip
        self.port = port
        self.debug = debug
        self.dispatcher = dispatcher.Dispatcher()
        self.server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        if debug:
            print(f"OSC server is running at {ip}:{port}")
        self.nodes = []

    @classmethod
    def get_instance(cls, ip, port, debug=False):
        key = (ip, port)
        if key not in cls._instances:
            cls._instances[key] = cls(ip, port, debug)
        return cls._instances[key]

    def register_handler(self, path, handler):
        if self.debug:
            print(f"Registering handler for path: {path}")
        self.dispatcher.map(path, handler)
        self.nodes.append((path, handler))

    def unregister_handler(self, path, handler):
        if self.debug:
            print(f"Unregistering handler for path: {path}")
        self.dispatcher.unmap(path, handler)
        self.nodes.remove((path, handler))

    def shutdown(self):
        if self.debug:
            print("Shutting down OSC server...")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()


class VrchXYOSCControlNode:

    def __init__(self):
        self.x, self.y = 0.0, 0.0
        self.server_manager = None
        self.path = None
        self.debug = False

        # Store server parameters
        self.server_ip = None
        self.port = None
        self.path = None
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
                "port": ("INT", {"default": 8000}),
                "path": ("STRING", {"default": "/xy"}),
                "x_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "x_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "y_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "y_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "debug": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ("INT", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("X", "Y", "X_RAW", "Y_RAW")
    FUNCTION = "load_xy_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_xy_osc(self, server_ip, port, path, x_output_min, x_output_max, y_output_min, y_output_max, debug):

        if x_output_min > x_output_max or y_output_min > y_output_max:
            raise ValueError("Output min value cannot be greater than max value.")

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None or
            self.server_manager.ip != server_ip or
            self.server_manager.port != port or
            self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(f"{self.path}/*", self.handle_osc_message)
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(f"{self.path}/*", self.handle_osc_message)
            if debug:
                print(f"Registered XY handler at path {self.path}/*")

        x_mapped = int(VrchNodeUtils.remap(float(self.x), float(x_output_min), float(x_output_max)))
        y_mapped = int(VrchNodeUtils.remap(float(self.y), float(y_output_min), float(y_output_max)))
        return x_mapped, y_mapped, self.x, self.y

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0.0
        if self.debug:
            print(f"[XY Node] Received OSC message: addr={address}, value={value}")
        if address.endswith("/x"):
            self.x = value
        elif address.endswith("/y"):
            self.y = value

class VrchXYZOSCControlNode:

    def __init__(self):
        self.x, self.y, self.z = 0.0, 0.0, 0.0
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
                "port": ("INT", {"default": 8000, "max": 65535, "min": 0}),
                "path": ("STRING", {"default": "/xyz"}),
                "x_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "x_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "y_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "y_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "z_output_min": ("INT", {"default": 0, "max": 9999, "min": -9999}),
                "z_output_max": ("INT", {"default": 100, "max": 9999, "min": -9999}),
                "debug": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("X", "Y", "Z", "X_RAW", "Y_RAW", "Z_RAW")
    FUNCTION = "load_xyz_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_xyz_osc(self, server_ip, port, path, x_output_min, x_output_max, y_output_min, y_output_max, z_output_min, z_output_max, debug):

        if x_output_min > x_output_max or y_output_min > y_output_max or z_output_min > z_output_max:
            raise ValueError("Output min value cannot be greater than max value.")

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None or
            self.server_manager.ip != server_ip or
            self.server_manager.port != port or
            self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(f"{self.path}/*", self.handle_osc_message)
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(f"{self.path}/*", self.handle_osc_message)
            if debug:
                print(f"Registered XYZ handler at path {self.path}/*")

        x_mapped = int(VrchNodeUtils.remap(float(self.x), float(x_output_min), float(x_output_max)))
        y_mapped = int(VrchNodeUtils.remap(float(self.y), float(y_output_min), float(y_output_max)))
        z_mapped = int(VrchNodeUtils.remap(float(self.z), float(z_output_min), float(z_output_max)))
        return x_mapped, y_mapped, z_mapped, self.x, self.y, self.z

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0.0
        if self.debug:
            print(f"[XYZ Node] Received OSC message: addr={address}, value={value}")
        if address.endswith("/x"):
            self.x = value
        elif address.endswith("/y"):
            self.y = value
        elif address.endswith("/z"):
            self.z = value
