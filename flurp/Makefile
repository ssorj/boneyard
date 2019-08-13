.PHONY: run
run: clean
	sudo docker build -t flurp .
	cat config.txt | sudo docker run -i flurp | tar --extract
	find test
	cat test/config.txt

.PHONY: clean
clean:
	rm -rf test

# cat setup.json |  docker run -i  ubuntu /bin/bash -c 'cat'
