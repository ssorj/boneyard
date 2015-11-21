import logging
import os
import sys

from pprint import pprint
from cumin.formats import *

try:
    from xml.etree.ElementTree import *
except ImportError:
    from elementtree.ElementTree import *

def fmt_exchange_name(value):
    return value and value or "Default exchange"

def fmt_kbmb(value):
    return fmt_bytes(value * 1024)

def fmt_timestamp_ddhhmmss(value):
    days = value / 86400
    hours = (value / 3600) - (days * 24)
    minutes = (value / 60) - (days * 1440) - (hours * 60)
    return '%02d:%02d:%02d' % (days, hours, minutes)