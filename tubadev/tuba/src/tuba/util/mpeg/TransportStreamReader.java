package tuba.util.mpeg;

import java.io.*;

final class TransportStreamReader {
    private final InputStream m_in;
    private final ElementaryStreamPacket[] m_packets;
    final TransportStreamPacket m_tpacket;
    ElementaryStreamPacket m_packet;

    TransportStreamReader(final InputStream in) {
        m_in = in;
        m_packets = new ElementaryStreamPacket[8192];
        m_tpacket = new TransportStreamPacket();
    }

    boolean read(final TransportStreamPacket packet) throws IOException {
        int count = 0;

        while (count < 188) {
            final int n = m_in.read(packet.bytes, count, 188 - count);

            if (n == -1) return false;

            count += n;
        }

        return true;
    }

    ElementaryStreamPacket read() throws IOException {
        final TransportStreamPacket tpacket = m_tpacket;

        while (read(tpacket)) {
            tpacket.parse();

            ElementaryStreamPacket packet = m_packets[tpacket.getPid()];

            if (tpacket.isUnitStart()) {
                final ElementaryStreamPacket complete = packet;

                packet = new ElementaryStreamPacket();
                m_packets[tpacket.getPid()] = packet;

                if (tpacket.hasPayload()) {
                    tpacket.copyPayload(packet);
                }

                if (complete != null) {
                    return complete;
                }
            } else if (packet != null && tpacket.hasPayload()) {
                tpacket.copyPayload(packet);
            }
        }

        return null;
    }
}



                        //final String hex = HexCodec.encode
                        //    (vpacket.toByteArray());
                        //System.out.println("vpacket " + hex);


//         if (syncbyte == 0x47) {
//             m_in.mark(189);
//         } else {
//             m_in.reset();

//             for (int j = 0; true; j++) {
//                 final int b = m_in.read();

//                 if (b == -1) return -1;

//                 if (b == 0x47) {
//                     in.reset();
//                     in.skip(j);
//                     continue;
//                 }
//             }
//         }
