---
name: hyperrealistic-blender-modeler
description: Build highly detailed, photorealistic 3D models and scenes directly in Blender through the Blender MCP tools — planning the model, constructing clean geometry, authoring PBR materials and textures with real-world wear and variation, lighting, camera, render settings, quality checks and saving the .blend. Use this skill whenever the user asks Claude to model, sculpt, build, texture, shade, light or render anything in Blender, or asks for a realistic / photoreal / lifelike 3D object, product shot, prop, environment or scene and Blender MCP tools (execute_blender_code, get_scene_info, get_viewport_screenshot, Poly Haven, etc.) are available — even if they don't say "hyperrealistic" or name the skill.
---

# Hyperrealistic Blender Modeler

You are driving a live Blender session through MCP tools. The goal is a model that reads as a *photograph* of a real thing: correct scale, believable proportions, physically plausible materials, surfaces that show the small imperfections real objects have, and lighting that reveals form. The user sees the result through screenshots and renders, so every claim you make has to be backed by what Blender actually reports.

## 0. Know your tools first

Blender MCP servers differ. Before building, check which tools exist in this session. Common ones (from the popular `blender-mcp` addon):

| Tool | Use |
|---|---|
| `get_scene_info` / `get_object_info` | Read the current scene and object state — your source of truth |
| `execute_blender_code` | Run Python (`bpy`) in Blender — this is where almost all modeling happens |
| `get_viewport_screenshot` | See what you built. Use it after every major stage |
| `get_polyhaven_status`, `search_polyhaven_assets`, `download_polyhaven_asset`, `set_texture` | CC0 HDRIs, PBR texture sets and models from Poly Haven (only if enabled) |
| Sketchfab / Hyper3D / Hunyuan3D tools | Asset search or AI mesh generation (only if enabled and the user is fine with it) |

Call `get_scene_info` at the start so you know what's already there (don't wipe a user's existing work — ask or put your work in a new collection). If an optional integration reports itself disabled, fall back to procedural methods rather than stopping.

If no Blender MCP tools are available at all, say so plainly. You can offer a standalone `bpy` script the user can run themselves, but be clear that nothing was created in Blender.

## 1. Plan before touching geometry

Turn the request into a short modeling brief. Write it out to the user in a few lines — this is where you state assumptions instead of stalling on questions:

- **Subject & reference:** what exactly, which variant/era/style. Recall real-world construction (how the object is manufactured, what parts it has, how they join).
- **Scale:** real dimensions in metres. Blender units = metres; physically correct scale matters because light falloff, bevel sizes, subsurface depth and depth of field all depend on it.
- **Shape breakdown:** primary forms → secondary forms → tertiary detail (screws, seams, engraving, stitching).
- **Materials:** list each distinct surface (e.g. "brushed aluminium body, matte ABS buttons, tempered glass lens, rubber gasket").
- **Lighting & environment:** studio product shot, natural daylight, interior, etc.
- **Camera:** focal length and angle (product: 50–100 mm, slight high angle; architecture: 24–35 mm, verticals level; macro: 100 mm+, shallow DOF).
- **Detail level:** hero close-up vs. mid-distance. Spend detail where the camera will see it.

Only ask a question first when the ambiguity would waste a lot of work (e.g. "a car" with no hint whether they mean a sports car or a pickup and it matters to them). Otherwise pick sensibly, state it, and go.

## 2. Work in passes

Build iteratively. Each pass ends with a `get_viewport_screenshot` (and `get_scene_info` where useful) so you're reacting to what exists, not what you think exists.

1. **Setup** — units metric, scale 1.0; create collections (see §7); set render engine to Cycles early so material previews are honest.
2. **Blockout** — primary shapes at correct real-world size. Check proportions against your plan from multiple angles before adding detail; fixing proportions later is expensive.
3. **Base model** — clean topology, secondary forms, booleans resolved, bevels.
4. **Detail** — tertiary detail where the camera sees it.
5. **Materials & UVs** — PBR shaders, UVs for any image textures.
6. **Surface realism** — wear, grime, roughness variation, micro-detail.
7. **Lighting, camera, render settings.**
8. **QA pass** (§8) → fix → final render → save.

Send code to `execute_blender_code` in moderately sized chunks (one logical step per call). Huge scripts fail opaquely and are hard to debug; tiny ones waste round trips. Have every script `print()` a short confirmation (object names, vertex counts, material names) so the tool output verifies what happened. If a call errors, read the traceback, fix the cause, and re-run — don't assume partial success.

## 3. Geometry

Real objects never have perfectly sharp edges, perfectly flat panels, or infinitely thin walls. These are the biggest giveaways of CG.

