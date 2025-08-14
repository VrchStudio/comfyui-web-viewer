import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { triggerNewGeneration } from "./node_utils.js";

app.registerExtension({
    name: "vrch.AudioSaverNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchAudioSaverNode") {
            nodeData.input.required.audioUI = ['AUDIO_UI', {}]
        }
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchAudioSaverNode") {

            const audioUIWidget = node.widgets.find(w => w.name === "audioUI");
            const enablePreviewWidget = node.widgets.find(w => w.name === "enable_preview");

            if (enablePreviewWidget) {
                enablePreviewWidget.callback = (value) => {
                    if (audioUIWidget) {
                        if (value) {
                            audioUIWidget.element.classList.remove("empty-audio-widget");
                        } else {
                            audioUIWidget.element.classList.add("empty-audio-widget");
                        }
                    }
                };
            }

            node.onExecuted = function(message) {
                if (message != null && message.audio) {
                    if (audioUIWidget) {
                        const audio = message.audio[0];
                        audioUIWidget.element.src = api.apiURL(
                            `/view?filename=${encodeURIComponent(audio.filename)}&type=${audio.type}&subfolder=${encodeURIComponent(audio.subfolder)}`
                        );
                        audioUIWidget.element.classList.remove("empty-audio-widget");
                    }
                }
            };
        }
    }
});

