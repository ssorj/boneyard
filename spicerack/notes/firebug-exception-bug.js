var scratchy;

(function() {
    scratchy = new Scratchy();

    function Scratchy() {
        this.x = new Object();

        this.itchy = function(callback, interval) {
            var x = this.x;

            setTimeout(show, 1000);

            function show() {
                try {
                    callback();
                } catch (e) {
                    throw e;
                }
            }
        }
    }
}());
