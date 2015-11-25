package tuba.datadirect.xtvd;

import org.jdom.*;

public final class ScheduleElement extends Element {
    public ScheduleElement() {
        super("schedule");
    }

    public String getProgram() {
        return getAttributeValue("program");
    }

    public String getStation() {
        return getAttributeValue("station");
    }

    public String getTime() {
        return getAttributeValue("time");
    }

    public String getDuration() {
        return getAttributeValue("duration");
    }

    public String getHdtv() {
        return getAttributeValue("hdtv");
    }
}
