SUBDIRS = qmfgen
mace_CXXFLAGS = -I$(QPID_DIR)/cpp/src -I$(QPID_DIR)/cpp/src/gen -Iqmfgen \
	-DCONF_FILE=\"$(sysconfdir)/mace.conf\" \
	-DLOCSTATE_DIR=\"$(localstatedir)/mace\"

include qmfgen/qmfgen.mk

bin_PROGRAMS = mace
nodist_mace_SOURCES = $(qmfgen_sources)
mace_SOURCES = GridSim.cpp

mace_LDADD = $(QPID_LIBS)


