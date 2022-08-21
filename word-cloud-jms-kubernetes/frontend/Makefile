.PHONY: build
build:
	docker build -t frontend .

.PHONY: run
run: build
	docker run --rm -p 8080:8080 frontend

.PHONY: push
push:
