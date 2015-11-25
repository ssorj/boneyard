package tuba.dvb;

import java.io.*;
import tuba.runtime.*;

final class Driver {
    static {
        final File file = new File
            (Tuba.getRuntime().getLibDirectory(), "dvb.so");

        System.load(file.getPath());
    }

    native static int tune(final String frontend, final int freq);
    native static int add_video_filter(final String demuxer, final int pid);
    native static int add_audio_filter(final String demuxer, final int pid);
    native static int close(final int fd);

    public static void main(final String[] args) throws Exception {
        int[] fds = new int[3];

        fds[0] = tune("/dev/dvb/adapter0/frontend0", 623000000);
        fds[1] = add_video_filter("/dev/dvb/adapter0/demux0", 49);
        fds[2] = add_audio_filter("/dev/dvb/adapter0/demux0", 52);

        final InputStream in = new FileInputStream("/dev/dvb/adapter0/dvr0");
        final OutputStream out = new FileOutputStream("test.ts");
        byte[] b = new byte[4096];

        while (in.read(b) != -1) {
            out.write(b);
        }

        in.close();
        out.close();

        close(fds[0]);
        close(fds[1]);
        close(fds[2]);
    }
}
