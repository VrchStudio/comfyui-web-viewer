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
// Extension: vrch.ImageWebSocketSimpleWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.ImageWebSocketSimpleWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchImageWebSocketSimpleWebViewerNode") {
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
                    numberOfImagesWidget,
                    imageDisplayDurationWidget,
                    fadeAnimDurationWidget,
                    extraParamsWidget,
                    devModeWidget,
                ],
                "VrchImageWebSocketSimpleWebViewerNode"
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
            try {
                // Find widgets
                const debugWidget = node.widgets.find(w => w.name === "debug");
                const serverWidget = node.widgets.find(w => w.name === "server");
                const portWidget = node.widgets.find(w => w.name === "port");
            
                // Create a container for the indicator
                const container = document.createElement("div");
                container.classList.add("vrch-server-indicator-container");
                node.addDOMWidget("indicator_container", "Status", container);

                // Initialize the indicator
                const statusIndicator = createServerStatusIndicatorElement();
                container.appendChild(statusIndicator);

                // Create Full Address container with copy feature
                const addrContainer = document.createElement("div");
                addrContainer.classList.add("vrch-server-address-container");
                const addrText = document.createElement("span");
                addrText.classList.add("vrch-server-address");
                addrText.textContent = "-";
                addrContainer.appendChild(addrText);
                node.addDOMWidget("full_address_container", "Address", addrContainer);

                function computeAddress() {
                    const host = serverWidget?.value ?? "";
                    const port = portWidget?.value ?? "";
                    return `${host}:${port}`;
                }

                function updateAddress(fromExecuted) {
                    // Compute locally; onExecuted will override with server_full if provided
                    addrText.textContent = computeAddress();
                }

                async function copyToClipboard(text) {
                    try {
                        if (navigator.clipboard && window.isSecureContext) {
                            await navigator.clipboard.writeText(text);
                        } else {
                            const ta = document.createElement("textarea");
                            ta.value = text;
                            ta.style.position = "fixed";
                            ta.style.left = "-9999px";
                            document.body.appendChild(ta);
                            ta.focus();
                            ta.select();
                            document.execCommand("copy");
                            document.body.removeChild(ta);
                        }
                        // Show a checkmark via CSS without shifting layout
                        addrText.classList.add("copied");
                        setTimeout(() => { addrText.classList.remove("copied"); }, 1200);
                    } catch (e) {
                        console.warn("[VrchWebSocketServerNode] Copy failed", e);
                    }
                }

                addrText.addEventListener("click", () => {
                    copyToClipboard(addrText.textContent || "");
                });

            // Hook widget callbacks to refresh address
                function hookWidget(widget) {
                    if (!widget) return;
                    const orig = widget.callback;
                    widget.callback = function() {
                        try { orig?.apply(this, arguments); } catch(e) { /* ignore */ }
                        try { updateAddress(false); } catch(e) { /* ignore */ }
                    };
                }
                hookWidget(serverWidget);
                hookWidget(portWidget);
                // initial
                updateAddress(false);

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
                // Update full address if provided
                    const serverFull = message?.server_full?.[0];
                    if (serverFull) {
                        addrText.textContent = serverFull;
                    } else {
                        updateAddress(true);
                    }
                
                // If there's an error message from path validation, it would be handled by ComfyUI's error system
                // We can add extra debug logging here if needed
                if (isDebugEnabled && typeof isRunning === 'undefined') {
                    console.log("[VrchWebSocketServerNode] Executed but no status received:", message);
                }
                };
            } catch (e) {
                console.error("[vrch.WebSocketServer] UI init failed:", e);
            }
        }
    }
});

// =====================================================================
// Extension: vrch.ImageWebSocketFilterSettings (add Reset Filters button)
// =====================================================================
app.registerExtension({
    name: "vrch.ImageWebSocketFilterSettings",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchImageWebSocketFilterSettingsNode") {
            // New order (grayscale removed): opacity, brightness, contrast, saturate, hue_rotate, invert, sepia, blur
            const widgetNames = [
                "opacity",
                "brightness",
                "contrast",
                "saturate",
                "hue_rotate",
                "invert",
                "sepia",
                "blur"
            ];
            const defaults = {
                opacity: 1.0,
                brightness: 1.0,
                contrast: 1.0,
                saturate: 1.0,
                hue_rotate: 0,
                invert: 0.0,
                sepia: 0.0,
                blur: 0,
            };

            // Create button container
            const container = document.createElement("div");
            // Use a smaller dedicated container so it isn't as tall as the big viewer buttons
            container.classList.add("vrch-filter-reset-container");
            const btn = document.createElement("button");
            btn.textContent = "Reset Filters";
            btn.classList.add("vrch-filter-reset-btn");
            container.appendChild(btn);
            node.addDOMWidget("filter_reset_btn", "Reset", container);

            function setWidgetValue(widget, value) {
                if (!widget) return;
                widget.value = value;
                if (widget.callback) {
                    try { widget.callback(widget.value, node, widget); } catch(e) { /* ignore */ }
                }
            }

            btn.addEventListener("click", () => {
                widgetNames.forEach(name => {
                    const w = node.widgets.find(w => w.name === name);
                    if (w) setWidgetValue(w, defaults[name]);
                });
                // Force UI refresh
                app.graph.setDirtyCanvas(true, true);
                console.log("[VrchImageWebSocketFilterSettingsNode] Filters reset to defaults", defaults);
            });
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
        transform: scale(1.01); 
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
        padding: 2px; /* tighter */
        margin: 0;    /* remove extra gap */
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
    .vrch-filter-reset-container {
        width: 100%;
        box-sizing: border-box;
        display: flex;
        height: 32px; /* smaller than big buttons */
        align-items: center;
        justify-content: center;
    }
    .vrch-filter-reset-btn {
        background-color: #4CAF50;
        color: #fff;
        font-size: 16px;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        width: 90%;
        height: 32px;
        line-height: 1;
        transition: background-color 0.25s, transform 0.2s;
        padding: 4px 8px;
    }
    .vrch-filter-reset-btn:hover { background-color: #45a049; transform: scale(1.01); }
    .vrch-filter-reset-btn:active { background-color: #3e8e41; transform: scale(1); }

    /* Server full address (centered, clickable, checkmark overlay) */
    .vrch-server-address-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2px 0; /* tighter */
        margin-top: -4px; /* pull closer to status */
        width: 100%;
        box-sizing: border-box;
    }
    .vrch-server-address {
        padding: 6px 14px;
        background: #222;
        border: 1px solid #555;
        border-radius: 6px;
        font-family: monospace;
        font-size: 15px;
        position: relative;
        cursor: pointer;
    }
    .vrch-server-address::after {
        content: "copied"; /* small indicator */
        position: absolute;
        right: -28px;  /* outside top-right corner */
        top: -8px;
        color: #7CFC00;
        font-weight: 700;
        font-size: 11px; /* small text */
        letter-spacing: 0.3px;
        opacity: 0;
        transform: scale(0.96);
        transition: opacity 0.2s ease, transform 0.2s ease;
        pointer-events: none;
    }
    .vrch-server-address.copied::after {
        opacity: 1;
        transform: scale(1.0);
    }
`;
document.head.appendChild(style);
