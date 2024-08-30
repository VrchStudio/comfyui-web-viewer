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

const startRecording = (startBtn, node) => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Browser does not support audio recording');
        return;
    }

    let mediaRecorder;
    let audioChunks = [];

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
            localStorage.setItem('_vrch_audio_recorder', base64data);

            // Update node with the recorded audio in base64 format
            let data = getLocalData('_vrch_audio_recorder') || {};
            data[node.id] = base64data;
            localStorage.setItem('_vrch_audio_recorder', JSON.stringify(data));

            console.log('Audio recording saved.');
        };
        reader.readAsDataURL(audioBlob);

        startBtn.innerText = 'Start';
        startBtn.className = '';
    };

    const startMediaRecording = (stream) => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = onMediaDataAvailable;
        mediaRecorder.onstop = onStopRecording;

        mediaRecorder.start();
        startBtn.innerText = 'Stop';
        startBtn.className = 'recording';

        console.log('Recording started...');
    };

    startBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder = null;
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(startMediaRecording)
                .catch(error => console.error('Error accessing audio devices.', error));
        }
    });
};

app.registerExtension({
    name: 'vrch.AudioRecorderNode',  // Node name
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
                    async serializeValue(nodeId, widgetIndex) {
                        let data = getLocalData('_vrch_audio_recorder') || {};
                        return data[nodeId] || 'No audio recorded';
                    }
                };
                node.addCustomWidget(widget);
                return widget;
            }
        };
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass === 'VrchAudioRecorderNode') {
            const orig_nodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                orig_nodeCreated?.apply(this, arguments);

                const currentNode = this;  // Ensure 'this' is referenced correctly as 'currentNode'

                const widgetDiv = document.createElement('div');
                widgetDiv.style.display = 'flex';
                widgetDiv.style.flexDirection = 'column';
                widgetDiv.style.margin = '10px';

                const startBtn = document.createElement('button');
                startBtn.innerText = 'Start';

                // Button styling
                startBtn.style = `
                    margin-top: 10px;
                    background-color: var(--comfy-input-bg);
                    border-radius: 4px;
                    border: 1px solid var(--border-color);
                    color: var(--descrip-text);
                    padding: 6px 12px;
                    cursor: pointer;
                `;

                widgetDiv.appendChild(startBtn);

                // Integrate the button div into the node using LiteGraph methods
                const customWidget = currentNode.addWidget('button', 'Record Audio', '', () => {}, {width: 150});
                customWidget.content = widgetDiv;
                
                startRecording(startBtn, currentNode);

                this.onRemoved = function () {
                    widgetDiv.remove();  // Clean up when node is removed
                    orig_nodeCreated?.apply(this, arguments);
                };

                this.serialize_widgets = true;  // Ensure widget state is saved
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                try {
                    let data = getLocalData('_vrch_audio_recorder') || {};
                    if (data[this.id]) {
                        console.log('Recorded audio exists, ready for use.');
                    }
                } catch (error) {
                    console.log('###VrchAudioRecorderNode', error);
                }
            };
        }
    }
});
