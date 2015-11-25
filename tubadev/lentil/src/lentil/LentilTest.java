package lentil;

import java.io.*;

public final class LentilTest {
    public static final void main(final String[] args) throws ParseException {
        final LentilParser parser = new LentilParser(System.in);

        final LentilPackage lpackage = parser.parse
            (LentilTest.class.getResource("LentilTest.lentil"));

        lpackage.print(new PrintWriter(System.out, true));
    }
}
