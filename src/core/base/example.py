"""Example Abstract Base Class (Contract).

This module demonstrates how to define contracts using Python's ABC.
A contract defines WHAT must be done, not HOW.

Usage:
    1. Define an ABC with abstract methods
    2. Document the expected behavior in docstrings
    3. Implementations must satisfy the contract

Example:
    class MyProcessor(Processor[InputModel, OutputModel]):
        @property
        def name(self) -> str:
            return "my_processor"

        def process(self, data: InputModel) -> OutputModel:
            # Implementation here
            ...
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Generic type variables for input/output
Input = TypeVar("Input")
Output = TypeVar("Output")


class Processor(ABC, Generic[Input, Output]):
    """Abstract base class for data processors.

    This is a CONTRACT: any class implementing Processor must:
    1. Have a unique `name` property
    2. Implement `process()` with proper input validation
    3. Raise clear exceptions on failure (fail-fast)

    Type Parameters:
        Input: The type of data this processor accepts
        Output: The type of data this processor produces
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this processor.

        Returns:
            A string that uniquely identifies this processor.
        """
        ...

    @abstractmethod
    def process(self, data: Input) -> Output:
        """Process input data and produce output.

        This method MUST:
        - Validate input data at the start (fail-fast)
        - Raise clear exceptions with [X] prefix on errors
        - Return a valid Output on success

        Args:
            data: Validated input data

        Returns:
            Processed output data

        Raises:
            ValueError: If input data is invalid
            ProcessingError: If processing fails
        """
        ...

    def validate(self, data: Input) -> None:
        """Validate input data before processing.

        Override this method to add custom validation.
        Default implementation does nothing.

        Args:
            data: Data to validate

        Raises:
            ValueError: If validation fails
        """
        pass


class ProcessingError(Exception):
    """Exception raised when processing fails.

    Use this for errors that occur during processing,
    not for validation errors (use ValueError for those).
    """

    pass
