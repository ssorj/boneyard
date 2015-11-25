package tuba.datadirect.xtvd;

import org.jdom.*;

public final class MapElement extends Element {
    public MapElement() {
        super("map");
    }

    public String getStation() {
        return getAttributeValue("station");
    }

    public String getChannel() {
        return getAttributeValue("channel");
    }
}
