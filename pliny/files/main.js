function _showElement(id) {
    var elem = document.getElementById(id);
    elem.style.display = "block";
}

function _hideElement(id) {
    var elem = document.getElementById(id);
    elem.style.display = "none";
}

function _playDemoProvisioningLog() {
    var elem = document.getElementById("provisioning-log");

    elem.textContent += "Starting\n";

    var func = function() {
        elem.textContent += "Reticulating splines\n";
    };

    setTimeout(func, 1000);

    var func = function() {
        elem.textContent += "Flibberty jibbits!\n";
    };

    setTimeout(func, 2000);

    var func = function() {
        elem.textContent += "Done\n";
        _enableElement("continue-button");
    };

    setTimeout(func, 3000);
}

function _enableElement(id) {
    var elem = document.getElementById(id);
    elem.disabled = false;
}
