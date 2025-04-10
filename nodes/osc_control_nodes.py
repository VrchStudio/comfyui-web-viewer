import hashlib
import time
from pythonosc import dispatcher, osc_server
from .node_utils import VrchNodeUtils
import threading


# Define the category for organizational purposes
CATEGORY = "vrch.ai/control/osc"
# The default server IP address
DEFAULT_SERVER_IP = VrchNodeUtils.get_default_ip_address()

# Global dictionaries to store output states and previous hashes
node_output_states = {}
previous_hashes = {}
# Lock for thread-safe access to global dictionaries
state_lock = threading.Lock()

class AlwaysEqualProxy(str):
        def __eq__(self, _):
            return True

        def __ne__(self, _):
            return False

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

        # Add default value properties
        self.x_default = 0
        self.y_default = 0
        # Add server connection status
        self.server_connected = False
        # Add flags to track if data was received
        self.server_data_received_x = False
        self.server_data_received_y = False

        # Store server parameters
        self.server_ip = None
        self.port = None
        self.path = None

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000}),
            "path": ("STRING", {"default": "/xy"}),
            "x_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "x_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "x_output_invert": ("BOOLEAN", {"default": False}),
            "x_output_default": ("INT", {"default": 50, "min": -9999, "max": 9999}),
            "y_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "y_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "y_output_invert": ("BOOLEAN", {"default": False}),
            "y_output_default": ("INT", {"default": 50, "min": -9999, "max": 9999}),
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
                    x_input_min, x_input_max, x_output_min, x_output_max, x_output_invert, x_output_default,
                    y_input_min, y_input_max, y_output_min, y_output_max, y_output_invert, y_output_default,
                    debug):

        if x_output_min > x_output_max:
            raise ValueError("[VrchXYOSCControlNode] X output min value cannot be greater than max value.")
        if y_output_min > y_output_max:
            raise ValueError("[VrchXYOSCControlNode] Y output min value cannot be greater than max value.")
        if x_input_min > x_input_max:
            raise ValueError("[VrchXYOSCControlNode] X input min value cannot be greater than max value.")
        if y_input_min > y_input_max:
            raise ValueError("[VrchXYOSCControlNode] Y input min value cannot be greater than max value.")
            
        # Validate default values are within range
        if x_output_default < x_output_min or x_output_default > x_output_max:
            raise ValueError("[VrchXYOSCControlNode] X default value must be within the output range.")
        if y_output_default < y_output_min or y_output_default > y_output_max:
            raise ValueError("[VrchXYOSCControlNode] Y default value must be within the output range.")

        # Store default values
        self.x_default = x_output_default
        self.y_default = y_output_default

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None 
            or self.server_manager.ip != server_ip 
            or self.server_manager.port != port 
            or self.path != path 
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(f"{self.path}*", self.handle_osc_message)
            # Get or create the server manager
            try:
                self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
                self.debug = debug
                # Register new handler
                self.path = path
                self.server_manager.register_handler(f"{self.path}*", self.handle_osc_message)
                self.server_connected = True
                # Reset data received flags when changing server parameters
                self.server_data_received_x = False
                self.server_data_received_y = False
                self.x_raw = 0.0
                self.y_raw = 0.0
                if debug:
                    print(f"[VrchXYOSCControlNode] Registered XY handler at path {self.path}*")
            except Exception as e:
                self.server_connected = False
                if debug:
                    print(f"[VrchXYOSCControlNode] Failed to connect to OSC server: {e}")

        x_remap_func = VrchNodeUtils.select_remap_func(x_output_invert)
        y_remap_func = VrchNodeUtils.select_remap_func(y_output_invert)

        # Use raw values only if server is connected and data was received
        # Otherwise use default values
        if not self.server_connected or not self.server_data_received_x:
            x_value = float(x_output_default)
            x_raw = 0.0
            if debug:
                print(f"[VrchXYOSCControlNode] Using X default value: {x_output_default}")
        else:
            x_value = x_remap_func(
                float(self.x_raw),
                float(x_input_min),
                float(x_input_max),
                float(x_output_min),
                float(x_output_max)
            )
            x_raw = self.x_raw

        if not self.server_connected or not self.server_data_received_y:
            y_value = float(y_output_default)
            y_raw = 0.0
            if debug:
                print(f"[VrchXYOSCControlNode] Using Y default value: {y_output_default}")
        else:
            y_value = y_remap_func(
                float(self.y_raw),
                float(y_input_min),
                float(y_input_max),
                float(y_output_min),
                float(y_output_max)
            )
            y_raw = self.y_raw

        # Store remapped values
        self.x = x_value
        self.y = y_value

        # Convert to integers
        self.x_int = int(x_value)
        self.y_int = int(y_value)

        return self.x_int, self.y_int, self.x, self.y, x_raw, y_raw

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchXYOSCControlNode] Received OSC message: addr={address}, args={args}")

        try:
            if len(args) == 1:
                value = args[0] if args else 0.0
                if address.endswith("/x"):
                    self.x_raw = value
                    self.server_data_received_x = True
                    if self.debug:
                        print(f"[VrchXYOSCControlNode] Received X value: {value}")
                elif address.endswith("/y"):
                    self.y_raw = value
                    self.server_data_received_y = True
                    if self.debug:
                        print(f"[VrchXYOSCControlNode] Received Y value: {value}")
            elif len(args) == 2:
                self.x_raw = args[0]
                self.y_raw = args[1]
                self.server_data_received_x = True
                self.server_data_received_y = True
                if self.debug:
                    print(f"[VrchXYOSCControlNode] Received XY values: {args}")
            else:
                if self.debug:
                    print(f"[VrchXYOSCControlNode] handle_osc_message() called with invalid args: {args}")
        except Exception as e:
            # In case of error, mark data as not received
            if address.endswith("/x"):
                self.server_data_received_x = False
            elif address.endswith("/y"):
                self.server_data_received_y = False
            else:
                self.server_data_received_x = False
                self.server_data_received_y = False
                
            if self.debug:
                print(f"[VrchXYOSCControlNode] Error handling OSC message: {e}")

