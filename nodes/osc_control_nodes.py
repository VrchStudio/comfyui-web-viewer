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
    def remap(value, in_min=0.0, in_max=1.0, out_min=0.0, out_max=1.0):
        """
        Remap a scalar value from the range [in_min, in_max] to [out_min, out_max].
        """
        if in_max == in_min:
            return out_min
        # Clamp the value within the input range
        value = max(min(value, in_max), in_min)
        # Perform the remapping
        return out_min + ((value - in_min) / (in_max - in_min)) * (out_max - out_min)

    @staticmethod
    def remap_invert(value, in_min=0.0, in_max=1.0, out_min=0.0, out_max=1.0):
        """
        Invert and remap a scalar value from the range [in_min, in_max] to [out_min, out_max].
        """
        if in_max == in_min:
            return out_max
        # Clamp the value within the input range
        value = max(min(value, in_max), in_min)
        # Perform the inverted remapping
        return out_max - ((value - in_min) / (in_max - in_min)) * (out_max - out_min)

    @staticmethod
    def select_remap_func(invert: bool):
        return VrchNodeUtils.remap_invert if invert else VrchNodeUtils.remap



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
        self.x_raw, self.y_raw = 0.0, 0.0  # Raw captured values
        self.x, self.y = 0.0, 0.0          # Remapped float values
        self.x_int, self.y_int = 0, 0      # Remapped integer values
        self.server_manager = None
        self.path = None
        self.debug = False

        # Store server parameters
        self.server_ip = None
        self.port = None
        self.path = None

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
            "port": ("INT", {"default": 8000}),
            "path": ("STRING", {"default": "/xy"}),
            "x_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "x_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "x_output_invert": ("BOOLEAN", {"default": False}),
            "y_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "y_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "y_output_invert": ("BOOLEAN", {"default": False}),
            "debug": ("BOOLEAN", {"default": False})
        }}

    RETURN_TYPES = ("INT", "INT", "FLOAT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("X_INT", "Y_INT", "X_FLOAT", "Y_FLOAT", "X_RAW", "Y_RAW")
    FUNCTION = "load_xy_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_xy_osc(self, server_ip, port, path,
                    x_input_min, x_input_max, x_output_min, x_output_max, x_output_invert,
                    y_input_min, y_input_max, y_output_min, y_output_max, y_output_invert, debug):

        if x_output_min > x_output_max:
            raise ValueError("[VrchXYOSCControlNode] X output min value cannot be greater than max value.")
        if y_output_min > y_output_max:
            raise ValueError("[VrchXYOSCControlNode] Y output min value cannot be greater than max value.")
        if x_input_min > x_input_max:
            raise ValueError("[VrchXYOSCControlNode] X input min value cannot be greater than max value.")
        if y_input_min > y_input_max:
            raise ValueError("[VrchXYOSCControlNode] Y input min value cannot be greater than max value.")

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
                self.server_manager.unregister_handler(f"{self.path}*", self.handle_osc_message)
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(f"{self.path}*", self.handle_osc_message)
            if debug:
                print(f"[VrchXYOSCControlNode] Registered XY handler at path {self.path}*")

        x_remap_func = VrchNodeUtils.select_remap_func(x_output_invert)
        y_remap_func = VrchNodeUtils.select_remap_func(y_output_invert)

        # Remap the raw values to float values
        self.x = x_remap_func(
            float(self.x_raw),
            float(x_input_min),
            float(x_input_max),
            float(x_output_min),
            float(x_output_max)
        )
        self.y = y_remap_func(
            float(self.y_raw),
            float(y_input_min),
            float(y_input_max),
            float(y_output_min),
            float(y_output_max)
        )

        # Convert to integers
        self.x_int = int(self.x)
        self.y_int = int(self.y)

        return self.x_int, self.y_int, self.x, self.y, self.x_raw, self.y_raw

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchXYOSCControlNode] Received OSC message: addr={address}, args={args}")

        if len(args) == 1:
            value = args[0] if args else 0.0
            if address.endswith("/x"):
                self.x_raw = value
            elif address.endswith("/y"):
                self.y_raw = value
        elif len(args) == 2:
            self.x_raw = args[0]
            self.y_raw = args[1]
        else:
            print(f"[VrchXYOSCControlNode] handle_osc_message() call with invalid args: {args}")


