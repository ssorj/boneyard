package tuba.web;

import java.util.*;
import wooly.*;

public final class PageFooter extends WoolyWidget {
    public PageFooter(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write(new Date().toString());
    }
}