class VrchXYZOSCControlNode:

    def __init__(self):
        self.x_raw, self.y_raw, self.z_raw = 0.0, 0.0, 0.0  # Raw captured values
        self.x, self.y, self.z = 0.0, 0.0, 0.0              # Remapped float values
        self.x_int, self.y_int, self.z_int = 0, 0, 0        # Remapped integer values
        self.server_manager = None
        self.path = None
        self.debug = False
        # Add default value properties
        self.x_default = 0
        self.y_default = 0
        self.z_default = 0
        # Add server connection status
        self.server_connected = False
        # Add flags to track if data was received
        self.server_data_received_x = False
        self.server_data_received_y = False
        self.server_data_received_z = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/xyz"}),
            "x_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "x_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "x_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "x_output_invert": ("BOOLEAN", {"default": False}),
            "x_output_default": ("INT", {"default": 50, "min": -9999, "max": 9999}),
            "y_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "y_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "y_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "y_output_invert": ("BOOLEAN", {"default": False}),
            "y_output_default": ("INT", {"default": 50, "min": -9999, "max": 9999}),
            "z_input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "z_input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "z_output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "z_output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "z_output_invert": ("BOOLEAN", {"default": False}),
            "z_output_default": ("INT", {"default": 50, "min": -9999, "max": 9999}),
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
                     x_input_min, x_input_max, x_output_min, x_output_max, x_output_invert, x_output_default,
                     y_input_min, y_input_max, y_output_min, y_output_max, y_output_invert, y_output_default,
                     z_input_min, z_input_max, z_output_min, z_output_max, z_output_invert, z_output_default, 
                     debug):

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
            
        # Validate default values are within range
        if x_output_default < x_output_min or x_output_default > x_output_max:
            raise ValueError("[VrchXYZOSCControlNode] X default value must be within the output range.")
        if y_output_default < y_output_min or y_output_default > y_output_max:
            raise ValueError("[VrchXYZOSCControlNode] Y default value must be within the output range.")
        if z_output_default < z_output_min or z_output_default > z_output_max:
            raise ValueError("[VrchXYZOSCControlNode] Z default value must be within the output range.")

        # Store default values
        self.x_default = x_output_default
        self.y_default = y_output_default
        self.z_default = z_output_default

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None 
            or self.server_manager.ip != server_ip 
            or self.server_manager.port != port 
            or self.path != path 
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(f"{self.path}*", self.handle_osc_message)
            # Get or create the server manager
            try:
                self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
                self.debug = debug
                # Register new handler
                self.path = path
                self.server_manager.register_handler(f"{self.path}*", self.handle_osc_message)
                self.server_connected = True
                # Reset data received flags when changing server parameters
                self.server_data_received_x = False
                self.server_data_received_y = False
                self.server_data_received_z = False
                self.x_raw = 0.0
                self.y_raw = 0.0
                self.z_raw = 0.0
                if debug:
                    print(f"[VrchXYZOSCControlNode] Registered XYZ handler at path {self.path}*")
            except Exception as e:
                self.server_connected = False
                if debug:
                    print(f"[VrchXYZOSCControlNode] Failed to connect to OSC server: {e}")

        # Select remap functions based on invert options
        x_remap_func = VrchNodeUtils.select_remap_func(x_output_invert)
        y_remap_func = VrchNodeUtils.select_remap_func(y_output_invert)
        z_remap_func = VrchNodeUtils.select_remap_func(z_output_invert)

        # Use raw values only if server is connected and data was received
        # Otherwise use default values
        if not self.server_connected or not self.server_data_received_x:
            x_value = float(x_output_default)
            x_raw = 0.0
            if debug:
                print(f"[VrchXYZOSCControlNode] Using X default value: {x_output_default}")
        else:
            x_value = x_remap_func(
                float(self.x_raw),
                float(x_input_min),
                float(x_input_max),
                float(x_output_min),
                float(x_output_max)
            )
            x_raw = self.x_raw

        if not self.server_connected or not self.server_data_received_y:
            y_value = float(y_output_default)
            y_raw = 0.0
            if debug:
                print(f"[VrchXYZOSCControlNode] Using Y default value: {y_output_default}")
        else:
            y_value = y_remap_func(
                float(self.y_raw),
                float(y_input_min),
                float(y_input_max),
                float(y_output_min),
                float(y_output_max)
            )
            y_raw = self.y_raw

        if not self.server_connected or not self.server_data_received_z:
            z_value = float(z_output_default)
            z_raw = 0.0
            if debug:
                print(f"[VrchXYZOSCControlNode] Using Z default value: {z_output_default}")
        else:
            z_value = z_remap_func(
                float(self.z_raw),
                float(z_input_min),
                float(z_input_max),
                float(z_output_min),
                float(z_output_max)
            )
            z_raw = self.z_raw

        # Store remapped values
        self.x = x_value
        self.y = y_value  
        self.z = z_value

        # Convert to integers
        self.x_int = int(x_value)
        self.y_int = int(y_value)
        self.z_int = int(z_value)

        return (
            self.x_int, self.y_int, self.z_int,
            self.x, self.y, self.z,
            x_raw, y_raw, z_raw
        )

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchXYZOSCControlNode] Received OSC message: addr={address}, args={args}")

        try:
            if len(args) == 1:
                value = args[0] if args else 0.0
                if address.endswith("/x"):
                    self.x_raw = value
                    self.server_data_received_x = True
                    if self.debug:
                        print(f"[VrchXYZOSCControlNode] Received X value: {value}")
                elif address.endswith("/y"):
                    self.y_raw = value
                    self.server_data_received_y = True
                    if self.debug:
                        print(f"[VrchXYZOSCControlNode] Received Y value: {value}")
                elif address.endswith("/z"):
                    self.z_raw = value
                    self.server_data_received_z = True
                    if self.debug:
                        print(f"[VrchXYZOSCControlNode] Received Z value: {value}")
            elif len(args) == 3:
                self.x_raw = args[0]
                self.y_raw = args[1]
                self.z_raw = args[2]
                self.server_data_received_x = True
                self.server_data_received_y = True
                self.server_data_received_z = True
                if self.debug:
                    print(f"[VrchXYZOSCControlNode] Received XYZ values: {args}")
            else:
                if self.debug:
                    print(f"[VrchXYZOSCControlNode] handle_osc_message() called with invalid args: {args}")
        except Exception as e:
            # In case of error, mark data as not received
            if address.endswith("/x"):
                self.server_data_received_x = False
            elif address.endswith("/y"):
                self.server_data_received_y = False
            elif address.endswith("/z"):
                self.server_data_received_z = False
            else:
                self.server_data_received_x = False
                self.server_data_received_y = False
                self.server_data_received_z = False
                
            if self.debug:
                print(f"[VrchXYZOSCControlNode] Error handling OSC message: {e}")

