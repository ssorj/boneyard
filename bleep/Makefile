.PHONY: run
run: build
	java -cp twiddle/target/twiddle-1.0.0-SNAPSHOT-jar-with-dependencies.jar twiddle.Main "amqp://localhost"

.PHONY: build
build:
	cd twiddle && mvn package

.PHONY: clean
clean:
	cd twiddle && mvn clean
