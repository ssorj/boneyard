.PHONY: build
build:
	docker build -t processor .

.PHONY: run
run: build
	docker run --rm processor

.PHONY: push
push:
