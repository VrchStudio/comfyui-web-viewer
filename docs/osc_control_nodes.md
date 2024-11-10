### Node: `XY OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `XY OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/xy"`).
   - **X Input Range:**
     - **`x_input_min`:** Minimum expected X input value (default is `0.0`).
     - **`x_input_max`:** Maximum expected X input value (default is `1.0`).
   - **X Output Range:**
     - **`x_output_min`:** Minimum X output value (integer, default is `0`).
     - **`x_output_max`:** Maximum X output value (integer, default is `100`).
     - **`x_output_invert`:** Invert the X output mapping if checked (default is `False`).
   - **Y Input Range:**
     - **`y_input_min`:** Minimum expected Y input value (default is `0.0`).
     - **`y_input_max`:** Maximum expected Y input value (default is `1.0`).
   - **Y Output Range:**
     - **`y_output_min`:** Minimum Y output value (integer, default is `0`).
     - **`y_output_max`:** Maximum Y output value (integer, default is `100`).
     - **`y_output_invert`:** Invert the Y output mapping if checked (default is `False`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with either two arguments (`x` and `y` values) or to sub-paths `path/x` and `path/y` with single values.
   - **Data Mapping:**
     - The node maps the incoming `x` and `y` values from the input range to the output range, optionally inverting the mapping.
   - **Outputs:**
     - **`X_INT`, `Y_INT`**: The remapped integer values of X and Y.
     - **`X_FLOAT`, `Y_FLOAT`**: The remapped float values of X and Y.
     - **`X_RAW`, `Y_RAW`**: The raw input values received from OSC messages.

4. **Connect Outputs:**
   - Use the outputs to control other nodes or parameters within your ComfyUI workflow.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and `path`.
- The input and output ranges allow you to calibrate and map values as needed.
- The node supports both combined (`/xy` with two arguments) and separate (`/xy/x` and `/xy/y`) OSC messages.

---

### Node: `XYZ OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `XYZ OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/xyz"`).
   - **X Input Range:**
     - **`x_input_min`:** Minimum expected X input value (default is `0.0`).
     - **`x_input_max`:** Maximum expected X input value (default is `1.0`).
   - **X Output Range:**
     - **`x_output_min`:** Minimum X output value (integer, default is `0`).
     - **`x_output_max`:** Maximum X output value (integer, default is `100`).
     - **`x_output_invert`:** Invert the X output mapping if checked (default is `False`).
   - **Y Input Range:**
     - **`y_input_min`:** Minimum expected Y input value (default is `0.0`).
     - **`y_input_max`:** Maximum expected Y input value (default is `1.0`).
   - **Y Output Range:**
     - **`y_output_min`:** Minimum Y output value (integer, default is `0`).
     - **`y_output_max`:** Maximum Y output value (integer, default is `100`).
     - **`y_output_invert`:** Invert the Y output mapping if checked (default is `False`).
   - **Z Input Range:**
     - **`z_input_min`:** Minimum expected Z input value (default is `0.0`).
     - **`z_input_max`:** Maximum expected Z input value (default is `1.0`).
   - **Z Output Range:**
     - **`z_output_min`:** Minimum Z output value (integer, default is `0`).
     - **`z_output_max`:** Maximum Z output value (integer, default is `100`).
     - **`z_output_invert`:** Invert the Z output mapping if checked (default is `False`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with three arguments (`x`, `y`, and `z` values) or to sub-paths `path/x`, `path/y`, and `path/z` with single values.
   - **Data Mapping:**
     - The node maps the incoming `x`, `y`, and `z` values from the input ranges to the output ranges, optionally inverting the mappings.
   - **Outputs:**
     - **`X_INT`, `Y_INT`, `Z_INT`**: The remapped integer values of X, Y, and Z.
     - **`X_FLOAT`, `Y_FLOAT`, `Z_FLOAT`**: The remapped float values of X, Y, and Z.
     - **`X_RAW`, `Y_RAW`, `Z_RAW`**: The raw input values received from OSC messages.

4. **Connect Outputs:**
   - Use the outputs to control other nodes or parameters within your ComfyUI workflow.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and `path`.
- The input and output ranges allow you to calibrate and map values as needed.
- The node supports both combined (`/xyz` with three arguments) and separate (`/xyz/x`, `/xyz/y`, `/xyz/z`) OSC messages.

---

### Node: `INT OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `INT OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/path"`).
   - **Input Range:**
     - **`input_min`:** Minimum expected input value (default is `0.0`).
     - **`input_max`:** Maximum expected input value (default is `1.0`).
   - **Output Range:**
     - **`output_min`:** Minimum output value (integer, default is `0`).
     - **`output_max`:** Maximum output value (integer, default is `100`).
     - **`output_invert`:** Invert the output mapping if checked (default is `False`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with a single value.
   - **Data Mapping:**
     - The node maps the incoming value from the input range to the output range, optionally inverting the mapping.
   - **Outputs:**
     - **`VALUE`**: The remapped integer value.
     - **`RAW_VALUE`**: The raw input value received from the OSC message.

4. **Connect Outputs:**
   - Use the `VALUE` output to control integer parameters in your workflow.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and `path`.
- Adjust the input and output ranges to suit your application's needs.
- The node clamps and maps values to ensure they stay within the specified ranges.

---

### Node: `FLOAT OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `FLOAT OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/path"`).
   - **Input Range:**
     - **`input_min`:** Minimum expected input value (default is `0.0`).
     - **`input_max`:** Maximum expected input value (default is `1.0`).
   - **Output Range:**
     - **`output_min`:** Minimum output value (float, default is `0.0`).
     - **`output_max`:** Maximum output value (float, default is `100.0`).
     - **`output_invert`:** Invert the output mapping if checked (default is `False`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with a single value.
   - **Data Mapping:**
     - The node maps the incoming value from the input range to the output range, optionally inverting the mapping.
   - **Outputs:**
     - **`VALUE`**: The remapped float value.
     - **`RAW_VALUE`**: The raw input value received from the OSC message.

4. **Connect Outputs:**
   - Use the `VALUE` output to control float parameters in your workflow.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and `path`.
- Adjust the input and output ranges to suit your application's needs.
- The node clamps and maps values to ensure they stay within the specified ranges.

---

### Node: `SWITCH OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `SWITCH OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Paths:**
     - **`path1`** to **`path8`**: Set the OSC address paths for each of the 8 switches (defaults are `"/toggle1"` to `"/toggle8"`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified paths with a value indicating the switch state (`0` for OFF, `1` for ON).
   - **Outputs:**
     - **`SWITCH_1`** to **`SWITCH_8`**: Boolean outputs representing the state of each switch.

4. **Connect Outputs:**
   - Use the switch outputs to control boolean parameters or logic in your workflow.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and paths.
- Each switch corresponds to a separate OSC path, allowing independent control.

---

### Node: `TEXT Switch OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `TEXT Switch OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Texts:**
     - **`text1`** to **`text8`**: Enter up to 8 text options to switch between.
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/radio1"`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with a single integer argument representing the index of the text to select (`0` to `7`).
   - **Output:**
     - **`TEXT_OUTPUT`**: The selected text based on the received index.

4. **Connect Output:**
   - Use the `TEXT_OUTPUT` to feed into other nodes that accept string inputs.

**Note:**
- Ensure the index sent in the OSC message is within the valid range (`0` to `7`).
- If an invalid index is received, the node retains the previous output.

---

### Node: `IMAGE Switch OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `IMAGE Switch OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Inputs:**
     - **`image0`** to **`image3`**: Connect up to 4 image inputs to switch between.
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/radio1"`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with a single integer argument representing the index of the image to select (`0` to `3`).
   - **Output:**
     - **`IMAGE`**: The selected image based on the received index.

4. **Connect Output:**
   - Use the `IMAGE` output to feed into other nodes that accept image inputs.

**Note:**
- Ensure that the image inputs are properly connected and that the indices sent correspond to the available images.
- If an invalid index is received or the image at that index is not connected, the node outputs `None`.

---

### Node: `ANY Value OSC Control @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `ANY Value OSC Control @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server IP (`server_ip`):** Enter the IP address of the OSC server (default is your local IP address).
   - **Port (`port`):** Specify the port number on which the OSC server is listening (default is `8000`).
   - **Path (`path`):** Set the OSC address path to listen for messages (default is `"/path"`).
   - **Debug (`debug`):** Enable debug mode to print detailed logs (default is `False`).

3. **Use the Node:**
   - **Send OSC Messages:**
     - Send OSC messages to the specified `path` with a single argument of any type: integer, float, string, or boolean.
   - **Value Detection:**
     - The node detects the type of the received value and updates the corresponding output while resetting the others to default values.
       - If the value is an **integer**, it updates the **`INT`** output.
       - If the value is a **float**, it updates the **`FLOAT`** output.
       - If the value is a **string**, it updates the **`TEXT`** output.
       - If the value is a **boolean**, it updates the **`BOOL`** output.

4. **Outputs:**
   - **`INT`**: Outputs the integer value received (default is `0`).
   - **`FLOAT`**: Outputs the float value received (default is `0.0`).
   - **`TEXT`**: Outputs the string value received (default is an empty string `""`).
   - **`BOOL`**: Outputs the boolean value received (default is `False`).

5. **Connect Outputs:**
   - Use the appropriate output to feed into other nodes in your workflow based on the expected data type.

**Note:**
- Ensure your OSC client is sending messages to the correct `server_ip`, `port`, and `path`.
- Only one output will be updated at a time, corresponding to the type of the received value; the other outputs will reset to their default values.
- If the received value is of an unsupported type, the node will not update any outputs.
- This node is useful when you need to receive dynamic values of varying types over OSC without knowing the exact type in advance.

---

### Node: `OSC Control Settings @ vrch.ai` (vrch.ai/control/osc)

1. **Add the `OSC Control Settings @ vrch.ai` node to your ComfyUI workflow.**
   
2. **Configure the Node:**
   - **Server IP (`server_ip`):** Specify the IP address of the OSC server. By default, this is set to the local IP address of your machine.
   - **Port (`port`):** Set the port number on which the OSC server is listening. The default value is `8000`, but you can specify any valid port number between `0` and `65535`.
   - **Debug (`debug`):** Enable this option to activate debug mode, which will print detailed logs to help with troubleshooting. The default is `False`.

3. **Use the Node:**
   - This node initializes and configures the OSC server settings in your workflow. It does not actively send or receive OSC messages but serves as a central configuration point for OSC communication.
   - If `debug` is enabled, the node outputs debug information, including the server IP and port details, to the console for verification and troubleshooting.

4. **Outputs:**
   - **`SERVER_IP`**: Outputs the configured IP address for the OSC server as a string.
   - **`PORT`**: Outputs the configured port number for the OSC server as an integer.

5. **Connect Outputs:**
   - Use the `SERVER_IP` and `PORT` outputs to link this configuration to other OSC nodes in your workflow, ensuring that all nodes are using the same IP and port settings.

**Note:**  
- Ensure that the OSC client is configured to communicate with the specified `server_ip` and `port`.
- This node is useful for setting up a consistent OSC configuration across multiple nodes within a ComfyUI workflow, centralizing the IP and port details for easy management.
- When `debug` mode is active, it helps you monitor OSC activity by outputting server connection details to the console.

--- 