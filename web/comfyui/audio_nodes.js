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
                        return [128, 32];  // Default widget size
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

                const currentNode = this;  // Ensure 'this' is referenced correctly as 'currentNode'

                // Define mediaRecorder at the node level scope
                let mediaRecorder;
                let audioChunks = [];

                // Hide the base64_data widget
                const base64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                if (base64Widget) {
                    base64Widget.hidden = true;
                }

                // Create a container div for the button
                const widget = {
                    type: 'div',
                    name: 'audioRecorderDiv',
                    draw(ctx, node, widget_width, y, widget_height) {
                        Object.assign(
                            this.div.style,
                            get_position_style(ctx, widget_width, 150, node.size[1])
                        );
                    }
                };

                widget.div = document.createElement('div');

                const startBtn = document.createElement('button');
                startBtn.innerText = 'Press and Hold to Record';

                // Button styling
                startBtn.className = "comfy-btn";
                startBtn.style = `
                    font-size: 18px;
                    padding: 15px 10px;
                `;

                widget.div.appendChild(startBtn);

                document.body.appendChild(widget.div);  // Append to document body

                const startRecording = () => {
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                        console.error('Browser does not support audio recording');
                        return;
                    }

                    audioChunks = []; // Reset chunks

                    const onMediaDataAvailable = (event) => {
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                        }
                    };

                    const onStopRecording = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const reader = new FileReader();

                        reader.onloadend = () => {
                            const base64data = reader.result.split(',')[1];

                            // Update the input field with the recorded base64 data
                            const audioBase64Widget = currentNode.widgets.find(w => w.name === 'base64_data');
                            if (audioBase64Widget) {
                                audioBase64Widget.value = base64data;
                            }

                            // Update the audioUI widget to play the recorded base64 audio
                            const audioUIWidget = currentNode.widgets.find(w => w.name === "audioUI");
                            if (audioUIWidget) {
                                audioUIWidget.element.src = `data:audio/webm;base64,${base64data}`;
                                audioUIWidget.element.classList.remove("empty-audio-widget");
                            }

                            console.log('Audio recording saved.');
                        };
                        reader.readAsDataURL(audioBlob);

                        startBtn.innerText = 'Press and Hold to Record';
                    };

                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then((stream) => {
                            mediaRecorder = new MediaRecorder(stream, {
                                mimeType: 'audio/webm'
                            });
                            mediaRecorder.ondataavailable = onMediaDataAvailable;
                            mediaRecorder.onstop = onStopRecording;
                            mediaRecorder.start();
                            startBtn.innerText = 'Recording...';

                            console.log('Recording started...');
                        })
                        .catch(error => console.error('Error accessing audio devices.', error));
                };

                const stopRecording = () => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        mediaRecorder = null;
                    }
                };

                startBtn.addEventListener('mousedown', () => {
                    startRecording();
                });

                startBtn.addEventListener('mouseup', () => {
                    stopRecording();
                });

                startBtn.addEventListener('mouseleave', () => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        stopRecording();
                    }
                });

                this.addCustomWidget(widget);

                const onRemoved = this.onRemoved;
                this.onRemoved = function () {
                    widget.div.remove();  // Clean up when node is removed
                    return onRemoved?.();
                };

                this.serialize_widgets = true;  // Ensure widget state is saved
            };
        }
    }
});
