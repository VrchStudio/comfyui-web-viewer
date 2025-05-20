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

---

### Node: `Microphone Loader @ vrch.ai` (vrch.ai/audio)

1. **Add the `Microphone Loader @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Sensitivity** (`sensitivity`): Adjust the microphone sensitivity level (0.0-1.0).
   - **Frame Size** (`frame_size`): Select audio frame size (256, 512, or 1024 samples).
   - **Sample Rate** (`sample_rate`): Choose sampling rate (16000, 24000, or 48000 Hz).
   - **Debug Mode** (`debug`): Enable to show raw data and debugging information.
3. **Connect to Microphone:**
   - The node will automatically detect available microphones.
   - Click "Refresh" to update the list of available devices.
   - Select a microphone from the dropdown menu to connect to it.
4. **Control the Microphone:**
   - Use the "Mute" button to silence/unmute the microphone.
   - The volume meter shows the current audio level.
   - Real-time waveform and spectrum visualizations display the audio characteristics.
5. **Outputs:**
   - `RAW_DATA`: Complete raw microphone data in JSON format.
   - `WAVEFORM`: Normalized audio waveform data as a float array.
   - `SPECTRUM`: Frequency spectrum data as a float array.
   - `VOLUME`: Current volume level (0.0-1.0).
   - `IS_ACTIVE`: Boolean indicating whether active sound is detected.

**Applications:**
- Voice activity detection for triggering actions in ComfyUI workflows
- Audio-reactive visual effects
- Sound level monitoring
- Signal processing and analysis chains

**Note:** For optimal performance, adjust the sensitivity based on your microphone and ambient noise conditions.

---

### Node: `AUDIO Concat @ vrch.ai` (vrch.ai/audio)

1. **Add the `AUDIO Concat @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Audio Inputs:**
     - `audio1`: The first audio input to be concatenated.
     - `audio2`: The second audio input to be appended after the first.
   - **Crossfade Configuration:**
     - `crossfade_duration_ms`: The duration of the crossfade transition between audio1 and audio2, in milliseconds (0-10000).
       - **0:** No crossfade, audio files are simply joined together.
       - **> 0:** A gradual transition between the end of audio1 and the beginning of audio2.
3. **Audio Processing Features:**
   - **Sample Rate Handling:** Automatically resamples the second audio to match the first audio's sample rate if they differ.
   - **Channel Matching:** Ensures both audio inputs have compatible channel configurations.
   - **Crossfade:** Creates smooth transitions between audio segments when crossfade duration is set.
4. **Output:**
   - `AUDIO`: The concatenated audio that can be connected to other nodes in your workflow.

**Applications:**
- Creating continuous audio tracks from multiple recordings
- Joining speech segments with background music
- Building custom audio sequences for multimedia projects
- Creating seamless loops by connecting the end of an audio clip to its beginning

**Note:** For best results when using crossfade, ensure that both audio inputs have sufficient length for the crossfade duration. The crossfade will be limited to the shorter of the two audio segments if either is shorter than the specified crossfade duration. Remember that crossfade duration is specified in milliseconds (1000 milliseconds = 1 second).