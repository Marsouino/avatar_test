# Co-Development Workflow

How we work together, you (human) and the AI.

---

## The Ownership Model

### What YOU Control

| Domain | Your Role | Artifact |
|--------|-----------|----------|
| **Vision** | Define the problem | User stories, specs |
| **Architecture** | Validate decisions | Diagrams, ADRs |
| **Behavior** | Define what must be true | Behavior tests |
| **Interfaces** | Validate contracts | Pydantic models |
| **Quality** | Define thresholds | Metrics, thresholds |

### What AI Does

| Domain | AI's Role | Your Safety Net |
|--------|-----------|-----------------|
| Implementation | Write code | Your tests must pass |
| Refactoring | Restructure | Tests + review |
| Documentation | Generate docs | Your validation |
| Detailed tests | Cover edge cases | You validate tests |

### The Golden Rule

> **If you can't test it, you can't delegate it.**

---

## Feature Workflow

### Phase 1: Specification (YOU)

You define the problem and acceptance criteria:

```markdown
## Feature: [Name]

### User Story
As a [user], I want [action] so that [benefit].

### Acceptance Criteria
1. [Measurable criterion 1]
2. [Measurable criterion 2]
3. [Measurable criterion 3]
```

### Phase 2: Behavior Tests (YOU)

You write tests BEFORE implementation:

```python
def test_feature_produces_expected_result():
    """The action must produce the expected result."""
    result = system.do_action(valid_input)
    assert result.is_valid()
    assert result.meets_criteria()

def test_feature_fails_fast_on_invalid_input():
    """Invalid input = immediate error."""
    with pytest.raises(ValueError):
        system.do_action(invalid_input)
```

### Phase 3: Interface (YOU + AI)

AI proposes, you validate:

```python
class FeatureConfig(BaseModel):
    """Configuration for the feature."""
    required_field: str      # You validate: required
    optional_field: int = 10 # You validate: default OK?
```

### Phase 4: Implementation (AI)

AI writes the code. You don't need to read everything.
**Your tests verify it works.**

### Phase 5: Verification (CI + YOU)

```bash
pytest tests/ -v
# Green = OK
# Red = issue to investigate
```

---

## Communication

### When AI Proposes Code

AI will:
1. Briefly explain the approach
2. Show the code
3. Indicate which tests to run

### When AI Needs Clarification

AI will ask BEFORE implementing:
- "Is this behavior expected?"
- "What should happen if X?"
- "Should I handle case Y?"

### When AI Detects a Problem

AI will:
1. Signal the problem clearly
2. Propose alternative solutions
3. Wait for your decision

---

## Anti-patterns to Avoid

### ❌ Trusting Blindly

```python
# BAD
def test_it_works():
    result = function()
    assert result  # "It works" is not a test
```

### ❌ Testing Implementation, Not Behavior

```python
# BAD - Fragile
def test_calls_correct_methods():
    with patch('module.internal') as mock:
        run()
        mock.assert_called()

# GOOD - Stable
def test_produces_correct_output():
    result = run(input)
    assert result.output == expected
```

### ❌ Reading Everything

You don't need to read 500 lines of code.
**Run the tests.** Green = the code does what it should.

---

## Summary

```
1. YOU define what must be true (specs, tests)
2. AI proposes how to make it true (code)
3. CI verifies it's true (automation)
4. YOU validate the final result
```
