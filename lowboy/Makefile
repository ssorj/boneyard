.PHONY: default test setup

ifndef LOWBOY_HOME
    $(error "Run 'source config.sh' first")
endif

tmp_dir := ${LOWBOY_TMP_DIR}

default: test

test:
	scripts/director | scripts/executor-python
	scripts/director | scripts/executor-ruby

setup:
	rm -rf ${tmp_dir}
	mkdir -p ${tmp_dir}
	mkdir ${tmp_dir}/proton-build
	mkdir ${tmp_dir}/proton-install
	svn export "https://svn.apache.org/repos/asf/qpid/proton/trunk" ${tmp_dir}/proton-source
	cd ${tmp_dir}/proton-build && cmake ${tmp_dir}/proton-source
	cd ${tmp_dir}/proton-build && make -j4
	cd ${tmp_dir}/proton-build && make install DESTDIR=${tmp_dir}/proton-install
