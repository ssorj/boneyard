package tuba.dvb;

import java.io.*;
import java.util.*;
import tuba.runtime.*;

public final class DvbTuner {
    private final String m_adapter;
    private final String m_frontend;
    private final String m_demux;
    private final String m_dvr;

    DvbTuner(final String adapter,
             final String frontend,
             final String demux,
             final String dvr) {
        m_adapter = adapter;
        m_frontend = frontend;
        m_demux = demux;
        m_dvr = dvr;
    }

    public void capture(final Channel chan,
			final File file,
			final Date end) throws IOException {
        if (chan == null) throw new IllegalArgumentException();
        if (file == null) throw new IllegalArgumentException();
        if (end == null) throw new IllegalArgumentException();

        FileOutputStream out = null;

        try {
            out = new FileOutputStream(file);

            capture(chan.getFrequency(),
                    chan.getVideoPid(),
                    chan.getAudioPid(),
                    out,
                    end);

            out.flush();
        } finally {
            if (out != null) out.close();
        }
    }

    private String getFrontend() {
        return m_adapter + "/" + m_frontend;
    }

    private String getDemux() {
        return m_adapter + "/" + m_demux;
    }

    private String getDvr() {
        return m_adapter + "/" + m_dvr;
    }

    private void capture(final int freq,
			 final int vpid,
			 final int apid,
			 final OutputStream out,
			 final Date end) throws IOException {
        final Timer timer = new Timer();
        final boolean[] ended = new boolean[1];

        timer.schedule(new TimerTask() {
                public void run() {
                    ended[0] = true;
                }
            }, end);

        int frontend = -1;

        for (int i = 0; i < 60; i++) {
            frontend = Driver.tune(getFrontend(), freq);

            try {
                Thread.sleep(3000);
            } catch (InterruptedException e) {
            }

            if (frontend != -1) break;
        }

        if (frontend == -1) {
            throw new IOException("Failed tuning");
        }

        int vfilter = Driver.add_video_filter(getDemux(), vpid);

        if (vfilter == -1) {
            throw new IOException("Failed setting video filter");
        }

        int afilter = Driver.add_audio_filter(getDemux(), apid);

        if (afilter == -1) {
            throw new IOException("Failed setting audio filter");
        }

        InputStream in = null;

        try {
            in = new FileInputStream(getDvr());
            final byte[] b = new byte[4096];
            int len;

            while (!ended[0] && (len = in.read(b)) != -1) {
                out.write(b, 0, len);
            }
        } finally {
            if (in != null) in.close();
        }

        Driver.close(afilter);
        Driver.close(vfilter);
        Driver.close(frontend);
    }

//     public static void main(final String[] args) throws Exception {
//         TubaDvb.initialize();

//         final DvbTuner tuner = TubaDvb.getTuner();
//         final long now = System.currentTimeMillis();

//         tuner.capture(TubaDvb.getChannels().get("WGBHDT"),
//                       new File("test1.ts"),
//                       new Date(now + 30000));

//         tuner.capture(TubaDvb.getChannels().get("WGBHDT"),
//                       new File("test2.ts"),
//                       new Date(now + 60000));

//         tuner.capture(TubaDvb.getChannels().get("WSBKDT"),
//                       new File("test3.ts"),
//                       new Date(now + 90000));
//     }
}
