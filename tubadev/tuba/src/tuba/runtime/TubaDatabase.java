package tuba.runtime;

import java.io.*;
import org.hsqldb.*;

public final class TubaDatabase {
    private final Server m_server;

    TubaDatabase() {
        m_server = new Server();

        // XXX change this to tubadb
        m_server.setDatabaseName(0, "tuba");

        final TubaRuntime runtime = Tuba.getRuntime();
        final File file = new File(runtime.getDataDirectory(), "tuba");

        m_server.setDatabasePath(0, file.getPath());

        m_server.setSilent(true);
        m_server.setTrace(false);
        m_server.setNoSystemExit(true);
        m_server.setTls(false);
    }

    void startup() {
        try {
            m_server.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    void shutdown() {
        try {
            m_server.shutdown();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static final void main(final String[] sargs) {
        Tuba.getRuntime().initialize();

        int exit = 1;
        final TubaDatabase base = new TubaDatabase();

        try {
            base.startup();

            while (true) {
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                }
            }
        } catch (Exception e) {
            try {
                e.printStackTrace();
            } catch (Exception ie) {
            }
        } finally {
            base.shutdown();

            exit = 0;
        }

        System.exit(exit);
    }
}
