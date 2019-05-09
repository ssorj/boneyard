.PHONY: build
build:
	sudo docker build -t stagger --build-arg CACHE_BUST=$${RANDOM} .

.PHONY: restart
restart:
	sudo systemctl stop stagger-container
	sudo docker rm stagger
	sudo docker run -d --name stagger -p 56721:8080 stagger
	sudo systemctl start stagger-container
