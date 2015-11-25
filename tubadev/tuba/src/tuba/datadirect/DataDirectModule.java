package tuba.datadirect;

import java.net.*;
import smoky.*;
import tuba.datadirect.xtvd.*;
import tuba.runtime.*;
import wheaty.*;
import wheaty.parameters.*;

public final class DataDirectModule extends SmokyModule {
    public static DataDirectModule getModule() {
        return (DataDirectModule) Tuba.getModule("datadirect");
    }

    public static URL getTestXml(final String key) {
        return XtvdElement.class.getResource(key + ".xml");
    }

    private final DataDirectCommand m_command;
    private final StringParameter m_user;
    private final StringParameter m_password;
    private final StringParameter m_url;

    public DataDirectModule(final SmokyRuntime runtime) {
        super("datadirect", runtime);

        m_command = new DataDirectCommand(Tuba.getCommand());

	m_user = new StringParameter("user");
	m_user.setNullable(false);

	m_password = new StringParameter("password");
	m_password.setNullable(false);

	m_url = new StringParameter("url");
	m_url.setNullable(false);
	m_url.set("http://datadirect.webservices.zap2it.com" +
		  "/tvlistings/xtvdService");

        getModel().addParameter(m_user);
        getModel().addParameter(m_password);
        getModel().addParameter(m_url);
    }

    protected void initialize(final WheatySession session) {
    }

    protected void startup() {
    }

    protected void shutdown() {
    }

    public DataDirectSession getSession() {
        final DataDirectSession session = new DataDirectSession();
        final SmokyConfig config = getRuntime().getConfig();

        session.setUser((String) m_user.get(config));
        session.setPassword((String) m_password.get(config));
        session.setListingsUrl((String) m_url.get(config));

        return session;
    }

    public DataDirectCommand getCommand() {
        return m_command;
    }
}
