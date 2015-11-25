package tuba.recorder;

import java.io.*;
import java.net.*;
import java.util.*;
import tuba.capture.*;
import tuba.runtime.*;
import tuba.update.*;
import tuba.util.*;

public final class TubaRecorder {
    private final int m_port;
    private final CaptureSession m_capture;

    private TubaRecorder(final int port) {
        m_port = port;

        m_capture = CaptureModule.get().getSession();
    }

    private int run() throws IOException {
        final TubaRuntime runtime = Tuba.getRuntime();

        runtime.initialize();

        ServerSocket server = null;
        int ret = 1;

        try {
            runtime.startup();

            server = new ServerSocket(m_port);

            m_capture.schedule();

            run(server);

            ret = 0;
        } catch (Exception e) {
            try {
                e.printStackTrace();
            } catch (Exception ie) {
            }
        } finally {
            server.close();
            runtime.shutdown();
        }

        return ret;
    }

    private void run(final ServerSocket server) throws IOException {
        while (true) {
            final Socket socket = server.accept();
            final BufferedReader in = new BufferedReader
                (new InputStreamReader(socket.getInputStream()));
            final PrintWriter out = new PrintWriter
                (new OutputStreamWriter(socket.getOutputStream()), true);

            try {
                run(in, out);
            } finally {
                in.close();
                out.close();
                socket.close();
            }
        }
    }

    private void run(final BufferedReader in,
                     final PrintWriter out) throws IOException {
        out.println("Tuba, " + new Date());
        out.println("Type 'quit' to disconnect");

        while (true) {
            out.print("tuba$ ");
            out.flush();

            String line = in.readLine();

            if (line == null) break;

            line = line.trim();

            if (line.equals("")) continue;

            if (line.equals("quit") || line.equals("exit")) break;

            final LinkedList args = new LinkedList
                (Arrays.asList(line.split("\\s")));

            Tuba.getCommand().execute(args, in, out, out);
        }
    }

    public static void main(final String[] args) throws IOException {
        int port = 9000;

        if (args.length == 1) {
            port = Integer.parseInt(args[0]);
        }

        final TubaRecorder server = new TubaRecorder(port);

        System.exit(server.run());
    }
}
