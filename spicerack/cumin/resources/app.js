var cumin;

(function() {
    cumin = new Cumin();

    function runModelListeners(model) {
        for (var id in this.modelListeners) {
            this.modelListeners[id](id, model);
        }
    }

    function runObjectListeners(object) {
        for (var id in this.objectListeners) {
            this.objectListeners[id](id, object);
        }
    }

    function Cumin() {
        this.modelListeners = new Object();
        this.objectListeners = new Object();

        this.runModelListeners = runModelListeners;
        this.runObjectListeners = runObjectListeners;

        this.refreshTime = function(src) {
            var branch = wooly.session.branch(src);
            branch.ts = new Date().getTime();
            return branch.marshal()
        }

        this.updateChart = function(id) {
            var chart = $(id);
            var img = chart.getElementsByTagName("img")[0]

            var src = img.src;
            src = cumin.refreshTime(src);
            img.src = src;
        }

        this.clickTableCheckbox = function (check, name) {
            var val = check.value;
            var hash = wooly.session.hash();
            if (!(name in hash)) {
                hash[name] = "";
            }
            var vals = Array.from(hash[name].split('|'));
            if ((vals.length == 1) && (vals[0] == ""))
                vals.empty();
            var valIndex = vals.indexOf(val);
            var negValIndex = vals.indexOf("-"+val);
            if (check.checked) {
                // the checkbox was just checked
                if (negValIndex > -1)
                    vals.erase("-"+val);
                else if (valIndex == -1)
                    vals.push(val);
            } else {
                if (valIndex > -1)
                    vals.erase(val);
                else if (negValIndex == -1)
                    vals.push("-"+val);
            }
            if (vals.length == 0)
                delete hash[name];
            else
                hash[name] = vals.join('|');
            wooly.session.setHash(hash);
        }

        this.restoreTableCheckboxes = function () {
            var hash = wooly.session.hash();
            for (var key in hash) {
                if (!(hash[key] instanceof Function)) {
                    if (document.forms.length > 0) {
                        var checks = document.forms[0].elements[key];
                        if (checks) {
                            var vals = Array.from(hash[key].split('|'));
                            if ((vals.length == 1) && (vals[0] == ""))
                                vals.empty();
                            if (typeof checks.length == "undefined") {
                                if (vals.contains(checks.value)) {
                                    checks.checked = true;
                                }
                                if (vals.contains("-"+checks.value))
                                    checks.checked = false;
                            } else {
                                for (var i=0; i < checks.length; i++) {
                                    if (vals.contains(checks[i].value)) {
                                        checks[i].checked = true;
                                    }
                                    if (vals.contains("-"+checks[i].value))
                                        checks[i].checked = false;
                                }
                            }
                        }
                    }
                }
            }
        }

        this.setFullpageHandler = function (id, fullpage_url) {
            var chart = $(id);
            if (chart) {
                chart.preFullPage = function () { cumin.fullpageChart(fullpage_url); return false;};
            }
        }

        this.setupChart = function (id, width) {
            var chart = $(id);
            chart.onfullpage = function (width, height) { cumin.chartNotify(true, width, height, id); };
            chart.onrestore = function () { cumin.chartNotify(false, width, 100, id); };
            var oImg = document.images[id];
            var mImg = $(oImg);
            mImg.addEvent('load', function () {
                this.style.visibility = "visible";
                this.removeAttribute("width");
                this.removeAttribute("height");
                this.className = "";
                var loading = chart.getElement(".loading");
                loading.setStyle('display', 'none');
                loading.setStyle('visibility', 'visible');
                loading.loading = false;
                var over = mImg.retrieve("over");
                if (over) {
                    get_chart_points(oImg);
                }
            });
            mImg.addEvent('mousedown', function(event){
                event.stop();
            });
            mImg.addEvent('mouseout', function(event){
                if (event.relatedTarget && event.relatedTarget.className)
                    if (event.relatedTarget.className.indexOf("img") == 0) {
                        event.stop();
                        return false;
                    }
                var mBody = $(document.body);
                var oHighlight = mBody.getElement(".imgHighlight_red");
                if (oHighlight) oHighlight.style.display = "none";
                oHighlight = mBody.getElement(".imgHighlight_green");
                if (oHighlight) oHighlight.style.display = "none";
                oHighlight = mBody.getElement(".imgHighlight_blue");
                if (oHighlight) oHighlight.style.display = "none";
                var oValue = mBody.getElement(".imgValues_red");
                if (oValue) oValue.style.display = "none";
                oValue = mBody.getElement(".imgValues_green");
                if (oValue) oValue.style.display = "none";
                oValue = mBody.getElement(".imgValues_blue");
                if (oValue) oValue.style.display = "none";
                mImg.store("over", false);
            });
            mImg.addEvent('mouseover', function(event){
                mImg.store("over", true);
                get_chart_points(mImg);
            });
            mImg.addEvent('mousemove', function(event){
                cumin.chartMove(mImg, event);
            });
        }

        this.chartMove = function (mImg, event) {
            closestPoint = function (x, info) {
                samples = info['points'];
                var closest = samples[0];
                for (var i=0; i<samples.length; i++) {
                    var coord = samples[i];
                    if (Math.abs(x - coord[0]) < Math.abs(x -closest[0]))
                        closest = coord;
                }
                return closest;
            }
            highlight = function (stat, point, xy) {
                var mBody = $(document.body);
                var oHighlight = mBody.getElement(".imgHighlight_"+stat);
                var oValues = mBody.getElement(".imgValues_"+stat);
                if (!oHighlight) {
                    oHighlight = new Element('div', { 'class': 'imgHighlight_'+stat });
                    oValues = new Element('div', { 'class': 'imgValues_'+stat });
                    mBody.appendChild(oHighlight);
                    mBody.appendChild(oValues);
                }
                var pos = mImg.getPosition();
                oHighlight.style.display = "block";
                oHighlight.style.left = (pos.x + point[0] - 5) + "px";
                oHighlight.style.top = (pos.y + point[1] - 3) + "px";

                oValues.style.display = "block";
                oValues.style.left = (pos.x + xy[0] + 32) + "px";
                oValues.style.top = (pos.y + xy[1] - 8) + "px";
                oValues.innerHTML = "("+point[2]+")";
            }
            
            var points = mImg.retrieve('points');
            if (points) {
                for (var stat in points) {
                    var samples = points[stat];
                    var x = event.client.x;
                    mImg.store("lastX", x);
                    var pos = mImg.getPosition();
                    var point = closestPoint(x - pos.x, samples);
                    if (typeof point != "undefined")
                        highlight(points[stat]['color'], point, points[stat]['xy']);
                }
            }
        }

        // called when a chart widget is maximized or restored
        this.chartNotify = function (full, width, height, id) {
            var bWidth = Math.max(width - 100, 360);
            var bHeight = Math.max(height - 100, 100);
            var oImg = document.images[id];
            if (oImg) {
                var src = oImg.src;
                var branch = wooly.session.branch(src);
                branch.width = bWidth;
                branch.height = bHeight;
                src = branch.marshal();

                src = cumin.refreshTime(src);
                oImg.className = "Loading";
                oImg.onerror = oImg.onload = function () {this.className = ""};
                oImg.width = width;
                oImg.height = height;
                oImg.style.visibility = "hidden";
                oImg.src = src;

                var loading = $(id).getElement(".loading");
                loading.loading = true;
                setTimeout("showLoading('"+id+"')", 1000);
                setTimeout("hideLoading('"+id+"')", 1000 * 60);
            }
            return true;
        }

        this.makeFullPageable = function (element) {
            if (element.getParent().getElement(".fullpageIcon"))
                return; // already fullpaged

            var fpIconClass = 'fullpageIcon';
            if (element.get('class').indexOf("oldfpiconlocation") != -1) {
            	fpIconClass = 'fullpageIconOldLocation';
            }
            
            var icon = new Element('p', {'class': fpIconClass, 
                 'title': 'Full Page', 
                 'events': {'click': function () {fullpage(this)}}});

            var title = element.getElement("h2");
            if (title) {
                icon.inject(title, 'before');
                title.addEvent('dblclick', function () {fullpage(icon)});
            }
            element.originalParent = element.getParent();

            var widgets = element.getElements('.fullpage_notify');
            element.widgetPaths = [];
            widgets.each(function (widget) {
                if (widget.get("id")) {
                    element.widgetPaths.push(widget.get("id"));
                }
            });
        }

        this.fullpageChart = function (fullpage_url) {
            var params  = 'width='+screen.width;
            params += ', height='+screen.height;
            params += ', top=0, left=0'
            params += ', fullscreen=yes';
            var branch = wooly.session.branch(fullpage_url);
            branch['width'] = Math.floor(screen.width * 0.96);
            branch['height'] = Math.floor(screen.height * 0.96);

            var newwin = window.open(branch.marshal(), 'cuminflash', params);
            if (window.focus) {
                newwin.focus();
            }
        }

    }
}())


