# PBR Material Reference

Starting values for Principled BSDF. Colors are linear RGB (what Blender's node inputs expect). These are *starting points* — always add variation (see the recipes below) on hero surfaces.

## Contents
1. Metals
2. Dielectrics (plastic, glass, liquids, stone, wood…)
3. Organic / subsurface
4. Procedural recipes (edge wear, cavity dirt, smudges, dust, color variation, brushed metal, scratches)
5. Image texture checklist
6. Practitioner rules: glass & liquids, imperfections, decals, special layers

## 1. Metals (Metallic = 1.0)

| Material | Base Color (linear) | Roughness | Notes |
|---|---|---|---|
| Aluminium (raw) | 0.91, 0.92, 0.92 | 0.25–0.45 | Anisotropic if brushed |
| Aluminium (anodized) | tinted, value ~0.4–0.7 | 0.3–0.5 | Often modeled as coat over metal |
| Steel / stainless | 0.56, 0.57, 0.58 | 0.2–0.4 | Brushed: anisotropy 0.5–0.8 |
| Chrome | 0.55, 0.56, 0.55 | 0.02–0.08 | Needs a rich environment to read |
| Iron (raw) | 0.53, 0.51, 0.49 | 0.4–0.7 | |
| Gold | 1.00, 0.77, 0.34 | 0.1–0.3 | |
| Copper | 0.95, 0.64, 0.54 | 0.15–0.35 | Patina: non-metal teal layer |
| Brass | 0.91, 0.78, 0.42 | 0.2–0.4 | |
| Silver | 0.97, 0.96, 0.92 | 0.05–0.25 | |
| Rust (on iron) | 0.25, 0.08, 0.03 | 0.8–0.95 | Metallic 0, masked over iron |

## 2. Dielectrics (Metallic = 0.0)

| Material | Base Color (linear) | Roughness | IOR | Other |
|---|---|---|---|---|
| Glossy plastic (ABS) | any, value 0.02–0.8 | 0.1–0.3 | 1.46 | |
| Matte plastic | any | 0.45–0.7 | 1.46 | Micro-bump noise scale ~800 |
| Rubber | 0.02–0.05 | 0.6–0.9 | 1.52 | Slight sheen |
| Clear glass | 1, 1, 1 | 0.01–0.03 (never 0) | 1.50 | Transmission 1.0, needs thickness; tint via Volume Absorption |
| Frosted glass | 1, 1, 1 | 0.3–0.5 | 1.50 | Transmission 1.0 |
| Water | 1, 1, 1 | 0.0–0.02 | 1.33 | Transmission 1.0; tint via volume absorption |
| Ceramic glaze | any | 0.05–0.2 | 1.5 | Or base + Coat Weight 1, coat roughness 0.05 |
| Unglazed ceramic / clay | 0.5, 0.3, 0.2 | 0.7–0.9 | 1.5 | |
| Concrete | 0.35–0.5 grey | 0.8–0.95 | 1.5 | Bump + displacement |
| Marble | 0.75–0.85 | 0.1–0.3 polished | 1.5 | Subsurface 0.1–0.3 |
| Wood (raw) | 0.2–0.5 browns | 0.5–0.8 | 1.5 | Grain texture essential |
| Wood (varnished) | same | 0.5 under, coat 0.05–0.15 | 1.5 | Coat Weight 1.0 |
| Car paint | any | 0.3–0.4 base | 1.5 | Coat Weight 1, coat roughness 0.02; metallic flakes via noise into normal |
| Fabric (cotton) | any, value ≤0.7 | 0.8–1.0 | 1.5 | Sheen Weight 0.3–1.0 |
| Leather | 0.05–0.3 | 0.4–0.7 | 1.5 | Fine voronoi/noise bump |
| Paper | 0.75–0.85 | 0.7–0.9 | 1.5 | Subsurface ~0.05 for thin sheets |
| Snow | 0.85 | 0.4–0.6 | 1.31 | Subsurface |
| Asphalt | 0.04–0.08 | 0.7–0.95 | 1.5 | |

## 3. Organic / subsurface

| Material | Base Color | Roughness | Subsurface |
|---|---|---|---|
| Skin (light) | 0.8, 0.55, 0.45 | 0.35–0.5 | Weight 0.2–0.4, Random Walk (Skin), radius (1.0, 0.2, 0.1) × scale ~0.005–0.02 m (too high = waxy, too low = plastic) |
| Wax / candle | 0.85, 0.8, 0.65 | 0.3–0.5 | Weight 0.5–1.0 |
| Leaves | 0.05, 0.15, 0.02 | 0.4–0.6 | Weight 0.1–0.3 or translucency via Mix + Translucent BSDF |
| Fruit (apple) | varies | 0.2–0.4 | Weight 0.1–0.3 |
| Milk | 0.9, 0.9, 0.85 | 0.1 | Weight 1.0 |

Subsurface radius is in scene units (metres), so it depends on correct object scale.

## 4. Procedural recipes

All of these are node graphs you build via `bpy` (see `bpy-patterns.md` for a node helper). Keep contrast low; check at the final camera distance.

**Edge wear**
- Cycles: Geometry → Pointiness → ColorRamp (tight, around 0.5–0.55) → multiply by Noise (scale 20–60, detail 8) → mask.
- Alternative/EEVEE-safe: Bevel node (radius ~0.002–0.01) → dot product with true Geometry Normal → invert → ColorRamp → mask.
- Use mask to mix base color toward a lighter/bare material, and roughness toward a polished or rough value depending on the material (painted metal edges → bare metal, metallic 1, rougher).

**Cavity dirt / occlusion grime**
- Ambient Occlusion node (distance 0.02–0.1 m, *Only Local* on) → invert → ColorRamp → × Noise → mask.
- Darken base color by 10–30% and raise roughness by +0.1–0.2 in the mask.

**Smudges & fingerprints on glossy surfaces**
- Noise (scale 3–8, detail 2) × Voronoi (smooth F1, scale 40) → ColorRamp narrow → add 0.05–0.15 to roughness.
- Only on hero surfaces that would be touched (screens, glossy plastic, chrome, glass).

**Dust on upward faces**
- Geometry Normal → Separate XYZ → Z → ColorRamp (0.6→0.9) × Noise (scale 50, detail 10) → mask.
- Mix toward a light grey-brown (0.4, 0.37, 0.33), roughness 0.9.

**Base color variation**
- Noise (scale 2–10, detail 4) → ColorRamp between two colors ±5% value → base color. Add Object Info → Random → Hue/Saturation for per-object variation on repeated parts.

**Brushed metal**
- Noise texture with vector stretched along one axis (Mapping scale e.g. (1, 1, 200) on the brush direction) → roughness variation ±0.05 and bump strength 0.02–0.05.
- Principled Anisotropic 0.5–0.8 with a tangent along the brush direction (needs UVs or radial tangent).

**Fine scratches**
- Wave texture (bands, scale 50–200, distortion 10–30) or stretched noise → ColorRamp very narrow → Bump (strength 0.05–0.2, distance 0.0005) and roughness ±0.1. Two layers at different rotations look more natural.

**Micro surface bump (makes "plastic CG" look real)**
- Noise scale 300–1000 → Bump strength 0.02–0.08. Almost every manufactured surface has this.

**Breaking up texture tiling**
- Two Image Texture nodes sampling the same image at different scales/rotations, blended with a large noise mask.
- Or offset UV by Noise Color × small factor before sampling.

## 5. Image texture checklist

- Albedo/diffuse/basecolor → **sRGB**.
- Roughness, metallic, normal, displacement, AO, opacity → **Non-Color**.
- Normal map → Normal Map node (tangent space; check if OpenGL vs DirectX — DirectX maps need the green channel inverted).
- Gloss maps are inverted roughness → Invert node.
- AO maps: multiply into base color lightly (factor 0.3–0.5) or skip in Cycles (it computes real AO).
- Displacement map → Displacement node (midlevel 0.5, scale in metres, e.g. 0.01–0.05) → Material Output Displacement; set material `displacement_method = 'BOTH'` and give the mesh enough subdivision.
- Real-world scale: set Mapping scale so a 1 m Poly Haven texture covers ~1 m of surface.
- Verify no pink (missing) textures in the screenshot.

## 6. Practitioner rules: glass & liquids, imperfections, decals, special layers

**PBR plumbing**
- Specular IOR Level stays ~0.5 (= IOR 1.5) on dielectrics, specular tint 0. Everything reflects about the same base amount; roughness is what differs.
- **Never zero reflectivity to make something "matte".** Raise roughness instead.
- Never use a normal map and displacement made from the same height data; pick displacement. True displacement strength usually 0.02–0.05 m, not the default 1.0. Use 16-bit height maps (8-bit shows banding).
- Noise texture Detail costs ~2× per step; keep it ≤5–6 unless the close-up needs more.
- Base-colour anchors (albedo): coal ~0.04, asphalt 0.05–0.12, grass 0.15–0.25, concrete 0.25–0.4, fresh snow ~0.8. Outside ~0.02–0.9 the GI energy balance breaks and no light rig fixes it.

**Glass and liquids**
- Model vessels like real objects: solid walls, a base thicker than the walls, a rounded rim lip, two support loops just under the rim before Subdivision. Solidify is fine for simple straight cylinders (1–3 mm walls); stemware and flat panes need hand-built topology.
- Glass Base Color = 1.0 white. Tint comes from **Volume Absorption** in the Volume output, so it deepens with thickness on its own (density ~0.5–1 subtle, up to ~100 for stained glass). Never tint glass through base colour.
- **Liquid IOR 1.33**, distinct from the glass. The liquid mesh slightly **overlaps** the inside of the glass wall (never flush: that z-fights). Model a meniscus by insetting the top face and pulling it down.
- Coloured liquids need volume bounces (~12); cloudy liquids (milk, smoothies): Transmission 1 with some Transmission Roughness, colour via the Volume input.
- Wet surfaces are glossier **and** darker: drive a mask into lower roughness, a Coat layer, and a slightly darker base colour.

**Imperfections (route by physical cause)**
- Stack many subtle layers, each one real flaw: crevice dirt, edge wear, roughness variation, dust, smudges, discolouration. One flat high-quality texture is never enough.
- **Crevice dirt is usually the last node before the output:** AO (or Pointiness) → ColorRamp → Mix Multiply over base colour (factor ~1.0 standard, 0.5 subtle), and feed the same mask into bump at ~0.25 so grime reads recessed. Drive the AO distance with noise so it isn't uniform.
- Pick the edge mask by geometry: Bevel-based for hard-surface, AO for curved, Pointiness for dense organic meshes. Floor the wear mask at ~0.01 so no edge is perfectly clean.
- **Scratches change the surface → bump/normal. Fingerprints and oil change reflectivity → roughness only.** Dust sits on up-facing surfaces.
- Write down **where and why** wear happens before adding it: drips run down from ledges, overhangs protect what's under them, hands and feet polish what they touch. Random placement reads fake. Use procedural masks for the base pass and hand-placed or vertex-painted masks where the story needs a specific mark.
- Match imperfection size to the camera: fingerprints and fibres only in shots that could resolve them; wear, grime and roughness variation belong everywhere.
- Hero surfaces from photo/scan texture sets; procedural masks for wear that has to follow the geometry. A bare diffuse photo with no roughness/normal is "a printed sticker"; at minimum reuse the photo, desaturated and remapped, as roughness and bump.
- Set texture mapping to the texture's real-world size (a 2.5 m texture on a 2 m surface → scale ×1.25 or ×0.8 as appropriate) and check against a known object.

**Decals (three gotchas)**
- Drive the Mix factor from the decal image's **Alpha**, not its colour, so the decal stays recolourable.
- Set the decal Image Texture's extension to **Clip**, or it tiles across the whole UV space.
- Position and scale it with its own Mapping node off the UV coordinates; no second UV map needed.

**Special layers (Principled, 4.0+)**
- **Coat** = a separate, sharper clear layer with its own normal (scratched lacquer over wood; car clear coat).
- **Sheen** ~0.1–0.3 on most cloth, higher for velvet.
- **Thin Film** for iridescence (soap bubbles, oil slicks, coated optics): thickness ~200–800 nm.
- **Anisotropic** with a tangent (radial for pan bottoms, UV for brushed sheet) for machined metal highlights.
- **Car paint** has three layers: metallic base, noise-driven flake normals, and a smooth Coat on top. Single-layer metallic reads as a toy.
- Skin close-ups: a sparse, very fine, slightly transparent hair layer (peach fuzz) catching rim light is one of the biggest upgrades.
