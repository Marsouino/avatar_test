# Testing Strategy

Tests are your **contract** with the code. They define what MUST be true.

---

## The Test Pyramid

```
                    ╱╲
                   ╱  ╲
                  ╱ 👁️ ╲      Human validation (rare)
                 ╱Review╲     You look at the final result
                ╱────────╲
               ╱ 🔗 Integ ╲   Integration tests (PR)
              ╱  Components╲  Components connected together
             ╱──────────────╲
            ╱   ✅ Unit       ╲  Unit tests (each commit)
           ╱  Behavior specs   ╲ Each function does what it should
          ╱────────────────────╲
         ╱    📝 Contracts       ╲  Design time
        ╱   Pydantic, interfaces  ╲ Data validation
       ╱──────────────────────────╲
```

---

## Types of Tests

### 1. Behavior Tests (YOU WRITE)

Define what MUST be true, before implementation.

```python
def test_feature_expected_behavior():
    """
    Description in one sentence of what MUST be true.

    Business context: Why this is important.
    """
    # GIVEN - Initial setup
    config = create_valid_config()

    # WHEN - Action to test
    result = system.do_something(config)

    # THEN - Observable result
    assert result.is_valid()
    assert result.value == expected_value
```

### 2. Unit Tests (AI + YOU)

AI writes them, you validate.

```python
def test_parser_handles_empty_string():
    """Parser returns empty list for empty string."""
    result = parse("")
    assert result == []

def test_parser_splits_on_comma():
    """Parser splits on commas."""
    result = parse("a,b,c")
    assert result == ["a", "b", "c"]
```

### 3. Integration Tests (AI + YOU)

Verify that components work together.

```python
def test_pipeline_end_to_end():
    """The complete pipeline produces a valid result."""
    input_data = load_test_input()

    result = pipeline.run(input_data)

    assert result.status == "success"
    assert result.output.exists()
```

---

## Best Practices

### ✅ Test Behavior, Not Implementation

```python
# ❌ BAD - Tests how
def test_uses_cache():
    assert system.cache_enabled == True

# ✅ GOOD - Tests the result
def test_second_call_is_faster():
    t1 = time_call(system.process, data)
    t2 = time_call(system.process, data)  # Same data
    assert t2 < t1 * 0.1  # 10x faster
```

### ✅ Test Properties, Not Exact Values

```python
# ❌ BAD - Fragile
def test_output_exact():
    result = process(input)
    assert result == [1.234, 5.678, 9.012]

# ✅ GOOD - Stable
def test_output_properties():
    result = process(input)
    assert len(result) == 3
    assert all(isinstance(x, float) for x in result)
    assert all(0 <= x <= 10 for x in result)
```

### ✅ Descriptive Test Names

```python
# ❌ BAD
def test_parse():
def test_error():

# ✅ GOOD
def test_parse_returns_empty_list_for_empty_input():
def test_parse_raises_ValueError_for_invalid_format():
```

---

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
│   ├── test_parser.py
│   └── test_validator.py
├── integration/         # Integration tests
│   └── test_pipeline.py
└── fixtures/            # Test data
    └── sample_input.json
```

### conftest.py File

```python
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir() -> Path:
    """Directory containing test data."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_config() -> dict:
    """Valid test configuration."""
    return {
        "input": "test_input.txt",
        "output": "test_output.txt",
        "verbose": True,
    }
```

---

## When to Write Tests

| Moment | Type of Test | Who |
|--------|--------------|-----|
| **Before** implementation | Behavior | You |
| **During** implementation | Unit | AI |
| **After** implementation | Integration | AI (you validate) |
| **Bug discovered** | Regression test | AI |

---

## Useful Commands

```bash
# All tests
pytest

# Tests with verbose output
pytest -v

# A specific file
pytest tests/unit/test_parser.py

# A specific test
pytest tests/unit/test_parser.py::test_parse_empty

# With coverage
pytest --cov=src --cov-report=html
```