class VrchIntOSCControlNode:

    def __init__(self):
        self.value = 0
        self.default_value = 0
        self.server_connected = False  # Server connection status
        self.server_data_received = False  # Flag to check if value was received from server
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/path"}),
            "input_min": ("FLOAT", {"default": 0.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "input_max": ("FLOAT", {"default": 1.0, "min": -9999.0, "max": 9999.0, "step": 0.01}),
            "output_min": ("INT", {"default": 0, "min": -9999, "max": 9999}),
            "output_max": ("INT", {"default": 100, "min": -9999, "max": 9999}),
            "output_invert": ("BOOLEAN", {"default": False}),
            "output_default": ("INT", {"default": 0, "min": -9999, "max": 9999}),
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
        output_default=0,
        debug=False,
    ):

        if output_min > output_max:
            raise ValueError("[VrchIntOSCControlNode] Output min value cannot be greater than max value.")

        if input_min > input_max:
            raise ValueError("[VrchIntOSCControlNode] Input min value cannot be greater than max value.")
        
        if output_default < output_min or output_default > output_max:
            raise ValueError("[VrchIntOSCControlNode] Default value must be within the output range.")
        
        # Set default value
        self.default_value = output_default

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
                self.server_manager.unregister_handler(
                    self.path, self.handle_osc_message
                )
            # Get or create the server manager
            try:
                self.server_manager = VrchOSCServerManager.get_instance(
                    server_ip, port, debug
                )
                self.debug = debug
                # Register new handler
                self.path = path
                self.server_manager.register_handler(self.path, self.handle_osc_message)
                self.server_connected = True
                self.server_data_received = False
                self.value = 0
                if debug:
                    print(f"[VrchIntOSCControlNode] Registered Int handler at path {self.path}")
            except Exception as e:
                self.server_connected = False
                if debug:
                    print(f"[VrchIntOSCControlNode] Failed to connect to OSC server: {e}")
        
        # Check if the server is connected and if a value was received
        if not self.server_connected or not self.server_data_received:
            if debug:
                print(
                    f"[VrchIntOSCControlNode] Server Status: "
                    f"connected: {self.server_connected}, "
                    f"data received: {self.server_data_received}, "
                    f"using default value: {self.default_value}"
                )
            return self.default_value, self.value

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
        try:
            if args:
                value = args[0]
                self.value = value
                self.server_data_received = True
                if self.debug:
                    print(f"[VrchIntOSCControlNode] Received OSC message: addr={address}, value={value}")
            else:
                # No arguments, mark as not received
                self.server_data_received = False
                self.value = 0
                if self.debug:
                    print(f"[VrchIntOSCControlNode] No arguments received, using default value: {self.default_value}")
                
        except Exception as e:
            # Mark as data not received when exception occurs
            self.server_data_received = False
            self.value = 0
            if self.debug:
                print(f"[VrchIntOSCControlNode] Error handling OSC message: {e}, using default value: {self.default_value}")


class VrchFloatOSCControlNode:

    def __init__(self):
        self.value = 0.0
        self.server_manager = None
        self.path = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
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
            or self.path != path
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
                    {"multiline": False, "default": DEFAULT_SERVER_IP},
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
        server_ip, port,
        path1, path2, path3, path4, path5, path6, path7, path8,
        debug,
    ):
        
        new_paths = [path1, path2, path3, path4, path5, path6, path7, path8]
        
        # Check if server parameters or paths have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.paths != new_paths
            or self.debug != debug
        )

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
                    {"multiline": False, "default": DEFAULT_SERVER_IP},
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
        text1, text2, text3, text4, text5, text6, text7, text8,
        server_ip, port,
        path1, path2, path3, path4, path5, path6, path7, path8,
        separator,
        debug,
    ):
        # Update texts and separator
        self.texts = [text1, text2, text3, text4, text5, text6, text7, text8]
        self.separator = separator
        self.debug = debug
        
        new_paths = [path1, path2, path3, path4, path5, path6, path7, path8]

        # Check if server parameters or paths have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.paths != new_paths
            or self.debug != debug
        )
        

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
                    {"multiline": False, "default": DEFAULT_SERVER_IP},
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
        text1, text2, text3, text4, text5, text6, text7, text8,
        server_ip, port, path,
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
            or self.path != path
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

