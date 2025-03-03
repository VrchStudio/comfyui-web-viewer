### Node: `JSON URL Loader @ vrch.ai` (vrch.ai/text)

1. **Add the `JSON URL Loader @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **URL:**
     - **`url`**: Provide the URL from which the node will load JSON content.
   - **Optional Settings:**
     - **`print_to_console`**: Toggle this option to print the loaded JSON to the console for debugging purposes.

3. **Load JSON:**
   - The node sends a GET request to the specified URL with a 5-second timeout.
   - Upon success, it parses the response into a JSON object.
   - In case of a request failure or if the JSON is invalid, the node outputs an empty JSON object (`{}`).
   - If enabled, the node prints a formatted version of the JSON to the console for inspection.

**Note:**
- Ensure that the URL is accessible and returns valid JSON data.


---

### Node: `TEXT SRT Player @ vrch.ai` (vrch.ai/text)

1. **Add the `TEXT SRT Player @ vrch.ai` node to your ComfyUI workflow.**

2. **Configure the Node:**
   - **SRT Text Input:**
     - **`srt_text`**: Provide the SRT-formatted text containing subtitle timing and content. The text should follow proper SRT formatting.
   - **Placeholder Text:**
     - **`placeholder_text`**: Specify the text that will be output when no subtitle is active (i.e., when `current_selection` is set to `-1`).
   - **Loop:**
     - **`loop`**: Toggle this option to enable or disable looping playback of the SRT file.
   - **Current Selection:**
     - **`current_selection`**: This integer value is automatically updated during playback to indicate the currently active subtitle. When the playback time is outside any subtitle interval, the value is set to `-1`, causing the placeholder text to be output instead.
   - **Debug:**
     - **`debug`**: Enable debug mode to print detailed parsing and playback logs to the console (useful for troubleshooting or verifying SRT parsing).

3. **Play SRT Text & Interactive Controls:**
   - **Subtitle Parsing & Playback:**
     - The node uses an SRT parsing library to convert the provided SRT text into a list of subtitle entries.
     - As the node “plays” the subtitles, it continuously updates `current_selection` based on the current playback time.
   - **Play/Pause Button:**
     - Toggles between playing and pausing the subtitle playback. The button text updates to reflect the current state.
   - **Reset Button:**
     - Resets the playback time to the beginning (0 seconds).
   - **Playback Time Display:**
     - Shows the current playback time (in seconds) and updates in real time while subtitles are playing.
   - **Progress Slider:**
     - An interactive timeline bar for jumping to a specific time within the SRT file.  
     - Dragging the slider updates the playback time accordingly, and the displayed subtitle changes if a new subtitle range is entered.
   - **Looping:**
     - If `loop` is enabled, playback automatically restarts at 0 seconds after the last subtitle entry ends.

4. **Node Output:**
   - The node outputs the text of the currently active subtitle entry. If the playback time is not within any subtitle range, the node outputs the `placeholder_text`.
   - You can chain this output into subsequent nodes in your ComfyUI workflow for further processing or display.

**Note:**
- Ensure that your SRT text is correctly formatted (with sequential numbering, time range lines, and subtitle text).