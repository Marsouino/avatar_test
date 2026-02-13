"""Base classes with mandatory validation.

This module provides abstract base classes that enforce validation
before processing. The architecture itself guarantees fail-fast behavior.

Usage:
    from src.core.base.validated import ValidatedProcessor

    class ImageProcessor(ValidatedProcessor[ImageInput, ImageOutput]):
        def validate(self, inputs: ImageInput) -> None:
            if not inputs.path.exists():
                raise ValueError(f"[X] Image not found: {inputs.path}")

        def process(self, inputs: ImageInput) -> ImageOutput:
            # This is only called if validate() passes
            return ImageOutput(...)
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from beartype import beartype

# Generic type variables
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class ValidatedProcessor(ABC, Generic[InputT, OutputT]):
    """Abstract processor with mandatory validation.

    This class uses the Template Method pattern to guarantee that
    validation always runs before processing.

    The workflow is:
    1. User calls run(inputs)
    2. run() calls validate(inputs) - MUST raise if invalid
    3. Only if validate() passes, run() calls process(inputs)
    4. process() returns the result

    Subclasses MUST implement:
    - validate(): Raise ValueError/TypeError if inputs are invalid
    - process(): Do the actual work (only called if validation passes)
    """

    @beartype
    def run(self, inputs: InputT) -> OutputT:
        """Execute validation then processing.

        This is the public API. Users call this method.
        It guarantees validate() runs before process().

        Args:
            inputs: The input data to process

        Returns:
            The processed output

        Raises:
            ValueError: If validation fails
            TypeError: If input types are wrong (via beartype)
        """
        self.validate(inputs)
        return self.process(inputs)

    @abstractmethod
    def validate(self, inputs: InputT) -> None:
        """Validate inputs before processing.

        MUST raise an exception if inputs are invalid.
        Use clear error messages with [X] prefix.

        Args:
            inputs: The input data to validate

        Raises:
            ValueError: If inputs are invalid
            TypeError: If input types are wrong

        Example:
            def validate(self, inputs: MyInput) -> None:
                if not inputs.path:
                    raise ValueError("[X] inputs.path is required")
                if not inputs.path.exists():
                    raise ValueError(f"[X] File not found: {inputs.path}")
        """
        ...

    @abstractmethod
    def process(self, inputs: InputT) -> OutputT:
        """Process validated inputs.

        This method is ONLY called after validate() passes.
        You can assume inputs are valid.

        Args:
            inputs: Validated input data

        Returns:
            The processed output
        """
        ...


class ValidatedTransformer(ABC, Generic[InputT, OutputT]):
    """Simpler variant for pure transformations.

    Use this when you have a simple transform function that
    should validate its inputs.
    """

    @beartype
    def __call__(self, data: InputT) -> OutputT:
        """Transform data with validation."""
        self.validate(data)
        return self.transform(data)

    @abstractmethod
    def validate(self, data: InputT) -> None:
        """Validate input data. Must raise if invalid."""
        ...

    @abstractmethod
    def transform(self, data: InputT) -> OutputT:
        """Transform validated data."""
        ...
