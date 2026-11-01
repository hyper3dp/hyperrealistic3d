# Photoreal Doctrine: the rules, the tells, the checklist

The short version of what working realism artists agree on. It was condensed from a cross-check of ~57 tutorials and talks; see `CREDITS.md`. The more independent artists teach a rule, the higher it sits here. Use it when planning, and again when a render "looks CG" and you need to find out why.

## Contents
1. Core principle
2. The ten laws
3. The "looks fake" list (ranked)
4. Pre-render checklist
5. Perceptual QA tricks
6. Where to read more

## 1. Core principle

**You are not simulating reality. You are simulating a photograph of reality.** Every choice (exposure, depth of field, motion blur, grain, lens artifacts, what clips) should answer: *what would a real camera with a real lens, held by a real person, in this light, have captured?* As soon as one element could not have come out of a camera, viewers read the image as CG, even when they can't say why.

Where the effort goes: **materials and lighting are most of the realism.** Modeling and post split the rest. Spend time to match.

## 2. The ten laws

1. **Colour management first.** Never render on Standard. Use AgX (4.0+) or Filmic (3.x) plus a contrast Look. Check exposure with False Color while lighting. → `lighting-camera.md` §3
2. **Real-world scale, metric, typed in.** Look dimensions up. Scale drives DOF blur, light falloff, displacement height, texture density and AO distance. Bad scale can't be fixed later with materials or lights. Keep a 1.8 m human proxy in big scenes to sanity-check.
3. **Light with real sources, starting from black.** HDRI is the default environment. Use Kelvin colours (Blackbody node) for natural sources. Shape shadows, don't erase them. Add lights one at a time from a dark scene. → `lighting-camera.md` §1
4. **No flat values.** Every property varies across the surface: roughness from maps or noise, crevice dirt, stacked imperfection layers. Metallic stays 0 or 1. Non-albedo maps are Non-Color. → `materials.md`
5. **Nothing is perfectly sharp, clean or aligned.** Bevel every hard edge. Put wear, dust and fingerprints only where the camera could resolve them. Rotate clutter slightly off-axis. Break straight lines that would sag or warp in reality.
6. **The camera is a physical object.** Choose the focal length on purpose. Keep DOF on, aimed with an Empty, with blur that matches the scene's scale. Use 6–8 aperture blades. Put motion blur on anything that moves. → `lighting-camera.md` §2
7. **Render clean, then rebuild the photograph in post.** Denoise fully, then add real grain on top: render noise is not grain. Grade with Offset/Power/Slope. Save EXR for anything you'll grade. → `post-compositing.md`
8. **Post artifacts are tiny and justified.** Glare only around truly bright sources. Chromatic aberration 0.004–0.02. Lens distortion barely there. A slight softening pass takes the edge off "3D sharpness".
9. **Reference discipline and an attention budget.** Work from real photos, not memory. The HDRI or backplate's light direction must match the key light. Lock the camera before detailing, and spend detail only where the eye lands.
10. **Restraint.** Dial every effect back from "looks cool" to "stops being noticeable". When two settings both look plausible, choose the subtler one.

## 3. The "looks fake" list (ranked by how many artists name it)

1. View transform left on Standard (clipped, harsh highlights).
2. No DOF, or too much (miniature effect: the blur contradicts the scale).
3. Perfectly sharp 90° edges.
4. Flat, uniform material values (plastic look).
5. Reflectivity zeroed to look "matte" (raise roughness instead; everything reflects).
6. No motion blur on moving things.
7. HDRI/backplate light direction doesn't match the key light.
8. A guessed procedural sky where an HDRI would do better.
9. Low-quality organics (plants, people, animals): use sparingly or use top assets.
10. Visible texture tiling.
11. Diffuse-only texturing (a photo stuck on a box with no roughness/normal/height).
12. Overdone or unjustified post effects.
13. Guessed IOR (a liquid with the glass's IOR reads as "glass inside glass").
14. Pure black, pure white, or fully saturated colours anywhere.
15. Everything clean and axis-aligned.

## 4. Pre-render checklist

Run before every final render. Each miss is one of the tells above.

- [ ] View transform AgX/Filmic + contrast Look; exposure checked with False Color (some mid-grey on the subject; clipping only where a real camera would clip)
- [ ] Real metric scale, scale applied
- [ ] Every hard edge bevelled (or Bevel shader node on dense scenes)
- [ ] Roughness varies on every visible material; metallic 0/1; Non-Color set; normal maps through a Normal Map node
- [ ] Crevice dirt (AO/pointiness) on hero materials
- [ ] HDRI or a physically justified rig; key light matches backdrop direction
- [ ] Shadows visible and shaped; no light radius left at 0; plausible Kelvin colours
- [ ] DOF on, focus Empty, f-stop fits the shot and scale, 6–8 blades
- [ ] Motion blur on if anything moves (shutter 0.5 by default)
- [ ] Bounces raised for glass, liquid or volume (black patches = ray starvation)
- [ ] Denoised, real grain composited on top
- [ ] Every post effect subtle and with a physical source
- [ ] Something imperfect in frame: dust, wear, clutter, slight misalignment
- [ ] Nothing 100 % black, 100 % white or 100 % saturated

## 5. Perceptual QA tricks

- **Flip it horizontally.** Your eye has adapted to the image; mirroring resets it and flaws jump out.
- **Squint test.** Look at the render small or blurred. Realism survives blurring; CG-ness doesn't.
- **A/B one variable.** Render to slots and flip between them. Change one thing at a time.
- **Fresh eyes.** After a long session, hand the render to a reviewer that hasn't seen the build (the `render-critic` agent; see SKILL.md §11).
- **Side by side with the reference** at the same size: compare hue, saturation, value, contrast and shadow softness.

## 6. Where to read more

| Topic | File |
|---|---|
| Lighting, volumetrics, camera, colour management, render settings | `lighting-camera.md` |
| Shaders, glass, liquids, imperfections, decals | `materials.md` |
| Compositing, grain, grading, lens effects | `post-compositing.md` |
| Animation, motion blur, camera moves, particles | `animation.md` |
| Big spaces | `environments.md` |
