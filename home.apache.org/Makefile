.PHONY: render
render: clean
	transom input output

.PHONY: clean
clean:
	rm -rf output

.PHONY: publish
publish: temp_dir := $(shell mktemp -d)
publish: temp_script := $(shell mktemp)
publish:
	chmod 755 ${temp_dir}
	transom input ${temp_dir} --site-url "http://home.apache.org/~jross"
#	rsync -av ${temp_dir}/ jross@home.apache.org:public_html
	echo 'lcd ${temp_dir}' >> ${temp_script}
	cd ${temp_dir} && find * -type d -exec echo '-mkdir {}' \; >> ${temp_script}
	cd ${temp_dir} && find * -type f -exec echo 'put {} {}' \; >> ${temp_script}
	sftp -b ${temp_script} jross@home.apache.org:public_html
	rm -rf ${temp_dir}
	rm ${temp_script}
