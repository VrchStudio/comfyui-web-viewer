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
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
            const rawDataWidget = node.widgets.find(w => w.name === "raw_data");
            const debugWidget = node.widgets.find(w => w.name === "debug");
            // Set up the timer to fetch gamepad data
            let timerId = null;

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

            // fetch gamepad data from browser gamepad API
            const fetchGamepadData = async () => {
                try {
                    const gamepads = navigator.getGamepads();
                    if (gamepads) {
                        const gamepad = gamepads[indexWidget.value];

                        // Only log in debug mode with throttling
                        if (debugWidget && debugWidget.value && Math.random() < 0.1) { // 90% logs are suppressed
                            console.log(`[VrchGamepadLoaderNode] Gamepad data for index ${indexWidget.value}:`, gamepad);
                        }

                        if (gamepad) {
                            // Always update name for UI responsiveness
                            if (nameWidget.value !== gamepad.id) {
                                nameWidget.value = gamepad.id;
                            }
                            
                            // Extract gamepad data and convert to JSON string
                            const gamepadData = extractGamepadData(gamepad);
                            const dataString = JSON.stringify(gamepadData, null, 2);
                            // Only update if data actually changed
                            if (rawDataWidget.value !== dataString) {
                                rawDataWidget.value = dataString;
                            }
                        } else if (nameWidget.value !== "n/a") {
                            nameWidget.value = "n/a";
                            if (debugWidget && debugWidget.value) {
                                rawDataWidget.value = "No gamepad found";
                            }
                        }
                    } else if (nameWidget.value !== "n/a") {
                        nameWidget.value = "n/a";
                        if (debugWidget && debugWidget.value) {
                            rawDataWidget.value = "No gamepad data available";
                        }
                    }
                } catch (error) {
                    console.error("[VrchGamepadLoaderNode] Error fetching gamepad data:", error);
                }
            };

            // Function to start or restart the timer with the current refresh interval
            const startTimer = () => {
                // Clear existing timer if it exists
                if (timerId !== null) {
                    clearInterval(timerId);
                    timerId = null;
                }
                
                // Get the refresh interval value (default to 100ms if not available)
                const interval = refreshIntervalWidget ? Math.max(10, refreshIntervalWidget.value) : 100;
                
                // Set up the new timer with the current interval value
                timerId = setInterval(() => {
                    fetchGamepadData();
                }, interval);
                
                if (debugWidget && debugWidget.value) {
                    console.log(`[VrchGamepadLoaderNode] Gamepad data refresh interval set to ${interval}ms`);
                }
            };
            
            // Add callback to refresh interval widget to update the timer when changed
            if (refreshIntervalWidget) {
                refreshIntervalWidget.callback = () => {
                    startTimer();
                };
            }

            // Initial timer start
            startTimer();

            // Set a delay initialization for the widget visibility
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

