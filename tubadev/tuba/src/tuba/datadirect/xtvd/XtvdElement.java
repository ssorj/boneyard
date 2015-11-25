package tuba.datadirect.xtvd;

import java.util.*;
import org.jdom.*;

public final class XtvdElement extends Element {
    public XtvdElement() {
        super("xtvd");
    }

    public String getFrom() {
        return getAttribute("from", getNamespace()).getValue();
    }

    public String getTo() {
        return getAttribute("to", getNamespace()).getValue();
    }

    public List getStations() {
        return getChild("stations", getNamespace()).getChildren
            ("station", getNamespace());
    }

    public List getLineups() {
        return getChild("lineups", getNamespace()).getChildren
            ("lineup", getNamespace());
    }

    public List getSchedules() {
        return getChild("schedules", getNamespace()).getChildren
            ("schedule", getNamespace());
    }

    public List getPrograms() {
        return getChild("programs", getNamespace()).getChildren
            ("program", getNamespace());
    }
}
