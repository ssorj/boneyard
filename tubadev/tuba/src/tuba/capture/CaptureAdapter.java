package tuba.capture;

import java.io.*;
import java.util.*;

public interface CaptureAdapter {
    void capture(int tuner, String channel, Date end, File file)
        throws IOException;
}