class VrchXYZOSCControlNode:

    def __init__(self):
        self.x_raw, self.y_raw, self.z_raw = 0.0, 0.0, 0.0  # Raw captured values
        self.x, self.y, self.z = 0.0, 0.0, 0.0              # Remapped float values
        self.x_int, self.y_int, self.z_int = 0, 0, 0        # Remapped integer values
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/xyz"}),
            "x_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "x_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "x_output_invert": ("BOOLEAN", {"default": False}),
            "y_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "y_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "y_output_invert": ("BOOLEAN", {"default": False}),
            "z_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "z_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "z_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "z_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "z_output_invert": ("BOOLEAN", {"default": False}),
            "debug": ("BOOLEAN", {"default": False})
        }}

    RETURN_TYPES = ("INT", "INT", "INT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = (
        "X_INT", "Y_INT", "Z_INT",
        "X_FLOAT", "Y_FLOAT", "Z_FLOAT",
        "X_RAW", "Y_RAW", "Z_RAW"
    )
    FUNCTION = "load_xyz_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_xyz_osc(self, server_ip, port, path,
                     x_input_min, x_input_max, x_output_min, x_output_max, x_output_invert,
                     y_input_min, y_input_max, y_output_min, y_output_max, y_output_invert,
                     z_input_min, z_input_max, z_output_min, z_output_max, z_output_invert, debug):

        if x_output_min > x_output_max:
            raise ValueError("[VrchXYZOSCControlNode] X output min value cannot be greater than max value.")
        if y_output_min > y_output_max:
            raise ValueError("[VrchXYZOSCControlNode] Y output min value cannot be greater than max value.")
        if z_output_min > z_output_max:
            raise ValueError("[VrchXYZOSCControlNode] Z output min value cannot be greater than max value.")

        if x_input_min > x_input_max:
            raise ValueError("[VrchXYZOSCControlNode] X input min value cannot be greater than max value.")
        if y_input_min > y_input_max:
            raise ValueError("[VrchXYZOSCControlNode] Y input min value cannot be greater than max value.")
        if z_input_min > z_input_max:
            raise ValueError("[VrchXYZOSCControlNode] Z input min value cannot be greater than max value.")

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
                self.server_manager.unregister_handler(f"{self.path}*", self.handle_osc_message)
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(f"{self.path}*", self.handle_osc_message)
            if debug:
                print(f"[VrchXYZOSCControlNode] Registered XYZ handler at path {self.path}*")

        # Select remap functions based on invert options
        x_remap_func = VrchNodeUtils.select_remap_func(x_output_invert)
        y_remap_func = VrchNodeUtils.select_remap_func(y_output_invert)
        z_remap_func = VrchNodeUtils.select_remap_func(z_output_invert)

        # Remap the raw values to float values
        self.x = x_remap_func(
            float(self.x_raw),
            float(x_input_min),
            float(x_input_max),
            float(x_output_min),
            float(x_output_max)
        )
        self.y = y_remap_func(
            float(self.y_raw),
            float(y_input_min),
            float(y_input_max),
            float(y_output_min),
            float(y_output_max)
        )
        self.z = z_remap_func(
            float(self.z_raw),
            float(z_input_min),
            float(z_input_max),
            float(z_output_min),
            float(z_output_max)
        )

        # Convert to integers
        self.x_int = int(self.x)
        self.y_int = int(self.y)
        self.z_int = int(self.z)

        return (
            self.x_int, self.y_int, self.z_int,
            self.x, self.y, self.z,
            self.x_raw, self.y_raw, self.z_raw
        )

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchXYZOSCControlNode] Received OSC message: addr={address}, args={args}")

        if len(args) == 1:
            value = args[0] if args else 0.0
            if address.endswith("/x"):
                self.x_raw = value
            elif address.endswith("/y"):
                self.y_raw = value
            elif address.endswith("/z"):
                self.z_raw = value
        elif len(args) == 3:
            self.x_raw = args[0]
            self.y_raw = args[1]
            self.z_raw = args[2]
        else:
            print(f"[VrchXYZOSCControlNode] handle_osc_message() call with invalid args: {args}")



