package smoky;

import java.util.*;

public abstract class SmokyQueueThread implements Runnable {
    private final String m_name;
    private final SmokyModule m_module;
    private final LinkedList m_queue;
    private volatile Thread m_thread;

    public SmokyQueueThread(final String name, final SmokyModule module) {
        m_name = name;
        m_module = module;
        m_queue = new LinkedList();
    }

    public final String getName() {
        return m_name;
    }

    public final SmokyModule getModule() {
        return m_module;
    }

    public void start() {
        if (m_thread != null) throw new IllegalStateException();

        m_thread = new Thread(this, getName());
        m_thread.start();
    }

    public void stop() {
        if (m_thread == null) throw new IllegalStateException();

        final Thread thread = m_thread;

        m_thread = null;

        thread.interrupt();
    }

    public final void send(final Object obj) {
        synchronized (m_queue) {
            m_queue.addLast(obj);
        }
    }

    public final void run() {
        final Thread current = Thread.currentThread();

        while (m_thread == current) {
            try {
                if (m_queue.size() == 0) {
                    Thread.sleep(200);
                } else {
                    // Receive
                    run(m_queue.removeFirst());
                }
            } catch (InterruptedException e) {
            } catch (Exception e) {
                try {
                    log(e);
                } catch (Exception ie) {
                    System.out.println(ie.getMessage());
                }
            }
        }
    }

    protected abstract void run(final Object obj) throws Exception;

    protected final void log(final Exception e) {
        getModule().log(e);
    }

    protected final void log(final String message) {
        getModule().log(message);
    }

    protected final void log(final int threshold, final String message) {
        getModule().log(threshold, message);
    }
}
