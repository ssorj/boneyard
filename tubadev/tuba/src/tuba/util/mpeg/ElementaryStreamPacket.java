package tuba.util.mpeg;

import java.io.*;

final class ElementaryStreamPacket {
    byte[] bytes = new byte[524288];
    int length = 0;

    private int m_start;
    private int m_sid;
    private int m_length;

    void parse() {
        m_start =
            (0xff & bytes[0]) << 16 |
            (0xff & bytes[1]) << 8 |
            (0xff & bytes[2]);
        m_sid = 0xff & bytes[3];
        m_length = (0xff & bytes[4]) << 8 | (0xff & bytes[5]);
    }

    void print() {
        final PrintWriter out = new PrintWriter(System.out);

        printSummary(out);
        //printBytes(out);
    }

    void printSummary(final PrintWriter out) {
        out.print(Integer.toHexString(getStartCode()));
        out.print(" ");
        out.print(Integer.toHexString(getStreamId()));
        out.print(" ");
        out.print(getDeclaredLength());
        out.print(" ");
        out.print(getEstablishedLength());
        out.println();
        out.flush();
    }

    int getStartCode() {
        return m_start;
    }

    int getStreamId() {
        return m_sid;
    }

    int getDeclaredLength() {
        return m_length;
    }

    int getEstablishedLength() {
        return length;
    }

    void printBytes(final PrintWriter out) {
        final char[] chars = new char[2];

        for (int i = 0; i < length; i++) {
            if (i != 0) {
                if (i % 4 == 0) {
                    out.print(" ");
                }

                if (i % 32 == 0) {
                    out.println(i);
                    out.flush();
                }
            }

            final byte b = bytes[i];

            chars[0] = s_digits[(b & 0xf0) >> 4];
            chars[1] = s_digits[b & 0x0f];

            out.print(chars);
        }

        out.flush();
    }

    private static final char[] s_digits = {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'a', 'b', 'c', 'd', 'e', 'f'
    };
}