app.registerExtension({
    name: 'vrch.AudioRecorderNode',
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === 'VrchAudioRecorderNode') {
            nodeData.input.required.audioUI = ['AUDIO_UI', {}]

            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const currentNode = this;

                let mediaRecorder;
                // NOTE: Avoid shared mutable chunks across sessions; use session-scoped chunks instead.
                // let audioChunks = [];
                let isRecording = false;
                let isStopping = false; // prevent re-entrant stop
                let recordingTimer;
                let loopIntervalTimer;
                let shortcutKeyPressed = false; // Flag to handle shortcut key status
                let currentSession = null; // holds the latest recording session object
                let cooldownUntil = 0; // timestamp ms for short cooldown after stop
                const COOL_DOWN_MS = 300; // minimal cooldown to debounce rapid toggles

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.type = "hidden";
                }

                // Create a custom button element
                const startBtn = document.createElement("div");
                startBtn.textContent = "";
                startBtn.classList.add("comfy-vrch-big-button");

                const countdownDisplay = document.createElement("div");
                countdownDisplay.classList.add("comfy-vrch-value-small-display");

                // Add the button and tag to the node using addDOMWidget
                this.addDOMWidget("button_widget", "Press and Hold to Record", startBtn);
                this.addDOMWidget("text_widget", "Countdown Display", countdownDisplay);

                // Default shortcut settings
                let enableShortcut = false;
                let selectedShortcut = 'F2';

                // Retrieve settings from widgets
                const enableShortcutWidget = currentNode.widgets.find(w => w.name === 'shortcut');
                const shortcutOptionWidget = currentNode.widgets.find(w => w.name === 'shortcut_key');
                const recordModeWidget = currentNode.widgets.find(w => w.name === 'record_mode');
                const newGenerationWidget = currentNode.widgets.find(w => w.name === 'new_generation_after_recording');

                if (enableShortcutWidget) {
                    enableShortcut = enableShortcutWidget.value;
                    enableShortcutWidget.callback = (value) => {
                        enableShortcut = value;
                    };
                }

                if (shortcutOptionWidget) {
                    selectedShortcut = shortcutOptionWidget.value;
                    shortcutOptionWidget.callback = (value) => {
                        selectedShortcut = value;
                    };
                }

                if (recordModeWidget) {
                    recordModeWidget.callback = (value) => {
                        switchButtonMode(recordModeWidget.value);
                        // Save the current record mode to localStorage
                        localStorage.setItem('vrch_audio_recorder_record_mode', recordModeWidget.value);
                    };
                }

                // Handle keyboard press events based on record mode
                const handleKeyPress = (event) => {
                    if (enableShortcut && event.key === selectedShortcut) {
                        console.log("shortcut key pressed");
                        if (recordModeWidget.value === 'press_and_hold') {
                            if (!shortcutKeyPressed) {
                                shortcutKeyPressed = true; // Mark shortcut as pressed
                                startRecording();
                            }
                        } else if (recordModeWidget.value === 'start_and_stop') {
                            if (isRecording) {
                                stopRecording(true); // Manual stop
                            } else {
                                startRecording();
                            }
                        }
                    }
                };

                const handleKeyRelease = (event) => {
                    if (enableShortcut && event.key === selectedShortcut && recordModeWidget.value === 'press_and_hold') {
                        console.log("shortcut key released");
                        if (shortcutKeyPressed) {
                            stopRecording(true); // Manual stop on key release
                            shortcutKeyPressed = false; // Reset flag
                        }
                    }
                };

                // Add global keydown and keyup event listeners
                window.addEventListener('keydown', handleKeyPress);
                window.addEventListener('keyup', handleKeyRelease);

                const switchButtonMode = (mode) => {
                    const loopWidget = currentNode.widgets.find(w => w.name === 'loop');
                    const isLoopEnabled = loopWidget && loopWidget.value === true;

                    if (mode === 'press_and_hold') {
                        startBtn.innerText = isRecording ? 'Recording...' : 'Press and Hold to Record';
                        startBtn.onmousedown = startRecording;
                        startBtn.onmouseup = () => stopRecording(true); // manual stop
                        startBtn.onmouseleave = () => stopRecording(true); // manual stop
                        startBtn.onclick = null;
                    } else if (mode === 'start_and_stop') {
                        if (isRecording) {
                            startBtn.innerText = isLoopEnabled ? 'STOP LOOPING' : 'STOP';
                        } else {
                            startBtn.innerText = 'START';
                        }
                        startBtn.onmousedown = null;
                        startBtn.onmouseup = null;
                        startBtn.onmouseleave = null;
                        startBtn.onclick = () => {
                            if (isRecording) {
                                stopRecording(true); // manual stop
                            } else {
                                startRecording();
                            }
                        };
                    }
                };

                const inCooldown = () => Date.now() < cooldownUntil;

                const startRecording = () => {
                    // Prevent starting while already recording, stopping, or during cooldown
                    if (isRecording || isStopping || inCooldown()) {
                        return;
                    }

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        console.error('Browser does not support audio recording');
                        return;
                    }

                    if (loopIntervalTimer) {
                        clearInterval(loopIntervalTimer);
                        loopIntervalTimer = null;
                    }

                    isRecording = true;
                    isStopping = false;

                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then((stream) => {
                            mediaRecorder = new MediaRecorder(stream, {
                                mimeType: 'audio/webm'
                            });
                            // Create a session scoped container to avoid races between rapid start/stop
                            const session = {
                                id: Symbol('rec'),
                                chunks: [],
                                stream,
                                recorder: mediaRecorder,
                                active: true,
                            };
                            currentSession = session;
                            mediaRecorder.ondataavailable = (event) => {
                                // Only accept data for current active session
                                if (session.active && currentSession === session && event.data && event.data.size > 0) {
                                    session.chunks.push(event.data);
                                }
                            };
                            mediaRecorder.onstop = () => {
                                // Guard: stop may fire after a new session started
                                session.active = false;
                                try { session.stream.getTracks().forEach(t => t.stop()); } catch (e) {}

                                // Drop stale session callback work
                                if (currentSession !== session) {
                                    // ensure state flags progress, but skip UI/trigger
                                    isStopping = false;
                                    cooldownUntil = Date.now() + COOL_DOWN_MS;
                                    return;
                                }

                                const audioBlob = new Blob(session.chunks || [], { type: 'audio/webm' });
                                const reader = new FileReader();

                                reader.onloadend = () => {
                                    const base64data = reader.result.split(',')[1];
                                    const audioBase64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                                    if (audioBase64Widget) {
                                        audioBase64Widget.value = base64data;
                                    }

                                    const audioUIWidget = currentNode.widgets.find(w => w.name === "audioUI");
                                    if (audioUIWidget) {
                                        audioUIWidget.element.src = `data:audio/webm;base64,${base64data}`;
                                        audioUIWidget.element.classList.remove("empty-audio-widget");
                                    }

                                    console.log('Audio recording saved.');

                                    // Trigger a new queue job if `new_generation_after_recording` is enabled
                                    if (newGenerationWidget && newGenerationWidget.value === true) {
                                        triggerNewGeneration();
                                    }

                                    // finalize stop state and start cooldown
                                    isStopping = false;
                                    cooldownUntil = Date.now() + COOL_DOWN_MS;

                                };
                                reader.readAsDataURL(audioBlob);
                            };
                            mediaRecorder.start();

                            switchButtonMode(recordModeWidget.value);

                            console.log('Recording started...');

                            // Start the countdown for maximum recording duration
                            const recordDurationMaxWidget = currentNode.widgets.find(w => w.name === 'record_duration_max');
                            const maxDuration = recordDurationMaxWidget ? recordDurationMaxWidget.value : 10;
                            
                            let remainingTime = maxDuration;
                            const startCountdown = Math.min(10, maxDuration);

                            const updateCountdown = () => {
                                const showTime = Math.max(remainingTime, 0);
                                if (showTime <= startCountdown) {
                                    countdownDisplay.textContent = `Recording will stop in ${showTime} seconds`;
                                } else {
                                    countdownDisplay.textContent = 'Recording...';
                                }

                                if (remainingTime <= 0) {
                                    if (recordingTimer) {
                                        clearInterval(recordingTimer);
                                        recordingTimer = null;
                                    }
                                    if (isRecording) {
                                        stopRecording(false); // auto stop (not manual)
                                    }
                                    return; // do not decrement further
                                }
                                remainingTime--;
                            };

                            // execute immediately
                            updateCountdown();
                            // start timer
                            recordingTimer = setInterval(updateCountdown, 1000);
                        })
                        .catch(error => {
                            console.error('Error accessing audio devices.', error);
                            // reset state if we failed to start
                            isRecording = false;
                            isStopping = false;
                            countdownDisplay.textContent = '';
                            switchButtonMode(recordModeWidget.value);
                        });
                };

                const stopRecording = (isManualStop = false, delay = 300) => {
                    if (isStopping) {
                        return; // already stopping
                    }
                    isStopping = true;

                    // Always clear countdown and loop timers (idempotent cleanup)
                    if (recordingTimer) {
                        clearInterval(recordingTimer);
                        recordingTimer = null;
                    }
                    if (loopIntervalTimer) {
                        clearTimeout(loopIntervalTimer);
                        loopIntervalTimer = null;
                    }
                    countdownDisplay.textContent = '';

                    const loopWidget = currentNode.widgets.find(w => w.name === 'loop');
                    if (isManualStop) {
                        // Manual stop cancels loop immediately
                        if (loopWidget) {
                            loopWidget.value = false;
                            if (loopWidget.callback) {
                                loopWidget.callback(loopWidget.value);
                            }
                        }
                        console.log('Recording stopped manually');
                    } else if (loopWidget && loopWidget.value === true && recordModeWidget.value === 'start_and_stop') {
                        // Auto-stop: schedule restart after interval
                        const loopIntervalWidget = currentNode.widgets.find(w => w.name === 'loop_interval');
                        const loopInterval = (loopIntervalWidget && loopIntervalWidget.value) ? loopIntervalWidget.value : 0.5;
                        loopIntervalTimer = setTimeout(() => {
                            startRecording();
                        }, loopInterval * 1000);
                        console.log('Recording is restarted in a loop');
                    }

                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        setTimeout(() => {
                            try { mediaRecorder.stop(); } catch (e) {}
                            mediaRecorder = null;
                        }, delay);
                    } else {
                        // Not actually recording (e.g., rapid double stop), finalize flags
                        isStopping = false;
                        cooldownUntil = Date.now() + COOL_DOWN_MS;
                    }

                    isRecording = false;
                    switchButtonMode(recordModeWidget.value);
                };

                // Initialize button mode based on the record mode
                // Load settings from localStorage if available
                const savedRecordMode = localStorage.getItem('vrch_audio_recorder_record_mode');
                if (savedRecordMode) {
                    recordModeWidget.value = savedRecordMode;
                }
                switchButtonMode(recordModeWidget.value);

                // Initialize function to ensure widget values are properly loaded
                function init() {
                    if (enableShortcutWidget) {
                        enableShortcut = enableShortcutWidget.value;
                    }
                    if (shortcutOptionWidget) {
                        selectedShortcut = shortcutOptionWidget.value;
                    }
                    console.log("[VrchAudioRecorderNode] init() - shortcut enabled:", enableShortcut, "key:", selectedShortcut);
                }

                // Initialize display after ensuring all widgets are loaded
                function delayedInit() {
                    init();
                }
                setTimeout(delayedInit, 1000);

                const onRemoved = this.onRemoved;
                this.onRemoved = function () {
                    if (recordingTimer) {
                        clearInterval(recordingTimer);
                    }
                    if (loopIntervalTimer) {
                        clearInterval(loopIntervalTimer);
                    }
                    window.removeEventListener('keydown', handleKeyPress);
                    window.removeEventListener('keyup', handleKeyRelease);
                    return onRemoved?.();
                };

                this.serialize_widgets = true; // Ensure widget state is saved
            };
        }
    }
});

// Add custom styles for the button
const style = document.createElement("style");
style.textContent = `
    .comfy-vrch-big-button {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 20px;
        height: 40px !important;
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
    }

    .comfy-vrch-big-button:hover {
        background-color: #45a049;
    }

    .comfy-vrch-big-button:active {
        background-color: #3e8e41;
    }

    .comfy-vrch-value-display {
        margin-top: 20px;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
    }
    
    .comfy-vrch-value-small-display {
        margin-top: 20px;
        font-size: 14px;
        text-align: center;
    }
`;
document.head.appendChild(style);
