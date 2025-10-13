import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

import { 
    hideWidget, 
    showWidget,
    createMicrophoneControls
} from "./node_utils.js";

app.registerExtension({
    name: "vrch.MicLoader",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchMicLoaderNode") {
            // Get required widgets
            const deviceIdWidget = node.widgets.find(w => w.name === "device_id");
            const nameWidget = node.widgets.find(w => w.name === "name");
            const sensitivityWidget = node.widgets.find(w => w.name === "sensitivity");
            const frameSizeWidget = node.widgets.find(w => w.name === "frame_size");
            const sampleRateWidget = node.widgets.find(w => w.name === "sample_rate");
            const enablePreviewWidget = node.widgets.find(w => w.name === "enable_preview");
            const rawDataWidget = node.widgets.find(w => w.name === "raw_data");
            const debugWidget = node.widgets.find(w => w.name === "debug");
            
            // State variables
            let audioContext = null;
            let analyser = null;
            let microphone = null;
            let gainNode = null;
            let animationFrameId = null;
            let isCapturing = false;
            let isMuted = false;
            let suppressMuteCallback = false;
            
            // Hide technical widgets from the UI
            if (rawDataWidget) {
                hideWidget(node, rawDataWidget);
            }
            
            // Function to update widget visibility
            const updateWidgetVisibility = () => {
                if (debugWidget && rawDataWidget) {
                    if (debugWidget.value) {
                        showWidget(node, rawDataWidget);
                    } else {
                        hideWidget(node, rawDataWidget);
                    }
                }
            };
            
            if (debugWidget) {
                debugWidget.callback = (value) => {
                    updateWidgetVisibility();
                };
            }
            
            if (enablePreviewWidget) {
                enablePreviewWidget.callback = (value) => {
                    updateVisualizerVisibility();
                };
            }
            
            // Create visualizer elements
            const visualizerContainer = document.createElement("div");
            visualizerContainer.classList.add("mic-visualizer-container");
            
            // Create waveform canvas
            const waveformCanvas = document.createElement("canvas");
            waveformCanvas.width = 300;
            waveformCanvas.height = 100;
            waveformCanvas.classList.add("mic-canvas");
            
            // Create spectrum canvas
            const spectrumCanvas = document.createElement("canvas");
            spectrumCanvas.width = 300;
            spectrumCanvas.height = 100;
            spectrumCanvas.classList.add("mic-canvas");
            
            // Create volume meter container
            const volumeMeterContainer = document.createElement("div");
            volumeMeterContainer.classList.add("mic-volume-meter-container");
            
            const volumeMeterFill = document.createElement("div");
            volumeMeterFill.classList.add("mic-volume-meter-fill");
            
            volumeMeterContainer.appendChild(volumeMeterFill);
            
            let micControls;
            let statusIndicator = null;

            const updateStatusIndicator = (status) => {
                if (micControls) {
                    micControls.setStatus(status);
                }
            };

            const updateMuteState = (mute, { syncControl = false } = {}) => {
                isMuted = mute;

                if (gainNode) {
                    gainNode.gain.value = mute ? 0 : 1;
                }

                if (mute) {
                    volumeMeterFill.style.width = "0%";
                }

                if (syncControl && micControls) {
                    suppressMuteCallback = true;
                    micControls.setMuted(mute);
                    suppressMuteCallback = false;
                }

                if (statusIndicator) {
                    const text = statusIndicator.textContent;
                    if (text === "Status: Ready" || text === "Status: Muted") {
                        updateStatusIndicator(mute ? "Muted" : "Ready");
                    }
                }
            };

            const handleDeviceSelection = (deviceId) => {
                if (deviceIdWidget) {
                    deviceIdWidget.value = deviceId || "";
                }

                if (nameWidget) {
                    const selectedDevice = micControls ? micControls.devices().find(d => d.deviceId === deviceId) : null;
                    if (selectedDevice && selectedDevice.label) {
                        nameWidget.value = selectedDevice.label;
                    } else if (!deviceId) {
                        nameWidget.value = "";
                    }
                }

                if (deviceId) {
                    updateStatusIndicator(isMuted ? "Muted" : "Ready");
                } else {
                    updateStatusIndicator("Ready");
                }
            };

            micControls = createMicrophoneControls({
                onDeviceChange: handleDeviceSelection,
                onMuteChange: (muted) => {
                    if (suppressMuteCallback) {
                        return;
                    }
                    updateMuteState(muted);
                }
            });

            const deviceSelect = micControls.selectEl;
            const reloadButton = micControls.reloadButton;
            const muteButton = micControls.muteButton;
            statusIndicator = micControls.statusLabel;
            handleDeviceSelection(micControls.getSelection());
            
            visualizerContainer.appendChild(waveformCanvas);
            visualizerContainer.appendChild(spectrumCanvas);
            visualizerContainer.appendChild(volumeMeterContainer);
            visualizerContainer.appendChild(micControls.container);
            
            // Function to update visualizer visibility (only visual elements)
            const updateVisualizerVisibility = () => {
                if (enablePreviewWidget) {
                    // Only hide/show the canvas elements and volume meter, keep controls visible
                    const displayValue = enablePreviewWidget.value ? "block" : "none";
                    waveformCanvas.style.display = displayValue;
                    spectrumCanvas.style.display = displayValue;
                    volumeMeterContainer.style.display = displayValue;
                }
            };
            
            // Add the visualizer container as a DOM widget
            const widget = node.addDOMWidget("mic_visualizer_widget", "Microphone", visualizerContainer);
            // Override the computeSize method to dynamically adjust height based on enable_preview
            widget.computeSize = function(width) {
                const baseHeight = 100;
                const visualizerHeight = 280;
                
                // Check if preview is enabled
                const isPreviewEnabled = enablePreviewWidget ? enablePreviewWidget.value : true;
                const totalHeight = baseHeight + (isPreviewEnabled ? visualizerHeight : 0);
                
                return [width, totalHeight];
            };

            // Function to enumerate and list available audio devices
            const listAudioDevices = async ({ requestAccess = false } = {}) => {
                updateStatusIndicator("Loading");
                try {
                    const deviceList = await micControls.refreshDevices({
                        requestAccess,
                        logPrefix: "[VrchMicLoaderNode]"
                    });

                    const savedDeviceId = deviceIdWidget ? deviceIdWidget.value : "";
                    if (savedDeviceId && !micControls.getSelection()) {
                        micControls.setSelection(savedDeviceId);
                    }

                    handleDeviceSelection(micControls.getSelection());
                    updateMuteState(isMuted, { syncControl: true });

                    return true; // Indicate successful completion
                } catch (error) {
                    console.error("[VrchMicLoaderNode] Error listing audio devices:", error);
                    updateStatusIndicator("Error");
                    return false; // Indicate error
                }
            };
            
            // Function to request microphone access and start capturing
            const startCapturing = async () => {
                try {
                    // Stop any existing capture
                    stopCapturing();
                    
                    const selectedDeviceId = micControls.getSelection();
                    if (!selectedDeviceId) {
                        updateStatusIndicator("No device");
                        return;
                    }
                    
                    // Create audio context
                    audioContext = new (window.AudioContext || window.webkitAudioContext)({
                        sampleRate: parseInt(sampleRateWidget.value, 10)
                    });
                    
                    // Request microphone access
                    const constraints = {
                        audio: {
                            deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: false
                        }
                    };
                    
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    
                    // Set up audio processing pipeline
                    microphone = audioContext.createMediaStreamSource(stream);
                    analyser = audioContext.createAnalyser();
                    gainNode = audioContext.createGain();
                    
                    // Configure analyser
                    analyser.fftSize = parseInt(frameSizeWidget.value, 10) * 2; // FFT size must be 2x frame size
                    analyser.smoothingTimeConstant = 0.8;
                    
                    // Connect nodes: microphone -> gain -> analyser
                    microphone.connect(gainNode);
                    gainNode.connect(analyser);
                    
                    // Update mute state
                    updateMuteState(isMuted, { syncControl: true });
                    
                    // Get the selected device info
                    const selectedDevice = micControls.devices().find(d => d.deviceId === selectedDeviceId);
                    
                    // Update widgets with device info
                    deviceIdWidget.value = selectedDeviceId;
                    if (selectedDevice && selectedDevice.label) {
                        nameWidget.value = selectedDevice.label;
                    }
                    
                    // Start visualization and data collection
                    isCapturing = true;
                    updateStatusIndicator(isMuted ? "Muted" : "Ready");
                    startVisualization();
                    
                } catch (error) {
                    console.error("Error accessing microphone:", error);
                    updateStatusIndicator("Error");
                }
            };
            
            // Function to stop capturing
            const stopCapturing = () => {
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                    animationFrameId = null;
                }
                
                if (microphone && microphone.mediaStream) {
                    // Get all tracks from the stream
                    const tracks = microphone.mediaStream.getTracks();
                    tracks.forEach(track => track.stop());
                    microphone = null;
                }
                
                if (gainNode) {
                    gainNode.disconnect();
                    gainNode = null;
                }
                
                if (analyser) {
                    analyser.disconnect();
                    analyser = null;
                }
                
                if (audioContext) {
                    audioContext.close();
                    audioContext = null;
                }
                
                isCapturing = false;
                updateStatusIndicator("Disconnected");
                
                // Clear visualizations
                clearCanvas(waveformCanvas);
                clearCanvas(spectrumCanvas);
                volumeMeterFill.style.width = "0%";
            };
            
            // Function to start the visualization loop
            const startVisualization = () => {
                if (!analyser) return;
                
                const waveformCtx = waveformCanvas.getContext("2d");
                const spectrumCtx = spectrumCanvas.getContext("2d");
                
                const frameSize = parseInt(frameSizeWidget.value, 10);
                const timeData = new Uint8Array(analyser.fftSize);
                const frequencyData = new Uint8Array(analyser.frequencyBinCount);
                
                const updateVisualization = () => {
                    if (!analyser || !isCapturing) return;
                    
                    // Get time domain data (waveform)
                    analyser.getByteTimeDomainData(timeData);
                    
                    // Get frequency domain data (spectrum)
                    analyser.getByteFrequencyData(frequencyData);
                    
                    // Calculate RMS (volume)
                    let rms = 0;
                    for (let i = 0; i < timeData.length; i++) {
                        const amplitude = (timeData[i] - 128) / 128;
                        rms += amplitude * amplitude;
                    }
                    rms = Math.sqrt(rms / timeData.length);
                    
                    // Calculate zero-crossing rate (ZCR)
                    let zcr = 0;
                    for (let i = 1; i < timeData.length; i++) {
                        if ((timeData[i - 1] < 128 && timeData[i] >= 128) || 
                            (timeData[i - 1] >= 128 && timeData[i] < 128)) {
                            zcr++;
                        }
                    }
                    zcr = zcr / (timeData.length - 1);
                    
                    // Find peak amplitude
                    let peak = 0;
                    for (let i = 0; i < timeData.length; i++) {
                        const amplitude = Math.abs((timeData[i] - 128) / 128);
                        if (amplitude > peak) peak = amplitude;
                    }
                    
                    // Apply sensitivity
                    const sensitivity = sensitivityWidget ? sensitivityWidget.value : 0.5;
                    const adjustedRms = Math.min(1.0, rms * (1.0 / sensitivity));
                    
                    // Determine if microphone is active
                    const threshold = 0.05 * (1.0 - sensitivity); // Lower sensitivity = higher threshold
                    const isActive = adjustedRms > threshold;
                    
                    // Create normalized waveform and spectrum arrays
                    const waveformArray = Array(128).fill(0);
                    const spectrumArray = Array(128).fill(0);
                    
                    // Create normalized waveform array (128 values)
                    const waveStep = Math.max(1, Math.floor(timeData.length / 128));
                    for (let i = 0; i < 128; i++) {
                        const dataIdx = Math.min(i * waveStep, timeData.length - 1);
                        waveformArray[i] = (timeData[dataIdx] - 128) / 128.0; // -1.0 to 1.0
                    }
                    
                    // Create normalized spectrum array (128 values)
                    const specStep = Math.max(1, Math.floor(frequencyData.length / 128));
                    for (let i = 0; i < 128; i++) {
                        const dataIdx = Math.min(i * specStep, frequencyData.length - 1);
                        spectrumArray[i] = frequencyData[dataIdx] / 255.0; // 0.0 to 1.0
                    }
                    
                    // Draw waveform
                    drawWaveform(waveformCtx, timeData);
                    
                    // Draw spectrum
                    drawSpectrum(spectrumCtx, frequencyData);
                    
                    // Update volume meter
                    volumeMeterFill.style.width = `${adjustedRms * 100}%`;
                    
                    // Update volume meter color based on level
                    if (adjustedRms < 0.3) {
                        volumeMeterFill.style.backgroundColor = "#4CAF50"; // Green
                    } else if (adjustedRms < 0.7) {
                        volumeMeterFill.style.backgroundColor = "#FFC107"; // Yellow
                    } else {
                        volumeMeterFill.style.backgroundColor = "#F44336"; // Red
                    }
                    
                    // Prepare and send data to Python backend
                    if (rawDataWidget) {
                        const micData = {
                            device_id: deviceIdWidget.value,
                            name: nameWidget.value,
                            sr: parseInt(sampleRateWidget.value, 10),
                            ch: 1,  // Mono for simplicity
                            hop: parseInt(frameSizeWidget.value, 10),
                            waveform: waveformArray,
                            spectrum: spectrumArray,
                            volume: adjustedRms,
                            is_active: isActive,
                            rms: rms,
                            zcr: zcr,
                            peak: peak
                        };
                        
                        rawDataWidget.value = JSON.stringify(micData);
                    }
                    
                    // Continue animation loop
                    animationFrameId = requestAnimationFrame(updateVisualization);
                };
                
                // Start the animation loop
                updateVisualization();
            };
            
            // Function to draw waveform on canvas
            const drawWaveform = (ctx, data) => {
                const width = ctx.canvas.width;
                const height = ctx.canvas.height;
                
                // Clear canvas
                ctx.clearRect(0, 0, width, height);
                
                // Draw background
                ctx.fillStyle = "#111";
                ctx.fillRect(0, 0, width, height);
                
                // Draw center line
                ctx.beginPath();
                ctx.strokeStyle = "#333";
                ctx.moveTo(0, height / 2);
                ctx.lineTo(width, height / 2);
                ctx.stroke();
                
                // Draw waveform - changed from green to grayscale
                ctx.beginPath();
                ctx.strokeStyle = "#CCCCCC"; // Light gray instead of green
                ctx.lineWidth = 2;
                
                const sliceWidth = width / data.length;
                let x = 0;
                
                for (let i = 0; i < data.length; i++) {
                    const v = data[i] / 255;
                    const y = v * height;
                    
                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                    
                    x += sliceWidth;
                }
                
                ctx.stroke();
            };
            
            // Function to draw frequency spectrum on canvas
            const drawSpectrum = (ctx, data) => {
                const width = ctx.canvas.width;
                const height = ctx.canvas.height;
                
                // Clear canvas
                ctx.clearRect(0, 0, width, height);
                
                // Draw background
                ctx.fillStyle = "#111";
                ctx.fillRect(0, 0, width, height);
                
                // Calculate bar width
                const barCount = Math.min(128, data.length);
                const barWidth = width / barCount;
                
                // Draw frequency bars
                for (let i = 0; i < barCount; i++) {
                    // Get a subset of the data to avoid too many bars
                    const dataIndex = Math.floor(i * data.length / barCount);
                    const value = data[dataIndex];
                    
                    const percent = value / 255;
                    // Calculate bar height based on full height
                    const barHeight = percent * height;
                    const x = i * barWidth;
                    const y = height - barHeight;
                    
                    // Restore colorful spectrum
                    const hue = i / barCount * 120; // 0-120 gives a range from red to green
                    ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
                    ctx.fillRect(x, y, barWidth, barHeight); // Removed -1 to eliminate gaps
                }
            };
            
            // Function to clear canvas
            const clearCanvas = (canvas) => {
                const ctx = canvas.getContext("2d");
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#111";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            };
            
            // Set up event listeners
            deviceSelect.addEventListener("change", () => {
                if (micControls.getSelection()) {
                    startCapturing();
                } else {
                    stopCapturing();
                }
            });
            
            reloadButton.addEventListener("click", async () => {
                // First stop any existing capture
                stopCapturing();
                
                // Then reload device list
                const devicesLoaded = await listAudioDevices({ requestAccess: true });
                
                // Automatically restart if a device is selected
                if (devicesLoaded && micControls.getSelection()) {
                    startCapturing();
                }
            });
            
            // Set a delay initialization for the widget visibility
            setTimeout(async () => {
                // Initial setup
                updateWidgetVisibility();
                updateVisualizerVisibility();
                
                // Store the previously selected deviceId for recovery
                const savedDeviceId = deviceIdWidget.value;
                
                // Request microphone permissions and list devices
                await navigator.mediaDevices.getUserMedia({ audio: true }).catch(err => {
                    console.warn("Microphone permission request failed:", err);
                });
                
                // List audio devices with proper permissions
                const devicesLoaded = await listAudioDevices();
                
                // Try to restore the previously selected device
                if (devicesLoaded) {
                    if (savedDeviceId && savedDeviceId !== "") {
                        micControls.setSelection(savedDeviceId);
                        handleDeviceSelection(micControls.getSelection());
                        if (micControls.getSelection()) {
                            console.log("Restored previously selected microphone:", savedDeviceId);
                            setTimeout(() => {
                                startCapturing();
                            }, 100);
                        }
                    } else {
                        updateStatusIndicator("Ready"); // No device selected
                    }
                }
            }, 1000);
            
            // Cleanup when node is removed
            const onRemoved = node.onRemoved;
            node.onRemoved = function() {
                stopCapturing();
                if (onRemoved) {
                    onRemoved.apply(this, arguments);
                }
            };
        }
    }
});

