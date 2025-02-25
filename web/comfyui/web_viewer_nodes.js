import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Enable debug logging
const ENABLE_DEBUG = false;

// Helper functions to hide and show widgets
function hideWidget(node, widget) {
    // If widget is already hidden, do nothing
    if (widget.type === "hidden") return;
    // Save original type and computeSize so it can be restored later
    widget.origType = widget.type;
    widget.origComputeSize = widget.computeSize;
    widget.type = "hidden";
}

function showWidget(node, widget) {
    // Restore the widget's original type and computeSize
    widget.type = widget.origType;
    widget.computeSize = widget.origComputeSize;
}

/**
 * Helper function to build the URL based on configuration.
 *
 * @param {Object} config - The configuration object with the following properties:
 *    serverWidget: widget for server address
 *    sslWidget: widget for SSL flag (boolean)
 *    extraParamsWidget: widget for extra parameters (string)
 *    mode: string specifying the viewer mode (e.g., "image", "video", etc.)
 *    path: string specifying the path (default is "web_viewer")
 *    fileGenerator: a function that returns the filename (receives the config as argument)
 *    additionalParams: (optional) extra query parameters as an object (keys with widget values) or string
 *
 * @returns {string} The constructed URL.
 */
function buildUrl(config) {
    // Retrieve server address and SSL flag (with default values)
    const server = config.serverWidget ? config.serverWidget.value : "127.0.0.1:8188";
    const ssl = config.sslWidget ? config.sslWidget.value : false;
    const sslStr = ssl ? "true" : "false";
    const scheme = ssl ? "https" : "http";

    // Process extra parameters; if not empty and not starting with '&', prepend '&'
    let extraParams = config.extraParamsWidget ? config.extraParamsWidget.value : "";
    if (extraParams && extraParams[0] !== "&") {
        extraParams = "&" + extraParams;
    }

    // Use provided mode and path (with a default for path)
    const mode = config.mode || "";
    const path = config.path || "web_viewer";

    // Generate the filename using the provided fileGenerator callback
    const filename = config.fileGenerator ? config.fileGenerator(config) : "";

    // Process additional query parameters if provided
    let additionalQuery = "";
    if (config.additionalParams && typeof config.additionalParams === "object") {
        // Assume each value in the object is a widget; extract its value
        additionalQuery = Object.entries(config.additionalParams)
            .map(([key, widget]) => `&${key}=${widget.value}`)
            .join("");
    } else if (typeof config.additionalParams === "string") {
        additionalQuery = "&" + config.additionalParams;
    }

    // Return the final URL
    return `${scheme}://vrch.ai/viewer?mode=${mode}&server=${server}&ssl=${sslStr}&file=${filename}&path=${path}${additionalQuery}${extraParams}`;
}

/**
 * Helper function to initialize the URL and widget visibility after a delay.
 *
 * @param {Object} node - The current node.
 * @param {Object} showUrlWidget - The widget controlling URL visibility.
 * @param {Object} urlWidget - The URL widget.
 * @param {Function} updateUrl - The updateUrl callback.
 */
function delayInit(node, showUrlWidget, urlWidget, updateUrl) {
    setTimeout(() => {
        if (showUrlWidget) {
            showUrlWidget.value ? showWidget(node, urlWidget) : hideWidget(node, urlWidget);
        }
        updateUrl();
    }, 1000);
}

/**
 * Helper function to create the "Open Web Viewer" button.
 *
 * @param {Object} node - The current node.
 * @param {Object} urlWidget - The widget containing the URL.
 * @param {Object} widthWidget - The widget for window width.
 * @param {Object} heightWidget - The widget for window height.
 */
function createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget) {
    const button = document.createElement("button");
    button.textContent = "Open Web Viewer";
    button.classList.add("comfy-big-button");
    button.onclick = () => {
        if (urlWidget && urlWidget.value) {
            const width = widthWidget ? widthWidget.value : 1280;
            const height = heightWidget ? heightWidget.value : 960;
            window.open(urlWidget.value, "_blank", `width=${width},height=${height}`);
        } else {
            console.error("URL widget not found or empty");
        }
    };
    node.addDOMWidget("button_widget", "Open Web Viewer", button);
}

/**
 * Helper function to set up widget callbacks for updating the URL and toggling visibility.
 *
 * @param {Object} node - The current node.
 * @param {Function} updateUrl - The updateUrl function to be called on widget change.
 * @param {Object} urlWidget - The URL widget to be toggled.
 * @param {Object} showUrlWidget - The widget controlling URL visibility.
 * @param {Array} widgets - An array of widgets whose callbacks will trigger updateUrl.
 * @param {string} [logPrefix] - (Optional) A prefix to log for debugging.
 */
function setupWidgetCallback(node, updateUrl, urlWidget, showUrlWidget, widgets, logPrefix) {
    widgets.forEach(widget => {
        if (widget) {
            widget.callback = () => {
                if (logPrefix && ENABLE_DEBUG) {
                    console.log(`${logPrefix}:::${widget.name}`);
                }
                updateUrl();
            };
        }
    });
    if (showUrlWidget) {
        showUrlWidget.callback = (value) => {
            if (value) {
                showWidget(node, urlWidget);
            } else {
                hideWidget(node, urlWidget);
            }
        };
    }
}

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
                [serverWidget, sslWidget, channelWidget, extraParamsWidget],
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
                        additionalParams: { numberOfImages: numberOfImagesWidget }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [serverWidget, sslWidget, channelWidget, numberOfImagesWidget, extraParamsWidget],
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
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [serverWidget, sslWidget, channelWidget],
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
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [serverWidget, sslWidget, channelWidget, extraParamsWidget],
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
                        }
                    });
                }
            }

            setupWidgetCallback(
                node,
                updateUrl,
                urlWidget,
                showUrlWidget,
                [serverWidget, sslWidget, channelWidget, extraParamsWidget],
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