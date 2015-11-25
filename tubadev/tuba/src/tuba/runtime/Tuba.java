package tuba.runtime;

import java.io.*;
import java.util.*;
import java.text.*;
import smoky.*;
import wheaty.*;

public final class Tuba {
    private static final DateFormat s_time = new SimpleDateFormat
        ("yyyy-MM-dd-HH-mm-ss");
    private static final DateFormat s_date = new SimpleDateFormat
        ("yyyy-MM-dd");

    private static TubaRuntime s_runtime = new TubaRuntime();

    // XXX Should this go inside initialize()?
    static {
        final List modules = new ArrayList();

        modules.add("tuba.runtime.RuntimeModule");
        modules.add("tuba.update.UpdateModule");
        modules.add("tuba.datadirect.DataDirectModule");
        modules.add("tuba.capture.CaptureModule");
        modules.add("tuba.dvb.DvbModule");

        Tuba.getRuntime().load(modules);
    }

    public static TubaCommand getCommand() {
        return RuntimeModule.getModule().getCommand();
    }

    public static TubaRuntime getRuntime() {
        return s_runtime;
    }

    public static File getHomeDirectory() {
        return Tuba.getRuntime().getHomeDirectory();
    }

    public static SmokyModule getModule(final String name) {
        return Tuba.getRuntime().getModule(name);
    }

    public static SmokyConfig getConfig() {
        return Tuba.getRuntime().getConfig();
    }

    public static TubaConnection getConnection() {
        return RuntimeModule.getModule().getConnection();
    }

    public static DateFormat getTimeFormat() {
        return s_time;
    }

    public static DateFormat getDateFormat() {
        return s_date;
    }
}
