# Plan d'implémentation — AnimateDiff SDXL (validation rapide)

**Contexte :** Environnement Python standalone, diffusers ≥ 0.27.0, GPU CUDA local. Checkpoint et MotionAdapter fournis localement par l'utilisateur.

**Règle :** Une étape à la fois, commit après chaque étape.

---

## Où placer tes fichiers (à faire avant / pendant l’étape 1)

| Fichier | Emplacement dans le projet |
|--------|-----------------------------|
| **Checkpoint SDXL** `juggernautXL_v10_nsfw.safetensors` | `models/checkpoints/juggernautXL_v10_nsfw.safetensors` |
| **MotionAdapter** (safetensors ~1.82 GB, de `guoyww/animatediff-motion-adapter-sdxl-beta`) | `models/motion_adapter/` — dépose **tous** les fichiers du repo (souvent un `.safetensors` + éventuellement `config.json`). Si c’est un seul fichier, mets-le dans `models/motion_adapter/` et on pointera dessus. |

Après création des dossiers à l’étape 1, tu n’auras qu’à copier ces deux éléments aux emplacements indiqués.

---

## Étape 1 — Squelette projet et config des chemins

**Objectif :** Structure des dossiers, configuration des chemins (sans toucher à `config/hardware.yaml`), dépendances, et doc “où mettre les fichiers”.

**Fichiers à créer :**

- `models/checkpoints/.gitkeep` et `models/motion_adapter/.gitkeep` (dossiers vides versionnés).
- `config/animatediff.yaml` — config **projet** (pas hardware) :
  - `checkpoint_path`: chemin vers le checkpoint (ex. `models/checkpoints/juggernautXL_v10_nsfw.safetensors`).
  - `motion_adapter_path`: chemin vers le dossier ou fichier MotionAdapter (ex. `models/motion_adapter/`).
  - `output_dir`: ex. `outputs/`.
- `requirements-animatediff.txt` — dépendances pour ce workflow :
  - `torch`, `torchvision` (versions alignées avec `config/hardware.yaml` pour le local : 2.10.0),
  - `diffusers>=0.27.0`,
  - `transformers`, `accelerate`, `safetensors`,
  - `xformers` (optionnel mais recommandé pour VRAM).
- `.gitignore` (ou mise à jour) : ignorer `outputs/`, `models/checkpoints/*.safetensors`, `models/motion_adapter/*.safetensors` (pour ne pas commit les gros binaires), et `venv/` / `venv_policy/` si besoin.
- `docs/animatediff_setup.md` (ou section dans README) : où placer checkpoint et motion adapter, comment installer avec `requirements-animatediff.txt`, et référence à `config/animatediff.yaml`.

**Règles :** Ne pas modifier `config/hardware.yaml` ni `pyproject.toml` (fichiers sacrés). Les versions PyTorch dans `requirements-animatediff.txt` doivent être cohérentes avec `config/hardware.yaml` (local : 2.10.0).

**Commit :** `chore(animatediff): project skeleton, paths config, and model placement doc`

---

## Étape 2 — Validation des chemins (fail-fast)

**Objectif :** Au démarrage du script, vérifier que les chemins requis existent ; sinon, lever une erreur claire avec préfixe `[X]`.

**Fichiers à créer :**

- `src/animatediff/__init__.py` (package dédié).
- `src/animatediff/config_loader.py` (ou équivalent) :
  - Charger `config/animatediff.yaml`.
  - Exposer des variables ou une petite structure pour `checkpoint_path`, `motion_adapter_path`, `output_dir`.
  - **Pas de fallback silencieux** : si une clé obligatoire manque → `raise ValueError("[X] config key '...' is required")`.
- `src/animatediff/paths.py` (ou intégré au config_loader) :
  - Fonction `validate_paths()` (ou équivalent) : vérifier que les fichiers/dossiers existent (`Path.exists()`).
  - Si manquant : `raise FileNotFoundError("[X] Checkpoint not found: ...")` / `"[X] MotionAdapter not found: ..."`.
  - Appelée au démarrage du pipeline (étape suivante) ou depuis un point d’entrée unique.

**Règles :** Pas de `config.get("key", default)`. Erreurs avec préfixe `[X]`.

**Commit :** `feat(animatediff): config loader and path validation (fail-fast)`

---

## Étape 3 — Chargement du pipeline et optimisations VRAM

**Objectif :** Charger le MotionAdapter depuis le chemin local, créer `AnimateDiffPipeline.from_single_file(checkpoint)`, configurer le scheduler et les optimisations.

**Fichiers à créer / modifier :**

- `src/animatediff/pipeline.py` (ou `load_pipeline.py`) :
  - Charger la config (étape 2) et appeler `validate_paths()`.
  - Charger le MotionAdapter depuis le chemin local (API diffusers : selon la version, `MotionAdapter.from_pretrained(local_path)` ou équivalent pour SDXL beta).
  - `AnimateDiffPipeline.from_single_file(checkpoint_path, ...)`.
  - Configurer `DDIMScheduler` : `beta_schedule="linear"`, `steps_offset=1`.
  - Pipeline en `torch.float16`, `enable_xformers_memory_efficient_attention()`, `enable_vae_slicing()`.
  - Exposer une fonction `get_pipeline()` ou `load_pipeline()` qui retourne le pipeline prêt à l’emploi.

**Règles :** Pas de guess des versions — s’appuyer sur `config/hardware.yaml` pour la compatibilité PyTorch/CUDA. Gestion d’erreurs explicite (pas de `except: pass`).

**Commit :** `feat(animatediff): pipeline loading with DDIM and VRAM optimizations`

---

## Étape 4 — Génération d’une vidéo et export MP4

