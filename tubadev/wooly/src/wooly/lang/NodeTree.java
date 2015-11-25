package wooly.lang;

import java.util.*;
import wooly.*;

final class NodeTree {
    private final Node m_root;
    private final WoolyModel m_model;
    private final Map m_nodes;
    private final Map m_widgets;

    NodeTree(final Node root, final WoolyModel model) {
        m_root = root;
        m_model = model;
        m_nodes = new HashMap();
        m_widgets = new HashMap();
    }

    WoolyModel getModel() {
        return m_model;
    }

    // XXX remove
    Map getIndex() {
        return m_nodes;
    }

    Map getNodes() {
        return m_nodes;
    }

    Map getWidgets() {
        return m_widgets;
    }

    Node getNode(final String path) {
        return (Node) getNodes().get(path);
    }

    WoolyWidget getWidget(final Node node) {
        return (WoolyWidget) getWidgets().get(node);
    }

    WoolyWidget getWidget(final String path) {
        return getWidget(getNode(path));
    }

    void index() {
        index(m_root, "");
    }

    private void index(final Node node, String path) {
        path = path + "." + node.name;

        getNodes().put(path, node);

        for (final Node child : node.children) {
            index(child, path);
        }
    }

    WoolyWidget build() {
        return build(m_root, null);
    }

    private WoolyWidget build(final Node node, WoolyWidget parent) {
        final WoolyWidget widget = node.build(this);

        if (widget != null) {
            getWidgets().put(node, widget);

            if (parent != null) {
                parent.add(widget);
            }

            parent = widget;
        }

        for (final Node child : node.children) {
            build(child, widget);
        }

        return widget;
    }

    void configure() {
        configure(m_root);
    }

    private void configure(final Node node) {
        node.configure(this);

        System.out.println("node " + node.name + " " + node.children);

        for (final Node child : node.children) {
            configure(child);
        }
    }
}