/* surround all elements that have class 'fullpageable' with
    supporting divs and add event behaviors */
window.addEvent('domready', function () {
    var elements = $$('.fullpageable');
    for (var i=0; i<elements.length; i++) {
        var element = elements[i];

        if (element.getStyle("visibility") != "hidden") {
            cumin.makeFullPageable(element);
        }
    }
});

/* called when the full page icon is clicked */
function fullpage(oIcon) {
    var oFullPage = oIcon.getParent();

    // short circuit to open in a new window
    if (oFullPage.preFullPage) {
        if (!oFullPage.preFullPage())
            return false;
    }

    var oBack = $("fullpageBack");
    if (!oBack) {
        oBack = new Element('div', {'class': 'fullpageBack', 'id': 'fullpageBack', 'events': {'click': fullpage}});
        document.body.appendChild(oBack);
    }
    if (oFullPage.parentNode == document.body) {
        // undo full page
        oBack.style.display = "none";
        oFullPage.removeClass('fullpaged');
        oFullPage.addClass('fullpageable');

        document.body.style.height = "auto";
        oFullPage.originalParent.appendChild(oFullPage);
        oIcon.setProperty("title", "Full Page");
        setFullpageParam(false, oFullPage);
        $(oFullPage).getElement(".jqplotgraph").setProperty("style", "width:400px;height:150px;");
        drawSingleChart($(oFullPage).getElement(".jqplotgraph"), false);
        var onrestore = oFullPage.onrestore;
        if (onrestore) onrestore();
        window.scrollTo(oFullPage.origScroll.x, oFullPage.origScroll.y);
    } else {
        // make it full page

        oBack.style.display = "block";
        oBack.style.height = Math.max($(document.body).getCoordinates().height, window.getScrollSize().y) + "px";
        document.body.style.height = "100%";

        document.body.appendChild(oFullPage);

        oFullPage.removeClass('fullpageable');
        oFullPage.addClass('fullpaged');

        oIcon.setProperty("title", "Restore");
        setFullpageParam(true, oFullPage);

        var onfullpage = oFullPage.onfullpage;
        var coords = $(oFullPage).getCoordinates();
        var height = Math.min(Math.max(window.getSize().y - 100, 200), 600);
        if (onfullpage) 
            onfullpage(coords.width, height);
        $(oFullPage).getElement(".jqplotgraph").setProperty("style", "width:100%");
        drawSingleChart($(oFullPage).getElement(".jqplotgraph"), false);
        var curScroll = window.getScroll();
        oFullPage.origScroll = curScroll;
        window.scrollTo(0,0);
    }

    // sets/clears the fullpage parameter in the wooly background update url 
    function setFullpageParam(set, oFullPage) {
        var branch = wooly.branchIntervalUpdate();
        if (set) {
            var width = $(oFullPage).getCoordinates().width + "";
            oFullPage.widgetPaths.each(function (path) {
                branch.session[path+".fullpage"] = width;
            });
        } else {
            oFullPage.widgetPaths.each(function (path) {
                delete branch.session[path+".fullpage"];
            });
        }
        wooly.restartIntervalUpdate(branch.marshal());
        cumin.expireIntervalUpdate();
    }
}