class VrchIntOSCControlNode:

    def __init__(self):
        self.value = 0
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/path"}),
            "input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "output_invert": ("BOOLEAN", {"default": False}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("INT", "FLOAT")
    RETURN_NAMES = ("VALUE", "RAW_VALUE")
    FUNCTION = "load_int_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_int_osc(
        self,
        server_ip,
        port,
        path,
        input_min=0.0,
        input_max=1.0,
        output_min=0,
        output_max=100,
        output_invert=False,
        debug=False,
    ):

        if output_min > output_max:
            raise ValueError("[VrchIntOSCControlNode] Output min value cannot be greater than max value.")

        if input_min > input_max:
            raise ValueError("[VrchIntOSCControlNode] Input min value cannot be greater than max value.")

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

        # Select remap function based on invert option
        remap_func = VrchNodeUtils.select_remap_func(output_invert)

        # Perform the remapping (clamping is handled within remap functions)
        mapped_value = remap_func(
            float(self.value),
            float(input_min),
            float(input_max),
            float(output_min),
            float(output_max),
        )

        return int(mapped_value), self.value

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
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/path"}),
            "input_min": ("FLOAT", {"default": 0.0, "min": -9999.00, "max": 9999.00, "step": 0.01}),
            "input_max": ("FLOAT", {"default": 1.0, "min": -9999.00, "max": 9999.00, "step": 0.01}),
            "output_min": ("FLOAT", {"default": 0.00, "min": -9999.00, "max": 9999.00, "step": 0.01}),
            "output_max": ("FLOAT", {"default": 100.00, "min": -9999.00, "max": 9999.00, "step": 0.01}),
            "output_invert": ("BOOLEAN", {"default": False}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("FLOAT", "FLOAT")
    RETURN_NAMES = ("VALUE", "RAW_VALUE")
    FUNCTION = "load_float_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_float_osc(
        self, server_ip, port, path, input_min, input_max, output_min, output_max, output_invert, debug
    ):

        if output_min > output_max:
            raise ValueError("[VrchFloatOSCControlNode] Output min value cannot be greater than max value.")

        if input_min > input_max:
            raise ValueError("[VrchFloatOSCControlNode] Input min value cannot be greater than max value.")

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

        # Select remap function based on invert option
        remap_func = VrchNodeUtils.select_remap_func(output_invert)

        # Perform the remapping
        mapped_value = remap_func(
            float(self.value),
            float(input_min),
            float(input_max),
            float(output_min),
            float(output_max),
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
        self.texts = [""] * 8
        self.switches = [False] * 8
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
                "text5": ("STRING", {"multiline": True, "default": ""}),
                "text6": ("STRING", {"multiline": True, "default": ""}),
                "text7": ("STRING", {"multiline": True, "default": ""}),
                "text8": ("STRING", {"multiline": True, "default": ""}),
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
        text5,
        text6,
        text7,
        text8,
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
        separator,
        debug,
    ):
        # Update texts and separator
        self.texts = [text1, text2, text3, text4, text5, text6, text7, text8]
        self.separator = separator
        self.debug = debug

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
    

