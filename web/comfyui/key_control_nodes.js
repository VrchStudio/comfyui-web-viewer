// key_control_nodes.js

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Debug flag to control log outputs
const ENABLE_DEBUG = true;

/**
 * VrchIntKeyControlNode allows users to control an integer output value within
 * a customizable range using keyboard shortcuts. Users can adjust the step size,
 * choose different shortcut key combinations, and define minimum and maximum values.
 */
app.registerExtension({
    name: "vrch.IntKeyControlNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchIntKeyControlNode") {
            // Removed the block that defines required inputs to prevent UI issues
            // nodeData.input.required = nodeData.input.required || {};
            // nodeData.input.required.min_value = ["min_value"];
            // nodeData.input.required.max_value = ["max_value"];
            // nodeData.input.required.step_size = ["step_size"];
            // nodeData.input.required.shortcut_key1 = ["shortcut_key1"];
            // nodeData.input.required.shortcut_key2 = ["shortcut_key2"];
            // nodeData.input.required.current_value = ["current_value"];
        }
    },
    getCustomWidgets() {
        return {};
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchIntKeyControlNode") {
            // Initialize node state from inputs
            let currentValueWidget = node.widgets.find(w => w.name === "current_value");
            let minValueWidget = node.widgets.find(w => w.name === "min_value");
            let maxValueWidget = node.widgets.find(w => w.name === "max_value");

            let currentValue = parseInt(currentValueWidget ? currentValueWidget.value : 50) || 50; // Default value
            let minValue = parseInt(minValueWidget ? minValueWidget.value : 0) || 0;
            let maxValue = parseInt(maxValueWidget ? maxValueWidget.value : 100) || 100;

            // Ensure initial currentValue is within min and max bounds
            currentValue = Math.max(Math.min(currentValue, maxValue), minValue);

            // Create display elements for the current value
            const valueDisplay = document.createElement("div");
            valueDisplay.classList.add("comfy-value-display");
            valueDisplay.textContent = `Value: ${currentValue}`;
            node.addDOMWidget("int_value_display", "int_value_display", valueDisplay);

            if (ENABLE_DEBUG) {
                console.log("[VrchIntKeyControlNode] Initialized with value:", currentValue);
                console.log("[VrchIntKeyControlNode] Min value:", minValue);
                console.log("[VrchIntKeyControlNode] Max value:", maxValue);
            }

            // Function to update the display
            const updateDisplay = () => {
                currentValue = Math.max(Math.min(currentValue, maxValue), minValue);
                valueDisplay.textContent = `Value: ${currentValue}`;
                if (currentValueWidget) {
                    currentValueWidget.value = currentValue;
                }
                if (ENABLE_DEBUG) {
                    console.log(`[VrchIntKeyControlNode] current_value updated to: ${currentValue}`);
                }
            };

            // Set up callbacks for min_value and max_value changes
            if (minValueWidget) {
                minValueWidget.callback = (value) => {
                    minValue = parseInt(value) || 0;
                    if (minValue > maxValue) {
                        minValue = maxValue;
                        if (ENABLE_DEBUG) {
                            console.log(`[VrchIntKeyControlNode] min_value adjusted to not exceed max_value: ${minValue}`);
                        }
                    }
                    // Clamp currentValue within new minValue
                    currentValue = Math.max(currentValue, minValue);
                    updateDisplay();
                };
            }

            if (maxValueWidget) {
                maxValueWidget.callback = (value) => {
                    maxValue = parseInt(value) || 100;
                    if (maxValue < minValue) {
                        maxValue = minValue;
                        if (ENABLE_DEBUG) {
                            console.log(`[VrchIntKeyControlNode] max_value adjusted to not be below min_value: ${maxValue}`);
                        }
                    }
                    // Clamp currentValue within new maxValue
                    currentValue = Math.min(currentValue, maxValue);
                    updateDisplay();
                };
            }

            // Update display when current_value changes
            node.onInputChanged = function(inputName, value) {
                if (inputName === "current_value") {
                    currentValue = parseInt(value) || 50;
                    updateDisplay();
                }
            };

            // Set to keep track of pressed keys
            const pressedKeys = new Set();

            // Handler for keydown events
            const handleKeyDown = (event) => {
                const fxKeys = ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"];
                const directionKeysMap = {
                    "Down/Up": ["ArrowDown", "ArrowUp"],
                    "Left/Right": ["ArrowLeft", "ArrowRight"]
                };

                // Add the key to the pressedKeys Set
                pressedKeys.add(event.key);

                // Get the currently selected shortcut_key1 and shortcut_key2
                const shortcutKey1Widget = node.widgets.find(w => w.name === "shortcut_key1");
                const shortcutKey1 = shortcutKey1Widget ? shortcutKey1Widget.value : "F2"; // Default is now F2

                const shortcutKey2Widget = node.widgets.find(w => w.name === "shortcut_key2");
                const shortcutKey2 = shortcutKey2Widget ? shortcutKey2Widget.value : "Down/Up";

                // Check if shortcut_key1 is pressed and is a valid fxKey
                if (fxKeys.includes(shortcutKey1.toUpperCase())) {
                    const isShortcutKey1Pressed = pressedKeys.has(shortcutKey1.toUpperCase());

                    // Get the list of direction keys based on shortcut_key2
                    const directionKeys = directionKeysMap[shortcutKey2] || ["ArrowDown", "ArrowUp"];

                    // Check if a direction key is pressed
                    for (const dirKey of directionKeys) {
                        if (event.key === dirKey && isShortcutKey1Pressed) {
                            if (dirKey === "ArrowUp" || dirKey === "ArrowRight") {
                                // Increment the value
                                const stepSizeWidget = node.widgets.find(w => w.name === "step_size");
                                const stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1) || 1;
                                const newValue = Math.min(currentValue + stepSize, maxValue);
                                if (newValue !== currentValue) {
                                    currentValue = newValue;
                                    updateDisplay();
                                    if (ENABLE_DEBUG) {
                                        console.log(`[VrchIntKeyControlNode] Value incremented to: ${currentValue}`);
                                    }
                                }
                            } else if (dirKey === "ArrowDown" || dirKey === "ArrowLeft") {
                                // Decrement the value
                                const stepSizeWidget = node.widgets.find(w => w.name === "step_size");
                                const stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1) || 1;
                                const newValue = Math.max(currentValue - stepSize, minValue);
                                if (newValue !== currentValue) {
                                    currentValue = newValue;
                                    updateDisplay();
                                    if (ENABLE_DEBUG) {
                                        console.log(`[VrchIntKeyControlNode] Value decremented to: ${currentValue}`);
                                    }
                                }
                            }

                            // Prevent default behavior (e.g., scrolling)
                            event.preventDefault();
                        }
                    }
                }
            };

            // Handler for keyup events
            const handleKeyUp = (event) => {
                // Remove the key from the pressedKeys Set
                pressedKeys.delete(event.key);
            };

            // Add the keydown and keyup listeners
            window.addEventListener("keydown", handleKeyDown);
            window.addEventListener("keyup", handleKeyUp);
            if (ENABLE_DEBUG) {
                console.log("[VrchIntKeyControlNode] Keydown and Keyup event listeners added.");
            }

            // Cleanup when the node is removed
            node.onRemoved = function () {
                window.removeEventListener("keydown", handleKeyDown);
                window.removeEventListener("keyup", handleKeyUp);
                if (ENABLE_DEBUG) {
                    console.log("[VrchIntKeyControlNode] Keydown and Keyup event listeners removed.");
                }
            };
        }
    }
});

