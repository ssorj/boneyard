package tuba.capture;

import tuba.runtime.model.*;

public interface CaptureListener {
    void captured(final CaptureSession session, final Recording rec);
}
