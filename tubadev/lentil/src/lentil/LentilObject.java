package lentil;

import java.lang.reflect.*;
import java.util.*;
import org.jdom.*;

public class LentilObject {
    private final LentilClass m_lclass;
    private boolean m_represented;

    protected LentilObject(final LentilClass lclass) {
        m_lclass = lclass;
        m_represented = false;
    }

    protected LentilObject(final Class jclass) {
        final Package jpackage = jclass.getPackage();

        if (jpackage == null) throw new IllegalStateException();

        final LentilPackage lpackage = LentilPackage.getPackage
            (jpackage.getName());

        m_lclass = lpackage.getClass(jclass);
        m_represented = false;
    }

    public LentilClass getLentilClass() {
        return m_lclass;
    }

    private boolean isRepresented() {
        return m_represented;
    }

    private void setRepresented(final boolean represented) {
        m_represented = represented;
    }

    public final Object getKey() {
        return getLentilClass().getKeyField().get(this);
    }

    public final void setKey(final Object value) {
        getLentilClass().getKeyField().set(this, value);
    }

    void load(final LentilSession session,
	      final String sql) throws LentilObjectNotFound {
        LentilCursor cursor = null;

        try {
            cursor = session.read(sql);

            if (!cursor.next()) {
                throw new LentilObjectNotFound();
            }

            load(cursor);
        } finally {
            if (cursor != null) cursor.close();
        }
    }

    // XXX I suddenly had to make this public?  I think I forgot
    // something
    public final void load(final LentilCursor cursor) {
        final Iterator iter = getLentilClass().getFields().values().iterator();

        while (iter.hasNext()) {
            final LentilField field = (LentilField) iter.next();

            field.set(this, field.get(cursor));
        }

        setRepresented(true);
    }

    protected void setNewKey(final LentilSession session) {
        setKey(getLentilClass().newKey(session));
    }

    protected void save(final LentilSession session) {
        if (isRepresented()) {
            if (update(session) == 0) {
                throw new IllegalStateException();
            }
        } else {
            if (insert(session) != 1) {
                throw new IllegalStateException();
            }
        }
    }

    protected int update(final LentilSession session) {
        return session.write(getLentilClass().getUpdateSql(this));
    }

    protected int insert(final LentilSession session) {
        return session.write(getLentilClass().getInsertSql(this));
    }

    protected int delete(final LentilSession session) {
        return session.write(getLentilClass().getDeleteSql(this));
    }

    private Map getSqlLiterals() {
        final Map map = new HashMap();
        final Iterator iter = getLentilClass().getFields().values().iterator();

        while (iter.hasNext()) {
            final LentilField field = (LentilField) iter.next();

            map.put(field.getColumn(), field.getSqlLiteral(this));
        }

        return map;
    }
}
