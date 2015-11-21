import htmlentitydefs as entity
import re
import logging
import math
import os
import random
import sys
import time
import struct
import urlparse

from copy import copy
from cStringIO import StringIO
from datetime import datetime, timedelta
from threading import Thread
from traceback import print_exc, print_exception
from urllib import quote, unquote_plus, unquote
from xml.sax.saxutils import escape

from parsley.collectionsex import *

quote_entities = {'"': "&quot;",
                  "'": "&#39;"}

def xml_escape(string, entities=None):
    if type(string) in (str, unicode):
        unescaped = unescape_entity(string)
        if entities is None:
            entities = quote_entities
        return escape(unescaped, entities)
    return string

def unique_id():
    # Generate 4 unsigned integers.
    # Take 4 bytes from urandom and interpret
    # them as a standard-sized ('=') unsigned long ('L').
    # Unpack returns a tuple, hence the [0].

    try:
        bits = [struct.unpack("=L", os.urandom(4))[0] for x in range(4)]
    except NotImplementedError:
        bits = [random.getrandbits(32) for x in range(4)]
        log.debug("Wooly: os.urandom raised NotImplementedError")

    return "%08x-%08x-%08x-%08x" % (bits[0], bits[1], bits[2], bits[3])

def escape_amp(string):
    return str(string).replace("&", "&amp;")

def escape_entity(string, exceptions=None):
    if not string:
        return ""
    t = ""
    ex = exceptions or list()
    for i in string:
        if ord(i) in entity.codepoint2name and \
            i not in ex:
            name = entity.codepoint2name.get(ord(i))
            t += "&" + name + ";"
        else:
            t += i
    return t

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
#   from Fredrik Lundh
#   http://effbot.org/zone/re-sub.htm#unescape-html
##
def unescape_entity(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(entity.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class Writer(object):
    def __init__(self):
        self.writer = StringIO()

    def write(self, string):
        self.writer.write(string)

    def to_string(self):
        string = self.writer.getvalue()

        self.writer.close()

        return string

class StringCatalog(object):
    def __init__(self, file):
        self.strings = None
        self.path = os.path.splitext(file)[0] + ".strings"

    def clear(self):
        self.strings = None

    def load(self):
        file = open(self.path)
        try:
            self.strings = self.parse_catalog_file(file)
        finally:
            file.close()

    def parse_catalog_file(self, file):
        strings = dict()
        key = None
        writer = Writer()

        for line in file:
            line = line.rstrip()

            if line.startswith("[") and line.endswith("]"):
                if key:
                    strings[key] = writer.to_string().strip()

                writer = Writer()

                key = line[1:-1]

                continue

            writer.write(line)
            writer.write("\r\n")

        strings[key] = writer.to_string().strip()

        return strings

    def get(self, key):
        if not self.strings:
            self.load()

        return self.strings.get(key)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.path)

class NotImplemented(Exception):
    pass