/**
 * VrchFloatKeyControlNode allows users to control a floating-point output value (0.0-1.0)
 * using keyboard shortcuts. Users can adjust the step size and choose different
 * shortcut key combinations.
 */
app.registerExtension({
    name: "vrch.FloatKeyControlNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchFloatKeyControlNode") {
            // Removed the block that defines required inputs to prevent UI issues
            // nodeData.input.required = nodeData.input.required || {};
            // nodeData.input.required.step_size = ["step_size"];
            // nodeData.input.required.shortcut_key1 = ["shortcut_key1"];
            // nodeData.input.required.shortcut_key2 = ["shortcut_key2"];
            // nodeData.input.required.current_value = ["current_value"];
        }
    },
    getCustomWidgets() {
        return {};
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchFloatKeyControlNode") {
            // Initialize node state from inputs
            let currentValueWidget = node.widgets.find(w => w.name === "current_value");
            let currentValue = parseFloat(currentValueWidget ? currentValueWidget.value : 0.50) || 0.50; // Default value

            // Create a display element for the current value
            const valueDisplay = document.createElement("div");
            valueDisplay.classList.add("comfy-value-display");
            valueDisplay.textContent = `Value: ${currentValue.toFixed(2)}`;
            node.addDOMWidget("float_value_display", "float_value_display", valueDisplay);

            if (ENABLE_DEBUG) {
                console.log("[VrchFloatKeyControlNode] Initialized with value:", currentValue);
            }

            // Update display when current_value changes
            node.onInputChanged = function(inputName, value) {
                if (inputName === "current_value") {
                    currentValue = parseFloat(value) || 0.50;
                    valueDisplay.textContent = `Value: ${currentValue.toFixed(2)}`;
                    if (ENABLE_DEBUG) {
                        console.log(`[VrchFloatKeyControlNode] current_value updated to: ${currentValue.toFixed(2)}`);
                    }
                }
            };

            // Set to keep track of pressed keys
            const pressedKeys = new Set();

            // Handler for keydown events
            const handleKeyDown = (event) => {
                const fxKeys = ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"];
                const directionOptions = ["Down/Up", "Left/Right"];
                const directionKeysMap = {
                    "Down/Up": ["ArrowDown", "ArrowUp"],
                    "Left/Right": ["ArrowLeft", "ArrowRight"]
                };

                // Add the key to the pressedKeys Set
                pressedKeys.add(event.key);

                // Get the currently selected shortcut_key1 and shortcut_key2
                const shortcutKey1Widget = node.widgets.find(w => w.name === "shortcut_key1");
                const shortcutKey1 = shortcutKey1Widget ? shortcutKey1Widget.value : "F2";

                const shortcutKey2Widget = node.widgets.find(w => w.name === "shortcut_key2");
                const shortcutKey2 = shortcutKey2Widget ? shortcutKey2Widget.value : "Down/Up";

                // Check if shortcut_key1 is pressed
                if (fxKeys.includes(shortcutKey1.toUpperCase())) {
                    const isShortcutKey1Pressed = pressedKeys.has(shortcutKey1.toUpperCase());

                    // Get the list of direction keys based on shortcut_key2
                    const directionKeys = directionKeysMap[shortcutKey2] || ["ArrowDown", "ArrowUp"];

                    // Check if a direction key is pressed
                    for (const dirKey of directionKeys) {
                        if (event.key === dirKey && isShortcutKey1Pressed) {
                            if (dirKey === "ArrowUp" || dirKey === "ArrowRight") {
                                // Increment the value
                                const stepSizeWidget = node.widgets.find(w => w.name === "step_size");
                                const stepSize = parseFloat(stepSizeWidget ? stepSizeWidget.value : 0.01) || 0.01;
                                const newValue = Math.min(parseFloat((currentValue + stepSize).toFixed(2)), 1.0);
                                if (newValue !== currentValue) {
                                    currentValue = newValue;
                                    valueDisplay.textContent = `Value: ${currentValue.toFixed(2)}`;
                                    if (currentValueWidget) {
                                        currentValueWidget.value = currentValue.toFixed(2);
                                    }
                                    if (ENABLE_DEBUG) {
                                        console.log(`[VrchFloatKeyControlNode] Value incremented to: ${currentValue.toFixed(2)}`);
                                    }
                                }
                            } else if (dirKey === "ArrowDown" || dirKey === "ArrowLeft") {
                                // Decrement the value
                                const stepSizeWidget = node.widgets.find(w => w.name === "step_size");
                                const stepSize = parseFloat(stepSizeWidget ? stepSizeWidget.value : 0.01) || 0.01;
                                const newValue = Math.max(parseFloat((currentValue - stepSize).toFixed(2)), 0.0);
                                if (newValue !== currentValue) {
                                    currentValue = newValue;
                                    valueDisplay.textContent = `Value: ${currentValue.toFixed(2)}`;
                                    if (currentValueWidget) {
                                        currentValueWidget.value = currentValue.toFixed(2);
                                    }
                                    if (ENABLE_DEBUG) {
                                        console.log(`[VrchFloatKeyControlNode] Value decremented to: ${currentValue.toFixed(2)}`);
                                    }
                                }
                            }

                            // Prevent default behavior (e.g., scrolling)
                            event.preventDefault();
                        }
                    }
                }
            };

            // Handler for keyup events
            const handleKeyUp = (event) => {
                // Remove the key from the pressedKeys Set
                pressedKeys.delete(event.key);
            };

            // Add the keydown and keyup listeners
            window.addEventListener("keydown", handleKeyDown);
            window.addEventListener("keyup", handleKeyUp);
            if (ENABLE_DEBUG) {
                console.log("[VrchFloatKeyControlNode] Keydown and Keyup event listeners added.");
            }

            // Cleanup when the node is removed
            node.onRemoved = function () {
                window.removeEventListener("keydown", handleKeyDown);
                window.removeEventListener("keyup", handleKeyUp);
                if (ENABLE_DEBUG) {
                    console.log("[VrchFloatKeyControlNode] Keydown and Keyup event listeners removed.");
                }
            };
        }
    }
});

