import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "vrch.AudioSaverNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchAudioSaverNode") {
            nodeData.input.required.audioUI = ["AUDIO_UI"];
        }
    },
    getCustomWidgets() {
        return {
            AUDIO_UI(node, inputName) {
                const audio = document.createElement("audio");
                audio.controls = true;
                audio.classList.add("comfy-audio");
                audio.setAttribute("name", "media");
                const audioUIWidget = node.addDOMWidget(inputName, "audioUI", audio);
                audioUIWidget.serialize = false;

                if (node.comfyClass === "VrchAudioSaverNode") {
                    audioUIWidget.element.classList.add("empty-audio-widget");
                    node.onExecuted = function(message) {
                        const audios = message.audio;
                        if (!audios) return;
                        const audio = audios[0];
                        audioUIWidget.element.src = api.apiURL(
                            `/view?filename=${encodeURIComponent(audio.filename)}&type=${audio.type}&subfolder=${encodeURIComponent(audio.subfolder)}`
                        );
                        audioUIWidget.element.classList.remove("empty-audio-widget");
                    };
                }

                return { widget: audioUIWidget };
            }
        };
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchAudioSaverNode") {
            node.onExecuted = function(message) {
                if (message.audio) {
                    const audioUIWidget = node.widgets.find(w => w.name === "audioUI");
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

function get_position_style(ctx, widget_width, y, node_height) {
    const MARGIN = 4; // the margin around the html element

    /* Create a transform that deals with all the scrolling and zooming */
    const elRect = ctx.canvas.getBoundingClientRect();
    const transform = new DOMMatrix()
        .scaleSelf(
            elRect.width / ctx.canvas.width,
            elRect.height / ctx.canvas.height
        )
        .multiplySelf(ctx.getTransform())
        .translateSelf(MARGIN, MARGIN + y);

    return {
        transformOrigin: '0 0',
        transform: transform,
        left: `0`,
        top: `0`,
        cursor: 'pointer',
        position: 'absolute',
        maxWidth: `${widget_width - MARGIN * 2}px`,
        width: `${widget_width - MARGIN * 2}px`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-around'
    };
}

app.registerExtension({
    name: 'vrch.AudioRecorderNode',
    async getCustomWidgets(app) {
        return {
            AUDIOINPUTMIX(node, inputName, inputData, app) {
                const widget = {
                    type: inputData[0],
                    name: inputName,
                    size: [128, 32],
                    draw(ctx, node, width, y) {},
                    computeSize(...args) {
                        return [128, 32]; // Default widget size
                    },
                };
                node.addCustomWidget(widget);
                return widget;
            },
        };
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === 'VrchAudioRecorderNode') {
            nodeData.input.required.audioUI = ["AUDIO_UI"];

            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const currentNode = this;

                let mediaRecorder;
                let audioChunks = [];
                let isRecording = false;
                let recordingTimer;
                let loopIntervalTimer;
                let shortcutKeyPressed = false; // Flag to handle shortcut key status

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.hidden = true;
                }

                // Create a container div for the button and countdown
                const widget = {
                    type: 'div',
                    name: 'audioRecorderDiv',
                    draw(ctx, node, widget_width, y, widget_height) {
                        Object.assign(
                            this.div.style,
                            get_position_style(ctx, widget_width, 250, node.size[1])
                        );
                    }
                };

                widget.div = document.createElement('div');

                const startBtn = document.createElement('button');
                startBtn.className = "comfy-btn";
                startBtn.style = `
                    font-size: 18px;
                    padding: 15px 10px;
                    width: 100%;
                `;

                const countdownDisplay = document.createElement('div');
                countdownDisplay.style = `
                    font-size: 14px;
                    margin-top: 5px;
                    text-align: center;
                `;

                widget.div.appendChild(startBtn);
                widget.div.appendChild(countdownDisplay);
                document.body.appendChild(widget.div);
                this.addCustomWidget(widget);

                // Default shortcut settings
                let enableShortcut = false;
                let selectedShortcut = 'F1';

                // Retrieve settings from widgets
                const enableShortcutWidget = currentNode.widgets.find(w => w.name === 'shortcut');
                const shortcutOptionWidget = currentNode.widgets.find(w => w.name === 'shortcut_key');
                const recordModeWidget = currentNode.widgets.find(w => w.name === 'record_mode');

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
                            // Delay stopRecording to ensure startRecording has enough time
                            setTimeout(() => {
                                stopRecording(true); // Manual stop on key release
                                shortcutKeyPressed = false; // Reset flag
                            }, 100); // Adjust the delay if necessary
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

                const startRecording = () => {
                    if (isRecording) {
                        return; // Don't start a new recording if we're not supposed to continue the loop
                    }

                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        console.error('Browser does not support audio recording');
                        return;
                    }

                    if (loopIntervalTimer) {
                        clearInterval(loopIntervalTimer);
                        loopIntervalTimer = null;
                    }

                    audioChunks = [];
                    isRecording = true;

                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then((stream) => {
                            mediaRecorder = new MediaRecorder(stream, {
                                mimeType: 'audio/webm'
                            });
                            mediaRecorder.ondataavailable = (event) => {
                                if (event.data.size > 0) {
                                    audioChunks.push(event.data);
                                }
                            };
                            mediaRecorder.onstop = () => {
                                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
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
                                if (remainingTime <= startCountdown) {
                                    countdownDisplay.textContent = `Recording will stop in ${remainingTime} seconds`;
                                } else {
                                    countdownDisplay.textContent = 'Recording...';
                                }
                                
                                if (remainingTime <= 0) {
                                    clearInterval(recordingTimer);
                                    remainingTime = 0;
                                    if (isRecording) {
                                        stopRecording(false); //auto stop
                                    }
                                }
                                remainingTime--;
                            };

                            // execute immediately
                            updateCountdown();
                            // start timer
                            recordingTimer = setInterval(updateCountdown, 1000);
                        })
                        .catch(error => console.error('Error accessing audio devices.', error));
                };

                const stopRecording = (isManualStop = false) => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        mediaRecorder = null;
                        isRecording = false;

                        if (recordingTimer) {
                            clearInterval(recordingTimer);
                            recordingTimer = null;
                        }

                        countdownDisplay.textContent = ''; // Clear countdown display

                        const loopWidget = currentNode.widgets.find(w => w.name === 'loop');

                        if (isManualStop) {
                            // If it's a manual stop, always stop the loop and update the button
                            if (loopWidget) {
                                loopWidget.value = false;
                                if (loopWidget.callback) {
                                    loopWidget.callback(loopWidget.value);
                                }
                            }

                            if (loopIntervalTimer) {
                                clearInterval(loopIntervalTimer);
                                loopIntervalTimer = null;
                            }

                            console.log('Recording stopped manually');

                        } else if (loopWidget.value === true && recordModeWidget.value === 'start_and_stop') {
                            // If it's an automatic stop and loop is enabled, restart recording after the interval
                            const loopIntervalWidget = currentNode.widgets.find(w => w.name === 'loop_interval');
                            const loopInterval = (loopIntervalWidget && loopIntervalWidget.value) ? loopIntervalWidget.value : 0.5;
                            loopIntervalTimer = setTimeout(() => {
                                startRecording();
                            }, loopInterval * 1000);

                            console.log('Recording is restarted in a loop');
                        }

                        switchButtonMode(recordModeWidget.value);
                    }
                };

                document.body.appendChild(widget.div);

                this.addCustomWidget(widget);

                // Initialize button mode based on the record mode
                // Load settings from localStorage if available
                const savedRecordMode = localStorage.getItem('vrch_audio_recorder_record_mode');
                if (savedRecordMode) {
                    recordModeWidget.value = savedRecordMode;
                }
                switchButtonMode(recordModeWidget.value);

                const onRemoved = this.onRemoved;
                this.onRemoved = function () {
                    // Clean up when node is removed
                    widget.div.remove();
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

