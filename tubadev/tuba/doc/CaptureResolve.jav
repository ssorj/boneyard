package tuba.capture;

import java.util.*;
import tuba.data.*;

final class CaptureResolve {
    private boolean m_debug = true;

    private void debug(final String message) {
        if (m_debug) {
            System.out.println(message);
        }
    }

    Set run(final CaptureSession session, final Set recs)
            throws CaptureException {
        loadConflicts(recs);
        loadRepeats(recs);

        final Set prioritized = new TreeSet(new PriorityComparator());
        prioritized.addAll(recs);

        final Set winners = new TreeSet(new TimeComparator());
        final Set repeats = new HashSet();
        final Set conflicts = new HashSet();

        cull(prioritized, winners, repeats, conflicts);

        return winners;
    }

    // Wants a time-ordered set of recs
    private void loadConflicts(final Set recs) {
        final LinkedList window = new LinkedList();
        final Iterator iter = recs.iterator();

        while (iter.hasNext()) {
            final Recording rec = (Recording) iter.next();

            final Iterator candidates = window.iterator();

            while (candidates.hasNext()) {
                final Recording candidate = (Recording) candidates.next();

                final Date end = new Date
                    (candidate.getEndTime().getTime() - 1);

                if (end.before(rec.getStartTime())) {
                    candidates.remove();
                } else {
                    candidate.getConflicts().add(rec);
                    rec.getConflicts().add(candidate);
                }
            }

            window.addLast(rec);
        }
    }

    private void loadRepeats(final Set recs) {
        final Map repeats = new HashMap();
        final Iterator iter = recs.iterator();

        while (iter.hasNext()) {
            final Recording rec = (Recording) iter.next();
            final String key = rec.getProgramKey();
            final Recording repeat = (Recording) repeats.get(key);

            if (repeat == null) {
                repeats.put(key, rec);

                debug("No repeat yet: " + rec);
            } else {
                repeat.getRepeats().add(rec);
                rec.getRepeats().add(repeat);

                debug("Repeat: " + rec + " (" + repeat + ")");
            }
        }
    }

    // Flaw: This will schedule more than one rec of the
    // same program.  IE, it does not eliminate repeat showings as it
    // picks winners
    //
    // Since fixed.  The earliest, highest-priority showing of a set
    // of repeats is a winner; the rest lose.

    // Requires a priority-ordered set of showings

    // Note that repeats are *winner* repeats.  There are still
    // repeats in the conflicts set, which would get picked up in
    // subsequent calls to cull
    private void cull(final Set recs,
                      final Set winners,
                      final Set repeats,
                      final Set conflicts) {
        final Iterator iter = recs.iterator();

        while (iter.hasNext()) {
            final Recording rec = (Recording) iter.next();

            if (repeats.contains(rec)) {
                debug("Repeat " + rec);

                if (winners.contains(rec)) {
                    throw new IllegalStateException
                        ("Repeat " + rec + " is also in the winner set");
                }

                if (conflicts.contains(rec)) {
                    throw new IllegalStateException
                        ("Repeat " + rec + " is also in the conflict set");
                }
            } else if (conflicts.contains(rec)) {
                debug("Conflict " + rec);

                if (winners.contains(rec)) {
                    throw new IllegalStateException
                        ("Conflict " + rec + " is also in the winner set");
                }

                if (repeats.contains(rec)) {
                    throw new IllegalStateException
                        ("Conflict " + rec + " is also in the repeat set");
                }
            } else {
                // Winners are those that haven't lost already
                winners.add(rec);

                debug("Winner " + rec);

                final Iterator riter = rec.getRepeats().iterator();

                while (riter.hasNext()) {
                    final Recording repeat = (Recording) riter.next();
                    riter.remove();
                    repeat.getRepeats().remove(rec);

                    if (conflicts.contains(repeat)) {
                        // We have a conflicting repeat.  Since
                        // repeats are preferentially discarded, move
                        // it out of the conflicts list and into the
                        // repeats list.

                        debug("  Repeat " + repeat + " is already a " +
                              "conflict; making it a repeat instead");

                        conflicts.remove(repeat);

                        final Iterator rciter = repeat.getConflicts().iterator();

                        while (rciter.hasNext()) {
                            final Recording conflict = (Recording) rciter.next();

                            if (conflicts.contains(conflict)) {
                                rciter.remove();
                                conflict.getConflicts().remove(repeat);
                            }
                        }
                    }

                    // Each repeat is a loser
                    repeats.add(repeat);

                    debug("  Versus repeat " + repeat);
                }

                final Iterator citer = rec.getConflicts().iterator();

                while (citer.hasNext()) {
                    final Recording conflict = (Recording) citer.next();
                    citer.remove();
                    conflict.getConflicts().remove(rec);

                    if (repeats.contains(conflict)) {
                        debug("  Conflict " + conflict + " is already a " +
                              "repeat; skipping it");
                    } else {
                        // Each conflict is a loser
                        conflicts.add(conflict);

                        debug("  Versus conflict " + conflict);
                    }
                }
            }
        }

        // Repeats have conflict mappings to entries in the conflict
        // set; remove these mappings

        final Iterator riter = repeats.iterator();

        while (riter.hasNext()) {
            final Recording repeat = (Recording) riter.next();

            final Iterator rciter = repeat.getConflicts().iterator();

            while (rciter.hasNext()) {
                final Recording conflict = (Recording) rciter.next();

                if (conflicts.contains(conflict)) {
                    rciter.remove();
                    conflict.getConflicts().remove(repeat);
                }
            }
        }

        if (m_debug) {
            System.out.println("Input: " + recs.size());
            System.out.println("Winners: " + winners.size());
            System.out.println("Repeats: " + repeats.size());
            System.out.println("Conflicts: " + conflicts.size());

            printRecordings("Winners", winners);
            printRecordings("Repeats", repeats);
            printRecordings("Conflicts", conflicts);

            checkDisjoint(winners, repeats);
            checkDisjoint(winners, conflicts);
            checkDisjoint(repeats, conflicts);

            checkSubset(recs, winners);
            checkSubset(recs, repeats);
            checkSubset(recs, conflicts);
        }

        if (winners.size() + repeats.size() + conflicts.size() != recs.size()) {
            throw new IllegalStateException
                ("Culled results don't add up");
        }
    }

    private static void printRecordings(final String header, final Set recs) {
        final Iterator iter = recs.iterator();

        System.out.println(header);

        while (iter.hasNext()) {
            final Recording rec = (Recording) iter.next();

            System.out.print("  " + rec);
            System.out.print(" " + rec.getRepeats());
            System.out.print(" " + rec.getConflicts());
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

// XXX For multi-tuner stuff later on

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