cumin.getChart = function (id) {
    var chart = $(id.replace(/\./g, "_")+"_chart");
    return chart;
}

function incrementChartSequence(chart) {
    var src = chart.src;
    var branch = wooly.session.branch(src);
    if (typeof branch['seq'] == "undefined")
        branch['seq'] = '0';
    var seq = parseInt(branch['seq']) + 1;
    branch['seq'] = seq;
    chart.src = branch.marshal();
    return seq;
}


function addJavascript(jsname, pos) {
    var th = document.getElementsByTagName(pos)[0];
    var s = document.createElement('script');
    s.setAttribute('type','text/javascript');
    s.setAttribute('src',jsname);
    th.appendChild(s);
}
addJavascript('resource?name=incrementalSearch.js', 'head');

function ofc_debug(msg) {
    wooly.log(msg);
}

function showHistoryChart(title, src) {

    if (src != '') {
        new StickyWin.Modal.Ajax({
          url: src,
          wrapWithUi: true,
          caption: title,
          useIframeShim: false,
          allowMultiple: false,
          closeOnEsc: true,
          uiOptions: {width: 450},
          edge: false,
          position: 'center',
          offset: {x:0,y:0},
          relativeTo: document.body,
          handleResponse: function(response){
			var responseScript = "";
			this.Request.response.text.stripScripts(function(script){ responseScript += script; });
			if (this.options.wrapWithUi) response = StickyWin.ui(this.options.caption, response, this.options.uiOptions);
			this.setContent(response);
			this.show();
			if (this.evalScripts) $exec(responseScript);
			drawAllCharts();
			}
        }).update();
    }
    return false;
}

