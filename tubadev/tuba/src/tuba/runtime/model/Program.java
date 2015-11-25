package tuba.runtime.model;

import java.math.*;
import java.security.*;
import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.util.*;

public final class Program extends LentilObject {
    public Program() {
        super(Program.class);

        Priority = new Integer(-1);
    }

    public Long Key;
    public String SourceKey;
    public String Title;
    public String Subtitle;
    public String Description;
    public Date OriginalAirDate;
    public String Checksum;
    public Long SeriesKey;
    public Integer Priority;

    private byte[] computeChecksum() {
        final String[] elems = new String[] {
            Title,
            Subtitle,
            Description
        };

        final StringBuffer buffer = new StringBuffer();

        for (int i = 0; i < elems.length; i++) {
            String elem = elems[i];

            if (elem == null) {
                buffer.append("-");
            } else {
                elem = elem.toLowerCase();
                elem.replaceAll("\\W", "");

                buffer.append(elem);
            }

            buffer.append("\t");
        }

        if (OriginalAirDate == null) {
            buffer.append("-");
        } else {
            buffer.append(Tuba.getDateFormat().format(OriginalAirDate));
        }

        final byte[] bytes = buffer.toString().getBytes();
        final MessageDigest digest;

        try {
            digest = MessageDigest.getInstance("SHA-1");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }

        final byte[] checksum = digest.digest(bytes);

        return checksum;
    }

    protected final int insert(final LentilSession session) {
        Checksum = HexCodec.encode(computeChecksum());

	return super.insert(session);
    }

    public static void main(final String[] args) throws Exception {
        final TubaRuntime runtime = Tuba.getRuntime();
        runtime.initialize();

        try {
            runtime.startup();

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final Set skeys = new HashSet();
                final LentilCursor cursor = conn.load(Program.class);

                while (cursor.next()) {
                    final Program program = new Program();
                    program.load(cursor);

                    if (skeys.contains(program.SourceKey)) {
                        throw new IllegalStateException(program.SourceKey);
                    }

                    skeys.add(program.SourceKey);

                    program.Checksum = HexCodec.encode(program.computeChecksum());

                    System.out.println("Key " + program.Key);
                    System.out.println("SourceKey " + program.SourceKey);
                    System.out.println("Checksum " + program.Checksum);

                    program.update(conn);
                }

                conn.commit();
            } finally {
                conn.close();
            }
        } finally {
            runtime.shutdown();
        }
    }

//     public static void main(final String[] args) throws Exception {
//         final TubaSession session = Tuba.getSession();
//         Connection conn = null;


//         try {
//             session.open();
//             conn = TubaData.getConnection();

//             final Statement stmt = conn.createStatement
//                 (ResultSet.TYPE_SCROLL_INSENSITIVE,
//                  ResultSet.CONCUR_UPDATABLE);
//             final ResultSet results = stmt.executeQuery(s_sql.get("load_all"));

//             while (results.next()) {
//                 final Program program = new Program();
//                 program.load(results);

//                 program.Description =
//                     new BigInteger(program.computeChecksum()).toString();

//                 program.save(results);
//                 results.updateRow();
//             }

//             results.close();
//             stmt.close();
//         } finally {
//             conn.close();
//             session.close();
//         }
//     }
}
