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
   - **Websocket Parameters:**
     - **`number_of_images`**: Set the number of images to load (default is **`4`**, range: 1-99).
     - **`image_display_duration`**: Duration to display each image in milliseconds (default is **`1000`**, range: 1-10000).
     - **`fade_anim_duration`**: Duration of fade animation in milliseconds (default is **`200`**, range: 1-10000).
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the websocket settings to a JSON file. When enabled, sends settings via WebSocket.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **1280**).
     - **`window_height`**: Set the height of the web viewer window (default is **960**).
   - **Show URL:**
     - **`show_url`**: Toggle the display of the constructed URL in the interface. When enabled, the **`url`** field becomes visible.
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.
   - **Extra Parameters:**
     - **`extra_params`**: The extra parameters for Image WebSocket Web Viewer, see [websocket_nodes_extra_params.md](./websocket_nodes_extra_params.md)
   - **URL Input:**
     - **`url`**: This field is automatically updated with a constructed URL based on your inputs (server, channel, extra parameters, etc.). You can control its visibility with the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the generated URL in a new browser window, where your image will be displayed in real time via the WebSocket connection.

**Notes:**
- Make sure that the server address and configuration are correct and that the server is accessible.
- This node uses the WebSocket protocol to transmit image data in real time to the specified channel; ensure your client browser supports WebSocket connections.
- When **`save_settings`** is enabled, a JSON with your websocket parameters is sent via the same WebSocket connection.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the image transmission process and troubleshoot any issues.

---

### Node: `WebSocket Server @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `WebSocket Server @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Server:**
     - **`server`**: Enter the server's address and port in the format `IP:PORT`. The default is typically your local IP address and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Server Status Indicator:**
   - The node displays a status indicator that shows whether the server is running:
     - **Grey "Stopped"**: The WebSocket server is not running
     - **Green "Running"**: The WebSocket server is active and accepting connections

4. **Usage:**
   - This node must be executed in your workflow to start the WebSocket server
   - Once running, it handles communication for all WebSocket nodes (Image and JSON)
   - The server maintains separate connection paths for different data types (/image and /json)
   - Multiple clients can connect simultaneously to the same server

**Notes:**
- This node is required for any WebSocket-based communication in your workflow.
- Only one server can run on a specific IP:port combination.
- If a server is already running on the specified address and port, the node will use the existing server.
- WebSocket connections are maintained even when your workflow is not actively running.
- When debug mode is enabled, the server outputs detailed connection logs to the console.

---

### Node: `IMAGE WebSocket Channel Loader @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `IMAGE WebSocket Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to specify which WebSocket channel to listen on.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Placeholder:**
     - **`placeholder`**: Choose the placeholder to display when no image data is received. Options:
         - **"black"**: pure black placeholder image.
         - **"white"**: pure white placeholder image.
         - **"grey"**: mid-grey placeholder image.
         - **"image"**: use the provided **`default_image`** as placeholder. Requires supplying **`default_image`**. The node detects changes to this image and outputs it immediately once per change.
   - **Default Image:** *(Optional)*
     - **`default_image`**: Image to use when **`placeholder`** is set to **"image"**.
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Receiving Images:**
   - This node automatically connects to the specified WebSocket channel and listens for incoming image data.
   - When an image is received, it will be processed and made available as an output that can be connected to other nodes in your workflow.
   - If **`placeholder`** is set to **"image"** and a new **`default_image`** was provided since the last execution, it is output immediately once (before listening for WebSocket data).
   - If no WebSocket image is received afterward, the **`default_image`** is used as the placeholder output.

**Notes:**
- This node is designed to work with the `IMAGE WebSocket Web Viewer @ vrch.ai` node, receiving the images it broadcasts.
- The node automatically establishes and maintains WebSocket connections, reconnecting if the connection is lost.
- The node continuously monitors for new images, allowing your workflow to react to images sent from any source that connects to the same WebSocket channel.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the image reception process and troubleshoot any issues.

---

### Node: `JSON WebSocket Sender @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `JSON WebSocket Sender @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **JSON Input:**
     - **`json_string`**: Enter the JSON string you want to send over WebSocket. This should be a properly formatted JSON string.
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to differentiate WebSocket connections.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Sending JSON Data:**
   - The node validates the JSON string before sending. If the string is not valid JSON, the node will raise a ValueError.
   - Once validated, the JSON data is sent to the specified WebSocket channel and path (/json).
   - The validated JSON is also available as an output that can be connected to other nodes.

**Notes:**
- This node works with the `WebSocket Server @ vrch.ai` node, which must be running to establish connections.
- Ensure your JSON string is properly formatted to avoid validation errors.
- The JSON data is sent through the WebSocket as a raw string.
- When debug mode is enabled, the node outputs detailed logs to the console, including the content of the sent JSON data.

---

### Node: `JSON WebSocket Channel Loader @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `JSON WebSocket Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to specify which WebSocket channel to listen on.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.
   - **Default JSON:**
     - **`default_json_string`**: (Optional) Enter a default JSON string to use when no data is received. This should be a properly formatted JSON string.

3. **Receiving JSON Data:**
   - This node automatically connects to the specified WebSocket channel and listens for incoming JSON data.
   - When JSON data is received, it will be parsed and made available as an output that can be connected to other nodes in your workflow.
   - If no JSON data has been received yet, the default JSON string will be used (if provided), otherwise an empty object `{}` is returned.
   - If the provided default JSON string is not valid JSON, the node will raise a ValueError.

**Notes:**
- This node is designed to work with the `JSON WebSocket Sender @ vrch.ai` node, receiving the JSON data it broadcasts.
- The node automatically establishes and maintains WebSocket connections, reconnecting if the connection is lost.
- The node continuously monitors for new JSON data, allowing your workflow to react to data sent from any source that connects to the same WebSocket channel.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the JSON data reception process.

