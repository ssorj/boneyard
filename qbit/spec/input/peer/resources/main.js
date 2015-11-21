function addVisibilityHandlers() {
    var nodes = document.getElementsByTagName("a");

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];

        value = node.getAttribute("class");

        if (value == "visibility-toggle") {
            node.onclick = toggleVisibility;
        }
    }
}

function toggleVisibility(event) { 
    var controlElem = event.target;
    var targetId = controlElem.getAttribute("target-id");
    var targetElem = document.getElementById(targetId);

    if (targetElem.style.display == "block") {
        hide(controlElem, targetElem);
    } else {
        show(controlElem, targetElem);
    }
}

function show(controlElem, targetElem) {
    controlElem.innerHTML = "&#171;"
    targetElem.style.display = "block";
}

function hide(controlElem, targetElem) {
    controlElem.innerHTML = "&#187;"
    targetElem.style.display = "none";
}

function showAll() {
    var nodes = document.getElementsByTagName("a");

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        
        value = node.getAttribute("class");

        if (value == "visibility-toggle") {
            var controlElem = node;
            var targetId = controlElem.getAttribute("target-id");
            var targetElem = document.getElementById(targetId);

            show(controlElem, targetElem);
        }
    }
}

function hideAll() {
    var nodes = document.getElementsByTagName("a");

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];

        value = node.getAttribute("class");

        if (value == "visibility-toggle") {
            var controlElem = node;
            var targetId = controlElem.getAttribute("target-id");
            var targetElem = document.getElementById(targetId);

            hide(controlElem, targetElem);
        }
    }
}

function replaceElemText(parent, text) {
    var nodes = parent.childNodes;

    for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];

        if (node.nodeType == Node.ELEMENT_NODE) {
            node.innerHTML = text;
            break;
        }
    }
}

window.onload = addVisibilityHandlers
