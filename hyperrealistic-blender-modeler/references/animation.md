# Animation and Motion Realism

Read this when anything moves: a turntable, a camera move, dust, foliage, water. Good motion adds realism even to "still" shots; bad motion breaks it faster than any material flaw.

## Rules

1. **Motion blur on every animated render.** Baseline **shutter 0.5** (Blender's shutter is in frames: 0.5 = the 180° rule = normal cinematic blur at any frame rate). Go toward 1.0 for implied night/low-light shots, 0.2–0.3 for crisp action-cam looks. Long shutters (several frames) are a stylised streak look for sparks, not a default. Stills can use it too: keyframe two poses and render the in-between with blur.
2. **Camera movement comes from an imagined operator.** Decide the rig first, then animate to match it:
   - dolly or slider: slow, smooth, linear-ish
   - gimbal: smooth with slight floating drift
   - handheld/phone/drone: small jitter, imperfect framing, attention that wanders
   - first-person walk: eye height ~1.7 m, 20–24 mm lens
   Too-smooth motion on a scene meant to feel candid is itself a tell. For handheld, add a Noise F-curve modifier to rotation (small strength, low frequency) rather than hand-keying shake.
3. **Turntable:** Empty at the subject, camera parented to it, rotate the Empty, set interpolation to **Linear** (default Bezier ease-in/out looks wrong). For a seamless loop key 0° at frame 1 and 360° at frame N+1, render 1..N. Orbiting the camera keeps lighting fixed to the world; spinning the object makes its reflections move. Choose on purpose.
4. **Airborne particles (dust, sparks, bubbles, pollen): gravity off.** Falling reads as rain. Emit from Volume with zero normal velocity so they start still. Add a Turbulence force field (strength ~2–2.5) for gentle drift. Give scale randomness so most specks are tiny; a few elongated ones read as fibres.
5. **Hide emitters and bake simulations** before rendering. Unbaked caches are the main reason particles glitch or vanish in final renders.
6. **Wind on foliage: procedural, not physics.** Noise-driven rotation in Geometry Nodes or a Wave/Displace modifier with low strength and high detail, so plants move independently. Loops cleanly and needs no bake.
7. **Water motion: fake it first.** Animate the noise/displacement coordinates (e.g. a driver on the 4D W value: `frame/5000`) and drift the mapping in X/Y, so it's not a single-axis wobble. Dynamic Paint (canvas = water, brush = object) for ripples around objects. Reach for a fluid sim only when nothing else works.
8. **Pre-roll** effects that were "already happening" when the camera started (fire sparks, smoke, rain): start the emitter before frame 1 (e.g. frame −150).
9. **Glass and caustics shimmer** between frames because they converge unevenly. Give those shots more samples, use OIDN on GPU with quality High, and the blue-noise sampling pattern (4.4+) if available.

## Snippet

```python
import bpy, math
sc = bpy.context.scene
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5      # 180° rule

def turntable(target_empty, frames=120):
    sc.frame_start, sc.frame_end = 1, frames
    target_empty.rotation_euler = (0, 0, 0)
    target_empty.keyframe_insert("rotation_euler", index=2, frame=1)
    target_empty.rotation_euler[2] = math.tau
    target_empty.keyframe_insert("rotation_euler", index=2, frame=frames + 1)
    ad = target_empty.animation_data
    fcurves = ad.action.fcurves if hasattr(ad.action, "fcurves") else [
        fc for layer in ad.action.layers for strip in layer.strips
        for bag in strip.channelbags for fc in bag.fcurves]   # 4.4+ layered actions
    for fc in fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    print("Turntable:", target_empty.name, "frames 1 -", frames)
```