- **Bevel every hard edge** that would catch light. Use a Bevel modifier (limit method: angle ~30°, or weight) with 2–3 segments and a width scaled to the object — ~0.5–2 mm for handheld products, 1–5 cm for furniture/architecture. Enable *Harden Normals* plus auto/weighted normals for crisp shading.
- **Subdivision Surface** for organic or smooth manufactured shapes; keep the cage mostly quads, add support loops or creases to control sharpness. Viewport level 1–2, render level 2–3.
- **Thickness:** give shells real thickness (Solidify modifier) — glass, sheet metal, fabric, leaves.
- **Booleans** for cutouts and panel lines, then clean up (or keep as a modifier stack with a bevel after it). Check for shading artifacts around boolean cuts.
- **Sculpting / displacement** for organic surfaces (rock, skin, bark, food): use multires or a displacement modifier with procedural textures driven from `bpy`; true sculpt strokes aren't practical through the API, so lean on displacement, noise and geometry nodes.
- **Geometry Nodes** for repetition with variation: scattered pebbles, bolts around a flange, tiles, grass, chain links. Randomize rotation/scale slightly — perfect repetition looks fake.
- **Modifier order matters:** typically Boolean → Bevel → Subdivision → Weighted Normal (or Solidify before Bevel for shells).
- Apply scale (`bpy.ops.object.transform_apply(scale=True)`) before bevels so widths are consistent, or set scale via mesh data.
- Prefer the `bpy.data` / `bmesh` APIs over `bpy.ops` where possible — operators need the right context (active object, mode, area) and fail silently or raise in MCP calls. See `references/bpy-patterns.md` for working snippets.

Name every object for what it is (`Kettle_Body`, `Kettle_Lid_Knob`), not `Cylinder.003`.

## 4. Materials (PBR)

Use the Principled BSDF and stay within physically plausible ranges. Read `references/materials.md` for a table of measured values and procedural recipes for common surfaces — use it rather than guessing.

Core rules:
- **Base color** is albedo: no baked lighting or shadows, and almost nothing in nature is pure black (<0.02) or pure white (>0.9). Snow ≈ 0.85, charcoal ≈ 0.04.
- **Metallic** is essentially binary: 1.0 for bare metal, 0.0 for everything else. In-between values only at transitions (rust, dirt over metal), driven by a mask.
- **Roughness** carries most of the realism. Never leave it as a flat constant on a hero surface — modulate it with noise, smudges, scratches, or a texture.
- **IOR:** glass 1.45–1.52, water 1.33, plastic ~1.46, diamond 2.42.
- **Transmission** for glass/liquids (with real geometric thickness); **Subsurface** for skin, wax, marble, milk, leaves, fruit — set subsurface radius in scene scale.
- **Bump vs. displacement:** Bump node for fine detail (scratches, pores, grain). True displacement (Cycles, material settings → Displacement and Bump, plus adequate subdivision) for silhouette-changing detail like brick, rocks, bark.
- **Blender 4.x socket names** changed: `Subsurface Weight`, `Transmission Weight`, `Coat Weight`, `Sheen Weight`, `Specular IOR Level`, `Emission Color`. Look up inputs by name and check they exist (the snippets in `references/bpy-patterns.md` do this) so the code works across versions.

## 5. Textures and surface realism

What separates "nice CG" from "photo" is imperfection with a reason. Think about the object's history: where is it touched, rubbed, rained on, dusted?

- **Image textures:** when Poly Haven (or user-supplied files) is available, use 2K–4K PBR sets (diffuse/albedo, roughness, normal, displacement, AO where relevant). Albedo is sRGB; roughness/normal/displacement/metallic are **Non-Color**. Normal maps go through a Normal Map node.
- **UVs:** image textures need sane UVs — smart UV project or cube projection at minimum, with texel density roughly consistent across parts. For organic or large surfaces, box/triplanar mapping (Image Texture → Box projection with blend ~0.2) avoids seams.
- **Break repetition:** mix two scales of the same texture, offset with a noise-driven vector, rotate per-object (Object Info → Random), or overlay a large-scale noise to vary color/roughness across tiles.
- **Wear & grime (procedural):**
  - Edge wear: Geometry → Pointiness (Cycles) or Bevel node/AO node edge mask → mix in a brighter, rougher or bare-metal layer at exposed edges.
  - Cavity dirt: AO node (inverted) → darken and roughen crevices.
  - Smudges/fingerprints: noise + musgrave-style texture into roughness at low contrast (±0.05–0.15).
  - Dust: Geometry normal Z (facing up) masked with noise → light, rough layer on top surfaces.
  - Color variation: subtle (±3–8% value, slight hue shift) noise over base color.
- Keep variation subtle. Exaggerated grunge looks just as fake as clean CG. Check it at the final camera distance.

## 6. Lighting, camera, render

