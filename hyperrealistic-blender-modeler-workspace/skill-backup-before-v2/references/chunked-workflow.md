# Chunked Build Mode

Build a big scene as separate **chunks**. Each chunk is modeled, rendered on its own and shaded on its own, and the chunks are assembled at the end. Use it when:
- the scene is large (a station, a street, a building interior, a landscape);
- the user asks to work piece by piece;
- a single MCP call or render keeps timing out;
- the Blender connection has been unstable (a crash only costs the chunk in progress).

For a single prop, the normal pass-based workflow in SKILL.md is simpler. Don't use chunks there.

The helper functions are in `scripts/chunk_tools.py`. Paste the file into `execute_blender_code` (or stash its functions in `bpy.app.driver_namespace`) and call them.

## Contents
1. Why chunks work
2. Plan the chunk map
3. The per-chunk loop
4. Assembly and integration
5. Rendering chunks: live, isolated, or headless
6. Tell the user what's happening
7. Example chunk map: underground platform

## 1. Why chunks work

- **Smaller problems.** One chunk (e.g. "track bed") fits in a few MCP calls and one look. You can judge it properly instead of skimming a 250-object scene.
- **Honest checks.** A chunk rendered alone, close up, shows problems the hero shot hides: stretched UVs, flat roughness, intersecting parts, missing back faces.
- **Separable passes.** Shaders and textures for one chunk don't wait on modeling of another. Each chunk goes through modeling, then a render check, then shading, then a render check, then approval.
- **Crash resilience.** Each approved chunk is saved to its own `.blend` and recorded in a manifest. If Blender dies, reload the master or re-append chunks, and continue.
- **Parallel work becomes possible.** A chunk's `.blend` can be rendered by a headless Blender process (§5) while the live session keeps building the next chunk.

## 2. Plan the chunk map

Before building, write a chunk map in the brief and register it in the manifest (`plan_chunk`). Each chunk needs:
- **A name and footprint.** World-space bounds in metres, so neighbours meet exactly. Snap edges to a grid (e.g. 3 m bays).
- **Its contents**, in one sentence.
- **Interfaces.** Where it meets other chunks: shared edges, heights, a tile course that must line up, a cable that crosses over.
- **Dependencies.** Usually `Structure` first, because everything else sits on it.
- **Detail level**, by distance from the hero camera (see environments.md §4).

Good chunk boundaries follow how the real thing is built: structure / floor / track / furniture / signage / lighting / set dressing. Or split by area, e.g. near zone / mid zone / far zone / backdrop. Avoid chunks that share surfaces. Two chunks both modeling the same wall will z-fight.

Keep **global things outside chunks**, in their own collections:
- the hero camera(s)
- world/HDRI
- global lights
- the haze volume
- the human-scale proxy

`isolate_chunks` leaves those collections alone.

## 3. The per-chunk loop

For each chunk in dependency order:

1. **Block out** inside `CHUNK_<Name>` at the planned bounds. Check the footprint with `chunk_bounds(name)` against the plan.
2. **Model.** Bevels, real thickness, instancing for repeats, descriptive names (the SKILL.md rules apply).
3. **Model check.** `render_chunk(m, name, tag="model", samples=32)` renders the chunk alone from its own `CAM_Chunk_<Name>`. Use a clay look if helpful: temporarily set `view_layer.material_override` to a plain grey material, then clear it. Look at the image and fix shape and scale problems now, while they're cheap.
4. **Shade and texture** this chunk only:
   - UVs or box mapping;
   - PBR materials (see materials.md);
   - per-instance variation;
   - grime that follows physics (see environments.md §5);
   - decals.
5. **Shading check.**
   - Render it alone with `render_chunk(..., tag="shaded", samples=64–128)` under neutral lighting: the world HDRI, or a temporary 3-point rig in a `Lights_ChunkPreview` collection that you hide afterwards.
   - Also render one view through the hero camera with neighbouring chunks visible, so you judge it in context.
6. **Approve.**
   - `set_status(m, name, "approved")`
   - `save_chunk_file(m, name)` writes `chunks/<Name>/<Name>.blend`
   - `checkpoint(m)` saves the master and manifest
7. Report one line per chunk to the user, e.g. "Track bed done: rails, chairs, conductor rails, pit; render at chunks/Track/shaded_02.png".

