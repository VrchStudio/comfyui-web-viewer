### Node: `Image Web Viewer @ vrch.ai` (vrch.ai/viewer)

1. **Add the `Image Web Viewer @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`images`**: Connect the image(s) you want to display in the web viewer.
   - **Channel:** Select a channel number from **"1"** to **"8"** (default is **"1"**).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Image Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the specified URL in a new browser window, displaying your image based on the input parameters.

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
   - **Number_of_Images:** Select the number of images to load (default is **"4"**).
   - **Server:** Enter the server's domain name or IP address (default is **`127.0.0.1:8188`**).
   - **SSL:** Choose whether the connection should use SSL. If checked (`True`), it will use `https`; otherwise, it will use `http`.
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Image Flipbook Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, `number_of_images` etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the specified URL in a new browser window, displaying your images based on the input parameters.

**Note**:
- Ensure that the server address and settings are correct and that the server is accessible.
- The image is saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}_{index}.jpeg` (e.g., `channel_1_03.jpeg`).
- The "Show URL" option allows you to view and copy the dynamically constructed URL if needed.
- The image is saved in JPEG format with a quality setting of 85.

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
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. Enabling this will make the **`url`** field visible.
   - **Extra Params**: The extra parameters for Video Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - After providing a valid video file and configuring the node, a **"Play Video"** or **"Open Web Viewer"** button (as implemented in your UI) can be used to launch the specified URL in a new browser window, playing your video based on the input parameters.

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
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface. If enabled, the **`url`** field will become visible and show the constructed URL based on your input parameters (`server`, `ssl`, `channel`, etc.).
   - **Extra Params**: The extra parameters for Audio Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field is automatically updated with the constructed URL if **`show_url`** is enabled. You can copy and open this URL manually if desired.

3. **Open Web Viewer:**
   - After connecting your audio and configuring the node, you can open the web viewer (often via a button or link in your ComfyUI interface) to listen to the audio in a new browser window.
   - The audio is saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}.mp3` (e.g., `channel_1.mp3`).

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
   - **Window Dimensions:**
     - **`window_width`**: Set the width of the web viewer window (default is **`1280`**).
     - **`window_height`**: Set the height of the web viewer window (default is **`960`**).
   - **Show URL:** Toggle whether to display the constructed URL in the interface.
   - **Extra Params**: The extra parameters for 3D Model Web Viewer, see [web_viewer_nodes_extra_params.md](./web_viewer_nodes_extra_params.md)
   - **URL Input:** This field is automatically updated with the constructed URL if **`show_url`** is enabled.

3. **Open Web Viewer:**
   - After executing the node, the 3D model is saved in the `web_viewer` directory under the ComfyUI output folder with a filename such as `channel_1.glb`.
   - Open the web viewer (typically via a button or link in the interface) to load and interact with the 3D model in your browser.

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

**Note**:
- Ensure that the URL entered or constructed is valid and accessible. The web viewer window will open based on the specified dimensions.
- The "Show URL" option allows you to see the dynamically constructed URL if you want to inspect or copy it.
  
---