package tuba.datadirect;

import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.runtime.model.*;
import tuba.datadirect.xtvd.*;

final class SessionSave {
    void run(final TubaConnection conn, final XtvdElement xtvd) {
        final Map stationKeys = new HashMap();
        final Iterator stations = xtvd.getStations().iterator();

        while (stations.hasNext()) {
            final StationElement elem = (StationElement) stations.next();
            final Station station = new Station();

            try {
                conn.load(station, "SourceKey", elem.getKey());
            } catch (LentilObjectNotFound e) {
                conn.setNewKey(station);
            }

            station.SourceKey = elem.getKey();
            station.CallSign = elem.getCallSign();
            station.FccChannel = elem.getFccChannelNumber();

            conn.save(station);

            stationKeys.put(station.SourceKey, station.Key);
        }

        final Map programKeys = new HashMap();
        final Iterator programs = xtvd.getPrograms().iterator();

        while (programs.hasNext()) {
            final ProgramElement elem = (ProgramElement) programs.next();
            final Program program = new Program();

            try {
                conn.load(program, "SourceKey", elem.getKey());
            } catch (LentilObjectNotFound e) {
                conn.setNewKey(program);
            }

            program.SourceKey = elem.getKey();
            program.Title = elem.getTitle();
            program.Subtitle = elem.getSubtitle();
            program.Description = elem.getDescription();

            final String date = elem.getOriginalAirDate();

            if (date != null) {
                program.OriginalAirDate = Formats.parseDate(date);
            }

            if (elem.getSeries() != null) {
                final Series series = new Series();

                try {
                    conn.load(series, "SourceKey", elem.getSeries());
                } catch (LentilObjectNotFound e2) {
                    conn.setNewKey(series);
                }

                series.SourceKey = elem.getSeries();
                series.Title = program.Title;

                conn.save(series);

                program.SeriesKey = series.Key;
            }

            conn.save(program);

            programKeys.put(program.SourceKey, program.Key);
        }

        conn.delete(Showing.class);

        final Iterator schedules = xtvd.getSchedules().iterator();

        while (schedules.hasNext()) {
            final ScheduleElement elem = (ScheduleElement) schedules.next();
            final Showing showing = new Showing();

            showing.ProgramKey = (Long) programKeys.get(elem.getProgram());
            showing.StationKey = (Long) stationKeys.get(elem.getStation());
            showing.StartTime = Formats.parseTime(elem.getTime());

            final long duration = Formats.parseDuration(elem.getDuration());
            showing.EndTime = new Date(showing.StartTime.getTime() + duration);

            if ("true".equals(elem.getHdtv())) {
                showing.ContentFormat = "hd";
            } else {
                showing.ContentFormat = "sd";
            }

            conn.insert(showing);
        }
    }
}
