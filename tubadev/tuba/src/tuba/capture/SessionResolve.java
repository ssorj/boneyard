package tuba.capture;

import java.text.*;
import java.util.*;
import tuba.runtime.model.*;

final class SessionResolve {
    //private static final DecimalFormat s_nf = new DecimalFormat("0000");
    private static final boolean s_debug = false;

    private static String toString(final CaptureRequest req) {
        final String string;
        final CaptureRequest sup = req.getSuperior();

        if (sup == null) {
            string = String.valueOf(req.hashCode());
        } else {
            string = req.hashCode() + " " + "(" + sup.hashCode() + ")";
        }

        return string;
    }

    private void debug(final String message) {
        if (s_debug) {
            System.out.println(message);
        }
    }

    private void debug(final String message, final CaptureRequest req) {
        if (s_debug) {
            System.out.println(message + " " + toString(req));
        }
    }

    void run(final CaptureSession session) throws CaptureException {
        final Set<CaptureRequest> reqs = session.getCandidates();

        if (s_debug) {
            for (final CaptureRequest req : reqs) {
                System.out.println(toString(req) + " " + req);
            }
        }

        loadConflicts(reqs);
        loadRepeats(reqs);

        if (s_debug) {
            printRequests("Recordings before mapping edits", reqs);
        }

        final Set candidates = new TreeSet(new PriorityComparator());
        candidates.addAll(reqs);

        final Set winners = session.getWinners();
        final Set repeats = new HashSet();
        final Set conflicts = new HashSet();

        cull(candidates, winners, repeats, conflicts);
    }

    // Expects a time-ordered set of reqs
    private void loadConflicts(final Set<CaptureRequest> reqs) {
        final LinkedList window = new LinkedList();

        for (final CaptureRequest req : reqs) {
            final Iterator iter = window.iterator();

            while (iter.hasNext()) {
                final CaptureRequest prior = (CaptureRequest) iter.next();

                final Date end = new Date(prior.getEndTime().getTime() - 1);

                if (end.before(req.getStartTime())) {
                    iter.remove();
                } else {
                    prior.getConflicts().add(req);
                    req.getConflicts().add(prior);
                }
            }

            window.addLast(req);
        }
    }

    // XXX Make this faster with a program-ordered set, similar to
    // loadConflicts
    private void loadRepeats(final Set<CaptureRequest> reqs) {
        for (final CaptureRequest req : reqs) {
            for (final CaptureRequest ireq : reqs) {
                if (!ireq.equals(req)) {
                    if (req.isRepeat(ireq)) {
                        req.getRepeats().add(ireq);
                        ireq.getRepeats().add(req);
                    }
                }
            }
        }
    }

    // Flaw: This will schedule more than one req of the
    // same program.  IE, it does not eliminate repeat showings as it
    // picks winners
    //
    // Since fixed.  The earliest, highest-priority showing of a set
    // of repeats is a winner; the rest lose.

    // Requires a priority-ordered set of requests

    // Note that repeats are *winner* repeats.  There are still
    // repeats in the conflicts set, which would get picked up in
    // subsequent calls to cull
    private void cull(final Set<CaptureRequest> reqs,
                      final Set<CaptureRequest> winners,
                      final Set<CaptureRequest> repeats,
                      final Set<CaptureRequest> conflicts) {
        for (final CaptureRequest req : reqs) {
            if (repeats.contains(req) || conflicts.contains(req)) {
                debug("Loser", req);

                if (winners.contains(req)) {
                    throw new IllegalStateException
                        ("Loser " + req + " is also in the winner set");
                }
            } else {
                debug("Winner", req);

                // Winners are those that haven't lost already
                winners.add(req);

                final Iterator riter = req.getRepeats().iterator();

                while (riter.hasNext()) {
                    final CaptureRequest repeat = (CaptureRequest) riter.next();
                    riter.remove();
                    repeat.getRepeats().remove(req);

                    // Each repeat is a loser
                    repeats.add(repeat);
                    repeat.setSuperior(req);

                    debug("  Versus repeat", repeat);
                }

                final Iterator citer = req.getConflicts().iterator();

                while (citer.hasNext()) {
                    final CaptureRequest conflict = (CaptureRequest) citer.next();
                    citer.remove();
                    conflict.getConflicts().remove(req);

                    // Each conflict is a loser
                    conflicts.add(conflict);
                    conflict.setSuperior(req);

                    debug("  Versus conflict", conflict);
                }
            }
        }

        // Repeat-ness trumps Conflict-ness, and we want the sets to
        // be exclusive, so remove all conflicts that are already
        // represented in repeats and fix up pointers

        Iterator iter = conflicts.iterator();

        while (iter.hasNext()) {
            final CaptureRequest conflict = (CaptureRequest) iter.next();

            if (repeats.contains(conflict)) {
                iter.remove();

                final Iterator citer = conflict.getConflicts().iterator();

                while (citer.hasNext()) {
                    final CaptureRequest cconflict = (CaptureRequest) citer.next();
                    citer.remove();
                    cconflict.getConflicts().remove(conflict);
                }
            }
        }

        // XXX I think I need to fix up repeat pointers here too

        if (s_debug) {
            System.out.println("Superset: " + reqs.size());
            System.out.println("Winners: " + winners.size());
            System.out.println("Repeats: " + repeats.size());
            System.out.println("Conflicts: " + conflicts.size());

            printRequests("Winners", winners);
            printRequests("Repeats", repeats);
            printRequests("Conflicts", conflicts);

            for (final CaptureRequest req : reqs) {
                if (winners.contains(req)) continue;
                if (repeats.contains(req)) continue;
                if (conflicts.contains(req)) continue;

                throw new IllegalStateException
                    ("CaptureRequest " + req + " got left behind");
            }

            checkDisjoint(winners, repeats);
            checkDisjoint(winners, conflicts);
            checkDisjoint(repeats, conflicts);

            checkSubset(reqs, winners);
            checkSubset(reqs, repeats);
            checkSubset(reqs, conflicts);
        }

        if (winners.size() + repeats.size() + conflicts.size() != reqs.size()) {
            throw new IllegalStateException
                ("Culled results don't add up");
        }
    }

    private static void printRequests(final String header, final Set reqs) {
        final Iterator iter = reqs.iterator();

        System.out.println(header);

        while (iter.hasNext()) {
            final CaptureRequest req = (CaptureRequest) iter.next();

            System.out.print("  " + req);
            System.out.print(" " + req.getRepeats());
            System.out.print(" " + req.getConflicts());
            System.out.println();
        }
    }

    private static void checkDisjoint(final Set set1, final Set set2) {
        final Iterator iter = set1.iterator();

        while (iter.hasNext()) {
            if (set2.contains(iter.next())) throw new IllegalStateException();
        }
    }

    private static void checkSubset(final Set set1, final Set set2) {
        if (!set1.containsAll(set2)) throw new IllegalStateException();
    }
}

// For multi-tuner stuff later on

//         Set showings = new TreeSet(new PriorityComparator());
//         showings.addAll(rshowings);

//         for (Object object : showings) {
//             System.out.println(object);
//         }

//         for (int i = 1; showings.size() > 0; i++) {
//             final Set winners = new TreeSet(new PriorityComparator());
//             final Set losers = new TreeSet(new PriorityComparator());

//             System.out.println("Round " + i + " " + showings.size());

//             cull(showings, winners, losers);

//             for (Showing sh : (Set<Showing>) winners) {
//                 System.out.println(sh + "  " + sh.getConflicts());
//             }

//             showings = losers;
//         }
