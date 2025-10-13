import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

import { 
    triggerNewGeneration, 
    createMicrophoneControls
} from "./node_utils.js";

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
                let shortcutKeyPressed = false; // Flag to handle shortcut key status (keyboard)
                let holdPressed = false; // Flag for mouse press-and-hold on the button
                let currentSession = null; // holds the latest recording session object
                let cooldownUntil = 0; // timestamp ms for short cooldown after stop
                const COOL_DOWN_MS = 300; // minimal cooldown to debounce rapid toggles

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.type = "hidden";
                }

                const deviceIdWidget = currentNode.widgets.find(w => w.name === "device_id");
                const deviceNameWidget = currentNode.widgets.find(w => w.name === "device_name");
                const debugWidget = currentNode.widgets.find(w => w.name === "debug");

                const isDebugEnabled = () => !!(debugWidget && debugWidget.value);
                const debugLog = (...args) => {
                    if (isDebugEnabled()) {
                        console.log("[VrchAudioRecorderNode]", ...args);
                    }
                };
                const debugError = (...args) => {
                    if (isDebugEnabled()) {
                        console.error("[VrchAudioRecorderNode]", ...args);
                    } else {
                        console.error(...args);
                    }
                };

                if (debugWidget) {
                    const originalDebugCallback = debugWidget.callback;
                    debugWidget.callback = (value) => {
                        if (originalDebugCallback) {
                            originalDebugCallback(value);
                        }
                        if (value) {
                            console.log("[VrchAudioRecorderNode] Debug enabled");
                        }
                    };
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

                // Microphone selector block
                const micContainer = document.createElement("div");
                micContainer.classList.add("mic-visualizer-container");

                const micControls = createMicrophoneControls({
                    onDeviceChange: (deviceId) => {
                        updateDeviceWidgets(deviceId);
                        syncStatus();
                    },
                    onMuteChange: () => {
                        if (currentSession && currentSession.stream) {
                            currentSession.stream.getAudioTracks().forEach(track => {
                                track.enabled = !micControls.getMuted();
                            });
                        }
                        debugLog("Mute state:", micControls.getMuted());
                        syncStatus();
                    }
                });
                micContainer.appendChild(micControls.container);

                const micWidget = this.addDOMWidget("mic_selector_widget", "Microphone", micContainer);
                micWidget.computeSize = function(width) {
                    return [width, 140];
                };

                const updateDeviceWidgets = (deviceId) => {
                    if (deviceIdWidget) {
                        deviceIdWidget.value = deviceId || "";
                    }
                    if (deviceNameWidget) {
                        const selected = micControls.devices().find(device => device.deviceId === deviceId);
                        deviceNameWidget.value = selected && selected.label ? selected.label : "";
                    }
                    debugLog("Device selected:", deviceId || "(none)");
                };

                const syncStatus = () => {
                    if (!micControls.getSelection()) {
                        micControls.setStatus("No device");
                    } else if (micControls.getMuted()) {
                        micControls.setStatus("Muted");
                    } else {
                        micControls.setStatus(isRecording ? "Recording" : "Ready");
                    }
                };
                syncStatus();

                const refreshMicrophones = async ({ requestAccess = false } = {}) => {
                    micControls.setStatus("Loading");
                    try {
                        const devices = await micControls.refreshDevices({
                            requestAccess,
                            logPrefix: "[VrchAudioRecorderNode]",
                        });
                        if (deviceIdWidget && deviceIdWidget.value) {
                            micControls.setSelection(deviceIdWidget.value);
                        }
                        updateDeviceWidgets(micControls.getSelection());
                        syncStatus();
                        debugLog(`Microphone list refreshed (${devices.length})`);
                    } catch (error) {
                        micControls.setStatus("Error");
                        debugError("Failed to refresh microphone list", error);
                    }
                };

                micControls.reloadButton.addEventListener("click", () => {
                    refreshMicrophones({ requestAccess: true });
                });

                // Default shortcut settings
                let enableShortcut = false;
                let selectedShortcut = 'F2';

                // Retrieve settings from widgets
                const enableShortcutWidget = currentNode.widgets.find(w => w.name === 'shortcut');
                const shortcutOptionWidget = currentNode.widgets.find(w => w.name === 'shortcut_key');
                const recordModeWidget = currentNode.widgets.find(w => w.name === 'record_mode');
                const newGenerationWidget = currentNode.widgets.find(w => w.name === 'new_generation_after_recording');

                const shouldAutoLoop = () => {
                    const loopWidget = currentNode.widgets.find(w => w.name === 'loop');
                    return !!(loopWidget && loopWidget.value === true && recordModeWidget && recordModeWidget.value === 'start_and_stop');
                };

                const scheduleLoopRestart = () => {
                    const loopIntervalWidget = currentNode.widgets.find(w => w.name === 'loop_interval');
                    const loopInterval = (loopIntervalWidget && loopIntervalWidget.value) ? loopIntervalWidget.value : 0.5;

                    const attemptRestart = () => {
                        if (!shouldAutoLoop()) {
                            return;
                        }
                        if (isStopping) {
                            loopIntervalTimer = setTimeout(attemptRestart, 100);
                            return;
                        }
                        startRecording();
                    };

                    loopIntervalTimer = setTimeout(attemptRestart, loopInterval * 1000);
                };

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
                        debugLog("Shortcut key pressed");
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
                        debugLog("Shortcut key released");
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
                        startBtn.onmousedown = () => { holdPressed = true; startRecording(); };
                        startBtn.onmouseup = () => { holdPressed = false; stopRecording(true); }; // manual stop
                        startBtn.onmouseleave = () => { holdPressed = false; stopRecording(true); }; // manual stop
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
                        debugLog("Start ignored due to active recording or cooldown");
                        return;
                    }

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        debugError('Browser does not support audio recording');
                        micControls.setStatus("Error");
                        return;
                    }

                    if (loopIntervalTimer) {
                        clearTimeout(loopIntervalTimer);
                        loopIntervalTimer = null;
                    }

                    isRecording = true;
                    isStopping = false;

                    micControls.setStatus("Requesting");

                    const selectedDeviceId = micControls.getSelection();
                    const mediaConstraints = selectedDeviceId
                        ? { audio: { deviceId: { exact: selectedDeviceId } } }
                        : { audio: true };

                    navigator.mediaDevices.getUserMedia(mediaConstraints)
                        .then((stream) => {
                            // If recording was cancelled before permissions resolved, abort cleanly
                            const isPressAndHold = recordModeWidget && recordModeWidget.value === 'press_and_hold';
                            const stillHolding = shortcutKeyPressed || holdPressed;
                            if (!isRecording || isStopping || (isPressAndHold && !stillHolding)) {
                                try { stream.getTracks().forEach(t => t.stop()); } catch (e) {}
                                // Ensure state is consistent and UI reflects idle
                                isRecording = false;
                                syncStatus();
                                switchButtonMode(recordModeWidget.value);
                                return; // do not start a recorder anymore
                            }
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
                            stream.getAudioTracks().forEach(track => {
                                track.enabled = !micControls.getMuted();
                            });
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
                                    if (shouldAutoLoop()) {
                                        cooldownUntil = Date.now();
                                    }
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

                                    debugLog('Audio recording saved');

                                    // Trigger a new queue job if `new_generation_after_recording` is enabled
                                    if (newGenerationWidget && newGenerationWidget.value === true) {
                                        triggerNewGeneration();
                                    }

                                    // finalize stop state and start cooldown
                                    isStopping = false;
                                    cooldownUntil = Date.now() + COOL_DOWN_MS;
                                    if (shouldAutoLoop()) {
                                        cooldownUntil = Date.now();
                                    }
                                    syncStatus();

                                };
                                reader.readAsDataURL(audioBlob);
                            };
                            mediaRecorder.start();

                            switchButtonMode(recordModeWidget.value);

                            updateDeviceWidgets(selectedDeviceId);
                            syncStatus();
                            debugLog('Recording started');

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
                            debugError('Error accessing audio devices.', error);
                            // reset state if we failed to start
                            isRecording = false;
                            isStopping = false;
                            countdownDisplay.textContent = '';
                            micControls.setStatus("Error");
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
                        debugLog('Recording stopped manually');
                    } else if (shouldAutoLoop()) {
                        // Auto-stop: schedule restart after interval
                        scheduleLoopRestart();
                        debugLog('Recording will restart after loop interval');
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
                        if (shouldAutoLoop()) {
                            cooldownUntil = Date.now();
                        }
                    }

                    isRecording = false;
                    switchButtonMode(recordModeWidget.value);
                    syncStatus();
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
                    debugLog("init() - shortcut enabled:", enableShortcut, "key:", selectedShortcut);
                }

                // Initialize display after ensuring all widgets are loaded
                async function delayedInit() {
                    init();
                    await refreshMicrophones({ requestAccess: true });
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
