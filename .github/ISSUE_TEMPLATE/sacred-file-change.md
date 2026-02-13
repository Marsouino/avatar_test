---
name: Sacred File Modification Request
about: Request to modify a protected file
title: "[SACRED] Modify: <filename>"
labels: governance
assignees: ''
---

## File to Modify

- **File path**: `<e.g., .semgrep/rules/philosophy.yaml>`
- **Category**: [ ] governance_rules [ ] project_config [ ] meta_protection

## Reason for Modification

<!-- Explain why this modification is necessary -->

## Proposed Change

```diff
# Show the diff or describe the change

- old content
+ new content
```

## Impact on Governance

- [ ] Weakens an existing protection
- [ ] Adds a new protection
- [ ] Neutral (typo, reformulation, clarification)

## Checklist

- [ ] I understand this file is protected because it enforces code quality
- [ ] I have verified there is no alternative that doesn't require modifying this file
- [ ] I will create a dedicated PR (not mixed with functional code)
