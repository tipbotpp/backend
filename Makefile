# ——————— run ———————
.PHONY: run
run:
	uv run python3 -m src

# ——————— lines ———————
.PHONY: lines/scc
lines/scc:
	scc . --no-cocomo

.PHONY: lines
lines:
	git ls-files | xargs wc -l

# ——————— pre-commit ———————
.PHONY: pre-commit/install
pre-commit/install:
	uv run pre-commit install
	@echo "pre-commit hooks installed"

.PHONY: pre-commit/run
pre-commit/run:
	uv run pre-commit run --all-files

# ——————— ruff ———————
.PHONY: format
format:
	@ruff format . > /dev/null 2>&1
	@echo "code formatted"

.PHONY: lint
lint:
	ruff check .

.PHONY: lint/fix
lint/fix:
	ruff check . --fix

.PHONY: check
check:
	ruff check .
#	ruff format --check .

# ——————— alembic ———————
.PHONY: revision
revision:
	@read -p "Введите сообщение миграции: " msg;\
	uv run --active alembic revision --autogenerate -m "$$msg"

.PHONY: upgrade
upgrade:
	uv run --active alembic upgrade head

# ——————— uv ———————
.PHONY: sync
sync:
	uv sync

.PHONY: dev
dev: sync
	uv sync --dev

# ——————— pytest ———————
.PHONY: test
test: dev
	TEST_DB_URI=$(TEST_DB_URI) uv run pytest -q -ra --disable-warnings -m "unit"

.PHONY: test/coverage
test/coverage: dev
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html -m "not e2e"

.PHONY: test/repo
test/repo: dev
	TEST_DB_URI=$(TEST_DB_URI) uv run pytest -q -ra --disable-warnings -m "repo"

# ——————— pytest helpers ———————
.PHONY: get_markers
get_markers:
	uv run python tools/get_markers.py

.PHONY: mark_tests
mark_tests:
	uv run python tools/mark_tests.py

.PHONY: mark
mark: mark_tests get_markers