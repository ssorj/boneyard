package tuba.datadirect;

import tuba.runtime.model.*;
import tuba.update.*;

public final class DataDirectAdapter implements UpdateAdapter {
    public void update() {
        final DataDirectSession session = DataDirectModule.getModule
            ().getSession();

        try {
            session.open();

            session.authenticate();
            session.update();
        } finally {
            session.close();
        }
    }
}
