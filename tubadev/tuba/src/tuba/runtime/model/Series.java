package tuba.runtime.model;

import lentil.*;
import tuba.util.*;

public final class Series extends LentilObject {
    public Series() {
        super(Series.class);

        Priority = new Integer(-1);
    }

    public Long Key;
    public String SourceKey;
    public String Title;
    public Integer Priority;
}
