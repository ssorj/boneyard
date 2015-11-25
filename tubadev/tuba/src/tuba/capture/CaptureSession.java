package tuba.capture;

import java.io.*;
import java.text.*;
import java.util.*;
import smoky.*;
import tuba.runtime.*;
import tuba.runtime.model.*;

public final class CaptureSession {
    private final CaptureModule m_module;
    private final Set<CaptureRequest> m_candidates;
    private final Set<CaptureRequest> m_winners;

    CaptureSession(final CaptureModule module) {
        m_module = module;
        m_candidates = new TreeSet(new TimeComparator());
        m_winners = new TreeSet(new TimeComparator());
    }

    private CaptureModule getModule() {
        return m_module;
    }

    Set<CaptureRequest> getCandidates() {
        return m_candidates;
    }

    Set<CaptureRequest> getWinners() {
        return m_winners;
    }

    public synchronized void open() {
    }

    public synchronized void close() {
        getCandidates().clear();
        getWinners().clear();
    }

    public void load() throws CaptureException {
        final TubaConnection conn = Tuba.getConnection();

        try {
            conn.open();

            CaptureRequest.loadCandidates(conn, getCandidates());
        } finally {
            conn.close();
        }
    }

    public void resolve() throws CaptureException {
        final SessionResolve resolve = new SessionResolve();

        resolve.run(this);
    }

    public void schedule() throws CaptureException {
        synchronized (getModule()) {
            getModule().getTimer().cancel();
            getModule().setTimer(new Timer());
        }

        final Date now = new Date();

        for (final CaptureRequest req : getWinners()) {
            final Date start = req.getStartTime();

            if (start.before(now)) {
                getModule().log("Skipping " + req + "; it has already begun");
            } else {
                getModule().schedule(req);
            }
        }
    }
}
