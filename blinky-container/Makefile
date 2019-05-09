.PHONY: build
build:
	sudo docker build -t blinky --build-arg CACHE_BUST=$${RANDOM} .

.PHONY: restart
restart:
	sudo systemctl stop blinky-container
	sudo docker rm blinky
	sudo docker run -d --name blinky -p 56720:56720 blinky
	sudo systemctl start blinky-container