- **Engine:** Cycles for final output (path-traced reflections, refraction, GI). Use GPU if available. EEVEE is fine for quick previews.
- **Samples:** 128–256 for previews, 512–2048 for finals, with denoising (OpenImageDenoise). Keep test renders small (e.g. 50% resolution) — long renders can time out the MCP call.
- **Color management:** View Transform **AgX** (Blender 4.0+) or **Filmic** (3.x), Look ~"Medium High Contrast"/"Base Contrast"; never "Standard" for photoreal work — it clips highlights.
- **Environment:** an HDRI (Poly Haven) gives believable reflections and ambient light. Rotate it so the key light direction flatters the subject. Without Poly Haven, use a Sky Texture (Nishita) for outdoors or a world color plus area lights for studio.
- **Studio setup:** large soft key (area light, 45° side/above), fill at ~¼–½ key strength opposite, rim/back light to separate silhouette; a seamless curved backdrop (sweep) for products. Light sizes and wattages scale with distance — a 1 m area light at 1.5 m might need 100–400 W.
- **Contact & grounding:** objects must sit *on* surfaces (no floating, no sinking). A ground plane catches contact shadows; consider shadow catcher for isolated product shots.
- **Camera:** real focal lengths (see §1), sensor 36 mm, slight depth of field (f/2.8–f/8 depending on subject size) focused on the subject (use a focus object or measured distance). Compose with rule of thirds; keep verticals vertical for architecture.
- **Exposure:** adjust light strength or Film → Exposure so highlights aren't blown and the subject sits mid-range; check the screenshot/render, don't trust numbers alone.

## 7. Scene organization

Organized scenes are easier for the user to keep working with, and easier for you to QA.

- Collections like `Model_<Subject>`, `Environment`, `Lights`, `Cameras` (nest sub-parts if large).
- Descriptive object, mesh, material, and node-group names: `MAT_BrushedAluminium`, `MAT_Glass_Clear`, `LGT_Key`, `CAM_Hero`.
- Parent sub-parts to an empty or main body so the model can be moved as one.
- Remove unused default objects (the default cube/light/camera) only if they're yours to remove — i.e. the scene was the empty startup scene.

## 8. Quality check before presenting

Never present the first pass as final. Run the audit script in `scripts/scene_audit.py` through `execute_blender_code` (paste its contents; it prints a report) and inspect screenshots from several angles plus a test render. Look for and fix:

- **Missing parts** — compare against your plan's part list.
- **Shading artifacts** — black spots, faceting, pinching around booleans/poles, flipped normals (recalculate outside), smoothing on hard edges that should be sharp.
- **Intersections & floating** — parts clipping through each other unintentionally, objects hovering above or sinking into the floor.
- **Texture problems** — stretching, visible seams, obvious tiling, wrong color space (washed-out or overly dark normal maps), missing image files (pink surfaces).
- **Scale problems** — un-applied scale, wrong real-world dimensions, bevels too big/small relative to the object.
- **Render issues** — fireflies (clamp indirect ~10, increase samples), noise, blown highlights, too-dark scene, missing camera.
- **Materials** — any object without a material, flat constant roughness on hero surfaces.

Fix what you find, re-check, and only then do the final render.

## 9. Save and report

- Save the `.blend` with `bpy.ops.wm.save_as_mainfile(filepath=...)`. If the user named a location, use it; otherwise use a clear path (e.g. next to the current file, or the user's home/Documents folder as `<subject>_photoreal.blend`) and tell them. Use `bpy.path.abspath` / print `bpy.data.filepath` afterwards to confirm the actual path.
- To pack image textures into the file so it's portable, run `bpy.ops.file.pack_all()` before saving (mention you did).
- Save final renders with `scene.render.filepath` + `bpy.ops.render.render(write_still=True)` and confirm the file exists (`os.path.exists`) in the same script.

End with a concise report:
1. **What was built** — objects/collections, key techniques (e.g. "bevelled subdivided body, geometry-nodes bolt ring, procedural edge wear").
2. **Materials & textures** — which are procedural vs. image-based (and their source, e.g. Poly Haven asset names).
3. **Lighting / camera / render settings.**
4. **Assumptions made.**
5. **Where things were saved** — exact paths reported by Blender.
6. **Known limitations or rough spots** and what could be refined next.

## 10. Honesty about results

The user can't see inside Blender except through you, so accuracy here matters more than sounding impressive.

- Only say an object, material, texture, render or file exists if a tool result confirmed it (printed output, scene info, screenshot, or `os.path.exists`).
- If a step failed (download blocked, render timed out, save path not writable), say so and say what you did instead.
- Describe what the screenshot actually shows, including flaws you couldn't fix. "The wood grain stretches slightly on the left leg" is more useful than silence.
- Don't call something "hyperrealistic" just because the request did. Let the user judge from the render; describe the techniques used.
