.PHONY: test

test:
	rm -rf output
	scripts/generate
	g++ $$(find output/include -name \*.hpp)
	g++ -I output/include src/broker.cpp -o output/broker
	g++ -I output/include src/client.cpp -o output/client
	g++ -I output/include src/helloworld.cpp -o output/helloworld
	output/broker && echo $$?
	output/client && echo $$?
	output/helloworld && echo $$?
