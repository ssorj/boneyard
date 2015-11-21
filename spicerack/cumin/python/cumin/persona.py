#!/usr/bin/env python
import logging
import os.path
import re

try:
    import xml.etree.ElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree

log = logging.getLogger("cumin.authorize")

class CuminGroup(object):
    def __init__(self, name):
        self.name = name
        self.mainpage = "index.html"
        self.allowed = [] # which modules the group can access

class CuminPersona(object):
    def __init__(self, name, auth):
        self.name = name  # may be handy to have this here

        self.auth = auth.lower() == "true"  # should groups be checked?
        self.modules = [] # which modules are enabled
        self.mapping = {} # dictionary of CuminGroup objects

    def find_mainpage(self, group):
        return self.mapping[group].mainpage

    def lookup(self, group, module):
        try:
            if type(module) in (list, tuple):
                return len(set(module) & \
                           set(self.mapping[group].allowed)) > 0
            else:
                return module in self.mapping[group].allowed
        except KeyError:
            return False
    
class CuminPersonaMap(object):
    def __init__(self):
        log.info("Initializing %s", self.__class__.__name__)
        self.personas = {}
        self.filepath = None

    def __repr__(self):
        return ("%s %s" % ( self.__class__.__name__,  self.filepath ))

    def parse_personafile(self, filepath):
        #TODO: handle exceptions during parsing
        acctree = etree.ElementTree().parse(filepath)
        for prec in acctree.getiterator('Persona'):
            pkey = prec.attrib["name"]
            auth = prec.attrib["auth"]
            persona = CuminPersona(pkey, auth)
            self.personas[pkey] = persona     

            for pchild in prec.getchildren():
                if pchild.tag == "Module":
                    persona.modules.append(pchild.attrib["name"])
                elif pchild.tag == "GroupAccess":
                    gkey = pchild.attrib["name"]
                    group = CuminGroup(gkey)
                    persona.mapping[gkey] = group
                    for gchild in pchild.getchildren():
                        if gchild.tag == "MainPage":
                            group.mainpage = gchild.attrib["name"]
                        elif gchild.tag == "ModuleAccess":
                            if gchild.attrib["name"] == "*":
                                group.allowed.extend(persona.modules)
                            else:
                                group.allowed.append(gchild.attrib["name"])

class CuminAuthorizator(object):
    def __init__(self, app, access_path, do_authorize):
        self.app = app
        self.access_path = access_path
        log.info("Initializing %s", self)
        self.personas = CuminPersonaMap()
        self.persona = None
        self.do_authorize = do_authorize

        log.debug("Access file path is %s", access_path)
        if os.path.isdir(access_path):
            files = [os.path.join(access_path, x) \
                         for x in os.listdir(access_path)]
        elif os.path.isfile(access_path):
            files = [access_path]
        else:
            files = []
            log.error("Path '%s' for access files does not exist!" % access_path)

        for accfile in files:
            if os.path.isfile(accfile) and \
               os.path.splitext(accfile)[1] == ".xml":
                try:
                    self.personas.parse_personafile(accfile)
                except:
                    log.error("Access file '%s' does not parse!" % accfile)

    def set_persona(self, name):
        self.persona = self.personas.personas[name]

    def is_enforcing(self):
        return self.do_authorize and self.persona.auth

    def find_mainpage(self, web_session):
        # Find a main page for the current login session.
        # If user is in the admin group, prefer that one.
        # If we have multiple groups someday beyond user/admin,
        # we may have to have a priority scheme here (or find
        # a way to NOT have more than one mainpage).
        try:
            group = web_session.client_session.attributes['login_session'].group
        except KeyError:
            group = "nogroup"
        if type(group) == type([]):
            if "admin" in group:
                group = "admin"
            else:
                group = group[0]
        return self.persona.find_mainpage(group)

    def get_enabled_modules(self):
        return self.persona.modules

    def contains_valid_group(self, groups):
        for g in groups:
            if g in self.persona.mapping:
                return True
        return False

    def authorize(self, web_session, widget):
        if not hasattr(widget, "cumin_module") or \
           widget.cumin_module is None:
            # no module for this widget, we have to allow it
            return True

        # We can't logically be authorized for a module we haven't even
        # enabled!  This may occur when parts of a display have
        # associated themselves with a module explicitly.
        # (like a column in a table that is only valid if a 
        # particular module has been loaded).
        if type(widget.cumin_module) in (list, tuple):
            if len(set(widget.cumin_module) & set(self.persona.modules)) == 0:
                return False
        elif not widget.cumin_module in self.persona.modules:
            return False

        if not self.is_enforcing():
            # Auth checks against group are off.
            return True

        try:
            group = web_session.client_session.attributes['login_session'].group
        except KeyError:
            group = "nogroup"

        if type(group) == type([]):
            for g in group:
                if self.persona.lookup(g, widget.cumin_module):
                    log.debug("Allowing %s authorization for %s ",
                              widget.cumin_module, group)
                    return True
        else:
            return self.persona.lookup(group, widget.cumin_module)

        log.debug("Denying  %s authorization for %s ", widget.my_name, group)
        return False

