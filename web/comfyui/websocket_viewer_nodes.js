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

// Add custom styles for the button
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
`;
document.head.appendChild(style);