# Red fire hydrant on a wet city sidewalk at dusk

**Final render:** `final_render.png`, 1920x1080, Cycles with OptiX GPU, 256 samples (adaptive), OpenImageDenoise.
**Blend file:** `fire_hydrant_wet_sidewalk_dusk.blend`
Both files are in this folder: `C:\Users\Hype\Desktop\hyperrealistic3d\hyperrealistic-blender-modeler-workspace\iteration-1\rainy-street-fire-hydrant\with_skill\outputs`. Blender confirmed both exist.

## Brief / assumptions
- **Hydrant type:** a US-style dry-barrel municipal hydrant: a flanged base with 6 bolts, a straight barrel, and a bonnet flange with 8 bolts. It has a domed bonnet with a pentagon operating nut, one large 4.5" pumper nozzle and two 2.5" side hose nozzles, all with pentagon-nut caps.
- **Scale:** 0.735 m tall, 0.34 m base-flange diameter, about 0.43 m across the side caps. Real-world metric scale.
- **Setting:** a long straight downtown street at dusk just after rain. A brick building with lit storefronts sits behind the sidewalk, and blocks of buildings run across the street. A row of sodium-orange streetlights recedes to a vanishing point.
- **Camera:** "CAM_Hero" is a 35 mm lens at about 30 cm height (a crouching street-level shot), f/3.2 with focus on the hydrant. The hydrant sits on the right third with the street receding to the left.

## What was built
- **Model_FireHydrant** (26 objects, parented to the `Hydrant_Root` empty):
  - Lathe-profile body (`Hydrant_Body`), separate nozzles, caps and cap nuts, operating nut and collar, and 14 hex flange bolts.
  - Every part has a Bevel modifier (angle-limited, harden normals) plus a Weighted Normal modifier.
- **Environment:**
  - `Sidewalk_Slabs`: about 640 individual 1.5 m concrete slabs with 8 mm joints and a few mm of random tilt, bevelled.
  - `Curb_Stone`, `Road_Asphalt`, the far curb and far sidewalk.
  - `Building_Facade` (brick) with storefront and upper windows and dark metal frames, plus `Building_FarBlocks` and windows across the street.
  - `StreetLight_Poles`, `_Heads` and `_Lenses` (emissive): 35 lamps.
- **Collections:** `Model_FireHydrant`, `Environment`, `Lights`, `Cameras`.

## Materials (all procedural, no image textures)
- **MAT_Hydrant_PeelingPaint** builds up layers, all driven by noise fields in world space:
  - Deep red paint with large-scale fading and vertical run-off streaks.
  - Two noise layers for peeling: large peel patches plus small chips. They expose a thin tan/grey older paint layer at the chip edges, then rust (dark brown to orange noise, roughness ~0.88).
  - A height mask that pushes peeling toward the base, an edge-wear mask (Bevel node vs. normal) and AO cavity grime.
  - A wet clear-coat that is reduced over the rust, and roughness variation plus Voronoi water droplets.
  - Bump from the paint-chip step, rust grain and droplets.
- **MAT_Concrete_Wet / MAT_CurbConcrete_Wet / MAT_Asphalt_Wet** share one wet-ground graph:
  - Base colour darkened for wetness, with a darker damp rim around puddles.
  - A noise-masked puddle layer with roughness ~0.015 (mirror-like) and surface bump suppressed under the water, plus faint ripples.
  - Wet surface roughness of 0.18–0.5 elsewhere, and a grain + pit bump.
  - The asphalt also has aggregate speckles and extra puddling along the gutter.
- **Other materials:** brick (Brick texture with mortar bump and roughness), warm/cool varied window emission, emissive lamp lenses, and dark painted steel and metal frames with roughness noise.

## Lighting / render
- **World:** a physical Sky texture (Multiple Scattering model) with the sun 1.5° below the horizon gives a blue-to-pink dusk gradient.
- **Streetlamps:** 35 warm spot lights (900 W, ~2000K-ish orange) along the street, plus one lamp just behind the camera (out of frame) that lights the hydrant's front.
- **Fill:** a weak cool sun fill and a soft warm area light standing in for the storefront spill.
- **Colour management:** AgX with the Medium High Contrast look, exposure -0.3, indirect clamp 10.

## QA performed
- **Test renders:** 7 iterations. Fixes along the way:
  - The first version was far too bright and read like daytime, and the ground looked dry.
  - Bright yellow under-paint was replaced with a thin tan primer layer.
  - The view originally faced a wall, so the street was extended to 300 m to reveal the sky and the far buildings.
  - Small paint chips were added.
- **Audit script:** `scene_audit.py` found 0 hard issues. Every mesh has a material, there are no default names, no loose or degenerate geometry, and no unapplied scale. Its bounding-box "overlap" notes come only from the very large joined background mesh.
- **Grounding:** the hydrant was moved off a slab joint and raycast onto the slab top. Contact is flush to within 0.1 mm.
- **Back-angle check:** a test render from behind confirmed the model has no shading artifacts and sits properly on the slab.

## Known limitations / next steps
- The upper-floor windows read as flat, uniformly lit panels with no interior detail. Up close they look CG, so interior cards or blinds would help.
- Puddles are a roughness/colour mask on flat geometry, with no real water depth or displacement. Some sidewalk puddles reflect the dark facade and read as dark blotches.
- There is no falling rain, no wet mist or volumetric haze, and no hose-cap chains.
- The peeling pattern is driven by world-space noise. The back of the hydrant is more heavily rusted than the front, and the pumper cap shows fairly heavy rust, a bit more than "some rust".
- The background buildings are simple boxes. They work because they are out of focus, but would not hold up in a wider shot.
