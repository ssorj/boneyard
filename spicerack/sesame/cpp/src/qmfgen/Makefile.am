
.PHONY: force

force:

EXTRA_DIST = schema.xml

qmfgen_cmd=$(QMF_GEN) -o $(srcdir)/qmf -m qmfgen.mk -p $$\(top_srcdir\)/src/qmfgen schema.xml

include qmfgen.mk

all : schema.xml
	$(qmfgen_cmd)

clean:
	rm -rf $(srcdir)/qmf
