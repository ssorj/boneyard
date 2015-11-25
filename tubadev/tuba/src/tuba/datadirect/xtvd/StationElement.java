package tuba.datadirect.xtvd;

import org.jdom.*;

public final class StationElement extends Element {
    public StationElement() {
        super("station");
    }

    public String getKey() {
        return getAttributeValue("id");
    }

    public String getCallSign() {
        return getChildText("callSign", getNamespace());
    }

    public String getFccChannelNumber() {
        return getChildText("fccChannelNumber", getNamespace());
    }
}
