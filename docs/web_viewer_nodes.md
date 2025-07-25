### Node: `Image Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Image Web Viewer @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`images`**: Connect the image(s) you want to display in the web viewer.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Refresh Interval:** Time in milliseconds between refresh attempts (default is **`300`**, range: 1-10000).
   - **Fade Animation Duration:** Duration of fade animation in milliseconds (default is **`200`**, range: 1-10000).
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the image viewer settings to a JSON file. When enabled, creates `channel_{channel}_settings.json`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Image Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the specified URL in a new browser window, displaying your image based on the input parameters.

4. **Outputs:**
   - **`IMAGES`**: The input images are passed through as output.
   - **`URL`**: The constructed URL for the web viewer.

**Note**:
- Ensure that the server address and settings are correct and that the server is accessible.
- The image is saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}.jpeg` (e.g., `channel_1.jpeg`).
- The "Show URL" option allows you to view and copy the dynamically constructed URL if needed.
- The image is saved in JPEG format with a quality setting of 85.

----

### Node: `Image Flipbook Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Image Flipbook Web Viewer @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`images`**: Connect the image(s) you want to display in the web viewer.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Flipbook Parameters:**
     - **`number_of_images`**: Set the number of images to load (default is **`4`**, range: 1-99).
     - **`refresh_interval`**: Time interval for refreshing in milliseconds (default is **`5000`**, range: 1-10000).
     - **`image_display_duration`**: Duration to display each image in milliseconds (default is **`1000`**, range: 1-10000).
     - **`fade_anim_duration`**: Duration of fade animation in milliseconds (default is **`200`**, range: 1-10000).
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the flipbook settings to a JSON file. When enabled, creates `channel_{channel}_settings.json`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**, range: 100-10240).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**, range: 100-10240).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Image Flipbook Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs. You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the specified URL in a new browser window, displaying your images based on the input parameters.

4. **Outputs:**
   - **`IMAGES`**: The input images are passed through as output.
   - **`URL`**: The constructed URL for the web viewer.

**Note**:
- Ensure that the server address and settings are correct and that the server is accessible.
- Images are saved in the `web_viewer` directory under the ComfyUI output folder with filenames like `channel_{channel}_{index}.jpeg`.
- When **`save_settings`** is enabled, a JSON file with your flipbook parameters is created in the same directory.
- The "Show URL" option allows you to view and copy the dynamically constructed URL if needed.
- Images are saved in JPEG format with a quality setting of 85.

----

### Node: `Video Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Video Web Viewer @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Video Input:**
     - **`filename`**: Provide the full path of the video file (currently only `.mp4` format is supported).
       - If the file does not exist or the extension is not allowed, the node will raise an error.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Refresh Interval:** Time in milliseconds between refresh attempts (default is **`5000`**, range: 1-10000).
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the video viewer settings to a JSON file. When enabled, creates `channel_{channel}_settings.json`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Video Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - After providing a valid video file and configuring the node, a **"Play Video"** or **"Open Web Viewer"** button (as implemented in your UI) can be used to launch the specified URL in a new browser window, playing your video based on the input parameters.

4. **Outputs:**
   - **`URL`**: The constructed URL for the web viewer.

**Note**:
- Ensure that the server address and settings are correct and that the server is accessible.
- The video is copied and saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}.mp4` (e.g., `channel_1.mp4`).
- Only `.mp4` format is currently supported.
- The "Show URL" option allows you to view and copy the dynamically constructed URL if needed.

-----

### Node: `Audio Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Audio Web Viewer @ vrch.ai` node** to your ComfyUI workflow.  
   This node enables you to save and preview audio in a web viewer interface.

2. **Configure the Node:**
   - **Audio Input:**
     - **`audio`**: Connect the audio tensor (`AUDIO` type) that you want to save and preview.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).  
     This channel number is appended to the saved filename, e.g., `channel_1.mp3`.
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Refresh Interval:** Time in milliseconds between refresh attempts (default is **`5000`**, range: 1-10000).
   - **Visualizer Type:** Choose from visualizer types: **"bars"**, **"circles"**, **"matrix"**, **"particles"**, **"spiral"**, **"waterball"**, or **"waveform"** (default is **"waveform"**).
   - **Audio Transitions:**
     - **`fade_in_duration`**: Duration in milliseconds for the audio fade-in effect (default is **`0`**, range: 0-10000). If set to 0, no fade-in effect will be applied.
     - **`fade_out_duration`**: Duration in milliseconds for the audio fade-out effect (default is **`0`**, range: 0-10000). If set to 0, no fade-out effect will be applied.
     - **`crossfade_duration`**: Duration in milliseconds for crossfade between audio tracks (default is **`0`**, range: 0-10000). If set to 0, crossfade will not be used.
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the audio viewer settings to a JSON file. When enabled, creates `channel_{channel}_settings.json`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. If enabled, the **`url`** field will become visible and show the constructed URL based on your input parameters (`server`, `ssl`, `channel`, etc.).
   - **Extra Params**: The extra parameters for Audio Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field is automatically updated with the constructed URL if **`show_url`** is enabled. You can copy and open this URL manually if desired.

3. **Open Web Viewer:**
   - After connecting your audio and configuring the node, you can open the web viewer (often via a button or link in your ComfyUI interface) to listen to the audio in a new browser window.
   - The audio is saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}.mp3` (e.g., `channel_1.mp3`).

4. **Outputs:**
   - **`AUDIO`**: The input audio is passed through as output.
   - **`URL`**: The constructed URL for the web viewer.

