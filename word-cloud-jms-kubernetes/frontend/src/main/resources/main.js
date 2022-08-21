"use strict";

const rhea = require("rhea");

class Word {
    constructor(app, text) {
        this.app = app;
        this.text = text;
        this.x = 0;
        this.y = 0;
        this.height = 0;
        this.width = 0;
        this.count = 1;

        this.calculateDimensions();

        this.app.words.set(this.text, this);
    }

    calculateDimensions() {
        let context = this.app.canvas.getContext("2d");

        this.height = (12 + 4 * this.count) * 2;
        context.font = `${this.height}px 'Source Sans Pro'`;
        this.width = context.measureText(this.text).width;
    }

    randomizePosition() {
        this.x = Math.random() * this.app.canvas.width;
        this.y = Math.random() * this.app.canvas.height;
    }

    overlapsWithAnyOtherWord() {
        for (let other of this.app.words.values()) {
            if (other === this) continue;

            if (this.overlaps(other)) {
                return true;
            }
        }

        return false;
    }

    overlaps(other) {
        let l1x = this.x - this.width / 2;
        let l1y = this.y - this.height / 2;

        let r1x = this.x + this.width / 2;
        let r1y = this.y + this.width / 2;

        let l2x = other.x - other.width / 2;
        let l2y = other.y - other.height / 2;

        let r2x = other.x + other.width / 2;
        let r2y = other.y + other.width / 2;

        if (l1x > r2x || l2x > r1x) return false;
        if (l1y > r2y || l2y > r1y) return false;

        return true;
    }
}

class WordsInTheCloud {
    constructor() {
        this.words = new Map();

        this.colors = [
            "#d32f2f", "#c2185b", "#7b1fa2", "#512da8",
            "#3949ab", "#039be5", "#00acc1", "#00897b",
            "#43a047", "#7cb342", "#f4511e", "#6d4c41",
        ];

        this.canvas = document.getElementById("canvas");
        this.canvas.width = 640 * 2;
        this.canvas.height = 480 * 2;

        window.addEventListener("load", (event) => {
            this.render();

            const container = rhea.create_container();

            container.on("message", (event) => {
                this.addWord(event.message.body);
                this.render();
            });

            const url = "ws://localhost:5672";
            const ws = rhea.websocket_connect(WebSocket);
            const conn = container.connect({connection_details: ws(url, ['binary', 'AMQPWSB10', 'amqp']), reconnect: true});

            conn.open_receiver("example/processed-words");
        });
    }

    addWord(text) {
        let word = this.words.get(text);

        if (word) {
            word.count += 1;
            word.calculateDimensions();
            return;
        }

        word = new Word(this, text);

        for (let i = 0; i < 1000; i++) {
            word.randomizePosition();

            if (!word.overlapsWithAnyOtherWord()) {
                break;
            }
        }
    }

    render() {
        const context = this.canvas.getContext("2d");

        context.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (let word of this.words.values()) {
            context.font = `${word.height}px 'Source Sans Pro'`;
            context.textBaseline = "middle";
            context.textAlign = "center";
            context.fillStyle = this.colors[Math.floor(word.x % this.colors.length)];
            context.fillText(word.text, word.x, word.y);
        }
    }
}