/**
 * VrchBooleanKeyControlNode allows users to toggle a boolean output value (True/False)
 * using a keyboard shortcut. Users can choose a shortcut key from F1-F12.
 */
app.registerExtension({
    name: "vrch.BooleanKeyControlNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchBooleanKeyControlNode") {
            // Removed the block that defines required inputs to prevent UI issues
            // nodeData.input.required = nodeData.input.required || {};
            // nodeData.input.required.shortcut_key = ["shortcut_key"];
            // nodeData.input.required.current_value = ["current_value"];
        }
    },
    getCustomWidgets() {
        return {};
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchBooleanKeyControlNode") {
            // Initialize node state from inputs
            let currentValueWidget = node.widgets.find(w => w.name === "current_value");
            let currentValue = currentValueWidget ? (currentValueWidget.value === "True" || currentValueWidget.value === true) : false; // Default value

            // Create a display element for the current value
            const valueDisplay = document.createElement("div");
            valueDisplay.classList.add("comfy-value-display");
            valueDisplay.textContent = `Value: ${currentValue}`;
            node.addDOMWidget("boolean_value_display", "boolean_value_display", valueDisplay);

            if (ENABLE_DEBUG) {
                console.log("[VrchBooleanKeyControlNode] Initialized with value:", currentValue);
            }

            // Update display when current_value changes
            node.onInputChanged = function(inputName, value) {
                if (inputName === "current_value") {
                    currentValue = value === "True" || value === true;
                    valueDisplay.textContent = `Value: ${currentValue}`;
                    if (ENABLE_DEBUG) {
                        console.log(`[VrchBooleanKeyControlNode] current_value updated to: ${currentValue}`);
                    }
                }
            };

            // Set to keep track of pressed keys
            const pressedKeys = new Set();

            // Handler for keydown events
            const handleKeyDown = (event) => {
                const fxKeys = ["F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"];

                // Add the key to the pressedKeys Set
                pressedKeys.add(event.key);

                // Get the currently selected shortcut_key
                const shortcutKeyWidget = node.widgets.find(w => w.name === "shortcut_key");
                const shortcutKey = shortcutKeyWidget ? shortcutKeyWidget.value : "F2";

                // Check if the pressed key matches shortcut_key
                if (event.key.toUpperCase() === shortcutKey.toUpperCase() && fxKeys.includes(event.key.toUpperCase())) {
                    // Toggle the current_value
                    currentValue = !currentValue;
                    valueDisplay.textContent = `Value: ${currentValue}`;
                    if (currentValueWidget) {
                        currentValueWidget.value = currentValue;
                    }

                    if (ENABLE_DEBUG) {
                        console.log(`[VrchBooleanKeyControlNode] Value toggled to: ${currentValue}`);
                    }

                    // Prevent default behavior (if any)
                    event.preventDefault();
                }
            };

            // Handler for keyup events
            const handleKeyUp = (event) => {
                // Remove the key from the pressedKeys Set
                pressedKeys.delete(event.key);
            };

            // Add the keydown and keyup listeners
            window.addEventListener("keydown", handleKeyDown);
            window.addEventListener("keyup", handleKeyUp);
            if (ENABLE_DEBUG) {
                console.log("[VrchBooleanKeyControlNode] Keydown and Keyup event listeners added.");
            }

            // Cleanup when the node is removed
            node.onRemoved = function () {
                window.removeEventListener("keydown", handleKeyDown);
                window.removeEventListener("keyup", handleKeyUp);
                if (ENABLE_DEBUG) {
                    console.log("[VrchBooleanKeyControlNode] Keydown and Keyup event listeners removed.");
                }
            };
        }
    }
});

// Additional styles for the widget (optional)
const style = document.createElement("style");
style.textContent = `
    .comfy-value-display {
        margin-top: 10px;
        font-size: 16px;
        font-weight: bold;
        text-align: center;
    }
`;
document.head.appendChild(style);