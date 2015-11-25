package tuba.web;

import wooly.*;

public final class PageHeader extends WoolyWidget {
    public PageHeader(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<h>Tuba Web</h>");
    }
}
