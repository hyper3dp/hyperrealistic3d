# Realistic Coffee Mug - Blender

I modeled a realistic ceramic coffee mug with coffee in it, set it on a wooden tabletop, and rendered it in Cycles.

**What's in the scene**
- **Mug body**: built by spinning a real-world profile (about 8.3 cm across and 9.6 cm tall, a standard 11 oz mug). It has a recessed foot ring, walls that taper slightly, real wall thickness, a rounded lip and an inner floor. Smoothed with Subdivision Surface.
- **Handle**: a swept C-shaped curve with an oval cross-section. Both ends sink into the wall, and it was converted to a mesh.
- **Coffee**: a dark, glossy liquid surface (IOR 1.34) sitting about 1.5 cm below the rim.
- **Materials**: a glossy terracotta-red glaze with a clear coat, faint color variation where the glaze pools, and a fine surface bump. The tabletop uses procedural wood grain, with a neutral backdrop behind it.
- **Lighting and camera**: a warm key light, a cool rim light and a soft fill light (all area lights) under a dim world. The camera is an 85 mm lens with shallow depth of field (f/5.6), focused on the front of the mug. Color management is AgX.
- **Render**: Cycles on the GPU (OptiX), 256 samples, denoised, 1600x1200.

**Files**
- `coffee_mug.blend`: the scene
- `final_render.png`: the final render
- `preview.png`: low-res test render

**Known limitations / easy next steps**
- The wood texture is procedural and reads as soft or streaky up close. A scanned wood PBR texture or an HDRI would push the realism further.
- There is no steam, crema, chips or wear, and no unglazed bisque ring on the foot. Any of these can be added.
- If you want a different glaze color (white, black, speckled stoneware), change the ColorRamp in the `Ceramic_Glaze` material.
