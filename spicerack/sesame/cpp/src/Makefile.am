SUBDIRS = qmfgen
sesame_CXXFLAGS = $(QPID_CXXFLAGS) -Iqmfgen \
	-DCONF_FILE=\"$(sysconfdir)/sesame/sesame.conf\" \
	-DLOCSTATE_DIR=\"$(localstatedir)/lib/sesame\" \
	$(DBUS_CFLAGS) \
	-I$(QPID_INCLUDE)

include qmfgen/qmfgen.mk

bin_PROGRAMS = sesame
nodist_sesame_SOURCES = $(qmfgen_sources)
sesame_SOURCES = SysAgent.cpp

sesame_LDADD = $(QPID_LIBS) $(DBUS_LIBS)
