// key_control_nodes.js

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Debug flag to control log outputs
const ENABLE_DEBUG = false;

/**
 * VrchIntKeyControlNode allows users to control an integer output value within
 * a customizable range using keyboard shortcuts. Users can adjust the step size,
 * choose different shortcut key combinations, and define minimum and maximum values.
 */
app.registerExtension({
    name: "vrch.IntKeyControlNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchIntKeyControlNode") {
            // No changes needed here
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
            let stepSizeWidget = node.widgets.find(w => w.name === "step_size");

            // Retrieve values from the node's inputs
            let currentValue = parseInt(currentValueWidget ? currentValueWidget.value : 50);
            let minValue = parseInt(minValueWidget ? minValueWidget.value : 0);
            let maxValue = parseInt(maxValueWidget ? maxValueWidget.value : 100);
            let stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1);

            // Ensure values are valid numbers
            currentValue = isNaN(currentValue) ? 50 : currentValue;
            minValue = isNaN(minValue) ? 0 : minValue;
            maxValue = isNaN(maxValue) ? 100 : maxValue;
            stepSize = isNaN(stepSize) || stepSize < 1 ? 1 : stepSize;

            // Ensure initial currentValue is within min and max bounds
            currentValue = Math.max(Math.min(currentValue, maxValue), minValue);

            // Create display element for the current value
            const valueDisplay = document.createElement("div");
            valueDisplay.classList.add("comfy-value-display");
            valueDisplay.textContent = `Value: ${currentValue}`;
            node.addDOMWidget("int_value_display", "int_value_display", valueDisplay);

            if (ENABLE_DEBUG) {
                console.log("[VrchIntKeyControlNode] Initialized with value:", currentValue);
                console.log("[VrchIntKeyControlNode] Min value:", minValue);
                console.log("[VrchIntKeyControlNode] Max value:", maxValue);
                console.log("[VrchIntKeyControlNode] Step size:", stepSize);
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

            // Functions to handle widget changes
            const handleMinValueChange = (value) => {
                minValue = parseInt(value);
                if (isNaN(minValue)) {
                    minValue = 0;
                }
                if (minValue > maxValue) {
                    minValue = maxValue;
                    if (ENABLE_DEBUG) {
                        console.log(`[VrchIntKeyControlNode] min_value adjusted to not exceed max_value: ${minValue}`);
                    }
                }
                currentValue = Math.max(currentValue, minValue);
                updateDisplay();
            };

            const handleMaxValueChange = (value) => {
                maxValue = parseInt(value);
                if (isNaN(maxValue)) {
                    maxValue = 100;
                }
                if (maxValue < minValue) {
                    maxValue = minValue;
                    if (ENABLE_DEBUG) {
                        console.log(`[VrchIntKeyControlNode] max_value adjusted to not be below min_value: ${maxValue}`);
                    }
                }
                currentValue = Math.min(currentValue, maxValue);
                updateDisplay();
            };

            const handleStepSizeChange = (value) => {
                stepSize = parseInt(value);
                if (isNaN(stepSize) || stepSize < 1) {
                    stepSize = 1;
                }
                if (ENABLE_DEBUG) {
                    console.log(`[VrchIntKeyControlNode] step_size updated to: ${stepSize}`);
                }
            };

            // Set up callbacks for widget changes
            if (minValueWidget) {
                minValueWidget.callback = (value) => {
                    handleMinValueChange(value);
                };
            }

            if (maxValueWidget) {
                maxValueWidget.callback = (value) => {
                    handleMaxValueChange(value);
                };
            }

            if (stepSizeWidget) {
                stepSizeWidget.callback = (value) => {
                    handleStepSizeChange(value);
                };
            }

            // Function to initialize or re-initialize values on document load
            const initializeValues = () => {
                // Re-read widget values
                currentValue = parseInt(currentValueWidget ? currentValueWidget.value : 50);
                minValue = parseInt(minValueWidget ? minValueWidget.value : 0);
                maxValue = parseInt(maxValueWidget ? maxValueWidget.value : 100);
                stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1);

                // Ensure values are valid numbers
                currentValue = isNaN(currentValue) ? 50 : currentValue;
                minValue = isNaN(minValue) ? 0 : minValue;
                maxValue = isNaN(maxValue) ? 100 : maxValue;
                stepSize = isNaN(stepSize) || stepSize < 1 ? 1 : stepSize;

                // Ensure currentValue is within bounds
                currentValue = Math.max(Math.min(currentValue, maxValue), minValue);

                updateDisplay();

                if (ENABLE_DEBUG) {
                    console.log("[VrchIntKeyControlNode] Values re-initialized on document load:");
                    console.log("[VrchIntKeyControlNode] current_value:", currentValue);
                    console.log("[VrchIntKeyControlNode] min_value:", minValue);
                    console.log("[VrchIntKeyControlNode] max_value:", maxValue);
                    console.log("[VrchIntKeyControlNode] step_size:", stepSize);
                }
            };

            // FIXME
            // the widget value is NOT properly initilised when the node is created and the document is loaded
            // to workaround this issie, I have to introduce this delayed initialization operation
            // which will call initializeValues() again after 1 second when the node has been created
            function delayedInit() {
                if (ENABLE_DEBUG) {
                    console.log("[VrchIntKeyControlNode] delayedInit currentValueWidget.value->", currentValueWidget.value);
                }
                
                initializeValues();

                if (ENABLE_DEBUG) {
                    console.log("[VrchIntKeyControlNode] delayedInit currentValueWidget.value->", currentValueWidget.value);
                }
            }
            setTimeout(delayedInit, 1000);

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
                                const maxValueWidget = node.widgets.find(w => w.name === "max_value");
                                const stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1) || 1;
                                const maxValue = parseInt(maxValueWidget ? maxValueWidget.value : 100) || 100;
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
                                const minValueWidget = node.widgets.find(w => w.name === "min_value");
                                const stepSize = parseInt(stepSizeWidget ? stepSizeWidget.value : 1) || 1;
                                const minValue = parseInt(minValueWidget ? minValueWidget.value : 0) || 0;
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
                // Remove the valueDisplay widget
                if (valueDisplay.parentNode) {
                    valueDisplay.parentNode.removeChild(valueDisplay);
                }
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
                // Remove the valueDisplay widget
                if (valueDisplay.parentNode) {
                    valueDisplay.parentNode.removeChild(valueDisplay);
                }
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
                // Remove the valueDisplay widget
                if (valueDisplay.parentNode) {
                    valueDisplay.parentNode.removeChild(valueDisplay);
                }
                if (ENABLE_DEBUG) {
                    console.log("[VrchBooleanKeyControlNode] Keydown and Keyup event listeners removed.");
                }
            };
        }
    }
});


