
//+ Jonas Raoni Soares Silva
//@ http://jsfromhell.com/dhtml/incremental-search [rev. #4]

IncrementalSearch = function(input, callback, className, listObjectID, maxEntries){
    var i, thisObject = this;
    thisObject.listObjectID = listObjectID;
    thisObject.maxEntries = maxEntries;
    (thisObject.input = input).autocomplete = "off", thisObject.callback = callback || function(){},
    thisObject.className = className || "", thisObject.hide(), thisObject.visible = 0;
    for(i in {keydown: 0, focus: 0, blur: 0, keyup: 0, keypress: 0})
        this.addEvent(input, i, thisObject._handler, thisObject);
};
with({p: IncrementalSearch.prototype}){
    //+ Carlos R. L. Rodrigues
    //@ http://jsfromhell.com/geral/event-listener [rev. #5]
    p.addEvent = function(o, e, f, s){
        var r = o[r = "_" + (e = "on" + e)] = o[r] || (o[e] ? [[o[e], o]] : []), a, c, d;
        r[r.length] = [f, s || o], o[e] = function(e){
            try{
                (e = e || event).preventDefault || (e.preventDefault = function(){e.returnValue = false;});
                e.stopPropagation || (e.stopPropagation = function(){e.cancelBubble = true;});
                e.target || (e.target = e.srcElement || null);
                e.key = (e.which + 1 || e.keyCode + 1) - 1 || 0;
            }catch(f){}
            for(d = 1, f = r.length; f; r[--f] && (a = r[f][0], o = r[f][1], a.call ? c = a.call(o, e) : (o._ = a, c = o._(e), o._ = null), d &= c !== false));
            return e = null, !!d;
        }
    };

    p.show = function(){
        var i = $(this.input), s = $(this.c);
        var iSize = i.getSize(), iPos = i.getPosition();
        var sPos = iPos; sPos.y = iPos.y + iSize.y;
        s.setPosition(sPos); s.setStyle('width', iSize.x);
        var thisObject = this, s = thisObject.c.style;
        thisObject.l.length ? (s.display = "block", !thisObject.visible && (thisObject._callEvent("onshow"), ++thisObject.visible), thisObject.highlite(0)) : s.display = "none";
    };
    p.hide = function(){
        var thisObject = this, d = document, s = (thisObject.c && thisObject.c.parentNode.removeChild(thisObject.c),
        thisObject.c = d.body.appendChild(d.createElement("div"))).style;
        thisObject.l = [], thisObject.i = -1, thisObject.c.className = thisObject.className, s.position = "absolute", s.display = "none";
        thisObject._old = null, thisObject.visible && (thisObject._callEvent("onhide"), --thisObject.visible);
    };
    p.add = function(s, x, data){
        var thisObject = this, l = 0, d = document, i = thisObject.l.length, v = thisObject.input.value.length,
            o = (thisObject.l[i] = [s, data, thisObject.c.appendChild(d.createElement("div"))])[2];
        if(i >= thisObject.maxEntries)
            return;
        if ( x == -1) {
            o.appendChild(d.createTextNode( s ));
        } else {
            if(x instanceof Array || (x = [x]), o.i = i, o.className = "normal", !isNaN(x[0]))
                for(var j = -1, k = x.length; ++j < k; o.appendChild(d.createTextNode(
                    s.substring(l, x[j]))).parentNode.appendChild(d.createElement(
                    "span")).appendChild(d.createTextNode(s.substring(x[j],
                    l = x[j] + v))).parentNode.className = "highlited");
            
            for(x in o.appendChild(d.createTextNode(s.substr(l))), {click: 0, mouseover: 0})
                p.addEvent(o, x, thisObject._handler, thisObject);
        }
    };
    p.highlite = function(i){
        var thisObject = this;
        thisObject._invalid(i) || (thisObject._invalid(thisObject.i) || (thisObject.l[thisObject.i][2].className = "normal"),
        thisObject.l[thisObject.i = i][2].className += " selected", thisObject._callEvent("onhighlite", thisObject.l[i][0], thisObject.l[i][1]));
    };
    p.select = function(i){
        var thisObject = this;
        thisObject._invalid(i = isNaN(i) ? thisObject.i : i) || (thisObject._callEvent("onselect",
            thisObject.input.value = thisObject.l[thisObject.i][0], thisObject.l[i][1]), thisObject.hide());
    };
    p.next = function(){
        var thisObject = (thisObject = this, thisObject.highlite((thisObject.i + 1) % thisObject.l.length));
    };
    p.previous = function(){
        var thisObject = (thisObject = this, thisObject.highlite((!thisObject.i ? thisObject.l.length : thisObject.i) - 1));
    };
    p._fadeOut = function(){
        var f = (f = function(){arguments.callee.x.hide();}, f.x = this, setTimeout(f, 200));
        this.select();
    };
    p._handler = function(e){
        var thisObject = this, t = e.type, k = e.key;
        t == "focus" || t == "keyup" ? k != 40 && k != 38 && k != 13 && thisObject._old != thisObject.input.value && (thisObject.hide(), thisObject.callback(thisObject, thisObject.input.value))
        : t == "keydown" ? k == 40 ? thisObject.next() : k == 38 ? thisObject.previous() : thisObject._old = thisObject.input.value
        : t == "keypress" ? k == 13 && (e.preventDefault(), thisObject.select())
        : t == "blur" ? thisObject._fadeOut() : t == "click" ? thisObject.select()
        : thisObject.highlite((/span/i.test((e = e.target).tagName) ? e.parentNode : e).i);
    };
    p._invalid = function(i){
        return isNaN(i) || i < 0 || i >= this.l.length;
    }
    p._callEvent = function(e){
        var thisObject = this;
        return thisObject[e] instanceof Function ? thisObject[e].apply(thisObject, [].slice.call(arguments, 1)) : undefined;
    };
}
function Inc_CIBeginning(o, search) {
    if (search = search.toLowerCase()) {
        var select = $(o.listObjectID);
        for (var i = 0, l = select.options.length; i < l; ++i) {
            if (select.options[i].text.toLowerCase().indexOf(search) == 0)
                o.add(select.options[i].text, 0, select.options[i].value);
        }
    }
    if ((o.l.length == 0) && (search.length > 0)) {
        o.add("No Matches", -1);
    }
    o.show();
}
