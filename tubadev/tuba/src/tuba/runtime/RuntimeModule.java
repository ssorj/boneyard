package tuba.runtime;

import java.net.*;
import butyl.*;
import lentil.*;
import smoky.*;
import tuba.runtime.model.*;
import wheaty.*;
import wheaty.parameters.*;

public final class RuntimeModule extends SmokyModule {
    public static RuntimeModule getModule() {
        return (RuntimeModule) Tuba.getModule("runtime");
    }

    private final TubaCommand m_command;
    private final Schema m_schema;
    private final StringParameter m_url;
    private final StringParameter m_user;
    private final StringParameter m_driver;

    private LentilPackage m_package;
    private TubaDatabase m_database;

    public RuntimeModule(final SmokyRuntime runtime) {
        super("runtime", runtime);

        m_command = new TubaCommand();
        m_schema = new Schema();

        m_url = new StringParameter("jdbc_url");
        m_url.setNullable(false);
        m_url.set("jdbc:hsqldb:hsql://localhost/tuba");

        m_user = new StringParameter("jdbc_user");
        m_user.setNullable(false);
        m_user.set("sa");

        m_driver = new StringParameter("jdbc_driver");
        m_driver.setNullable(false);
        m_driver.set("org.hsqldb.jdbcDriver");

        getModel().addParameter(m_url);
        getModel().addParameter(m_user);
        getModel().addParameter(m_driver);
    }

    protected void initialize(final WheatySession session) {
        final String driver = (String) m_driver.get(session);

        try {
            Class.forName(driver);
        } catch (ClassNotFoundException e) {
            throw new TubaException
                ("JDBC driver class '" + driver + "' not found");
        }

        // XXX wrong
        final URL res = Program.class.getResource("package.lentil");
        m_package = LentilParser.parse(res);
    }

    protected void startup() {
        try {
            getConnection().open();
        } catch (LentilConnectionException e) {
            // Can't connect; try starting db up

            m_database = new TubaDatabase();
            m_database.startup();

            // Make sure we can connect now

            final TubaConnection conn = getConnection();
            try {
                conn.open();
            } finally {
                conn.close();
            }
        }
    }

    protected void shutdown() {
        if (m_database != null) {
            m_database.shutdown();
        }
    }

    public TubaCommand getCommand() {
        return m_command;
    }

    Schema getSchema() {
        return m_schema;
    }

    private LentilPackage getLentilPackage() {
        return m_package;
    }

    LentilClass getLentilClass(final Class jclass) {
        return getLentilPackage().getClass(jclass);
    }

    TubaConnection getConnection() {
        final String url = (String) m_url.get(Tuba.getConfig());

        return new TubaConnection(url);
    }
}