class VrchImageSwitchOSCControlNode:

    DEFAULT_IMAGE_NUM = 4  # Number of image inputs

    def __init__(self):
        self.images = [None] * self.DEFAULT_IMAGE_NUM
        self.current_output = None
        self.server_manager = None
        self.path = None
        self.debug = False
        self.last_index = 0

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "server_ip": (
                    "STRING",
                    {"multiline": False, "default": DEFAULT_SERVER_IP},
                ),
                "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
                "path": ("STRING", {"default": "/radio1"}),
                "debug": ("BOOLEAN", {"default": False}),
            },
            "optional": {},
        }
        for i in range(cls.DEFAULT_IMAGE_NUM):
            inputs["optional"][f"image{i}"] = ("IMAGE", {})
        return inputs

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "load_image_switch_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def check_lazy_status(self, **kwargs):
        index = self.last_index
        if index is None:
            return []  # No index selected yet
        key = f"image{index}"
        if kwargs.get(key, None) is None:
            return [key]
        return []

    def load_image_switch_osc(
        self,
        server_ip,
        port,
        path,
        debug,
        **kwargs,
    ):
        # Update images
        for i in range(self.DEFAULT_IMAGE_NUM):
            key = f"image{i}"
            if key in kwargs:
                self.images[i] = kwargs[key]
            else:
                self.images[i] = None
        self.debug = debug

        # Check if server parameters or path have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.path != path
            or self.debug != debug
        )
        if server_params_changed or self.path != path:
            # Unregister previous handler if it exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(
                    self.path, self.handle_osc_message
                )
                if debug:
                    print(f"[VrchImageSwitchOSCControlNode] Unregistered handler at path {self.path}")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchImageSwitchOSCControlNode] Registered handler at path {self.path}")

        # Set current output based on last index
        if self.last_index is not None and 0 <= self.last_index < len(self.images):
            self.current_output = self.images[self.last_index]
        else:
            self.current_output = None

        # Return the current output as a tuple
        return (self.current_output,)

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchImageSwitchOSCControlNode] Received OSC message: addr={address}, args={args}")
        value = args[0] if args else 0
        try:
            index = int(value)
            if 0 <= index < len(self.images):
                self.last_index = index
                if self.debug:
                    print(f"[VrchImageSwitchOSCControlNode] Selected image at index {index}")
            else:
                if self.debug:
                    print(f"[VrchImageSwitchOSCControlNode] Index {index} out of range")
        except (ValueError, TypeError):
            if self.debug:
                print(f"[VrchImageSwitchOSCControlNode] Received invalid value: {value}")


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
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
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
        """
        Determines if the outputs have changed by comparing the current hash with the previous hash.
        Returns the hash digest if changed, otherwise returns False.
        """
        path = kwargs.get('path')
        debug = kwargs.get('debug', False)
        if not path:
            if debug:
                print("[VrchAnyOSCControlNode] No path provided to IS_CHANGED.")
            return False  # No path provided, no change detected
        
        with state_lock:
            state = node_output_states.get(path, {
                'INT': 0,
                'FLOAT': 0.0,
                'TEXT': '',
                'BOOL': False
            })
            combined = f"{state['INT']}_{state['FLOAT']}_{state['TEXT']}_{state['BOOL']}"
            m = hashlib.sha256()
            m.update(combined.encode())
            hash_digest = m.hexdigest()

            previous_hash = previous_hashes.get(path)
            if previous_hash != hash_digest:
                previous_hashes[path] = hash_digest
                if debug:
                    print(f"[VrchAnyOSCControlNode] Change detected for path '{path}': {combined} -> {hash_digest}")
                return hash_digest  # Change detected
            if debug:
                print(f"[VrchAnyOSCControlNode] No change detected for path '{path}'.")
            return False  # No change detected

    def load_any_osc(self, server_ip, port, path, debug):
        """
        Initializes or updates the OSC server handler based on the provided parameters.
        Returns the current output values for IS_CHANGED to detect changes.
        """
        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.path != path
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handler if exists
            if self.server_manager and self.path:
                self.server_manager.unregister_handler(self.path, self.handle_osc_message)
                if debug:
                    print(f"[VrchAnyOSCControlNode] Unregistered handler at path '{self.path}'")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchAnyOSCControlNode] Registered handler at path '{self.path}'")

        # Return the current values along with path and debug for IS_CHANGED
        return self.int_value, self.float_value, self.text_value, self.bool_value

    def handle_osc_message(self, address, *args):
        """
        Handles incoming OSC messages and updates the node's output values based on the message type.
        """
        if self.debug:
            print(f"[VrchAnyOSCControlNode] Received OSC message: addr='{address}', args={args}")

        if not args:
            if self.debug:
                print("[VrchAnyOSCControlNode] No arguments received.")
            return

        value = args[0]

        # Reset all outputs
        self.int_value = 0
        self.float_value = 0.0
        self.text_value = ""
        self.bool_value = False

        # Determine the type of the value and update the corresponding output
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
            return  # Unsupported type, do not update state

        # Update the global state with the current outputs using path
        with state_lock:
            node_output_states[self.path] = {
                'INT': self.int_value,
                'FLOAT': self.float_value,
                'TEXT': self.text_value,
                'BOOL': self.bool_value
            }
            if self.debug:
                print(f"[VrchAnyOSCControlNode] Updated state for path '{self.path}': {node_output_states[self.path]}")