var ONE_MINUTE = 60;
var TEN_MINUTES = 600;
var ONE_HOUR = 3600;
var ONE_DAY = 86400;
var ONE_MONTH = 2592000;
var ONE_YEAR = 31557600;
var MAX_UPDATE_CHART_DURATION = ONE_DAY;

var CHART_UPDATE_INTERVAL_MS = 10000;
/* 
   This block of code sets up the allCharts object which is where all of the
   charts will be stored.  If a given chart already exists in the allCharts
   object, it will be redrawn rather than fully rebuilt to preserve client side 
   cycles/memory
*/ 
var allCharts = new Object();
allCharts['chartNowTime'] = new Date();
chart_href = 0; //used if we rearrange the divs that show the charts
window.addEvent("domready", function() {
	drawAllCharts();
});


/*
	This function grabs all of the charts [with the .joplotgraph class] on the page and
	triggers a draw [or redraw] for each of them
*/
drawAllCharts = function() {
	$$('.jqplotgraph').each(function(thisdiv) {
			drawSingleChart(thisdiv, false);
		});
}

/*
  This function grabs the data url (chart.json) from the div that will house the chart.
  It then uses the wooly.setIntervalUpdate to fetch the data via AJAX and will call the stathandler
  function after that data is fetched
*/ 
drawSingleChart = function(id, doForceRedraw) {
	var jsonurl = $(id).getParent().getElements('a')[chart_href].get('href');
	var passback = "";
	if(allCharts[id.id]) {
		allCharts[id.id].forceRedraw = doForceRedraw;
	}
	allCharts['chartNowTime'] = new Date();
	wooly.setIntervalUpdate(jsonurl, stathandler, 0, passback, true);
}

