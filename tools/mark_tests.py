#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from pathlib import Path

DEF_TEST_RE = re.compile(
    r"^\s*(?:async\s+def|def)\s+(test_[A-Za-z0-9_]+)\s*\(",
    re.M,
)
DECORATOR_RE = re.compile(r"^[ \t]*@.+", re.M)
PYTEST_MARK_RE = re.compile(
    r"^[ \t]*@pytest\.mark\.(?P<mark>[A-Za-z0-9_]+)\s*$",
)

API_PATH_WITH_HANDLER_RE = re.compile(
	r"""
	tests[/\\]api[/\\]v\d+[/\\]endpoints[/\\]
	(?P<router>[^/\\]+)[/\\]
	(?P<handler>[^/\\]+)[/\\]
	(?P<case>[^/\\]+)\.py$
	""",
	re.X,
)

API_PATH_FLAT_RE = re.compile(
	r"""
	tests[/\\]api[/\\]v\d+[/\\]endpoints[/\\]
	(?P<router>[^/\\]+)[/\\]
	(?P<case>[^/\\]+)\.py$
	""",
	re.X,
)

REPO_PATH_RE = re.compile(
    r"""^.*tests[/\\]repositories[/\\](?P<repo>[^/\\]+)[/\\](?P<method>[^/\\]+)[/\\].+\.py$""",
    re.X,
)

# 🔥 НОВОЕ: сервисы
SERVICE_PATH_RE = re.compile(
    r"""^.*tests[/\\]services[/\\]
        (?P<group>[^/\\]+)[/\\]          # например auth
        (?P<service>[^/\\]+)[/\\]        # например token / auth / verification
        (?P<method>[^/\\]+)[/\\]         # например create_access_token / register
        .+\.py$
    """,
    re.X,
)


def marks_from_path(path: Path) -> list[str] | None:
	s = str(path)

	# api with handler subfolder
	m_api = API_PATH_WITH_HANDLER_RE.search(s)
	if m_api:
		router = m_api.group("router")
		handler = m_api.group("handler")
		marks = ["anyio", "api", "unit", router, handler]
		if "ws" in router or "websocket" in s:
			marks.append("ws")
		return marks

	# api flat (tests directly under router)
	m_api_flat = API_PATH_FLAT_RE.search(s)
	if m_api_flat:
		router = m_api_flat.group("router")
		case = m_api_flat.group("case")
		marks = ["anyio", "api", "unit", router, case]
		if "ws" in router or "websocket" in s:
			marks.append("ws")
		return marks

	# repositories
	m_repo = REPO_PATH_RE.search(s)
	if m_repo:
		repo = m_repo.group("repo")
		method = m_repo.group("method")
		return ["anyio", "repo", "unit", repo, method]

	# 🔥 services
	m_service = SERVICE_PATH_RE.search(s)
	if m_service:
		group = m_service.group("group")       # auth
		service = m_service.group("service")   # token / auth / verification
		method = m_service.group("method")     # create_access_token / register / ...
		return ["anyio", "service", "unit", group, service, method]

	return None


def ensure_import_pytest(lines: list[str]) -> list[str]:
    if any("import pytest" in line for line in lines):
        return lines

    idx: int = 0
    while idx < len(lines) and lines[idx].strip() in (
        "",
        "# -*- coding: utf-8 -*-",
        "#!/usr/bin/env python3",
    ):
        idx += 1

    if idx < len(lines) and lines[idx].lstrip().startswith(("'''", '"""')):
        quote = lines[idx].lstrip()[:3]
        idx += 1
        while idx < len(lines):
            if lines[idx].rstrip().endswith(quote):
                idx += 1
                break
            idx += 1

    lines[idx:idx] = ["import pytest\n"]
    return lines


def iter_test_function_blocks(
    lines: list[str],
) -> Iterable[tuple[int, int, int, str]]:
    i: int = 0
    n: int = len(lines)
    while i < n:
        if DEF_TEST_RE.match(lines[i]):
            def_start: int = i
            deco_start: int = i
            j: int = i - 1
            while j >= 0 and DECORATOR_RE.match(lines[j]):
                deco_start = j
                j -= 1
            name_match = DEF_TEST_RE.match(lines[def_start])
            test_name: str = name_match.group(1) if name_match else ""
            yield deco_start, def_start, i, test_name
        i += 1


def collect_existing_marks(decorator_lines: list[str]) -> set[str]:
    marks: set[str] = set()
    for line in decorator_lines:
        m = PYTEST_MARK_RE.match(line.strip())
        if m:
            marks.add(m.group("mark"))
    return marks


def add_mark_decorators(
    lines: list[str],
    required_marks: list[str],
) -> tuple[list[str], bool]:
    changed: bool = False
    i: int = 0
    while i < len(lines):
        if not DEF_TEST_RE.match(lines[i]):
            i += 1
            continue

        def_idx: int = i
        deco_start: int = def_idx

        j: int = def_idx - 1
        while j >= 0 and DECORATOR_RE.match(lines[j]):
            deco_start = j
            j -= 1

        existing_decorators: list[str] = lines[deco_start:def_idx]
        existing_marks = collect_existing_marks(existing_decorators)

        to_add: list[str] = []
        for mark in required_marks:
            if mark not in existing_marks:
                to_add.append(f"@pytest.mark.{mark}\n")

        if to_add:
            lines[deco_start:deco_start] = to_add
            i += len(to_add)
            changed = True

        i += 1

    return lines, changed


def process_file(path: Path, dry_run: bool = False) -> bool:
    required_marks = marks_from_path(path)
    if not required_marks:
        return False

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    original = "".join(lines)

    lines = ensure_import_pytest(lines)
    lines, _ = add_mark_decorators(lines, required_marks)

    modified = "".join(lines)
    if modified != original:
        if not dry_run:
            path.write_text(modified, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mark pytest tests with api/repo/service/unit/... markers based on file path.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default="tests",
        help="Root directory to scan (default: tests)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write changes, only report",
    )
    args = parser.parse_args()

    root = Path(args.root)
    files = list(root.rglob("test_*.py"))
    touched: int = 0

    for file in files:
        if "__init__.py" in str(file):
            continue
        if process_file(file, dry_run=args.dry_run):
            touched += 1

    print(f"done. files updated: {touched}")


if __name__ == "__main__":
    main()
