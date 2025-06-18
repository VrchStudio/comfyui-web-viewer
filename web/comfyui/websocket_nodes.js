import { app } from "../../scripts/app.js";
import { ComfyWidgets } from '../../../scripts/widgets.js';

import {
    hideWidget,
    showWidget,
    buildUrl,
    delayInit,
    createOpenWebViewerButton,
    createQRCodeWidget,
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
    indicator.textContent = "Run to Start Server"; // Initial text
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
            const blendModeWidget = node.widgets.find(w => w.name === "blend_mode");
            const loopPlaybackWidget = node.widgets.find(w => w.name === "loop_playback");
            const updateOnEndWidget = node.widgets.find(w => w.name === "update_on_end");
            const backgroundColorWidget = node.widgets.find(w => w.name === "background_colour_hex");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");
            const devModeWidget = node.widgets.find(w => w.name === "dev_mode");

            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "image-websocket",
                        protocol: "websocket",
                        devMode: devModeWidget,
                        additionalParams: {
                            channel: channelWidget,
                            numberOfImages: numberOfImagesWidget,
                            imageDisplayDuration: imageDisplayDurationWidget,
                            fadeAnimDuration: fadeAnimDurationWidget,
                            mixBlendMode: blendModeWidget,
                            enableLoop: loopPlaybackWidget,
                            enableUpdateOnEnd: updateOnEndWidget,
                            bgColourPicker: backgroundColorWidget,
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
                    blendModeWidget,
                    loopPlaybackWidget,
                    updateOnEndWidget,
                    backgroundColorWidget,
                    devModeWidget,
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
            // Find the debug widget to access its current value
            const debugWidget = node.widgets.find(w => w.name === "debug");
            
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

                // Get server status and debug status from message
                const isRunning = message?.server_status?.[0];
                const isDebugEnabled = message?.debug_status?.[0];

                if (typeof isRunning !== 'undefined') {
                    statusIndicator.textContent = isRunning ? "Running" : "Stopped";
                    statusIndicator.classList.toggle("on", !!isRunning);
                    statusIndicator.classList.toggle("off", !isRunning);
                    
                    // Log status update if debug is enabled
                    if (isDebugEnabled) {
                        console.log(`[VrchWebSocketServerNode] Server status update: ${isRunning ? 'Running' : 'Stopped'}`);
                    }
                }
                
                // If there's an error message from path validation, it would be handled by ComfyUI's error system
                // We can add extra debug logging here if needed
                if (isDebugEnabled && typeof isRunning === 'undefined') {
                    console.log("[VrchWebSocketServerNode] Executed but no status received:", message);
                }
            };
        }
    }
});

// Add custom styles for the button and indicator
const style = document.createElement("style");
style.textContent = `
    /* Button container style */
    .vrch-button-container {
        width: 100%;
        box-sizing: border-box;
        display: flex;
        height: 48px !important; /* Ensure the container has a fixed height */
        align-items: center; /* Center vertically */
        justify-content: center; /* Center horizontally */
    }
    
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
        width: 100%;
        height: 100%; 
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
        width: 200px; 
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