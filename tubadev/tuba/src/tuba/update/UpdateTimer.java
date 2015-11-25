package tuba.update;

import java.util.*;

final class UpdateTimer extends Timer {
    private final UpdateModule m_module;

    UpdateTimer(final UpdateModule module) {
        super("update-timer");

        m_module = module;
    }

    private UpdateModule getModule() {
        return m_module;
    }

    void schedule() {
        final Date time = getLateTime();

        getModule().log("Scheduling update for " + time);

        // XXX reuse an UpdateTask object?
        schedule(new UpdateTask(), time);
    }

    private final class UpdateTask extends TimerTask {
        public void run() {
            UpdateTimer.this.getModule().getThread().send(new Object());
            UpdateTimer.this.schedule();
        }
    }

    private static Date getLateTime() {
        final Calendar cal = Calendar.getInstance();
        final Date now = cal.getTime();

        cal.set(Calendar.HOUR_OF_DAY, 2);
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);

        if (cal.getTime().before(now)) {
            cal.add(Calendar.DAY_OF_MONTH, 1);
        }

        if (cal.getTime().before(now)) {
            throw new IllegalStateException();
        }

        // We aim for some time, randomly chosen, between 2 and 6
        // o'clock in the morning.  This is so that we go easy on the
        // listing provider's servers.

        final int secs = (int) Math.round(Math.random() * 60 * 60 * 4);

        cal.add(Calendar.SECOND, secs);

        return cal.getTime();
    }
}