.PHONY: install test test-python test-terraform test-all lint format security semgrep clean

install:
	uv sync --locked --group dev --group lint
	cd tests/terraform && go mod tidy && go mod download

test: install lint test-python

test-all: install lint test-python test-terraform

test-python: install
	. $(PWD)/test.env && uv run pytest tests/ops/

test-terraform: install
	cd tests/terraform && PATH="$(PWD)/.venv/bin:$$PATH" go test -v -timeout 30m

test-coverage:
	. $(PWD)/test.env && uv run pytest \
		--cov=ops \
		--cov-report=term-missing \
		--cov-report=html \
		tests/ops/

lint:
	uv run ruff check ops/ tests/
	uv run black --check ops/ tests/
	cd tests/terraform && go vet ./...
	cd tests/terraform && gofmt -d .

format:
	uv run black ops/ tests/
	uv run ruff check --fix ops/ tests/
	cd tests/terraform && gofmt -w .

security:
	uvx bandit -i -s B101,B311 -r ops/ tests/

semgrep:
	uvx semgrep --error --verbose --config p/security-audit ops/ tests/

clean:
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	cd tests/terraform && go clean -testcache
