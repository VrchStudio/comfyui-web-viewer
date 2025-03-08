# Tutorial 006: Audio Picture Book with Your Own Voice

![](../workflows/example_others_004_srt_to_audio_picture_book.png)

You can **[Download the Workflow Hewre](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_others_004_srt_to_audio_picture_book.json)**

## TL;DR

This tutorial guides you on how to create an **AI-powered Audio Picture Book using your own cloned voice** with the [**ComfyUI Web Viewer**](https://github.com/VrchStudio/comfyui-web-viewer). It utilizes the **Audio Recorder**, **TEXT SRT Player**, and web viewer nodes to transform timed SRT subtitle files into synchronized audio-visual storytelling experiences. Your voice recordings are cloned to narrate stories, while AI dynamically generates matching visuals in real-time.

**Practical Use Cases**:
- Personalized audio books with visually rich storytelling.
- Real-time, interactive visual and audio content for educational or entertainment settings.
- Immersive presentations and performances with custom voice narration.

**🚀 Support Us:**

If you find the **ComfyUI Web Viewer** useful or inspiring, consider supporting us:

- 💖 **Sponsor**: Help us maintain and enhance the project through [GitHub Sponsors](https://github.com/sponsors/VrchStudio).
- ⭐ **Star the Project**: A star on GitHub greatly motivates us and helps increase visibility!
- 📩 **Business Inquiries**: For commercial collaborations, reach us at [hi@vrch.io](mailto:hi@vrch.io).

---

## Preparations

### Download Tools and Models
- **Ollama - Llama3.2**:  
   - [https://ollama.com/library/llama3.2](https://ollama.com/library/llama3.2)
- **T5XXL_FP8_E4M3FN**:  
   - Location: `ComfyUI/models/clip`  
   - [https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors)
- **Flux Turbo-Alpha lora**:
  - Location: `ComfyUI/models/loras`
  - See [https://huggingface.co/alimama-creative/FLUX.1-Turbo-Alpha/tree/main](https://huggingface.co/alimama-creative/FLUX.1-Turbo-Alpha/tree/main)
    - **Note**: please rename the model filename to be `FLUX.1-Turbo-Alpha.safetensors`

### Install Main Custom Nodes

1. **ComfyUI-F5-TTS**  
   - Simply search and install **"ComfyUI-F5-TTS"** in ComfyUI Manager.  
   - See [https://github.com/niknah/ComfyUI-F5-TTS](https://github.com/niknah/ComfyUI-F5-TTS)

2. **ComfyUI-Web-Viewer**  
   - Simply search and install **"ComfyUI Web Viewer"** in ComfyUI Manager.  
   - See [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)

3. **ComfyUI Ollama**:
   - Simply search and install **"comfyui-ollama"** in ComfyUI Manager.
   - See [https://github.com/stavsap/comfyui-ollama](https://github.com/stavsap/comfyui-ollama)

4. **ComfyUI TeaCache**:
   - Simply search and install **"ComfyUI-TeaCache"** in ComfyUI Manasger.
   - See [https://github.com/welltop-cn/ComfyUI-TeaCache](https://github.com/welltop-cn/ComfyUI-TeaCache)

### Install Other Necessary Custom Nodes

- **ComfyUI Chibi Nodes**  
   - Simply search and install **"ComfyUI-Chibi-Nodes"** in ComfyUI Manager.
   - See [https://github.com/chibiace/ComfyUI-Chibi-Nodes](https://github.com/chibiace/ComfyUI-Chibi-Nodes)
- **RGThree's ComfyUI Nodes**:  
   - Simply search and install **"rgthree-comfy"** in ComfyUI Manager.
   - [https://github.com/rgthree/rgthree-comfy](https://github.com/rgthree/rgthree-comfy)

## How to Use

### Run Workflow in ComfyUI

1. **Open the Workflow**  
   - Import the [example_others_004_srt_to_audio_picture_book](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_others_004_srt_to_audio_picture_book.json) workflow into ComfyUI.
2. **Record Your Voice**
   - In the **`Audio Recorder @ vrch.ai`** node:
       - Press and hold the **[Press and Hold to Record]** button.
       - Read aloud the text in `Sample Text to Record` (for example):
         > This is a test recording to make AI clone my voice.
3. **Trigger the SRT Player**
   - Change the **`[Queue]`** button to **`[Queue (Instant)]`**
   - In the **`TEXT SRT Player @vrch.ai`** node:
     - Click **`[Play SRT File]`** button to start SRT player
   - Click **`[Queue (Instant)]`** button to start Infinite Queue
4. **Open Audio Web Viewer Page for Audio Play**
   - In the **`AUDIO Web Viewer @ vrch.ai`** node, click the **[Open Web Viewer]** button.
   - A new browser window (or tab) will open, playing the story audio with your cloned voice.
5. **Open Image Instant Viewer Page for Image Display**
   - In the **`IMAGE Web Viewer @ vrch.ai`** node, click the **[Open Web Viewer]** button.
   - A new browser window (or tab) will open, display the story pictures generated.
6. **(Optinal) Enable Preview Image in Background for Image Preview in ComfyUI** 
   - In the **`IMAGE Preview in Background @ vrch.ai`** node, enable `background_display` option
   - The story pictures will be displayed in ComfyUI web page as background
  
### Example: SRT Format Stories

#### Story One

```
1
00:00:00,000 --> 00:00:13,000
Little Deer opened her eyes as moonlight gently caressed the forest.
The woods at night were wrapped in a silvery veil, peaceful and enchanting.

2
00:00:13,000 --> 00:00:25,000
“Little deer, a star has lost its way,” whispered the owl from the tall oak tree,
his eyes glowing softly in the moonlight.

3
00:00:25,000 --> 00:00:42,000
Tiptoeing gently through the forest, Little Deer passed a sleeping hedgehog curled beneath leaves,
and a little fox smiling sweetly in his dreams.

4
00:00:42,000 --> 00:00:56,000
Soon, little deer spotted a star gently floating on the lake,
glimmering quietly and rocking with the waves.

4
00:00:56,000 --> 00:01:10,000
Little deer carefully waded into the water and whispered softly,
“Don’t be afraid, little star. I'll help you find your way back home.”

6
00:01:10,000 --> 00:01:25,000
She looked upward, where countless stars twinkled brightly in the velvet sky,
each gently waving, waiting for their lost friend to return.

7
00:01:25,000 --> 00:01:42,000
Gently lifting the star back into the sky, little deer watched as it shone brighter,
joining friends that twinkled happily in thanks.

8
00:01:42,000 --> 00:02:00,000
Little deer lay down softly beneath the tree, closed her eyes,
and drifted into sweet dreams, as the forest sparkled brighter than ever,
wrapping every animal in the gentlest sleep.
```

#### Story Two

```
1
00:00:00,000 --> 00:00:13,000
As little rabbit opened her eyes, the moonlight softly touched the forest.
The night was quiet and calm, like a gentle lullaby.

2
00:00:13,000 --> 00:00:25,000
“Little rabbit, the forest is yours tonight,”
said a tiny firefly, glowing gently like a star.

3
00:00:25,000 --> 00:00:42,000
She hopped through the woods, gently checking on her sleeping friends—
the hedgehog curled up tight, the little fox smiling sweetly.

4
00:00:42,000 --> 00:00:56,000
Suddenly, rabbit saw the reflection of the moon in the pond,
but the little moon in the water was crying softly.

5
00:00:56,000 --> 00:01:10,000
“Don’t cry, little moon, I’m here,”
rabbit said, crafting a leaf boat and gently sailing toward the center.

6
00:01:10,000 --> 00:01:25,000
She gently rocked the moon to sleep,
until the little reflection smiled again, shimmering happily.

7
00:01:25,000 --> 00:01:42,000
Back on shore, rabbit looked up to the sky,
where the real moon smiled warmly down at them.

8
00:01:42,000 --> 00:02:00,000
Rabbit closed her eyes, cuddling softly beneath the trees.
Tonight, every animal slept peacefully under the gentle moonlight.
```


## References

- **Audio Picture Book Workflow**:
  [example_others_004_srt_to_audio_picture_book](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_others_004_srt_to_audio_picture_book.json)
- **ComfyUI Web Viewer GitHub Repo**:  
  [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)



