package tuba.util.mpeg;

import java.io.*;
import tuba.util.*;

public final class Test {
    public static void main(final String[] args) throws Exception {
        ps(args);
    }

    public static void ts(final String[] args) throws Exception {
        if (args.length != 1) throw new IllegalStateException
            ("Wrong number of arguments: " + args.length);

        final PushbackInputStream in = new PushbackInputStream
            (new FileInputStream(args[0]), 188);
        final TransportStreamReader reader = new TransportStreamReader(in);
        final TransportStreamPacket packet = new TransportStreamPacket();

        while (reader.read(packet)) {
            packet.parse();
            packet.print();
        }

        in.close();
    }

    public static void ps(final String[] args) throws Exception {
        if (args.length != 2) throw new IllegalStateException
            ("Wrong number of arguments: " + args.length);

        final InputStream in = new FileInputStream(args[0]);
        final OutputStream out = new FileOutputStream(args[1]);

        final TransportStreamReader reader = new TransportStreamReader(in);
        final ProgramStreamWriter writer = new ProgramStreamWriter(out);

        writer.writePackHeader();
        writer.writeSystemHeader();

        ElementaryStreamPacket packet;

        for (int i = 0; i < 1000; i++) {
            packet = reader.read();

            if (packet == null) break;

            writer.write(packet);
        }

        writer.writeEndCode();

        in.close();
        out.close();
    }
}
