import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

/**
 * Create a non‑clickable circular indicator element with a label.
 * @param {number} id    – the indicator number to display
 * @returns {HTMLElement}
 */
function createTriggerToggleIndicatorElement(id = 1) {
    const indicator = document.createElement("div");
    indicator.textContent = String(id);
    indicator.classList.add("vrch-trigger-indicator", "off");
    indicator.style.pointerEvents = "none";
    return indicator;
}

/**
 * Create multiple indicators and append them into a container.
 * @param {HTMLElement} container – parent element to hold indicators
 * @param {number} count          – number of indicators to create
 * @returns {HTMLElement[]}
 */
function createTriggerToggleIndicators(container, count = 1) {
    const indicators = [];
    for (let i = 1; i <= count; i++) {
        const elt = createTriggerToggleIndicatorElement(i);
        container.appendChild(elt);
        indicators.push(elt);
    }
    return indicators;
}

app.registerExtension({
    name: "vrch.TriggerToggleNodes",
    async nodeCreated(node) {
        if (node.comfyClass === "VrchTriggerToggleNode") {
            // create a container to hold all indicators
            const container = document.createElement("div");
            container.classList.add("vrch-trigger-indicators-container");
            node.addDOMWidget("indicator_container", "Indicators", container);

            // initialize indicators (default count = 1, can be extended)
            const stateIndicators = createTriggerToggleIndicators(container, 1);

            node.onExecuted = function(message) {
                const states = message.current_state;      // array of booleans
                const ids    = message.ui?.indicator_id ?? [];

                states.forEach((state, index) => {
                    const indicator = stateIndicators[index];
                    const id        = ids[index] ?? (index + 1);
                    indicator.textContent = String(id);
                    indicator.classList.toggle("on",  !!state);
                    indicator.classList.toggle("off", !state);
                });
            };
        }

        if (node.comfyClass === "VrchTriggerToggleX4Node") {
            // create a container to hold all indicators
            const container = document.createElement("div");
            container.classList.add("vrch-trigger-indicators-container");
            node.addDOMWidget("indicator_container", "Indicators", container);

            // initialize indicators (default count = 4)
            const stateIndicators = createTriggerToggleIndicators(container, 4);

            node.onExecuted = function(message) {
                const states = message.current_state;      // array of booleans
                const ids    = message.ui?.indicator_id ?? [];

                states.forEach((state, index) => {
                    const indicator = stateIndicators[index];
                    const id        = ids[index] ?? (index + 1);
                    indicator.textContent = String(id);
                    indicator.classList.toggle("on",  !!state);
                    indicator.classList.toggle("off", !state);
                });
            };
        }

        if (node.comfyClass === "VrchTriggerToggleX8Node") {
            // create a container to hold all indicators
            const container = document.createElement("div");
            container.classList.add("vrch-trigger-indicators-container");
            node.addDOMWidget("indicator_container", "Indicators", container);

            // initialize indicators (default count = 8)
            const stateIndicators = createTriggerToggleIndicators(container, 8);

            node.onExecuted = function(message) {
                const states = message.current_state;      // array of booleans
                const ids    = message.ui?.indicator_id ?? [];

                states.forEach((state, index) => {
                    const indicator = stateIndicators[index];
                    const id        = ids[index] ?? (index + 1);
                    indicator.textContent = String(id);
                    indicator.classList.toggle("on",  !!state);
                    indicator.classList.toggle("off", !state);
                });
            };
        }
    }
});

// inject stylesheet for the container + circular indicators
const style = document.createElement("style");
style.textContent = `
.vrch-trigger-indicators-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center; 
    align-items: center;
    gap: 8px;
    padding: 4px;
}
.vrch-trigger-indicator {
    width: 32px;              
    height: 32px;              
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
    transition: background-color 0.3s;
    user-select: none;
}
.vrch-trigger-indicator.off {
    background-color: #ccc;
    color: #333;
}
.vrch-trigger-indicator.on {
    background-color: #4CAF50;
    color: #fff;
}`;
document.head.appendChild(style);