# ComfyUI-Web-Viewer

This is a custom node collection for ComfyUI that provides a Web Viewer utility under the vrch.io category.

## Changelog

[Changelog](CHANGELOG.md)

## Installation

1. Copy this project folder into the `custom_nodes` directory of ComfyUI.
2. Install dependencies: `pip install -r requirements.txt`
3. Restart ComfyUI

## Usage

### Node: `Web Viewer by vrch.io` (vrch.io/web)

1. **Add the `Web Viewer by vrch.io` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Page Type:** Select the type of page to open from `image`, `audio`, or `depthmap`.
   - **Server:** Set the ComfyUI server's domain name (default is `127.0.0.1:8188`).
   - **SSL:** Choose whether the connection should use SSL (if `True`, it will use `https`, otherwise `http`).
   - **File Name:** Enter the file name to be used in the web viewer (e.g., `web_viewer_image.jpeg`).
   - **Path:** Enter the path for the resource (default is `web_viewer`).
   - **Window Dimensions:**
     - `window_width`: Set the width of the web viewer window.
     - `window_height`: Set the height of the web viewer window.
   - **Show URL:** Toggle whether to display the constructed URL in the interface. If enabled, the `url` input field will become visible and show the constructed URL based on the input parameters.
   - **URL Input:** This field is automatically updated with the constructed URL based on the inputs provided (`page`, `server`, `ssl`, `file`, and `path`). You can toggle its visibility using the `show_url` input.
3. **Open Web Viewer:**
   - Click the "Open Web Viewer" button to launch the specified URL in a new browser window based on the input parameters.

**Note**:
- Ensure that the URL entered or constructed is valid and accessible. The web viewer window will open based on the specified dimensions.
- The "Show URL" option allows you to see the dynamically constructed URL if you want to inspect or copy it.

---

### Node: `Audio Recorder by vrch.io` (vrch.io/audio)

1. **Add the `Audio Recorder by vrch.io` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Record Mode (`record_mode`):**
     - **"Press and Hold":**
       - **Button Control:** Hold the record button to start recording; release to stop.
       - **Shortcut Control:** Press and hold the selected shortcut key to start recording; release to stop.
     - **"Start and Stop":**
       - **Button Control:** Click "START" to begin recording; click "STOP" to end.
       - **Shortcut Control:** Press the selected shortcut key once to start recording; press again to stop.
   - **Recording Parameters:**
     - `record_duration_max`: Set the maximum recording duration (1-60 seconds).
     - `loop`: Enable or disable loop recording.
     - `loop_interval`: Set the interval between loop recordings (if loop is enabled).
   - **Shortcut Configuration:**
     - `shortcut`: Enable or disable the keyboard shortcut for controlling recording.
     - `shortcut_key`: Select the desired shortcut key (e.g., F1, F2, ..., F12) for controlling the recording.
3. **Record Audio:**
   - **"Press and Hold" Mode:**
     - **Button Control:** Hold the record button to record; release to stop.
     - **Shortcut Control:** Press and hold the selected shortcut key to record; release to stop.
   - **"Start and Stop" Mode:**
     - **Button Control:** Click "START" to begin recording; click "STOP" to end.
     - **Shortcut Control:** Press the selected shortcut key once to start recording; press again to stop.
   - **Loop Mode (Applicable in "Start and Stop" Mode):**
     - Click "START" to begin loop recording.
     - Click "STOP LOOPING" to end loop recording.
4. **Playback and Output:**
   - The recorded audio will appear in the `audioUI` widget for playback.
   - Use the `AUDIO` output to connect the recorded audio to other nodes in your workflow.

**Note**: A countdown displays during the last 10 seconds of recording to inform you of the remaining time.

---

### Node: `Get Music Genres by vrch.io` (vrch.io/audio)

1. **Add the `Get Music Genres by vrch.io` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Audio Input (`audio`):** Provide an `AUDIO` input from a previous node in the workflow, such as an audio recorder or a file loader.
3. **Analyze Audio:**
   - The node processes the input audio to predict its music genre(s).
   - It uses a pre-trained model to analyze the waveform and outputs the predicted genres along with their probabilities.
4. **View Results:**
   - The predicted genres and their associated probabilities are displayed in a text output format.
   - The results indicate the likelihood of the audio belonging to specific music genres.
5. **Connect to Other Nodes:**
   - Use the `AUDIO` output to pass the analyzed audio to other nodes for further processing or playback.
   - Use the `STRING` output to connect the genre predictions to nodes that require textual input or visualization.

**Note:** Ensure that the input audio is properly preprocessed and normalized for accurate genre prediction. The node's output is influenced by the quality and clarity of the input audio.

---

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

---


## Version Update

This project uses `bump2version` for version management. To update the version:

1. Ensure you have `bump2version` installed:
   ```bash
   pip install bump2version
   ```
2. To update the version, run:
   ```bash
   python update_version.py [major|minor|patch]
   ```
   Replace `[major|minor|patch]` with the part of the version you want to increment.
3. This will automatically:
   - Update the version number in `__init__.py`
   - Update the CHANGELOG.md file
   - Create a new git commit and tag (if you're using git)
4. After running the script, review and update the CHANGELOG.md file with details about the new version's changes.
   - Note: make sure you've put changes in `Unreleased` section manually

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)