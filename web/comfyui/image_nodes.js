import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";


function imgToCanvasBase64 (img) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = img.width
    canvas.height = img.height
    ctx.drawImage(img, 0, 0)
    const base64 = canvas.toDataURL('image/png')

    return base64
}

function convertImageToBase64 (img) {
    try {
        const base64 = imgToCanvasBase64(img)
        return base64
    } catch (error) {
        console.error(error)
    }
}

app.registerExtension({
    name: "vrch.ImageTDBackground",

    async nodeCreated(node) {
        // Only process nodes of type "VrchImageTDBackgroundNode"
        if (node.comfyClass === "VrchImageTDBackgroundNode") {
            // Get the relevant widgets
            const channelWidget = node.widgets.find(w => w.name === "channel");
            const enableWidget = node.widgets.find(w => w.name === "background_display");
            const colorWidget = node.widgets.find(w => w.name === "transparent_colour");
            const intervalWidget = node.widgets.find(w => w.name === "refresh_interval_ms");

            const widgets = [channelWidget, enableWidget, colorWidget, intervalWidget];

            // Set callbacks for widget changes to update the background immediately
            widgets.forEach(widget => {
                if (widget) {
                    widget.callback = () => {
                        console.log(`callback:::${widget.name}:::${widget.value}`);
                        reinitBackground();
                        updateBackground()
                    };
                }
            });

            // Function that returns the final image path
            function getImagePath() {
                const channel = channelWidget.value || "1";
                const folder = "td_background";
                const filename = `channel_${channel}.jpg`;
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

            // Main function to update the background image
            function updateBackground() {
                if (!enableWidget.value) {
                    // If disabled, clear the image and trigger redraw
                    if (window._td_bg_img.src) {
                        window._td_bg_img.src = "";
                        lastLoadedPath = null;
                    }
                    return;
                }

                const path = getImagePath();
                if (path !== lastLoadedPath) {
                    lastLoadedPath = path;
                    // Create a new image object to load the image
                    let imgObj = new Image();
                    imgObj.onload = () => {
                        // TODO: check if the base64 -> hashcode (md5?) is the same as the last one
                        // If the image is the same, don't update the background
                        let base64 = convertImageToBase64(imgObj);
                        window._td_bg_img.src = base64;
                    };
                    imgObj.onerror = err => {
                        console.warn("Background image not found or load error:", path);
                    };
                    console.log("Loading background image:", path);
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
                const tdNodes = app.graph._nodes.filter(n => n?.comfyClass === "VrchImageTDBackgroundNode");
                let colorVal = "#000000";
                let enableVal = false;
                if (tdNodes.length) {
                    const n = tdNodes[0];
                    const cWidget = n.widgets.find(w => w.name === "transparent_colour");
                    const eWidget = n.widgets.find(w => w.name === "background_display");
                    enableVal = eWidget ? eWidget.value : false;
                    colorVal = cWidget ? cWidget.value : "#000000";
                }
                // If background display is not enabled, do nothing
                if (!enableVal) return;

                const ctx = this.bgcanvas.getContext("2d");
                ctx.save();

                // Reset transform if viewport is not defined
                if (!this.viewport) {
                    ctx.setTransform(1, 0, 0, 1, 0, 0);
                }

                // Calculate dimensions for "fit" scaling (preserving aspect ratio)
                const canvasWidth = this.bgcanvas.width;
                const canvasHeight = this.bgcanvas.height;
                const imageWidth = window._td_bg_img.width;
                const imageHeight = window._td_bg_img.height;

                // Calculate scale ratio using the smaller ratio (fit inside canvas)
                const scaleRatio = Math.min(canvasWidth / imageWidth, canvasHeight / imageHeight);

                // Calculate drawing dimensions
                const drawWidth = imageWidth * scaleRatio;
                const drawHeight = imageHeight * scaleRatio;

                // Calculate offsets to center the image in the canvas
                const offsetX = (canvasWidth - drawWidth) / 2;
                const offsetY = (canvasHeight - drawHeight) / 2;

                // Draw the image with computed dimensions and position
                ctx.drawImage(window._td_bg_img, offsetX, offsetY, drawWidth, drawHeight);

                // Process the transparent color: set alpha to 0 for matching pixels
                if (colorVal && colorVal.startsWith("#")) {
                    const imgData = ctx.getImageData(0, 0, this.bgcanvas.width, this.bgcanvas.height);
                    const data = imgData.data;

                    // Normalize hex code (convert #abc to #aabbcc)
                    function normalizeHex(hex) {
                        if (hex.length === 4) {
                            return "#" + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
                        }
                        return hex;
                    }
                    const hex = normalizeHex(colorVal);
                    const rT = parseInt(hex.substr(1, 2), 16),
                          gT = parseInt(hex.substr(3, 2), 16),
                          bT = parseInt(hex.substr(5, 2), 16);

                    // Loop through image data and set matching pixel alpha to 0
                    for (let i = 0; i < data.length; i += 4) {
                        if (data[i] === rT && data[i + 1] === gT && data[i + 2] === bT) {
                            data[i + 3] = 0;
                        }
                    }
                    ctx.putImageData(imgData, 0, 0);
                }

                ctx.restore();
            }
        };
    }
});