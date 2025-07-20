from typing import Any, Protocol

from pydantic import BaseModel


class DataValidator(Protocol):
    """Protocol for validating loaded data."""

    def validate(self, data: dict[str, Any]) -> Any:
        """Validate and potentially transform the data."""
        ...


class NoOpValidator:
    """Validator that returns data unchanged."""

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        return data


class PydanticValidator:
    """Validator for Pydantic BaseModel classes."""

    def __init__(self, model_class: type[BaseModel]) -> None:
        self.model_class = model_class

    def validate(self, data: dict[str, Any]) -> BaseModel:
        try:
            return self.model_class.model_validate(data)
        except Exception as e:
            msg = f"Pydantic validation failed: {e}"
            raise ValueError(msg) from e