app.registerExtension({  
    name: "vrch.XboxControllerNode",  
    async nodeCreated(node) {  
        if (node.comfyClass === "VrchXboxControllerNode") {  
            // Define the SVG template for Xbox controller  
            const svgTemplate = `  
            <svg viewBox="0 0 300 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">  
                <style>  
                    /* Wireframe for buttons and controls, keep body fill */  
                    path:not(.controller-body), rect, circle { stroke: #666; stroke-width: 2; }
                    /* Default state - no fill */
                    path:not(.controller-body):not(.pressed), 
                    rect:not(.pressed), 
                    circle:not(.pressed) { fill: none; }
                    /* Allow JavaScript to control the fill when elements get .pressed class */
                    .pressed { transition: fill 0.2s ease; }
                    path.controller-body { fill: #222; stroke: none; }  
                </style>  
                <!-- Controller base -->  
                <path class="controller-body" d="M150,30 C70,30 30,80 30,120 C30,160 70,170 150,170 C230,170 270,160 270,120 C270,80 230,30 150,30 Z" />  
                  
                <!-- D-pad - moved down 20px -->  
                <circle id="dpad" cx="90" cy="130" r="10" />   
                <rect id="dpad-up" x="85" y="100" width="10" height="20" rx="2" />  
                <rect id="dpad-down" x="85" y="140" width="10" height="20" rx="2" />  
                <rect id="dpad-left" x="60" y="125" width="20" height="10" rx="2" />  
                <rect id="dpad-right" x="100" y="125" width="20" height="10" rx="2" />  
                  
                <!-- Face buttons -->  
                <circle id="button-a" cx="210" cy="110" r="10" />  
                <circle id="button-b" cx="230" cy="90" r="10" />  
                <circle id="button-x" cx="190" cy="90" r="10" />  
                <circle id="button-y" cx="210" cy="70" r="10" />  
                  
                <!-- Bumpers -->  
                <rect id="lb" x="70" y="35" width="40" height="10" rx="5" />  
                <rect id="rb" x="190" y="35" width="40" height="10" rx="5" />  
                  
                <!-- Triggers -->  
                <rect id="lt" x="70" y="10" width="40" height="20" rx="5" />
                <rect id="rt" x="190" y="10" width="40" height="20" rx="5" />
                  
                <!-- Sticks - right stick moved down 20px -->  
                <circle id="left-stick-base" cx="90" cy="70" r="15" />  
                <circle id="left-stick" cx="90" cy="70" r="10" />  
                <circle id="right-stick-base" cx="190" cy="140" r="15" />  
                <circle id="right-stick" cx="190" cy="140" r="10" />  
                  
                <!-- Center buttons -->  
                <rect id="button-back" x="120" y="70" width="25" height="10" rx="2" />  
                <rect id="button-start" x="150" y="70" width="25" height="10" rx="2" />  
                <circle id="button-guide" cx="148" cy="100" r="12" />  
            </svg>`;  
              
            // Create and register a container for the SVG as a DOM widget
            node.svgContainer = document.createElement("div");
            node.svgContainer.style.width = "100%";
            node.svgContainer.style.height = "250px";
            node.svgContainer.style.overflow = "hidden";
            node.svgContainer.innerHTML = svgTemplate;
            node.addDOMWidget("svg_container", "Controller", node.svgContainer);
              
            // Function to update SVG elements based on controller state  
            node.updateControllerVisual = function(buttonsBoolean, buttonsFloat, leftStick, rightStick) {  
                if (!node.svgContainer) return;  
                  
                const svg = node.svgContainer.querySelector("svg");  
                if (!svg) return;  
                  
                // Standard Xbox mapping (may need adjustment based on browser/device)  
                const BUTTON_A = 0;  
                const BUTTON_B = 1;  
                const BUTTON_X = 2;  
                const BUTTON_Y = 3;  
                const BUTTON_LB = 4;  
                const BUTTON_RB = 5;  
                const BUTTON_LT = 6;  
                const BUTTON_RT = 7;  
                const BUTTON_BACK = 8;  
                const BUTTON_START = 9;  
                const BUTTON_L_STICK = 10;  
                const BUTTON_R_STICK = 11;  
                const BUTTON_DPAD_UP = 12;  
                const BUTTON_DPAD_DOWN = 13;  
                const BUTTON_DPAD_LEFT = 14;  
                const BUTTON_DPAD_RIGHT = 15;  
                const BUTTON_GUIDE = 16;  
                  
                // Update face buttons  
                this.updateButtonElement(svg, "#button-a", buttonsBoolean[BUTTON_A], buttonsFloat[BUTTON_A], "#0f0", "#0a0");  
                this.updateButtonElement(svg, "#button-b", buttonsBoolean[BUTTON_B], buttonsFloat[BUTTON_B], "#f00", "#a00");  
                this.updateButtonElement(svg, "#button-x", buttonsBoolean[BUTTON_X], buttonsFloat[BUTTON_X], "#00f", "#00a");  
                this.updateButtonElement(svg, "#button-y", buttonsBoolean[BUTTON_Y], buttonsFloat[BUTTON_Y], "#ff0", "#aa0");  
                  
                // Update bumpers and triggers  
                this.updateButtonElement(svg, "#lb", buttonsBoolean[BUTTON_LB], buttonsFloat[BUTTON_LB], "#666", "#999");  
                this.updateButtonElement(svg, "#rb", buttonsBoolean[BUTTON_RB], buttonsFloat[BUTTON_RB], "#666", "#999");  
                this.updateButtonElement(svg, "#lt", buttonsBoolean[BUTTON_LT], buttonsFloat[BUTTON_LT], "#666", "#999");  
                this.updateButtonElement(svg, "#rt", buttonsBoolean[BUTTON_RT], buttonsFloat[BUTTON_RT], "#666", "#999");  
                  
                // Update D-pad  
                this.updateButtonElement(svg, "#dpad-up", buttonsBoolean[BUTTON_DPAD_UP], buttonsFloat[BUTTON_DPAD_UP], "#666", "#999");  
                this.updateButtonElement(svg, "#dpad-down", buttonsBoolean[BUTTON_DPAD_DOWN], buttonsFloat[BUTTON_DPAD_DOWN], "#666", "#999");  
                this.updateButtonElement(svg, "#dpad-left", buttonsBoolean[BUTTON_DPAD_LEFT], buttonsFloat[BUTTON_DPAD_LEFT], "#666", "#999");  
                this.updateButtonElement(svg, "#dpad-right", buttonsBoolean[BUTTON_DPAD_RIGHT], buttonsFloat[BUTTON_DPAD_RIGHT], "#666", "#999");  
                  
                // Update center buttons  
                this.updateButtonElement(svg, "#button-back", buttonsBoolean[BUTTON_BACK], buttonsFloat[BUTTON_BACK], "#666", "#999");  
                this.updateButtonElement(svg, "#button-start", buttonsBoolean[BUTTON_START], buttonsFloat[BUTTON_START], "#666", "#999");  
                this.updateButtonElement(svg, "#button-guide", buttonsBoolean[BUTTON_GUIDE], buttonsFloat[BUTTON_GUIDE], "#666", "#999");  
                  
                // Update analog sticks  
                if (leftStick && leftStick.length >= 2) {  
                    const leftStickElem = svg.querySelector("#left-stick");  
                    if (leftStickElem) {  
                        const baseX = 90;  
                        const baseY = 70;  
                        const maxOffset = 10;  
                        const newX = baseX + (leftStick[0] * maxOffset);  
                        const newY = baseY + (leftStick[1] * maxOffset);  
                        leftStickElem.setAttribute("cx", newX);  
                        leftStickElem.setAttribute("cy", newY);  
                          
                        // Highlight left stick if pressed  
                        if (buttonsBoolean[BUTTON_L_STICK]) {  
                            leftStickElem.setAttribute("fill", "#999");  
                            leftStickElem.classList.add("pressed");
                        } else {  
                            leftStickElem.setAttribute("fill", "none");
                            leftStickElem.classList.remove("pressed");
                        }  
                    }  
                }  
                  
                if (rightStick && rightStick.length >= 2) {  
                    const rightStickElem = svg.querySelector("#right-stick");  
                    if (rightStickElem) {  
                        const baseX = 190;  
                        const baseY = 140;  
                        const maxOffset = 10;  
                        const newX = baseX + (rightStick[0] * maxOffset);  
                        const newY = baseY + (rightStick[1] * maxOffset);  
                        rightStickElem.setAttribute("cx", newX);  
                        rightStickElem.setAttribute("cy", newY);  
                          
                        // Highlight right stick if pressed  
                        if (buttonsBoolean[BUTTON_R_STICK]) {  
                            rightStickElem.setAttribute("fill", "#999");  
                            rightStickElem.classList.add("pressed");
                        } else {  
                            rightStickElem.setAttribute("fill", "none");
                            rightStickElem.classList.remove("pressed");
                        }  
                    }  
                }  
            };  
              
            // Helper function to update a button element based on its state  
            node.updateButtonElement = function(svg, selector, isPressed, pressure, defaultColor, activeColor) {  
                const element = svg.querySelector(selector);
                if (!element) return;
                
                // L2/R2 triggers - ID matching in new SVG structure
                if (selector === "#lt" || selector === "#rt" || selector === "#L2" || selector === "#R2") {
                    // triggers pressure-based fill
                    if (pressure > 0) {
                        element.setAttribute("fill", activeColor);
                        element.setAttribute("fill-opacity", pressure);
                        element.classList.add("pressed");
                    } else {
                        element.setAttribute("fill", "none");
                        element.classList.remove("pressed");
                    }
                } 
                // Face buttons, DPad, etc.
                else if (
                    selector.includes("button") || 
                    selector.includes("dpad") || 
                    selector === "#lb" || selector === "#rb" || 
                    selector === "#L1" || selector === "#R1" ||
                    selector.includes("BTop") || selector.includes("BRight") || 
                    selector.includes("BBottom") || selector.includes("BLeft") ||
                    selector.includes("DUp") || selector.includes("DRight") || 
                    selector.includes("DDown") || selector.includes("DLeft") ||
                    selector.includes("LMeta") || selector.includes("RMeta")
                ) {
                    // regular buttons - just toggle fill
                    if (isPressed) {
                        element.setAttribute("fill", activeColor);
                        element.classList.add("pressed");
                    } else {
                        element.setAttribute("fill", "none");
                        element.classList.remove("pressed");
                    }
                }
            };  
              
            // Hook into the node's onExecuted callback  
            const originalOnExecuted = node.onExecuted;  
            node.onExecuted = function(message) {  
                if (originalOnExecuted) {  
                    originalOnExecuted.call(node, message);  
                }  
                  
                // Get the input data from the message  
                const buttonsBoolean = message?.buttonsBoolean || [];  
                const buttonsFloat = message?.buttonsFloat || [];  
                const leftStick = message?.leftStick || [0, 0];  
                const rightStick = message?.rightStick || [0, 0];  
                  
                // Update the controller visualization  
                node.updateControllerVisual(buttonsBoolean, buttonsFloat, leftStick, rightStick);  
            };  
        }  
    }  
});