/*
 * This function handles the automatic updates for each chart.  Updates will only happen
 * for charts that have a duration <= MAX_UPDATE_CHART_DURATION (1 day).  Updates will also only happen
 * when the "resume updates" button is not showing.
 */
updateSingleChart = function(id) {
	// if the "resume updates" is displayed, we don't want to do updates.
	if($('shock').style.display != "undefined" && $('shock').style.display != "block") {
		var jsonurl = $(id).getParent().getElements('a')[chart_href].get('href');
		chartParams = wooly.session.branch(jsonurl);
		// for long-duration charts, updating is not particularly useful
		if(chartParams.duration <= MAX_UPDATE_CHART_DURATION) {
			drawSingleChart(id, false);
		}
	}
}

/*
   This function sets up the timer that will trigger the updating of each chart
*/
startChartMonitor = function(id) {
	allCharts[id].intervalId = setInterval(function() {updateSingleChart(id)}, CHART_UPDATE_INTERVAL_MS);
}

/*
   This function is meant to take the JSON response from cumin and do some basic work on it (determine max/min).
   A lot of the dirtier work is done in the parseJson function.
   After getting the data into the dataContainer object, the drawChart funct// maybe there needs to be updatesinglechart that will check duration, etcion is called
*/
stathandler = function(response) {
	try {
	response = JSON.decode(response);
	var dataopts = new Object();
	dataopts['xmin'] = response['duration'] * -1;
	dataopts['xmax'] = 0;
	dataContainer = parseJson(response);
	drawChart(response["graph_div"], dataContainer, dataopts);
	} catch(err) {
		console.log("Caught exception: " + err);
	}
	return true;
}

/*
    The parseJson function takes the output from cumin and massages it into
	something that is useful for the charting library in use (currently jqplot).
	It is most definitely easier to tweak this function as needed than it is to 
	make significant (and possibly temporary) adjustments to the cumin output
*/
parseJson = function(json) {
	var dataContainer = new Object();
	dataContainer['end_secs'] = json.end_secs;
	dataContainer['tnow'] = json.tnow;
	dataContainer['x_axis_values'] = [];
	dataContainer['duration'] = json['duration'];
	
	switch(json['duration']) {
			case TEN_MINUTES:
				dataContainer['x_axis_normalizer'] = ONE_MINUTE;
				dataContainer['x_axis_unit_label'] = "min";
				break;
			case ONE_HOUR:
			    dataContainer['x_axis_normalizer'] = ONE_MINUTE;
			    dataContainer['x_axis_unit_label'] = "min";
			    break;
			case ONE_DAY:
			    dataContainer['x_axis_normalizer'] = ONE_HOUR;
			    dataContainer['x_axis_unit_label'] = "hr";
			    break;
			case ONE_MONTH:
			    dataContainer['x_axis_normalizer'] = ONE_DAY;
			    dataContainer['x_axis_unit_label'] = "day";
			    break;
			case ONE_YEAR:
				dataContainer['x_axis_normalizer'] = ONE_MONTH;
				dataContainer['x_axis_unit_label'] = "mo";
				break;			    
		}

	for ( var i = 0; i < json.x_axis.labels.labels.length; i++) {
		dataContainer['x_axis_values'] = dataContainer['x_axis_values']
				.append([ json.x_axis.labels.labels[i].text ]);
	}

	dataContainer['x_coordinate_values'] = new Array();
	for ( var i = 0; i < json.elements.length; i++) {
		dataContainer['x_coordinate_values'][i] = new Array();
		for ( var j = 0; j < json.elements[i].values.length; j++) {
			dataContainer['x_coordinate_values'][i]
					.append([ json.elements[i].values[j].dt / dataContainer['x_axis_normalizer'] ]);
		}
	}

	dataContainer['y_coordinate_values'] = new Array();
	for ( var i = 0; i < json.elements.length; i++) {
		dataContainer['y_coordinate_values'][i] = new Array();
		for ( var j = 0; j < json.elements[i].values.length; j++) {
			dataContainer['y_coordinate_values'][i].append([ [
					(json.elements[i].values[j].dt - dataContainer['tnow']) / dataContainer['x_axis_normalizer'],
					json.elements[i].values[j].y ] ]);
		}
	}

	dataContainer['labels'] = new Array(json.elements.length);
	for ( var i = 0; i < json.elements.length; i++) {
		dataContainer['labels'][i] = json.elements[i].text;
	}

	for ( var i = 0; i < json.x_axis.labels.labels.length; i++) {
		dataContainer['x_axis_values'] = dataContainer['x_axis_values']
				.append([ json.x_axis.labels.labels[i].text ]);
	}
	return dataContainer;
}


