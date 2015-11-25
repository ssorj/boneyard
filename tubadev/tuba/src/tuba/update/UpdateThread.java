package tuba.update;

import java.util.*;
import smoky.*;

class UpdateThread extends SmokyQueueThread {
    UpdateThread(final UpdateModule module) {
        super("main", module);
    }

    protected void run(final Object obj) throws Exception {
        final UpdateModule module = (UpdateModule) getModule();

        module.log("Updating");

        module.getAdapter().update();

        //CaptureModule.get().getSession().schedule();
    }
}
