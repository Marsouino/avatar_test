"""Génération vidéo AnimateDiff SDXL et export MP4 à 30 FPS. Fail-fast sur chemins et arguments."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import torch

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from diffusers import AnimateDiffSDXLPipeline

# Prompts fixes (brief)
DEFAULT_PROMPT = "1person standing idle, subtle breathing, natural pose, photorealistic, detailed face, soft lighting"
DEFAULT_NEGATIVE_PROMPT = (
    "motion blur, fast movement, running, jumping, bad quality, deformed, ugly, blurry"
)
OUTPUT_FPS = 30
WARMUP_FRAMES = 8
WARMUP_STEPS = 5


@dataclass(frozen=True)
class RunResult:
    """Résultat d'un run : chemin MP4 et métriques de temps."""

    output_path: Path
    generation_time_s: float
    duration_s: float
    num_frames: int
    realtime_ratio: float


def warmup(pipe: AnimateDiffSDXLPipeline) -> None:
    """
    Run minimal pour compiler les kernels CUDA (num_frames=8, steps=5, output_type=latent).
    Pas d'export vidéo. En cas d'échec, propage l'exception avec contexte [X].
    """
    device = next(pipe.unet.parameters()).device
    generator = torch.Generator(device=device).manual_seed(0)
    try:
        pipe(
            prompt=DEFAULT_PROMPT,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            num_frames=WARMUP_FRAMES,
            num_inference_steps=WARMUP_STEPS,
            height=256,
            width=256,
            guidance_scale=7.0,
            generator=generator,
            output_type="latent",
        )
    except Exception as e:
        raise RuntimeError(f"[X] Warmup failed: {e}") from e


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
) -> RunResult:
    """
    Lance un run de génération, exporte en MP4 à 30 FPS dans output_dir.

    Nom de fichier déterministe : seed + résolution (et output_basename si fourni).
    Retourne RunResult (chemin + métriques). Lève en cas d'erreur (pas de fallback silencieux).
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

    t0 = time.perf_counter()
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
    generation_time_s = time.perf_counter() - t0

    if not output.frames or len(output.frames) < 1:
        raise RuntimeError("[X] Pipeline returned no frames")
    frames = output.frames[0]
    if not frames:
        raise RuntimeError("[X] Pipeline returned empty frame list")

    name_part = f"{output_basename}_" if output_basename else ""
    filename = f"{name_part}seed{seed}_{width}x{height}.mp4"
    output_path = output_dir / filename
    export_to_video(frames, str(output_path), fps=OUTPUT_FPS)

    duration_s = num_frames / OUTPUT_FPS
    if generation_time_s <= 0.0:
        raise RuntimeError("[X] generation_time_s must be > 0")
    realtime_ratio = duration_s / generation_time_s

    return RunResult(
        output_path=output_path,
        generation_time_s=generation_time_s,
        duration_s=duration_s,
        num_frames=num_frames,
        realtime_ratio=realtime_ratio,
    )


def print_run_report(result: RunResult) -> None:
    """Log le rapport (generation_time, duration, frames, realtime_ratio, chemin MP4)."""
    logger.info(
        "generation_time=%.2fs duration=%.2fs frames=%s realtime_ratio=%.2f output=%s",
        result.generation_time_s,
        result.duration_s,
        result.num_frames,
        result.realtime_ratio,
        result.output_path,
    )
