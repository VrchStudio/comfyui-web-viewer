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