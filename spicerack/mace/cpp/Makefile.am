AUTOMAKE_OPTIONS = 1.9.6 foreign
ACLOCAL_AMFLAGS = -I m4


EXTRA_DIST = README etc/mace.conf

sysconf_DATA = etc/mace.conf

SUBDIRS = src

# Update libtool, if needed.
libtool: $(LIBTOOL_DEPS)
	$(SHELL) ./config.status --recheck