/*
   This function takes the dataContainer and formats the data (and labels)
   for jqplot library.  The resultant series array is used in the options
   passed to draw the chart.
*/  
getSeries = function(dataContainer) {
	var series = new Array(dataContainer['labels'].length);
	for(var i=0; i < dataContainer['labels'].length; i++) {
		series[i] = {yaxis: 'y2axis', label: dataContainer['labels'][i]};					
	}
	return series; 
}

/*
   This function will render a jqplot chart for the given div (holder), dataContainer (lists of data) and options on that data (dataopts)
*/    
drawChart = function(holder, dataContainer, dataopts, forceRedraw) {
   $j.jqplot.config.enablePlugins = true; // needed when using pie and non-pie charts since pie charts explicitly turn off enablePlugins

	// The chartOptionsObject is where the action is.  Pretty much every characteristic of the chart is defined here.
	// Details on usage are found here:  http://www.jqplot.com/docs/files/usage-txt.html
	var chartOptionsObject = {
	title: {
        text: '',
        show: false,
    },
    gridPadding: {top:35, right:20, bottom:20, left:20},
	grid: { background: '#FFFFFF' },
		legend: {
		 show:true,
		 location: 'n',
		 renderer: $j.jqplot.EnhancedLegendRenderer,
		 yoffset: 0,
		 xoffset: 0,
		 placement: "outside",
		 rendererOptions:{
                 numberColumns:6,
                 seriesToggle:"fast",
                 disableIEFading:true
            }
		 },
	axes: {
	        y2axis: {
	        	autoscale:true,
	        	min:0,
	        	tickOptions:{formatString:'%.0f',formatter: y_axis_Formatter,},
	        	pad:1.2,
	        	numberTicks:4,
	        	},
			xaxis: {
				autoscale: true, 
				pad:0, 
				min:dataopts['xmin'] / dataContainer['x_axis_normalizer'], 
				max:dataopts['xmax'] / dataContainer['x_axis_normalizer'],
				tickOptions:{formatString:'%.0f ' + dataContainer['x_axis_unit_label'], formatter: x_axis_Formatter,},
				}
	      },
    series: getSeries(dataContainer),
    seriesColors: ['#009926','#992600','#0036d6','#ffc414','730099','#ff00cc'],
	seriesDefaults: {
		lineWidth:1,
		fill:true,
		fillAndStroke:true,
		fillAlpha: 0.1,
		rendererOptions: {
		        highlightMouseOver: false,
		        highlightMouseDown: false,
		        highlightColor: null,
				markerRenderer: $j.jqplot.MarkerRenderer,    
		},
	markerOptions: {show:true,
					lineWidth:1,
					style:'filledCircle',
					size:3,
				    },
	},
	highlighter: {
			sizeAdjust: 6,
			lineWidthAdjust: 2.5,
			showTooltip:true,
			fadeTooltip:true,
			tooltipOffset: 2,
			tooltipSeparator: ",",
			tooltipaxes:'xy',
			tooltipLocation: 'n',
			useAxesFormatters:true,
        	show: true,
        	formatString:'<table class="jqplot-highlighter"><tr><td>Time: %s</td></tr>#allSeries#</table>',
        	tooltipContentEditor:customTooltip,
    },
	cursor:{
			style:"pointer",
			show:true,
			zoom:true,
			showTooltip:false, // this is for the tooltip that gives the location of the cursor whether on a point or not
			looseZoom:true,
			showCursorLegend:false,
			constrainZoomTo: 'x',
			showVerticalLine:false,
	},	
  }; // end of chartOptionsObject  
  
  var divName = $(holder).get('id');
  
  // If we have no real data to plot, add a fake coordinate to plot an empty chart
  for (i=0; i < dataContainer['labels'].length; i++) {
    if(dataContainer['y_coordinate_values'][i].length == 0) {
    	dataContainer['y_coordinate_values'][i] = [1,0];
    }
  }
  
  // if the chart already exists, perform a "replot()" on the chart, otherwise, draw the chart from scratch
  if(allCharts[divName] != undefined) {
	  if(allCharts[divName]["forceRedraw"] == true) {
		  allCharts[divName].destroy();
		  allCharts[divName] =  $j.jqplot(holder, dataContainer['y_coordinate_values'],chartOptionsObject);
	  } else {
	      for(i=0; i < allCharts[divName].series.length; i++) {
	      	allCharts[divName].series[i].data = dataContainer['y_coordinate_values'][i];
	      }
	      try {
			allCharts[divName].replot({resetAxes:(!allCharts[divName].plugins.cursor._zoom.isZoomed), axes:{y2axis:{autoscale:true,min:0,pad:1.2,numberTicks:4,tickOptions:{formatString:'%.0f',formatter: y_axis_Formatter,}}, xaxis:{min:dataopts['xmin'] / dataContainer['x_axis_normalizer'], max:dataopts['xmax'] / dataContainer['x_axis_normalizer'],tickOptions:{formatString:'%.0f ' + dataContainer['x_axis_unit_label'], formatter: x_axis_Formatter,}}}})
		  } catch (err) {
		  	// this is needed in the event of the first draw for a fullpage chart
		    allCharts[divName] =  $j.jqplot(holder, dataContainer['y_coordinate_values'],chartOptionsObject);
		  }
	  }
  } else {
	  $j.jqplot.preDrawHooks.push(cuminChartPreDraw);
	  $j.jqplot.postDrawHooks.push(cuminChartPostDraw);
	  allCharts[divName] =  $j.jqplot(holder, dataContainer['y_coordinate_values'],chartOptionsObject);
	  allCharts[divName].target.bind('jqplotResetZoom', cuminChartResetZoom);   
	  allCharts[divName].target.bind('jqplotZoom', cuminChartZoom);
      startChartMonitor(divName);
  }
  
}  // end function drawChart   

