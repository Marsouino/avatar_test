# DAG Pipeline — Nodes / Providers / Backends

## Quand utiliser

- Pipeline data-driven avec étapes chaînées (ML, GenAI, ETL)
- Besoin d'isoler des modules avec des dépendances hétérogènes
- Besoin de flexibilité : réordonner, ajouter, retirer des étapes

---

## Vue d'ensemble

Architecture en 3 couches qui sépare **quoi faire**, **avec quoi**, et **où/comment** :

```
┌──────────────────────────────────────────────────────────┐
│  NODES — Étapes du pipeline. Orchestration uniquement.   │
│  Déclare requires / consumes / provides                  │
│  run(ctx) -> ctx                                         │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  PROVIDERS — Façades métier. API typée.                  │
│  Délègue l'exécution à un Backend.                       │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  BACKENDS — Infrastructure d'exécution.                  │
│  Local, subprocess, HTTP, cloud.                         │
└──────────────────────────────────────────────────────────┘
```

### Responsabilités

| Couche | ✅ Fait | ❌ Ne fait pas |
|--------|---------|----------------|
| **Node** | Orchestre, valide les inputs, déclare le contrat | Logique métier, gestion d'infra |
| **Provider** | API métier typée, sérialise vers Backend | Transport, isolation |
| **Backend** | Transport (subprocess, HTTP), isolation (venv, container) | Logique métier |

---

## Nodes — Le contrat

Chaque Node déclare explicitement ce qu'il consomme et produit :

```python
class Node(ABC):
    name: str
    requires: dict[str, type]     # Clés requises + type. Fail-fast si absentes.
    provides: dict[str, type]     # Clés produites + type.
    consumes: list[str] = []      # Clés optionnelles (namespace wildcard accepté).
    priority: int = 0             # Ordre d'exécution (plus haut = plus tôt).

    def run(self, ctx: PipelineContext) -> None: ...
```

### Exemple

```python
class FeatureExtractionNode(Node):
    name = "feature_extraction"
    requires = {"dataset.train": pd.DataFrame}
    provides = {"features.train": np.ndarray, "features.metadata": dict}
    priority = 10

    def run(self, ctx):
        df = ctx.get("dataset.train")
        features = self.provider.extract(df)
        ctx.set("features.train", features)
        ctx.set("features.metadata", {"n_features": features.shape[1]})
```

---

## Contexte typé

Les données circulent via un `PipelineContext` fail-fast :

```python
class PipelineContext:
    """Contexte partagé entre les Nodes. Fail-fast, pas de default."""

    def set(self, key: str, value: Any) -> None:
        """Écrit une valeur. Refuse l'écrasement silencieux."""
        if key in self._data:
            raise KeyError(f"[X] Key '{key}' already set by another Node")
        self._data[key] = value

    def get(self, key: str) -> Any:
        """Lit une valeur. Fail-fast si absente."""
        if key not in self._data:
            raise KeyError(f"[X] Context key '{key}' not found")
        return self._data[key]

    def get_namespace(self, prefix: str) -> dict[str, Any]:
        """Retourne toutes les clés qui commencent par prefix."""
        result = {k: v for k, v in self._data.items() if k.startswith(prefix)}
        if not result:
            raise KeyError(f"[X] No keys found with prefix '{prefix}'")
        return result
```

### Convention de nommage des clés

| Pattern | Exemple | Description |
|---------|---------|-------------|
| `{domaine}.{sortie}` | `features.train` | Sortie d'un domaine |
| `{namespace}.*` | `conditioning.*` | Groupe de sorties similaires |
| `input.*` | `input.data` | Entrées du pipeline |
| `output.*` | `output.model` | Sorties finales |

### Clés strictes vs souples

- **`requires`** → clés **strictes** (noms exacts, fail-fast si absentes)
- **`consumes`** → clés **souples** (namespace wildcard, utilisées si présentes)

```python
class GenerationNode(Node):
    requires = {"prompt.compiled": str}          # Strict : doit exister
    consumes = ["conditioning.*"]                # Souple : prend tout ce qui est dispo
```

Un Node qui provides `conditioning.pose` et un autre `conditioning.depth` : GenerationNode les ramasse tous via le namespace, sans les lister individuellement. Ajouter un nouveau type de conditioning ne nécessite pas de modifier GenerationNode.

---

## Wiring — Deux modes

### Mode 1 : Explicite (recommandé pour commencer)

L'utilisateur définit l'ordre. `validate()` vérifie le chaînage avant exécution.

```python
pipeline = Pipeline([
    DataLoaderNode(),
    FeatureExtractionNode(),
    TrainingNode(),
    EvaluationNode(),
])
pipeline.validate()
pipeline.run(ctx)
```

