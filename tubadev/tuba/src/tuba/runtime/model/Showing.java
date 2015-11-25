package tuba.runtime.model;

import java.text.*;
import java.util.*;
import lentil.*;
import tuba.util.*;

public final class Showing extends LentilObject {
    public Showing() {
        super(Showing.class);
    }

    public Long ProgramKey;
    public Long StationKey;
    public Date StartTime;
    public Date EndTime;
    public String ContentFormat;
}