class VrchChannelOSCControlNode:

    def __init__(self):
        self.output_value = None
        self.server_manager = None
        self.path = None
        self.debug = False
        self.channel_on = False
        self.any_channel_on = None
        self.any_channel_off = None

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "any_channel_on": (AlwaysEqualProxy("*"), {}),
            "any_channel_off": (AlwaysEqualProxy("*"), {}),
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/channel"}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = (AlwaysEqualProxy("*"),)
    RETURN_NAMES = ("ANY_OUTPUT",)
    FUNCTION = "load_channel_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_channel_osc(self, any_channel_on, any_channel_off, server_ip, port, path, debug):
        # Store the input values
        self.any_channel_on = any_channel_on
        self.any_channel_off = any_channel_off
        self.debug = debug

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
                    print(f"[VrchChannelOSCControlNode] Unregistered handler at path {self.path}")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handler
            self.path = path
            self.server_manager.register_handler(self.path, self.handle_osc_message)
            if debug:
                print(f"[VrchChannelOSCControlNode] Registered handler at path {self.path}")

        # Output the appropriate value based on channel state
        if self.channel_on:
            self.output_value = self.any_channel_on
        else:
            self.output_value = self.any_channel_off

        return (self.output_value,)

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchChannelOSCControlNode] Received OSC message: addr={address}, args={args}")

        value = args[0] if args else 0.0
        # Simplified check: Convert value to int, then to bool
        self.channel_on = bool(int(value))
        if self.debug:
            print(f"[VrchChannelOSCControlNode] Channel is {'ON' if self.channel_on else 'OFF'}")
            

