import { app } from "../../scripts/app.js";  
import { api } from "../../scripts/api.js";  
import { ComfyWidgets } from '../../../scripts/widgets.js';  
  
import {   
    hideWidget,   
    showWidget,  
} from "./node_utils.js";  
  
app.registerExtension({  
    name: "vrch.MidiDeviceLoader",  
    async nodeCreated(node) {  
        if (node.comfyClass === "VrchMidiDeviceLoaderNode") {  
            // Get required widgets  
            const deviceIdWidget = node.widgets.find(w => w.name === "device_id");  
            const nameWidget = node.widgets.find(w => w.name === "name");  
            const rawDataWidget = node.widgets.find(w => w.name === "raw_data");  
            const debugWidget = node.widgets.find(w => w.name === "debug");  
             
            // MIDI access object  
            let midiAccess = null;  
            // Current MIDI input device  
            let currentInput = null;  
            // Store current MIDI state  
            let midiState = {  
                cc: [],      // CC controller state - will be used for both INT and FLOAT CC values 
                notes: []    // Note state - will be used for both BOOLEAN note values and INT note values
            };

            // Function to update widget visibility  
            const updateWidgetVisibility = () => {  
                if (debugWidget) {  
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
  
            if (rawDataWidget) {  
                // Set initial visibility of raw data widget  
                hideWidget(node, rawDataWidget);  
            }  
  
            // Function to handle MIDI messages  
            const onMIDIMessage = (event) => {  
                try {  
                    // MIDI message contains three bytes: [status byte, data byte 1, data byte 2]  
                    const [statusByte, dataByte1, dataByte2] = event.data;  
                      
                    // Extract channel info and message type  
                    const messageType = statusByte >> 4;  
                    const channel = statusByte & 0xF;  
                      
                    if (debugWidget && debugWidget.value) {  
                        console.log(`[MIDI] Message: type=${messageType}, channel=${channel}, data1=${dataByte1}, data2=${dataByte2}`);  
                    }  
                      
                    switch (messageType) {  
                        case 0x8: // Note Off  
                            updateNoteStatus(dataByte1, 0, "noteOff");  
                            break;  
                              
                        case 0x9: // Note On  
                            updateNoteStatus(dataByte1, dataByte2, dataByte2 > 0 ? "noteOn" : "noteOff");  
                            break;  
                              
                        case 0xB: // Control Change  
                            updateCCValue(dataByte1, dataByte2);  
                            break;
                            
                        case 0xA: // Polyphonic Key Pressure (Aftertouch)
                            // Handle per-note aftertouch
                            updateAftertouch(dataByte1, dataByte2);
                            break;
                            
                        case 0xC: // Program Change
                            // Handle program change
                            updateProgramChange(dataByte1);
                            break;
                            
                        case 0xD: // Channel Pressure (Aftertouch)
                            // Handle channel-wide aftertouch
                            updateChannelPressure(dataByte1);
                            break;
                            
                        case 0xE: // Pitch Bend
                            // Handle pitch bend
                            updatePitchBend(dataByte1, dataByte2);
                            break;
                              
                        // Add more MIDI message type handlers as needed  
                    }  

                    // Update raw data widget  
                    const json_data = JSON.stringify(midiState, null, 2);
                    if (json_data && rawDataWidget && rawDataWidget.value != json_data) {
                        // Only update if the data has changed
                        rawDataWidget.value = json_data;
                    }

                } catch (error) {  
                    console.error("[VrchMidiDeviceLoaderNode] Error processing MIDI message:", error);  
                }  
            };  
              
            // Update note status  
            const updateNoteStatus = (noteNumber, velocity, status) => {  
                // Find existing note record  
                const existingNoteIndex = midiState.notes.findIndex(note => note.number === noteNumber);  
                  
                if (status === "noteOff" && velocity === 0) {  
                    // If note off and velocity is 0, remove from array  
                    if (existingNoteIndex !== -1) {  
                        midiState.notes.splice(existingNoteIndex, 1);  
                    }  
                } else {  
                    // Update or add note info  
                    const noteInfo = {  
                        number: noteNumber,  
                        velocity: velocity,  
                        status: status  
                    };  
                      
                    if (existingNoteIndex !== -1) {  
                        midiState.notes[existingNoteIndex] = noteInfo;  
                    } else {  
                        midiState.notes.push(noteInfo);  
                    }  
                }  
            };  
              
            // Update CC controller value  
            const updateCCValue = (ccNumber, value) => {  
                // Find existing CC record  
                const existingCCIndex = midiState.cc.findIndex(cc => cc.number === ccNumber);  
                  
                const ccInfo = {  
                    number: ccNumber,  
                    value: value  
                };  
                  
                if (existingCCIndex !== -1) {  
                    midiState.cc[existingCCIndex] = ccInfo;  
                } else {  
                    midiState.cc.push(ccInfo);  
                }  
            };
            
            // Handle polyphonic aftertouch
            const updateAftertouch = (noteNumber, pressure) => {
                // Store or process aftertouch data in the appropriate format
                // Similar to notes but with pressure instead of velocity
                const existingIndex = midiState.aftertouch?.findIndex(at => at.note === noteNumber) ?? -1;
                
                if (!midiState.aftertouch) midiState.aftertouch = [];
                
                const afterTouchInfo = {
                    note: noteNumber,
                    pressure: pressure
                };
                
                if (existingIndex !== -1) {
                    midiState.aftertouch[existingIndex] = afterTouchInfo;
                } else {
                    midiState.aftertouch.push(afterTouchInfo);
                }
            };
            
            // Handle program change
            const updateProgramChange = (programNumber) => {
                midiState.programChange = programNumber;
            };
            
            // Handle channel pressure (global aftertouch)
            const updateChannelPressure = (pressure) => {
                midiState.channelPressure = pressure;
            };
            
            // Handle pitch bend (combines two bytes for 14-bit resolution)
            const updatePitchBend = (lsb, msb) => {
                // Combine bytes to get the full pitch bend value (0-16383, centered at 8192)
                const value = (msb << 7) + lsb;
                midiState.pitchBend = value;
            };
  
            // Initialize MIDI access  
            const initMIDI = async () => {  
                try {  
                    if (navigator.requestMIDIAccess) {  
                        midiAccess = await navigator.requestMIDIAccess();  
                          
                        // List available MIDI devices  
                        const inputs = [...midiAccess.inputs.values()];  
                          
                        if (debugWidget && debugWidget.value) {  
                            console.log("[VrchMidiDeviceLoaderNode] Available MIDI devices:", inputs);  
                        }  
                          
                        // If device ID exists, try to connect to specific device  
                        if (deviceIdWidget.value) {  
                            connectToDevice(deviceIdWidget.value);  
                        } else if (inputs.length > 0) {  
                            // Otherwise connect to first available device  
                            connectToDevice(inputs[0].id);  
                            deviceIdWidget.value = inputs[0].id;  
                        }  
                          
                        // Set up MIDI connection state change listener  
                        midiAccess.onstatechange = (event) => {  
                            if (debugWidget && debugWidget.value) {  
                                console.log("[VrchMidiDeviceLoaderNode] MIDI connection state change:", event);  
                            }  
                              
                            // If device reconnects, try to reconnect  
                            if (event.port.type === "input" && event.port.state === "connected") {  
                                if (deviceIdWidget.value === event.port.id || !currentInput) {  
                                    connectToDevice(event.port.id);  
                                }  
                            }  
                        };  
                    } else {  
                        console.warn("[VrchMidiDeviceLoaderNode] Web MIDI API not supported in this browser");  
                    }  
                } catch (error) {  
                    console.error("[VrchMidiDeviceLoaderNode] Error initializing MIDI:", error);  
                }  
            };  
              
            // Connect to specific MIDI device  
            const connectToDevice = (deviceId) => {  
                try {  
                    // Disconnect current connection  
                    if (currentInput) {  
                        currentInput.onmidimessage = null;  
                    }  
                      
                    // Find and connect to new device  
                    const device = midiAccess.inputs.get(deviceId);  
                      
                    if (device) {  
                        device.onmidimessage = onMIDIMessage;  
                        currentInput = device;  
                        nameWidget.value = device.name || deviceId;  
                        deviceIdWidget.value = deviceId;  
                          
                        if (debugWidget && debugWidget.value) {  
                            console.log(`[VrchMidiDeviceLoaderNode] Connected to MIDI device: ${device.name || deviceId}`);  
                        }  
                    } else {  
                        if (debugWidget && debugWidget.value) {  
                            console.warn(`[VrchMidiDeviceLoaderNode] MIDI device not found: ${deviceId}`);  
                        }  
                        nameWidget.value = "Device not found";  
                        currentInput = null;  
                    }  
                } catch (error) {  
                    console.error("[VrchMidiDeviceLoaderNode] Error connecting to MIDI device:", error);  
                }  
            };  
              
            // Device ID widget callback  
            if (deviceIdWidget) {  
                deviceIdWidget.callback = () => {  
                    if (midiAccess && deviceIdWidget.value) {  
                        connectToDevice(deviceIdWidget.value);  
                    }  
                };  
            }  
              
            // Initialize MIDI  
            initMIDI();  
              
            // Set delayed initialization for widget visibility  
            setTimeout(() => {  
                updateWidgetVisibility();  
            }, 1000);  
              
            // Cleanup function, called when node is removed  
            const onRemoved = this.onRemoved;  
            this.onRemoved = function () {  
                if (currentInput) {  
                    currentInput.onmidimessage = null;  
                    currentInput = null;  
                }  
                return onRemoved?.();  
            };  
        }  
    }  
});