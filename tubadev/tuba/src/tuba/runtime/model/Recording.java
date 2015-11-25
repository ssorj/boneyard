package tuba.runtime.model;

import java.io.*;
import java.text.*;
import java.util.*;
import lentil.*;
import org.jdom.*;
import tuba.runtime.*;
import tuba.util.*;

public final class Recording extends LentilObject {
    private static final DateFormat s_start = new SimpleDateFormat
        ("EEE-HH:mm");
    private static final DateFormat s_end = new SimpleDateFormat
        ("HH:mm");

    public Recording() {
        super(Recording.class);
    }

    public Long Key;
    public String Filename;
    public String Title;
    public String Subtitle;
    public String Description;
    public Date OriginalAirDate;
    public String ProgramSourceKey;
    public String ProgramChecksum;
    public Date StartTime;
    public Date EndTime;
    public String CallSign;
    public String TransportFormat;
    public String ContentFormat;

    public String toString() {
        return CallSign +
            "-" + s_start.format(StartTime) +
            "-" + s_end.format(EndTime);
    }
}
