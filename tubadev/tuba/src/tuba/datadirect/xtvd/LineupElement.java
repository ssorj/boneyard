package tuba.datadirect.xtvd;

import java.util.*;
import org.jdom.*;

public final class LineupElement extends Element {
    public LineupElement() {
        super("lineup");
    }

    public String getKey() {
        return getAttributeValue("id");
    }

    public List getMaps() {
        return getChildren("map", getNamespace());
    }
}
