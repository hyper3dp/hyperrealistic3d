# London Underground-style platform: "Hallam Cross"

The Cycles render is done at 1920x1080 and the scene is saved as a .blend.

## How this was built (please read first)
The live Blender MCP connection (port 9876) was not available for this whole session. The open Blender 5.2.3 window had no MCP server listening, and the `_for_cli` MCP tool couldn't find a Blender executable. So I built the scene by running the same Blender 5.2.3 install headless from the command line (`blender.exe -b --python ...`). The build is a set of bpy scripts.
- The build script clears all objects and datablocks first, then builds everything from code and saves the .blend.
- Instead of viewport screenshots I checked the work with low-res Cycles test renders: the hero shot plus three close-up views of the bench, the track/pit and the tunnel mouth.
- The Blender window you have open was not touched. To see the scene, open the .blend.

## Brief and assumptions
- **Place and era:** a deep-level, tube-style platform tunnel with Victorian-style glazed tiling and later fittings. The time is late evening, so the platform is empty but clearly used.
- **Branding:** the station name is invented ("HALLAM CROSS"). The signs are in the style of a roundel (red ring, blue bar) but are not the trademarked logo. All the adverts are invented brands.
- **Real-world scale (metres):**
  - Platform tunnel: about 7.5 m diameter, 51 m modelled length.
  - Running-tunnel mouth: 3.7 m diameter.
  - Platform: 0.95 m above the rail tops, about 3.6 m wide.
  - Track: standard 1.435 m gauge.
  - Wall tiles: 152 x 76 mm. Floor tiles: 300 mm. Bench seat: 0.45 m.
- **Shot:** eye level (1.65 m), 28 mm lens, camera kept level so verticals stay vertical. It stands on the platform about 1.9 m back from the edge and looks down the platform into the tunnel mouth, about 42 m away.

## What was built (247 objects, in collections)
- **Structure**
  - Curved vault shell: 5,440 faces, with UVs in metres for the tiles and a 0.3 m Solidify.
  - Tiled end wall with the running-tunnel mouth cut by an exact Boolean, plus an iron collar around the mouth. Tiled rear wall.
  - A thin haze volume for depth.
- **Track**
  - Bullhead running rails, extruded from a real-ish profile and bevelled.
  - Four-rail electrification: an outer positive conductor rail and a centre negative rail, both on ceramic insulator pots.
  - Cast-iron rail chairs every 0.65 m (Array modifier).
  - A drainage pit between the rails along the platform, with cross-bearers, a puddle and litter in it.
  - Concrete sleepers in the tunnel section.
- **Platform**
  - Concrete coping with "MIND THE GAP" lettering, a worn yellow safety line, buff tactile blister paving (blisters are a shader bump), and a 300 mm tiled floor.
- **Running tunnel**
  - About 60 m of iron-segment lining, with flange rings every 0.508 m.
  - Cable runs, a lit red signal, and two dim warm bulkhead lamps further in.
- **Signage**
  - 6 large curved 48-sheet-style posters on the track-side wall and 6 smaller posters on the platform wall. Each has a frame, curved paper, a headline and a subline.
  - 5 roundel-style name boards on stand-off brackets.
  - A dot-matrix departure board ("1 Hammersley Park 2 min / 2 Clayfield 7 min") hung from the vault.
- **Lighting:** 32 suspended strip fittings in two rows, each a modelled housing plus diffuser.
- **Furniture:** 2 bench variants (one with a missing seat slat) built once as kit collections and placed 4 times as collection instances, with small random offsets and rotations.
- **Props and story details**
  - A newspaper on a bench and a coffee cup on the floor.
  - CCTV cameras, and a galvanised cable tray above the posters.
  - Sagging cable bundles on the track-side wall.
  - One dead fitting and one failing, dim, warm fitting.

## Materials (all procedural, no image textures)
- **Wall tiles:** a Brick-texture shader with per-tile random value and hue, occasional odd replacement tiles, recessed grout, and glaze waviness in the bump. There's a green dado below 0.95 m and an ox-blood band at about 2.3 m.
- **Grime, placed by physics:**
  - floor-up dirt along the wall base;
  - heavy brake dust on the track side, rising from the trackbed;
  - soot toward the crown;
  - general darkening toward the tunnel end, plus a soot fan around the tunnel mouth;
  - vertical drip streaks.
- **Floor:** per-tile variation, a polished walking path down the middle, dirt toward the wall, gum dots, stains, and a wet patch with low roughness.
- **Rails:** rusty sides, with polished bright metal on the running tops of the running and conductor rails. The trackbed and pit concrete have iron-dust staining and wet patches.
- **Posters:** procedural artwork that is faded, dirtier at the bottom, with paste wrinkles. Two have torn corners showing the old backing.
- **Other:** timber benches with per-instance colour variation and worn seat tops, enamel signs, and painted metal with edge wear.

## Lighting, camera, render
- **Lights:** each fitting has a rectangular area light (45 to 68 W) inside its emissive diffuser, at 4100 to 4700 K varied per fitting. The failing one is at 2800 K and 25% power. There are also a red signal point light and two tunnel bulkheads. The world is near-black.
- **Cycles:** OptiX GPU on the RTX 5050, 384 samples (adaptive threshold 0.015), OpenImageDenoise, light tree on, bounces 12 total (diffuse 5, glossy 4, transmission 8), indirect clamp 10.
- **Colour:** AgX with the Medium High Contrast look, exposure -0.3.
- The final render took 104 s.

## QA
- The skill's scene_audit.py found 0 hard issues.
- Its "floating" and "sinking" notes are expected here: wall-mounted signs, light fittings, and structure that sits below platform level.
- The flat-roughness notes are only on emission and water materials.
- About 326k triangles, no image textures.

## Known limitations / what to refine next
- **Floor too clean and regular:** the floor tiles in the foreground still look a bit clean and regular. More scuffing, worn tiles, and a darker band along the platform edge would help.
- **No train, no people:** the platform is empty. A train arriving with motion blur, or a few figures, would sell the scale much better.
- **Simplified tunnel and pit:** the tunnel interior is simple (lining, flanges, cables). The pit has no detailed drain grates.
- **Signs and posters:** the poster artwork is abstract procedural graphics plus text, not photographic adverts. Signs are flat boards on stand-offs rather than curved enamel panels.
- **Leading lines:** the wall-tile rows run along the platform. The cable runs and the poster line make strong leading lines, but there's no stair or passage entrance to break up the length.
- **Haze:** it's very subtle (density 0.0025). Raise it on MAT_Haze_Volume for more atmosphere, at some cost in render time.
- **Viewport checks:** because the MCP link was down, I couldn't check the scene through the live viewport. All checks were done with test renders.

## Files
- underground_station_platform.blend: the scene, saved by Blender.
- final_render.png: 1920x1080 Cycles render from CAM_Hero.
- report.md: this report.
