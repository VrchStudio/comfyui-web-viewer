// Enable debug logging
export const ENABLE_DEBUG = false;

// Helper functions to hide and show widgets
export function hideWidget(node, widget) {
    // If widget is already hidden, do nothing
    if (widget.type === "hidden") return;
    // Save original type and computeSize so it can be restored later
    widget.origType = widget.type;
    widget.origComputeSize = widget.computeSize;
    widget.type = "hidden";
}

export function showWidget(node, widget) {
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
 *    protocol: (optional) protocol to use (default is "http", also support "websocket")
 *    channel: (optional) channel number (default is "1", [1-8] based)
 *    fileGenerator: a function that returns the filename (receives the config as argument)
 *    additionalParams: (optional) extra query parameters as an object (keys with widget values) or string
 *
 * @returns {string} The constructed URL.
 */
export function buildUrl(config) {
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
    const pathStr = path ? `&path=${path}` : "";

    // Generate the filename using the provided fileGenerator callback
    const filename = config.fileGenerator ? config.fileGenerator(config) : "";
    const filenameStr = filename ? `&filename=${filename}` : "";

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

    let protocolStr = "";
    let channelStr = "";
    // If config.protocol is not http, insert the protocol in the URL before the server
    if (config.protocol) {
        protocolStr = `&protocol=${config.protocol}`;
    }
    if (config.channel) {
        channelStr = `&channel=${config.channel}`;
    }
    // Construct the URL using the provided parameters
    const url = `${scheme}://vrch.ai/viewer?mode=${mode}&server=${server}&ssl=${sslStr}${protocolStr}${channelStr}${filenameStr}${pathStr}${extraParams}${additionalQuery}`;

    // Return the final URL
    return url;
}

/**
 * Helper function to initialize the URL and widget visibility after a delay.
 *
 * @param {Object} node - The current node.
 * @param {Object} showUrlWidget - The widget controlling URL visibility.
 * @param {Object} urlWidget - The URL widget.
 * @param {Function} updateUrl - The updateUrl callback.
 */
export function delayInit(node, showUrlWidget, urlWidget, updateUrl) {
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
export function createOpenWebViewerButton(node, urlWidget, widthWidget, heightWidget) {
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
export function setupWidgetCallback(node, updateUrl, urlWidget, showUrlWidget, widgets, logPrefix) {
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