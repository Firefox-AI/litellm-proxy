PYTHON=python3
VENV=.venv
REQS=requirements.txt
REQS-DEV=requirements-dev.txt

.PHONY: all setup run clean qdrant-up

all: setup

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r $(REQS)
	$(VENV)/bin/pip install -r $(REQS-DEV)
	$(VENV)/bin/pip install -e .
	$(VENV)/bin/pre-commit install

litellm-proxy:
	$(VENV)/bin/litellm-proxy


clean:
	rm -rf __pycache__ .cache $(VENV)
