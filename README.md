# ComfyUI-Web-Viewer

Version: 1.0.0

This is a custom node collection for ComfyUI that provides a Web Viewer utility under the vrch.io category.

[Changelog](CHANGELOG.md)

## Installation

1. Copy this project folder into the `custom_nodes` directory of ComfyUI.
2. Install dependencies: `pip install -r requirements.txt`
3. Restart ComfyUI

## Usage

### Web Viewer by vrch.io (vrch.io/web)

1. Add the "Web Viewer by vrch.io" node to your ComfyUI workflow.
2. The node provides an input field for the URL and a button to open the web viewer.
3. You can customize the URL in the node's input field.
4. Click the "Open Web Viewer" button to open the specified URL in a new browser window.
5. You can also adjust the window size using the "window_width" and "window_height" inputs.

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)