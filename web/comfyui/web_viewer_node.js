import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "vrch.WebViewer",
    async nodeCreated(node) {
        if (node.comfyClass === "WebViewerNode") {
            // Find the existing url widget
            const urlWidget = node.widgets.find(w => w.name === "url");
            
            // Add the button widget
            const buttonWidget = node.addWidget("button", "Open Web Viewer", null, () => {
                if (urlWidget && urlWidget.value) {
                    window.open(urlWidget.value, "_blank", "width=1024,height=768");
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