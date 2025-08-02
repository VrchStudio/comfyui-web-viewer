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

### Node: `AUDIO Microphone Loader @ vrch.ai` (vrch.ai/audio)

1. **Add the `AUDIO Microphone Loader @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Sensitivity** (`sensitivity`): Adjust the microphone sensitivity level (0.0-1.0).
   - **Frame Size** (`frame_size`): Select audio frame size (256, 512, or 1024 samples).
   - **Sample Rate** (`sample_rate`): Choose sampling rate (16000, 24000, or 48000 Hz).
   - **Frequency Analysis Parameters:**
     - `low_freq_max`: Maximum frequency for low frequency band (50-1000 Hz, default: 200 Hz).
     - `mid_freq_max`: Maximum frequency for mid frequency band (1000-10000 Hz, default: 5000 Hz).
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
   - `VOLUME`: Current overall volume level (0.0-1.0).
   - `LOW_FREQ_VOLUME`: Volume level for low frequency band (0-low_freq_max Hz).
   - `MID_FREQ_VOLUME`: Volume level for mid frequency band (low_freq_max-mid_freq_max Hz).
   - `HIGH_FREQ_VOLUME`: Volume level for high frequency band (mid_freq_max Hz and above).
   - `IS_ACTIVE`: Boolean indicating whether active sound is detected.

**Frequency Band Analysis:**
- **Low Frequency Band (0-200 Hz):** Captures bass frequencies, useful for detecting low-pitched sounds, male voices, and bass instruments.
- **Mid Frequency Band (200-5000 Hz):** Covers most speech frequencies and important harmonic content.
- **High Frequency Band (5000 Hz+):** Contains consonants, sibilants, and high-pitched sounds that affect clarity and presence.

**Applications:**
- Voice activity detection for triggering actions in ComfyUI workflows
- Audio-reactive visual effects with frequency-specific responses
- Sound level monitoring across different frequency ranges
- Signal processing and analysis chains
- Music and speech analysis with frequency band separation
- Audio classification based on spectral characteristics

**Note:** For optimal performance, adjust the sensitivity based on your microphone and ambient noise conditions. The frequency band boundaries can be customized to match your specific application needs.

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

---

### Node: `AUDIO BPM Detector @ vrch.ai` (vrch.ai/audio)

1. **Add the `AUDIO BPM Detector @ vrch.ai` node to your ComfyUI workflow.**
2. **Connect Audio Data:**
   - **Raw Data Input (`raw_data`):** Connect to the `RAW_DATA` output from an `AUDIO Microphone Loader @ vrch.ai` node.
3. **Configure the Node:**
   - **Audio Parameters:**
     - `sample_rate`: Match the sample rate from your microphone loader (16000, 24000, or 48000 Hz).
   - **BPM Detection Parameters:**
     - `bpm_enabled`: Enable or disable BPM detection (default: True).
     - `analysis_window`: Duration of audio history used for BPM calculation (1.0-10.0 seconds, default: 4.0).
     - `update_interval`: How often BPM values are recalculated (0.1-2.0 seconds, default: 0.2).
     - `confidence_threshold`: Minimum confidence required for BPM output (0.0-1.0, default: 0.3).
     - `bpm_range_min`: Minimum valid BPM value (30-200, default: 60).
     - `bpm_range_max`: Maximum valid BPM value (60-300, default: 200).
   - **Debug Mode (`debug`):** Enable to show detailed BPM detection information.
4. **Real-time BPM Detection:**
   - The node continuously analyzes incoming audio for rhythmic patterns.
   - Beat detection focuses on low-frequency content (20-250 Hz) for optimal percussion detection.
   - BPM calculation uses progressive analysis with confidence scoring.
5. **Outputs:**
   - `BPM_DATA`: Complete BPM analysis data in JSON format including all parameters and statistics.
   - `BPM_VALUE`: Current detected BPM value (0.0 if no valid rhythm detected).
   - `BPM_CONFIDENCE`: Confidence score for the BPM detection (0.0-1.0).
   - `BEAT_DETECTED`: Boolean indicating if a beat was detected in the current frame.
   - `RHYTHM_STRENGTH`: Overall rhythm consistency and strength (0.0-1.0).

**BPM Detection Algorithm:**
- **Beat Detection:** Uses energy-based onset detection in low-frequency bands to identify individual beats.
- **Tempo Calculation:** Analyzes intervals between detected beats to calculate BPM.
- **Confidence Scoring:** Evaluates rhythm consistency and interval stability for confidence measurement.
- **Temporal Smoothing:** Uses rolling averages and history buffers to provide stable BPM readings.

**Applications:**
- Music tempo analysis and synchronization
- Rhythm-based visual effects and lighting control
- Audio-reactive animations with beat-accurate timing
- Live performance monitoring and analysis
- Music production and DJ applications
- Fitness and dance applications requiring beat tracking

**Usage Tips:**
- **Optimal Performance:** Works best with music containing clear rhythmic patterns and percussion.
- **Microphone Placement:** Position microphone to capture good low-frequency content for beat detection.
- **Parameter Tuning:** Adjust `analysis_window` and `confidence_threshold` based on your audio content:
  - Faster music: Use shorter analysis windows (1.0-2.0 seconds)
  - Slower music: Use longer analysis windows (3.0-5.0 seconds)
  - Noisy environments: Increase confidence threshold (0.4-0.6)
- **Chain Setup:** Connect directly after `AUDIO Microphone Loader @ vrch.ai` using the `RAW_DATA` output for real-time detection.

**Note:** BPM detection requires consistent audio input with discernible rhythmic patterns. The algorithm performs best with music containing clear beats and may struggle with highly ambient or arhythmic audio content.

---

### Node: `AUDIO Music to Emotion Detector @ vrch.ai` (vrch.ai/audio)

1. **Add the `AUDIO Music to Emotion Detector @ vrch.ai` node to your ComfyUI workflow.**
2. **Configure the Node:**
   - **Audio Input (`audio`):** Connect an `AUDIO` input from a previous node in the workflow, such as an audio recorder, file loader, or microphone loader.
   - **Analysis Parameters:**
     - `threshold`: Set the probability threshold for mood detection (0.0-1.0, default: 0.5). Only moods with probabilities above this threshold will be included in the output.
     - `debug`: Enable debug logging to show detailed processing information and intermediate results.
3. **Music Emotion Analysis:**
   - The node uses advanced Music2Emotion deep learning models to analyze audio for emotional content.
   - **Emotion Recognition:** Predicts multiple mood categories with confidence scores.
   - **Valence & Arousal:** Provides dimensional emotion analysis on a 1-9 scale:
     - **Valence:** Measures positive vs. negative emotional content (1=very negative, 9=very positive).
     - **Arousal:** Measures energy and activation level (1=very calm, 9=very energetic).
4. **Outputs:**
   - `AUDIO`: Passthrough of the original audio for further processing.
   - `RAW_DATA`: Complete analysis results in JSON format containing all detected moods, probabilities, and metadata.
   - `MOODS`: Formatted text output showing detected moods with their probabilities, displayed as:
     ```
     children: 0.9540
     fun: 0.9500
     funny: 0.9300
     happy: 0.8980
     upbeat: 0.8890
     ```
   - `VALENCE`: Emotional valence value (1.0-9.0) representing positive/negative sentiment.
   - `AROUSAL`: Emotional arousal value (1.0-9.0) representing energy/activation level.
5. **Mood Categories:**
   - The system can detect various musical moods including: happy, sad, energetic, calm, dramatic, romantic, epic, dark, upbeat, melancholic, aggressive, peaceful, triumphant, mysterious, and many others.
   - Each mood is assigned a probability score (0.0-1.0) indicating the confidence of detection.

**Technical Features:**
- **Multi-Modal Analysis:** Combines spectral, harmonic, and temporal audio features for comprehensive emotion detection.
- **Real-Time Processing:** Optimized for real-time analysis of audio streams.
- **Threshold Filtering:** Customizable probability thresholds to focus on high-confidence predictions.
- **Comprehensive Output:** Provides both human-readable formatted output and machine-readable JSON data.

**Applications:**
- Music recommendation systems based on emotional content
- Automatic playlist generation and categorization
- Audio-reactive visual effects synchronized with emotional content
- Content analysis for media production and post-production
- Therapeutic and wellness applications using music emotion
- Interactive installations responding to musical mood
- Educational tools for music theory and emotion studies

**Usage Tips:**
- **Audio Quality:** Works best with clear, well-recorded audio. Background noise may affect accuracy.
- **Threshold Setting:** 
  - Lower thresholds (0.2-0.4): Show more mood predictions, including less confident ones.
  - Higher thresholds (0.5-0.8): Focus on strong, confident mood predictions.
- **Audio Length:** Optimal results with audio segments of 10-30 seconds. Very short clips may have limited emotional context.
- **Music Types:** Performs well across various genres including pop, rock, classical, electronic, and acoustic music.

**Installation Requirements:**
- This node requires the Music2Emotion third-party module to be installed.
- If the module is not available, the node will display a warning message but remain functional for workflow compilation.
- Follow the installation instructions to download and set up the Music2emotion GitHub repository.

---

### Node: `AUDIO Visualizer @ vrch.ai` (vrch.ai/audio)

1. **Add the `AUDIO Visualizer @ vrch.ai` node to your ComfyUI workflow.**
2. **Connect Audio Data:**
   - Connect `raw_data` input to the `RAW_DATA` output from an `AUDIO Microphone Loader @ vrch.ai` node.
3. **Configure the Node:**
   - **Image Size:** Set `image_width` (256-2048) and `image_height` (128-1024) for output images.
   - **Color Scheme:** Choose from `colorful` (rainbow), `monochrome` (grayscale), `neon` (bright colors), or `plasma` (red-purple-blue).
   - **Colors:** Set `background_color` and `waveform_color` in hex format (e.g., "#111111").
   - **Waveform:** Adjust `waveform_amplification` (0.1-10.0) to enhance quiet signals or reduce loud ones.
   - **Style:** Set `line_width` (1-10) for waveform thickness.
4. **Outputs:**
   - `WAVEFORM_IMAGE`: Time-domain audio signal visualization with center reference line.
   - `SPECTRUM_IMAGE`: Frequency-domain visualization with color-coded intensity bars.

**Usage Tips:**
- Use amplification 2.0-5.0 for quiet audio, 0.3-0.8 for loud audio.
- Choose contrasting colors for better visibility.
- Larger images provide more detail but may impact performance.

**Applications:**
- Real-time audio monitoring and music visualization
- Audio debugging and educational demonstrations
- Creative visual effects synchronized with audio

**Note:** Connect directly after the microphone loader for optimal real-time performance.