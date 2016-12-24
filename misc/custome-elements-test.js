"use strict";

class TestButton extends HTMLButtonElement {
    constructor() {
        super();

        this.addEventListener("click", () => {
            alert("Clicked!");
        });
    }

    connectedCallback() {
        this.textContent = "Ohh";
    }
}

class TestElement extends HTMLElement {
    constructor() {
        super();

        this.textContent = "Yeah!";
     }
}

window.customElements.define("test-button", TestButton, { extends: "button" });
window.customElements.define("test-element", TestElement);
