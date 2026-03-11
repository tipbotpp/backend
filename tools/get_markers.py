#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections.abc import Generator, Iterable
from pathlib import Path

PYTEST_MARK_RE = re.compile(
	r"pytest\.mark\.(?P<mark>[A-Za-z_][A-Za-z0-9_]*)",
)


def update_pytest_ini_markers(
	ini_path: Path,
	marks: Iterable[str],
	default_description: str = "auto-detected marker",
) -> None:
	"""
	Обновляет pytest.ini:
	- находит блок [pytest]
	- парсит markers =
	- добавляет отсутствующие маркеры
	- сохраняет описания существующих маркеров
	- остальные секции/опции не трогает
	"""
	marks = set(marks)

	if not ini_path.exists():
		raise FileNotFoundError(f"pytest.ini not found: {ini_path}")

	text = ini_path.read_text(encoding="utf-8")
	lines = text.splitlines(keepends=True)

	pytest_section_start = None
	for i, line in enumerate(lines):
		if line.strip().lower() == "[pytest]":
			pytest_section_start = i
			break

	if pytest_section_start is None:
		if lines and not lines[-1].endswith("\n"):
			lines[-1] = lines[-1] + "\n"
		lines.append("[pytest]\n")
		pytest_section_start = len(lines) - 1

	markers_start = None
	section_end = len(lines)

	for i in range(pytest_section_start + 1, len(lines)):
		stripped = lines[i].strip()
		if stripped.startswith("[") and stripped.endswith("]"):
			section_end = i
			break

	markers_line_re = re.compile(r"^\s*markers\s*=")

	for i in range(pytest_section_start + 1, section_end):
		if markers_line_re.match(lines[i]):
			markers_start = i
			break

	if markers_start is None:
		markers_start = pytest_section_start + 1
		markers_indent = ""
		existing_markers: dict[str, str] = {}
		markers_end = markers_start
	else:
		line = lines[markers_start]
		markers_indent = line[: line.index("m")] if "m" in line else ""
		i = markers_start + 1
		marker_lines: list[str] = []
		while i < section_end:
			if not lines[i].strip():
				break
			if lines[i][0] not in (" ", "\t"):
				break
			marker_lines.append(lines[i])
			i += 1
		markers_end = i

		existing_markers: dict[str, str] = {}
		for ml in marker_lines:
			s = ml.strip()
			if not s or s.startswith("#"):
				continue
			if ":" in s:
				name, desc = s.split(":", 1)
				existing_markers[name.strip()] = desc.strip()
			else:
				existing_markers[s] = ""

	all_names = set(existing_markers.keys()) | set(marks)

	new_block: list[str] = [f"{markers_indent}markers =\n"]

	for name in sorted(all_names):
		desc = existing_markers.get(name, default_description)
		if desc:
			new_block.append(f"{markers_indent}    {name}: {desc}\n")
		else:
			new_block.append(f"{markers_indent}    {name}\n")

	lines[markers_start:markers_end] = new_block

	ini_path.write_text("".join(lines), encoding="utf-8")


def collect_marks_in_file(path: Path) -> set[str]:
	text = path.read_text(encoding="utf-8")
	marks: set[str] = set()
	for match in PYTEST_MARK_RE.finditer(text):
		marks.add(match.group("mark"))
	return marks


def iter_python_files(root: Path) -> Generator[Path]:
	for path in root.rglob("test_*.py"):
		if path.name == "__init__.py":
			continue
		yield path


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Collect all pytest markers from tests and print them in pytest.ini format.",
	)
	parser.add_argument(
		"--root",
		type=str,
		default="tests",
		help="Root directory with tests (default: tests)",
	)
	args = parser.parse_args()

	root = Path(args.root)
	if not root.exists():
		raise SystemExit(f"Root path does not exist: {root}")

	all_marks: set[str] = set()

	for file in iter_python_files(root):
		try:
			file_marks = collect_marks_in_file(file)
		except UnicodeDecodeError:
			continue
		all_marks |= file_marks
	ini_path = Path("pytest.ini")
	update_pytest_ini_markers(ini_path, all_marks)
	print("pytest.ini updated")


if __name__ == "__main__":
	main()
