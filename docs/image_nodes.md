### Node: `IMAGE Saver @ vrch.ai` (vrch.ai/image)

1. **Add the `IMAGE Saver @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`images`**: Provide one or more images to be saved.
   - **Filename:**
     - **`filename`**: Specify the base filename for saving the image(s). If multiple images are provided, an index will be appended (e.g., `web_viewer_image_00.jpeg`).
   - **Path:**
     - **`path`**: Define the subfolder within the ComfyUI output directory where the images will be saved (default is `web_viewer`).
   - **File Extension:**
     - **`extension`**: Choose the output image format from **`jpeg`**, **`png`**, or **`webp`** (default is **`jpeg`**).
   - **Quality Settings:**
     - **`quality_jpeg_or_webp`**: Set the quality for JPEG or WEBP images (default is **85**, valid range: **1–100**).
     - **`optimize_png`**: Enable PNG optimization when saving PNG images.
     - **`lossless_webp`**: Enable lossless compression for WEBP images.
   - **Preview Option:**
     - **`enable_preview`**: If enabled, the node will return preview information for the saved images.

3. **Save Images:**
   - The node saves the provided images into the specified subfolder under the ComfyUI output directory using the given filename and file extension.
   - When multiple images are provided, filenames will be automatically suffixed with an index.

---

### Node: `IMAGE Preview in Background @ vrch.ai` (vrch.ai/image)

![](../assets/images/example_003_preview_image_in_background.png)

1. **Add the `IMAGE Preview in Background @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **Image Input:**
     - **`image`**: Provide a single image that you wish to use for the background preview.
   - **Channel:**
     - **`channel`**: Select a channel number from **"1"** to **"8"** (default is **"1"**). This determines the filename (e.g., `channel_1.jpeg`).
   - **Background Display:**
     - **`background_display`**: Toggle to enable or disable the display of the image as a background in ComfyUI.
   - **Refresh Interval:**
     - **`refresh_interval_ms`**: Set the refresh interval in milliseconds for updating the background preview (default is **300ms**).
   - **Display Option:**
     - **`display_option`**: Choose how the image should be displayed in the background. Options include **`original`**, **`fit`**, **`stretch`**, and **`crop`** (default is **`fit`**).

3. **Preview in Background:**
   - The node saves the input image in the `preview_background` subfolder of the ComfyUI output directory using a filename based on the selected channel (e.g., `channel_1.jpeg`).
   - The saved image is intended to be used as a dynamic background inside the ComfyUI frontend.
   - The refresh interval controls how frequently the background preview is updated.

**Note**:
- Ensure that the output directory is correctly configured.
- This node is useful for continuously updating a background display with image previews.

---