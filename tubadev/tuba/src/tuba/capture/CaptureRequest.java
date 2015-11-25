package tuba.capture;

import java.io.*;
import java.text.*;
import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.runtime.model.*;
import tuba.util.*;

final class CaptureRequest {
    private static final StringCatalog s_sql = new StringCatalog
        (CaptureRequest.class, "CaptureRequest.sql");

    private static final DateFormat s_start = new SimpleDateFormat
        ("EEE-HH:mm");
    private static final DateFormat s_end = new SimpleDateFormat
        ("HH:mm");

    private Long m_program;
    private Long m_station;
    private Date m_start;
    private Date m_end;

    // XXX temporary
    private String m_callsign;

    private final Set<CaptureRequest> m_conflicts;
    private final Set<CaptureRequest> m_repeats;
    private Showing m_showing;
    private CaptureRequest m_superior;
    private int m_priority;

    CaptureRequest() {
        m_conflicts = new HashSet();
        m_repeats = new HashSet();
    }

    Long getProgramKey() {
        return m_program;
    }

    void setProgramKey(final Long key) {
        m_program = key;
    }

    Long getStationKey() {
        return m_station;
    }

    void setStationKey(final Long key) {
        m_station = key;
    }

    Date getStartTime() {
        return m_start;
    }

    void setStartTime(final Date start) {
        m_start = start;
    }

    Date getEndTime() {
        return m_end;
    }

    void setEndTime(final Date end) {
        m_end = end;
    }

    String getCallSign() {
        return m_callsign;
    }

    void setCallSign(final String callsign) {
        m_callsign = callsign;
    }

    Set<CaptureRequest> getConflicts() {
        return m_conflicts;
    }

    Set<CaptureRequest> getRepeats() {
        return m_repeats;
    }

    Showing getShowing() {
        return m_showing;
    }

    void setShowing(final Showing showing) {
        m_showing = showing;
    }

    CaptureRequest getSuperior() {
        return m_superior;
    }

    void setSuperior(final CaptureRequest superior) {
        m_superior = superior;
    }

    int getPriority() {
        return m_priority;
    }

    void setPriority(final int priority) {
        m_priority = priority;
    }

    boolean isRepeat(final CaptureRequest req) {
        return m_program.equals(req.m_program);
    }

    public String toString() {
        return getStationKey() +
            "-" + s_start.format(getStartTime()) +
            "-" + s_end.format(getEndTime()) +
            "-" + getPriority();
    }

    static void loadCandidates(final TubaConnection conn,
                               final Collection candidates) {
        final String sql = s_sql.get("load_candidates");

	final LentilCursor cursor = conn.read(sql);

	for (int i = 0; cursor.next(); i++) {
	    final Showing showing = new Showing();
	    showing.load(cursor);

            final CaptureRequest req = new CaptureRequest();

            // XXX say don't do this and save memory, eh?
            req.setShowing(showing);

            req.setProgramKey(showing.ProgramKey);
            req.setStationKey(showing.StationKey);
            req.setStartTime(showing.StartTime);
            req.setEndTime(showing.EndTime);

            // XXX temporary
            req.setCallSign((String) cursor.getObject("call_sign"));

            {
                int prio = 0;

                final Integer sprio = (Integer) cursor.getObject
                    ("series_priority");
                if (sprio != null) prio += sprio.intValue();

                final Integer pprio = (Integer) cursor.getObject
                    ("program_priority");
                prio += pprio.intValue();

                req.setPriority(prio);
            }

	    candidates.add(req);
	}

	cursor.close();
    }

    // This expects a recording with its key already set
    void toRecording(final TubaConnection conn, final Recording rec) {
        rec.StartTime = getStartTime();
        rec.EndTime = getEndTime();

        final Showing showing = getShowing();

        if (showing != null) {
            final Program program = new Program();

            try {
                conn.load(program, showing.ProgramKey);
            } catch (LentilObjectNotFound e) {
                throw new IllegalStateException(e);
            }

            rec.Title = program.Title;
            rec.Subtitle = program.Subtitle;
            rec.Description = program.Description;
            rec.OriginalAirDate = program.OriginalAirDate;
            rec.ProgramSourceKey = program.SourceKey;
            rec.ProgramChecksum = program.Checksum;
            rec.ContentFormat = showing.ContentFormat;

            final Station station = new Station();

            try {
                conn.load(station, showing.StationKey);
            } catch (LentilObjectNotFound e) {
                throw new IllegalStateException(e);
            }

            rec.CallSign = station.CallSign;
            rec.TransportFormat = station.TransportFormat;
        }
    }
}