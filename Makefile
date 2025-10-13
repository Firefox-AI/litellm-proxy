PYTHON-VERSION=3.12
VENV=.venv
REQS=requirements.txt
REQS-DEV=requirements-dev.txt

.PHONY: all setup run clean qdrant-up

all: setup

setup:
	uv venv --python $(PYTHON-VERSION)
	uv pip install -r $(REQS)
	uv pip install -r $(REQS-DEV)
	uv run pre-commit install
	@echo ""
	@echo "✅ Setup complete! To activate your environment, run:"
	@echo "   source .venv/bin/activate"

install:
	uv pip install --no-cache-dir -e .

litellm-proxy:
	$(VENV)/bin/litellm-proxy


clean:
	rm -rf __pycache__ .cache $(VENV)
