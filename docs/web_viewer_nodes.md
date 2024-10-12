### Node: `Image Web Viewer by vrch.io` (vrch.io/image)

1. **Add the `Image Web Viewer by vrch.io` node to your ComfyUI workflow.**

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
   - **URL Input:** This field automatically updates with the constructed URL based on your inputs (`server`, `ssl`, `channel`, etc.). You can toggle its visibility using the **`show_url`** option.

3. **Open Web Viewer:**
   - Click the **"Open Web Viewer"** button to launch the specified URL in a new browser window, displaying your image based on the input parameters.

**Note**:
- Ensure that the server address and settings are correct and that the server is accessible.
- The image is saved in the `web_viewer` directory under the ComfyUI output folder with the filename `channel_{channel}.jpeg` (e.g., `channel_1.jpeg`).
- The "Show URL" option allows you to view and copy the dynamically constructed URL if needed.
- The image is saved in JPEG format with a quality setting of 85.

----

### Node: `Web Viewer by vrch.io` (vrch.io/web)

1. **Add the `Web Viewer by vrch.io` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Page Type:** Select the type of page to open from `image`, `audio`, or `depthmap`.
   - **Server:** Set the ComfyUI server's domain name (default is `127.0.0.1:8188`).
   - **SSL:** Choose whether the connection should use SSL (if `True`, it will use `https`, otherwise `http`).
   - **File Name:** Enter the file name to be used in the web viewer (e.g., `web_viewer_image.jpeg`).
   - **Path:** Enter the path for the resource (default is `web_viewer`).
   - **Window Dimensions:**
     - `window_width`: Set the width of the web viewer window.
     - `window_height`: Set the height of the web viewer window.
   - **Show URL:** Toggle whether to display the constructed URL in the interface. If enabled, the `url` input field will become visible and show the constructed URL based on the input parameters.
   - **URL Input:** This field is automatically updated with the constructed URL based on the inputs provided (`page`, `server`, `ssl`, `file`, and `path`). You can toggle its visibility using the `show_url` input.
3. **Open Web Viewer:**
   - Click the "Open Web Viewer" button to launch the specified URL in a new browser window based on the input parameters.

**Note**:
- Ensure that the URL entered or constructed is valid and accessible. The web viewer window will open based on the specified dimensions.
- The "Show URL" option allows you to see the dynamically constructed URL if you want to inspect or copy it.

----
