package smoky;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import wheaty.*;

public class SmokyRuntime {
    private final String m_name;
    private final Map<String, SmokyModule> m_modules;
    private final SmokyConfig m_config;

    private boolean m_initialized;
    private boolean m_up;
    private File m_homedir;
    private File m_configdir;
    private File m_logdir;
    private PrintWriter m_log;

    protected SmokyRuntime(final String name) {
        m_name = name;
        m_modules = new LinkedHashMap();
        m_config = new SmokyConfig(this);
        m_initialized = false;
        m_up = false;
    }

    public final String getName() {
        return m_name;
    }

    public final SmokyConfig getConfig() {
        return m_config;
    }

    public final File getHomeDirectory() {
        return m_homedir;
    }

    protected final void setHomeDirectory(final File homedir) {
        if (!homedir.isDirectory()) throw new IllegalArgumentException();

        m_homedir = homedir;
    }

    public final File getConfigDirectory() {
        return m_configdir;
    }

    protected final void setConfigDirectory(final File configdir) {
        if (!configdir.isDirectory()) throw new IllegalArgumentException();

        m_configdir = configdir;
    }

    public final File getLogDirectory() {
        return m_logdir;
    }

    protected final void setLogDirectory(final File logdir) {
        if (!logdir.isDirectory()) throw new IllegalArgumentException();

        m_logdir = logdir;
    }

    protected final PrintWriter getLogWriter() {
        return m_log;
    }

    protected final void setLogWriter(final PrintWriter log) {
        m_log = log;
    }

    public final Collection<SmokyModule> getModules() {
        return m_modules.values();
    }

    public final SmokyModule getModule(final String name) {
        return m_modules.get(name);
    }

    final void addModule(final SmokyModule module) {
        final String name = module.getName();

        if (m_modules.containsKey(name)) {
            throw new IllegalStateException
                ("Module '" + name + "' already added");
        }

        m_modules.put(name, module);
    }

    protected final SmokyModule loadModule(final String sclass) {
        final Class jclass;

        try {
            jclass = Class.forName(sclass);
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(e);
        }

        final Constructor cons;

        try {
            cons = jclass.getConstructor(SmokyRuntime.class);
        } catch (NoSuchMethodException e) {
            throw new IllegalStateException(e);
        }

        final SmokyModule module;

        try {
            module = (SmokyModule) cons.newInstance(this);
        } catch (InstantiationException e) {
            throw new IllegalStateException(e);
        } catch (InvocationTargetException e) {
            throw new IllegalStateException(e);
        } catch (IllegalAccessException e) {
            throw new IllegalStateException(e);
        }

        return module;
    }

    public final void load(final List<String> modules) {
        for (final String sclass : modules) {
            loadModule(sclass);
        }
    }

    public synchronized final void initialize() {
        if (isInitialized()) {
            throw new IllegalStateException("Already initialized");
        }

        if (getHomeDirectory() == null) {
            throw new IllegalArgumentException("Home directory is not set");
        }

        if (getConfigDirectory() == null) {
            setConfigDirectory(new File(getHomeDirectory(), "conf"));
        }

        if (getLogWriter() == null) {
            setLogDirectory(new File(getHomeDirectory(), "log"));
        }

        if (getLogWriter() == null) {
            final File log = new File(getLogDirectory(), getName() + ".log");

            try {
                setLogWriter(new PrintWriter(new FileWriter(log)));
            } catch (IOException e) {
                throw new IllegalStateException(e);
            }
        }

        final SmokyConfig config = getConfig();

        try {
            config.load();
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        // XXX do this in two passes?  or just solve the ordering
        // problem better

        for (final SmokyModule module : getModules()) {
            module.getModel().unmarshal(config.getDocument(), config);
        }

        for (final SmokyModule module : getModules()) {
            module.initialize(config);
        }

        m_initialized = true;
    }

    public synchronized final boolean isInitialized() {
        return m_initialized;
    }

    public synchronized final void startup() {
        for (final SmokyModule module : getModules()) {
            module.startup();
        }

        m_up = true;
    }

    public synchronized final boolean isUp() {
        return m_up;
    }

    public synchronized final void shutdown() {
        final List<SmokyModule> modules = new ArrayList(getModules());
        Collections.reverse(modules);

        for (final SmokyModule module : modules) {
            module.shutdown();
        }

        m_up = false;
    }

    protected final void log(final Exception e) {
        final PrintWriter log = getLogWriter();

        synchronized (log) {
            e.printStackTrace(log);
        }

        log.flush();
    }

    protected final void log(final String message) {
        log(0, message);
    }

    protected final void log(final int threshold, final String message) {
        final PrintWriter log = getLogWriter();

        synchronized (log) {
            log.println(message);
        }

        log.flush();
    }
}
