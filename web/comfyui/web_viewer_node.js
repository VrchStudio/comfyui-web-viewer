import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "vrch.WebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchWebViewerNode") {
            // Find the existing widgets
            const urlWidget = node.widgets.find(w => w.name === "url");
            const widthWidget = node.widgets.find(w => w.name === "window_width");
            const heightWidget = node.widgets.find(w => w.name === "window_height");
            
            // Add the button widget
            const buttonWidget = node.addWidget("button", "Open Web Viewer", null, () => {
                if (urlWidget && urlWidget.value) {
                    const width = widthWidget ? widthWidget.value : 1024;
                    const height = heightWidget ? heightWidget.value : 768;
                    window.open(urlWidget.value, "_blank", `width=${width},height=${height}`);
                } else {
                    console.error("URL widget not found or empty");
                }
            });
            buttonWidget.serialize = false;
        }
    }
});

// This part is optional, but it can be useful for adding more functionality
class WebViewerNode {
    constructor() {
        this.serialize_widgets = true;
    }

    onNodeCreated() {
        // You can add more initialization here if needed
    }
}

// Register the node
app.registerNodeType("WebViewerNode", WebViewerNode);