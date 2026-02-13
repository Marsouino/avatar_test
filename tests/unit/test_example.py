"""Example unit tests demonstrating testing patterns.

These tests show:
1. GIVEN/WHEN/THEN pattern for clarity
2. Testing fail-fast behavior (expected exceptions)
3. Meaningful assertions (not just `assert True`)
"""

from typing import Any

import pytest
from pydantic import ValidationError

from src.models.base import StrictModel

# =============================================================================
# Example: Testing a Pydantic model
# =============================================================================


class UserConfig(StrictModel):
    """Example model for testing."""

    name: str
    age: int


class TestStrictModelBehavior:
    """Tests for StrictModel base class behavior."""

    def test_valid_data_creates_model(self) -> None:
        """Valid data should create a model instance.

        GIVEN: Valid input data matching the model schema
        WHEN: Creating a model instance
        THEN: Instance is created with correct values
        """
        # GIVEN
        name = "Alice"
        age = 30

        # WHEN
        config = UserConfig(name=name, age=age)

        # THEN
        assert config.name == name
        assert config.age == age

    def test_wrong_type_raises_validation_error(self) -> None:
        """Wrong type should raise ValidationError (fail-fast).

        GIVEN: Data with wrong type (string instead of int)
        WHEN: Creating a model instance
        THEN: ValidationError is raised immediately
        """
        # GIVEN
        name = "Alice"
        age_as_string = "30"  # Wrong type!

        # WHEN/THEN
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(name=name, age=age_as_string)  # type: ignore

        # Verify the error is about the 'age' field
        assert "age" in str(exc_info.value)

    def test_extra_field_raises_validation_error(self) -> None:
        """Extra fields should raise ValidationError (fail-fast).

        GIVEN: Data with an unknown extra field
        WHEN: Creating a model instance
        THEN: ValidationError is raised immediately
        """
        # WHEN/THEN
        with pytest.raises(ValidationError) as exc_info:
            UserConfig(name="Alice", age=30, unknown_field="oops")  # type: ignore

        # Verify the error mentions extra fields
        assert "extra" in str(exc_info.value).lower()

    def test_model_is_immutable(self) -> None:
        """Model should be immutable (frozen=True).

        GIVEN: A created model instance
        WHEN: Attempting to modify an attribute
        THEN: ValidationError is raised
        """
        # GIVEN
        config = UserConfig(name="Alice", age=30)

        # WHEN/THEN
        with pytest.raises(ValidationError):
            config.name = "Bob"


# =============================================================================
# Example: Testing fail-fast validation
# =============================================================================


def validate_config(config: dict[str, Any]) -> None:
    """Example function that validates configuration.

    Raises:
        ValueError: If required keys are missing
    """
    if "input_path" not in config:
        raise ValueError("[X] config.input_path is required")
    if "output_path" not in config:
        raise ValueError("[X] config.output_path is required")


class TestFailFastValidation:
    """Tests for fail-fast validation behavior."""

    def test_valid_config_passes(self, sample_config: dict[str, Any]) -> None:
        """Valid config should pass validation without error.

        GIVEN: A valid configuration with all required keys
        WHEN: Validating the configuration
        THEN: No exception is raised
        """
        # WHEN/THEN (no exception)
        validate_config(sample_config)

    def test_missing_input_path_raises_value_error(self) -> None:
        """Missing input_path should raise ValueError with clear message.

        GIVEN: Configuration missing input_path
        WHEN: Validating the configuration
        THEN: ValueError is raised with descriptive message
        """
        # GIVEN
        config = {"output_path": "/path/to/output"}

        # WHEN/THEN
        with pytest.raises(ValueError) as exc_info:
            validate_config(config)

        # Verify error message is clear and actionable
        assert "[X]" in str(exc_info.value)
        assert "input_path" in str(exc_info.value)

    def test_missing_output_path_raises_value_error(self) -> None:
        """Missing output_path should raise ValueError with clear message.

        GIVEN: Configuration missing output_path
        WHEN: Validating the configuration
        THEN: ValueError is raised with descriptive message
        """
        # GIVEN
        config = {"input_path": "/path/to/input"}

        # WHEN/THEN
        with pytest.raises(ValueError) as exc_info:
            validate_config(config)

        # Verify error message is clear and actionable
        assert "[X]" in str(exc_info.value)
        assert "output_path" in str(exc_info.value)
