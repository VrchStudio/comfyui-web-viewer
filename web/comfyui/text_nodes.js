import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "vrch.TextSrtPlayerNode",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchTextSrtPlayerNode") {
            // Obtain required widgets
            const srtTextWidget = node.widgets.find(w => w.name === "srt_text");
            const loopWidget = node.widgets.find(w => w.name === "loop");
            const currentSelectionWidget = node.widgets.find(w => w.name === "current_selection");
            const debugWidget = node.widgets.find(w => w.name === "debug");

            // Player state variables
            let isPlaying = false;
            let timerId = null;
            let playbackTime = 0; // Current playback time in seconds
            let lastResumeTimestamp = 0; // Timestamp when playback last resumed
            let srtEntries = []; // Parsed SRT entries array
            let shouldLoop = loopWidget ? loopWidget.value : false;

            // Debug logging function: logs messages when debug is enabled
            const debugLog = (msg) => {
                if (debugWidget && debugWidget.value) {
                    console.log("[VrchTextSrtPlayerNode]", msg);
                }
            };

            // Convert time string "HH:MM:SS,mmm" to seconds (as a float)
            function timeToSeconds(timeStr) {
                const parts = timeStr.split(/[:,]/);
                const hours = parseInt(parts[0], 10);
                const minutes = parseInt(parts[1], 10);
                const seconds = parseInt(parts[2], 10);
                const milliseconds = parseInt(parts[3], 10);
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
            }

            // Format seconds as "M:SS" (e.g. 65 -> "1:05")
            function formatTime(sec) {
                const m = Math.floor(sec / 60);
                const s = Math.floor(sec % 60);
                return m + ":" + (s < 10 ? "0" + s : s);
            }

            // Parse SRT text, return an array of objects containing index, start (in seconds), end (in seconds), and content
            function parseSRTText(srtText) {
                const entries = [];
                const blocks = srtText.split(/\r?\n\r?\n/);
                blocks.forEach(block => {
                    block = block.trim();
                    if (!block) return;
                    const lines = block.split(/\r?\n/);
                    if (lines.length < 2) return; // At least index and time line are required
                    const index = parseInt(lines[0], 10);
                    const timeLine = lines[1];
                    const timeMatch = timeLine.match(/(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})/);
                    if (!timeMatch) return;
                    const start = timeToSeconds(timeMatch[1]);
                    const end = timeToSeconds(timeMatch[2]);
                    const content = lines.slice(2).join("\n");
                    entries.push({ index, start, end, content });
                });
                debugLog("Parsed " + entries.length + " SRT entries.");
                return entries;
            }

            // Update current subtitle selection based on playback time (1-based index, set to -1 if not within any subtitle interval)
            function updateCurrentSelection() {
                if (!srtEntries || srtEntries.length === 0) return;
                let selectedIndex = -1;
                for (let i = 0; i < srtEntries.length; i++) {
                    const entry = srtEntries[i];
                    if (playbackTime >= entry.start && playbackTime < entry.end) {
                        selectedIndex = i + 1;
                        break;
                    }
                }
                if (currentSelectionWidget) {
                    currentSelectionWidget.value = selectedIndex;
                    debugLog("Updated current selection to: " + selectedIndex);
                }
            }

            // Update the text in the time display area
            function updateTimeDisplay() {
                timeDisplay.textContent = "Current time: " + playbackTime.toFixed(2) + " sec";
            }

            // Create or update tick labels at 0%, 25%, 50%, 75%, and 100% of the total duration,
            // each with a small vertical marker above the label.
            function createTickLabels(duration) {
                tickLabelsContainer.innerHTML = "";
                if (duration <= 0) return;

                // We want 5 tick positions: 0%, 25%, 50%, 75%, 100%
                const fractions = [0, 0.25, 0.5, 0.75, 1.0];
                fractions.forEach(frac => {
                    const labelTime = frac * duration;

                    // Container for marker + label
                    const labelDiv = document.createElement("div");
                    labelDiv.style.display = "flex";
                    labelDiv.style.flexDirection = "column";
                    labelDiv.style.alignItems = "center";

                    // The small vertical bar (marker) above the label
                    const marker = document.createElement("div");
                    marker.classList.add("vrch-srt-tick-marker");
                    // For example, you could also use marker.textContent = "|" if you want a direct symbol

                    // The time label below the marker
                    const label = document.createElement("div");
                    label.classList.add("vrch-srt-tick-label");
                    label.textContent = formatTime(labelTime);

                    labelDiv.appendChild(marker);
                    labelDiv.appendChild(label);
                    tickLabelsContainer.appendChild(labelDiv);
                });
            }

            // Timer tick function: update playback time, subtitle selection, time display, and slider
            function tick() {
                if (!isPlaying) return;
                const now = Date.now();
                const delta = (now - lastResumeTimestamp) / 1000;
                playbackTime += delta;
                lastResumeTimestamp = now;
                debugLog("Playback time: " + playbackTime.toFixed(2) + " sec");
                updateCurrentSelection();
                updateTimeDisplay();
                // Update the slider value
                slider.value = playbackTime;

                // Check if playback has reached the end time of the last subtitle
                if (srtEntries.length > 0 && playbackTime >= srtEntries[srtEntries.length - 1].end) {
                    if (shouldLoop) {
                        debugLog("Loop mode active, restarting playback.");
                        playbackTime = 0;
                        lastResumeTimestamp = Date.now();
                        pausePlayback();
                        startPlayback();
                    } else {
                        debugLog("Playback finished, stopping.");
                        pausePlayback();
                    }
                }
            }

            // Start or resume playback: parse SRT text and start the timer, also update slider max value and tick labels
            function startPlayback() {
                if (isPlaying) return;
                if (srtTextWidget) {
                    srtEntries = parseSRTText(srtTextWidget.value);
                    if (srtEntries.length > 0) {
                        slider.max = srtEntries[srtEntries.length - 1].end;
                        createTickLabels(srtEntries[srtEntries.length - 1].end);
                    } else {
                        slider.max = 0;
                        createTickLabels(0);
                    }
                }
                isPlaying = true;
                lastResumeTimestamp = Date.now();
                timerId = setInterval(tick, 100);
                playPauseButton.textContent = "Pause";
                debugLog("Playback started.");
            }

            // Pause playback: stop the timer but keep current playback time
            function pausePlayback() {
                if (!isPlaying) return;
                isPlaying = false;
                if (timerId) {
                    clearInterval(timerId);
                    timerId = null;
                }
                playPauseButton.textContent = "Play SRT File";
                debugLog("Playback paused at " + playbackTime.toFixed(2) + " sec.");
            }

            // Reset playback: pause and reset time to start, also update slider display
            function resetPlayback() {
                pausePlayback();
                playbackTime = 0;
                updateCurrentSelection();
                updateTimeDisplay();
                slider.value = playbackTime;
                debugLog("Playback reset.");
            }

            // Create a container for widgets, with a fixed height
            const widgetContainer = document.createElement("div");
            widgetContainer.style.setProperty("height", "120px", "important");
            widgetContainer.style.display = "flex";
            widgetContainer.style.flexDirection = "column";
            widgetContainer.style.justifyContent = "center";
            widgetContainer.style.alignItems = "center";

            // Create a container for buttons, arranged vertically and centered
            const buttonsContainer = document.createElement("div");
            buttonsContainer.style.display = "flex";
            buttonsContainer.style.flexDirection = "column";
            buttonsContainer.style.alignItems = "center";
            buttonsContainer.style.gap = "10px";

            // Create the Play/Pause button, initial state "Play SRT File"
            const playPauseButton = document.createElement("button");
            playPauseButton.textContent = "Play SRT File";
            playPauseButton.classList.add("vrch-srt-big-button");
            playPauseButton.onclick = () => {
                if (isPlaying) {
                    pausePlayback();
                } else {
                    startPlayback();
                }
            };

            // Create the Reset button
            const resetButton = document.createElement("button");
            resetButton.textContent = "Reset";
            resetButton.classList.add("vrch-srt-big-button", "vrch-srt-reset-button");
            resetButton.onclick = () => {
                resetPlayback();
            };

            // Append buttons to the buttons container
            buttonsContainer.appendChild(playPauseButton);
            buttonsContainer.appendChild(resetButton);

            // Create the progress slider
            const slider = document.createElement("input");
            slider.type = "range";
            slider.min = 0;
            slider.step = 0.01; // Allow adjustment in fractions of a second
            slider.value = playbackTime;
            slider.classList.add("vrch-srt-slider");

            // When the user drags the slider, update playback time and related displays
            slider.addEventListener("input", (e) => {
                playbackTime = parseFloat(slider.value);
                lastResumeTimestamp = Date.now();
                updateCurrentSelection();
                updateTimeDisplay();
                debugLog("Slider adjusted to: " + playbackTime.toFixed(2) + " sec.");
            });

            // Create a container for the tick labels below the slider
            const tickLabelsContainer = document.createElement("div");
            tickLabelsContainer.style.display = "flex";
            tickLabelsContainer.style.justifyContent = "space-between";
            tickLabelsContainer.style.width = "100%";
            tickLabelsContainer.style.marginTop = "5px";

            // Create a small display area to show playback time
            const timeDisplay = document.createElement("div");
            timeDisplay.classList.add("vrch-srt-small-display");
            timeDisplay.textContent = "Current time: 0.00 sec";

            // Append the buttons container, slider, tick labels, and time display to the main container in order
            widgetContainer.appendChild(buttonsContainer);
            widgetContainer.appendChild(slider);
            widgetContainer.appendChild(tickLabelsContainer);
            widgetContainer.appendChild(timeDisplay);

            // Add the main container as a component to the node
            node.addDOMWidget("srt_control_widget", "SRT Control", widgetContainer);

            // Listen for changes to the loop widget
            if (loopWidget) {
                loopWidget.callback = (value) => {
                    shouldLoop = value;
                    debugLog("Loop setting changed to: " + value);
                };
            }

            // If the srt_text widget value changes, re-parse and update the slider's max value and tick labels
            if (srtTextWidget) {
                srtTextWidget.callback = (value) => {
                    srtEntries = parseSRTText(value);
                    if (srtEntries.length > 0) {
                        slider.max = srtEntries[srtEntries.length - 1].end;
                        createTickLabels(srtEntries[srtEntries.length - 1].end);
                    } else {
                        slider.max = 0;
                        createTickLabels(0);
                    }
                    debugLog("srt_text updated, slider max set to: " + slider.max);
                };
            }

            // Clear the timer when the node is removed
            const onRemoved = this.onRemoved;
            this.onRemoved = function () {
                if (timerId) {
                    clearInterval(timerId);
                    timerId = null;
                }
                return onRemoved?.();
            };
        }
    }
});

