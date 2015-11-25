package tuba.util;

import java.io.*;
import java.util.*;

public final class StreamedProcess {
    public static void main(final String[] args) throws Exception {
        System.exit(StreamedProcess.exec(args, System.out));
    }

    public static int exec(final String[] args, final OutputStream out)
            throws IOException {
        final Process proc = Runtime.getRuntime().exec(args);

        final StreamConsumer in = new StreamConsumer
            (proc.getInputStream(), out);
        final StreamConsumer err = new StreamConsumer
            (proc.getErrorStream(), out);

        in.start();
        err.start();

        try {
            in.join();
            err.join();
        } catch (InterruptedException e) {
        }

        int exit = 1;

        try {
            exit = proc.waitFor();
        } catch (InterruptedException e) {
        }

        return exit;
    }

    private static class StreamConsumer extends Thread {
        public final InputStream m_in;
        public final OutputStream m_out;

        StreamConsumer(final InputStream in, final OutputStream out) {
            m_in = in;
            m_out = out;
        }

        public void run() {
            try {
                doRun();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        private void doRun() throws IOException {
            try {
                final byte[] b = new byte[4096];
                int len;

                while ((len = m_in.read(b)) != -1) {
                    m_out.write(b, 0, len);
                }

                m_out.flush();
            } finally {
                m_in.close();
                m_out.close();
            }
        }
    }
}
