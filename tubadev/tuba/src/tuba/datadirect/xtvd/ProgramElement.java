package tuba.datadirect.xtvd;

import org.jdom.*;

public final class ProgramElement extends Element {
    public ProgramElement() {
        super("program");
    }

    public String getKey() {
        return getAttributeValue("id");
    }

    public String getTitle() {
        return getChildText("title", getNamespace());
    }

    public String getSubtitle() {
        return getChildText("subtitle", getNamespace());
    }

    public String getDescription() {
        return getChildText("description", getNamespace());
    }

    public String getOriginalAirDate() {
        return getChildText("originalAirDate", getNamespace());
    }

    public String getSeries() {
        return getChildText("series", getNamespace());
    }
}
