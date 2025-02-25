// text_nodes.js

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "vrch.TextSrtPlayerNode",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchTextSrtPlayerNode") {
            // Get required widgets
            const srtTextWidget = node.widgets.find(w => w.name === "srt_text");
            const loopWidget = node.widgets.find(w => w.name === "loop");
            const currentSelectionWidget = node.widgets.find(w => w.name === "current_selection");
            const debugWidget = node.widgets.find(w => w.name === "debug");

            // Player state variables
            let isPlaying = false;
            let timerId = null;
            let playbackTime = 0; // current playback time in seconds
            let lastResumeTimestamp = 0; // timestamp when playback last resumed
            let srtEntries = []; // parsed SRT entries array
            let shouldLoop = loopWidget ? loopWidget.value : false;

            // Debug logging function: logs messages if debug widget is enabled
            const debugLog = (msg) => {
                if (debugWidget && debugWidget.value) {
                    console.log("[VrchTextSrtPlayerNode]", msg);
                }
            };

            // Converts a time string "HH:MM:SS,mmm" to seconds (as a float)
            function timeToSeconds(timeStr) {
                const parts = timeStr.split(/[:,]/);
                const hours = parseInt(parts[0], 10);
                const minutes = parseInt(parts[1], 10);
                const seconds = parseInt(parts[2], 10);
                const milliseconds = parseInt(parts[3], 10);
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
            }

            // Function to parse SRT text and return an array of entries.
            // Each entry contains: index, start (in seconds), end (in seconds), and content.
            function parseSRTText(srtText) {
                const entries = [];
                const blocks = srtText.split(/\r?\n\r?\n/);
                blocks.forEach(block => {
                    block = block.trim();
                    if (!block) return;
                    const lines = block.split(/\r?\n/);
                    if (lines.length < 2) return; // must have at least index and time line
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

            // Updates the current selection widget based on the current playback time.
            // If playback time is outside any subtitle interval, set current_selection to -1.
            function updateCurrentSelection() {
                if (!srtEntries || srtEntries.length === 0) return;
                let selectedIndex = -1;
                for (let i = 0; i < srtEntries.length; i++) {
                    const entry = srtEntries[i];
                    if (playbackTime >= entry.start && playbackTime < entry.end) {
                        selectedIndex = i + 1; // 1-based index
                        break;
                    }
                }
                if (currentSelectionWidget) {
                    currentSelectionWidget.value = selectedIndex;
                    debugLog("Updated current selection to: " + selectedIndex);
                }
            }

            // Timer tick function: updates playback time and current selection periodically
            function tick() {
                if (!isPlaying) return;
                const now = Date.now();
                const delta = (now - lastResumeTimestamp) / 1000;
                playbackTime += delta;
                lastResumeTimestamp = now;
                debugLog("Playback time: " + playbackTime.toFixed(2) + " sec");
                updateCurrentSelection();

                // Check if playback has reached the end of the last entry
                if (srtEntries.length > 0 && playbackTime >= srtEntries[srtEntries.length - 1].end) {
                    if (shouldLoop) {
                        debugLog("Loop mode active, restarting playback.");
                        playbackTime = 0;
                        lastResumeTimestamp = Date.now();
                    } else {
                        debugLog("Playback finished, stopping.");
                        pausePlayback();
                    }
                }
            }

            // Starts or resumes playback: parses SRT text and starts the timer
            function startPlayback() {
                if (isPlaying) return;
                if (srtTextWidget) {
                    srtEntries = parseSRTText(srtTextWidget.value);
                }
                isPlaying = true;
                lastResumeTimestamp = Date.now();
                timerId = setInterval(tick, 100);
                playPauseButton.textContent = "Pause";
                debugLog("Playback started.");
            }

            // Pauses playback: stops the timer and retains current playback time
            function pausePlayback() {
                if (!isPlaying) return;
                isPlaying = false;
                if (timerId) {
                    clearInterval(timerId);
                    timerId = null;
                }
                playPauseButton.textContent = "Play";
                debugLog("Playback paused at " + playbackTime.toFixed(2) + " sec.");
            }

            // Resets playback: pauses playback and resets time to the beginning
            function resetPlayback() {
                pausePlayback();
                playbackTime = 0;
                updateCurrentSelection();
                debugLog("Playback reset.");
            }

            // Create the Play/Pause button; initial state is "Play"
            const playPauseButton = document.createElement("button");
            playPauseButton.textContent = "Play";
            playPauseButton.classList.add("comfy-big-button");
            playPauseButton.onclick = () => {
                if (isPlaying) {
                    pausePlayback();
                } else {
                    startPlayback();
                }
            };
            node.addDOMWidget("play_pause_button", "Play / Pause", playPauseButton);

            // Create the Reset button
            const resetButton = document.createElement("button");
            resetButton.textContent = "Reset";
            resetButton.classList.add("comfy-big-button");
            resetButton.onclick = () => {
                resetPlayback();
            };
            node.addDOMWidget("reset_button", "Reset", resetButton);

            // Monitor changes to the loop widget
            if (loopWidget) {
                loopWidget.callback = (value) => {
                    shouldLoop = value;
                    debugLog("Loop setting changed to: " + value);
                };
            }

            // Cleanup timer when the node is removed
            node.onRemoved = function () {
                if (timerId) {
                    clearInterval(timerId);
                    timerId = null;
                }
            };
        }
    }
});