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
// Extension: vrch.WebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.WebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const filenameWidget = node.widgets.find(w => w.name === "filename");
            const pathWidget = node.widgets.find(w => w.name === "path");
            const modeWidget = node.widgets.find(w => w.name === "mode");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");

            // Function to update the URL using the buildUrl helper
            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: modeWidget ? modeWidget.value : "image",
                        path: pathWidget ? pathWidget.value : "web_viewer",
                        fileGenerator: (cfg) =>
                            filenameWidget ? filenameWidget.value : "web_viewer_image.jpeg"
                    });
                }
            }

            // Use setupWidgetCallback() to attach callbacks
            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [serverWidget, sslWidget, filenameWidget, pathWidget, modeWidget, extraParamsWidget],
                "VrchWebViewerNode"
            );

            // Initially hide the URL widget
            hideWidget(node, urlWidget);

            // Create the button and initialize after a delay
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.ImageWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.ImageWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchImageWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
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
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "image",
                        path: "web_viewer",
                        fileGenerator: (cfg) => {
                            const channel = channelWidget ? channelWidget.value : "1";
                            return `channel_${channel}.jpeg`;
                        },
                        additionalParams: { 
                            refreshInterval: refreshIntervalWidget,
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
                    sslWidget, 
                    channelWidget, 
                    refreshIntervalWidget,
                    fadeAnimDurationWidget,
                    extraParamsWidget,
                ],
                "VrchImageWebViewerNode"
            );

            hideWidget(node, urlWidget);
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.ImageFlipbookWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.ImageFlipbookWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchImageFlipBookWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const numberOfImagesWidget = node.widgets.find(w => w.name === "number_of_images");
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
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
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "flipbook",
                        path: "web_viewer",
                        fileGenerator: (cfg) => {
                            const channel = channelWidget ? channelWidget.value : "1";
                            return `channel_${channel}.jpeg`;
                        },
                        additionalParams: { 
                            numberOfImages: numberOfImagesWidget,
                            refreshInterval: refreshIntervalWidget,
                            imageDisplayDuration: imageDisplayDurationWidget,
                            fadeAnimDuration: fadeAnimDurationWidget,
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [
                    serverWidget, 
                    sslWidget, 
                    channelWidget,
                    numberOfImagesWidget,
                    refreshIntervalWidget,
                    imageDisplayDurationWidget,
                    fadeAnimDurationWidget,
                    extraParamsWidget,
                ],
                "VrchImageFlipbookWebViewerNode"
            );

            hideWidget(node, urlWidget);
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.VideoWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.VideoWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchVideoWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");

            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "video",
                        path: "web_viewer",
                        fileGenerator: (cfg) => {
                            const channel = channelWidget ? channelWidget.value : "1";
                            return `channel_${channel}.mp4`;
                        },
                        additionalParams: { 
                            refreshInterval: refreshIntervalWidget,
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [
                    serverWidget, 
                    sslWidget, 
                    channelWidget,
                    refreshIntervalWidget,
                    extraParamsWidget,
                ],
                "VrchVideoWebViewerNode"
            );

            hideWidget(node, urlWidget);
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.AudioWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.AudioWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchAudioWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
            const visualizerTypeWidget = node.widgets.find(w => w.name === "visualizer_type");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");

            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "audio",
                        path: "web_viewer",
                        fileGenerator: (cfg) => {
                            const channel = channelWidget ? channelWidget.value : "1";
                            return `channel_${channel}.mp3`;
                        },
                        additionalParams: { 
                            refreshInterval: refreshIntervalWidget,
                            visualizerType: visualizerTypeWidget,
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [
                    serverWidget, 
                    sslWidget, 
                    channelWidget,
                    refreshIntervalWidget,
                    visualizerTypeWidget,
                    extraParamsWidget,
                ],
                "VrchAudioWebViewerNode"
            );

            hideWidget(node, urlWidget);
            createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget);
            delayInit(node, showUrlWidget, urlWidget, updateUrl);
        }
    }
});

// =====================================================================
// Extension: vrch.ModelWebViewer
// =====================================================================
app.registerExtension({
    name: "vrch.ModelWebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchModelWebViewerNode") {
            // Find existing widgets
            const serverWidget = node.widgets.find(w => w.name === "server");
            const sslWidget = node.widgets.find(w => w.name === "ssl");
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const refreshIntervalWidget = node.widgets.find(w => w.name === "refresh_interval");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            const extraParamsWidget = node.widgets.find(w => w.name === "extra_params");
            const urlWidget = node.widgets.find(w => w.name === "url");
            const showUrlWidget = node.widgets.find(w => w.name === "show_url");

            function updateUrl() {
                if (urlWidget) {
                    urlWidget.value = buildUrl({
                        serverWidget: serverWidget,
                        sslWidget: sslWidget,
                        extraParamsWidget: extraParamsWidget,
                        mode: "3dmodel",
                        path: "web_viewer",
                        fileGenerator: (cfg) => {
                            const channel = channelWidget ? channelWidget.value : "1";
                            return `channel_${channel}.glb`;
                        },
                        additionalParams: { 
                            refreshInterval: refreshIntervalWidget,
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [
                    serverWidget, 
                    sslWidget, 
                    channelWidget, 
                    refreshIntervalWidget,
                    extraParamsWidget,
                ],
                "VrchModelWebViewerNode"
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
    .comfy-big-button {
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

    .comfy-big-button:hover {
        background-color: #45a049;
        transform: scale(1.05); 
    }

    .comfy-big-button:active {
        background-color: #3e8e41;
        transform: scale(1);
    }
`;
document.head.appendChild(style);