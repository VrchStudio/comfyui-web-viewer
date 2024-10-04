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
            print(f"[VrchOSCServerManager] OSC server is running at {ip}:{port}")
        self.nodes = []

    @classmethod
    def get_instance(cls, ip, port, debug=False):
        key = (ip, port)
        if key not in cls._instances:
            cls._instances[key] = cls(ip, port, debug)
        return cls._instances[key]

    def register_handler(self, path, handler, *args):
        if self.debug:
            if len(args) >= 1:
                message = f"path: {path}, args: {args}"
            else:
                message = f"path: {path}"
            print(f"[VrchOSCServerManager] Registering handler for {message}")
        
        if len(args) >= 1:
            self.dispatcher.map(path, handler, args)
        else:
            self.dispatcher.map(path, handler)
        self.nodes.append((path, handler))

    def unregister_handler(self, path, handler):
        if self.debug:
            print(f"[VrchOSCServerManager] Unregistering handler for path: {path}")
        try:
            self.dispatcher.unmap(path, handler)
            self.nodes.remove((path, handler))
        except Exception as e:
            print(f"[VrchOSCServerManager] unregister_handler() call with error: {e}")

    def shutdown(self):
        if self.debug:
            print(f"[VrchOSCServerManager] Shutting down OSC server...")
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
            raise ValueError("[VrchXYOSCControlNode] Output min value cannot be greater than max value.")

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
                print(f"[VrchXYOSCControlNode] Registered XY handler at path {self.path}/*")

        x_mapped = int(VrchNodeUtils.remap(float(self.x), float(x_output_min), float(x_output_max)))
        y_mapped = int(VrchNodeUtils.remap(float(self.y), float(y_output_min), float(y_output_max)))
        return x_mapped, y_mapped, self.x, self.y

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0.0
        if self.debug:
            print(f"[VrchXYOSCControlNode] Received OSC message: addr={address}, value={value}")
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
            raise ValueError("[VrchXYZOSCControlNode] Output min value cannot be greater than max value.")

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
                print(f"[VrchXYZOSCControlNode] Registered XYZ handler at path {self.path}/*")

        x_mapped = int(VrchNodeUtils.remap(float(self.x), float(x_output_min), float(x_output_max)))
        y_mapped = int(VrchNodeUtils.remap(float(self.y), float(y_output_min), float(y_output_max)))
        z_mapped = int(VrchNodeUtils.remap(float(self.z), float(z_output_min), float(z_output_max)))
        return x_mapped, y_mapped, z_mapped, self.x, self.y, self.z

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0.0
        if self.debug:
            print(f"[VrchXYZOSCControlNode] Received OSC message: addr={address}, value={value}")
        if address.endswith("/x"):
            self.x = value
        elif address.endswith("/y"):
            self.y = value
        elif address.endswith("/z"):
            self.z = value

class VrchIntOSCControlNode:

    def __init__(self):
        self.value = 0
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path": ("STRING", {"default": "/path"}),
                "output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
                "output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT")
    RETURN_NAMES = ("VALUE", "RAW_VALUE")
    FUNCTION = "load_int_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_int_osc(
        self, server_ip, port, path, output_min, output_max, debug
    ):

        if output_min > output_max:
            raise ValueError("[VrchIntOSCControlNode] Output min value cannot be greater than max value.")

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if it exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(
                    self.path, self.handle_osc_message
                )
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(
                server_ip, port, debug
            )
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchIntOSCControlNode] Registered Int handler at path {self.path}")

        mapped_value = int(
            VrchNodeUtils.remap(float(self.value), float(output_min), float(output_max))
        )
        return mapped_value, self.value

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0
        if self.debug:
            print(f"[VrchIntOSCControlNode] Received OSC message: addr={address}, value={value}")
        self.value = value


class VrchFloatOSCControlNode:

    def __init__(self):
        self.value = 0.0
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path": ("STRING", {"default": "/path"}),
                "output_min": ("FLOAT", {"default": 0.00, "min": -9999.00, "max": 9999.00, "step": 0.01}),
                "output_max": ("FLOAT", {"default": 100.00, "min": -9999.00, "max": 9999.00, "step": 0.01}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("FLOAT", "FLOAT")
    RETURN_NAMES = ("VALUE", "RAW_VALUE")
    FUNCTION = "load_float_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_float_osc(
        self, server_ip, port, path, output_min, output_max, debug
    ):

        if output_min > output_max:
            raise ValueError("[VrchFloatOSCControlNode] Output min value cannot be greater than max value.")

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if it exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(
                    self.path, self.handle_osc_message
                )
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(
                server_ip, port, debug
            )
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchFloatOSCControlNode] Registered Float handler at path {self.path}")

        mapped_value = VrchNodeUtils.remap(
            float(self.value), float(output_min), float(output_max)
        )
        return mapped_value, float(self.value)

    def handle_osc_message(self, address, *args):
        value = args[0] if args else 0.0
        if self.debug:
            print(f"[VrchFloatOSCControlNode] Received OSC message: addr={address}, value={value}")
        self.value = value