/**
 * VrchTextKeyControlNode allows users to select one of eight text inputs
 * using a keyboard shortcut. Users can choose a shortcut key (F1-F12),
 * define the current selection (1-8), and optionally skip empty text options
 * when cycling through selections.
 */
app.registerExtension({
    name: "vrch.TextKeyControlNode",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeType.comfyClass === "VrchTextKeyControlNode") {
            // Modify nodeData if necessary
        }
    },
    getCustomWidgets() {
        return {};
    },
    async nodeCreated(node) {
        if (node.comfyClass === "VrchTextKeyControlNode") {
            // Initialize node state from inputs
            let text1Widget = node.widgets.find(w => w.name === "text1");
            let text2Widget = node.widgets.find(w => w.name === "text2");
            let text3Widget = node.widgets.find(w => w.name === "text3");
            let text4Widget = node.widgets.find(w => w.name === "text4");
            let text5Widget = node.widgets.find(w => w.name === "text5");
            let text6Widget = node.widgets.find(w => w.name === "text6");
            let text7Widget = node.widgets.find(w => w.name === "text7");
            let text8Widget = node.widgets.find(w => w.name === "text8");
            let jumpEmptyOptionWidget = node.widgets.find(w => w.name === "skip_empty_option");
            let shortcutKeyWidget = node.widgets.find(w => w.name === "shortcut_key");
            let currentValueWidget = node.widgets.find(w => w.name === "current_value");

            // Retrieve initial values
            let currentValue = parseInt(currentValueWidget ? currentValueWidget.value : "1", 10);
            currentValue = [1, 2, 3, 4, 5, 6, 7, 8].includes(currentValue) ? currentValue : 1;
            let jumpEmptyOption = jumpEmptyOptionWidget ? jumpEmptyOptionWidget.value : true;

            // Create display element for the current value
            const valueDisplay = document.createElement("div");
            valueDisplay.classList.add("comfy-value-display");
            valueDisplay.textContent = `Value: ${currentValue}`;
            node.addDOMWidget("text_value_display", "text_value_display", valueDisplay);

            if (ENABLE_DEBUG) {
                console.log("[VrchTextKeyControlNode] Initialized with current_value:", currentValue);
                console.log("[VrchTextKeyControlNode] skip_empty_option:", jumpEmptyOption);
            }

            // Function to get all texts and filter based on jumpEmptyOption
            const getValidKeys = () => {
                const texts = {
                    "1": text1Widget ? text1Widget.value.trim() : "",
                    "2": text2Widget ? text2Widget.value.trim() : "",
                    "3": text3Widget ? text3Widget.value.trim() : "",
                    "4": text4Widget ? text4Widget.value.trim() : "",
                    "5": text5Widget ? text5Widget.value.trim() : "",
                    "6": text6Widget ? text6Widget.value.trim() : "",
                    "7": text7Widget ? text7Widget.value.trim() : "",
                    "8": text8Widget ? text8Widget.value.trim() : "",
                };

                if (jumpEmptyOption) {
                    return Object.keys(texts).filter(k => texts[k] !== "");
                } else {
                    return ["1", "2", "3", "4", "5", "6", "7", "8"];
                }
            };

            // Update display based on currentValue
            const updateDisplay = () => {
                const validKeys = getValidKeys();
                if (validKeys.length === 0) {
                    valueDisplay.textContent = `Value: None`;
                    if (currentValueWidget) {
                        currentValueWidget.value = "";
                    }
                    return;
                }

                // Ensure currentValue is within validKeys
                if (!validKeys.includes(currentValue.toString())) {
                    currentValue = parseInt(validKeys[0], 10);
                    if (currentValueWidget) {
                        currentValueWidget.value = currentValue.toString();
                    }
                }

                valueDisplay.textContent = `Value: ${currentValue}`;
                if (ENABLE_DEBUG) {
                    console.log(`[VrchTextKeyControlNode] current_value updated to: ${currentValue}`);
                }
            };

            // Handle changes to current_value
            const handleCurrentValueChange = (value) => {
                let val = parseInt(value, 10);
                if (![1, 2, 3, 4, 5, 6, 7, 8].includes(val)) {
                    val = 1;
                }
                currentValue = val;
                updateDisplay();
            };

            if (currentValueWidget) {
                currentValueWidget.callback = (value) => {
                    handleCurrentValueChange(value);
                };
            }

            // Handle changes to skip_empty_option
            const handleJumpEmptyOptionChange = (value) => {
                jumpEmptyOption = value;
                updateDisplay();
                if (ENABLE_DEBUG) {
                    console.log(`[VrchTextKeyControlNode] skip_empty_option set to: ${jumpEmptyOption}`);
                }
            };

            if (jumpEmptyOptionWidget) {
                jumpEmptyOptionWidget.callback = (value) => {
                    handleJumpEmptyOptionChange(value);
                };
            }

            // Initialize display after ensuring all widgets are loaded
            function delayedInit() {
                if (ENABLE_DEBUG) {
                    console.log("[VrchTextKeyControlNode] delayedInit called");
                }
                updateDisplay();
            }
            setTimeout(delayedInit, 1000);

            // Set to keep track of pressed keys
            const pressedKeys = new Set();

            // Handler for keydown events
            const handleKeyDown = (event) => {
                const fxKeys = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"];

                // Add the key to the pressedKeys Set
                pressedKeys.add(event.key.toUpperCase());

                // Get the currently selected shortcut_key
                const shortcutKey = shortcutKeyWidget ? shortcutKeyWidget.value.toUpperCase() : "F2";

                // Check if the pressed key matches the shortcut key
                if (event.key.toUpperCase() === shortcutKey && fxKeys.includes(event.key.toUpperCase())) {
                    const validKeys = getValidKeys();
                    if (validKeys.length === 0) {
                        if (ENABLE_DEBUG) {
                            console.log("[VrchTextKeyControlNode] No valid texts to select.");
                        }
                        return;
                    }

                    // Find the current index in validKeys
                    const currentIndex = validKeys.indexOf(currentValue.toString());
                    // Calculate the next index
                    const nextIndex = (currentIndex + 1) % validKeys.length;
                    // Update currentValue
                    currentValue = parseInt(validKeys[nextIndex], 10);
                    if (currentValueWidget) {
                        currentValueWidget.value = currentValue.toString();
                    }
                    updateDisplay();

                    if (ENABLE_DEBUG) {
                        console.log(`[VrchTextKeyControlNode] current_value toggled to: ${currentValue}`);
                    }

                    // Prevent default behavior
                    event.preventDefault();
                }
            };

            // Handler for keyup events
            const handleKeyUp = (event) => {
                // Remove the key from the pressedKeys Set
                pressedKeys.delete(event.key.toUpperCase());
            };

            // Add the keydown and keyup listeners
            window.addEventListener("keydown", handleKeyDown);
            window.addEventListener("keyup", handleKeyUp);
            if (ENABLE_DEBUG) {
                console.log("[VrchTextKeyControlNode] Keydown and Keyup event listeners added.");
            }

            // Cleanup when the node is removed
            node.onRemoved = function () {
                window.removeEventListener("keydown", handleKeyDown);
                window.removeEventListener("keyup", handleKeyUp);
                // Remove the valueDisplay widget
                if (valueDisplay.parentNode) {
                    valueDisplay.parentNode.removeChild(valueDisplay);
                }
                if (ENABLE_DEBUG) {
                    console.log("[VrchTextKeyControlNode] Keydown and Keyup event listeners removed.");
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