# Tutorial 005: Storytelling with Text SRT Player

![](../workflows/example_text_nodes_001_text_srt_player.png)

## TL;DR

This tutorial guides you on how to use the **TEXT SRT Playe @ vrch.air** node from [**ComfyUI Web Viewer**](https://github.com/VrchStudio/comfyui-web-viewer), leveraging SRT subtitle files with timestamps to dynamically control storytelling images generation. Combined with the **IMAGE Preview in Background** node, you can create a fully automated, timestamp-based storytelling experience with real-time AI-generated visuals in ComfyUI.

**Practical Use Cases**:
- Interactive storytelling for exhibitions or live performances.
- Dynamic AI-generated visual experiences for streaming or live events.
- Real-time creative sessions with precise narrative control.

## Preparations

### Install Main Custom Nodes

1. **ComfyUI-Web-Viewer**  
   - Simply search and install **"ComfyUI Web Viewer"** in ComfyUI Manager.  
   - See [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)


### Install Other Necessary Custom Nodes

- **ComfyUI Chibi Nodes**  
  - Simply search and install **"ComfyUI-Chibi-Nodes"** in ComfyUI Manager.
  - see [https://github.com/chibiace/ComfyUI-Chibi-Nodes](https://github.com/chibiace/ComfyUI-Chibi-Nodes)

## How to Use

### 1. Run Workflow in ComfyUI

1. **Open the Workflow**
   - Import the [example_text_nodes_001_text_srt_player](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_text_nodes_001_text_srt_player.json) workflow into ComfyUI.

2. **Use SRT Format Text for Storytelling Images Generation**
   - Here is an example:
     ```
        1
        00:00:00,000 --> 00:00:05,000
        A cozy medieval village waking up under a gentle golden sunrise; friendly cottages and blooming flowers surrounded by soft, magical mist; a cheerful young adventurer receives a mysterious, sparkling letter delivered by a small bluebird; storybook fantasy illustration, soft colors, warm lighting, highly detailed, 8K resolution.

        2
        00:00:05,000 --> 00:00:10,000
        A lively village marketplace filled with smiling villagers trading colorful fruits, toys, and treats; the adventurer eagerly studying a playful treasure map decorated with stars and symbols; magical butterflies flutter gently around; storybook fantasy illustration, soft colors, morning sunlight, highly detailed, 8K resolution.

        3
        00:00:10,000 --> 00:00:15,000
        A lush, enchanted forest glowing with magical green lights; giant, friendly trees with smiling faces, moss-covered paths; the young adventurer exploring curiously, cute woodland creatures peeking playfully through the leaves; storybook fantasy illustration, gentle atmosphere, soft colors, highly detailed, 8K resolution.

        4
        00:00:15,000 --> 00:00:20,000
        A secret clearing in the magical forest; a kind old wizard in robes decorated with stars kindly offering friendly advice, surrounded by softly glowing rune stones arranged in a circle; sparkling magic dust floating gently; storybook fantasy illustration, warm sunlight rays, whimsical details, highly detailed, 8K resolution.

        5
        00:00:20,000 --> 00:00:25,000
        A magical desert filled with gentle, rolling golden dunes under a bright cheerful sun; the adventurer happily riding a friendly camel through playful winds swirling magical sparkles in the air; storybook fantasy illustration, soft colors, joyful mood, highly detailed, 8K resolution.

        6
        00:00:25,000 --> 00:00:30,000
        Ancient ruins gently peeking from the sands; friendly-looking giant statues engraved with playful symbols; the young adventurer excitedly discovering a hidden clue while friendly desert foxes watch with curiosity; storybook fantasy illustration, whimsical atmosphere, soft lighting, highly detailed, 8K resolution.

        7
        00:00:30,000 --> 00:00:35,000
        Inside a hidden magical temple softly lit by twinkling torches; walls decorated with glowing playful glyphs; the adventurer cheerfully tiptoeing through the halls, enchanted echoes whispering gently; storybook fantasy illustration, cozy atmosphere, detailed textures, soft lighting, highly detailed, 8K resolution.

        8
        00:00:35,000 --> 00:00:40,000
        A magical chamber gently shrouded in sparkling mist; a giant, friendly stone guardian with softly glowing eyes greets the adventurer who bravely holds up a wooden sword; playful curiosity and awe; storybook fantasy illustration, gentle shadows, whimsical atmosphere, highly detailed, 8K resolution.

        9
        00:00:40,000 --> 00:00:45,000
        A beautiful magical altar glowing with gentle, colorful lights; the adventurer joyfully holds up a brightly glowing crystal treasure surrounded by swirling sparkles; happy magical creatures celebrating around; storybook fantasy illustration, dreamy atmosphere, soft colors, highly detailed, 8K resolution.

        10
        00:00:45,000 --> 00:00:50,000
        The adventurer happily returns to the welcoming village at sunset; villagers cheerfully celebrate with lanterns, music, and treats; gentle golden sunset casting warm lights; joyful mood, storybook fantasy illustration, cozy atmosphere, soft colors, highly detailed, 8K resolution.
     ```
   - Edit and past the SRT Format text into `TEXT SRT Player @ vrch.ai` node

3. **Enable and Start Queue (Instant) Mode**
   - Activate **Queue (Instant)** mode in ComfyUI for real-time prompt processing.
4. **Click [Play SRT File] Button to Start SRT Text Switch**
   - Click the **[Play SRT File]** button in the `TEXT SRT Player @ vrch.ai` node to initiate playback. 
   - The node automatically sends prompts to the workflow according to timestamps.

5. **Enjoy Real-time Visual Storytelling!**
   - Generated images appear dynamically in your ComfyUI interface via the **`IMAGE Preview in Background @ vrch.ai`** node.
   - Images will switch automatically based on SRT timestamps, delivering a smooth storytelling experience.


### 2. Using Your Artworks Outside of ComfyUI

To showcase your real-time AI-generated visuals externally:

- Replace the node **`IMAGE Preview in Background @ vrch.ai`** with the **`IMAGE Web Viewer @ vrch.ai`** node.
- After replacement, click the **[Open Web Viewer]** button.
- A new browser window/tab will open, displaying your real-time storytelling images.

#### Tips for External Viewing:
1. Make sure your **Server** address and **SSL** settings in `IMAGE Web Viewer @ vrch.ai` are correct for your network environment. If you want to access the audio from another device or over the internet, ensure that the server IP/domain is reachable and ports are open.
2. If you’re encountering a CORS policy error with a message like this:
   > `WARNING: request with non matching host and origin 127.0.0.1 != vrch.ai, returning 403`
   
   you can resolve this by launching the ComfyUI service with the `--enable-cors-header` flag appended, e.g.
   `python main.py --enable-cors-header`


## References

- **Storytelling with Text SRT Player Workflow**:
  [example_text_nodes_001_text_srt_player](https://github.com/VrchStudio/comfyui-web-viewer/blob/main/workflows/example_text_nodes_001_text_srt_player.json)
- **ComfyUI Web Viewer GitHub Repo**:
  [https://github.com/VrchStudio/comfyui-web-viewer](https://github.com/VrchStudio/comfyui-web-viewer)

---

Enjoy your journey into dynamic storytelling with ComfyUI!