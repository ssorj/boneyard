import sys
import os
import logging
import string
import select

from crypt import crypt
from datetime import datetime, timedelta
from qpid.datatypes import uuid4
from pprint import *
from random import randint
from random import sample
from threading import Thread, Event
from time import mktime, time, sleep
from parsley.threadingex import print_threads
from wooly.util import xml_escape

def short_id():
    return "%08x" % randint(0, sys.maxint)

def sorted_by(seq, attr="name"):
    return sorted_by_attr(seq, attr)

def sorted_by_attr(seq, attr):
    return sorted(seq, cmp, lambda x: getattr(x, attr))

def sorted_by_index(seq, index):
    return sorted(seq, cmp, lambda x: x[index])

def ess(num, ending="s"):
    return num != 1 and ending or ""

def plural(noun):
    # XXX handle exceptions here
    return "%ss" % noun

def conjugate(noun, count):
    if count != 1:
        noun = plural(noun)

    return noun

def nvl(expr1, expr2):
    if expr1 == None:
        return expr2
    else:
        return expr1

def calc_rate(curr, prev, csecs, psecs):
    if None not in (curr, prev, csecs, psecs):
        secs = csecs - psecs
        if secs > 0:
            return (curr - prev) / float(secs)

def secs(dt):
    if dt is not None:
        return mktime(dt.timetuple())

def parse_broker_addr(string):
    addr = string.split(":")

    if len(addr) > 1:
        host, port = addr[0], int(addr[1])
    else:
        host, port = addr[0], 5672

    return host, port

def is_active(obj):
    delTime = obj._get_qmfDeleteTime()
    if not delTime and obj.statsCurr:
        updateTime = obj.statsCurr.qmfUpdateTime
        delta = timedelta(minutes=10)
        # mirroring logic in widgets/PhaseSwitch.get_sql_constraint
        if not updateTime or (updateTime > datetime.now() - delta):
            return True

class Identifiable(object):
    def __init__(self, id=None):
        self.id = id

def convertStr(s):
    """Convert string to either int or float."""
    try:
        ret = int(s)
    except ValueError:
        try:
            ret = float(s)
        except ValueError:
            ret = None
    return ret

def wait(predicate, timeout=30, args=None):
    start = time()

    while True:
        if args is not None:
            if predicate(args):
                return True
        else:
            if predicate():
                return True

        if time() - start > timeout:
            return False

        sleep(1)

password_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def crypt_password(password, salt=None):
    if not salt:
        salt = "".join(sample(password_chars, 2))

    return crypt(password, salt)

def parse(text, begin_delim="{", end_delim="}"):
    strings = list()

    start = 0
    end = text.find(begin_delim)

    while True:
        if (end == -1):
            strings.append(text[start:])
            break

        strings.append(text[start:end])

        ccurly = text.find(end_delim, end + 1)

        if ccurly == -1:
            start = end
            end = -1
        else:
            ocurly = text.find(begin_delim, end + 1)

            if ocurly == -1:
                start = end
                end = ccurly + 1
            elif ocurly < ccurly:
                start = end
                end = ocurly
            else:
                strings.append(begin_delim + text[end + 1:ccurly] + end_delim)

                start = ccurly + 1
                end = ocurly

    return strings

def strip_string_quotes(value):
    dvalue = value
    if value:
        if value[:1] == "\"" and value[-1:] ==  "\"":
            dvalue = value[1:-1]
    return dvalue

class JobStatusInfo(object):
    stat_strings = ["Unexpanded", "Idle", "Running", "Removed", "Completed", 
                    "Held", "Transferring", "Suspended", "Submission error"]
    stat_colors = ["red", "clear", "green", "black", "blue", 
                   "yellow", "green", "yellow", "red"]
    @classmethod
    def get_status_string(cls, stat):
        # Allow strings to be passed in for flexibility.
        # Enforcing cumin case should make strings
        # match stat_strings for expected values
        if type(stat) in (str, unicode):
            return string.capitalize(stat)
        else:    
            try:
                return cls.stat_strings[stat]
            except:
                return "Unrecognized"

    @classmethod
    def get_status_color(cls, stat):
        try:
            return cls.stat_colors[stat]
        except:
            return "red"

    @classmethod
    def get_status_int(cls, stat):
        try:
            return cls.stat_strings.index(stat)
        except:
            return -1

    @classmethod
    def get_zipped_colors(cls):
        return zip(cls.stat_strings, cls.stat_colors)

def cursor_to_rows(cursor):
    cols = [spec[0] for spec in cursor.description]
    rows = list()

    for tuple in cursor:
        row = dict()
        for col, datum in zip(cols, tuple):
            row[col] = datum

        rows.append(row)

    return rows

def check_for_options(options,search):
    """
    Simple option checking.

    This is a rudimentary option checker that handles option strings of the form
    'option=value' or 'option'.

    The options parameter is a list of items for which to check.  The search
    parameter is a list of strings to match against the options list.

    A dictionary will be returned keyed on the elements of options.
    If an option is not found in the search list, its value in the dictionary
    will be None.  If it is found, its value will be True if the search list
    contains a string of the form 'option' or everything following '=' if the
    form is 'option=value'

    """
    result = dict()
    for opt in options:
        result[opt] = None
        for arg in search:
            if arg.find(opt) == 0:
                rem = arg[len(opt):]
                if rem != "" and rem[0] == "=":
                    result[opt] = rem[1:]
                else:
                    result[opt] = True
    return result

def rgb_to_string(r, g, b):
    hr, hg, hb = [hex(min(int(n*255), 255))[2:] for n in(r, g, b)]
    hList = []

    for n in (hr, hg, hb):
        hList.append(n.rjust(2, '0').upper())

    return "".join(hList)

def truncate_text(text, length, indicator):
    ''' Quick truncation of text at specified length
    
        text:  the text to be truncated
        length:  the length at which to truncate the text
        indicator:  If true, add "..." to the truncated text to indicate that truncation happened
    '''
    retval = len(text) > 0 and text or ""
    if(len(retval) > length):
        retval = retval[:length] 
        if indicator:
            retval = retval + "..."
    return retval

def poll_stdin(timeout=5, value=""):
    '''
    Use select() to poll for input on sys.stdin.  Return
    True if there is input and it matches value.

    timeout - seconds, how long to block for input
    value - compare the input string to this value.
            If value is "", all strings match.
    '''
    r, w, e = select.select([sys.stdin], [], [], timeout)
    if r:
        if value != "":
            a = raw_input()
            return a == value
        return True
    return False

class ShutdownThread(Thread):
    def __init__(self, routine):
        super(ShutdownThread, self).__init__()

        self.routine = routine
        self.daemon = True

    def run(self):
        # We know that ShutdwonThreads by nature may not
        # terminate, and the app may exit underneath them.
        # Try to squash exceptions here in the case of a 
        # timeout.
        try:
            self.routine()
        except:
            pass
