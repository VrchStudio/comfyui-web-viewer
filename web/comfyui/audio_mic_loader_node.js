import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

import { 
    hideWidget, 
    showWidget 
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
            let devices = [];
            
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
            
            // Create controls container
            const controlsContainer = document.createElement("div");
            controlsContainer.classList.add("mic-controls-container");
            
            // Device dropdown
            const deviceSelect = document.createElement("select");
            deviceSelect.classList.add("mic-device-select");
            
            // Create default option
            const defaultOption = document.createElement("option");
            defaultOption.value = "";
            defaultOption.textContent = "Select Microphone...";
            deviceSelect.appendChild(defaultOption);
            
            // Reload button
            const reloadButton = document.createElement("button");
            reloadButton.textContent = "Reload";
            reloadButton.classList.add("vrch-mic-reload-button");
            
            // Mute button with speaker icon instead of text
            const muteButton = document.createElement("button");
            muteButton.innerHTML = '<span class="vrch-mic-speaker-icon">🔊</span>';
            muteButton.classList.add("vrch-mic-mute-button");
            
            // Status indicator - now text-based on its own line
            const statusIndicator = document.createElement("div");
            statusIndicator.classList.add("vrch-mic-status-label");
            
            // Add elements to their containers
            controlsContainer.appendChild(deviceSelect);
            controlsContainer.appendChild(reloadButton);
            controlsContainer.appendChild(muteButton);
            
            // Create a separate container for the status label to put it on its own line
            const statusContainer = document.createElement("div");
            statusContainer.classList.add("vrch-mic-status-container");
            statusContainer.appendChild(statusIndicator);
            
            visualizerContainer.appendChild(waveformCanvas);
            visualizerContainer.appendChild(spectrumCanvas);
            visualizerContainer.appendChild(volumeMeterContainer);
            visualizerContainer.appendChild(controlsContainer);
            visualizerContainer.appendChild(statusContainer);
            
            // Add the visualizer container as a DOM widget
            node.addDOMWidget("mic_visualizer_widget", "Microphone", visualizerContainer);
            
            // Function to enumerate and list available audio devices
            const listAudioDevices = async () => {
                try {
                    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                        throw new Error("MediaDevices API not supported in this browser");
                    }
                    
                    // Request permission first to get proper device labels
                    try {
                        await navigator.mediaDevices.getUserMedia({ audio: true });
                    } catch (permissionError) {
                        console.warn("Could not get microphone permission:", permissionError);
                    }
                    
                    // Clear existing options except default
                    while (deviceSelect.options.length > 1) {
                        deviceSelect.remove(1);
                    }
                    
                    // Get devices
                    const mediaDevices = await navigator.mediaDevices.enumerateDevices();
                    devices = mediaDevices.filter(device => device.kind === "audioinput");
                    
                    // Store selected device ID before clearing
                    const previouslySelectedDeviceId = deviceSelect.value || deviceIdWidget.value;
                    let selectedDeviceStillExists = false;
                    
                    // Add devices to dropdown
                    devices.forEach(device => {
                        const option = document.createElement("option");
                        option.value = device.deviceId;
                        option.textContent = device.label || `Microphone (${device.deviceId.slice(0, 5)}...)`;
                        deviceSelect.appendChild(option);
                        
                        // Check if previously selected device still exists
                        if (device.deviceId === previouslySelectedDeviceId) {
                            selectedDeviceStillExists = true;
                        }
                    });
                    
                    // Restore previously selected device if it still exists
                    if (previouslySelectedDeviceId && selectedDeviceStillExists) {
                        deviceSelect.value = previouslySelectedDeviceId;
                        deviceIdWidget.value = previouslySelectedDeviceId;
                    } else if (devices.length > 0 && deviceIdWidget.value) {
                        // Reset if device doesn't exist anymore
                        deviceIdWidget.value = "";
                    }
                    
                    updateStatusIndicator("Ready");
                    return true; // Indicate successful completion
                    
                } catch (error) {
                    console.error("Error listing audio devices:", error);
                    updateStatusIndicator("Error");
                    return false; // Indicate error
                }
            };
            
            // Function to request microphone access and start capturing
            const startCapturing = async () => {
                try {
                    // Stop any existing capture
                    stopCapturing();
                    
                    if (!deviceSelect.value) {
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
                            deviceId: deviceSelect.value ? { exact: deviceSelect.value } : undefined,
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
                    setMuted(isMuted);
                    
                    // Get the selected device info
                    const selectedDevice = devices.find(d => d.deviceId === deviceSelect.value);
                    
                    // Update widgets with device info
                    deviceIdWidget.value = deviceSelect.value;
                    if (selectedDevice && selectedDevice.label) {
                        nameWidget.value = selectedDevice.label;
                    }
                    
                    // Start visualization and data collection
                    isCapturing = true;
                    updateStatusIndicator("Ready");
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
            
            // Function to toggle mute state
            const setMuted = (mute) => {
                isMuted = mute;
                
                if (gainNode) {
                    gainNode.gain.value = mute ? 0 : 1;
                }
                
                // Update icon instead of text
                muteButton.innerHTML = mute ? 
                    '<span class="vrch-mic-speaker-icon">🔇</span>' : 
                    '<span class="vrch-mic-speaker-icon">🔊</span>';
                // muteButton.style.backgroundColor = mute ? "#F44336" : "#4CAF50";
                
                if (mute) {
                    volumeMeterFill.style.width = "0%";
                }
            };
            
            // Function to update status indicator - now text-only
            const updateStatusIndicator = (status) => {
                // Just set the text content - no background color changes
                statusIndicator.textContent = `Status: ${status}`;
            };
            
            // Set up event listeners
            deviceSelect.addEventListener("change", () => {
                if (deviceSelect.value) {
                    startCapturing();
                } else {
                    stopCapturing();
                }
            });
            
            reloadButton.addEventListener("click", async () => {
                // First stop any existing capture
                stopCapturing();
                
                // Then reload device list
                const devicesLoaded = await listAudioDevices();
                
                // Automatically restart if a device is selected
                if (devicesLoaded && deviceSelect.value) {
                    startCapturing();
                }
            });
            
            muteButton.addEventListener("click", () => {
                setMuted(!isMuted);
            });

            // Set a delay initialization for the widget visibility
            setTimeout(async () => {
                // Initial setup
                updateWidgetVisibility();
                
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
                        // Set the dropdown value to match the stored device ID
                        for (let i = 0; i < deviceSelect.options.length; i++) {
                            if (deviceSelect.options[i].value === savedDeviceId) {
                                deviceSelect.selectedIndex = i;
                                console.log("Restored previously selected microphone:", savedDeviceId);
                                
                                // Start capturing with a slight delay to ensure the device is properly selected
                                setTimeout(() => {
                                    startCapturing();
                                }, 100);
                                
                                break;
                            }
                        }
                    } else {
                        updateStatusIndicator("Ready");
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
    }
    
    .mic-canvas {
        width: 100%;
        height: 100px;
        background-color: #111;
        border-radius: 4px;
    }
    
    .mic-volume-meter-container {
        width: 100%;
        height: 20px;
        background-color: #333;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }
    
    .mic-volume-meter-fill {
        height: 100%;
        background-color: #4CAF50;
        width: 0%;
        transition: width 0.1s ease;
    }
    
    .mic-controls-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
    }
    
    .mic-device-select {
        flex: 1;
        margin-right: 10px;
        padding: 5px;
        border-radius: 4px;
    }
    
    .vrch-mic-reload-button,
    .vrch-mic-mute-button {
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

    .vrch-mic-reload-button:hover,
    .vrch-mic-mute-button:hover {
        background-color: #45a049;
    }

    .vrch-mic-status-container {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-top: 10px;
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