package tuba.datadirect.xtvd;

import org.jdom.*;

public final class XtvdFactory extends DefaultJDOMFactory {
    public Element element(final String name) {
        if (name == null) throw new IllegalArgumentException();

        final Element elem;

        if (name.equals("station")) {
            elem = new StationElement();
        } else if (name.equals("lineup")) {
            elem = new LineupElement();
        } else if (name.equals("map")) {
            elem = new MapElement();
        } else if (name.equals("schedule")) {
            elem = new ScheduleElement();
        } else if (name.equals("program")) {
            elem = new ProgramElement();
        } else if (name.equals("xtvd")) {
            elem = new XtvdElement();
        } else {
            elem = new Element(name);
        }

        return elem;
    }

    public Element element(final String name, final Namespace ns) {
        final Element elem = element(name);

        elem.setNamespace(ns);

        return elem;
    }
}
