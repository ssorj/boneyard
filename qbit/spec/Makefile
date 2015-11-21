.PHONY: help generate prepare clean test

tmpdir := $(shell mktemp -d)
pygments_style := monokai

generate: \
	prepare \
	output/peer

prepare: clean
#	mkdir -p output/peer/examples
#	mkdir -p output/peer/resources
#	cp -a input/peer/resources/* output/peer/resources

help:
	@echo "generate, clean, test"

clean:
	$(MAKE) -C tools/pumpjack $@
	rm -rf output

test: generate
	python output/peer/module.py

	javac output/peer/module.java

	echo 'int main(int argc, char ** argv) {}' > ${tmpdir}/test.c
	gcc -std=c99 -pedantic -include output/peer/module.c -o ${tmpdir}/test.o ${tmpdir}/test.c

output/%: input/%
	pumpjack -r c -i $< -o $@
	pumpjack -r java -i $< -o $@
	pumpjack -r python -i $< -o $@
	cp $</module.xml $@/module.xml

	mv output/$*/module.python output/$*/module.py

	colorize output/$*/module.c output/$*/module.c.html 
	colorize output/$*/module.java output/$*/module.java.html 
	colorize output/$*/module.py output/$*/module.py.html 
	colorize output/$*/module.xml output/$*/module.xml.html

	pumpjack -r html -i $< -o $@

# output/peer/examples/%: input/peer/examples/%
# 	cp $< $@
# 	pygmentize -l `echo $* | cut -d . -f 2` -f html -O style=${pygments_style} $< >> $@.include
# 	bin/templatize input/peer/templates/example.html $@.include $@.html
# 	rm $@.include

# epydoc: output/peer/module.python
# 	PYTHONPATH=output epydoc --output output/peer/epydoc peer.module
