# Philosophie de Code : Policy as Code

Ce document explique **pourquoi** et **comment** on structure le co-développement avec l'IA.

---

## Le Problème

### L'IA génère du code qui "fonctionne"... en apparence

Quand tu demandes à une IA de coder, elle produit du code qui compile et semble correct. Mais elle a tendance à :

1. **Masquer les erreurs** avec des valeurs par défaut
2. **Avaler les exceptions** pour éviter les crashs
3. **Ajouter des fallbacks** "au cas où"

```python
# L'IA génère naturellement ça :
value = config.get("timeout", 30)  # "Au cas où timeout manque"
name = user.name or "Anonymous"     # "Au cas où name est vide"

try:
    result = process(data)
except Exception:
    result = default_result  # "Pour éviter le crash"
```

**Problème** : Ce code ne crashe pas... mais il cache des bugs.

- `timeout` manquant ? Tu ne le sauras jamais.
- `user.name` vide alors qu'il devrait exister ? Masqué.
- `process(data)` échoue ? L'erreur disparaît.

Tu découvriras ces bugs **10 étapes plus tard**, avec un message d'erreur incompréhensible, dans un contexte où tu ne comprendras plus ce qui s'est passé.

### Le vrai problème : tu ne peux pas tout relire

Avec un développeur humain, tu fais une code review. Avec l'IA qui génère 500 lignes en 30 secondes, **tu ne peux pas tout vérifier**. Les patterns dangereux passent inaperçus.

---

## La Solution : Policy as Code

### Le principe

> **Ce qui n'est pas vérifié automatiquement n'existe pas.**

On ne fait pas confiance à l'IA (ni à l'humain). On fait confiance aux **vérifications automatiques**.

```
┌─────────────────────────────────────────────────────────────────┐
│  HUMAIN    →  Définit les RÈGLES (quoi vérifier)               │
│  IA        →  Génère le CODE (implémentation)                   │
│  CI        →  ENFORCE les règles (automatiquement)              │
└─────────────────────────────────────────────────────────────────┘
```

### Le modèle mental

```
Local (IA peut tout faire)  ──push──►  Serveur (TU contrôles)
         │                                      │
    Peut bypasser                         Ne peut PAS bypasser
    pre-commit                            GitHub Actions
    --no-verify                           Branch protection
```

**Le local appartient à l'IA. Le serveur t'appartient.**

L'IA peut faire ce qu'elle veut localement. Mais au moment du push, les règles s'appliquent. Si le code viole une règle, il ne passe pas.

---

## Les Règles

Ces règles sont **vérifiées automatiquement par Semgrep** à chaque commit et dans la CI.
Tout code violant ces règles sera **bloqué**.

### Principe Fondamental : Fail Fast

> Les erreurs doivent être **visibles immédiatement**, pas cachées.

Un bug visible maintenant = 5 minutes à corriger.
Un bug caché qui ressort plus tard = des heures de debug.

---

### RÈGLE #1 : Zéro Silent Fallback

**Le problème** : Les fallbacks masquent les valeurs manquantes.

#### INTERDIT

```python
# ❌ dict.get() avec valeur par défaut
value = config.get("key", "default")
timeout = params.get("timeout", 30)

# ❌ or avec fallback
name = user.name or "Anonymous"
path = config.path or "/default/path"

# ❌ getattr() avec valeur par défaut
value = getattr(obj, "attr", "default")

# ❌ hasattr() avec fallback
x = obj.attr if hasattr(obj, "attr") else "default"

# ❌ Ternaire avec fallback
value = data["key"] if "key" in data else "default"
```

#### OBLIGATOIRE

```python
# ✅ Accès direct (lève KeyError/AttributeError si manquant)
value = config["key"]
timeout = params["timeout"]
name = user.name

# ✅ Validation explicite avec message d'erreur clair
if "key" not in config:
    raise ValueError("[X] config.key is required")
value = config["key"]

# ✅ Pour les attributs
if not hasattr(obj, "attr"):
    raise ValueError("[X] obj.attr is required")
value = obj.attr
```

#### Pourquoi ?

Une valeur manquante est **presque toujours un bug de configuration**. Un fallback silencieux masque ce bug. Tu le découvriras 10 étapes plus tard avec un message incompréhensible.

---

### RÈGLE #2 : Zéro Exception Swallowing

**Le problème** : Les exceptions avalées cachent les erreurs.

#### INTERDIT

```python
# ❌ Bare except
try:
    risky()
except:
    pass

# ❌ Broad except avec pass
try:
    risky()
except Exception:
    pass

# ❌ Except qui retourne une valeur par défaut
try:
    value = load_file()
except:
    value = "default"  # L'erreur disparaît!

# ❌ Except qui assigne une valeur par défaut
try:
    data = fetch_data()
except Exception:
    data = {}  # Masque le problème
```

#### OBLIGATOIRE

```python
# ✅ Exception spécifique avec contexte
try:
    value = load_file()
except FileNotFoundError as e:
    raise RuntimeError(f"[X] Config file missing: {e}") from e

# ✅ Si vraiment optionnel, DOCUMENTER pourquoi
try:
    cache = load_cache()
except FileNotFoundError:
    # Cache is optional - will be created on first save
    # This is expected on first run
    cache = {}
```

