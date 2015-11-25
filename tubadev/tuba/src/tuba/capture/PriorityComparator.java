package tuba.capture;

import java.util.*;
import tuba.runtime.model.*;

final class PriorityComparator implements Comparator {
    public int compare(final Object obj1, final Object obj2) {
        final CaptureRequest req1 = (CaptureRequest) obj1;
        final CaptureRequest req2 = (CaptureRequest) obj2;

        int sign = sgn(req1.getPriority(), req2.getPriority());

        if (sign == 0) {
            sign = req1.getStartTime().compareTo(req2.getStartTime());
        }

        // XXX isn't there something that makes more sense than this?

        if (sign == 0) {
            sign = req1.getCallSign().compareTo(req2.getCallSign());
        }

        return sign;
    }

    private static int sgn(final int a, final int b) {
        if (b == a) {
            return 0;
        }

        if (a > b) {
            return -1;
        }

        return 1;
    }
}
