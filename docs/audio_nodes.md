### Node: `Audio Recorder @ vrch.ai` (vrch.ai/audio)

1. **Add the `Audio Recorder @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Record Mode (`record_mode`):**
     - **"Press and Hold":**
       - **Button Control:** Hold the record button to start recording; release to stop.
       - **Shortcut Control:** Press and hold the selected shortcut key to start recording; release to stop.
     - **"Start and Stop":**
       - **Button Control:** Click "START" to begin recording; click "STOP" to end.
       - **Shortcut Control:** Press the selected shortcut key once to start recording; press again to stop.
   - **Recording Parameters:**
     - `record_duration_max`: Set the maximum recording duration (1-60 seconds).
     - `loop`: Enable or disable loop recording.
     - `loop_interval`: Set the interval between loop recordings (if loop is enabled).
     - `new_generation_after_recording`: Enable to automatically trigger a queue generation after recording.
   - **Shortcut Configuration:**
     - `shortcut`: Enable or disable the keyboard shortcut for controlling recording.
     - `shortcut_key`: Select the desired shortcut key (e.g., F1, F2, ..., F12) for controlling the recording.
3. **Record Audio:**
   - **"Press and Hold" Mode:**
     - **Button Control:** Hold the record button to record; release to stop.
     - **Shortcut Control:** Press and hold the selected shortcut key to record; release to stop.
   - **"Start and Stop" Mode:**
     - **Button Control:** Click "START" to begin recording; click "STOP" to end.
     - **Shortcut Control:** Press the selected shortcut key once to start recording; press again to stop.
   - **Loop Mode (Applicable in "Start and Stop" Mode):**
     - Click "START" to begin loop recording.
     - Click "STOP LOOPING" to end loop recording.
4. **Playback and Output:**
   - The recorded audio will appear in the `audioUI` widget for playback.
   - Use the `AUDIO` output to connect the recorded audio to other nodes in your workflow.

**Note**: A countdown displays during the last 10 seconds of recording to inform you of the remaining time.

---

### Node: `Get Music Genres @ vrch.ai` (vrch.ai/audio)

1. **Add the `Get Music Genres @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Audio Input (`audio`):** Provide an `AUDIO` input from a previous node in the workflow, such as an audio recorder or a file loader.
3. **Analyze Audio:**
   - The node processes the input audio to predict its music genre(s).
   - It uses a pre-trained model to analyze the waveform and outputs the predicted genres along with their probabilities.
4. **View Results:**
   - The predicted genres and their associated probabilities are displayed in a text output format.
   - The results indicate the likelihood of the audio belonging to specific music genres.
5. **Connect to Other Nodes:**
   - Use the `AUDIO` output to pass the analyzed audio to other nodes for further processing or playback.
   - Use the `STRING` output to connect the genre predictions to nodes that require textual input or visualization.

**Note:** Ensure that the input audio is properly preprocessed and normalized for accurate genre prediction. The node's output is influenced by the quality and clarity of the input audio.