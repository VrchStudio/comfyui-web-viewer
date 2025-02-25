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
     - **`current_selection`**: This integer value is automatically updated during playback to indicate the currently active subtitle. When the playback time is outside any subtitle interval, the value is set to `-1` so that the placeholder text is output.
   - **Debug:**
     - **`debug`**: Enable debug mode to print detailed parsing and playback logs to the console.

3. **Play SRT Text:**
   - The node uses an SRT parsing library to convert the provided SRT text into subtitle entries.
   - It then plays the subtitles by continuously updating the `current_selection` based on the current playback time.
   - The node provides interactive controls:
     - **Play/Pause:** A button that toggles between playing and pausing the subtitle playback. The button text updates to reflect the current state.
     - **Reset:** A button that resets the playback time to the beginning.
   - A small display shows the current playback time in seconds.
   - When looping is enabled, playback automatically restarts from the beginning upon reaching the end of the last subtitle entry.

**Note:**
- Ensure that the SRT text follows the correct SRT formatting standard.
- The node outputs the content of the selected subtitle (or the placeholder text when no subtitle is active) to subsequent nodes in your workflow.

