
force:

SCHEMADOCS = mace.xml condor-management-schema.xml sesame.xml
EXTRA_DIST = $(SCHEMADOCS)

qmfgen_cmd=$(QMF_GEN) -o $(srcdir)/qmf -m qmfgen.mk -p qmfgen $(SCHEMADOCS)

include qmfgen.mk

all : $(SCHEMADOCS)
	$(qmfgen_cmd)

clean:
	rm -rf $(srcdir)/qmf
