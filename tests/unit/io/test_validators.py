"""Tests for mcp_xray.io.validators module."""

import pytest
from pydantic import BaseModel

from mcp_xray.io.validators import NoOpValidator, PydanticValidator


class TestNoOpValidator:
    """Tests for NoOpValidator class."""

    def test_validate_returns_data_unchanged(self):
        """Test that validate returns data unchanged."""
        validator = NoOpValidator()
        data = {"key": "value", "number": 42}

        result = validator.validate(data)

        assert result == data
        assert result is data  # Same object reference

    def test_validate_empty_dict(self):
        """Test validating empty dictionary."""
        validator = NoOpValidator()
        data = {}

        result = validator.validate(data)

        assert result == {}

    def test_validate_nested_data(self):
        """Test validating nested data structure."""
        validator = NoOpValidator()
        data = {"level1": {"level2": {"level3": [1, 2, 3]}}}

        result = validator.validate(data)

        assert result == data


class TestPydanticValidator:
    """Tests for PydanticValidator class."""

    def test_validate_with_simple_model(self):
        """Test validation with a simple Pydantic model."""

        class SimpleModel(BaseModel):
            name: str
            value: int

        validator = PydanticValidator(SimpleModel)
        data = {"name": "test", "value": 123}

        result = validator.validate(data)

        assert isinstance(result, SimpleModel)
        assert result.name == "test"
        assert result.value == 123

    def test_validate_with_nested_model(self):
        """Test validation with nested Pydantic models."""

        class InnerModel(BaseModel):
            inner_value: str

        class OuterModel(BaseModel):
            name: str
            inner: InnerModel

        validator = PydanticValidator(OuterModel)
        data = {"name": "outer", "inner": {"inner_value": "nested"}}

        result = validator.validate(data)

        assert isinstance(result, OuterModel)
        assert result.name == "outer"
        assert isinstance(result.inner, InnerModel)
        assert result.inner.inner_value == "nested"

    def test_validate_with_optional_fields(self):
        """Test validation with optional fields."""

        class ModelWithOptional(BaseModel):
            required: str
            optional: str | None = None

        validator = PydanticValidator(ModelWithOptional)
        data = {"required": "value"}

        result = validator.validate(data)

        assert result.required == "value"
        assert result.optional is None

    def test_validate_with_default_values(self):
        """Test validation with default values."""

        class ModelWithDefaults(BaseModel):
            name: str
            count: int = 0
            enabled: bool = True

        validator = PydanticValidator(ModelWithDefaults)
        data = {"name": "test"}

        result = validator.validate(data)

        assert result.name == "test"
        assert result.count == 0
        assert result.enabled is True

    def test_validate_invalid_data_raises_error(self):
        """Test that invalid data raises ValueError."""

        class StrictModel(BaseModel):
            name: str
            value: int

        validator = PydanticValidator(StrictModel)
        data = {"name": "test", "value": "not an int"}

        with pytest.raises(ValueError) as exc_info:
            validator.validate(data)

        assert "Pydantic validation failed" in str(exc_info.value)

    def test_validate_missing_required_field_raises_error(self):
        """Test that missing required field raises ValueError."""

        class RequiredFieldModel(BaseModel):
            required_field: str

        validator = PydanticValidator(RequiredFieldModel)
        data = {}

        with pytest.raises(ValueError) as exc_info:
            validator.validate(data)

        assert "Pydantic validation failed" in str(exc_info.value)

    def test_validate_extra_fields_ignored_by_default(self):
        """Test that extra fields are ignored by default."""

        class SimpleModel(BaseModel):
            name: str

        validator = PydanticValidator(SimpleModel)
        data = {"name": "test", "extra": "ignored"}

        result = validator.validate(data)

        assert result.name == "test"
        assert not hasattr(result, "extra")

    def test_validate_with_list_field(self):
        """Test validation with list field."""

        class ModelWithList(BaseModel):
            items: list[str]

        validator = PydanticValidator(ModelWithList)
        data = {"items": ["a", "b", "c"]}

        result = validator.validate(data)

        assert result.items == ["a", "b", "c"]

    def test_validate_with_dict_field(self):
        """Test validation with dict field."""

        class ModelWithDict(BaseModel):
            mapping: dict[str, int]

        validator = PydanticValidator(ModelWithDict)
        data = {"mapping": {"one": 1, "two": 2}}

        result = validator.validate(data)

        assert result.mapping == {"one": 1, "two": 2}

    def test_validator_stores_model_class(self):
        """Test that validator stores the model class."""

        class TestModel(BaseModel):
            field: str

        validator = PydanticValidator(TestModel)

        assert validator.model_class is TestModel
