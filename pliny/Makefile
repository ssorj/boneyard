#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

.PHONY: build install clean gen-cabinet-doc

BUILD_DIR := build
PREFIX := /usr/local

build: files/slideshow.pdf
	md5sum --check python/cherrypy.checksum
	md5sum --check python/polly.checksum
	mkdir -p ${BUILD_DIR}/bin

	cp bin/pliny-web.in ${BUILD_DIR}/bin/pliny-web.in
	sed -i 's|@pliny_config@|${PREFIX}/etc/pliny/pliny.conf|g' ${BUILD_DIR}/bin/pliny-web.in
	sed -i 's|@pliny_home@|${PREFIX}/share/pliny|g' ${BUILD_DIR}/bin/pliny-web.in
	mv ${BUILD_DIR}/bin/pliny-web.in ${BUILD_DIR}/bin/pliny-web

	cp bin/pliny-admin.in ${BUILD_DIR}/bin/pliny-admin.in
	sed -i 's|@pliny_config@|${PREFIX}/etc/pliny/pliny.conf|g' ${BUILD_DIR}/bin/pliny-admin.in
	sed -i 's|@pliny_home@|${PREFIX}/share/pliny|g' ${BUILD_DIR}/bin/pliny-admin.in
	mv ${BUILD_DIR}/bin/pliny-admin.in ${BUILD_DIR}/bin/pliny-admin

	cp bin/pliny-bench.in ${BUILD_DIR}/bin/pliny-bench.in
	sed -i 's|@pliny_config@|${PREFIX}/etc/pliny/pliny.conf|g' ${BUILD_DIR}/bin/pliny-bench.in
	sed -i 's|@pliny_home@|${PREFIX}/share/pliny|g' ${BUILD_DIR}/bin/pliny-bench.in
	mv ${BUILD_DIR}/bin/pliny-bench.in ${BUILD_DIR}/bin/pliny-bench

	chmod 755 ${BUILD_DIR}/bin/pliny-bench

install: build
	install -d ${PREFIX}/share/pliny/python/cherrypy/wsgiserver
	install -d ${PREFIX}/share/pliny/python/polly
	install -d ${PREFIX}/share/pliny/python/cabinet
	install -d ${PREFIX}/share/pliny/python/pliny/web
	install -d ${PREFIX}/bin
	install -d ${PREFIX}/etc/pliny
	install -d ${PREFIX}/share/pliny/files

	install python/cherrypy/*.py \
		${PREFIX}/share/pliny/python/cherrypy
	install python/cherrypy/wsgiserver/*.py \
		${PREFIX}/share/pliny/python/cherrypy/wsgiserver
	install python/polly/*.py \
		${PREFIX}/share/pliny/python/polly
	install python/cabinet/*.py python/cabinet/*.strings \
		${PREFIX}/share/pliny/python/cabinet
	install python/pliny/*.py \
		${PREFIX}/share/pliny/python/pliny
	install python/pliny/web/*.py python/pliny/web/*.strings \
		${PREFIX}/share/pliny/python/pliny/web

	install ${BUILD_DIR}/bin/pliny-web ${PREFIX}/bin
	install ${BUILD_DIR}/bin/pliny-admin ${PREFIX}/bin
	install ${BUILD_DIR}/bin/pliny-bench ${PREFIX}/bin
	install etc/pliny.conf etc/insecure.pem ${PREFIX}/etc/pliny

	cp -a files/* ${PREFIX}/share/pliny/files

clean:
	find python -type f -name \*.pyc -delete
	rm -rf build
	rm -rf install

gen-cabinet-doc:
	rm -rf build/doc/cabinet
	mkdir -p build/doc
	epydoc --no-private --no-frames --include-log --verbose \
	    --inheritance included \
	    --output build/doc/cabinet \
	    python/cabinet 

files/slideshow.pdf: doc/slideshow.md
	pandoc -t beamer $< -o $@
