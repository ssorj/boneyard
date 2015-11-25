package wooly.lang;

import java.lang.reflect.*;
import java.util.*;
import wooly.*;

class ReflectionWidgetNode extends Node {
    String type;

    WoolyWidget build(final NodeTree tree) {
        if (type == null) throw new IllegalStateException();

        final Class clacc;

        try {
            clacc = Class.forName(type);
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException(e);
        }

        final Constructor cons;

        try {
            cons = clacc.getConstructor(String.class, WoolyModel.class);
        } catch (NoSuchMethodException e) {
            throw new IllegalStateException(e);
        } catch (SecurityException e) {
            throw new IllegalStateException(e);
        }

        final WoolyWidget widget;

        try {
            widget = (WoolyWidget) cons.newInstance(name, tree.getModel());
        } catch (IllegalAccessException e) {
            throw new IllegalStateException(e);
        } catch (InstantiationException e) {
            throw new IllegalStateException(e);
        } catch (InvocationTargetException e) {
            throw new IllegalStateException(e);
        }

        return widget;
    }
}
