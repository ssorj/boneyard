.PHONY: help tags clean

# version := 0.1.$(shell svn info | fgrep "Revision:" | cut -d " " -f 2)

help:
	@echo "Targets:"
	@echo "    help           Print this message"
	@echo "    clean          Remove build artifacts"
	@echo "    tags           Rebuild the tag index"

tags:
	find -name \*.py -print | etags -
	find -name \*.strings -print \
		| etags --append --regex='/^\[.*\][ \t]*$$/\1/' -

clean:
	$(MAKE) clean -C parsley
	$(MAKE) clean -C wooly
	$(MAKE) clean -C rosemary
	$(MAKE) clean -C mint
	$(MAKE) clean -C cumin
	$(MAKE) clean -C sage
