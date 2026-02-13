# AnimateDiff SDXL — installation et emplacement des modèles

Environnement de validation rapide pour AnimateDiff SDXL beta (diffusers ≥ 0.27.0), GPU CUDA local.

## Prérequis

- Python 3.11+ (aligné avec le projet ; local : 3.13 d’après `config/hardware.yaml`)
- GPU NVIDIA avec CUDA
- Ne pas deviner les versions PyTorch/CUDA : vérifier `config/hardware.yaml`

## Où placer les fichiers

Copie les fichiers suivants **avant** de lancer le pipeline :

| Fichier | Emplacement dans le projet |
|--------|-----------------------------|
| **Checkpoint SDXL** `juggernautXL_v10_nsfw.safetensors` | `models/checkpoints/juggernautXL_v10_nsfw.safetensors` |
| **MotionAdapter** (contenu de `guoyww/animatediff-motion-adapter-sdxl-beta`, ~1.82 GB) | `models/motion_adapter/` — déposer tous les fichiers (`.safetensors`, `config.json` si présent) dans ce dossier |

Les dossiers `models/checkpoints/` et `models/motion_adapter/` existent déjà (fichiers `.gitkeep` versionnés).

## Installation des dépendances

Depuis la racine du projet :

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-animatediff.txt
```

Les versions de PyTorch dans `requirements-animatediff.txt` sont alignées avec `config/hardware.yaml` pour l’environnement local.

## Configuration des chemins

Les chemins sont définis dans **`config/animatediff.yaml`** (ne pas modifier `config/hardware.yaml`) :

- `checkpoint_path` : chemin vers le checkpoint SDXL
- `motion_adapter_path` : chemin vers le dossier (ou fichier) MotionAdapter
- `output_dir` : répertoire de sortie des vidéos (défaut : `outputs/`)

Si tu places les fichiers aux emplacements indiqués ci-dessus, la config par défaut fonctionne sans changement.

## Lancer une génération

Après les étapes 2–6 du plan d’implémentation, un point d’entrée CLI permettra de lancer des runs manuellement avec les paramètres de ton choix. Voir `docs/ai_codev/ANIMATEDIFF_IMPLEMENTATION_PLAN.md` pour les étapes suivantes.
