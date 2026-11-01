# Building Whole Environments

Read this when the subject is a space the camera sits *inside* or looks *across*: a station, a platform, a street, a room, a corridor, a shop, a landscape. A single object (the watch) and a space (the station) fail in different ways. Props usually look fake because they're too clean and too sharp. Spaces usually look fake because they're **too uniform** (every tile, light and bench identical), **too empty**, **wrongly scaled**, or **lit like a product shot**. Most of this file is about avoiding those four problems without running out of time, VRAM or MCP-call budget.

## Contents
1. Plan the space: shot list, zones, modules, real dimensions
2. Blockout through the camera
3. Modular kits and instancing
4. Detail budget: hero, mid, background
5. Surfaces at scale: tiles, trims, decals, grime
6. Lighting interiors with many lights
7. Camera for spaces
8. Life and story details
9. Performance and render budget
10. Environment QA
11. Worked example: an underground metro platform
12. Snippets
13. A real-world environment workflow (canal scene breakdown)

## 1. Plan the space

Add these to the modeling brief:

- **Shot list.** 1–3 cameras that matter: e.g. "eye-level down the platform toward the tunnel mouth" and "low angle across the tracks to the far wall". Everything is judged through these. Detail that no camera sees is wasted effort.
- **Zones.** Split the space into named areas: e.g. `Structure` (walls, vault, floor), `Track`, `Platform`, `Furniture`, `Signage`, `Lighting`, `Decals`, `Props`. Each zone is a collection.
- **Modules.** What repeats? Wall bays, columns, light fittings, benches, poster frames, sleepers, ceiling panels. Build each once and instance it.
- **Real dimensions.** Look up or reason out the real measurements before building. Typical human-scale anchors:
  - door 2.0–2.1 m tall
  - stair riser 0.15–0.18 m, tread 0.28–0.30 m
  - handrail 0.9–1.0 m
  - bench seat 0.45 m
  - ceiling 2.4–3 m domestic, 3–5 m public
  - standard rail gauge 1.435 m
- **Keep the full real extent.** Repeated bays, rails and lights are instances, so a full 120 m platform costs little more than a 50 m one, and the vanishing perspective down a long space is a big part of what makes it read as real. If you do shorten something (render budget, or the far end is never seen), hide the cut beyond the camera's view, e.g. behind a curve, a closed end wall or darkness, and state the shortcut and the reason in the report.
- **Era and condition.** "Victorian, heavily used, recently cleaned" vs. "1970s, neglected". This decides every material and grime choice, so say it in the brief.
- **Real brands.** For real places with trademarked branding (transit logos, typefaces, adverts), default to a style-faithful version:
  - an invented station name
  - a roundel-*style* sign rather than a traced logo
  - generic posters

  Use exact branding only if the user asks for it or provides assets. Mention this choice in your assumptions.

## 2. Blockout through the camera

1. Build the space as simple boxes and cylinders at real size: walls, floor, ceiling and big volumes only.
2. Place the hero camera(s) **now**. Add a hidden 1.8 m human-scale proxy (a capsule with `hide_render = True`) where a person would stand. Nothing exposes wrong scale faster.
3. Take a screenshot through each camera. Adjust the proportions, the focal length and the composition until the empty blockout already reads as the right kind of place.
4. Only then start on the modules.

## 3. Modular kits and instancing

- **Build modules at the origin** in a hidden `KIT_` collection: `KIT_WallBay`, `KIT_Bench`, `KIT_LightFitting`, `KIT_PosterFrame`. Snap their dimensions to a grid (e.g. a 3.0 m wall bay) so they tile without gaps.
- **Instance, don't copy.** Use collection instances (`instance_type = 'COLLECTION'`) or linked duplicates (shared mesh data) for repeats. 200 benches as instances cost almost nothing; 200 real copies cost 200× the memory.
- **Arrays for strict repetition.** Use an Array modifier for strictly regular things such as sleepers, tiles as geometry, railings and ceiling ribs. Add a Curve modifier to follow a curved platform or tunnel.
- **Variation is mandatory.** Make 2–4 variants of each visible module, e.g. a bench with a scratch, a missing slat or graffiti, or posters with different artwork. Then:
  - pick variants randomly with a fixed seed;
  - randomize the small transforms (rotation ±1–3°, position ±1–2 cm) on loose props;
  - use per-instance random color and roughness in shaders (Object Info → Random).
