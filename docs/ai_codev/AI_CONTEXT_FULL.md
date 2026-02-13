# Context Refresh Primer

**Donne ce fichier a lire au LLM quand:**
- Le contexte est summarized/perdu
- Avant une grosse refactorisation
- L'AI fait des erreurs de philosophie ou d'infra

## Quick Refresh (dans Cursor)

```
1. /summarize              <- Compresse le contexte
2. @docs/ai_codev/AI_REFRESH.md  <- Injecte les regles fraiches
```

Le fichier `docs/ai_codev/AI_REFRESH.md` contient les regles critiques en format compact.
Utilise ce workflow quand la conversation devient longue (10+ echanges).

---

## 1. Philosophie de Code (CRITIQUE)

### Fail Fast - Zero Silent Fallback

```python
# INTERDIT - Masque les erreurs
value = config.get("key", "default")
name = user.name or "Anonymous"
x = getattr(obj, "attr", "default")

# OBLIGATOIRE - Erreur visible immediatement
value = config["key"]  # KeyError si manquant
if "key" not in config:
    raise ValueError("[X] config.key is required")
```

### Zero Exception Swallowing

```python
# INTERDIT
try:
    something()
except:
    pass

# OBLIGATOIRE
try:
    something()
except SpecificError as e:
    raise RuntimeError(f"[X] Context: {e}") from e
```

### Pourquoi?

Les LLM ont tendance a generer du code "safe" avec des fallbacks silencieux.
Ca masque les bugs qui explosent 10 etapes plus loin.
On prefere crash immediat avec message clair.

---

## 2. Gouvernance des Contrats

### Fichiers Sacres (Read-Only)

**→ Voir `.github/sacred-files.yml` pour la liste complete.**

Ces fichiers sont PROTEGES. Ne pas modifier sans approbation explicite.

### Avant de Modifier un Test

```
STOP! Ce fichier est un CONTRAT.

Changement propose:
  AVANT: [comportement actuel]
  APRES: [comportement propose]

Approuves-tu ce changement?
```

### Avant d'Utiliser --no-verify

```
STOP! Bypass de tous les hooks pre-commit.

Raison: [pourquoi]
Alternative tentee: [quoi]

Approuves-tu --no-verify?
```

---

## 3. Infrastructure (CRITIQUE)

**→ Lire `config/hardware.yaml` pour toutes les versions et contraintes.**

Règles clés :
- **Ne jamais deviner** les versions PyTorch/CUDA — toujours vérifier `config/hardware.yaml`
- **Environnements multiples** — local et production peuvent différer
- **Containers** — si l'environnement utilise des containers NVIDIA, ne pas installer PyTorch sur l'host
- **Réseau/Storage** — IPs, paths dans `config/hardware.yaml` sections `network` / `storage`

---

## 4. Workflow

1. **Avant implementation**: Lister les fichiers a modifier
2. **Fichier read-only?**: Signaler, pas contourner
3. **Modifier un test?**: Demander approbation
4. **Installer package ML?**: Verifier config/hardware.yaml

---

## 5. Messages d'Erreur

Prefix `[X]` pour que les erreurs soient searchables:

```python
raise ValueError("[X] config.input_path is required")
raise FileNotFoundError(f"[X] Model not found: {path}")
```

---

## Rappel Final

- **Humain** definit QUOI (specs, tests, seuils)
- **AI** propose COMMENT (implementation)
- **CI** verifie automatiquement (semgrep, tests, mypy)

Le serveur (CI) est le point de controle ultime, pas les checks locaux.