**Objectif :** Une fonction qui, étant donné une configuration (num_frames, num_inference_steps, height, width, guidance_scale, seed), lance un run, exporte en MP4 à 30 FPS dans `output_dir`.

**Fichiers à créer / modifier :**

- `src/animatediff/generate.py` (ou équivalent) :
  - Prompt et negative prompt **fixes** comme dans le brief :
    - prompt : `"1person standing idle, subtle breathing, natural pose, photorealistic, detailed face, soft lighting"`,
    - negative : `"motion blur, fast movement, running, jumping, bad quality, deformed, ugly, blurry"`.
  - Signature du type : `run_one(pipe, num_frames, num_inference_steps, height, width, guidance_scale, seed, output_dir, output_basename?)` (ou équivalent).
  - Utiliser `torch.Generator(device=...).manual_seed(seed)`.
  - Appel `pipe(...)` avec les bons arguments, puis `export_to_video(..., fps=30)` vers `output_dir`.
  - Nom de fichier de sortie déterministe (ex. inclure seed + résolution) pour ne pas écraser sans le vouloir.

**Règles :** Fail-fast si `output_dir` manquant ou non writable (message `[X]`).

**Commit :** `feat(animatediff): single-run generation and MP4 export at 30 FPS`

---

## Étape 5 — Warmup et métriques (temps, durée, realtime ratio)

**Objectif :** Warmup optionnel pour compiler les kernels CUDA ; mesure des temps et rapport (generation_time, duration, frames, realtime ratio).

**Fichiers à modifier :**

- `src/animatediff/generate.py` (ou module dédié `metrics.py`) :
  - **Warmup :** une fonction `warmup(pipe)` qui fait un run minimal : `num_frames=8`, `num_inference_steps=5`, `output_type="latent"`, sans export vidéo.
  - **Métriques :** autour de la génération réelle, utiliser `time.time()` pour mesurer le temps de génération ; à partir des frames et du FPS, calculer `duration` (durée vidéo en s) et `realtime_ratio` (duration / generation_time).
  - Retourner ou afficher un petit rapport : `generation_time`, `duration`, `frames`, `realtime_ratio` (et chemin du fichier MP4).

**Règles :** Pas de swallow d’exceptions ; en cas d’échec du warmup ou de la génération, propager l’erreur avec contexte.

**Commit :** `feat(animatediff): warmup and timing report (generation_time, realtime_ratio)`

---

## Étape 6 — Point d’entrée CLI (lancement manuel au choix)

**Objectif :** L’utilisateur peut lancer un run avec les paramètres de son choix (ou des presets), sans être forcé à exécuter les 3 configs en séquence.

**Fichiers à créer / modifier :**

- `src/animatediff/cli.py` ou script à la racine : `scripts/run_animatediff.py` (ou `run.py` dans un dossier dédié).
  - Arguments (ex. `argparse`) : `--frames`, `--steps`, `--height`, `--width`, `--guidance`, `--seed`, `--warmup` (flag), `--output-basename` (optionnel).
  - Charger la config, `validate_paths()`, `load_pipeline()`, optionnellement `warmup(pipe)`, puis `run_one(...)` avec les arguments fournis.
  - Documenter dans `docs/animatediff_setup.md` (ou README) les **3 presets du brief** comme exemples de commandes :
    - Preset A : 8 frames, 8 steps, 768×768, guidance 7.0
    - Preset B : 16 frames, 12 steps, 1024×1024, guidance 7.5
    - Preset C : 24 frames, 20 steps, 1024×1024, guidance 8.0

**Règles :** Validation des arguments (ex. frames > 0, steps > 0) avec erreurs `[X]` en cas de valeur invalide.

**Commit :** `feat(animatediff): CLI for manual runs and presets`

---

## Étape 7 — Documentation et usage final

**Objectif :** README (ou doc dédiée) à jour avec instructions claires : installation, où placer les fichiers, comment lancer un run, exemples des 3 presets.

**Fichiers à modifier :**

- `docs/animatediff_setup.md` (ou section README) :
  - Prérequis (Python, CUDA, GPU).
  - Installation : `pip install -r requirements-animatediff.txt` (et note sur l’alignement avec `config/hardware.yaml`).
  - Où placer checkpoint et motion adapter (tableau déjà prévu en étape 1).
  - Comment lancer : `python -m src.animatediff.cli ...` ou `python scripts/run_animatediff.py ...` avec exemples pour les 3 presets.
  - Description courte du rapport (generation_time, realtime_ratio, etc.).

**Commit :** `docs(animatediff): README and usage with presets`

---

## Résumé des commits prévus

| Étape | Message de commit |
|-------|-------------------|
| 1 | `chore(animatediff): project skeleton, paths config, and model placement doc` |
| 2 | `feat(animatediff): config loader and path validation (fail-fast)` |
| 3 | `feat(animatediff): pipeline loading with DDIM and VRAM optimizations` |
| 4 | `feat(animatediff): single-run generation and MP4 export at 30 FPS` |
| 5 | `feat(animatediff): warmup and timing report (generation_time, realtime_ratio)` |
| 6 | `feat(animatediff): CLI for manual runs and presets` |
| 7 | `docs(animatediff): README and usage with presets` |

---

## Fichiers sacrés (rappel)

Ne pas modifier sans approbation explicite :

- `config/hardware.yaml`
- `pyproject.toml`
- `tests/conftest.py`
- Fichiers listés dans `.github/sacred-files.yml`

L’ajout de **nouveaux** fichiers (config `animatediff.yaml`, modules sous `src/animatediff/`, scripts dédiés) est hors scope des fichiers sacrés.