#### Pourquoi ?

Une exception signifie "quelque chose s'est mal passé". L'ignorer ne fait pas disparaître le problème - ça le cache jusqu'à ce qu'il explose ailleurs.

---

### RÈGLE #3 : Zéro Legacy

**Le problème** : Le code "legacy" crée de la confusion.

#### INTERDIT

```python
# ❌ Noms avec legacy, old, deprecated, v1
def process_legacy(): ...
class OldHandler: ...
def get_data_v1(): ...
use_legacy_mode = True
```

#### OBLIGATOIRE

```python
# ✅ Un seul nom, la version actuelle
def process(): ...
class Handler: ...
def get_data(): ...
```

#### Pourquoi ?

Si l'ancienne version n'est plus utilisée, supprime-la. Si elle est encore utilisée, c'est la version actuelle - pas "legacy".

---

### RÈGLE #4 : Imports Explicites

**Le problème** : Les star imports cachent d'où viennent les choses.

#### INTERDIT

```python
# ❌ Star import
from module import *
```

#### OBLIGATOIRE

```python
# ✅ Import explicite
from module import ClassName, function_name
```

---

### RÈGLE #5 : Validation Immédiate des Inputs

**Le problème** : Valider tard = erreurs incompréhensibles.

#### OBLIGATOIRE

```python
def process_image(config: dict) -> Image:
    # 1. Validation IMMÉDIATE au début
    if "input_path" not in config:
        raise ValueError("[X] config.input_path is required")
    if "output_size" not in config:
        raise ValueError("[X] config.output_size is required")

    input_path = Path(config["input_path"])
    if not input_path.exists():
        raise FileNotFoundError(f"[X] Input image not found: {input_path}")

    # 2. Traitement seulement APRÈS validation complète
    image = load_image(input_path)
    return resize(image, config["output_size"])
```

---

### RÈGLE #6 : Messages d'Erreur Actionnables

**Le problème** : "Error" ne dit pas quoi faire.

#### INTERDIT

```python
# ❌ Message vague
raise ValueError("Invalid config")
raise RuntimeError("Error occurred")
```

#### OBLIGATOIRE

```python
# ✅ Message avec [X] prefix et contexte
raise ValueError("[X] config.input_path is required")
raise FileNotFoundError(f"[X] Model file not found: {model_path}")
raise RuntimeError(f"[X] Failed to connect to {host}:{port}")
```

Le prefix `[X]` rend les erreurs searchables dans les logs.

---

## Comment c'est Enforcé

### Niveau 1 : Semgrep (local + CI)

Semgrep analyse le code et détecte les patterns interdits.

Les règles sont organisées en fichiers thématiques :

| Fichier | Contenu |
|---------|---------|
| `.semgrep/rules/fail-fast.yaml` | Zero fallback + Zero swallow |
| `.semgrep/rules/code-clarity.yaml` | No legacy + Explicit imports |
| `.semgrep/rules/code-quality.yaml` | Mutable defaults + Print statements |
| `.semgrep/rules/testing.yaml` | Tests significatifs |
| `.semgrep/rules/no-bypass.yaml` | Détection des `# nosemgrep` |

- **Local** : Pre-commit bloque le commit
- **CI** : GitHub Actions bloque le merge

### Niveau 2 : Tests

Les tests vérifient le comportement, pas l'implémentation :

```python
def test_missing_config_raises_clear_error():
    """Missing required config must raise ValueError with clear message."""
    with pytest.raises(ValueError) as exc:
        process({})  # Missing required keys

    assert "[X]" in str(exc.value)
    assert "required" in str(exc.value)
```

### Niveau 3 : Fichiers Sacrés

Certains fichiers sont **protégés** et ne peuvent pas être modifiés sans approbation :

- `.semgrep/rules/` - Les règles elles-mêmes
- `.github/workflows/` - La CI qui enforce
- `pyproject.toml` - La configuration projet

Voir `.github/sacred-files.yml` pour la liste complète.

---

## Résumé

| Pattern | Interdit | Correct |
|---------|----------|---------|
| `dict.get("k", default)` | ❌ | `dict["k"]` |
| `x or default` | ❌ | `if not x: raise` |
| `getattr(o, "a", default)` | ❌ | `o.a` |
| `except: pass` | ❌ | `except SpecificError: raise` |
| `except: return default` | ❌ | Laisser remonter ou re-raise |
| `from x import *` | ❌ | `from x import y, z` |
| `raise ValueError("Error")` | ❌ | `raise ValueError("[X] context")` |

---

## La Question à se Poser

> "Si cette valeur est manquante, est-ce un **bug** ou une **situation normale** ?"

- **Bug** → Fail fast avec exception claire
- **Situation normale** → Documenter explicitement pourquoi c'est optionnel

---

## Conclusion

Cette philosophie n'est pas de la paranoïa - c'est de la **rigueur**.

Quand l'IA génère du code, tu ne peux pas tout relire. Tu dois pouvoir faire confiance aux vérifications automatiques. Ces règles garantissent que :

1. Les erreurs sont **visibles immédiatement**
2. Les bugs ne sont pas **masqués par des fallbacks**
3. Le code fait **ce qu'il dit** qu'il fait

> **Le local appartient à l'IA. Le serveur t'appartient.**
