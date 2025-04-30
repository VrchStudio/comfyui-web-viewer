### Node: `MIDI Device Loader @ vrch.ai` (vrch.ai/control/midi)

1. **Add the `MIDI Device Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **`device_id`**: Select the MIDI device ID to use. Default is empty (connects to first available device).
   - **`name`**: Displays the connected MIDI device name (read-only).
   - **`refresh_interval`**: Set the polling frequency in milliseconds (10–10000ms). Default is `100`.
   - **`debug`**: Enable to view detailed debug information in the console and display raw data. Default is `False`.
   - **`raw_data`**: Shows the raw MIDI state in JSON format (visible only when debug is enabled).

3. **Connecting a MIDI Device:**
   - Connect a compatible MIDI device to your computer before starting ComfyUI.
   - Ensure your browser supports the Web MIDI API (Chrome and Edge have the best support).
   - The node will automatically connect to the first available device if `device_id` is not specified.
   - To target a specific device, set the `device_id` field to the device’s ID and the node will reconnect if that device appears.

4. **Data Access:**
   - The node polls the connected MIDI device at the specified `refresh_interval`.
   - Incoming MIDI messages are parsed into CC (Control Change) and Note events.
   - CC and Note data are stored in arrays of length 128 (one slot per MIDI number).

5. **Node Outputs:**
   - **`RAW_DATA`**: Complete MIDI state in JSON format.
   - **`INT_CC_VALUES`**: Array of integer CC values (0–127).
   - **`FLOAT_CC_VALUES`**: Array of normalized CC values (0.0–1.0).
   - **`BOOLEAN_NOTE_VALUES`**: Array of booleans indicating note on (`True`) or off (`False`) for each MIDI note number.
   - **`INT_NOTE_VALUES`**: Array of integer note velocity values (0–127).

**Note:**
- Supported message types include Note On/Off, Control Change, Aftertouch, Program Change, Channel Pressure, and Pitch Bend.
- High-end MIDI controllers may send more message types; unsupported types are ignored by default.
- Multiple devices can be handled by adding multiple `MIDI Device Loader` nodes with different `device_id` settings.