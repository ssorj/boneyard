function $(name) {
    return document.getElementById(name);
}

function PennyChart(canvas) {
    this.canvas = canvas;
    this.context = this.canvas.getContext("2d");

    this.interestRate = 0.10;
    this.initialPrincipal = 1000;
    this.years = 30;

    this.data = null;
    this.maxSavings = null;

    this.init = function() {
        return;
    }

    this.draw = function() {
        this.generateData();

        this.drawFrame();
        this.drawContent();
    }

    this.drawFrame = function() {
        var ctx = this.context;
        var step = this.canvas.width / this.data.length;

        ctx.save();

        ctx.fillStyle = "#eee";

        for (var i = 0; i < this.data.length; i = i + 10) {
            var x = step * i;

            ctx.fillRect(x, 0, x + step * 5, this.canvas.height);
        }

        ctx.restore()
        ctx.save()

        ctx.beginPath();

        for (var i = 0; i < this.data.length; i++) {
            var x = step * i;

            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
        }

        ctx.closePath();

        ctx.strokeStyle = "rgba(127, 127, 127, 127)"
        ctx.lineWidth = 0.25;
        ctx.stroke();

        ctx.restore();
        ctx.save();

        //ctx.beginPath();
        //ctx.rect(0, 0, this.canvas.width, this.canvas.height);

        //ctx.strokeStyle = "gray";
        //ctx.stroke();

        ctx.restore();
    }

    this.drawContent = function() {
        var ctx = this.context;

        ctx.save();

        ctx.translate(0, this.canvas.height);

        ctx.beginPath();

        var step = this.canvas.width / this.data.length;

        for (var i = 0; i < this.data.length; i++) {
            record = this.data[i];

            y = (record.savings / this.maxSavings) * this.canvas.height * -0.95

            ctx.lineTo(step * (i + 1), y);
        }

        ctx.strokeStyle = "blue";
        ctx.lineWidth = "2";
        ctx.stroke();

        ctx.restore();
    };

    this.redraw = function() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.draw();
    };

    this.generateData = function() {
        var data = new Array();
        var savings = this.initialPrincipal;

        for (var i = 0; i < this.years; i++) {
            savings = savings + savings * this.interestRate * Math.random();

            if (savings > this.maxSavings) {
                this.maxSavings = savings
            }

            record = new Object();
            record.year = i;
            record.savings = savings;

            data[i] = record;
        }

        this.data = data;
    }
}
