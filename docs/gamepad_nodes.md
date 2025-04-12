### Node: `Gamepad Loader @ vrch.ai` (vrch.ai/control/gamepad)

1. **Add the `Gamepad Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Gamepad Selection:**
     - **`index`**: Select the gamepad index (0-7) to use. Default is `0`.
     - **`name`**: Displays the detected gamepad's name (read-only).
   - **Performance Settings:**
     - **`refresh_interval`**: Set the data polling frequency in milliseconds (10-10000ms). Default is `100`.
   - **Debug Options:**
     - **`debug`**: Enable to view detailed debug information in the console and display raw data. Default is `False`.
     - **`raw_data`**: Shows the raw gamepad data in JSON format (only visible when debug is enabled).

3. **Connecting a Gamepad:**
   - Connect a compatible gamepad to your computer before starting ComfyUI.
   - Most USB and Bluetooth gamepads compatible with your browser should work.
   - Press buttons on your gamepad to ensure it's detected by the browser.

4. **Data Access:**
   - The node continuously polls the connected gamepad at the specified refresh interval.
   - It extracts and processes the gamepad's buttons and axes data.
   - When a gamepad is detected at the specified index, its identifier will appear in the `name` field.

5. **Node Outputs:**
   - **`RAW_DATA`**: Complete gamepad data in JSON format.
   - **`LEFT_STICK`**: Array containing X and Y values for the left analog stick `[x, y]` (values range from -1.0 to 1.0).
   - **`RIGHT_STICK`**: Array containing X and Y values for the right analog stick `[x, y]` (values range from -1.0 to 1.0).
   - **`BOOLEAN_BUTTONS`**: Array of boolean values indicating if each button is pressed (`True`) or not (`False`).
   - **`INT_BUTTONS`**: Array of integer values (1 for pressed, 0 for not pressed).
   - **`FLOAT_BUTTONS`**: Array of float values representing the pressure sensitivity of each button (0.0-1.0).

**Note:**
- Gamepad support varies by browser. Chrome and Edge typically provide the best compatibility.
- The number of buttons and axes depends on your specific gamepad model.
- Standard gamepads typically follow this mapping:
  - Buttons 0-3: Face buttons (A/B/X/Y or ×/○/□/△)
  - Buttons 4-5: Shoulder buttons (LB/RB)
  - Buttons 6-7: Triggers (LT/RT)
  - Buttons 8-9: Back/Select and Start buttons
  - Buttons 10-11: Analog stick press buttons (L3/R3)
  - Buttons 12-15: D-pad (Up/Down/Left/Right)
  - Axes 0-1: Left analog stick (X, Y)
  - Axes 2-3: Right analog stick (X, Y)