// called on the jqplotZoom event
cuminChartZoom = function(gridpos, datapos, plot, cursor) {
//	console.log("cuminZoom");
}

//called on the jqplotResetZoom event
cuminChartResetZoom = function(gridpos, datapos, plot, cursor) {
//	console.log("cuminResetZoom");
}

// called immediately after the chart is drawn
cuminChartPostDraw = function() {
//	console.log("customPostDraw");
}

// called right before a chart is drawn
cuminChartPreDraw = function() {
//	console.log("customPreDraw");
}

// used to let us tweak the contents of the tooltip according to our whim, gets called from highlighter plugin showTooltip function
customTooltip = function(str, seriesIndex, pointIndex, plot) {
	value = plot.series[seriesIndex]._plotData[pointIndex][1];
	seriesValues = new Array();
	for(i=0; i<plot.series.length; i++) {
		series = "<tr><td>" + plot.series[i].label + ": " + plot.series[i]._plotData[pointIndex][1] + "</td></tr>";
		seriesValues.push(series);
	}
	str = str.replace(/#allSeries#/,seriesValues.join("")); 
	return str;
}

// used in axis:tickOptions:formatter to override the default axis label formatting  
function x_axis_Formatter(format, val) {
    if (typeof val == 'number') {
        if (!format) {
            format = $j.jqplot.config.defaultTickFormatString;
        }
        // when called to render a popup tooltip, the caller is named "showTooltip
        // if we don't use the ContentEditor mechanism, the name is 'g'...not sure why.  Whattup, g?
        callerName = arguments.callee.caller.getName();
        if(callerName == 'showTooltip' || callerName == 'g') {
        	var tempTime = allCharts['chartNowTime'].clone();
        	timeFormat = "%b %e, %T";
        	if(format.search(/min/) > -1) {
        		modifier = 60 * val; 
        	} else if (format.search(/day/) > -1) {
        	    modifier = 86400 * val;
        	} else if (format.search(/mo/) > -1) {
        	    modifier = 2592000 * val;
        	} else 	{
        		modifier = 3600 * val;
        	}
        	return (tempTime.increment('second', modifier).format(timeFormat));
        }
        return ($j.jqplot.sprintf(format, val)).replace(/-/,""); // hack to prevent negative axis labels, which we don't have
    }
    else {
        return String(val);
    }
}

// used in axis:tickOptions:formatter to override the default axis label formatting
y_axis_Formatter = function (format, val) {
	tickval = "";
    if (typeof val == 'number') {
        if (!format) {
            format = $j.jqplot.config.defaultTickFormatString;
        }
        if (val > 1000000) {
        	val = val / 1000000
        	format = "%.1fM";
        } else if (val > 100000) {
        	val = val / 1000
        	format = "%.1fk";
        } else if (val < 2) {
        	format = "%.2f";
        } 
        if (val == 0) {
        	format = "%d";
        }
        tickval = $j.jqplot.sprintf(format, val);
    }
    else {
        return String(val);
    }
    return tickval;
}

/*
	This function draws or updates the pie located in "piediv"
	with the given data (vals) and specified colors
*/
updatePieChart = function (piediv, vals, colors) {
	  $j.jqplot.config.enablePlugins = false;
	  var data = vals;
	  if(allCharts[piediv]) {
	  	allCharts[piediv].destroy();
	  }
	  allCharts[piediv] = jQuery.jqplot (piediv, [data],
	    {
	      grid: {
            drawBorder: false, 
            drawGridlines: false,
            background: '#ffffff',
            shadow:false
          },
	      seriesDefaults: {
	        renderer: jQuery.jqplot.PieRenderer,
	        rendererOptions: {
	          showDataLabels: false,
	          dataLabels: 'percent',
	          dataLabelThreshold: 3,
	          shadow:true,
	          shadowOffset: 1,
	          shadowAlpha: 0.06,
	          shadowDepth: 5,
	          padding:5,
	          sliceMargin:3,
	          diameter:null,
	          highlightMouseOver: false
	        }
	      },
	      legend: {show:false},
	      seriesColors: colors,
	      cursor: {show:false}, 
	    }
	  );
	}

// utility for Pie chart drawing since cumin gives us separate lists for data values and labels.
// This returns a single list of the format [[label1,data1], [labelN, dataN]]
combineValsAndLegend = function (vals, legend) {
	var index, length;
	var result = [];
	result.length = vals.length; // Helps performance in some implemenations, harmless in others
	for (index = 0, length = vals.length; index < length; ++index) {
     	result[index] = [legend[index], vals[index]];
	}
	return result;

} 	

// utility function to get the name of the function that this is called on 
Function.prototype.getName = function()
{
    if(this.name)
        return this.name;
    var definition = this.toString().split("\n")[0];
    var exp = /^function ([^\s(]+).+/;
    if(exp.test(definition))
        return definition.split("\n")[0].replace(exp, "$1") || "anonymous";
    return "anonymous";
}

