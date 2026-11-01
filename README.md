# Blender Photoreal Skill

A Claude skill for building photorealistic 3D models and whole environments directly in Blender through the Blender MCP tools: props, product shots, interiors, streets and stations. It covers planning, clean geometry, modular kits, PBR materials with real wear, lighting, a physical camera, colour management, compositing, animation, quality checks and saving the `.blend`.

## What's here

| Path | What it is |
|---|---|
| `hyperrealistic-blender-modeler/` | The skill: `SKILL.md`, `agents/`, `references/`, `scripts/`, `evals/` |
| `hyperrealistic-blender-modeler.skill` | The packaged skill (zip), ready to install |
| `hyperrealistic-blender-modeler-workspace/` | Development workspace: eval runs and benchmarks, the review page, snapshots and backups |

### Helper agents

`hyperrealistic-blender-modeler/agents/` holds prompts for subagents the skill can start:

- **reference-researcher**: real dimensions, construction, materials, wear and lighting for the subject
- **render-critic**: a fresh review of a test render, ranked by what makes it look CG
- **scene-auditor**: read-only, data-backed check of scale, materials, camera, bounces and lights
- **headless-chunk-worker**: builds or renders one chunk of a large scene in a background Blender process

## Install

Upload `hyperrealistic-blender-modeler.skill` in Claude, or copy the `hyperrealistic-blender-modeler/` folder into your skills folder (e.g. `~/.claude/skills/`).

## Credits

Many practitioner rules in the reference files were adapted from [blender-hyperrealism-skill](https://github.com/Bartindigital/blender-hyperrealism-skill) by Bartłomiej Kusiak (MIT). See `hyperrealistic-blender-modeler/references/CREDITS.md`.
