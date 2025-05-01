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

### Node: `Xbox Controller Mapper @ vrch.ai` (vrch.ai/control/gamepad)  
  
1. **Overview:**  
   - The `Xbox Controller Mapper @ vrch.ai` node provides optimized mapping for Xbox controllers.  
   - It takes raw gamepad data from the `Gamepad Loader @ vrch.ai` node and maps it to standard Xbox controller inputs.  
   - This makes it easier to work with Xbox controllers by providing named outputs for each button and control.  
  
2. **Setup:**  
   - First add a `Gamepad Loader @ vrch.ai` node to your workflow.  
   - Then add the `Xbox Controller Mapper @ vrch.ai` node.  
   - Connect the `RAW_DATA` output from the Gamepad Loader to the `raw_data` input of the Xbox Controller Mapper.  
  
3. **Inputs:**  
   - **`raw_data`**: JSON data from the `Gamepad Loader @ vrch.ai` node.  
   - **`debug`**: Enable to view detailed debug information in the console. Default is `False`.  
  
4. **Outputs:**  
   - **Analog Controls:**  
     - **`LEFT_STICK`**: Array containing X and Y values for the left analog stick `[x, y]` (values range from -1.0 to 1.0).  
     - **`RIGHT_STICK`**: Array containing X and Y values for the right analog stick `[x, y]` (values range from -1.0 to 1.0).  
     - **`LEFT_TRIGGER`**: Value for the left trigger (LT) (values range from 0.0 to 1.0).  
     - **`RIGHT_TRIGGER`**: Value for the right trigger (RT) (values range from 0.0 to 1.0).  
     
   - **Face Buttons:**  
     - **`A_BUTTON`**: Boolean state of the A button (bottom face button).  
     - **`B_BUTTON`**: Boolean state of the B button (right face button).  
     - **`X_BUTTON`**: Boolean state of the X button (left face button).  
     - **`Y_BUTTON`**: Boolean state of the Y button (top face button).  
     
   - **Shoulder Buttons:**  
     - **`LB_BUTTON`**: Boolean state of the left bumper (LB).  
     - **`RB_BUTTON`**: Boolean state of the right bumper (RB).  
     
   - **Center Buttons:**  
     - **`VIEW_BUTTON`**: Boolean state of the View button (formerly Back).  
     - **`MENU_BUTTON`**: Boolean state of the Menu button (formerly Start).  
     - **`XBOX_BUTTON`**: Boolean state of the Xbox logo button.  
     
   - **Stick Presses:**  
     - **`LEFT_STICK_PRESS`**: Boolean state of the left stick press (L3).  
     - **`RIGHT_STICK_PRESS`**: Boolean state of the right stick press (R3).  
     
   - **D-Pad:**  
     - **`DPAD_UP`**: Boolean state of the D-pad up direction.  
     - **`DPAD_DOWN`**: Boolean state of the D-pad down direction.  
     - **`DPAD_LEFT`**: Boolean state of the D-pad left direction.  
     - **`DPAD_RIGHT`**: Boolean state of the D-pad right direction.  
     
   - **Complete Data:**  
     - **`FULL_MAPPING`**: Complete mapping of all controller inputs as a JSON object.  
  
5. **Usage Examples:**  
   - Use `A_BUTTON` to trigger actions in your workflow.  
   - Use `LEFT_STICK` to control position or movement parameters.  
   - Use `RIGHT_TRIGGER` to control intensity or pressure-sensitive parameters.  
  
**Note:**  
- This node is specifically optimized for Xbox controllers and follows the standard Xbox controller button layout.  
- The button mapping is based on the standard Web Gamepad API implementation for Xbox controllers.  
- If your controller has a different layout, you may need to adjust your workflow accordingly.