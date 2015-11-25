package lentil;

import java.io.*;
import java.util.*;

public final class LentilPackage {
    private static Map s_packages = new HashMap();

    private static Map getPackages() {
        return s_packages;
    }

    public static final LentilPackage getPackage(final String name) {
        LentilPackage lpackage;

        synchronized (s_packages) {
            lpackage = (LentilPackage) getPackages().get(name);

            if (lpackage == null) {
                lpackage = new LentilPackage(name);
                getPackages().put(name, lpackage);
            }
        }

        return lpackage;
    }

    private String m_name;
    private Map m_lclasses;

    private LentilPackage(final String name) {
        m_name = name;
        m_lclasses = new LinkedHashMap();
    }

    public String getName() {
        return m_name;
    }

    Class getJavaClass(final String name) {
        final Class jclass;

        try {
            jclass = Class.forName(getName() + "." + name);
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(e);
        }

        return jclass;
    }

    Map getClasses() {
        return m_lclasses;
    }

    public LentilClass getClass(final Class jclass) {
        return (LentilClass) getClasses().get(jclass);
    }

    public final void print(final PrintWriter out) {
        out.println("package " + getName() + ";");

        final Iterator iter = getClasses().values().iterator();

        while (iter.hasNext()) {
            out.println();
            ((LentilClass) iter.next()).print(out);
        }
    }
}
