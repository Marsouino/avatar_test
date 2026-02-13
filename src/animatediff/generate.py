"""Génération vidéo AnimateDiff SDXL et export MP4 à 30 FPS. Fail-fast sur chemins et arguments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from diffusers import AnimateDiffSDXLPipeline

# Prompts fixes (brief)
DEFAULT_PROMPT = "1person standing idle, subtle breathing, natural pose, photorealistic, detailed face, soft lighting"
DEFAULT_NEGATIVE_PROMPT = (
    "motion blur, fast movement, running, jumping, bad quality, deformed, ugly, blurry"
)
OUTPUT_FPS = 30


def _validate_run_params(
    num_frames: int,
    num_inference_steps: int,
    height: int,
    width: int,
    guidance_scale: float,
    output_dir: Path,
) -> None:
    if num_frames <= 0:
        raise ValueError(f"[X] num_frames must be > 0, got {num_frames}")
    if num_inference_steps <= 0:
        raise ValueError(f"[X] num_inference_steps must be > 0, got {num_inference_steps}")
    if height <= 0 or height % 8 != 0:
        raise ValueError(f"[X] height must be positive and divisible by 8, got {height}")
    if width <= 0 or width % 8 != 0:
        raise ValueError(f"[X] width must be positive and divisible by 8, got {width}")
    if guidance_scale < 1.0:
        raise ValueError(f"[X] guidance_scale must be >= 1.0, got {guidance_scale}")
    if not output_dir.exists():
        raise FileNotFoundError(f"[X] Output directory not found: {output_dir}")
    if not output_dir.is_dir():
        raise FileNotFoundError(f"[X] Output path is not a directory: {output_dir}")
    if not os.access(str(output_dir), os.W_OK):
        raise PermissionError(f"[X] Output directory is not writable: {output_dir}")


def run_one(
    pipe: AnimateDiffSDXLPipeline,
    num_frames: int,
    num_inference_steps: int,
    height: int,
    width: int,
    guidance_scale: float,
    seed: int,
    output_dir: Path,
    output_basename: str | None = None,
    *,
    prompt: str = DEFAULT_PROMPT,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
) -> Path:
    """
    Lance un run de génération, exporte en MP4 à 30 FPS dans output_dir.

    Nom de fichier déterministe : seed + résolution (et output_basename si fourni).
    Lève en cas d'erreur (pas de fallback silencieux).
    """
    _validate_run_params(num_frames, num_inference_steps, height, width, guidance_scale, output_dir)

    try:
        from diffusers.utils import export_to_video
    except ImportError as e:
        raise ImportError(
            "[X] export_to_video requires diffusers.utils (imageio / imageio-ffmpeg). "
            f"Install: pip install imageio imageio-ffmpeg — {e}"
        ) from e

    device = next(pipe.unet.parameters()).device
    generator = torch.Generator(device=device).manual_seed(seed)

    output = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_frames=num_frames,
        num_inference_steps=num_inference_steps,
        height=height,
        width=width,
        guidance_scale=guidance_scale,
        generator=generator,
    )

    if not output.frames or len(output.frames) < 1:
        raise RuntimeError("[X] Pipeline returned no frames")
    frames = output.frames[0]
    if not frames:
        raise RuntimeError("[X] Pipeline returned empty frame list")

    name_part = f"{output_basename}_" if output_basename else ""
    filename = f"{name_part}seed{seed}_{width}x{height}.mp4"
    output_path = output_dir / filename
    export_to_video(frames, str(output_path), fps=OUTPUT_FPS)
    return output_path
