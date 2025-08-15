### Node: `IMAGE WebSocket Web Viewer (Legacy) @ vrch.ai` (vrch.ai/viewer)

1. **Add the `IMAGE WebSocket Web Viewer (Lagecy) @ vrch.ai` node to your ComfyUI workflow.**

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
     - **`mixBlendMode`**: Set the blend mode for image transitions (default is **`none`**). Options include **`normal`**, **`multiply`**, **`screen`**, etc.
     - **`enableLoop`**: Toggle whether to loop playback of images (default is **`True`**).
     - **`enableUpdateOnEnd`**: Toggle whether to update the image cache only at the end of playback (default is **`False`**).
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

4. **Outputs:**
   - **`IMAGES`**: The input images are passed through as output.
   - **`URL`**: The constructed URL for the web viewer.

**Notes:**
- Make sure that the server address and configuration are correct and that the server is accessible.
- This node uses the WebSocket protocol to transmit image data in real time to the specified channel; ensure your client browser supports WebSocket connections.
- When **`save_settings`** is enabled, a JSON with your websocket parameters is sent via the same WebSocket connection.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the image transmission process and troubleshoot any issues.

---

### Node: `IMAGE WebSocket Web Viewer @ vrch.ai` (vrch.ai/viewer)

A simplified version of the main WebSocket image viewer node that focuses purely on image transmission without settings management.

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
   - **Image Settings:**
     - **`number_of_images`**: Set the number of images to load (default is **1**, range: 1-99).
     - **`image_display_duration`**: Duration to display each image in milliseconds (default is **1000**, range: 1-10000).
     - **`fade_anim_duration`**: Duration of fade animation in milliseconds (default is **200**, range: 1-10000).
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **1280**, range: 100-10240).
     - **`window_height`**: Set the height of the web viewer window (default is **960**, range: 100-10240).
   - **Show URL:**
     - **`show_url`**: Toggle the display of the constructed URL in the interface. When enabled, the **`url`** field becomes visible (default is **False**).
   - **Development Mode:**
     - **`dev_mode`**: Enable development mode for additional features (default is **False**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting (default is **False**).
   - **Extra Parameters:**
     - **`extra_params`**: Additional parameters for the web viewer in string format (multiline text field).
   - **URL Input:**
     - **`url`**: This field is automatically updated with a constructed URL based on your inputs (server, channel, extra parameters, etc.). You can control its visibility with the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the generated URL in a new browser window, where your image will be displayed in real time via the WebSocket connection.

4. **Outputs:**
   - **`IMAGES`**: The input images are passed through as output.
   - **`URL`**: The constructed URL for the web viewer.

**Notes:**
- This simplified node focuses purely on image transmission and does not include advanced WebSocket parameters or settings management.
- For workflows requiring custom WebSocket settings, use the **`IMAGE WebSocket Settings @ vrch.ai`** node in combination with this node.
- Make sure that the server address and configuration are correct and that the server is accessible.
- The `extra_params` field allows for additional customization of the web viewer behavior.

---

### Node: `IMAGE WebSocket Settings @ vrch.ai` (vrch.ai/viewer)

A dedicated node for managing and transmitting WebSocket settings parameters separately from image data. Supports optional merging of image CSS filter parameters supplied by the `IMAGE Filter Settings @ vrch.ai` node.

1. **Add the `IMAGE WebSocket Settings @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to differentiate WebSocket connections.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Send Settings Control:**
     - **`send_settings`**: Toggle whether to actually send the settings to the WebSocket channel (default is **True**). When disabled, the node will skip settings transmission entirely, allowing you to prepare settings without broadcasting them.
  - **Websocket Parameters:**
     - **`number_of_images`**: Set the number of images to load (default is **1**, range: 1-99).
     - **`image_display_duration`**: Duration to display each image in milliseconds (default is **1000**, range: 1-10000).
     - **`fade_anim_duration`**: Duration of fade animation in milliseconds (default is **200**, range: 1-10000).
     - **`blend_mode`**: Set the blend mode for image transitions (default is **"none"**). Options include **"normal"**, **"multiply"**, **"screen"**, **"overlay"**, **"darken"**, **"lighten"**, **"color-dodge"**, **"color-burn"**, **"hard-light"**, **"soft-light"**, **"difference"**, **"exclusion"**, **"hue"**, **"saturation"**, **"color"**, **"luminosity"**.
     - **`loop_playback`**: Toggle whether to loop playback of images (default is **True**).
     - **`update_on_end`**: Toggle whether to update the image cache only at the end of playback (default is **False**).
   - **Background Settings:**
     - **`background_colour_hex`**: Set the background color in hexadecimal format (default is **"#222222"**).
   - **Server Messages:**
     - **`server_messages`**: Server messages to send to the web page viewer (default is empty string).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting (default is **False**).
   - **Optional Filters JSON:**
     - **`filters_json`** *(optional input)*: Connect the output of `IMAGE Filter Settings @ vrch.ai` (or any JSON node providing a compatible structure). When present, its filter data is merged into the outgoing settings under `settings.filters`.

3. **Settings Transmission:**
   - When **`send_settings`** is enabled (default), this node saves the WebSocket settings to a JSON format and sends them via the WebSocket connection.
   - When **`send_settings`** is disabled, the node will skip transmission and output a debug message (if debug mode is enabled) indicating that settings sending is disabled.
   - Settings are transmitted to the specified channel and can be received by web viewers or other WebSocket clients.
   - The settings JSON includes: numberOfImages, imageDisplayDuration, fadeAnimDuration, mixBlendMode, enableLoop, enableUpdateOnEnd, bgColourPicker, and serverMessages.

4. **Outputs:**
   - **`IMAGE_SETTINGS_JSON`**: The settings dictionary (Python/JSON) actually sent over WebSocket (only produced when `send_settings=True`; if sending is disabled, no output is generated). Structure example:

      ```json
      {
        "settings": {
          "numberOfImages": 1,
          "imageDisplayDuration": 1000,
          "fadeAnimDuration": 200,
          "mixBlendMode": "none",
          "enableLoop": true,
          "enableUpdateOnEnd": false,
          "bgColourPicker": "#222222",
          "serverMessages": "",
          "filters": {
            "blur": 4,
            "brightness": 1.2,
            "contrast": 1.1,
            "grayscale": 0.0,
            "hueRotate": 180,
            "invert": 0.0,
            "saturate": 1.4,
            "sepia": 0.2
          }
        }
      }
      ```

**Notes:**
- Chain the `IMAGE Filter Settings @ vrch.ai` node into this node's `filters_json` input to send CSS filter parameters together with viewer settings.
- If `filters_json` contains a top-level `filters` key it will use that; otherwise the entire object is treated as the filters map.
- Output is only produced when settings are actually sent (`send_settings=True`).
- Use a JSON inspection node (or subsequent logic nodes) with the `IMAGE_SETTINGS_JSON` output for dynamic downstream control.
- Blend mode parameter provides extensive compositing options in the viewer.
- Filters are optional; if omitted, the viewer retains its current filter state or defaults (depending on the front‑end logic).

---

### Node: `IMAGE Filter Settings @ vrch.ai` (vrch.ai/viewer/websocket)

Provides adjustable CSS image filter parameters as a JSON object for composition into WebSocket image settings. Designed to feed into the `IMAGE WebSocket Settings @ vrch.ai` node via its `filters_json` input.

1. **Add the `IMAGE Filter Settings @ vrch.ai` node to your workflow.**

2. **Configure Filter Parameters (inputs):**
  - **`blur`**: Integer pixels (0–50) – matches `blur(px)`.
  - **`brightness`**: Float (0.0–3.0) – 1.0 is neutral.
  - **`contrast`**: Float (0.0–3.0) – 1.0 is neutral.
  - **`grayscale`**: Float (0.0–1.0) – 0 is color, 1 is fully grayscale.
  - **`hue_rotate`**: Integer degrees (0–360) – applied as CSS `hue-rotate()`.
  - **`invert`**: Float (0.0–1.0) – 0 no invert, 1 full invert.
  - **`saturate`**: Float (0.0–3.0) – 1.0 is neutral.
  - **`sepia`**: Float (0.0–1.0) – 0 none, 1 full sepia.

3. **UI Convenience:**
  - A small green "Reset Filters" button (in the node UI) resets all parameters to their defaults.

4. **Output:**
  - **`IMAGE_FILTERS_JSON`**: JSON structure:
    ```json
    {
      "filters": {
      "blur": 0,
      "brightness": 1.0,
      "contrast": 1.0,
      "grayscale": 0.0,
      "hueRotate": 0,
      "invert": 0.0,
      "saturate": 1.0,
      "sepia": 0.0
      }
    }
    ```

5. **Typical Workflow:**
  - Connect `IMAGE_FILTERS_JSON` to the `filters_json` input of the `IMAGE WebSocket Settings @ vrch.ai` node.
  - Execute the settings node (with `send_settings=True`) to broadcast both regular settings and filters to the viewer.

**Notes:**
- The key names (`blur`, `brightness`, `contrast`, `grayscale`, `hueRotate`, `invert`, `saturate`, `sepia`) match the front‑end's `applyRemoteFilters()` expectations.
- Values are clamped on the viewer side as a safety measure; staying within documented ranges ensures predictable results.
- You can route this JSON through additional logic or merge nodes before feeding into the settings node to implement animations or dynamic modulation.

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
   - Once running, it handles communication for all WebSocket nodes (Image, JSON, and Latent)
   - The server maintains separate connection paths for different data types (/image, /json, /latent, /audio, /video, /text)
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
   - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to specify which WebSocket channel to listen on.
   - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **`placeholder`**: Choose the placeholder to display when no image data is received. Options:
         - **"black"**: pure black placeholder image.
         - **"white"**: pure white placeholder image.
         - **"grey"**: mid-grey placeholder image.
         - **"image"**: use the provided **`default_image`** as placeholder. Requires supplying **`default_image`**. The node detects changes to this image and outputs it immediately once per change.
   - **`default_image`**: *(Optional)* Image to use when **`placeholder`** is set to **"image"**.
   - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Outputs:**
   - **`IMAGE`**: The output image tensor or placeholder.
   - **`IS_DEFAULT_IMAGE`**: Boolean flag, `True` if the `IMAGE` output is the provided `default_image`, `False` otherwise.

4. **Receiving Images:**
   - This node automatically connects to the specified WebSocket channel and listens for incoming image data.
   - When an image is received, it will be processed and made available as the `IMAGE` output with `IS_DEFAULT_IMAGE` set to `False`.
   - If **`placeholder`** is set to **"image"** and a new **`default_image`** was provided since the last execution, it is output immediately once (`IMAGE` + `True`).
   - If no WebSocket image is received afterward, the **`default_image`** is used as the placeholder output (`IS_DEFAULT_IMAGE=False` in that case?).

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

---

### Node: `LATENT WebSocket Sender @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `LATENT WebSocket Sender @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Latent Input:**
     - **`latent`**: Connect the latent data you want to send over WebSocket. This should be a properly formatted latent tensor.
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to differentiate WebSocket connections.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.

3. **Sending Latent Data:**
   - The node validates the latent data before sending. If the latent data is invalid, the node will raise a ValueError.
   - The latent tensor is converted to JSON format (including shape information) and sent to the specified WebSocket channel and path (/latent).
   - The original latent data is also available as an output that can be connected to other nodes.

**Notes:**
- This node works with the `WebSocket Server @ vrch.ai` node, which must be running to establish connections.
- Ensure your latent data contains valid samples to avoid validation errors.
- The latent data is converted to JSON format for transmission and includes shape information for proper reconstruction.
- When debug mode is enabled, the node outputs detailed logs to the console, including the shape of the sent latent data.

---

### Node: `LATENT WebSocket Channel Loader @ vrch.ai` (vrch.ai/viewer/websocket)

1. **Add the `LATENT WebSocket Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**) to specify which WebSocket channel to listen on.
   - **Server:**
     - **`server`**: Enter the server's domain or IP address along with its port in the format `IP:PORT`. The default typically uses your IP and port **8001** (e.g., **`127.0.0.1:8001`**).
   - **Debug Mode:**
     - **`debug`**: Enable this option to print detailed debug information to the console for troubleshooting.
   - **Default Latent:**
     - **`default_latent`**: (Optional) Latent data to use when no data is received from the WebSocket channel.

3. **Receiving Latent Data:**
   - This node automatically connects to the specified WebSocket channel and listens for incoming latent data.
   - When latent data is received, it will be parsed and reconstructed into the proper tensor format for use in your workflow.
   - If no latent data has been received yet, the default latent will be used (if provided), otherwise an empty latent tensor is created.
   - The empty latent has dimensions (1, 4, 64, 64) suitable for most diffusion model workflows.

**Notes:**
- This node is designed to work with the `LATENT WebSocket Sender @ vrch.ai` node, receiving the latent data it broadcasts.
- The node automatically establishes and maintains WebSocket connections, reconnecting if the connection is lost.
- The node continuously monitors for new latent data, allowing your workflow to react to latent data sent from any source that connects to the same WebSocket channel.
- When debug mode is enabled, the node outputs detailed logs to the console, which can help you track the latent data reception process and show tensor shapes.

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

