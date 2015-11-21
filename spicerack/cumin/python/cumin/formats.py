from datetime import datetime
from random import random
from math import floor

from util import *
from wooly import Writer

def fmt_count(count):
    return "<span class=\"count\">(%i)</span>" % count

def fmt_datetime(dtime, sec=False):
    if dtime:
        if sec:
            tstamp = dtime.strftime("%d %b %Y %H:%M:%S")
        else:
            tstamp = dtime.strftime("%d %b %Y %H:%M")
    else:
        tstamp = fmt_none()

    return tstamp

def fmt_duration(secs):
    """Takes a duration in seconds, which can be a float"""

    sign = secs < 0 and " ago" or ""
    secs = abs(secs)

    elems = list()
    periods = (86400, 3600, 60, 1)
    units = ("day", "hour", "min", "sec")

    for period, unit in zip(periods, units):
        if secs >= period:
            count = secs // period
            elems.append("%i %s%s" % (count, unit, ess(count)))

            if len(elems) == 2:
                break

        secs = secs % period

    return ", ".join(elems) + sign

def fmt_duration_brief(secs):
    """Takes a duration in seconds, which can be a float"""

    sign = secs < 0 and "-" or ""
    secs = abs(secs)

    elems = list()
    periods = (86400, 3600, 60, 1)
    units = ("d", "h", "m", "s")

    for period, unit in zip(periods, units):
        if secs >= period:
            count = secs // period
            elems.append("%i%s" % (count, unit))

            if len(elems) == 2:
                break

        secs = secs % period

    return sign + "".join(elems)

def fmt_rate(rate, unit1, unit2):
    if rate == 0:
        str = "0"
    else:
        str = "%0.2f" % float(nvl(rate, 0))

    return "%s<small>/%s</small>" % (str, unit2)

def fmt_predicate(predicate):
    return predicate and "Yes" or "No"

def fmt_status(errors, warnings, active=True):
    count = errors + warnings

    if count == 0:
        number = "&nbsp;"
    elif count > 9:
        number = "+"
    else:
        number = str(count)

    if active:
        if count == 0:
            class_ = "green"
        else:
            class_ = errors and "red" or "yellow"
    else:
        class_ = "inactive"

    return "<div class=\"statuslight %s\">%s</div>" % (class_, number)

def fmt_ostatus(object):
    errs, warns = 0, 0

    #if random() < 0.075:
    #    errs = 1

    #if random() < 0.10:
    #    warns = 1

    return fmt_status(errs, warns)

def fmt_none():
    return "<span class=\"none\">None</span>"

def fmt_none_brief():
    return "<span class=\"none\">&ndash;</span>"

def fmt_shorten(string, pre=16, post=4, spanify=True):
    if len(string) > pre + post:
        if post:
            if spanify:
                string = "<span title=\"%s\">%s</span>" % (string, string[:pre] + "&#8230;" + string[-post:])
            else:
                string = "%s" % string[:pre] + "&#8230;" + string[-post:]
        else:
            if spanify:
                string = "<span title=\"%s\">%s</span>" % (string, string[:pre] + "&#8230;")
            else:
                string = "%s" % string[:pre] + "&#8230;"
    return string

def fmt_link(href, content, class_="", id="", link_title="", bm="", click="", attribs={}):
    full_id = id and " id=\"%s\"" % id or ""
    full_bm = bm and "#%s" % bm or ""
    full_class = class_ and " class=\"%s\"" % class_ or ""
    full_title = link_title and " title=\"%s\"" % link_title or ""
    full_click = click and " onclick=\"%s\"" % click or ""
    full_attribs = " ".join(("%s=\"%s\"" % (x, attribs[x]) for x in attribs)) or ""

    return "<a%s href=\"%s%s\"%s%s%s %s>%s</a>" % \
           (full_id, href, full_bm, full_class,
            full_title, full_click, full_attribs, content)

def fmt_olink(session, object, selected=False, name=None, pre=16, post=0):
    if name is None:
        name = getattr(object, "name", fmt_none())
        # don't shorten None since it will result in
        # invalid xml
    elif isinstance(name, basestring):
        name = fmt_shorten(name, pre, post)

    return fmt_link(session.marshal(), name, selected and "selected")

def fmt_dict(value, prefix=None):
    html = """
        <tr style="border-top: 0; border-bottom: 1px dotted #CCCCCC;">
            <td style="padding:0; color: #444444;" nowrap="nowrap">%s</td>
            <td style="padding:0 0 0 1em;">%s</td>
        </tr>
    """
    writer = Writer()
    writer.write("<table style='border-collapse: collapse;'>")
    for key in value:
        show_key = key
        if prefix:
            if key.startswith(prefix):
                show_key = key[len(prefix):]
        writer.write(html % (show_key, str(value[key])))
    writer.write("</table>")
    return writer.to_string()

def fmt_bytes(num, base="B"):
    sizes = ("", "K", "M", "G", "T", "P", "Y")
    k = 1024
    which_size = 0
    b = num

    while b >= k:
        b /= k
        which_size += 1

    if which_size < len(sizes):
        if b:
            return "%0.0d%s%s" % (floor(b), sizes[which_size], base)
    return str(num)

def fmt_bits(bits):
    return fmt_bytes(bits, base="b")
