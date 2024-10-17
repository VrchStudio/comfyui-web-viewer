# ComfyUI Web Viewer

This is a custom node collection for ComfyUI that provides a Web Viewer utility under the [vrch.ai](https://vrch.ai) category.

It's a framework for real-time AI generated interactive experience. Turn your ComfyUI workflow into interactive media art.

![](./assets/images/web_viewer_example_001.gif)

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
   or if you use the portable install, run this in `ComfyUI_windows_portable` folder:
   ```
   python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\comfyui-web-viewer\requirements.txt
   ```
3. Restart ComfyUI

## How to Use

### `Web Viewer Nodes`

- Documentation: [Usage of Web Viewer nodes](./docs/web_viewer_nodes.md)
- Example workflows: 
  - [Workflow Example: Image Web Viewer node](./workflows/example_web_viewer_001_image_web_viewer)

### `OSC Control Nodes`

- Documentation: [Usage of OSC Control nodes](./docs/osc_control_nodes.md)
- TouchOSC Control Panel:
  - [comfyui_osc_control.tosc](./assets/touchosc/comfyui_osc_control.tosc)
- Example workflows:
  - [Workflow Example: OSC Control Nodes](./workflows/example_osc_control_001_basic.json)
  - (TBA) [Workflow Example: Live Portrait]()
  - (TBA) [Workflow Example: IC-Light]()

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
- Example workflow: n/a

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


## License

[MIT License](LICENSE)