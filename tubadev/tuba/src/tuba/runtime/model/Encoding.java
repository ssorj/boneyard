package tuba.runtime.model;

import java.io.*;
import java.text.*;
import java.util.*;
import lentil.*;
import org.jdom.*;
import tuba.runtime.*;
import tuba.util.*;

public final class Encoding extends LentilObject {
    private static final DateFormat s_start = new SimpleDateFormat
        ("EEE-HH:mm");
    private static final DateFormat s_end = new SimpleDateFormat
        ("HH:mm");
    //    private static final StringCatalog s_sql = new StringCatalog
    //        (Encoding.class, "Encoding.sql");

    public Encoding() {
        super(Encoding.class);
    }

    public Long Key;
    public Long RecordingKey;
    public String Filename;

    private File m_file;

    public File getFile() {
        return m_file;
    }

    public void setFile(final File file) {
        m_file = file;
    }
}