`validate()` vérifie :
1. Tous les `requires` de chaque Node sont satisfaits par le contexte initial ou les `provides` d'un Node précédent
2. Compatibilité des types entre provides et requires
3. Pas de clé produite par deux Nodes différents (collision)

### Mode 2 : Auto-résolu

Un DagResolver infère l'ordre à partir d'un goal et des déclarations requires/provides de chaque Node.

```python
ordered = DagResolver(available_nodes).resolve(goal="output.model")
pipeline = Pipeline(ordered)
pipeline.validate()
pipeline.run(ctx)
```

Le resolver remonte récursivement depuis le goal, trouve les Nodes nécessaires, et les trie par priorité. Pour les `consumes`, des feature flags décident de l'inclusion.

**Conseil** : commencer en mode explicite. Passer en auto-résolu quand le DAG devient complexe (>10 nodes).

---

## Capacités attendues

### Checkpointing / Cache

Chaque Node peut être caché basé sur un hash de ses inputs. Si les inputs n'ont pas changé, le Node est skip et ses outputs sont restaurés depuis le cache.

Bénéfices :
- **Re-run partiel** : seuls les nodes dont les inputs ont changé sont ré-exécutés
- **Debug rapide** : relancer après un fix sans tout recalculer
- **Expérimentation** : changer les dernières étapes sans refaire les premières

Options de stockage :
- **Filesystem (pickle/joblib)** ← recommandé pour commencer (simple, pas de dépendance)
- SQLite — si besoin de requêtes sur le cache
- Redis — si pipeline distribué

### Dry Run / Plan

Avant d'exécuter, afficher ce qui va se passer :

```
[PLAN] Pipeline: 4 nodes
  1. DataLoaderNode        (→ dataset.train)                [WILL RUN]
  2. FeatureExtractionNode (dataset.train → features.train) [CACHED]
  3. TrainingNode          (features.train → model.trained) [WILL RUN]
  4. EvaluationNode        (model.trained → eval.metrics)   [WILL RUN]

Estimated: 2 cached, 2 to run
```

Combine checkpointing + validation. Aucune exécution, juste de la vérification.

### Exécution parallèle

Deux Nodes sont parallélisables si aucun ne requires/consumes ce que l'autre provides. Le pipeline regroupe les nodes indépendants et les exécute en parallèle.

Options d'exécution :
- **Séquentiel** ← recommandé pour commencer (simple, debug facile, pas de contention VRAM)
- ThreadPool — pour I/O bound (téléchargement, API calls)
- ProcessPool — pour CPU bound (feature extraction)

**Note** : en ML/GenAI, le séquentiel est souvent préférable à cause de la VRAM partagée.

---

## Boucles dans un DAG

Un DAG est acyclique — pas de boucle dedans. Deux patterns pour les cas itératifs :

### Pattern 1 : Boucle externe

L'orchestrateur relance le DAG entier avec des paramètres différents. Chaque exécution est indépendante et cacheable.

Utilisé pour : grid search, cross-validation, A/B testing.

### Pattern 2 : Boucle interne au Node

La boucle est un détail d'implémentation du Node (ex: epochs d'entraînement), invisible au DAG. Le pipeline voit un seul Node.

Utilisé pour : entraînement, optimisation itérative, convergence.

---

## Structure de fichiers suggérée

```
src/
├── core/
│   ├── base/              # ABCs : Node, Provider, Backend
│   ├── pipeline/          # PipelineContext, Pipeline, DagResolver
│   ├── cache/             # Checkpointing
│   ├── nodes/             # Implémentations des Nodes
│   ├── providers/         # Implémentations des Providers
│   └── backends/          # Local, Remote, InProcess
├── models/                # Pydantic models (data types)
└── config/                # Configuration YAML
```

---

## Checklist d'implémentation

1. [ ] Définir les ABCs (Node, Provider, Backend)
2. [ ] Implémenter PipelineContext avec typage et namespaces
3. [ ] Implémenter Pipeline avec validate() et run()
4. [ ] Implémenter le premier Node end-to-end
5. [ ] Ajouter le checkpointing
6. [ ] Ajouter le dry run / plan
7. [ ] (Optionnel) Implémenter DagResolver
8. [ ] (Optionnel) Ajouter l'exécution parallèle

---

## Principes (alignés avec la philosophie du template)

- **Fail-fast** : validate() avant run(), requires typés, contexte strict
- **Zero silent fallback** : `ctx.get()` raise si clé absente, pas de default
- **Contrats** : Node/Provider/Backend sont des ABCs, les interfaces sont documentées
- **Séparation** : chaque couche a un rôle clair, pas de mélange
