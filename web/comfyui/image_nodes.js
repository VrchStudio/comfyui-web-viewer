import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";


function imgToCanvasBase64 (img) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
    const base64 = canvas.toDataURL('image/png');
    return base64;
}

function convertImageToBase64 (img) {
    try {
        const base64 = imgToCanvasBase64(img);
        return base64;
    } catch (error) {
        console.error(error);
    }
}

// Helper function to compute SHA-256 hash of a string and return it as hex
async function computeHash(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

// Global flag to enable/disable debug logging
const ENABLE_DEBUG = false;

app.registerExtension({
    name: "vrch.ImagePreviewBackgroundNode",

    async nodeCreated(node) {
        // Only process nodes of type "VrchImagePreviewBackgroundNode"
        if (node.comfyClass === "VrchImagePreviewBackgroundNode") {
            // Get the relevant widgets
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const enableWidget = node.widgets.find(w => w.name === "background_display");
            const intervalWidget = node.widgets.find(w => w.name === "refresh_interval_ms");
            const displayOptionWidget = node.widgets.find(w => w.name === "display_option");
            const batchDisplayWidget = node.widgets.find(w => w.name === "batch_display");
            const batchDisplayIntervalWidget = node.widgets.find(w => w.name === "batch_display_interval_ms");
            const batchImagesSizeWidget = node.widgets.find(w => w.name === "batch_images_size");

            const widgets = [channelWidget, enableWidget, intervalWidget, displayOptionWidget, 
                batchDisplayWidget, batchDisplayIntervalWidget, batchImagesSizeWidget];

            // Global variable for batch index and timer
            let batchIndex = 0;
            let batchTimer = null;

            // Function to set up the batch display timer if enabled
            function setupBatchInterval() {
                if (batchTimer) {
                    clearInterval(batchTimer);
                    batchTimer = null;
                }
                if (batchDisplayWidget && batchDisplayWidget.value) {
                    let ms = parseInt(batchDisplayIntervalWidget.value || 1000, 10);
                    let imagesSize = parseInt(batchImagesSizeWidget.value || 1, 10);
                    // Reset batchIndex to 0 when (re)starting timer
                    batchIndex = 0;
                    batchTimer = setInterval(() => {
                        batchIndex = (batchIndex + 1) % imagesSize;
                        reinitBackground();
                        updateBackground();
                        if (ENABLE_DEBUG) {
                            console.log(`Batch display timer updated index to ${batchIndex}`);
                        }
                    }, ms);
                }
            }

            // Set callbacks for widget changes to update the background immediately
            widgets.forEach(widget => {
                if (widget) {
                    widget.callback = () => {
                        if (ENABLE_DEBUG) {
                            console.log(`callback:::${widget.name}:::${widget.value}`);
                        }
                        // For batch related widgets, update the batch timer
                        if (["batch_display", "batch_display_interval_ms", "batch_images_size"].includes(widget.name)) {
                            setupBatchInterval();
                        }
                        reinitBackground();
                        updateBackground();
                    };
                }
            });

            // Function that returns the final image path, with different logic based on batchDisplayWidget
            function getImagePath() {
                const channel = channelWidget.value || "1";
                const extension = "jpeg";
                const folder = "preview_background";
                let filename;
                if (batchDisplayWidget && batchDisplayWidget.value) {
                    // Use batch display logic: include current batch index formatted为两位数
                    filename = `channel_${channel}_${String(batchIndex).padStart(2, '0')}.${extension}`;
                } else {
                    filename = `channel_${channel}.${extension}`;
                }
                const basePath = window.location.href;
                return `${basePath}view?filename=${filename}&subfolder=${folder}&type=output&rand=${Math.random()}`;
            }

            // Store the last loaded path to avoid reloading if not changed
            let lastLoadedPath = null;

            // Reset lastLoadedPath so the next poll triggers a reload
            function reinitBackground() {
                lastLoadedPath = null;
            }

            // Global interval timer for polling new images
            let pollTimer = null;
            function setupInterval() {
                // Clear old timer if exists
                if (pollTimer) {
                    clearInterval(pollTimer);
                }
                let ms = parseInt(intervalWidget.value || 300, 10);
                pollTimer = setInterval(() => {
                    updateBackground();
                }, ms);
            }

            // Global image object for background
            if (!window._td_bg_img) {
                window._td_bg_img = new Image();
                window._td_bg_img.onload = () => {
                    // Trigger canvas redraw when image is loaded
                    if (app.canvas) {
                        app.canvas.draw(true, true);
                    }
                };
            }

            // Variable to store the last image hash
            let lastImageHash = null;

            // Main function to update the background image
            function updateBackground() {
                if (!enableWidget.value) {
                    // If disabled, clear the image and trigger redraw
                    if (window._td_bg_img.src) {
                        window._td_bg_img.src = "";
                        lastLoadedPath = null;
                        lastImageHash = null;
                    }
                    return;
                }

                const path = getImagePath();
                if (path !== lastLoadedPath) {
                    lastLoadedPath = path;
                    // Create a new image object to load the image
                    let imgObj = new Image();
                    imgObj.onload = async () => {
                        let base64 = convertImageToBase64(imgObj);
                        let newHash = await computeHash(base64);
                        // If the hash is unchanged from the last one, do not update the background
                        if (newHash === lastImageHash) {
                            return;
                        }
                        lastImageHash = newHash;
                        window._td_bg_img.src = base64;
                    };
                    imgObj.onerror = err => {
                        console.warn("Background image not found or load error:", path);
                    };
                    if (ENABLE_DEBUG) {
                        console.log("Loading background image:", path);
                    }
                    imgObj.src = path; // Prevent cache
                }
            }

            // Initialize polling and update
            setupInterval();
            setupBatchInterval();
            updateBackground();
        }

        // Handle new direct UI preview node
        if (node.comfyClass === "VrchImagePreviewBackgroundNewNode") {

            const enableWidget = node.widgets.find(w => w.name === "background_display");
            const displayOptionWidget = node.widgets.find(w => w.name === "display_option");
            const batchDisplayWidget = node.widgets.find(w => w.name === "batch_display");
            const batchDisplayIntervalWidget = node.widgets.find(w => w.name === "batch_display_interval_ms");

            const widgets = [enableWidget, displayOptionWidget, 
                batchDisplayWidget, batchDisplayIntervalWidget];

            widgets.forEach(widget => {
                if (widget) {
                    widget.callback = () => {
                        if (ENABLE_DEBUG) {
                            console.log(`callback:::${widget.name}:::${widget.value}`);
                        }
                        // For batch related widgets, update the batch timer
                        if (["batch_display", "batch_display_interval_ms"].includes(widget.name)) {
                            setupBatchInterval();
                        }
                        // For display option, reinitialize the background
                        if (widget.name === "display_option") {
                            window._td_bg_display_option = widget.value;
                            if (app.canvas) {
                                app.canvas.draw(true, true);
                            }
                        }
                        updateBackground();
                    };
                }
            });

            // Global variable for batch index and timer
            let batchIndex = 0;
            let batchTimer = null;
            // Function to set up the batch display timer if enabled
            function setupBatchInterval() {
                if (batchTimer) {
                    clearInterval(batchTimer);
                    batchTimer = null;
                }
                if (batchDisplayWidget && batchDisplayWidget.value) {
                    let ms = parseInt(batchDisplayIntervalWidget.value || 1000, 10);
                    let imageSize = window._td_bg_imgs.length;                    // Reset batchIndex to 0 when (re)starting timer
                    batchIndex = 0;
                    if (imageSize > 0) {
                        batchTimer = setInterval(() => {
                            batchIndex = (batchIndex + 1) % imageSize;
                            updateBackground();
                            if (ENABLE_DEBUG) {
                                console.log(`Batch display timer updated index to ${batchIndex}`);
                            }
                        }, ms);
                    }
                }
            }

            function updateBackground() {
                if (!enableWidget.value) {
                    // If disabled, clear the image and trigger redraw
                    if (window._td_bg_img.src) {
                        window._td_bg_img.src = "";
                    }
                    // Reset batch index
                    batchIndex = 0;
                    // Clear batch timer
                    if (batchTimer) {
                        clearInterval(batchTimer);
                        batchTimer = null;
                    }
                    return;
                }
                const base64 = window._td_bg_imgs?.[batchIndex];
                if (base64) {
                    window._td_bg_img.src = base64;
                }
            }

            // initialize enabled flag
            window._td_bg_enabled = window._td_bg_enabled ?? false;
            // Global image object for background
            if (!window._td_bg_img) {
                window._td_bg_img = new Image();
                window._td_bg_img.onload = () => {
                    // Trigger canvas redraw when image is loaded
                    if (app.canvas) {
                        app.canvas.draw(true, true);
                    }
                };
            }

            // Initialize polling and update
            setupBatchInterval();
            updateBackground();

            // onExecuted receives images as base64 strings
            node.onExecuted = function(message) {
                window._td_bg_enabled = message.background_display?.[0] ?? false;
                window._td_bg_imgs = message.background_images || [];
                window._td_bg_display_option = message.display_option?.[0] || 'fit';
                updateBackground();
            };
        }
    },

    init() {
        // Overwrite LGraphCanvas drawBackCanvas for the entire app
        const LGraphCanvas = window.LiteGraph.LGraphCanvas;
        const originalDrawBack = LGraphCanvas.prototype.drawBackCanvas;

        LGraphCanvas.prototype.drawBackCanvas = function(...args) {
            // 1) Call original background drawing (grid, etc.)
            originalDrawBack.apply(this, args);

            // 2) If a background image is loaded, draw it with "fit" scaling
            if (window._td_bg_img && window._td_bg_img.width) {
                // Determine enable and display mode from old or new preview node
                const nodes = app.graph._nodes.filter(n => ["VrchImagePreviewBackgroundNode","VrchImagePreviewBackgroundNewNode"].includes(n?.comfyClass));
                let enableVal = false;
                let displayOptionVal = 'fit';
                const oldNode = nodes.find(n => n.comfyClass === 'VrchImagePreviewBackgroundNode');
                const newNode = nodes.find(n => n.comfyClass === 'VrchImagePreviewBackgroundNewNode');

                if (newNode) {
                    enableVal = window._td_bg_enabled;
                    displayOptionVal = window._td_bg_display_option || displayOptionVal;
                } else if (oldNode) {
                    const eW = oldNode.widgets.find(w => w.name === 'background_display');
                    const dW = oldNode.widgets.find(w => w.name === 'display_option');
                    enableVal = eW? eW.value:false;
                    displayOptionVal = dW? dW.value:'fit';
                }

                if (!enableVal) return;

                const ctx = this.bgcanvas.getContext("2d");
                ctx.save();

                // Reset transform if viewport is not defined
                if (!this.viewport) {
                    ctx.setTransform(1, 0, 0, 1, 0, 0);
                }

                let offsetX, offsetY, drawWidth, drawHeight;
                const canvasWidth = this.bgcanvas.width;
                const canvasHeight = this.bgcanvas.height;
                const imageWidth = window._td_bg_img.width;
                const imageHeight = window._td_bg_img.height;
                
                switch (displayOptionVal) {
                    case "original":
                        drawWidth = imageWidth;
                        drawHeight = imageHeight;
                        offsetX = (canvasWidth - imageWidth) / 2;
                        offsetY = (canvasHeight - imageHeight) / 2;
                        break;
                    case "fit": {
                        const scaleRatio = Math.min(canvasWidth / imageWidth, canvasHeight / imageHeight);
                        drawWidth = imageWidth * scaleRatio;
                        drawHeight = imageHeight * scaleRatio;
                        offsetX = (canvasWidth - drawWidth) / 2;
                        offsetY = (canvasHeight - drawHeight) / 2;
                        break;
                    }
                    case "stretch":
                        offsetX = 0;
                        offsetY = 0;
                        drawWidth = canvasWidth;
                        drawHeight = canvasHeight;
                        break;
                    case "crop": {
                        const scaleRatio = Math.max(canvasWidth / imageWidth, canvasHeight / imageHeight);
                        drawWidth = imageWidth * scaleRatio;
                        drawHeight = imageHeight * scaleRatio;
                        offsetX = (canvasWidth - drawWidth) / 2;
                        offsetY = (canvasHeight - drawHeight) / 2;
                        break;
                    }
                    default: {
                        const scaleRatio = Math.min(canvasWidth / imageWidth, canvasHeight / imageHeight);
                        drawWidth = imageWidth * scaleRatio;
                        drawHeight = imageHeight * scaleRatio;
                        offsetX = (canvasWidth - drawWidth) / 2;
                        offsetY = (canvasHeight - drawHeight) / 2;
                    }
                }
                ctx.drawImage(window._td_bg_img, offsetX, offsetY, drawWidth, drawHeight);
                ctx.restore();
            }
        };
    }
});