class VrchTextSwitchOSCControlNode:
    
    def __init__(self):
        self.texts = [""] * 8
        self.current_output = ""
        self.server_manager = None
        self.path = None
        self.debug = False
        self.last_index = None  # To keep track of the last valid index
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text1": ("STRING", {"multiline": True, "default": ""}),
                "text2": ("STRING", {"multiline": True, "default": ""}),
                "text3": ("STRING", {"multiline": True, "default": ""}),
                "text4": ("STRING", {"multiline": True, "default": ""}),
                "text5": ("STRING", {"multiline": True, "default": ""}),
                "text6": ("STRING", {"multiline": True, "default": ""}),
                "text7": ("STRING", {"multiline": True, "default": ""}),
                "text8": ("STRING", {"multiline": True, "default": ""}),
                "server_ip": (
                    "STRING",
                    {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()},
                ),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path": ("STRING", {"default": "/radio1"}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("TEXT_OUTPUT",)
    FUNCTION = "load_text_switch_osc"
    CATEGORY = CATEGORY
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
    
    def load_text_switch_osc(
        self,
        text1,
        text2,
        text3,
        text4,
        text5,
        text6,
        text7,
        text8,
        server_ip,
        port,
        path,
        debug,
    ):
        # Update texts
        self.texts = [text1, text2, text3, text4, text5, text6, text7, text8]
        self.debug = debug

        # Check if server parameters or path have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.debug != debug
        )
        if server_params_changed or self.path != path:
            # Unregister previous handler if it exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(
                    self.path, self.handle_osc_message
                )
                if debug:
                    print(f"[VrchTextSwitchOSCControlNode] Unregistered handler at path {self.path}")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchTextSwitchOSCControlNode] Registered handler at path {self.path}")

        # Return the current output as a tuple
        return (self.current_output,)

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchTextSwitchOSCControlNode] Received OSC message: addr={address}, args={args}")
        value = args[0] if args else 0
        try:
            index = int(value)
            if 0 <= index < len(self.texts):
                self.current_output = self.texts[index]
                self.last_index = index
                if self.debug:
                    print(f"[VrchTextSwitchOSCControlNode] Updated output to text at index {index}")
            else:
                if self.debug:
                    print(f"[VrchTextSwitchOSCControlNode] Index {index} out of range, keeping current output")
                # Do not change current_output, keep last valid output
        except ValueError:
            if self.debug:
                print(f"[VrchTextSwitchOSCControlNode] Received invalid value: {value}, keeping current output")
            # Do not change current_output


class VrchAnyOSCControlNode:

    def __init__(self):
        self.int_value = 0
        self.float_value = 0.0
        self.text_value = ""
        self.bool_value = False
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": VrchNodeUtils.get_default_ip_address()}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/path"}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("INT", "FLOAT", "STRING", "BOOLEAN")
    RETURN_NAMES = ("INT", "FLOAT", "TEXT", "BOOL")
    FUNCTION = "load_any_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_any_osc(self, server_ip, port, path, debug):
        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.path != path
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if it exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(self.path, self.handle_osc_message)
                if debug:
                    print(f"[VrchAnyOSCControlNode] Unregistered handler at path {self.path}")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchAnyOSCControlNode] Registered handler at path {self.path}")

        # Return the current values
        return self.int_value, self.float_value, self.text_value, self.bool_value

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchAnyOSCControlNode] Received OSC message: addr={address}, args={args}")

        if not args:
            if self.debug:
                print(f"[VrchAnyOSCControlNode] No arguments received.")
            return

        value = args[0]

        # Reset all outputs
        self.int_value = 0
        self.float_value = 0.0
        self.text_value = ""
        self.bool_value = False

        # Determine the type of the value
        if isinstance(value, bool):
            self.bool_value = value
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Detected BOOLEAN value: {value}")
        elif isinstance(value, int):
            self.int_value = value
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Detected INT value: {value}")
        elif isinstance(value, float):
            self.float_value = value
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Detected FLOAT value: {value}")
        elif isinstance(value, str):
            self.text_value = value
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Detected STRING value: {value}")
        else:
            # Handle other types if necessary
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Received unsupported value type: {type(value)}")
