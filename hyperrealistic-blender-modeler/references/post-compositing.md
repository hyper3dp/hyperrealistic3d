# Post and Compositing

**Render clean and neutral, then rebuild the photographic look on purpose.** Post is where "simulating a photograph" is finished, and where overdoing anything reads fake fastest. Calibrate every effect the same way: push it until it's clearly visible to place it, then dial it back to just below where you'd notice it.

## Contents
1. The post stack, in order
2. Atmosphere in post
3. When to go further
4. Snippet: a version-safe base compositor

## 1. The post stack, in order

1. **Denoise** with the Denoise node fed Normal + Albedo passes (enable Denoising Data on the view layer). Denoise fully: leftover render noise never reads as grain.
2. **AO grounding (optional)**: AO pass with a short distance (~0.2 m at product scale), multiplied over the beauty at 0.3–0.5. Don't use the World AO checkbox; it brightens everything.
3. **Grade** with Color Balance in **Offset/Power/Slope** mode (ASC CDL). Lift/Gamma/Gain and blend modes like Multiply/Screen/Overlay are display-referred and behave wrongly on scene-linear data. Pick low-key (crush shadows) *or* high-key (let highlights go), not both. Teal-shadow / warm-highlight split-toning is common and easy to overdo.
4. **Glare** only around genuinely bright sources (bulbs, sun glints, specular hits). Fog Glow with a high threshold, mixed low. Streaks only for a lens/filter story. Ghosts barely there.
5. **Lens artifacts** via Lens Distortion: Dispersion **0.004–0.02** (0.1 is far too much); Distortion very low, a bit more only on wide lenses; enable Fit to crop the black corners. Vignette: a blurred ellipse mask, subtle. Decide from the implied camera: phone, vintage or documentary = some artifacts; professional corrected-lens look = almost none.
6. **Soften**: a tiny blur (≈1–2 px Gaussian at 1080p, or Filter → Soften mixed 0.05–0.2) to remove "3D sharpness". If you need sharpening instead, a high-pass built from Blur + Subtract beats the built-in Sharpen filters.
7. **Grain last**, on top of the denoised image. A real film-grain scan overlaid (Non-Color) is best. Match grain size to the implied camera and resolution. Three kinds of noise exist and look different: sensor noise (coloured, pixel-sized, worse in shadows), film grain (mostly grey, variable size), and render noise (neither, never acceptable as "grain").

Halation (red bleed around highlights, a film trait): isolate brights, tint red, blur slightly, add back so faint you barely see it.

## 2. Atmosphere in post

- **Mist pass** for aerial perspective outdoors: World → Mist Pass, start ~5 m, depth ~80 m for a street, more for landscapes. Mix toward a sky-tinted colour through a ColorRamp.
- **Faked god rays**: Mist or a bright-isolated pass → Sunbeams filter with the source at the window/sun → mix back at only ~0.05–0.1. No volume render cost.
- Boost real volumetrics without re-rendering by screening the Volume Direct/Indirect passes over the beauty.

## 3. When to go further

- **Multi-pass pipelines** (diffuse/glossy/volume recombined, per-light Light Groups, Cryptomatte for isolation) let you fix one element without re-rendering. If you don't know why you need it, you don't; grade the beauty pass.
- **Finishing outside Blender** (Resolve, Photoshop) means a lossy round-trip unless you export EXR. Blender's compositor stays 32-bit; do grading there for stills unless raster tools are needed.
- **AI detail passes** (img2img at low strength) on hero stills can add micro-texture but drift geometry, wreck text and flicker across frames. A taste call, never a default; tell the user if you suggest it.

## 4. Snippet: a version-safe base compositor

Builds: Render Layers → Denoise (with passes) → Lens Distortion (tiny dispersion) → output. Grain and grading are left for the user's taste or added after review. Blender 5.0 moved the compositor to a node group (`scene.compositing_node_group`) and replaced the Composite node with a Group Output; the code handles both and prints what it built. Verify node and socket names with `print([s.name for s in node.inputs])` if anything errors.

```python
import bpy
sc = bpy.context.scene
vl = bpy.context.view_layer
try: vl.cycles.denoising_store_passes = True
except AttributeError: pass

if hasattr(sc, "compositing_node_group"):          # Blender 5.0+
    tree = sc.compositing_node_group or bpy.data.node_groups.new("Post_Base", "CompositorNodeTree")
    sc.compositing_node_group = tree
    if not any(s.name == "Image" for s in tree.interface.items_tree if getattr(s, "in_out", "") == 'OUTPUT'):
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    out = tree.nodes.get("Group Output") or tree.nodes.new("NodeGroupOutput")
else:                                               # 2.8 – 4.x
    sc.use_nodes = True
    tree = sc.node_tree
    out = next((n for n in tree.nodes if n.type == 'COMPOSITE'), None) or tree.nodes.new("CompositorNodeComposite")

nodes, links = tree.nodes, tree.links
rl = next((n for n in nodes if n.type == 'R_LAYERS'), None) or nodes.new("CompositorNodeRLayers")
dn = nodes.new("CompositorNodeDenoise")
ld = nodes.new("CompositorNodeLensdist")

links.new(rl.outputs["Image"], dn.inputs["Image"])
for src, dst in (("Denoising Normal", "Normal"), ("Denoising Albedo", "Albedo")):
    if src in rl.outputs and dst in dn.inputs:
        links.new(rl.outputs[src], dn.inputs[dst])
links.new(dn.outputs["Image"], ld.inputs["Image"])
for name, val in (("Dispersion", 0.008), ("Distortion", 0.0)):
    if name in ld.inputs: ld.inputs[name].default_value = val
for attr in ("use_fit",):
    if hasattr(ld, attr): setattr(ld, attr, True)
links.new(ld.outputs["Image"], out.inputs[0])

rl.location, dn.location, ld.location, out.location = (-600, 0), (-300, 0), (0, 0), (300, 0)
print("Compositor:", tree.name, [n.name for n in nodes])
```

When using compositor denoising, turn off the render-level denoiser (`sc.cycles.use_denoising = False`) so you don't denoise twice.