class VrchChannelX4OSCControlNode:

    def __init__(self):
        self.output_values = [None] * 4
        self.server_manager = None
        self.paths = [None] * 4
        self.debug = False
        self.channel_states = [False] * 4
        self.any_channel_on = [None] * 4
        self.any_channel_off = [None] * 4
        self.handlers = [None] * 4  # Store handlers for unregistering

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "any_channel_1_on": (AlwaysEqualProxy("*"), {}),
            "any_channel_1_off": (AlwaysEqualProxy("*"), {}),
            "any_channel_2_on": (AlwaysEqualProxy("*"), {}),
            "any_channel_2_off": (AlwaysEqualProxy("*"), {}),
            "any_channel_3_on": (AlwaysEqualProxy("*"), {}),
            "any_channel_3_off": (AlwaysEqualProxy("*"), {}),
            "any_channel_4_on": (AlwaysEqualProxy("*"), {}),
            "any_channel_4_off": (AlwaysEqualProxy("*"), {}),
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path1": ("STRING", {"default": "/channel1"}),
            "path2": ("STRING", {"default": "/channel2"}),
            "path3": ("STRING", {"default": "/channel3"}),
            "path4": ("STRING", {"default": "/channel4"}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = (
        AlwaysEqualProxy("*"),
        AlwaysEqualProxy("*"),
        AlwaysEqualProxy("*"),
        AlwaysEqualProxy("*"),
    )
    RETURN_NAMES = ("ANY_OUTPUT_1", "ANY_OUTPUT_2", "ANY_OUTPUT_3", "ANY_OUTPUT_4")
    FUNCTION = "load_channel_x4_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_channel_x4_osc(
        self,
        any_channel_1_on, any_channel_1_off,
        any_channel_2_on, any_channel_2_off,
        any_channel_3_on, any_channel_3_off,
        any_channel_4_on, any_channel_4_off,
        server_ip, port, path1, path2, path3, path4, debug,
    ):
        # Store input values
        self.any_channel_on = [
            any_channel_1_on, any_channel_2_on, any_channel_3_on, any_channel_4_on
        ]
        self.any_channel_off = [
            any_channel_1_off, any_channel_2_off, any_channel_3_off, any_channel_4_off
        ]
        self.debug = debug

        new_paths = [path1, path2, path3, path4]

        # Check if server parameters or paths have changed
        server_params_changed = (
            self.server_manager is None
            or self.server_manager.ip != server_ip
            or self.server_manager.port != port
            or self.paths != new_paths
            or self.debug != debug
        )

        if server_params_changed:
            # Unregister previous handlers if they exist
            if self.server_manager and any(self.paths):
                for i, handler in enumerate(self.handlers):
                    if handler:
                        self.server_manager.unregister_handler(self.paths[i], handler)
                        if debug:
                            print(f"[VrchChannelX4OSCControlNode] Unregistered handler at path {self.paths[i]}")
            # Get or create the server manager
            self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
            self.debug = debug
            # Register new handlers
            self.paths = new_paths
            self.handlers = []
            for i, path in enumerate(self.paths):
                handler = self.create_handler(i)
                self.server_manager.register_handler(path, handler)
                self.handlers.append(handler)
                if debug:
                    print(f"[VrchChannelX4OSCControlNode] Registered handler at path {path} for channel {i+1}")

        # Update output values based on channel states
        for i in range(4):
            if self.channel_states[i]:
                self.output_values[i] = self.any_channel_on[i]
            else:
                self.output_values[i] = self.any_channel_off[i]

        return tuple(self.output_values)

    def create_handler(self, index):
        # Create a handler function for the specified channel index
        def handler(address, *args):
            if self.debug:
                print(f"[VrchChannelX4OSCControlNode] Received OSC message: addr={address}, args={args}, channel={index+1}")
            value = args[0] if args else 0.0
            # Simplified check: Convert value to int, then to bool
            self.channel_states[index] = bool(int(value))
            if self.debug:
                print(f"[VrchChannelX4OSCControlNode] Channel {index+1} is {'ON' if self.channel_states[index] else 'OFF'}")
        return handler

