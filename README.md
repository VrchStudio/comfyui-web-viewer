# ComfyUI-Web-Viewer

This is a custom node collection for ComfyUI that provides various utilities under the vrch.io category.

## Project Structure

- `nodes/`: Contains all custom node implementations
- `web/`: Web-related files for the Web Viewer node
- `workflow/`: Example workflow JSON files
- `__init__.py`: Node registration and initialization

## Installation

1. Copy this project folder into the `custom_nodes` directory of ComfyUI.
2. Install dependencies: `pip install -r requirements.txt`
3. Restart ComfyUI

## Usage

### Web Viewer by vrch.io (vrch.io/web)

1. Add the "Web Viewer by vrch.io" node to your ComfyUI workflow.
2. Connect an image output to this node.
3. After running the workflow, check the console for the Web viewer URL.
4. Open the URL in a web browser to view the generated image.

### Image Saver by vrch.io (vrch.io/image)

1. Add the "Image Saver by vrch.io" node to your workflow.
2. Connect an image output to this node.
3. Specify the save path in the node settings.
4. Run the workflow to save the image.

### Get Audio Genres by vrch.io (vrch.io/audio)

1. Add the "Get Audio Genres by vrch.io" node to your workflow.
2. Specify the audio file path in the node settings.
3. Run the workflow to detect audio genres.
4. The detected genres will be output as a string.

## Example Workflow

An example workflow JSON file is provided in the `workflow` directory. You can use this as a starting point or reference for creating your own workflows with these custom nodes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.