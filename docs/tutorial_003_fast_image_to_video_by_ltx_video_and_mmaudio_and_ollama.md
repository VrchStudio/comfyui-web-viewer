## TL;DR

This ComfyUI workflow leverages the powerful **LTX Videos + STG Framework** to create high-quality, motion-rich animations effortlessly. Now with added **MMAudio sound effects generation** and enhanced **model compatibility**! Here’s what it offers:

1. **Fast and Efficient Motion Picture Generation**:  
   Transform a static image into a 3-6 seconds motion picture with synchronized sound effects in just one minute using a local GPU, ensuring both speed and quality.
2. **Advanced Autocaption, Video and Sound Prompt Generator**:  
   Combines the capabilities of **Florence2** and **Llama3.2** as Image-to-Video/Sound-Prompt assistants, enabled via custom ComfyUI nodes. Simply upload an image, and the workflow generates a stunning motion picture with sounds based on it.
3. **Enhanced Customizability and Control**:  
   Includes a revamped **Control Panel** with more adjustable parameters for better precision. The optional **User Input** nodes let you fine-tune style, theme, and narrative to your liking for both motion pictures and sounds.
4. **Expanded Model and Framework Compatibility**:  
   Supports both `ltx-video-2b-v0.9.safetensors` and `ltx-video-2b-v0.9.1.safetensors` models. The workflow also now supports the **VAE Decode (Tiled)** node, making it accessible for GPUs with lower memory.

This workflow provides a comprehensive solution for generating AI-driven motion pictures with synchronized audio and highly customizable features.