- **Geometry Nodes** are a good fit for scattering: litter, gravel ballast, puddles, leaves, sleeper clips, rivets. Use "Distribute Points on Faces", then "Instance on Points" with a random Collection Info pick.
- **Avoid single-sided walls.** They leak light in interiors. Give structure real thickness (Solidify), especially on anything between a light and the camera.

## 4. Detail budget

Split the space by its distance from the hero camera:

| Zone | Distance from hero cam | Treatment |
|---|---|---|
| Hero | 0–5 m | Real bevels, modeled detail (screws, grilles, tile edges), 2K–4K textures or rich procedural detail, decals |
| Mid | 5–25 m | Bevel modifier at low segments, normal/bump instead of geometry, 1K–2K textures |
| Background | 25 m+ | Simple geometry, material variation only, no subdivision, maybe fog |

A 120 m platform at full hero detail everywhere will blow the VRAM and the MCP timeouts. Spend modeling time where the camera looks.

## 5. Surfaces at scale

**Tiles** (ceramic, subway, floor):
- Use a Brick Texture node (offset 0 for a stacked grid, 0.5 for running bond).
  - Set Color1 to black and Color2 to white with Bias 0: the Color output then gives a random grey value per tile.
  - Feed that value through Map Range nodes to drive small changes in each tile's hue, value (±3–6%) and roughness (±0.05–0.1).
- The Brick "Fac" output is the mortar mask. Make grout darker, rougher and dirtier than the tile, and recess it with a small bump.
- Tilt each tile slightly with a per-tile random normal (bump from the per-tile random at very low strength). Real tiled walls catch light unevenly.
- A few tiles should be different: cracked, chipped corners, replaced with a slightly different shade. Mask them with a high-threshold per-tile random.
- Real tile sizes: subway tile 152 × 76 mm (6 × 3 in), square wall tile 150 mm, floor tile 300–600 mm. Wrong tile scale is an instant tell.

**Grime that follows physics** (procedural masks, combine with Multiply/Max):
- **Floor-up dirt.** Use world Z through Map Range: dirt is darker within 0–0.3 m of the floor (mop splash, kicks, dust).
- **Top-down soot.** Ceilings and the upper walls near tunnel mouths, vents and lights get darker. Use Z near the ceiling × Noise.
- **Streaks and drips.** Stretch a Noise texture along Z (Mapping scale (1, 1, 0.05)) × a mask that starts under ledges, vents and cracks.
- **Traffic wear.** Floors are *polished* (lower roughness, slightly lighter) along walking paths and dirtier near edges and corners. Build a mask from distance to the path centre line, or from a painted vertex group.
- **Wet patches.** Lower roughness plus a slightly darker base color in noise-masked areas near drains, the platform edge and entrances. Puddles are near-zero roughness with a flat normal.
- **Gum and stains on floors.** Small dark Voronoi dots (random size, low density) and a few large faint blotches.

**Decals.** Posters, stains, graffiti tags, warning stickers, tactile-strip wear and route maps go on thin planes:
- Offset them 1–2 mm from the surface, or they will z-fight.
- Use alpha-masked materials.
- Age them too: a poster has peeling corners, sun fading and a torn edge.

**Mapping big surfaces.** Use world- or object-space box mapping so textures stay at real scale across modules. Hide tiling by blending two scales of the same texture with a large noise mask (see materials.md).

## 6. Lighting interiors with many lights

- **Model the fittings, then light them properly.** An emissive tube alone is noisy and weak. For each fitting:
  - give the tube a modest emission (so it reads as glowing);
  - put a matching **area light** (rectangle, same size, pointing out of the fitting) inside to do the actual illumination;
  - instance the fitting together with its light.
