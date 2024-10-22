# ComfyUI Web Viewer
 
A custom node collection for ComfyUI under the [vrch.ai](https://vrch.ai) category, providing a Web Viewer utility and a framework for real-time AI-generated interactive art.

**Features:**  
- Real-time interaction and AI generation.
- Easily accessible on any device with a web browser.
- Supports interactive input methods such as keyboard, OSC control, and sound input.

<video src="https://github.com/user-attachments/assets/cdac0293-64ce-4b74-95a8-d4dcce2300d2" controls="controls" style="max-width: 100%;">
</video>

## Changelog

see [CHANGELOG](CHANGELOG.md)

## Installation

### Method 1: Auto Installation (Recommended)

Simply search for `ComfyUI Web Viewer` in ComfyUI Manager and install it directly.

### Method 2: Manual Installation
1. Clone this repo into the `custom_nodes` directory of ComfyUI
2. Install dependencies: 
   ```
   pip install -r requirements.txt
   ``` 
   or if you use the `windows` portable install, run this in `ComfyUI_windows_portable` folder:
   ```
   python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\comfyui-web-viewer\requirements.txt
   ```
3. Restart ComfyUI

## How to Use

### `Web Viewer Nodes`

![](./assets/images/web_viewer_example_001.gif)

- Documentation: [Usage of Web Viewer nodes](./docs/web_viewer_nodes.md)
- Example workflows: 
  - [Workflow Example: Image Web Viewer node](./workflows/example_web_viewer_001_image_web_viewer)

### `OSC Control Nodes`

- Documentation: [Usage of OSC Control nodes](./docs/osc_control_nodes.md)
- TouchOSC Control Panel:
  - [comfyui_osc_control.tosc](./assets/touchosc/comfyui_osc_control.tosc)
- Example workflows:
  - [Workflow Example: OSC Control Nodes](./workflows/example_osc_control_001_basic.json)
  - [Workflow Example: Live Portrait + Gamepad](./workflows/example_osc_control_002_live_portrait_with_gamepad.json)
  - [Workflow Example: IC-Light](./workflows/example_osc_control_003_ic-light.png)

### `Key Control Nodes`

- Documentation: [Usage of Key Control nodes](./docs/key_control_nodes.md)
- Example workflows:
  - [Workflow Example: Key Control Nodes](./workflows/example_key_control_001_basic.json)

### `Audio Nodes`

- Documentation: [Usage of Audio nodes](./docs/audio_nodes.md)
- Example workflows:
  - [Workflow Example: Audio Recorder Node](./workflows/example_audio_nodes_001_audio_recorder.json)

### `Image Nodes`

- Documentation: [Usage of Image nodes](./docs/image_nodes.md)
- Example workflows: n/a

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

Created and maintained by the [vrch.io](https://vrch.io) team.

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact Us

For any inquiries, you can contact us at [hi@vrch.io](mailto:hi@vrch.io).

## License

[MIT License](LICENSE)