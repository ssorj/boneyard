package wooly;

import java.util.*;

public abstract class WoolyWidget {
    private final String m_name;
    private WoolyWidget m_parent;
    private final Map <String, WoolyWidget> m_children;
    private WoolyModel m_model;

    protected WoolyWidget(final String name) {
        if (name == null) throw new IllegalArgumentException();

        m_name = name;
        m_children = new LinkedHashMap();
    }

    public final String getName() {
        return m_name;
    }

    public final WoolyWidget getParent() {
        return m_parent;
    }

    private final void setParent(final WoolyWidget parent) {
        if (parent == null) throw new IllegalArgumentException();
        if (getParent() != null) throw new IllegalStateException();

        m_parent = parent;
    }

    private Map<String, WoolyWidget> getChildMap() {
        return m_children;
    }

    public final Collection<WoolyWidget> getChildren() {
        return getChildMap().values();
    }

    public final WoolyWidget getChild(final String name) {
        return getChildMap().get(name);
    }

    public final void addChild(final WoolyWidget child) {
        if (child == null) throw new IllegalArgumentException();

        getChildMap().put(child.getName(), child);
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

    public final WoolyWidget get(final String path) {
        if (path == null) throw new IllegalArgumentException();

        final WoolyWidget widget;
        final int sep = path.indexOf('.');

        if (sep == -1) {
            widget = getChildMap().get(path);
        } else {
            final WoolyWidget child = getChildMap().get
                (path.substring(0, sep - 1));

            widget = child.get(path.substring(sep));
        }

        return widget;
    }

    public final void initialize() {
        final WoolyModel model = new WoolyModel(getPath());

        doInitialize(model);

        m_model = model;

        for (final WoolyWidget child : getChildren()) {
            child.initialize();
        }
    }

    protected void doInitialize(final WoolyModel model) {
    }

    public final void process(final WoolySession session,
                              final WoolyQuery query) {
        if (session == null) throw new IllegalArgumentException();
        if (query == null) throw new IllegalArgumentException();

        doProcess(session, query);
    }

    protected void doProcess(final WoolySession session,
                             final WoolyQuery query) {
        for (final WoolyWidget child : getChildren()) {
            child.process(session, query);
        }
    }

    public final String render(final WoolySession session) {
        if (session == null) throw new IllegalArgumentException();

        final WoolyWriter writer = new WoolyWriter();

        doRender(session, writer);

        final String result = writer.toString();

        return result;
    }


    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        for (final WoolyWidget child : getChildren()) {
            writer.write(child.render(session));
        }
    }

    public final void print() {
        System.out.println(WoolyWidget.class.getName());
        System.out.println("  getPath() -> " + getPath());
    }

    public String toString() {
        return getClass().getName() + "@" + getPath();
    }
}


    //     private final Map m_cache = new LRUMap(200);
    //     private final Map m_timestamps = new LRUMap(200);


//     protected Object getKey(final WoolySession session) {
//         return null;
//         //return state.marshalCacheKey();
//     }

//     protected Date getTimestamp(final WoolySession session) {
//         return null;
//     }

        //         final Date timestamp = getTimestamp(session);
        //         String output;

        //         if (timestamp == null) {
        //             // Caching not in use

        //             final WoolyWriter writer = new WoolyWriter();

        //             render(state, writer);

        //             output = writer.toString();
        //         } else {
        //             final Object key = getKey(session);

        //             output = getCache(key, timestamp);

        //             if (output == null) {
        //                 // There's no cached output or the output is stale

        //                 final WoolyWriter writer = new WoolyWriter();

        //                 output = render(session);

        //                 setCache(key, timestamp, output);
        //             }
        //         }


    //     private void setCache(final Object key,
    //                           final Date timestamp,
    //                           final String value) {
    //         synchronized (m_cache) {
    //             m_cache.put(key, value);
    //             m_timestamps.put(key, timestamp);
    //         }
    //     }

    //     private String getCache(final Object key, final Date timestamp) {
    //         synchronized (m_cache) {
    //             final Date cached = (Date) m_timestamps.get(key);

    //             if (timestamp.equals(cached)) {
    //                 return (String) m_cache.get(key);
    //             } else {
    //                 return null;
    //             }
    //         }
    //     }





//     protected void doDebug(final WoolySession session,
//                            final WoolyWriter writer) {
//         StringBuilder builder = new StringBuilder();
//         WoolyWidget parent = getParent();

//         while (parent != null) {
//             builder.append("    ");
//             parent = parent.getParent();
//         }

//         final String inset = builder.toString();

//         // Fake lang

//         writer.write(inset);
//         writer.write("widget <b>" + getName() + "</b>");
//         writer.write(" {\n");

//         writer.write(inset + "    class " + getClass().getName() + ";\n");
//         writer.write(inset + "    namespace " + getNamespace() + ";\n");

//         final Iterator children = getChildren().iterator();

//         while (children.hasNext()) {
//             final WoolyWidget child = (WoolyWidget) children.next();

//             writer.write("\n");
//             writer.write(child.debug(session));
//         }

//         writer.write(inset);
//         writer.write("};\n");
//     }

//     public final String debug(final WoolySession session) {
//         if (session == null) throw new IllegalArgumentException();

//         final WoolyWriter writer = new WoolyWriter();

//         doDebug(session, writer);

//         return writer.toString();
//     }

//     public final String toString() {
//         return getName();
//     }
