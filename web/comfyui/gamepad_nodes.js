import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyWidgets } from '../../../scripts/widgets.js';

import { 
    hideWidget, 
    showWidget,
} from "./node_utils.js";

app.registerExtension({
    name: "vrch.GamepadControlLoader",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchGamepadLoaderNode") {
            // Obtain required widgets
            const indexWidget = node.widgets.find(w => w.name === "index");
            const nameWidget = node.widgets.find(w => w.name === "name");
            const rawDataWidget = node.widgets.find(w => w.name === "raw_data");
            const debugWidget = node.widgets.find(w => w.name === "debug");
            // Set up the timer to fetch gamepad data
            let timerId = null;

            // Function to extract gamepad data into a serializable object
            const extractGamepadData = (gamepad) => {
                return {
                    id: gamepad.id,
                    index: gamepad.index,
                    connected: gamepad.connected,
                    timestamp: gamepad.timestamp,
                    mapping: gamepad.mapping,
                    axes: Array.from(gamepad.axes || []),
                    buttons: Array.from(gamepad.buttons || []).map(btn => ({
                        pressed: btn.pressed,
                        touched: btn.touched,
                        value: btn.value
                    }))
                };
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
                // Set the initial visibility of the raw data widget
                hideWidget(node, rawDataWidget);
            }

            // fetch gamepad data from browser gamepad API
            const fetchGamepadData = async () => {
                try {
                    const gamepads = navigator.getGamepads();
                    if (gamepads) {
                        const gamepad = gamepads[indexWidget.value];
                        console.log("Gamepad data:", gamepad);
                        if (gamepad) {
                            nameWidget.value = gamepad.id;
                            
                            // Use the extract function to get serializable gamepad data
                            const gamepadData = extractGamepadData(gamepad);
                            
                            // Update the raw data widget with the extracted gamepad data
                            rawDataWidget.value = JSON.stringify(gamepadData, null, 2);
                        } else {
                            nameWidget.value = "n/a";
                            rawDataWidget.value = "No gamepad found";
                        }
                    } else {
                        nameWidget.value = "n/a";
                        rawDataWidget.value = "No gamepad data available";
                    }
                    // Update the debug widget with the gamepad data
                } catch (error) {
                    console.error("Error fetching gamepad data:", error);
                }
            };

            // Set up the timer to fetch gamepad data every 100ms
            timerId = setInterval(() => {
                fetchGamepadData();
            }, 100);

            // Set a delay initialization for the URL and widget visibility
            setTimeout(() => {
                updateWidgetVisibility();
            }, 1000);

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
