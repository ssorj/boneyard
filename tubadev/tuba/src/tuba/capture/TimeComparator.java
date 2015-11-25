package tuba.capture;

import java.util.*;
import tuba.runtime.model.*;

final class TimeComparator implements Comparator {
    public int compare(final Object obj1, final Object obj2) {
        final Recording rec1 = (Recording) obj1;
        final Recording rec2 = (Recording) obj2;

        int sign = rec1.StartTime.compareTo(rec2.StartTime);

        if (sign == 0) {
            sign = rec1.EndTime.compareTo(rec2.EndTime);
        }

        if (sign == 0) {
            // This is arbitrary
            sign = rec1.CallSign.compareTo(rec2.CallSign);
        }

        if (sign == 0) {
            throw new IllegalStateException();
        }

        return sign;
    }
}