// Add custom styles
const style = document.createElement("style");
style.textContent = `
    .mic-visualizer-container {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 10px;
        min-width: 0;
        box-sizing: border-box;
    }
    
    .mic-canvas {
        width: 100%;
        height: 100px;
        background-color: #111;
        border-radius: 4px;
        flex-shrink: 0;
        min-width: 0;
        box-sizing: border-box;
    }
    
    .mic-volume-meter-container {
        width: 100%;
        height: 20px;
        background-color: #111;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
        flex-shrink: 0;
        min-width: 0;
    }
    
    .mic-volume-meter-fill {
        height: 100%;
        background-color: #4CAF50;
        width: 0%;
        transition: width 0.1s ease;
    }
    
    .mic-controls-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 10px;
    }
    
    .mic-device-row {
        display: flex;
        width: 100%;
    }
    
    .mic-button-row {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 5px;
    }
    
    .mic-device-select {
        width: 100%;
        padding: 5px;
        border-radius: 4px;
    }
    
    .vrch-mic-reload-button {
        background-color: #4CAF50;
        color: white;
        height: 30px;
        font-size: 14px;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        margin: 0 5px;
        cursor: pointer;
        transition: background-color 0.3s;
        min-width: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .vrch-mic-mute-button {
        background-color: #4f9cff;
        color: white;
        height: 30px;
        font-size: 14px;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        margin: 0 5px;
        cursor: pointer;
        transition: background-color 0.3s;
        min-width: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .vrch-mic-reload-button:hover,
    .vrch-mic-mute-button:hover {
        filter: brightness(1.1); 
    }

    .vrch-mic-status-container {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-top: 0px;
    }
    
    .vrch-mic-status-label {
        font-size: 14px;
        color: #999;
        text-align: center;
    }
    
    .vrch-mic-speaker-icon {
        font-size: 16px;
    }
`;
document.head.appendChild(style);