- **Colour temperature by source.** Mix a little: fluorescent and LED 4000–5000 K, older tungsten 2700–3200 K, signage and display emission at its own colours. Use a Blackbody node or convert to RGB. A perfectly uniform white looks CG.
- **Cycles' light tree** (`scene.cycles.use_light_tree`, on by default in 4.x+) is what makes hundreds of lights affordable. Keep it on.
- **Bounces.** Interiors need light to bounce: set diffuse 4–6, glossy 4, transmission 8+, total 12. Use a clamp indirect of ~10 against fireflies.
- **Exposure.** Underground and night spaces are dark overall with bright pools. Set Film Exposure (or AgX plus an exposure tweak) so the walls sit mid-grey and the fittings clip only slightly. Never solve "too dark" by turning up the world color.
- **Haze.** A thin volume (Principled Volume density 0.001–0.005 in a box around the space) adds depth and light shafts. It's expensive: add it last, test at low resolution, and skip it if render time is tight.
- **Outdoor spaces at dusk or night.** Use a Sky texture with a low or negative sun elevation, or a dusk HDRI, plus warm practical lights (street lamps, windows). The sky contributes cool fill; the practicals give warm pools.

## 7. Camera for spaces

- **Height and lens.** Eye height 1.5–1.7 m (lower, 0.4–1 m, for drama). 18–35 mm lens; below ~16 mm the edges stretch unnaturally.
- **Two-point perspective.** Keep the camera level (X rotation 90°) so verticals stay vertical. Use Shift Y to reframe instead of tilting. Converging verticals make architecture read as amateur.
- **Leading lines.** A platform edge, rails, the ceiling and a light row converging to a vanishing point near a third line.
- **Depth of field.** Little or none (f/8–f/16 equivalent, or DOF off) unless there is a clear foreground hero.
- **Motion blur.** Optional: an arriving train with motion blur is a strong storytelling choice.

## 8. Life and story details

Empty spaces read as renders. Even without people, add evidence of use:
- discarded ticket or newspaper, a coffee cup on a bench, a puddle under a leak
- CCTV cameras, speakers, cable trays and conduit runs, fire extinguisher, emergency signs
- a departure-board dot-matrix display (emission text), a clock, a "mind the gap" painted line
- one broken or flickering light (dimmer, warmer), a maintenance access door, a patched area of newer tiles

If asset-library tools exist (Poly Haven, Sketchfab, etc.), use them for props and people. Imported assets arrive at arbitrary scale, so resize them using their bounding box and place them on the floor.

## 9. Performance and render budget

- **VRAM.** Check the GPU (e.g. a laptop RTX at 8 GB). Instances, 1–2K textures, and Simplify for previews keep you safe:
  - `scene.render.use_simplify = True`
  - `scene.render.simplify_subdivision_render = 1`
- **MCP calls.** Keep each `execute_blender_code` call to one zone or module. Build long runs with loops that create instances, not with thousands of operator calls.
- **Preview renders.** 25–50% resolution, 64–128 samples, denoise. Save and inspect each one.
- **Final render.** Start with a modest number of samples (256–512, adaptive threshold 0.01, denoise). If a single render would exceed the MCP call timeout, render at the resolution you need with fewer samples, report this honestly, and give the user the exact settings so they can press F12 themselves.
- **Stats.** Report scene stats (objects, instances, triangles after modifiers, image memory). The audit script prints these.

## 10. Environment QA

In addition to the general QA list in SKILL.md:
- Look through every hero camera, plus 2–3 views along the length of the space at different heights.
- **Seams between modules.** Visible gaps, doubled faces, misaligned tile patterns where bays meet.
- **Z-fighting.** Flickering stripes where two coplanar faces overlap, such as decals or floor overlays. Offset them by 1–2 mm.
- **Visible repetition.** In each hero camera, can you spot the same poster, bench or grime blotch twice? If so, add variants or rotate and offset the texture.
- **Scale.** Compare against the human proxy. Do the doors, benches and signs look right next to it?
- **Light leaks.** Bright lines at wall and ceiling joins mean thin geometry or gaps.
- **Noise.** Noise in dark corners means more samples, light tree on, or brighter fills.
- **Empty areas.** Any large surface with no variation or story detail.

## 11. Worked example: an underground metro platform

Brief, with assumptions you can state:
- deep-level tube-style station, Victorian-era tiling with a later refurbishment
- an invented station name
- an evening with light passenger use, so the platform is empty but used
- hero shot: eye level, standing near the platform edge, looking along the platform into the tunnel mouth

