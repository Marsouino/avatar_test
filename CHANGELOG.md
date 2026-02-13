# Changelog

Toutes les modifications notables du template sont documentées ici.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [1.0.0] - 2026-02-02

### Première version

#### Philosophie
- Fail-fast : erreurs visibles immédiatement
- Zero silent fallback : pas de `.get(key, default)`
- Zero exception swallowing : pas de `except: pass`
- Policy as Code : vérification automatique, pas review humaine

#### Règles Semgrep
- `fail-fast.yaml` : 20 règles (zero fallback + zero swallow)
- `code-clarity.yaml` : 2 règles (no legacy + explicit imports)
- `code-quality.yaml` : 2 règles (mutable default + print)
- `testing.yaml` : 1 règle (empty tests)
- `no-bypass.yaml` : 1 règle (détection # nosemgrep)

#### Enforcement
- Pre-commit hooks : Ruff, Semgrep, Mypy, tests unitaires
- CI : 3 jobs (Quick, Full, Sacred files)
- Branch protection : script de configuration

#### Architecture
- `StrictModel` : Pydantic avec validation stricte
- `ValidatedProcessor` : ABC avec validation obligatoire
- `beartype` : validation des types au runtime
- Marqueur `@pytest.mark.fail_fast` pour les tests de validation

#### Scripts
- `lock-governance` / `unlock-governance` : protection des fichiers sacrés
- `setup-github` : configuration branch protection
- `validate_setup` : vérification de l'installation
- `check_fail_fast` : linter custom pour patterns fail-fast

#### Documentation
- `docs/ai_codev/PHILOSOPHY.md` : règles de code et pourquoi
- `docs/ai_codev/WORKFLOW.md` : comment travailler avec l'IA
- `docs/ai_codev/TESTING.md` : stratégie de tests
- `docs/ai_codev/AI_CONTEXT_FULL.md` : contexte complet pour sessions AI
- `docs/ai_codev/AI_REFRESH.md` : refresh rapide post-summarize

---

## [Unreleased]

### Added
- **Dual venv architecture**: `venv/` (project deps + pytest) and `venv_policy/` (static analysis tools)
- `requirements-policy.txt`: isolated policy tool dependencies (semgrep, ruff, mypy, pre-commit)
- `scripts/run_policy_tool.py`: cross-platform wrapper for venv_policy tools
- `scripts/run_all_tests.py`: multi-venv test runner (each module tested in its own venv)
- `config/venvs.yaml`: module-to-venv-to-tests mapping
- `scripts/check_test_count.py`: AST-based test count ratchet (detects silent test removal)
- `docs/architecture_suggestions/DAG_PIPELINE.md`: DAG pipeline pattern with Nodes/Providers/Backends
- Pre-commit hook: test count ratchet
- `AI_REFRESH.md`: pre-commit enforcement rules section
- `AI_REFRESH.md`: infrastructure section pointing to `config/hardware.yaml`
- `PROJECT_BRIEF.md`: architecture selection checklist

### Changed
- `init_project.ps1/.sh`: now creates both venvs (7 steps instead of 5)
- `config/hardware.yaml`: real values replaced with template placeholders
- `.cursor/rules/infrastructure.mdc`: simplified to redirect to `config/hardware.yaml`
- `AI_CONTEXT_FULL.md`: infrastructure and sacred files sections redirect to source files
- `.pre-commit-config.yaml`: all hooks via `run_policy_tool.py`, sacred files excluded from modification hooks
- `pyproject.toml`: added `--cov --cov-report=term-missing` to pytest, removed `fail_under` gate
- Sacred files list centralized in `.github/sacred-files.yml` — all scripts read from this single source
- `lock-governance` / `unlock-governance` scripts read sacred files dynamically
- `validate_setup.py`: resolves tools from correct venvs (policy vs project)
- `check_fail_fast.py`: fixed false positive on `param: X | None = None` pattern

### Removed
- Pre-commit unit-tests hook (replaced by `run_all_tests.py` for multi-venv support)
- Hardcoded sacred files lists from governance scripts (now read from YAML)
- Coverage gate (`fail_under = 50`) — coverage is for visibility, not blocking

---

## Comment mettre à jour un projet existant

Quand une nouvelle version sort :

1. Lire les changements ci-dessus
2. Identifier ce qui s'applique à ton projet
3. Copier manuellement les fichiers/règles pertinents
4. Tester avec `pre-commit run --all-files`

### Fichiers généralement à synchroniser

| Priorité | Fichiers | Raison |
|----------|----------|--------|
| Haute | `.semgrep/rules/*.yaml` | Nouvelles règles de qualité |
| Haute | `.github/workflows/policy-enforcement.yml` | Nouveaux checks CI |
| Moyenne | `.cursor/rules/*.mdc` | Guidance IA mise à jour |
| Basse | `scripts/*.py` | Nouveaux utilitaires |
