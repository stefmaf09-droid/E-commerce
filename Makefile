# Makefile with convenience targets
.PHONY: audit audit-report

# Run pip-audit and fail on high
audit:
	python -m pip install --upgrade pip
	python -m pip install pip-audit
	pip-audit --fail-on high

# Generate a JSON report without failing
audit-report:
	python -m pip install --upgrade pip
	python -m pip install pip-audit
	pip-audit --format json --output pip-audit.json

authors:
	@echo "Maintainers: stefmaf09-droid"

.PHONY: e2e

e2e:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt
	python -m playwright install --with-deps
	pytest tests/e2e -q
