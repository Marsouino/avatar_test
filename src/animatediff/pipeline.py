"""Chargement du pipeline AnimateDiff SDXL depuis checkpoint single-file et MotionAdapter local."""

from __future__ import annotations

from pathlib import Path

import torch

from .config_loader import get_paths
from .paths import validate_paths

# On n'utilise pas xformers. Désactivation explicite pour que diffusers ne tente pas de l'importer.
_diffusers_import_utils = __import__(
    "diffusers.utils.import_utils", fromlist=["_xformers_available"]
)
_diffusers_import_utils._xformers_available = False

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
    MotionAdapter local, checkpoint single-file, DDIM, float16, VAE slicing (pas xformers).
    Lève en cas d'erreur (pas de fallback silencieux).
    """
    if device.strip().lower().startswith("cuda") and not torch.cuda.is_available():
        raise AssertionError(
            "[X] device='cuda' requested but PyTorch is not built with CUDA (torch.cuda.is_available() is False). "
            "Install PyTorch with CUDA: pip install torch==2.10.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"
        )
    checkpoint_path, motion_adapter_path, _output_dir = get_paths(config_path)
    validate_paths(checkpoint_path, motion_adapter_path, _output_dir)

    motion_adapter = MotionAdapter.from_pretrained(
        str(motion_adapter_path),
        torch_dtype=torch.float16,
        local_files_only=True,
        variant="fp16",
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
    return pipe
