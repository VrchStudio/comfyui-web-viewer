// Enable debug logging
export const ENABLE_DEBUG = false;

/**
 * Helper function to trigger a new queue generation.
 * This function finds the queue button and clicks it to start a new generation.
 */
export function triggerNewGeneration() {
    const buttonContainer = document.querySelector('div[data-testid="queue-button"]');
    if (buttonContainer) {
        const queueButton = buttonContainer.querySelector('button[data-pc-name="pcbutton"]');
        if (queueButton) {
            queueButton.click();
            console.log('New queue generation triggered.');
        } else {
            console.warn("Queue button not found inside container.");
        }
    } else {
        console.warn("Queue button container not found.");
    }
}

// Helper functions to hide and show widgets
export function hideWidget(node, widget) {
    if (!widget) return;
    if (widget.type === "hidden" || widget.hidden) return;

    widget.origType ??= widget.type;
    widget.origComputeSize ??= widget.computeSize;
    widget.origHidden = widget.hidden ?? false;

    widget.type = "hidden";
    widget.hidden = true;
    widget.computeSize = widget.computeSize || (() => [0, 0]);

    if (widget.element) {
        widget.element.style.display = "none";
    }

    node?.setDirtyCanvas?.(true, true);
}

export function showWidget(node, widget) {
    if (!widget) return;

    widget.type = widget.origType ?? widget.type;
    widget.computeSize = widget.origComputeSize ?? widget.computeSize;
    widget.hidden = widget.origHidden ?? false;

    if (widget.element) {
        widget.element.style.removeProperty("display");
    }

    node?.setDirtyCanvas?.(true, true);
}

/**
 * Enumerate available microphone input devices.
 *
 * @param {Object} [options]
 * @param {boolean} [options.requestAccess=true] - Whether to request `getUserMedia` before enumerating.
 * @param {string} [options.logPrefix="[Microphone]"] - Prefix for debug logging.
 * @param {boolean} [options.debugEnabled=false] - Enable console logs when true.
 * @returns {Promise<MediaDeviceInfo[]>} Resolves with the list of audioinput devices.
 */
export async function listMicrophoneDevices(options = {}) {
    const { requestAccess = true, logPrefix = "[Microphone]", debugEnabled = false } = options;
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            throw new Error("MediaDevices API not supported in this browser");
        }

        if (requestAccess) {
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
            } catch (permissionError) {
                if (debugEnabled) {
                    console.warn(`${logPrefix} Permission request failed:`, permissionError);
                }
            }
        }

        const mediaDevices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = mediaDevices.filter(device => device.kind === "audioinput");

        if (debugEnabled) {
            console.log(`${logPrefix} Enumerated ${audioInputs.length} microphone device(s).`);
        }

        return audioInputs;
    } catch (error) {
        if (debugEnabled) {
            console.error(`${logPrefix} Failed to enumerate microphones:`, error);
        }
        throw error;
    }
}

/**
 * Populate a <select> element with microphone device options.
 *
 * @param {HTMLSelectElement} selectEl - The select element to populate.
 * @param {MediaDeviceInfo[]} devices - List of microphone devices.
 * @param {Object} [options]
 * @param {string} [options.placeholder="Select Microphone..."] - Placeholder option label.
 * @param {string} [options.previousValue] - Previously selected deviceId to restore if available.
 * @returns {{selection: string, restored: boolean}} Selected value and whether it was restored.
 */
export function populateMicrophoneSelect(selectEl, devices, options = {}) {
    if (!selectEl) {
        return { selection: "", restored: false };
    }

    const { placeholder = "Select Microphone...", previousValue } = options;
    const priorValue = previousValue !== undefined ? previousValue : selectEl.value;

    while (selectEl.options.length > 0) {
        selectEl.remove(0);
    }

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = placeholder;
    selectEl.appendChild(defaultOption);

    let restored = false;
    devices.forEach(device => {
        const option = document.createElement("option");
        option.value = device.deviceId;
        option.textContent = device.label || `Microphone (${device.deviceId.slice(0, 5)}...)`;
        selectEl.appendChild(option);
        if (priorValue && device.deviceId === priorValue) {
            restored = true;
        }
    });

    if (restored) {
        selectEl.value = priorValue;
    } else {
        selectEl.value = "";
    }

    return {
        selection: selectEl.value,
        restored,
    };
}

/**
 * Create reusable microphone controls UI (select + reload + mute + status).
 *
 * @param {Object} options
 * @param {boolean} [options.debug=false] - Enable console logging.
 * @param {Function} [options.onDeviceChange] - Called with deviceId when selection changes.
 * @param {Function} [options.onMuteChange] - Called with boolean when mute toggles.
 * @param {Function} [options.filterDevices] - Optional filter returning filtered list.
 * @returns {Object} { container, selectEl, reloadButton, muteButton, statusLabel, refreshDevices, setMuted, setStatus, getSelection, setSelection }
 */
