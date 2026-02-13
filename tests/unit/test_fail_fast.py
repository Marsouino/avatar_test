"""Tests that verify fail-fast behavior.

These tests ensure that functions properly raise exceptions
on invalid input, rather than silently using fallback values.

Pattern: For each function that takes required parameters,
write a test that verifies it raises on missing/invalid input.

Mark these tests with @pytest.mark.fail_fast to track them.
Run only fail-fast tests: pytest -m fail_fast
"""

from typing import Any

import pytest
from pydantic import ValidationError

from src.core.base.validated import ValidatedProcessor
from src.models.base import StrictModel

# =============================================================================
# Example: Testing that Pydantic models fail fast
# =============================================================================


class RequiredConfig(StrictModel):
    """Config where all fields are required."""

    name: str
    count: int
    path: str


class TestPydanticFailFast:
    """Verify Pydantic models reject invalid input."""

    @pytest.mark.fail_fast
    def test_missing_field_raises_validation_error(self) -> None:
        """Missing required field must raise ValidationError.

        This ensures we don't have silent defaults.
        """
        with pytest.raises(ValidationError) as exc_info:
            RequiredConfig(name="test", count=5)  # type: ignore[call-arg]  # Missing 'path'

        # Verify the error mentions the missing field
        assert "path" in str(exc_info.value)

    @pytest.mark.fail_fast
    def test_wrong_type_raises_validation_error(self) -> None:
        """Wrong type must raise ValidationError, not coerce.

        This ensures strict=True is working.
        """
        with pytest.raises(ValidationError) as exc_info:
            RequiredConfig(
                name="test",
                count="5",  # type: ignore[arg-type]  # String instead of int
                path="/tmp",
            )

        assert "count" in str(exc_info.value)

    @pytest.mark.fail_fast
    def test_extra_field_raises_validation_error(self) -> None:
        """Extra/unknown field must raise ValidationError.

        This catches typos and misconfiguration.
        """
        with pytest.raises(ValidationError) as exc_info:
            RequiredConfig(
                name="test",
                count=5,
                path="/tmp",
                unknown="oops",  # Extra field
            )  # type: ignore

        assert "extra" in str(exc_info.value).lower()


# =============================================================================
# Example: Testing that ValidatedProcessor enforces validation
# =============================================================================


class ExampleInput(StrictModel):
    """Example input for processor."""

    value: int


class ExampleOutput(StrictModel):
    """Example output from processor."""

    result: int


class DoubleProcessor(ValidatedProcessor[ExampleInput, ExampleOutput]):
    """Example processor that doubles a value."""

    def validate(self, inputs: ExampleInput) -> None:
        if inputs.value < 0:
            raise ValueError("[X] inputs.value must be non-negative")

    def process(self, inputs: ExampleInput) -> ExampleOutput:
        return ExampleOutput(result=inputs.value * 2)


class TestValidatedProcessorFailFast:
    """Verify ValidatedProcessor enforces validation."""

    @pytest.mark.fail_fast
    def test_valid_input_processes_correctly(self) -> None:
        """Valid input should be processed."""
        processor = DoubleProcessor()
        result = processor.run(ExampleInput(value=5))
        assert result.result == 10

    @pytest.mark.fail_fast
    def test_invalid_input_raises_before_processing(self) -> None:
        """Invalid input must raise during validation, not processing.

        This ensures validate() is actually called.
        """
        processor = DoubleProcessor()

        with pytest.raises(ValueError) as exc_info:
            processor.run(ExampleInput(value=-1))

        # Verify it's our validation error
        assert "[X]" in str(exc_info.value)
        assert "non-negative" in str(exc_info.value)


# =============================================================================
# Template: Copy this pattern for your own functions
# =============================================================================


def example_function(config: dict[str, Any]) -> str:
    """Example function with validation.

    This is how functions should validate input.
    """
    if "required_key" not in config:
        raise ValueError("[X] config.required_key is required")

    return str(config["required_key"])


class TestExampleFunctionFailFast:
    """Template for testing fail-fast behavior."""

    @pytest.mark.fail_fast
    def test_valid_input_returns_value(self) -> None:
        """Valid input should return expected value."""
        result = example_function({"required_key": "hello"})
        assert result == "hello"

    @pytest.mark.fail_fast
    def test_missing_required_key_raises_value_error(self) -> None:
        """Missing required key must raise ValueError with clear message."""
        with pytest.raises(ValueError) as exc_info:
            example_function({})

        # Verify error message is actionable
        error_msg = str(exc_info.value)
        assert "[X]" in error_msg
        assert "required_key" in error_msg
