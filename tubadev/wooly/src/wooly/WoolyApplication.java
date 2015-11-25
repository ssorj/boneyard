package wooly;

import butyl.*;
import java.util.*;
import wheaty.*;
import wheaty.parameters.*;

public abstract class WoolyApplication {
    private final String m_name;
    private WoolyApplication m_parent;
    private final Map<String, WoolyApplication> m_children;

    public WoolyApplication(final String name) {
        if (name == null) throw new IllegalArgumentException();

        m_name = name;
        m_children = new LinkedHashMap();
    }

    public final String getName() {
        return m_name;
    }

    public final WoolyApplication getParent() {
        return m_parent;
    }

    private final void setParent(final WoolyApplication parent) {
        m_parent = parent;
    }

    public final Collection<WoolyApplication> getChildren() {
        return m_children.values();
    }

    public final WoolyApplication getChild(final String name) {
        return m_children.get(name);
    }

    public final String getPath() {
        final String path;

        if (getParent() == null) {
            path = getName();
        } else {
            path = getParent().getPath() + "." + getName();
        }

        return path;
    }

    public final String getHttpAddress() {
        final CachedPath path = CachedPath.get(getPath()).tail();
        String spath = "";

        if (path != null) {
            spath = path.toString();
        }

        return "/" + spath;
    }

    public final WoolySession process(final WoolyQuery query) {
        if (query == null) throw new IllegalArgumentException();

        return doProcess(query);
    }

    protected abstract WoolySession doProcess(final WoolyQuery query);

    public final String render(final WoolySession session) {
        return doRender(session);
    }

    protected abstract String doRender(final WoolySession session);

    public void print() {
        System.out.println(WoolyApplication.class.getName());
        System.out.println("  getPath() -> " + getPath());
    }
}
