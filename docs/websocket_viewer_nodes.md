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

---

### Node: `IMAGE WebSocket Channel Loader @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `IMAGE WebSocket Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to specify which WebSocket channel to listen on.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Receiving Images:**
   - This node automatically connects to the specified WebSocket channel and listens for incoming image data.
   - When an image is received, it will be processed and made available as an output that can be connected to other nodes in your workflow.
   - If no image has been received yet, a black placeholder image will be provided.

**Notes:**
- This node is designed to work with the `IMAGE WebSocket Web Viewer @ vrch.ai` node, receiving the images it broadcasts.
- The node automatically establishes and maintains WebSocket connections, reconnecting if the connection is lost.
- The node continuously monitors for new images, allowing your workflow to react to images sent from any source that connects to the same WebSocket channel.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the image reception process and troubleshoot any issues.

---