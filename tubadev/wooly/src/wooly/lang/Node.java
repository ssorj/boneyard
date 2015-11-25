package wooly.lang;

import java.util.*;
import wooly.*;

abstract class Node {
    String name;
    Node parent;
    List<Node> children;

    Node() {
        children = new ArrayList();
    }

    WoolyWidget build(final NodeTree tree) {
        return null;
    }

    void configure(final NodeTree tree) {
    }
}

/*

        for (int i = 0; i < modes.children.size(); i++) {
            final Node child = (Node) modes.children.get(i);

            if (child.name.equals(token.image)) {
                tab.mode = child;
                break;
            }
        }

*/