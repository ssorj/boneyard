export PYTHONPATH := ${PWD}/python

.PHONY: render
render: clean
	scripts/gen-jiropticon input/upstream.md "http://issues.apache.org/jira" ARTEMIS DISPATCH PROTON QPID QPIDJMS
	scripts/gen-jiropticon input/downstream.md "http://issues.jboss.org" ENTMQBR ENTMQCL ENTMQIC
	transom input output

.PHONY: clean
clean:
	rm -rf output
	find python -type f -name \*.pyc -delete

.PHONY: clean-cache
clean-cache:
	rm -rf /tmp/${USER}/lintel

.PHONY: update-plano
update-plano:
	curl "https://raw.githubusercontent.com/ssorj/plano/master/python/plano.py" -o python/plano.py

.PHONY: update-pencil
update-pencil:
	curl "https://raw.githubusercontent.com/ssorj/pencil/master/python/pencil.py" -o python/pencil.py
