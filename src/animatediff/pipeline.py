"""Chargement du pipeline AnimateDiff SDXL depuis checkpoint single-file et MotionAdapter local."""

from __future__ import annotations

from pathlib import Path

import torch

from .config_loader import get_paths
from .paths import validate_paths

# API diffusers >= 0.27 — AnimateDiff SDXL beta
try:
    from diffusers import AnimateDiffSDXLPipeline
    from diffusers.models import MotionAdapter
    from diffusers.schedulers import DDIMScheduler
except ImportError as e:
    raise ImportError(
        "[X] AnimateDiff SDXL requires diffusers>=0.27 with AnimateDiffSDXLPipeline. "
        f"Install: pip install -r requirements-animatediff.txt — {e}"
    ) from e


def _make_scheduler() -> DDIMScheduler:
    """DDIM pour cohérence temporelle (brief: beta_schedule=linear, steps_offset=1)."""
    return DDIMScheduler(
        num_train_timesteps=1000,
        beta_schedule="linear",
        steps_offset=1,
        clip_sample=False,
        timestep_spacing="linspace",
    )


def load_pipeline(
    device: str,
    config_path: Path | None = None,
) -> AnimateDiffSDXLPipeline:
    """
    Charge le pipeline AnimateDiff SDXL : config + validation des chemins,
    MotionAdapter local, checkpoint single-file, DDIM, float16, xformers, VAE slicing.
    Lève en cas d'erreur (pas de fallback silencieux).
    """
    checkpoint_path, motion_adapter_path, _output_dir = get_paths(config_path)
    validate_paths(checkpoint_path, motion_adapter_path, _output_dir)

    motion_adapter = MotionAdapter.from_pretrained(
        str(motion_adapter_path),
        torch_dtype=torch.float16,
        local_files_only=True,
    )
    scheduler = _make_scheduler()

    pipe = AnimateDiffSDXLPipeline.from_single_file(
        str(checkpoint_path),
        motion_adapter=motion_adapter,
        scheduler=scheduler,
        torch_dtype=torch.float16,
    )
    pipe = pipe.to(device)

    pipe.enable_vae_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception as e:
        raise RuntimeError(
            f"[X] xformers memory efficient attention failed (check xformers install): {e}"
        ) from e

    return pipe
