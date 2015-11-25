package smoky;

import java.io.*;
import java.util.*;
import wheaty.*;
import wheaty.documents.*;

public final class SmokyConfig extends WheatySession {
    private final SmokyRuntime m_runtime;
    private final PropertiesDocument m_doc;
    private final Properties m_props;

    SmokyConfig(final SmokyRuntime runtime) {
        m_runtime = runtime;
        m_doc = new PropertiesDocument();
	m_props = new Properties();
    }

    private SmokyRuntime getRuntime() {
        return m_runtime;
    }

    PropertiesDocument getDocument() {
        return m_doc;
    }

    private Properties getProperties() {
	return m_props;
    }

    File getFile() {
	final File file = new File(getRuntime().getConfigDirectory(),
                                   getRuntime().getName() + ".properties");

	return file;
    }

    public void load() throws IOException {
        final File file = getFile();

        if (!file.exists()) {
            file.createNewFile();
        }

	final FileInputStream in = new FileInputStream(file);
	getProperties().load(in);
	in.close();

	getDocument().load(getProperties());

        for (final SmokyModule module : getRuntime().getModules()) {
            module.getModel().unmarshal(getDocument(), this);
        }
    }

    public void save() throws IOException {
        for (final SmokyModule module : getRuntime().getModules()) {
            module.getModel().marshal(this, getDocument());
        }


        getDocument().print();

        getProperties().list(System.out);

	getDocument().save(getProperties());

        final File file = getFile();

        if (!file.exists()) {
            file.createNewFile();
        }

	final FileOutputStream out = new FileOutputStream(file);
	getProperties().store(out, null);
	out.close();
    }
}
