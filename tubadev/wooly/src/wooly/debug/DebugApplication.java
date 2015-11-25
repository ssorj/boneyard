package wooly.debug;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

public final class DebugApplication extends WoolyApplication {
    public DebugApplication(final String name,
                            final WoolyApplication parent) {
        super(name, parent);

        final WoolyPage page = new WoolyPage("page", this);
        setWidget(page);

        page.getTitle().set("Debug");

        page.add(new DebugPane("debug"));
    }
}
