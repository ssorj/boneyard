package tuba.capture;

import java.io.*;
import java.util.*;
import smoky.*;
import tuba.util.*;

// XXX the usefulness of this is dubious
public final class CaptureThread extends SmokyQueueThread {
    CaptureThread(final CaptureModule module) {
	super("capture", module);
    }

    protected void run(final Object obj) throws Exception {
	final CaptureRequest req = (CaptureRequest) obj;

        ((CaptureModule) getModule()).capture(req);
    }
}
