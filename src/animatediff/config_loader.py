"""Charge config/animatediff.yaml et expose les chemins. Fail-fast : pas de clé par défaut."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from typing import Any

_REQUIRED_KEYS = ("checkpoint_path", "motion_adapter_path", "output_dir")


def _project_root() -> Path:
    # src/animatediff/config_loader.py -> projet
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Charge le YAML AnimateDiff. Lève ValueError si une clé obligatoire manque."""
    root = _project_root()
    path = config_path if config_path is not None else root / "config" / "animatediff.yaml"
    if not path.exists():
        raise FileNotFoundError(f"[X] Config not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    for key in _REQUIRED_KEYS:
        if key not in raw:
            raise ValueError(f"[X] config key '{key}' is required")
    return raw


def get_paths(config_path: Path | None = None) -> tuple[Path, Path, Path]:
    """Retourne (checkpoint_path, motion_adapter_path, output_dir) en Path absolus."""
    root = _project_root()
    raw = load_config(config_path)
    checkpoint = root / raw["checkpoint_path"]
    motion = root / raw["motion_adapter_path"]
    output = root / raw["output_dir"]
    return checkpoint, motion, output