**Notes**:
- Only `.mp3` format is currently used when saving the audio file.
- Make sure the **`server`** address and **`ssl`** settings are correct so that the web viewer can access the generated audio file.
- The **"Show URL"** option allows you to inspect, copy, or manually open the dynamic URL created for your audio content.

-----

### Node: `3D Model Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `3D Model Web Viewer @ vrch.ai` node** to your ComfyUI workflow.  
   This node saves a 3D model (.glb) file into a designated folder and enables you to preview it in a web viewer interface.

2. **Configure the Node:**
   - **Model File:**  
     - **`model_file`**: Provide the filename (STRING) of the .glb file to be saved and viewed.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).  
     The channel number is appended to the saved filename (e.g., `channel_1.glb`).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether to use SSL; if enabled, `https` is used, otherwise `http`.
   - **Refresh Interval:** Time in milliseconds between refresh attempts (default is **`5000`**, range: 1-10000).
   - **Server Messages:** Save and send server messages to its web page viewer.
   - **Save Settings:** Toggle whether to save the 3D model viewer settings to a JSON file. When enabled, creates `channel_{channel}_settings.json`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface.
   - **Extra Params**: The extra parameters for 3D Model Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field is automatically updated with the constructed URL if **`show_url`** is enabled.

3. **Open Web Viewer:**
   - After executing the node, the 3D model is saved in the `web_viewer` directory under the ComfyUI output folder with a filename such as `channel_1.glb`.
   - Open the web viewer (typically via a button or link in the interface) to load and interact with the 3D model in your browser.

4. **Outputs:**
   - **`MODEL_FILE`**: The path to the saved 3D model file (e.g., `web_viewer/channel_1.glb`).
   - **`URL`**: The constructed URL for the web viewer.

**Notes:**
- Currently only `.glb` files are supported.
- Ensure the **`server`** address and **`ssl`** settings are correctly configured so that the web viewer can access the generated file.
- The returned file path (e.g., `web_viewer/channel_1.glb`) can be used by the default 3d Model Preview node to load and preview the 3d model.

---

### Node: `Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Web Viewer @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Mode:** Select the mode to open from `image`, `flipbook`, `audio`, `depthmap` or `3dmodel`.
   - **Server:** Set the ComfyUI server's domain name (default is `127.0.0.1:8188`).
   - **SSL:** Choose whether the connection should use SSL (if `True`, it will use `https`, otherwise `http`).
   - **File Name:** Enter the file name to be used in the web viewer (e.g., `web_viewer_image.jpeg`).
   - **Path:** Enter the path for the resource (default is `web_viewer`).
   - **Window Dimensions:**
     - `window_width`: Set the width of the web viewer window.
     - `window_height`: Set the height of the web viewer window.
   - **Show URL:** Toggle whether to display the constructed URL in the interface. If enabled, the `url` input field will become visible and show the constructed URL based on the input parameters.
   - **URL Input:** This field is automatically updated with the constructed URL based on the inputs provided (`page`, `server`, `ssl`, `file`, and `path`). You can toggle its visibility using the `show_url` input.
   - **Extra Params**: The extra parameters for Web Viewer pages, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
3. **Open Web Viewer:**
   - Click the "Open Web Viewer" button to launch the specified URL in a new browser window based on the input parameters.

4. **Outputs:**
   - **`URL`**: The constructed URL for the web viewer.

**Note**:
- Ensure that the URL entered or constructed is valid and accessible. The web viewer window will open based on the specified dimensions.
- The "Show URL" option allows you to see the dynamically constructed URL if you want to inspect or copy it.
  
----

### Node: `IMAGE Web Viewer Channel Loader @ vrch.ai` (vrch.ai/viewer)

1. **Add the `IMAGE Web Viewer Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**). The node loads the corresponding image file from the `web_viewer` subfolder in the output directory (e.g., `channel_1.jpeg`).

3. **Load Image:**
   - The node attempts to load the specified image file.
   - If the file exists, it is opened, and loaded.
   - If the file does not exist or an error occurs during loading, a 512x512 black placeholder image is returned.

4. **Caching Behavior:**
   - The node's `IS_CHANGED` method always returns `NaN`, ensuring that the node is always considered changed and forces reloading of the image.

**Note:**
- Ensure that the `web_viewer` directory under the ComfyUI output folder contains the expected image files named in the format `channel_[channel].jpeg`.

----

### Node: `AUDIO Web Viewer Channel Loader @ vrch.ai` (vrch.ai/viewer)

1. **Add the `AUDIO Web Viewer Channel Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**). The node loads the corresponding audio file from the `web_viewer` subfolder in the output directory (e.g., `channel_1.mp3`).
   - **Debug:**
     - **`debug`**: Enable or disable debug logging (default is **`False`**). When enabled, the node will output detailed information about the loading process.

3. **Load Audio:**
   - The node attempts to load the specified audio file.
   - If the file exists, it is loaded into a torch tensor and processed.
   - If the audio is mono (single channel), it is converted to stereo by duplicating the channel.
   - If the file does not exist or an error occurs during loading, a 5-second silent audio is generated as a fallback.

4. **Caching Behavior:**
   - The node's `IS_CHANGED` method always returns `NaN`, ensuring that the node is always considered changed and forces reloading of the audio.

**Note:**
- Ensure that the `web_viewer` directory under the ComfyUI output folder contains the expected audio files named in the format `channel_[channel].mp3`.
- The debug option is useful for troubleshooting audio loading issues.

----