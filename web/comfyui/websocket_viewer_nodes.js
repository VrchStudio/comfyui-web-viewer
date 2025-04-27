import { app } from "../../scripts/app.js";
import { ComfyWidgets } from '../../../scripts/widgets.js';

import {
    hideWidget,
    showWidget,
    buildUrl,
    delayInit,
    createOpenWebViewerButton,
    setupWidgetCallback,
} from "./node_utils.js";

// =====================================================================
// Helper: Create Server Status Indicator Element
// =====================================================================
/**
 * Create a non‑clickable circular indicator element for server status.
 * @returns {HTMLElement}
 */
function createServerStatusIndicatorElement() {
    const indicator = document.createElement("div");
    indicator.textContent = "Server"; // Initial text
    indicator.classList.add("vrch-server-indicator", "off"); // Start as off
    indicator.style.pointerEvents = "none";
    return indicator;
}

// =====================================================================
// Extension: vrch.ImageWebSocketWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.ImageWebSocketWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchImageWebSocketWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const numberOfImagesWidget = node.widgets.find(w => w.name === "number_of_images");
            const imageDisplayDurationWidget = node.widgets.find(w => w.name === "image_display_duration");
            const fadeAnimDurationWidget = node.widgets.find(w => w.name === "fade_anim_duration");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");

            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "image-websocket",
                        protocol: "websocket",
                        additionalParams: {
                            numberOfImages: numberOfImagesWidget,
                            imageDisplayDuration: imageDisplayDurationWidget,
                            fadeAnimDuration: fadeAnimDurationWidget,
                        }
                    });
                }
            }

            // Use setupWidgetCallback() with a custom log prefix if desired
            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [
                    serverWidget,
                    channelWidget,
                    extraParamsWidget,
                    numberOfImagesWidget,
                    imageDisplayDurationWidget,
                    fadeAnimDurationWidget,
                    extraParamsWidget,
                ],
                "VrchImageWebSocketWebViewerNode"
            );

            hideWidget(node, urlWidget);
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.WebSocketServer
// =====================================================================
app.registerExtension({
    name: "vrch.WebSocketServer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchWebSocketServerNode") {
            // Create a container for the indicator
            const container = document.createElement("div");
            container.classList.add("vrch-server-indicator-container");
            node.addDOMWidget("indicator_container", "Status", container);

            // Initialize the indicator
            const statusIndicator = createServerStatusIndicatorElement();
            container.appendChild(statusIndicator);

            // Update indicator based on execution results
            const onExecuted = node.onExecuted;
            node.onExecuted = function(message) {
                onExecuted?.apply(this, arguments);

                if (message?.server_status) {
                    const isRunning = message.server_status[0]; // Expecting a list with one boolean
                    statusIndicator.textContent = isRunning ? "Running" : "Stopped";
                    statusIndicator.classList.toggle("on", !!isRunning);
                    statusIndicator.classList.toggle("off", !isRunning);
                }
            };

             // Add a button to manually refresh status (optional, IS_CHANGED handles auto-refresh)
             /*
             const refreshButton = node.addWidget("button", "Refresh Status", null, () => {
                 // Trigger node execution manually if needed, though IS_CHANGED should handle it
                 node.graph.runStep(1, false); // Or find a more targeted way if possible
             });
             refreshButton.serialize = false;
             */
        }
    }
});

// Add custom styles for the button and indicator
const style = document.createElement("style");
style.textContent = `
    .vrch-big-button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
        transition: background-color 0.3s, transform 0.2s;
    }

    .vrch-big-button:hover {
        background-color: #45a049;
        transform: scale(1.05); 
    }

    .vrch-big-button:active {
        background-color: #3e8e41;
        transform: scale(1);
    }

    /* Styles for Server Status Indicator */
    .vrch-server-indicator-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 4px;
    }
    .vrch-server-indicator {
        width: 80px; /* Wider to fit text */
        height: 32px;
        border-radius: 16px; /* Pill shape */
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: bold;
        transition: background-color 0.3s, color 0.3s;
        user-select: none;
        border: 1px solid #555; /* Add border */
    }
    .vrch-server-indicator.off {
        background-color: #ccc;
        color: #333;
    }
    .vrch-server-indicator.on {
        background-color: #4CAF50; /* Green */
        color: #fff;
    }
`;
document.head.appendChild(style);