Don't move on with a chunk that looks wrong in its own render. Fixing it later, under the full scene, is slower and noisier.

## 4. Assembly and integration

When all chunks are approved, they're already in the master file (`isolate_chunks` only excludes them). If you built them in separate sessions, bring them in with `bring_in_chunk(path, name)`. That appends the chunk. If an older copy of the chunk is still in the scene, call `remove_chunk(name)` first, or the old objects linger and the new ones arrive renamed `.001`. Use `link=True` only for heavy, finished chunks you won't edit.

Then do the integration pass, which is where scenes stop looking like a kit:
- **Seams.** Inspect every chunk interface through the hero camera and close-up: gaps, doubled faces, tile courses that don't line up, z-fighting.
- **Unifying grime.** Some dirt must cross chunk boundaries: soot fans, floor-up dirt, wet patches, a stain running from the wall onto the floor. Add shared decals or a world-space grime pass that ignores chunk borders.
- **Material cleanup.** `dedupe_materials()` merges `Brick.001`/`Brick.002` duplicates from repeated imports. Then compare similar materials across chunks so concrete in one chunk isn't noticeably different from concrete in another, unless that's intended.
- **Global lighting and exposure.** Tune with everything visible. Chunk previews used neutral lights, so the final mood is set here.
- Run the audit script, do the final render, save, report.

## 5. Rendering chunks: live, isolated, or headless

- **Live and isolated (default).** `render_chunk` excludes other chunks from the view layer, renders with the chunk camera, then restores the camera, samples, resolution and view-layer state. Keep these renders small (25–50%, 32–128 samples) so each call returns before the MCP timeout.
- **Headless.** Render a saved chunk file in a separate Blender process. This leaves the live session free and survives MCP outages:

  ```bash
  "<blender.exe>" -b "<project>/chunks/Track/Track.blend" --python-expr "import bpy; s=bpy.context.scene; ..." -o "<project>/chunks/Track/headless_####.png" -f 1
  ```

  A chunk `.blend` written by `bpy.data.libraries.write` contains the chunk's data but no scene camera or lights, so the expression must add them. It's often simpler to save the *master* with only that chunk enabled, using `isolate_chunks` and then `save_as_mainfile(copy=True)`, and render that copy headless.
- **Headless build fallback.** If the MCP connection drops and won't come back, the same approach can build the scene. Write the chunk's build code to a `.py` file (short folder path), run `blender.exe -b <file.blend> --python build_chunk.py`, and have it save the result. Use test renders instead of screenshots. Tell the user you switched, and don't touch their open Blender window.

Find the Blender executable before relying on headless mode. On Windows it's usually `C:\Program Files\Blender Foundation\Blender <ver>\blender.exe`; elsewhere, check `bpy.app.binary_path` from a live session.

## 6. Tell the user what's happening

Chunked builds take longer, and the user may be watching. Share:
- the chunk map up front, with a one-line plan per chunk;
- a short line as each chunk is approved, with its preview render path;
- assumptions or changes in the plan when a chunk forces them;
- at the end: the manifest path, the chunk files, the master file and the final render.

If the user asks to see or change a specific chunk, re-open just that chunk (isolate it, edit it, re-render it, re-approve it). Leave the rest alone.

## 7. Example chunk map: underground platform

| Chunk | Bounds (x along platform) | Contents | Depends on |
|---|---|---|---|
| `Structure` | 0–120 m | vault shell, end walls, tunnel mouth, floor slab | — |
| `Track` | 0–180 m | rails, chairs, conductor rails, pit, sleepers in tunnel | Structure |
| `Platform` | 0–120 m | coping, safety line, tactile strip, floor tiles | Structure |
| `Furniture` | 0–120 m | bench kit + instances, bins | Platform |
| `Signage` | 0–120 m | name boards, posters, departure board | Structure |
| `Lighting` | 0–120 m | strip fittings with area lights | Structure |
| `Dressing` | 0–120 m | litter, newspaper, cables, CCTV, puddles, decals | all |
| `Tunnel` | 120–180 m | segment lining, cables, signal | Structure |

Order: Structure → Track and Platform → Lighting (it changes how everything else reads) → Signage and Furniture → Tunnel → Dressing → integration.