class VrchSwitchOSCControlNode:

    def __init__(self):
        self.switches = [False] * 8
        self.server_manager = None
        self.paths = []
        self.handlers = []
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_ip": (
                    "STRING",
                    {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()},
                ),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path1": ("STRING", {"default": "/toggle1"}),
                "path2": ("STRING", {"default": "/toggle2"}),
                "path3": ("STRING", {"default": "/toggle3"}),
                "path4": ("STRING", {"default": "/toggle4"}),
                "path5": ("STRING", {"default": "/toggle5"}),
                "path6": ("STRING", {"default": "/toggle6"}),
                "path7": ("STRING", {"default": "/toggle7"}),
                "path8": ("STRING", {"default": "/toggle8"}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",) * 8
    RETURN_NAMES = (
        "SWITCH_1",
        "SWITCH_2",
        "SWITCH_3",
        "SWITCH_4",
        "SWITCH_5",
        "SWITCH_6",
        "SWITCH_7",
        "SWITCH_8",
    )
    FUNCTION = "load_switches_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_switches_osc(
        self,
        server_ip,
        port,
        path1,
        path2,
        path3,
        path4,
        path5,
        path6,
        path7,
        path8,
        debug,
    ):
        # Check if server parameters or paths have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.debug != debug
        )
        new_paths = [path1, path2, path3, path4, path5, path6, path7, path8]

        if server_params_changed or self.paths != new_paths:
            # Unregister previous handlers if they exist
            if self.server_manager and self.handlers:
                for path, handler in self.handlers:
                    self.server_manager.unregister_handler(path, handler)
                    if debug:
                        print(f"[VrchSwitchOSCControlNode] Unregistered Switch handler at path {path}")
                self.handlers = []

            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handlers
            self.paths = new_paths
            self.handlers = []
            for i, path in enumerate(self.paths):
                handler = self.create_handler(i)
                self.server_manager.register_handler(path, handler)
                self.handlers.append((path, handler))
                if debug:
                    print(f"[VrchSwitchOSCControlNode] Registered Switch handler at path {path} with index {i}")

        return tuple(self.switches)

    def create_handler(self, index):
        def handler(address, *args):
            if self.debug:
                print(f"[VrchSwitchOSCControlNode] Received OSC message: addr={address}, args={args}, index={index}")
            value = args[0] if args else 0.0
            self.switches[index] = bool(int(value))
        return handler

class VrchTextConcatOSCControlNode:

    def __init__(self):
        self.texts = ["", "", "", ""]
        self.switches = [False] * 4
        self.server_manager = None
        self.paths = []
        self.handlers = []
        self.separator = ","
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text1": ("STRING", {"multiline": True, "default": ""}),
                "text2": ("STRING", {"multiline": True, "default": ""}),
                "text3": ("STRING", {"multiline": True, "default": ""}),
                "text4": ("STRING", {"multiline": True, "default": ""}),
                "server_ip": (
                    "STRING",
                    {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()},
                ),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path1": ("STRING", {"default": "/toggle1"}),
                "path2": ("STRING", {"default": "/toggle2"}),
                "path3": ("STRING", {"default": "/toggle3"}),
                "path4": ("STRING", {"default": "/toggle4"}),
                "separator": ("STRING", {"default": ","}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("TEXT_OUTPUT",)
    FUNCTION = "load_text_concat_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_text_concat_osc(
        self,
        text1,
        text2,
        text3,
        text4,
        server_ip,
        port,
        path1,
        path2,
        path3,
        path4,
        separator,
        debug,
    ):
        # Update texts and separator
        self.texts = [text1, text2, text3, text4]
        self.separator = separator
        self.debug = debug

        # Check if server parameters or paths have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.debug != debug
        )
        new_paths = [path1, path2, path3, path4]

        if server_params_changed or self.paths != new_paths:
            # Unregister previous handlers if they exist
            if self.server_manager and self.handlers:
                for path, handler in self.handlers:
                    self.server_manager.unregister_handler(path, handler)
                    if debug:
                        print(f"[VrchTextConcatOSCControlNode] Unregistered handler at path {path}")
                self.handlers = []

            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.paths = new_paths

            # Register new handlers
            self.handlers = []
            for i, path in enumerate(self.paths):
                handler = self.create_handler(i)
                self.server_manager.register_handler(path, handler)
                self.handlers.append((path, handler))
                if debug:
                    print(f"[VrchTextConcatOSCControlNode] Registered handler at path {path} with index {i}")

        # Generate the output text based on switches
        selected_texts = [text for text, switch in zip(self.texts, self.switches) if switch]
        output_text = self.separator.join(selected_texts)

        return (output_text,)

    def create_handler(self, index):
        def handler(address, *args):
            if self.debug:
                print(f"[VrchTextConcatOSCControlNode] Received OSC message: addr={address}, args={args}, index={index}")
            value = args[0] if args else 0.0
            self.switches[index] = bool(int(value))
        return handler
