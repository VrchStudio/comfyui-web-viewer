# Tutorial 007: Unleash Real-Time Avatar Control with Your Native Gamepad!

## TL;DR

Ready for some serious fun? 🚀 This guide shows how to integrate *native* gamepad support directly into ComfyUI in real time using the `ComfyUI Web Viewer` custom nodes, unlocking a new world of interactive possibilities! 🎮

*   **Native Gamepad Support:** Use `ComfyUI Web Viewer` nodes (`Gamepad Loader @ vrch.ai`, `Xbox Controller Mapper @ vrch.ai`) to connect your gamepad directly via the browser's API – no external apps needed.
*   **Interactive Control:** Control live portraits, animations, or *any* workflow parameter in real-time using your favorite controller's joysticks and buttons.
*   **Enhanced Playfulness:** Make your ComfyUI workflows more dynamic and fun by adding direct, physical input for controlling expressions, movements, and more.

![](../example_workflows/example_gamepad_nodes_002_live_portrait.png)

## Preparations

1.  **Install `ComfyUI Web Viewer` custom node**:
    *   Method 1: Search for `ComfyUI Web Viewer` in ComfyUI Manager.
    *   Method 2: Install from GitHub: [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)
2.  **Install `Advanced Live Portrait` custom node**:
    *   Method 1: Search for `ComfyUI-AdvancedLivePortrait` in ComfyUI Manager.
    *   Method 2: Install from GitHub: [https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait](https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait)
3.  **Download `Workflow Example: Live Portrait + Native Gamepad` workflow**:
    *   Download it from here: [example_gamepad_nodes_002_live_portrait.json](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_gamepad_nodes_002_live_portrait.json)
4.  **Connect Your Gamepad**:
    *   Connect a compatible gamepad (e.g., Xbox controller) to your computer via USB or Bluetooth. Ensure your browser recognizes it. Most modern browsers (Chrome, Edge) have good Gamepad API support.

## How to Play

### Run Workflow in ComfyUI

1.  **Load Workflow**:
    *   In ComfyUI, load the file [example_gamepad_nodes_002_live_portrait.json](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_gamepad_nodes_002_live_portrait.json).
2.  **Check Gamepad Connection**:
    *   Locate the `Gamepad Loader @ vrch.ai` node in the workflow.
    *   Ensure your gamepad is detected. The `name` field should show your gamepad's identifier. If not, try pressing some buttons on the gamepad. You might need to adjust the `index` if you have multiple controllers connected.
3.  **Select Portrait Image**:
    *   Locate the `Load Image` node (or similar) feeding into the `Advanced Live Portrait` setup.
    *   You could use [sample_pic_01_woman_head.png](https://raw.githubusercontent.com/VrchStudio/comfyui-web-viewer/refs/heads/main/assets/images/sample_pic_01_woman_head.png) as an example portrait to control.
4.  **Enable Auto Queue**:
    *   Enable `Extra options` -> `Auto Queue`. Set it to `instant` or a suitable mode for real-time updates.
5.  **Run Workflow**:
    *   Press the `Queue Prompt` button to start executing the workflow.
    *   Optionally, use a `Web Viewer` node (like `VrchImageWebSocketWebViewerNode` included in the example) and click its `[Open Web Viewer]` button to view the portrait in a separate, cleaner window.
6.  **Use Your Gamepad**:
    *   Grab your gamepad and enjoy controlling the portrait with it!

### Cheat Code (Based on Example Workflow)

```
Head Move (pitch/yaw) --- Left Stick
Head Move (rotate/roll) - Left Stick + A
Pupil Move -------------- Right Stick
Smile ------------------- Left Trigger + Right Bumper
Wink -------------------- Left Trigger + Y
Blink ------------------- Right Trigger + Left Bumper
Eyebrow ----------------- Left Trigger + X
Oral - aaa -------------- Right Trigger + Pad Left
Oral - eee -------------- Right Trigger + Pad Up
Oral - woo -------------- Right Trigger + Pad Right
```

*Note: This mapping is defined within the example workflow using logic nodes (`Float Remap`, `Boolean Logic`, etc.) connected to the outputs of the `Xbox Controller Mapper @ vrch.ai` node. You can customize these connections to change the controls.*

### Advanced Tips

1.  You can modify the connections between the `Xbox Controller Mapper @ vrch.ai` node and the `Advanced Live Portrait` inputs (via remap/logic nodes) to customize the control scheme entirely.
2.  Explore the different outputs of the `Gamepad Loader @ vrch.ai` and `Xbox Controller Mapper @ vrch.ai` nodes to access various button states (boolean, integer, float) and stick/trigger values. See the [Gamepad Nodes Documentation](./gamepad_nodes.md) for details.

## Materials

-   ComfyUI workflow: [example_gamepad_nodes_002_live_portrait.json](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_gamepad_nodes_002_live_portrait.json)
-   Sample portrait picture: [sample_pic_01_woman_head.png](https://raw.githubusercontent.com/VrchStudio/comfyui-web-viewer/refs/heads/main/assets/images/sample_pic_01_woman_head.png)
