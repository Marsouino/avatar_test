"""Validation des chemins (checkpoint, motion adapter, output_dir). Fail-fast avec [X]."""

from __future__ import annotations

from pathlib import Path


def validate_paths(
    checkpoint_path: Path,
    motion_adapter_path: Path,
    output_dir: Path,
) -> None:
    """
    Vérifie que les chemins existent. Lève FileNotFoundError avec préfixe [X] si manquant.
    - checkpoint_path : fichier existant
    - motion_adapter_path : fichier ou répertoire existant
    - output_dir : répertoire existant
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"[X] Checkpoint not found: {checkpoint_path}")
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"[X] Checkpoint is not a file: {checkpoint_path}")

    if not motion_adapter_path.exists():
        raise FileNotFoundError(f"[X] MotionAdapter not found: {motion_adapter_path}")
    if not motion_adapter_path.is_file() and not motion_adapter_path.is_dir():
        raise FileNotFoundError(
            f"[X] MotionAdapter path is neither file nor directory: {motion_adapter_path}"
        )

    if not output_dir.exists():
        raise FileNotFoundError(f"[X] Output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise FileNotFoundError(f"[X] Output path is not a directory: {output_dir}")