Approximate dimensions (sanity-check against references when exact accuracy matters):
- **Platform tunnel.** Circular-ish vault about 6.5–7.5 m in diameter. The platform level cuts across the lower part of the circle.
- **Running tunnel mouth.** About 3.6–3.8 m in diameter, much smaller than the platform tunnel. This contrast is a key visual.
- **Platform.** Length 110–130 m; width 3–4 m. Platform edge about 0.9–1.0 m above the rail tops.
- **Track.**
  - Standard gauge 1.435 m; sleepers every ~0.6–0.7 m.
  - Four-rail electrification: an outer conductor rail on insulator pots and a centre conductor rail between the running rails.
  - A drainage pit (well) between the rails along the platform.
- **Edge strip.** Yellow or white safety line ~0.1 m wide, about 0.7–0.9 m from the edge, with tactile paving inside it. The edge is a coping stone with a slight lip.
- **Walls.** Cream subway tiles (152 × 76 mm) on the vault, with bands of colored tile, framed poster panels, a station-name sign every few bays, and benches against the wall in recesses.
- **Lights.** Strip luminaires running along the vault ~3–4 m above the platform, every 2–3 m, at 4000–5000 K, plus warmer older fittings near the stairs.

Build order:
1. **Blockout.** A vault cylinder section with Solidify; platform slab; track bed; tunnel mouth ring; hero camera; human proxy. Screenshot.
2. **Kit.** One 3 m wall bay (tile vault section + poster frame + light fitting with area light), bench (2 variants), poster (4 variants), sign, sleeper, rail profile (curve with a rail-shaped bevel object), insulator pot.
3. **Assembly.** Array or instance the bays along the platform with random variants; array sleepers and rails along the track; the tunnel mouth with cables and a dark interior.
4. **Materials.**
   - Per-tile random tile shader with dirty grout.
   - Floor-up dirt, ceiling soot (heaviest near the tunnel mouth: brake dust and air flow), drip streaks under poster frames.
   - Polished walking path on the platform floor; gum dots.
   - Rust-brown iron dust on track ballast and sleepers; shiny worn tops on the running rails.
5. **Lighting.** Fittings with area lights; light tree on; exposure tuned; optional faint haze toward the tunnel.
6. **Story details.** Departure board, CCTV, cable runs in the tunnel, a newspaper on a bench, a puddle near the pit.
7. **QA**, final render, save, report.

## 12. Snippets

Random collection instances along a line, with a fixed seed:

```python
import bpy, random
random.seed(7)
variants = [bpy.data.collections[n] for n in ("KIT_Bench_A", "KIT_Bench_B")]
target = get_collection("Furniture")            # helper from bpy-patterns.md
for i, x in enumerate(range(3, 120, 9)):        # one bench every 9 m
    inst = bpy.data.objects.new(f"Bench_{i:02d}", None)
    inst.instance_type = 'COLLECTION'
    inst.instance_collection = random.choice(variants)
    inst.location = (x + random.uniform(-0.05, 0.05), 1.6, 0.0)
    inst.rotation_euler[2] = random.uniform(-0.02, 0.02)
    target.objects.link(inst)
result = {"benches": i + 1}
```

Keep `KIT_` collections excluded from the view layer (or move them out of the scene and keep only their instances) so the originals don't render at the origin.

Per-tile random tile shader (core of the graph):

```python
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
brick = nt.nodes.new("ShaderNodeTexBrick")
brick.offset = 0.0                               # stacked grid; 0.5 for running bond
brick.inputs["Color1"].default_value = (0, 0, 0, 1)
brick.inputs["Color2"].default_value = (1, 1, 1, 1)
brick.inputs["Mortar"].default_value = (0, 0, 0, 1)
brick.inputs["Brick Width"].default_value = 0.152   # with object/world-space mapping in metres
brick.inputs["Row Height"].default_value = 0.076
brick.inputs["Mortar Size"].default_value = 0.002
brick.inputs["Scale"].default_value = 1.0
# brick.outputs["Color"] -> random 0..1 per tile; brick.outputs["Fac"] -> mortar mask
```

Feed `Color` through Map Range into hue/value/roughness offsets, and use `Fac` to mix in the grout material and drive a small negative bump. Drive the coordinates from Texture Coordinate → Object (or Position) so the metre-based sizes hold.

