# PBR Material Reference

Starting values for Principled BSDF. Colors are linear RGB (what Blender's node inputs expect). These are *starting points* — always add variation (see the recipes below) on hero surfaces.

## Contents
1. Metals
2. Dielectrics (plastic, glass, liquids, stone, wood…)
3. Organic / subsurface
4. Procedural recipes (edge wear, cavity dirt, smudges, dust, color variation, brushed metal, scratches)
5. Image texture checklist

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
| Clear glass | 1, 1, 1 | 0.0–0.03 | 1.50 | Transmission 1.0, needs thickness |
| Frosted glass | 1, 1, 1 | 0.3–0.5 | 1.50 | Transmission 1.0 |
| Water | 1, 1, 1 | 0.0 | 1.33 | Transmission 1.0; tint via volume absorption |
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
| Skin (light) | 0.8, 0.55, 0.45 | 0.35–0.5 | Weight 0.2–0.4, radius (1.0, 0.2, 0.1) × scale ~0.005 m |
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
