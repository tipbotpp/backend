from abc import ABC, abstractmethod


class AbstractLogger(ABC):
	@abstractmethod
	def debug(self: "AbstractLogger", message: str, **kwargs: object) -> None:
		raise NotImplementedError

	@abstractmethod
	def info(self: "AbstractLogger", message: str, **kwargs: object) -> None:
		raise NotImplementedError

	@abstractmethod
	def warning(
		self: "AbstractLogger",
		message: str,
		**kwargs: object,
	) -> None:
		raise NotImplementedError

	@abstractmethod
	def error(self: "AbstractLogger", message: str, **kwargs: object) -> None:
		raise NotImplementedError

	@abstractmethod
	def critical(
		self: "AbstractLogger",
		message: str,
		**kwargs: object,
	) -> None:
		raise NotImplementedError

	@abstractmethod
	def bind(self: "AbstractLogger", **kwargs: object) -> "AbstractLogger":
		raise NotImplementedError