export function createMicrophoneControls(options = {}) {
    const {
        debug = false,
        onDeviceChange,
        onMuteChange,
        filterDevices,
    } = options;

    const log = (...args) => {
        if (debug) {
            console.log("[MicrophoneControls]", ...args);
        }
    };

    let devicesCache = [];
    let isMuted = false;

    const container = document.createElement("div");
    container.classList.add("mic-controls-container");

    const deviceRow = document.createElement("div");
    deviceRow.classList.add("mic-device-row");
    const selectEl = document.createElement("select");
    selectEl.classList.add("mic-device-select");
    populateMicrophoneSelect(selectEl, []);
    deviceRow.appendChild(selectEl);

    const buttonRow = document.createElement("div");
    buttonRow.classList.add("mic-button-row");

    const reloadButton = document.createElement("button");
    reloadButton.textContent = "Reload";
    reloadButton.classList.add("vrch-mic-reload-button");

    const muteButton = document.createElement("button");
    muteButton.classList.add("vrch-mic-mute-button");
    const applyMuteStyle = () => {
        muteButton.innerHTML = isMuted
            ? '<span class="vrch-mic-speaker-icon">🔇</span>'
            : '<span class="vrch-mic-speaker-icon">🔊</span>';
        muteButton.style.backgroundColor = isMuted ? "#9e6a6a" : "#4f9cff";
    };
    applyMuteStyle();

    buttonRow.appendChild(reloadButton);
    buttonRow.appendChild(muteButton);

    const statusContainer = document.createElement("div");
    statusContainer.classList.add("vrch-mic-status-container");
    const statusLabel = document.createElement("div");
    statusLabel.classList.add("vrch-mic-status-label");
    statusLabel.textContent = "Status: Ready";
    statusContainer.appendChild(statusLabel);

    container.appendChild(deviceRow);
    container.appendChild(buttonRow);
    container.appendChild(statusContainer);

    const setStatus = (status) => {
        statusLabel.textContent = `Status: ${status}`;
    };

    const updateSelection = (deviceId) => {
        if (!selectEl) return;
        selectEl.value = deviceId || "";
        if (onDeviceChange) {
            onDeviceChange(selectEl.value);
        }
    };

    const setMuted = (mute) => {
        isMuted = !!mute;
        applyMuteStyle();
        if (onMuteChange) {
            onMuteChange(isMuted);
        }
    };

    const getSelection = () => selectEl.value;

    const setSelection = (deviceId) => {
        const existing = devicesCache.find(device => device.deviceId === deviceId);
        if (existing) {
            selectEl.value = deviceId;
        }
    };

    const refreshDevices = async ({ requestAccess = false, logPrefix = "[MicrophoneControls]" } = {}) => {
        try {
            const deviceList = await listMicrophoneDevices({
                requestAccess,
                logPrefix,
                debugEnabled: debug,
            });
            const filtered = filterDevices ? deviceList.filter(filterDevices) : deviceList;
            devicesCache = filtered;
            const prior = selectEl.value;
            const { selection } = populateMicrophoneSelect(selectEl, devicesCache, {
                previousValue: prior,
            });
            if (selection !== prior && onDeviceChange) {
                onDeviceChange(selection);
            }
            log(`Refreshed devices: ${devicesCache.length}`);
            return devicesCache;
        } catch (error) {
            log("Failed to refresh devices", error);
            throw error;
        }
    };

    selectEl.addEventListener("change", () => {
        if (onDeviceChange) {
            onDeviceChange(selectEl.value);
        }
    });

    muteButton.addEventListener("click", () => {
        setMuted(!isMuted);
    });

    return {
        container,
        selectEl,
        reloadButton,
        muteButton,
        statusLabel,
        refreshDevices,
        setMuted,
        getMuted: () => isMuted,
        setStatus,
        getSelection,
        setSelection,
        devices: () => devicesCache.slice(),
    };
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
    // Check if dev mode is enabled
    const devMode = config.devMode ? config.devMode.value : false;
    const viewerPath = devMode ? "dev/viewer" : "viewer";
    
    // Construct the URL using the provided parameters
    const url = `${scheme}://vrch.ai/${viewerPath}?mode=${mode}&server=${server}&ssl=${sslStr}${protocolStr}${channelStr}${filenameStr}${pathStr}${extraParams}${additionalQuery}`;

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
        // Handle URL widget visibility
        if (showUrlWidget) {
            showUrlWidget.value ? showWidget(node, urlWidget) : hideWidget(node, urlWidget);
        }
        // Update URL
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
    // Create a container with fixed height for the button
    const container = document.createElement("div");
    container.classList.add("vrch-button-container");
    
    const button = document.createElement("button");
    button.textContent = "Open Web Viewer";
    button.classList.add("vrch-big-button");
    button.onclick = () => {
        if (urlWidget && urlWidget.value) {
            const width = widthWidget ? widthWidget.value : 1280;
            const height = heightWidget ? heightWidget.value : 960;
            window.open(urlWidget.value, "_blank", `width=${width},height=${height}`);
        } else {
            console.error("URL widget not found or empty");
        }
    };
    
    // Add button to container
    container.appendChild(button);
    
    // Add the container (with button inside) as widget
    const widget = node.addDOMWidget("button_widget", "Open Web Viewer", container);
    
    // Override the computeSize method to force correct sizing
    widget.computeSize = function(width) {
        return [width, 60]; // Force height to be 48px
    };
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
