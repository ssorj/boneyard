package tuba.runtime;

import java.io.*;
import java.util.*;
import smoky.*;

public final class TubaRuntime extends SmokyRuntime {
    private File m_data;
    private File m_lib;

    TubaRuntime() {
        super("tuba");

        final File home = new File(System.getenv("TUBA_HOME"));

        setHomeDirectory(home);
        setConfigDirectory(new File(home, "conf"));
        setLogDirectory(new File(home, "log"));

        m_data = new File(home, "data");
        m_lib = new File(home, "lib");
    }

    public final File getDataDirectory() {
        return m_data;
    }

    public final File getLibDirectory() {
        return m_lib;
    }
}