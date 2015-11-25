package tuba.runtime.model;

import lentil.*;
import tuba.util.*;

public final class Station extends LentilObject {
    public Station() {
        super(Station.class);

        Priority = new Integer(0);
    }

    public Long Key;
    public String SourceKey;
    public String CallSign;
    public String FccChannel;
    public String TransportFormat;
    public Integer Priority;
}
