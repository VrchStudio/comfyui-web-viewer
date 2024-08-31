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

1. Add the `Web Viewer by vrch.io` node to your ComfyUI workflow.
2. The node provides an input field for the URL and a button to open the web viewer.
3. You can customize the URL in the node's input field.
4. Click the "Open Web Viewer" button to open the specified URL in a new browser window.
5. You can also adjust the window size using the "window_width" and "window_height" inputs.
   
### Node: `Audio Recorder by vrch.io` (vrch.io/audio)


1. Add the `Audio Recorder by vrch.io` node to your ComfyUI workflow.
2. Configure the node:
   - `record_mode`: Choose between "press_and_hold" or "start_and_stop".
   - `record_duration_max`: Set maximum recording duration (1-60 seconds).
   - `loop`: Enable/disable loop recording.
   - `loop_interval`: Set interval between loop recordings (if loop is enabled).
3. Record audio:
   - "Press and Hold" mode: Hold the button to record, release to stop.
   - "Start and Stop" mode: Click "START" to begin, "STOP" to end.
   - In loop mode (Start and Stop): Click "START" to begin loop, "STOP LOOPING" to end.
4. The recorded audio will appear in the `audioUI` widget for playback.
5. Use the `AUDIO` output to connect the recorded audio to other nodes.

Note: A countdown displays for the last 10 seconds of recording.

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