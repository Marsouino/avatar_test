# Project Brief

<!--
Fill this template after running init_project.
Give it to the AI after @docs/ai_codev/AI_CONTEXT_FULL.md
-->

## Vision (1-2 phrases)

What problem does this project solve? For whom?

> _Example: "A tool that helps researchers track experiment results without switching contexts."_

**Your vision:**
Le projet est un environnement Python standalone utilisant diffusers>=0.27.0 pour tester AnimateDiff SDXL beta en mode validation rapide. L'architecture charge le MotionAdapter depuis guoyww/animatediff-motion-adapter-sdxl-beta (~1.82GB safetensors) et initialise un AnimateDiffPipeline.from_single_file() pointant vers le checkpoint SDXL juggernautXL_v10_nsfw.safetensors, configuré avec un DDIMScheduler (beta_schedule="linear", steps_offset=1) pour la cohérence temporelle. Le pipeline utilise torch.float16 avec enable_xformers_memory_efficient_attention() et enable_vae_slicing() pour optimiser la VRAM, et génère trois vidéos programmatiquement via des appels pipe() avec des configurations paramétriques distinctes : (num_frames=8, num_inference_steps=8, height=768, width=768), (16, 12, 1024, 1024), et (24, 20, 1024, 1024), chacune avec guidance_scale respectivement à 7.0, 7.5, et 8.0, en utilisant un torch.Generator avec seed fixe (42) pour reproductibilité. Les prompts utilisent une structure standardisée "1person standing idle, subtle breathing, natural pose, photorealistic, detailed face, soft lighting" avec negative prompt "motion blur, fast movement, running, jumping, bad quality, deformed, ugly, blurry", et les outputs sont exportés via export_to_video() à 30 FPS en format MP4 dans un répertoire outputs/. Le script inclut un warmup initial (num_frames=8, num_inference_steps=5, output_type="latent") pour compiler les kernels CUDA, mesure précisément les temps de génération avec time.time(), et affiche un rapport final avec métriques (generation_time, duration, frames count, realtime ratio) pour chaque configuration testée, permettant une évaluation quantitative et qualitative immédiate de la performance et qualité d'AnimateDiff SDXL sur le hardware cible avant toute décision d'adoption ou d'intégration ultérieure.

## Constraints (what we know for sure)

- [local si possible ] Must run on: [local / cloud / both]
- [internal ] Data sensitivity: [public / internal / confidential]
- [ ] Timeline pressure: [exploration / deadline-driven]
- [solo] Team size: [solo / small team / large team]

## Architecture (optional)

Reference a proven pattern from `docs/architecture_suggestions/`:

- [ ] `DAG_PIPELINE.md` — DAG Pipeline with Nodes/Providers/Backends (ML, GenAI, ETL)
- [ ] Other: [describe]
- [ x] None yet — we'll decide together

## Open Questions (we'll decide together)

These are NOT decided yet. We'll figure them out during development:

- Data storage?
- Key libraries/frameworks?
- Testing strategy beyond the template defaults?

---

## For the AI: Comprehension Check

After reading this brief and the philosophy docs, please:

1. **Summarize** your understanding of the project in 2-3 sentences
2. **Identify** any ambiguities or missing information
3. **Ask** 2-3 clarifying questions before we start coding

This ensures we have shared understanding before implementation.
