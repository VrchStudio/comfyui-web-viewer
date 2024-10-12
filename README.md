# ComfyUI-Web-Viewer

This is a custom node collection for ComfyUI that provides a Web Viewer utility under the vrch.ai category.

## Changelog

see [CHANGELOG](CHANGELOG.md)

## Installation

1. Copy this project folder into the `custom_nodes` directory of ComfyUI.
2. Install dependencies: `pip install -r requirements.txt`
3. Restart ComfyUI

## Usage

### `Web Viewer Nodes`

see [Usage of Web Viewer nodes](./docs/web_viewer_nodes.md)

### `OSC Control Nodes`

see [Usage of OSC Control nodes](./docs/osc_control_nodes.md)

### `Key Control Nodes`

see [Usage of Key Control nodes](./docs/key_control_nodes.md)

### `Audio Nodes`

see [Usage of Audio nodes](./docs/audio_nodes.md)

### `Image Nodes`

see [Usage of Image nodes](./docs/image_nodes.md)

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

Created and maintained by vrch.io team.

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)