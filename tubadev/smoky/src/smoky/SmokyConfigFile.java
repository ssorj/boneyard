package smoky;

import java.io.*;
import java.util.*;
import wheaty.documents.*;

public final class SmokyConfigFile extends PropertiesDocument {
    private final SmokyRuntime m_runtime;
    private final Properties m_props;

    SmokyConfigFile(final SmokyRuntime runtime) {
        m_runtime = runtime;
	m_props = new Properties();
    }

    private SmokyRuntime getRuntime() {
        return m_runtime;
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

	load(getProperties());
    }

    public void save() throws IOException {
	save(getProperties());

        final File file = getFile();

        if (!file.exists()) {
            file.createNewFile();
        }

	final FileOutputStream out = new FileOutputStream(file);
	getProperties().store(out, null);
	out.close();
    }
}