- You can [download the workflow from here](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_web_viewer_004_video_web_viewer_video_with_sfx.json)
- see [ComfyUI Web Viewer github repo](https://github.com/VrchStudio/comfyui-web-viewer) for more details

![](../example_workflows/example_web_viewer_004_video_web_viewer_video_with_sfx.png)

## What's New

1. **Sound Effects Generation**:  
   Using the new **MMAudio Module**, the workflow now allows for synchronized sound effect generation to complement your motion pictures.
   
2. **Enhanced Control Panel**:  
   The Control Panel has been significantly updated, featuring additional adjustable parameters for better flexibility and precision (see screenshots).

3. **Improved Model Compatibility**:  
   The workflow now supports both `LTX Videos v0.9` and `LTX Videos v0.9.1` models.

4. **Lower Memory Requirement**:  
   With support for the **VAE Decode (Tiled)** node and enhanced optional `Free GPU Memory` panel , even GPUs with smaller memory can now run this workflow smoothly.

---

## Preparations

### Update ComfyUI Framework
Ensure your ComfyUI framework is updated to the **latest version** to unlock new features such as support for the **VAE Decode (Tiled)** node, which optimizes performance on GPUs with lower memory.

### Download Tools and Models

- **Ollama - Llama3.2**:
   - Download and install `Ollama` first: [https://ollama.com/](https://ollama.com/)
   - Download and run `llama3.2` from here: [https://ollama.com/library/llama3.2](https://ollama.com/library/llama3.2)
- **Florence-2-Large-FT**:  
   - Auto-downloaded on first use.
   - Module official website: [https://huggingface.co/microsoft/Florence-2-large-ft](https://huggingface.co/microsoft/Florence-2-large-ft)
- **LTX-Video-2B v0.9/v0.9.1**:  
   - Location: `ComfyUI/models/checkpoints/video`  
   - Downloads:  
     - **v0.9**: [https://huggingface.co/Lightricks/LTX-Video/blob/main/ltx-video-2b-v0.9.safetensors](https://huggingface.co/Lightricks/LTX-Video/blob/main/ltx-video-2b-v0.9.safetensors)  
     - **v0.9.1**: [https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors](https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors)
- **T5XXL_FP8_E4M3FN Clip model**:  
   - Location: `ComfyUI/models/clip`  
   - [https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors)

---

### Install ComfyUI-MMAudio (For Sound Effects)

ComfyUI-MMAudio enables synchronized sound effects generation for your motion pictures. Follow the steps below to set it up:

1. **Install the Custom Node**:  
   - Use **ComfyUI Manager** and select `Install via Git URL`.  
     - Git URL: [https://github.com/kijai/ComfyUI-MMAudio](https://github.com/kijai/ComfyUI-MMAudio)

2. **Download the Required Models**:  
   - Location: `ComfyUI/models/mmaudio`
   - Models to Download:  
     - `apple_DFN5B-CLIP-ViT-H-14-384_fp16.safetensors`:  
       [https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/apple_DFN5B-CLIP-ViT-H-14-384_fp16.safetensors](https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/apple_DFN5B-CLIP-ViT-H-14-384_fp16.safetensors)  
     - `mmaudio_large_44k_v2_fp16.safetensors`:  
       [https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_large_44k_v2_fp16.safetensors](https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_large_44k_v2_fp16.safetensors)  
     - `mmaudio_synchformer_fp16.safetensors`:  
       [https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_synchformer_fp16.safetensors](https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_synchformer_fp16.safetensors)  
     - `mmaudio_vae_44k_fp16.safetensors`:  
       [https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_vae_44k_fp16.safetensors](https://huggingface.co/Kijai/MMAudio_safetensors/blob/main/mmaudio_vae_44k_fp16.safetensors)
     - `Nvidia bigvganv2 (used with 44k mode)` should be autodownloaded to `ComfyUI/models/mmaudio/nvidia/bigvgan_v2_44khz_128band_512x`:
       [https://huggingface.co/nvidia/bigvgan_v2_44khz_128band_512x](https://huggingface.co/nvidia/bigvgan_v2_44khz_128band_512x)
       
   - Full MMAudio Safetensors Directory:  
     - [https://huggingface.co/Kijai/MMAudio_safetensors/tree/main](https://huggingface.co/Kijai/MMAudio_safetensors/tree/main)

Once installed, this module will allow your workflow to generate motion pictures with synced audio, enhancing the overall experience.

---

### Install Custom Nodes

**Note**: You can use `ComfyUI Manager` to install these nodes directly via their names or Git URLs.

#### Install Main Custom Nodes
- **ComfyUI Ollama**:  
   - [https://github.com/stavsap/comfyui-ollama](https://github.com/stavsap/comfyui-ollama)
- **ComfyUI Florence2**:  
   - [https://github.com/kijai/ComfyUI-Florence2](https://github.com/kijai/ComfyUI-Florence2)
- **ComfyUI LTXVideo**:  
   - [https://github.com/Lightricks/ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)
- **ComfyUI LTXTricks**:  
   - [https://github.com/logtd/ComfyUI-LTXTricks](https://github.com/logtd/ComfyUI-LTXTricks)
- **ComfyUI Web Viewer**:  
   - [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)
- **ComfyUI Video Helper Suite**:  
   - [https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)

#### Install Other Necessary Custom Nodes
- **Image Resize for ComfyUI**:  
   - [https://github.com/palant/image-resize-comfyui](https://github.com/palant/image-resize-comfyui)
- **ComfyUI Image Round**:  
   - [https://github.com/cdb-boop/comfyui-image-round](https://github.com/cdb-boop/comfyui-image-round)
- **rgthree's ComfyUI Nodes**:  
   - [https://github.com/rgthree/rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
- **ComfyUI Easy Use**:  
   - [https://github.com/yolain/ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
- **Derfuu ComfyUI Modded Nodes**:  
   - [https://github.com/Derfuu/Derfuu_ComfyUI_ModdedNodes](https://github.com/Derfuu/Derfuu_ComfyUI_ModdedNodes)
- **ComfyUI Chibi Nodes**:  
   - [https://github.com/chibiace/ComfyUI-Chibi-Nodes](https://github.com/chibiace/ComfyUI-Chibi-Nodes)

---

## How to Use

### Run Workflow in ComfyUI

When running this workflow, the following key parameters in the **Control Panel** can be adjusted to customize the motion picture generation:

- **Frame Max Size**:  
   Sets the maximum resolution for generated frames (e.g., 384, 512, 640, 768). Higher resolutions may require more GPU memory.
- **Frames**:  
   Controls the total number of frames in the motion picture (e.g., 49, 65, 97, 121, 145). More frames result in longer animations but also increase rendering time.
- **Steps**:  
   Specifies the number of iterations per frame; higher steps improve the visual quality but require more processing time.
- **Video CFG**:  
   Determines how strongly the generated video follows the given prompts. A higher CFG value ensures closer adherence to the input prompts but might reduce motion strength.
- **Video Frame Rate (in generation)**:  
   Controls the frame rate (frames per second) used during generation. Default is **24 fps**.
- **Video Frame Rate (in output)**:  
   Defines the final frame rate of the output video. Adjust this to match your desired playback speed.
- **Sound Duration (in seconds)**:  
   Automatically calculated based on the number of frames and frame rate to ensure the generated sound matches the length of the motion picture.
- **User Input (for Video)**:  
   Allows users to input text instructions for generating video prompts, directly influencing the video style, theme, or narrative.
- **User Input (for SFX)**:  
   Accepts user-provided text prompts to generate synchronized sound effects for the motion picture. Examples include descriptions like "gentle snowfall sounds" or "ocean waves crashing."

By adjusting these parameters, you can fine-tune the workflow to meet your specific needs, whether you prioritize quality, speed, or creative control.

### Display Your Generated Artwork Outside of ComfyUI

The **`VIDEO Web Viewer @ vrch.ai`** node (available via the [`ComfyUI Web Viewer`](https://github.com/VrchStudio/comfyui-web-viewer) custom node) makes it easy to showcase your generated motion pictures.

Simply click the `[Open Web Viewer]` button in the `Video Post-Process` group panel, and a web page will open to display your motion picture independently.

For advanced users, this feature even supports simultaneous viewing on multiple devices, giving you greater flexibility and accessibility!

---

## References

- ComfyUI Video + SFX Workflow: [example_web_viewer_004_video_web_viewer_video_with_sfx.json](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_web_viewer_004_video_web_viewer_video_with_sfx.json)
- ComfyUI Web Viewer GitHub Repo: [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)
- LTX Videos GitHub Repo: [https://github.com/Lightricks/ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)
- ComfyUI MMAudio GitHub Repo: [https://github.com/kijai/ComfyUI-MMAudio](https://github.com/kijai/ComfyUI-MMAudio)