// Insert custom CSS styles
const srtButtonStyle = document.createElement("style");
srtButtonStyle.textContent = `
    .vrch-srt-big-button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        width: 100%;
        height: 60px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
        margin-top: 20px;
        padding: 8px 16px;
    }
    
    .vrch-srt-big-button:hover {
        background-color: #45a049;
    }
    
    .vrch-srt-big-button:active {
        background-color: #3e8e41;
    }
    
    /* Grey style for the Reset button */
    .vrch-srt-reset-button {
        height: 40px;
        margin-top: 10px;
        background-color: #757575;
    }
    
    .vrch-srt-reset-button:hover {
        background-color: #616161;
    }
    
    .vrch-srt-reset-button:active {
        background-color: #424242;
    }
    
    /* Style for the slider */
    .vrch-srt-slider {
        width: 100%;
        margin-top: 30px; /* Additional space from the buttons */
        -webkit-appearance: none;
        appearance: none;
        background: transparent;
    }

    /* Slider track (default gray) */
    .vrch-srt-slider::-webkit-slider-runnable-track {
        height: 6px;
        background: #ddd;
        border-radius: 3px;
        cursor: pointer;
    }
    .vrch-srt-slider::-moz-range-track {
        height: 6px;
        background: #ddd;
        border-radius: 3px;
        cursor: pointer;
    }

    /* Slider thumb (solid theme color), with basic hover/active animation */
    .vrch-srt-slider::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 24px;
        height: 24px;
        background: #4CAF50;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        margin-top: -9px; /* center on the track (half thumb size + half track height) */
        transition: transform 0.2s, background 0.2s;
    }
    .vrch-srt-slider::-webkit-slider-thumb:hover {
        transform: scale(1.1);
        background: #45a049;
    }
    .vrch-srt-slider::-webkit-slider-thumb:active {
        transform: scale(1.2);
        background: #3e8e41;
    }

    .vrch-srt-slider::-moz-range-thumb {
        width: 24px;
        height: 24px;
        background: #4CAF50;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        transition: transform 0.2s, background 0.2s;
    }
    .vrch-srt-slider::-moz-range-thumb:hover {
        transform: scale(1.1);
        background: #45a049;
    }
    .vrch-srt-slider::-moz-range-thumb:active {
        transform: scale(1.2);
        background: #3e8e41;
    }

    /* Small display area for the current time */
    .vrch-srt-small-display {
        font-size: 14px;
        color: #666;
        margin-top: 20px;
        width: 100%;
        text-align: center;
    }

    /* Tick marker and label styles */
    .vrch-srt-tick-marker {
        width: 2px;
        height: 8px;
        background-color: #333;
        margin-bottom: 2px; /* small gap between marker and label */
    }
    .vrch-srt-tick-label {
        font-size: 12px;
        color: #666;
    }
`;
document.head.appendChild(srtButtonStyle);