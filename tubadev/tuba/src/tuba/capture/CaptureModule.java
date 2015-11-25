package tuba.capture;

import butyl.*;
import java.io.*;
import java.text.*;
import java.util.*;
import smoky.*;
import wheaty.*;
import wheaty.parameters.*;
import tuba.runtime.*;
import tuba.runtime.model.*;

public final class CaptureModule extends SmokyModule {
    private static final DateFormat s_datetime = new SimpleDateFormat
        ("yyyy-MM-dd-HH-mm-ss");
    private static final DateFormat s_date = new SimpleDateFormat
        ("yyyy-MM-dd");
    private static final DateFormat s_time = new SimpleDateFormat
        ("HH-mm-ss");

    static DateFormat getDateTimeFormat() {
        return s_datetime;
    }

    static DateFormat getDateFormat() {
        return s_date;
    }

    static DateFormat getTimeFormat() {
        return s_time;
    }

    public static CaptureModule get() {
        return (CaptureModule) Tuba.getModule("capture");
    }

    private final CaptureCommand m_command;
    private final CaptureThread m_thread;
    private final StringParameter m_adapterp;
    private final StringParameter m_recordingsp;
    private CaptureAdapter m_adapter;
    private File m_recordings;
    private Timer m_timer;

    public CaptureModule(final SmokyRuntime runtime) {
        super("capture", runtime);

        m_command = new CaptureCommand(Tuba.getCommand());
        m_thread = new CaptureThread(this);

        m_adapterp = new StringParameter("adapter");
        m_adapterp.setNullable(false);
        m_adapterp.set("tuba.dvb.DvbAdapter");

        m_recordingsp = new StringParameter("recordings_dir");
        m_recordingsp.setNullable(false);
        final File dir = new File
            (getRuntime().getHomeDirectory(), "recordings");
        m_recordingsp.set(dir.getPath());

        getModel().addParameter(m_adapterp);
        getModel().addParameter(m_recordingsp);
    }

    protected void initialize(final WheatySession session) {
        m_adapter = (CaptureAdapter)
            ReflectFunctions.newInstance((String) m_adapterp.get(session));

        m_recordings = new File((String) m_recordingsp.get(session));
    }

    protected void startup() {
        if (m_timer != null) throw new IllegalStateException();

        getThread().start();

        m_timer = new Timer("capture-timer");
    }

    protected void shutdown() {
        if (m_timer == null) throw new IllegalStateException();

        m_timer.cancel();
        m_timer = null;

        getThread().stop();
    }

    public CaptureSession getSession() {
        return new CaptureSession(this);
    }

    Timer getTimer() {
        return m_timer;
    }

    void setTimer(final Timer timer) {
        m_timer = timer;
    }

    CaptureThread getThread() {
        return m_thread;
    }

    CaptureAdapter getAdapter() {
        return m_adapter;
    }

    public File getRecordingsDirectory() {
        return m_recordings;
    }

    public CaptureCommand getCommand() {
        return m_command;
    }

    // XXX why do we have to use the worker thread here?
    void schedule(final CaptureRequest req) {
        log("Scheduling " + req + " for capture");

        final TimerTask task = new TimerTask() {
                public void run() {
                    CaptureModule.this.getThread().send(req);
                }
            };

        getTimer().schedule(task, req.getStartTime());
    }

    void capture(final CaptureRequest req) {
        final TubaConnection conn = Tuba.getConnection();
        final Recording rec = new Recording();
        final File file;

        try {
            conn.open();

            conn.setNewKey(rec);

            file = CaptureFile.create(conn, req);
        } finally {
            conn.close();
        }

        final File tmp = new File(file.getPath() + ".part");

        if (file.exists()) {
            throw new IllegalStateException
                ("File '" + file.getPath() + "' already exists");
        }

        if (tmp.exists()) {
            throw new IllegalStateException
                ("File '" + tmp.getPath() + "' already exists");
        }

        tmp.getParentFile().mkdirs();

        try {
            tmp.createNewFile();
        } catch (IOException e) {
            throw new IllegalStateException("Failed creating output file", e);
        }

        log("Capturing " + req);

        try {
            getAdapter().capture(0, req.getCallSign(), req.getEndTime(), tmp);
        } catch (Exception e) {
            log(e);
            log("Failed capturing " + req);
            return;
        }

        log("Finished capturing " + req);

        if (!tmp.renameTo(file)) {
            log("Failed renaming file '" + tmp + "' to '" + file + "'");
        }

        try {
            conn.open();

            req.toRecording(conn, rec);

            conn.setWriteEnabled(true);

            if (conn.insert(rec) == 0) {
                throw new IllegalStateException();
            }

            conn.commit();
        } finally {
            conn.close();
        }
    }
}
