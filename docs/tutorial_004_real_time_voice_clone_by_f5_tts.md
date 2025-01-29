# Tutorial 004: Real Time Voice Clone by F5-TTS

![](../workflows/example_web_viewer_005_audio_web_viewer_f5_tts.png)

## TL;DR

- You can [download the workflow from here](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_web_viewer_005_audio_web_viewer_f5_tts.json)

## Preparations

### Install Main Custom Nodes

- **ComfyUI-F5-TTS**:
  - simply search and install "ComfyUI-F5-TTS" in ComfyUI Manager
  - see [https://github.com/niknah/ComfyUI-F5-TTS](https://github.com/niknah/ComfyUI-F5-TTS)
- **ComfyUI-Web-Viewer**:
  - simply search and install "ComfyUI Web Viewer" in ComfyUI Manager
  - see [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)

### Install Other Necessary Custom Nodes

- **ComfyUI Chibi Nodes**:  
   - [https://github.com/chibiace/ComfyUI-Chibi-Nodes](https://github.com/chibiace/ComfyUI-Chibi-Nodes)

## How to Use

### Run Workflow in ComfyUI

1. Open the workflow [example_web_viewer_005_audio_web_viewer_f5_tts](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_web_viewer_005_audio_web_viewer_f5_tts.json)
2. In **`Audio Recorder @ vrch.ai`** node, press and hold the `[Press and Hold to Record]` button and read the words in `Sample Text to Record`:
   > This is a test recording to make AI clone my voice.
3. The recorded voice should be recorded and send to `F5-TTS` node to process automatically. And if not, just simply click the [Queue] button to trigger it, for example:
   > I've seen things you people wouldn't believe. Attack ships on fire off the shoulder of Orion. I've watched c-beams glitter in the dark near the Tannhauser Gate. 
   > All those ... 
   > moments will be lost in time, 
   > like tears ... in rain.
4. The words in `Text To Read` node will be read by AI with your cloned voice.
5. Enjoy it!

### Use Your Cloned Voice Outside of ComfyUI

The **`Audio Web Viewer @ vrch.ai`** node (available via the [`ComfyUI Web Viewer`](https://github.com/VrchStudio/comfyui-web-viewer) custom node) makes it easy to showcase your cloned voice.

Simply click the `[Open Web Viewer]` button in that node, and a web page will open to display your cloned voice independently.

## References

- Real Time Voice Clone Workflow: [example_web_viewer_005_audio_web_viewer_f5_tts](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_web_viewer_005_audio_web_viewer_f5_tts.json)
- ComfyUI Web Viewer GitHub Repo: [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)
- ComfyUI F5 TTS GitHub Repo: [https://github.com/niknah/ComfyUI-F5-TTS](https://github.com/niknah/ComfyUI-F5-TTS)