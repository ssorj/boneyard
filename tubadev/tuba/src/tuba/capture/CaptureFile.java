package tuba.capture;

import java.io.*;
import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.runtime.model.*;

// XXX stop using unix path separators
final class CaptureFile extends File {
    private CaptureFile(final File dir, final String file) {
        super(dir, file);
    }

    static CaptureFile create(final TubaConnection conn,
                                      final CaptureRequest req) {
        final StringBuilder file = new StringBuilder();

        String title = null;
        String subtitle = null;
        Date airdate = null;

        final Showing showing = req.getShowing();

        if (showing != null) {
            final Program program = new Program();

            try {
                conn.load(program, showing.ProgramKey);
            } catch (LentilObjectNotFound e) {
                throw new IllegalStateException(e);
            }

            title = program.Title;
            subtitle = program.Subtitle;
            airdate = program.OriginalAirDate;
        }

        if (title != null) {
            file.append(title);
            file.append("/");

            if (airdate == null) {
                // XXX let's see if this ever happens
                file.append("___Yikes___");
            } else {
                file.append(format(airdate));
            }

            if (subtitle != null) {
                file.append(" - ");
                file.append(subtitle);
            }

            file.append("/");
        }

        file.append("tuba.");
        file.append(req.getStationKey());
        file.append(".");
        file.append(format(req.getStartTime()));
        file.append(".stream");

        final File dir = CaptureModule.get().getRecordingsDirectory();

        return new CaptureFile(dir, file.toString());
    }

    static String format(final Date date) {
        return CaptureModule.get().getDateTimeFormat().format(date);
    }
}