
## TL;DR

This ComfyUI workflow leverages the powerful **LTX Videos + STG Framework** to create high-quality, motion-rich animations effortlessly. Here’s what it offers:

1. **Fast and Efficient Motion Picture Generation**:  
   Transform a static image into a 3-6 seconds motion picture in just 15-30 seconds using a local GPU, ensuring both speed and quality.
2. **Advanced Autocaption and Video Prompt Generator**:  
   Combines the capabilities of **Florence2** and **Llama3.2** as Image-to-Video-Prompt assistants, enabled via custom ComfyUI nodes. Simply upload an image, and the workflow generates a stunning motion picture based on it.
3. **Also Support User's Customised Instruction**: 
   Includes an optional **User Input** node, allowing you to add specific instructions to further tailor the generated content, adjusting the style, theme, or narrative to match your vision.

This workflow provides a streamlined and customizable solution for generating AI-driven motion pictures with minimal effort.

- You can [download the workflow from here](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_web_viewer_003_video_web_viewer.json)

![](../example_workflows/example_web_viewer_003_video_web_viewer.png)

## Preparations

### Download Tools and Models
- **Ollama - Llama3.2**:  
   - [https://ollama.com/library/llama3.2](https://ollama.com/library/llama3.2)
- **Florence-2-Large-FT**:  
   - Auto-downloaded on first use
- **LTX-Video-2B v0.9**:  
   - Location: `ComfyUI/models/checkpoints`  
   - [https://huggingface.co/Lightricks/LTX-Video/blob/main/ltx-video-2b-v0.9.safetensors](https://huggingface.co/Lightricks/LTX-Video/blob/main/ltx-video-2b-v0.9.safetensors)
- **T5XXL_FP8_E4M3FN**:  
   - Location: `ComfyUI/models/clip`  
   - [https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors)

### Install ComfyUI Custom Nodes

**Note**: You could use `ComfyUI Manager` to install them in ComfyUI webpage directly.

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

## How to Use

### Run Workflow in ComfyUI

When running this workflow, the following key parameters in the control panel could be adjusted:

- **Frame Max Size**:  
   Sets the maximum resolution for generated frames (e.g., 384, 512, 640, 768).
- **Frames**:  
   Controls the total number of frames in the motion picture (e.g., 49, 65, 97, 121).
- **Steps**:  
   Specifies the number of iterations per frame; higher steps improve quality but increase processing time.
- **User Input** (Optional):  
   Allows users to input extra instruction to customize the generated content, directly affecting the output's style and theme.  
   **Note**: the test shows that the user's input might not always work.

Use these settings in ComfyUI's Control Panel Group to adjust the workflow for optimal results.

### Display Your Generated Artwork Outside of ComfyUI

The **`VIDEO Web Viewer @ vrch.ai`** node (available via the [`ComfyUI Web Viewer`](https://github.com/VrchStudio/comfyui-web-viewer) plugin) makes it easy to showcase your generated motion pictures.

Simply click the `[Open Web Viewer]` button in the `Video Post-Process` group panel, and a web page will open to display your motion picture independently.

For advanced users, this feature even supports simultaneous viewing on multiple devices, giving you greater flexibility and accessibility! :D

### Advanced Tips

You may further tweak Ollama's `System Prompt` to adjust the motion picture's style or quality:

```
You are transforming user inputs into descriptive prompts for generating AI Videos. Follow these steps to produce the final description:
1. English Only: The entire output must be written in English with 80-150 words.
2. Concise, Single Paragraph: Begin with a single paragraph that describes the scene, focusing on key actions in sequence.
3. Detailed Actions and Appearance: Clearly detail the movements of characters, objects, and relevant elements in the scene. Include brief, essential visual details that highlight distinctive features.
4. Contextual Setting: Provide minimal yet effective background details that establish time, place, and atmosphere. Keep it relevant to the scene without unnecessary elaboration.
5. Camera Angles and Movements: Mention camera perspectives or movements that shape the viewer’s experience, but keep it succinct.
6. Lighting and Color: Incorporate lighting conditions and color tones that set the scene’s mood and complement the actions.
7. Source Type: Reflect the nature of the footage (e.g., real-life, animation) naturally in the description.
8. No Additional Commentary: Do not include instructions, reasoning steps, or any extra text outside the described scene. Do not provide explanations or justifications—only the final prompt description.

Example Style:
• A group of colorful hot air balloons take off at dawn in Cappadocia, Turkey. Dozens of balloons in various bright colors and patterns slowly rise into the pink and orange sky. Below them, the unique landscape of Cappadocia unfolds, with its distinctive “fairy chimneys” - tall, cone-shaped rock formations scattered across the valley. The rising sun casts long shadows across the terrain, highlighting the otherworldly topography.
```

## References

- ComfyUI Web Viewer GitHub Repo: [ComfyUI Web Viewer](https://github.com/VrchStudio/comfyui-web-viewer)
- ComfyUI Video Web Viewer workflow: [example_web_viewer_003_video_web_viewer.json](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/example_workflows/example_web_viewer_003_video_web_viewer.json)
- LTX Videos GitHub Repo: [LTX Videos](https://github.com/Lightricks/ComfyUI-LTXVideo)
- Another LTX IMAGE to MOTION PICTURE with STG and autocaption workflow: [civitai link](https://civitai.com/models/995093/ltx-image-to-video-with-stg-and-autocaption-workflow)
