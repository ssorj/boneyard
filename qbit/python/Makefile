.PHONY: help hello client server

help:
	@echo "clean, hello, client, server"

hello:
	PN_TRACE_FRM=1 python -m qpid.peer.test hello localhost 5672

client:
	PN_TRACE_FRM=1 python -m qpid.peer.test client localhost 5672

server:
	PN_TRACE_FRM=1 python -m qpid.peer.test server localhost 5672

clean:
	find src -name \*.pyc -delete
