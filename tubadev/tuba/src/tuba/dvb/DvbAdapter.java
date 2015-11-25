package tuba.dvb;

import java.io.*;
import java.util.*;
import tuba.capture.*;

// Note that this is an adapter in the sense that it adapts the dvb
// code to the capture code.  It does not represent a hardware
// adapter.
public final class DvbAdapter implements CaptureAdapter {
    public void capture(final int tuner,
                        final String schan,
                        final Date end,
                        final File file)
            throws IOException {
	final Channel chan = DvbModule.getModule().getChannels().get(schan);

        if (chan == null) {
            throw new IllegalStateException
                ("Channel '" + schan + "' has no tuning configuration");
        }

        DvbModule.getModule().getTuner().capture(chan, file, end);
    }
}