class VrchDelayOscControlNode:

    def __init__(self):
        self.delay_period = 0  # Delay in milliseconds
        self.raw_value = 0.0    # Original OSC message value
        self.server_manager = None
        self.path = None
        self.debug = False
        self.any_output = None  # To store the delayed output

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "any_input": (AlwaysEqualProxy("*"), {}),
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "path": ("STRING", {"default": "/path"}),
            "input_min": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 9999.0, "step": 0.01}),
            "input_max": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 9999.0, "step": 0.01}),
            "output_min": ("INT", {"default": 0, "min": 0, "max": 9999}),
            "output_max": ("INT", {"default": 1000, "min": 0, "max": 9999}),
            "output_invert": ("BOOLEAN", {"default": False}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = (AlwaysEqualProxy("*"), "INT", "FLOAT")
    RETURN_NAMES = ("ANY_OUTPUT", "DELAY_PERIOD", "RAW_VALUE")
    FUNCTION = "load_delay_osc"
    CATEGORY = CATEGORY

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_delay_osc(self, any_input, server_ip, port, path,
                       input_min, input_max, output_min, output_max, output_invert, debug):

        if output_min > output_max:
            raise ValueError("[VrchDelayOscControlNode] Output min value cannot be greater than max value.")
        if input_min > input_max:
            raise ValueError("[VrchDelayOscControlNode] Input min value cannot be greater than max value.")

        # Check if server parameters have changed
        server_params_changed = (
            self.server_manager is None 
            or self.server_manager.ip != server_ip 
            or self.server_manager.port != port 
            or self.path != path 
            or self.debug != debug
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
                print(f"[VrchDelayOscControlNode] Registered handler at path {self.path}*")

        # Select remap function based on invert option
        remap_func = VrchNodeUtils.select_remap_func(output_invert)

        # Remap the raw OSC value to delay_period in milliseconds
        mapped_delay = remap_func(
            float(self.raw_value),
            float(input_min),
            float(input_max),
            float(output_min),
            float(output_max),
        )
        self.delay_period = int(mapped_delay)

        # Process the any_input with the specified delay
        if any_input is not None:
            if self.debug:
                print(f"[VrchDelayOscControlNode] Delaying input for {self.delay_period} ms")
            time.sleep(self.delay_period / 1000.0)  # Convert ms to seconds
            self.any_output = any_input
            if self.debug:
                print(f"[VrchDelayOscControlNode] Output set after delay: {self.any_output}")

        return (self.any_output, self.delay_period, self.raw_value)

    def handle_osc_message(self, address, *args):
        if self.debug:
            print(f"[VrchDelayOscControlNode] Received OSC message: addr={address}, args={args}")

        if len(args) == 1:
            try:
                value = float(args[0])
                # Update raw_value based on the received value
                self.raw_value = value
                if self.debug:
                    print(f"[VrchDelayOscControlNode] Updated raw_value to: {self.raw_value}")
            except (ValueError, TypeError):
                if self.debug:
                    print(f"[VrchDelayOscControlNode] Received non-float value: {args[0]}")
        else:
            if self.debug:
                print(f"[VrchDelayOscControlNode] handle_osc_message() call with invalid args: {args}")

class VrchOSCControlSettingsNode:

    def __init__(self):
        self.server_manager = None
        self.debug = False

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "server_ip": ("STRING", {"multiline": False, "default": DEFAULT_SERVER_IP}),
            "port": ("INT", {"default": 8000, "min": 0, "max": 65535}),
            "debug": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("SERVER_IP", "PORT")
    FUNCTION = "load_osc_server_settings"
    CATEGORY = CATEGORY

    def load_osc_server_settings(self, server_ip, port, debug=False):
        
        # Get or create the server manager
        self.server_manager = VrchOSCServerManager.get_instance(server_ip, port, debug)
        self.debug = debug
        
        if self.debug:
            print(f"[VrchOSCControlServerNode] server: {server_ip}, port: {port}")
        
        return server_ip, port
    
    @classmethod
    def IS_CHANGED(s, **kwargs):
        return False

