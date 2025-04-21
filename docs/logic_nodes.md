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
