var wooly;

(function() {
    wooly = new Wooly();

    function assert() {
        for (var i = 0; i < arguments.length; i++) {
            if (!arguments[i]) {
                throw new Error("Assertion failure in " +
                                arguments.callee.caller.prototype);
            }
        }
    }

    function log() {
        try {
            wooly.console.log.apply(wooly.console, arguments);
        } catch (e) {
        }
    }

    function dir() {
        try {
            wooly.console.dir.apply(wooly.console, arguments);
        } catch (e) {
        }
    }

    function translate(node, parent) {
        //log("node", node.nodeType, node, "parent", parent);

        var first = node.firstChild;
        var name = node.nodeName;

        if (first && first.nodeType == 3 && parent) {
            parent[name] = first.nodeValue;

            return null;
        }

        var object = new Object();
        var attrs = node.attributes;

        if (parent) {
            var keyattr = null;

            if (attrs) {
                keyattr = attrs.getNamedItem("id");

                if (keyattr == null) {
                    keyattr = attrs.getNamedItem("key");
                }

                if (keyattr == null) {
                    keyattr = attrs.getNamedItem("name");
                }

                if (keyattr) {
                    var key = keyattr.nodeValue;
                    var extant = parent[name];

                    if (extant == null) {
                        extant = new Object();
                        parent[name] = extant;
                    }

                    extant[key] = object;
                }
            }

            if (keyattr == null) {
                var extant = parent[name];

                if (extant == null) {
                    parent[name] = object;
                } else {
                    var array;

                    if (extant instanceof Array) {
                        array = extant;
                    } else {
                        array = new Array();
                        array.push(extant);

                        parent[name] = array;
                    }

                    array.push(object);
                }
            }
        }

        var attr;

        for (var i = 0; i < attrs.length; i++) {
            attr = attrs[i];
            object[attr.nodeName] = attr.nodeValue;
        }

        var childs = node.childNodes;

        for (var i = 0; i < childs.length; i++) {
            translate(childs[i], object);
        }

        return object;
    }

    function update(elem, elems, object) {
        //log("update", "elem", elem, "elems", elems, "object", object);

        if (typeof(object) == "string") {
            if (elem.firstChild.nodeType == 3) {
                elem.firstChild.data = object;
            }
        } else if (object instanceof Array) {
            for (var i = 0; i < object.length; i++) {
                update(elems[i], elems, object[i]);
            }
        } else {
            for (var child in object) {
                var elems = elem.getElementsByTagName(child);
                update(elems[0], elems, object[child]);
            }
        }
    }

    function descendant(elem, path) {
        var names = path.split(".");
        var node = elem;

        for (var i = 0; i < names.length; i++) {
            var elems = elem.getElementsByTagName(names[i]);

            if (elems.length) {
                node = elems[0];
            } else {
                break;
            }
        }

        return node;
    }

    function findexpr(found, limit, node, expr) {
        var result = document.evaluate
            (expr, node, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);

        var node = result.iterateNext();

        for (var i = 0; node != null && i < limit; i++) {
            found.push(node);
            node = result.iterateNext();
        }

        return found;
    }

    function find(found, limit,
                  node, nodeType, nodeName,
                  attr, attrValue) {
        //log("find", found, limit, node, nodeType, nodeName, attr, attrValue);

        /*
        assert(found);
        assert(found instanceof Array);
        assert(node);
        assert(nodeType);
        */

        var children = node.childNodes;

        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            var candidate = child;

            if (child.nodeType != nodeType) {
                candidate = null;
            } else if (nodeName != null && child.nodeName.toLowerCase() != nodeName) {
                candidate = null;
            } else if (attr != null && child.nodeType == 1) {
                var value = child.getAttribute(attr);

                if (!value) {
                    candidate = null;
                } else if (attrValue != null && value != attrValue) {
                    candidate = null;
                }
            }

            if (candidate) {
                found.push(candidate);

                if (found.length == limit) {
                    return;
                }
            } else if (child.nodeType == 1) {
                find(found, limit, child, nodeType, nodeName, attr, attrValue);
            }
        }
    }

    var damnyouie = /msie/i.test(navigator.userAgent) && !/opera/i.test(navigator.userAgent);

    function replaceNode(newNode, oldNode) {
        if (document.all) {
            oldNode.outerHTML = newNode.xml;
        } else {
            var node = copyNode(newNode, true);
            oldNode.parentNode.replaceChild(node, oldNode);
        }
    }

    function xmlGetElementById(parent, id) {
        var child = parent.firstChild;
        // loop through siblings first
        while (child) {
            if (child.nodeType == 1) {
                if (child.getAttribute("id") == id)
                    return child;
            }
            child = child.nextSibling;
        }
        // then do a deep look at relatives
        var child = parent.firstChild;
        while (child) {
            if (child.nodeType == 1) {
                var progeny = xmlGetElementById(child, id);
                if (progeny)
                    return progeny;
            }
            child = child.nextSibling;
        }
        return null;
    }

    function copyNode(node) {
        switch (node.nodeType) {
            case 1:
                return copyElement(node);
            case 3:
            case 4:
                return document.createTextNode(node.nodeValue);
            default:
                return null;
        }
    }

    function copyElement(node) {
        var newElem = document.createElement(node.nodeName);

        // XXX consider using hasAttributes here
        if (node.attributes && node.attributes.length > 0) {
            var len = node.attributes.length;

            for (var i = 0; i < len; i++) {
                var attr = node.getAttribute(node.attributes[i].nodeName);
                newElem.setAttribute(node.attributes[i].nodeName, attr);
            }
        }

        var child = node.firstChild;

        while (child) {
            var newChild = copyNode(child);

            if (newChild) {
                newElem.appendChild(newChild);
            }

            child = child.nextSibling;
        }

        return newElem;
    }

    function executeJS(node) {
        var child = node.firstChild;
        while (child) {
            if (child.nodeType == 1 && child.nodeName == "script") {
                var oScript = document.createElement("script");
                if(child.textContent) {
                	oScript.text = child.textContent;
                } else {
                	oScript.text = child.text;  // for IE
                }                
                document.getElementsByTagName("head").item(0).appendChild(oScript);
            }
            child = child.nextSibling;
        }
    }

    function getNewRequest() {
        var request;

        if (window.XMLHttpRequest) {
            request = new XMLHttpRequest();
        } else {
            if (window.ActiveXObject) {
                try {
                    request = new ActiveXObject("Microsoft.XMLHTTP");
                } catch (e) {
                    request = new ActiveXObject("Msxml2.XMLHTTP");
                }
            }
        }

        return request;
    }


    function Wooly() {
        if (window.console) {
            this.console = window.console;
        }

        this.assert = assert;
        this.log = log;
        this.dir = dir;

        this.updaterIDs = [];
        this.session = new Session();

        this.getNewRequest = getNewRequest

        // Updates

        this.pageUpdateListeners = new Array();

        this.addPageUpdateListener = function(listener) {
            this.pageUpdateListeners.push(listener);
        }

        this.updatePage = function(xml) {
        	var success = true;
        	var had_updates = false;
        	if(xml == null) {
        		success = false;
        	} else {
	            var child = xml.documentElement.firstChild;
	            while (child) {
	                if (child.nodeType == 1 && child.nodeName == "widget") {
	                	had_updates = true;
	                    var id = child.getAttribute("id");
	                    var oldElem = document.getElementById(id);
	
	                    if (oldElem) {
	                        var newElem = child.firstChild;
	
	                        while (newElem && newElem.nodeType != 1) {
	                            newElem = newElem.nextSibling;
	                        }
	
	                        if (newElem) {
	                            // only update a sub-block of html
	
	                            var updateId = newElem.getAttribute("update");
	
	                            if (updateId) {
	                                oldElem = document.getElementById(updateId);
	                                newElem = xmlGetElementById(newElem, updateId);
	                            }
	
	                            replaceNode(newElem, oldElem);
	                        } else {
	                            oldElem.parentNode.removeChild(oldElem);
	                        }
	                    }  // end if (oldElem)
	                    // find and execute any javascript
	                    executeJS(child);
	                }
	
	                child = child.nextSibling;
	            }
	            
	            if(!had_updates) {
	            	// if there were no updates in the returned XML, 
	            	// maybe it was because our session timed-out and
	            	// we need to be sent to the login page
	            	child = xml.documentElement.firstChild;
	            	while(child) {
	            		if(child.nodeType == 1) {
	            			if(child.nodeName == "body") {
	            				body = child.firstChild;
	            				while(body) {
	            					if(body.nodeType == 1) {
	            						if(body.getAttribute("id") == "loginpage_token") {
	            							document.location.href = '/login.html';
	            						}
	            					}
	            					body = body.nextSibling;
	            				}
	            			}
	            		}
	            		child = child.nextSibling;
	            	}
	            }
	            
        	}
        	
            var len = wooly.pageUpdateListeners.length;

            for (var i = 0; i < len; i++) {
                wooly.pageUpdateListeners[i](success);
            }        	
        }

        this.backgroundUpdate = function(url, callback, passback) {
            var req = this.getNewRequest();

            req.open("get", url, true);
            req.onreadystatechange = update;
            req.send(null);

            function update() {
                try {
                    if (req.readyState == 4 && req.status == 200) {
                        var data = wooly.doc(req.responseXML);
                        var obj = data.objectify();
                        callback(obj, passback);
                    }
                } catch (e) {
                    log(e);
                    throw e;
                }
            }
        }

        this.intervalUpdateInfo = {
            timerId: 0,
            url: "",
            callback: "",
            interval: 0,
            passback: null
        };

        this.setIntervalUpdate = function(url, callback, interval, passback, astext) {
            var req = this.getNewRequest();

            function fetch() {
                // don't preempt a pending request
                if (req.readyState == 0 || req.readyState == 4) {
                    req.open("get", url, true);
                    req.onreadystatechange = update;
                    req.send(null);
                }
            }

            if (interval > 0) {
                var id = window.setInterval(fetch, interval);
                this.updaterIDs.push(id);

                // save the arguments in case we need to modify the url
                // and restart the interval
                this.intervalUpdateInfo.timerId = id;
                this.intervalUpdateInfo.url = url;
                this.intervalUpdateInfo.callback = callback;
                this.intervalUpdateInfo.interval = interval;
                this.intervalUpdateInfo.passback = passback;
            } else { 
                fetch(); 
            }

            function update() {
                try {
                    // The location header provides away to recover from a
                    // failed update
                    var checkForRedirect = req.getResponseHeader("Location")
                    if (checkForRedirect){
                        if (checkForRedirect == "reload") {
                            location.reload()
                        } else {
                            location.href = checkForRedirect
                        }
                    } else if (req.readyState == 4 && req.status == 200) {
                        if (astext == true)
                            callback(req.responseText, passback);
                        else
                            callback(req.responseXML, passback);
                    } else {
                        if(req.readyState == 4) {
                    	    //readyState == 4 means that the call is done...a non-200 status means that something bad happened, call the callback with null for the XML
                            callback(null, passback);
                        }                    	
                    }
                } catch (e) {
                    log(e);
                    // XXX might want to retry for a bit before we do
                    // this
                    window.clearInterval(id);
                    throw e;
                }
            }
        }

        this.clearUpdates = function() {
            for (var i = 0; i < this.updaterIDs.length; i++) {
                window.clearInterval(this.updaterIDs[i])
            }
        }

        this.cancelIntervalUpdate = function () {
            var id = this.intervalUpdateInfo.timerId;
            if (this.updaterIDs.contains(id)) {
                window.clearInterval(id);
                this.updaterIDs.erase(id);
            }
        }

        this.restartIntervalUpdate = function (url) {
            this.cancelIntervalUpdate();
            this.setIntervalUpdate(url, this.intervalUpdateInfo.callback,
                    this.intervalUpdateInfo.interval,
                    this.intervalUpdateInfo.passback);
        }

        this.branchIntervalUpdate = function () {
            return this.session.branch(this.intervalUpdateInfo.url);
        }

        this.resumeIntervalUpdate = function () {
            wooly.setIntervalUpdate(wooly.intervalUpdateInfo.url,
                    wooly.intervalUpdateInfo.callback,
                    wooly.intervalUpdateInfo.interval,
                    wooly.intervalUpdateInfo.passback);
        }
        this.updateNow = function () {
            wooly.setIntervalUpdate(wooly.intervalUpdateInfo.url,
                    wooly.intervalUpdateInfo.callback,
                    0,
                    wooly.intervalUpdateInfo.passback);
        }
        this.doubleIntervalUpdate = function () {
            wooly.cancelIntervalUpdate();
            wooly.intervalUpdateInfo.interval *= 2;
            wooly.setIntervalUpdate(wooly.intervalUpdateInfo.url,
                    wooly.intervalUpdateInfo.callback,
                    wooly.intervalUpdateInfo.interval,
                    wooly.intervalUpdateInfo.passback);
        }

        this._doc = new WoolyDocument(document);

        this.doc = function(doc) {
            if (doc) {
                return new WoolyDocument(doc);
            } else {
                return this._doc;
            }
        }
    }

    function WoolyDocument(node) {
        assert(node);

        this.node = node;

        this.root = function() {
            return new WoolyElement(this, node.documentElement);
        }

        this.elems = function(name, start) {
            if (start == null) {
                start = 0;
            }

            var nodes = this.node.getElementsByTagName(name);
            var coll = new WoolyCollection(this, nodes, WoolyElement);

            for (var i = 0; i < start; i++) {
                coll.next();
            }

            return coll;
        }

        this.elem = function(name, n) {
            return this.elems(name, n).next();
        }

        this.objectify = function() {
            return this.root().object();
        }
    }

    function WoolyCollection(doc, nodes, nodeClass) {
        assert(doc);
        assert(nodes);
        assert(nodeClass);

        this.doc = doc;
        this.nodes = nodes;
        this.nodeClass = nodeClass;

        this.pos = 0;

        this.next = function() {
            var node = this.nodes[this.pos++];

            if (node) {
                return new this.nodeClass(this.doc, node);
            } else {
                return null;
            }
        }

        this.get = function(index) {
            var node = this.nodes[index];

            if (node) {
                return new this.nodeClass(this.doc, node);
            } else {
                return null;
            }
        }
    }

    function WoolyElement(doc, node) {
        assert(doc);
        assert(doc instanceof WoolyDocument);
        assert(node);
        // assert(node instanceof Node); IE pukes on this
        assert(node.nodeType == 1);

        this.doc = doc;
        this.node = node;

        this.clear = function() {
            var child = this.node.firstChild;
            var next;

            while (child) {
                next = child.nextSibling;
                this.node.removeChild(child);
                child = next;
            }

            return this;
        }

        this.add = function(content) {
            assert(content);

            if (typeof content == "string") {
                // XXX flatten this out
                this.add(new WoolyText(this.doc, null).set(content));
            } else if (content.hasOwnProperty("node")) {
                this.node.appendChild(content.node);
            } else {
                throw new Error("Content is of unexpected type");
            }

            return this;
        }

        this.set = function(content) {
            this.clear().add(content);

            return this;
        }

        this.getattr = function(name) {
            return this.node.getAttribute(name);
        }

        this.setattr = function(name, value) {
            this.node.setAttribute(name, value);

            return value
        }

        this.dict = function(name, kattr, vattr) {
            var dict = new Object();
            var elems = this.elems(name);
            var elem = elems.next();

            while (elem != null) {
                dict[elem.getattr(kattr)] = elem.getattr(vattr);
                elem = elems.next();
            }

            return dict;
        }

        // XXX Rename to objectify
        this.object = function() {
            return translate(this.node, null);
        }

        this.update = function(data) {
            update(this.node, null, data);
        }

        this.descendant = function(path) {
            var node = descendant(this.node, path);

            return new WoolyElement(this.doc, node);
        }

        this.elems = function(name, attr, attrValue, start, limit) {
            if (start == null) {
                start = 0;
            }

            var nodes = new Array();

            find(nodes, limit, this.node, 1, name, attr, attrValue);

            var coll = new WoolyCollection(this.doc, nodes, WoolyElement);

            for (var i = 0; i < start; i++) {
                coll.next();
            }

            return coll;
        }

        this.elem = function(name, attr, attrValue) {
            return this.elems(name, attr, attrValue, 0, 1).next();
        }

        this.texts = function(start, limit) {
            var nodes = new Array();

            find(nodes, limit, this.node, 3);

            var coll = new WoolyCollection(this.doc, nodes, WoolyText);

            for (var i = 0; i < start; i++) {
                coll.next();
            }

            return coll;
        }

        this.text = function() {
            return this.texts(0, 1).next();
        }
    }

    function WoolyText(doc, node) {
        assert(doc);
        assert(doc instanceof WoolyDocument);
        if (node) {
        //assert(node instanceof Node);
        assert(node.nodeType == 3);
        }

        this.doc = doc;

        if (node == null) {
            this.node = doc.node.createTextNode("");
        } else {
            this.node = node;
        }

        this.get = function() {
            return this.node.data
        }

        this.set = function(data) {
            assert(typeof data == "string");

            this.node.data = data

            return this;
        }
    }

    function Session() {
        this.branch = function (url) {
            if (arguments.length == 0) url = window.location.href + "";
            return new Branch(url);
        }

        this.hash = function () {
            var h = window.location.hash;
            if ((h.length > 0) && (h.substring(0, 1) == "#"))
                h = h.substring(1, h.length );
            return wooly.session.branch(h);
        }

        this.setHash = function (hash) {
            var href = window.location.href;
            var hashIndex = href.indexOf("#");
            if (hashIndex > 0) {
                href = href.substring(0, hashIndex);
            }
            window.location.replace(href + "#" + hash.marshal());
        }

        /* convert string query into cumin session object */
        function Branch (s) {

            /* convert this branch object to string */
            this.marshal = function () {
                var nvs = [];
                for (var key in this) {
                    if (this[key] instanceof Array) {
                        // there were multiple parameters with the same name
                        for (var i=0; i < this[key].length; i++) {
                            nvs.push(key + "=" + encodeURIComponent(this[key][i]));
                        }
                    } else if (key == "__page") {
                        //pass;
                    } else if (key == "session") {
                        var sess = this[key].marshal();
                        nvs.push("session="+encodeURIComponent(sess));
                    } else if (this[key] == null) {
                        nvs.push(key);
                    } else if (!(this[key] instanceof Function)) {
                        nvs.push(key + "=" + encodeURIComponent(this[key] + ""));
                    }
                }

                return (nvs.length) ? ((this.__page) ? this.__page + "?" : "") + nvs.join(";") : (this.__page) ? this.__page : "";
            }

            this.set = function (key, value) {
                this[key] = value;
            }

            // find the page
            var query = s.split("?");
            if (query.length > 1) {
                this.__page = query[0];
            } else if (s.indexOf("=") == -1) {
                this.__page = s;
                return;
            } else {
                this.__page = null;
            }
            // find the other nv pairs
            var q = (query.length > 1) ? query[1] : s;
            Object.append(this, parseQuery(q)); // $extend went away with mootools 1.3

            // background updates have another session object under the key "session"
            if (this.session) {
                var sess = decodeURIComponent(this.session);
                this.session = wooly.session.branch(sess);
            }
        }

        /* convert ; separated string to and object.
           supports names with no values and
           puts duplicate names into an array */
        function parseQuery(s) {
            var vars = s.split(";");
            var obj = {};
            for (var i=0; i < vars.length; i++) {
                var val = vars[i];
                var keys = val.split('=');
                if (keys.length == 2) {
                    var value = decodeURIComponent(keys[1]);
                    if (typeof obj[keys[0]] != "undefined") {
                        var oldval = obj[keys[0]];
                        if (oldval.push) {
                            oldval.push(value); // already added at least two values
                        } else {
                            obj[keys[0]] = [oldval, value]; // adding second value
                        }
                    } else {
                        obj[keys[0]] = value;  // adding first value
                    }
                } else {
                    obj[keys[0]] = null;  // there was no value
                }
            }
            return obj;
        }
    }

}())
