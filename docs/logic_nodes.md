### Node: `INT Remap @ vrch.ai` (vrch.ai/logic)

1. **Add the `INT Remap @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Optional Input:**
     - **`input`**: The integer value to remap. Connect an INT input or leave unconnected for the default.
   - **Required Parameters:**
     - **`input_min`**: Minimum of the input range (default: 0).
     - **`input_max`**: Maximum of the input range (default: 1).
     - **`output_min`**: Minimum of the output range (default: 0).
     - **`output_max`**: Maximum of the output range (default: 100).
     - **`output_invert`**: Toggle to invert the mapping (default: False).
     - **`output_default`**: Default output if mapping fails (default: 0).

3. **Remapping Behavior:**
   - Ensures `input_min <= input_max` and `output_min <= output_max`, otherwise raises an error.
   - Maps the input proportionally from the input range to the output range.
   - Clamps the result within `[output_min, output_max]` and casts to INT.
   - On any exception, outputs `output_default`.

4. **Node Output:**
   - **Output (INT):** The remapped integer value.

---

### Node: `FLOAT Remap @ vrch.ai` (vrch.ai/logic)

1. **Add the `FLOAT Remap @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Optional Input:**
     - **`input`**: The float value to remap. Connect a FLOAT input or leave unconnected for the default.
   - **Required Parameters:**
     - **`input_min`**: Minimum of the input range (default: 0.0).
     - **`input_max`**: Maximum of the input range (default: 1.0).
     - **`output_min`**: Minimum of the output range (default: 0.0).
     - **`output_max`**: Maximum of the output range (default: 100.0).
     - **`output_invert`**: Toggle to invert the mapping (default: False).
     - **`output_default`**: Default output if mapping fails (default: 0.0).

3. **Remapping Behavior:**
   - Validates ranges (`input_min <= input_max` and `output_min <= output_max`).
   - Maps the input proportionally, clamps to `[output_min, output_max]`.
   - Returns a FLOAT. On error, outputs `output_default`.

4. **Node Output:**
   - **Output (FLOAT):** The remapped float value.

---

### Node: `Trigger Toggle @ vrch.ai` (vrch.ai/logic)

1. **Add the `Trigger Toggle @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Optional Input:**
     - **`trigger`**: BOOLEAN trigger input; toggles state when True.
   - **Required Parameters:**
     - **`initial_state`**: Starting boolean state (default: False).
     - **`debug`**: Enable console logging of transitions (default: False).

3. **Toggle Behavior:**
   - If `initial_state` changes, resets the internal state accordingly.
   - On each True `trigger` event, flips the current state.
   - If `debug` is enabled, prints trigger, initial, and current states.

4. **Node Output:**
   - **Output (BOOLEAN):** The current toggle state.
   - **JSON (JSON):** A JSON object containing `trigger`, `initial_state`, and `current_state`.

5. **Visual Indicators:**
   - Displays a non‑clickable circular indicator in the UI reflecting the current state.

---

### Node: `Trigger Toggle x4 @ vrch.ai` (vrch.ai/logic)

1. **Add the `Trigger Toggle x4 @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Optional Inputs:**
     - **`trigger1`**, **`trigger2`**, **`trigger3`**, **`trigger4`**: Four BOOLEAN triggers.
   - **Required Parameters:**
     - **`initial_state1`** … **`initial_state4`**: Four starting states (default: False).
     - **`debug`**: Enable console logging (default: False).

3. **Toggle Behavior:**
   - Resets each channel when its initial state changes.
   - Toggles individual channel states on corresponding triggers.
   - Builds a JSON summary of all four channels.
   - If `debug` is enabled, prints the JSON summary.

4. **Node Outputs:**
   - **Output1–Output4 (BOOLEAN):** Current states for each channel.
   - **JSON (JSON):** JSON object grouping triggers, initial, and current states for all channels.

5. **Visual Indicators:**
   - Renders four non‑clickable circular indicators in the UI, one per channel, showing each current state.

---

### Node: `Trigger Toggle x8 @ vrch.ai` (vrch.ai/logic)

1. **Add the `Trigger Toggle x8 @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Optional Inputs:**
     - **`trigger1` … `trigger8`**: Eight BOOLEAN triggers.
   - **Required Parameters:**
     - **`initial_state1` … `initial_state8`**: Eight starting states (default: False).
     - **`debug`**: Enable console logging (default: False).

3. **Toggle Behavior:**
   - Resets each channel on initial state change.
   - Toggles individual states on corresponding triggers.
   - Builds a JSON summary of all eight channels.
   - If `debug` is enabled, prints the JSON summary.

4. **Node Outputs:**
   - **Output1–Output8 (BOOLEAN):** Current states for each channel.
   - **JSON (JSON):** JSON object grouping triggers, initial, and current states for all channels.

5. **Visual Indicators:**
   - Renders eight non‑clickable circular indicators in the UI, one per channel, showing each current state.

---

### Node: `Delay @ vrch.ai` (vrch.ai/logic)

1. **Add the `Delay @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Input:**
     - **`any_input`**: Connect any type of input that you want to delay.
   - **Parameters:**
     - **`delay_ms`**: Delay period in milliseconds (integer, default is `0`, range `0` to `10000`).
     - **`debug`**: Enable debug mode to print detailed logs (default is `False`).

3. **Delay Behavior:**
   - The node delays the passing of its input by the specified `delay_ms` value.
   - Uses `time.sleep()` to synchronously pause the workflow for the specified duration.
   - After the delay completes, it passes the original input to the output.

4. **Node Output:**
   - **`ANY_OUTPUT`**: The delayed input (same type and value as `any_input`).

**Note:**
- **Blocking Behavior**: The node uses `time.sleep` to synchronously pause the workflow. Use reasonable delay periods to avoid making the interface unresponsive.
- **Debug Mode**: When enabled, prints messages about the delay process.
- **Error Handling**: If any exception occurs during the delay, the node will log the error if debug is enabled, but will still attempt to output the input value.
- **Use Cases**: Useful for introducing timing delays in animations, creating sequential effects, or synchronizing operations that need specific timing.

---

### Node: `QR Code Generator @ vrch.ai` (vrch.ai/logic)

1. **Add the `QR Code Generator @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Required Parameters:**
     - **`text`**: The text string to encode into a QR code (default: "Hello, World!"). Supports multiline text input.
     - **`size`**: The size of the generated QR code image in pixels (default: 256, range: 64-1024, step: 32).
     - **`error_correction`**: Error correction level - "L", "M", "Q", "H" (default: "M").
     - **`border`**: White border size around the QR code (default: 4, range: 0-20).
     - **`debug`**: Enable debug logging (default: False).

3. **QR Code Generation:**
   - Uses Python's `qrcode` library for backend generation.
   - Automatically regenerates when any parameter changes.
   - Converts output to ComfyUI IMAGE tensor format.

4. **Node Output:**
   - **QR_CODE (IMAGE):** The generated QR code as a ComfyUI IMAGE tensor.

5. **Library Dependency:**
   - Requires `qrcode[pil]` Python package: `pip install qrcode[pil]`
   - Creates placeholder image with warning message if library is missing.

**Note:**
- **Error Correction Levels**: L (~7%), M (~15%), Q (~25%), H (~30%) - higher levels provide better reliability.
- **Debug Mode**: When enabled, prints generation details to Python console.
- **Use Cases**: Generate QR codes for URLs, contact info, or text messages that can be integrated with other image processing workflows.
