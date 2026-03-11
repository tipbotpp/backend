from typing import Any

from sqlalchemy import Select, and_, or_
from sqlalchemy.orm import ORMExecuteState, with_loader_criteria
from sqlalchemy.sql.selectable import Join


def filter_soft_deleted(execute_state: ORMExecuteState) -> None:
	"""
	Автоматически фильтрует записи с deleted_at != None
	для всех SELECT запросов, если не указано обратное.

	Поддерживает исключение конкретных таблиц через execution_options:
	session.exclude_soft_delete_for('table_name')
	"""
	from src.models.mixins import SoftDeleteMixin

	if not execute_state.is_select:
		return

	if execute_state.is_column_load or execute_state.is_relationship_load:
		return

	if execute_state.execution_options.get("include_deleted", False):
		return

	stmt = execute_state.statement
	if not isinstance(stmt, Select):
		execute_state.statement = execute_state.statement.options(
			with_loader_criteria(
				SoftDeleteMixin,
				lambda cls: cls.deleted_at.is_(None),
				include_aliases=True,
			),
		)
		return

	exclude_tables = execute_state.execution_options.get(
		"exclude_tables_from_soft_delete",
		set(),
	)
	exclude_set = frozenset(exclude_tables) if exclude_tables else frozenset()

	conditions = []
	processed_tables = set()

	def extract_table_info(table: Any) -> Any:  # noqa: ANN401
		if hasattr(table, "entity"):
			return table.entity
		if hasattr(table, "element"):
			return extract_table_info(table.element)
		return None

	def is_outer_join(froms: Any, table_name: Any) -> bool:  # noqa: ANN401
		for from_clause in froms:
			if isinstance(from_clause, Join):
				if from_clause.isouter and str(table_name) in str(from_clause):
					return True
				if hasattr(from_clause, "left") and is_outer_join(
					[from_clause.left],
					table_name,
				):
					return True
				if hasattr(from_clause, "right") and is_outer_join(
					[from_clause.right],
					table_name,
				):
					return True
		return False

	for from_clause in stmt.get_final_froms():
		tables_to_check = [from_clause]

		while tables_to_check:
			current = tables_to_check.pop(0)

			if isinstance(current, Join):
				if hasattr(current, "left"):
					tables_to_check.append(current.left)
				if hasattr(current, "right"):
					tables_to_check.append(current.right)
				continue

			model = extract_table_info(current)
			if model is None:
				continue

			if not hasattr(model, "deleted_at"):
				continue

			table_name = getattr(model, "__tablename__", None)
			class_name = getattr(model, "__name__", None)

			if (
				table_name in processed_tables
				or class_name in processed_tables
			):
				continue

			if table_name in exclude_set or class_name in exclude_set:
				continue

			processed_tables.add(table_name or class_name)

			is_outer = is_outer_join(
				stmt.get_final_froms(),
				table_name or class_name,
			)

			if is_outer and hasattr(model, "id"):
				conditions.append(
					or_(model.deleted_at.is_(None), model.id.is_(None)),
				)
			else:
				conditions.append(model.deleted_at.is_(None))

	if conditions:
		modified_stmt = stmt.where(and_(*conditions))
		execute_state.statement = modified_stmt
	else:
		execute_state.statement = execute_state.statement.options(
			with_loader_criteria(
				SoftDeleteMixin,
				lambda cls: cls.deleted_at.is_(None),
				include_aliases=True,
			),
		)
