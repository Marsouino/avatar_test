"""Base Pydantic models with strict validation.

This module provides a StrictModel base class that enforces
the project's fail-fast philosophy at the data layer.

Usage:
    from src.models.base import StrictModel

    class UserConfig(StrictModel):
        name: str
        age: int
        email: str

    # Validation is automatic and strict
    config = UserConfig(name="Alice", age=30, email="alice@example.com")

    # These will raise ValidationError:
    # - UserConfig(name="Alice", age="30", email="...")  # age must be int
    # - UserConfig(name="Alice", age=30, extra="...")    # extra field forbidden
    # - config.name = "Bob"                              # frozen, immutable
"""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base model with strict validation enabled.

    This model enforces:
    - strict=True: No automatic type coercion (int won't accept "30")
    - frozen=True: Immutable after creation (no attribute modification)
    - extra="forbid": Unknown fields raise an error
    - validate_default=True: Default values are validated too

    Why these settings?
    - strict: Catches type mismatches immediately (fail-fast)
    - frozen: Prevents accidental mutation, makes data predictable
    - extra="forbid": Catches typos and misconfiguration immediately
    - validate_default: Ensures defaults are valid, not just assumed
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="forbid",
        validate_default=True,
    )


class MutableStrictModel(BaseModel):
    """Base model with strict validation but allowing mutation.

    Use this when you need to modify the model after creation.
    Still enforces strict typing and forbids extra fields.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=False,  # Allows mutation
        extra="forbid",
        validate_default=True,
    )
