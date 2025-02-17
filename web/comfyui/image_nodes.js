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
const ENABLE_DEBUG = true;

app.registerExtension({
    name: "vrch.ImageTDBackground",

    async nodeCreated(node) {
        // Only process nodes of type "VrchImagePreviewBackgroundNode"
        if (node.comfyClass === "VrchImagePreviewBackgroundNode") {
            // Get the relevant widgets
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const enableWidget = node.widgets.find(w => w.name === "background_display");
            const intervalWidget = node.widgets.find(w => w.name === "refresh_interval_ms");
            const displayOptionWidget = node.widgets.find(w => w.name === "display_option");

            const widgets = [channelWidget, enableWidget, intervalWidget, displayOptionWidget];

            // Set callbacks for widget changes to update the background immediately
            widgets.forEach(widget => {
                if (widget) {
                    widget.callback = () => {
                        console.log(`callback:::${widget.name}:::${widget.value}`);
                        reinitBackground();
                        updateBackground();
                    };
                }
            });

            // Function that returns the final image path
            function getImagePath() {
                const channel = channelWidget.value || "1";
                const extension = "jpeg";
                const folder = "preview_background";
                const filename = `channel_${channel}.${extension}`;
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

            // Initialize polling and update immediately
            setupInterval();
            updateBackground();
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
                // Retrieve the node to read widget values
                const tdNodes = app.graph._nodes.filter(n => n?.comfyClass === "VrchImagePreviewBackgroundNode");
                let enableVal = false;
                let displayOptionVal = "fit";
                if (tdNodes.length) {
                    const n = tdNodes[0];
                    const eWidget = n.widgets.find(w => w.name === "background_display");
                    const displayOptionWidget = n.widgets.find(w => w.name === "display_option");
                    enableVal = eWidget ? eWidget.value : false;
                    displayOptionVal = displayOptionWidget ? displayOptionWidget.value : "fit";
                }

                // If background display is not enabled, do nothing
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