Floor-up dirt mask:

```python
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
rng = nt.nodes.new("ShaderNodeMapRange")
rng.inputs["From Min"].default_value = 0.0      # floor height
rng.inputs["From Max"].default_value = 0.35     # dirt fades out by 35 cm
rng.inputs["To Min"].default_value = 1.0
rng.inputs["To Max"].default_value = 0.0
nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
# multiply rng.Result by a Noise texture, then use it to darken base color / raise roughness
```

Area light inside an emissive fitting:

```python
fit_light = bpy.data.lights.new("LGT_Strip", 'AREA')
fit_light.shape = 'RECTANGLE'; fit_light.size = 1.2; fit_light.size_y = 0.08
fit_light.energy = 60                              # W; tune by eye with exposure
try:
    fit_light.use_temperature = True; fit_light.temperature = 4500   # 4.x+/5.x
except AttributeError:
    fit_light.color = (1.0, 0.95, 0.88)
```

Check the result of each snippet with a screenshot. Property names drift between Blender versions, so if an attribute errors, look it up (`dir(obj)` or the API docs tool) rather than guessing.

## 13. A real-world environment workflow (canal scene breakdown)

These lessons come from an environment artist's breakdown of a photoreal Utrecht canal scene built in Blender with Poly Haven assets ("Creating Hyper Realistic Environments in Blender", Pietro Chiovaro). They reinforce the sections above and add a few production tricks.

- **Reference before geometry.** Screenshot the real place (map street views, photos) and bring the images into Blender next to the viewport. Keep checking them as you build: what's missing, where the scale is off, where proportions drift.
- **Materials on the blockout.** Give the blockout quick UVs and real materials early, so you judge proportion and material scale together rather than discovering wrong texture scale at the end.
- **Asset library, not one-by-one imports.** Downloaded Poly Haven `.blend` assets can sit in a Blender asset library (marked as assets) for fast drag-in. Repeated imports create duplicate materials (`Brick`, `Brick.001`, `Brick.002`…). Merge them (`dedupe_materials()` in `scripts/chunk_tools.py`) so the project stays clean and edits apply everywhere.
- **Low-poly where possible, bevels where it shows.** Bridges, quays and walls were simple shapes: a circle extruded for an arch, cubes for the deck. Bevelled edges (Ctrl+B / Bevel modifier) catch light, and simple UVs carry the materials. The polycount stays low, so renders stay fast.
- **Calibrate materials against the reference.** A library material is a starting point, not the answer. The artist's brick was noticeably too saturated compared with the real canal. Compare hue, saturation and value side by side with the reference and adjust (Hue/Saturation node before Base Color).
- **Photo cards for distant context.** Distant buildings were photo cut-outs (sky removed to alpha) on image planes: a matte-painting trick from film and TV. Viewed straight on they're convincing.
  - Seen at an angle, they need help to read as 3D. Stacking a few offset duplicates of the card in depth gives a parallax-like effect.
  - With distance, depth of field and motion blur, nobody notices.
  - Use this for backgrounds beyond ~30 m when modeling them would be wasted effort. Only use photos the user provides or that are licensed for it, e.g. CC0.
- **Decals are mandatory.** Fallen leaves on the ground and on water, cracks in concrete and brick, and stains add storytelling. They also **hide unconvincing seams** where models meet. Always budget time for a decal pass.
- **Decide the mood, then light it.** The hard part is knowing what the image should feel like (romantic, dramatic, mysterious). The artist's process:
  - put point lights at each real lamp to read the practical lighting;
  - add an HDRI matching the intended weather and time (a cloudy November night);
  - add a box with a simple Volume shader where fog should gather, not everywhere.
- **Set dressing is where most of the time goes.** Place props, render, compare with the reference, move things by centimetres, render again. Many small renders beat one big one.
- **Handheld camera for realism in animation.** A keyframed walk-through camera plus a subtle procedural shake (e.g. the free Camera Shakify add-on, or a noise modifier on the camera's F-curves) reads like phone footage. Keep the intensity low. Motion blur on.
- **Not covered in the video:** the water shader and the falling-leaf particles. The video doesn't show how they were made, so build those from the general material and geometry-nodes guidance instead.
