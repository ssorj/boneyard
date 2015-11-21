# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# Author: Eugene Kin Chee Yip
# Date:   14 June 2009

# Modified to not require cjson or json by Ernie
CJSON = False
JJSON = False
try:
    import cjson
    CJSON = True
except ImportError:
    try:
        import json
        JJSON = True
    except ImportError:
        pass
import    copy

class Chart(dict):
    # Dictionary for replacing attribute names
    replaceKeyDictionary =    {
        "on_show": "on-show",            "on_click": "on-click", "on_click_text": "on-click-text",
        "start_angle": "start-angle",
        
        "threeD": "3d",                    "tick_height": "tick-height",
        "grid_colour": "grid-colour",    "tick_length": "tick-length",
    
        "dot_style": "dot-style",        "dot_size": "dot-size",
        "halo_size": "halo-size",
            
        "line_style": "line-style",        "outline_colour": "outline-colour",
        "fill_alpha": "fill-alpha",        "gradient_fill": "gradient-fill",
        "visible_steps": "visible-steps",
    }

    # Redefine to allow for nested attributes.
    # E.g. when calling the leaf attribute, text, in chart.title.text
    #      without previously defining the branch attribute, title.
    def __getattribute__(self, key):
        try:
            return dict.__getattribute__(self, key)
        except AttributeError:
            self.__dict__[key] = Chart()
            return dict.__getattribute__(self, key)

    # This copy function is called when we want to get all the attributes of the 
    # chart instance so we can pass it off to cjson to create the JSON string.
    # Recursive trick to get leaf attributes.  Have to be careful of list types.
    # Also, replace certain underscored keys.
    # E.g. getting the leaf attribute, text, from the parent Chart instance where a  
    #      previous assignment was to chart.title.text
    def __copy__(self):
        attributes = dict()
        for key, value in self.__dict__.items():
            if isinstance(value, list):
                attributes[self.replaceKey(key)] = [copy.copy(item) for item in value]
            else:
                attributes[self.replaceKey(key)] = copy.copy(value)
        return attributes

    # If key has an underscore, replace with a dash.
    # Python does not allow dash in object names.
    def replaceKey(self, key):
        if (key in self.replaceKeyDictionary):
            return self.replaceKeyDictionary[key]
        else:
            return key

    # Encode the chart attributes as JSON
    def create(self):
        attributes = copy.copy(self)
        if CJSON:
            return cjson.encode(attributes)
        elif JJSON:
            return json.dumps(attributes)
        else:
            return str(attributes).\
                replace("': u'", "': '")

class Element(Chart):
    pass