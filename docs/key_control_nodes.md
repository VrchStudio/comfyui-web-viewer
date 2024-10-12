### Node: `INT Key Control by vrch.io` (vrch.io/control)

1. **Add the `INT Key Control by vrch.io` to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Minimum Value (`min_value`):** Set the minimum allowable integer value (integer between `-9999` and `9999`). Default is `0`.
   - **Maximum Value (`max_value`):** Set the maximum allowable integer value (integer between `-9999` and `9999`). Default is `100`.
   - **Step Size (`step_size`):** Set the increment/decrement value (integer between `1-10`). Default is `1`.
   - **Shortcut Key 1 (`shortcut_key1`):** Select a key from `F1` to `F12` to serve as the primary shortcut key. Default is `F2`.
   - **Shortcut Key 2 (`shortcut_key2`):** Choose between `"Down/Up"` or `"Left/Right"` to determine the direction keys. Default is `"Down/Up"`.
   - **Current Value (`current_value`):** Set the initial integer value within the specified range (integer between `-9999` and `9999`). Default is `50`.
3. **Control Integer Value:**
   - **Incrementing:**
     - Press and hold the selected `shortcut_key1` (e.g., `F2`).
     - While holding `shortcut_key1`, press `ArrowUp` or `ArrowRight` to increment.
     - The `current_value` will increase by `step_size` each time, up to the defined `max_value`.
   - **Decrementing:**
     - Press and hold the selected `shortcut_key1` (e.g., `F2`).
     - While holding `shortcut_key1`, press `ArrowDown` or `ArrowLeft` to decrement.
     - The `current_value` will decrease by `step_size` each time, down to the defined `min_value`.
4. **Display and Output:**
   - The current integer value is displayed within the node's UI.
   - Use the `INT` output to connect the integer value to other nodes in your workflow.

**Note:** 
- Ensure that the ComfyUI window/tab is focused when using keyboard shortcuts.
- Prevent browser-specific shortcuts from interfering with the node's functionality.
- Modified `min_value`, `max_value`, and `step_size` values persist across page reloads.
- The `current_value` will always stay within the defined `min_value` and `max_value` boundaries, regardless of user interactions.

---

### Node: `FLOAT Key Control by vrch.io` (vrch.io/control)

1. **Add the `FLOAT Key Control by vrch.io` to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Step Size (`step_size`):** Set the increment/decrement value (float between `0.01-0.10`). Default is `0.01`.
   - **Shortcut Key 1 (`shortcut_key1`):** Select a key from `F1` to `F12` to serve as the primary shortcut key. Default is `F1`.
   - **Shortcut Key 2 (`shortcut_key2`):** Choose between `"Down/Up"` or `"Left/Right"` to determine the direction keys. Default is `"Down/Up"`.
   - **Current Value (`current_value`):** Set the initial floating-point value (between `0.0-1.0`). Default is `0.50`.
3. **Control Floating-Point Value:**
   - **Incrementing:**
     - Press and hold the selected `shortcut_key1` (e.g., `F1`).
     - While holding `shortcut_key1`, press the corresponding direction key based on `shortcut_key2`:
       - If `"Down/Up"`: Press `ArrowUp` to increment.
       - If `"Left/Right"`: Press `ArrowLeft` to increment.
     - The `current_value` will increase by `step_size` each time, up to a maximum of `1.0`.
   - **Decrementing:**
     - Press and hold the selected `shortcut_key1` (e.g., `F1`).
     - While holding `shortcut_key1`, press the corresponding direction key based on `shortcut_key2`:
       - If `"Down/Up"`: Press `ArrowDown` to decrement.
       - If `"Left/Right"`: Press `ArrowRight` to decrement.
     - The `current_value` will decrease by `step_size` each time, down to a minimum of `0.0`.
4. **Display and Output:**
   - The current floating-point value is displayed within the node's UI.
   - Use the `FLOAT` output to connect the floating-point value to other nodes in your workflow.

**Note:** Ensure that the ComfyUI window/tab is focused when using keyboard shortcuts. Prevent browser-specific shortcuts from interfering with the node's functionality.

---

### Node: `BOOLEAN Key Control by vrch.io` (vrch.io/control)

1. **Add the `BOOLEAN Key Control by vrch.io` to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Shortcut Key (`shortcut_key`):** Select a key from `F1` to `F12` to serve as the toggle shortcut. Default is `F1`.
   - **Current Value (`current_value`):** Set the initial boolean value (`True`/`False`). Default is `False`.
3. **Toggle Boolean Value:**
   - **Using Shortcut Key:**
     - Press the selected `shortcut_key` (e.g., `F1`) to toggle the `current_value` between `True` and `False`.
     - Each press of the `shortcut_key` will switch the state.
4. **Display and Output:**
   - The current boolean value is displayed within the node's UI.
   - Use the `BOOL` output to connect the boolean value to other nodes in your workflow.

**Note:** Ensure that the ComfyUI window/tab is focused when using the shortcut key. Prevent browser-specific shortcuts from interfering with the node's functionality.

---

### Node: `TEXT Key Control by vrch.io` (vrch.io/control)

1. **Add the `TEXT Key Control by vrch.io` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Text Inputs (`text1` - `text8`):** Enter text for each option. Supports multiple lines. Defaults are empty (`""`).
   - **Jump Empty Option (`skip_empty_option`):** Enable or disable skipping empty text options when cycling. Default is `True`.
   - **Shortcut Key (`shortcut_key`):** Select a function key (`F1` to `F12`) to cycle through texts. Default is `F2`.
   - **Current Value (`current_value`):** Set the initial selection (`1` to `8`). Default is `1`.
3. **Cycle Through Text Options:**
   - **Using Shortcut Key:**
     - Press the selected `shortcut_key` (e.g., `F2`) to cycle through the text options.
     - **With `skip_empty_option` Enabled (`True`):**
       - Skips any empty `text` inputs.
     - **With `skip_empty_option` Disabled (`False`):**
       - Cycles through all texts, including empty ones.
4. **Display and Output:**
   - **Display:**
     - Shows `Value: X`, where `X` is the current selection (`1` to `8`).
   - **Output:**
     - **Type:** `STRING`
     - Outputs the selected text based on `current_value`. Connect to other nodes as needed.

**Note:**  
Ensure the ComfyUI window/tab is focused when using the shortcut key to prevent conflicts with browser shortcuts.