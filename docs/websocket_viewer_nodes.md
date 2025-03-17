### Node: `IMAGE WebSocket Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `IMAGE WebSocket Web Viewer @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`images`**: Connect the image(s) you wish to display in the WebSocket-based web viewer.
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to differentiate WebSocket connections.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Image Format:**
     - **`format`**: Choose the image format for transmission, supporting **PNG** and **JPEG** (default is **JPEG**).
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **1280**).
     - **`window_height`**: Set the height of the web viewer window (default is **960**).
   - **Show URL:**
     - **`show_url`**: Toggle the display of the constructed URL in the interface. When enabled, the **`url`** field becomes visible.
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.
   - **Extra Parameters:**
     - **`extra_params`**: The extra parameters for Image WebSocket Web Viewer, see [websocket_viewer_nodes_extra_params.md](./websocket_viewer_nodes_extra_params.md)
   - **URL Input:**
     - **`url`**: This field is automatically updated with a constructed URL based on your inputs (server, channel, extra parameters, etc.). You can control its visibility with the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the generated URL in a new browser window, where your image will be displayed in real time via the WebSocket connection.

**Notes:**
- Make sure that the server address and configuration are correct and that the server is accessible.
- This node uses the WebSocket protocol to transmit image data in real time to the specified channel; ensure your client browser supports WebSocket connections.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the image transmission process and troubleshoot any issues.