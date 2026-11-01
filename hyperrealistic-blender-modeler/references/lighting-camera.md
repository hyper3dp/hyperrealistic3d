# Lighting, Camera and Colour Management

Practitioner rules with working values. Values marked "start" are where to begin; judge the result on screen (False Color for exposure).

## Contents
1. Lighting
2. Camera and optics
3. Colour management and render settings
4. Snippets

## 1. Lighting

**Defaults**
- **HDRI first.** One HDRI gives light, colour and accurate reflections together; no hand-built rig matches sky, cloud and bounce. Rotate it so the key direction flatters the subject. Set World → Settings → Sampling → Map Resolution to ~2048 to reduce hot-spot noise from small suns.
- **HDRI reads flat?** After the Environment Texture, split it with two Math nodes: *Multiply* (or Power) boosts the bright regions into a sharper directional key; *Add* puts back soft ambient. Restores contrast without one flat exposure value.
- **Nishita sky** when you need a sun angle no stock HDRI has. Strength usually far below 1.0 (start ~0.1–0.3 under AgX). Keep sun size near the real 0.53°; bigger softens shadows unrealistically.
- **Build from black.** World strength 0, all lights off, then add one source at a time and tune it alone. Keep alternative rigs in hidden collections for A/B.
- **Kelvin for natural sources** via a Blackbody node: candle ~1500 K, tungsten 2000–2700 K, warm interior ~3000–4000 K, daylight 5500–6500 K, shade/overcast 6500–8000 K. Use plain RGB only for non-natural sources (neon, signage, sci-fi).
- **Shape shadows, never eliminate them.** Piling on fill is a beginner tell. Never light from the camera axis: the shadows fall out of view and the image goes flat. There is no fixed fill ratio; judge by eye.
- **Size = softness = visible detail.** Large sources hide pores and scratches; small ones reveal them. A radius/size of 0 gives razor-sharp CG shadows; always give lights some size. Moving a light closer softens it like enlarging it.
- **Inverse-square falloff.** Doubling distance gives a quarter of the light. Move a light closer to create local contrast that guides the eye, instead of adding more lights.
- **Gobos / cookies.** A plane in front of the key with a noise or cutout image driving alpha (via Mix with Transparent BSDF) breaks flat light into real, patchy light: window shafts, leaf dapple, cloud shadows on terrain. Parent the gobo to the light. Soften with light size or gobo distance.
- **Let one end clip.** A single exposure can't hold both a bright window and a dark corner. Choosing what clips is part of the photographic look.
- **Practicals.** Model the real bulb (frosted glass, roughness ~0.02) inside a fixture. A bare emissive blob reads fake. Use IES profiles (IES Texture → Emission strength) for architectural fixtures.

**Interiors**
- Light Portals: an Area light with *Portal* enabled, fitted to each window or door opening, cleans HDRI noise in interiors far better than more samples.
- Rotate a low-sun HDRI until the beam hits the window. It's fine to delete off-camera walls that block light, rather than inventing interior fills.
- Helper lights are allowed only where a real reflector or bounce could plausibly be, colour-matched and subtle. For directional control without fake light, use a **black flag**: a large black plane just out of frame that absorbs light from one side.

**Volumetrics / god rays**
- Use a **cube with a Volume material** around the area. A World-tab volume is not lit by the HDRI or a sun lamp, so god rays silently vanish.
- Default density is far too thick. Start **0.02 for ambient haze, 0.2–0.3 for visible shafts**, then lower.
- Visible shafts need a hard-edged shadow caster (window frame, gobo) **and** a small but non-zero light size.
- Anisotropy 0 = even scatter; ~0.3–0.7 forward-scatter for golden-hour or fire glow; near 0.95 the shafts dissolve into glow.
- Height fog: drive density with a Gradient texture rather than noise for a clean falloff.
- Cheap fog: billboarded image planes (Emission/Transparent mix with a noise mask faded at the edges). Far cheaper than volumes for local wisps.

**Product / studio**
- A true softbox: an Area light with a Translucent-BSDF plane in front softens both diffuse light *and* reflections (enlarging the light only softens diffuse).
- Commercial-style controlled reflections (disable a light's glossy visibility, gradient emissive cards) are a deliberate break from physics. Fine for product shots; use with restraint.

## 2. Camera and optics

- **Focal length on purpose:** ~35 mm ≈ the human eye; 50 mm neutral; 80–100 mm products and furniture (less distortion, pulled back); 85–135 mm portraits; 24 mm deep-focus wides; 20 mm first-person walkthroughs; ~30 mm landscape establishing shots.
- **DOF always on**, focused with an Empty at the subject, never a typed distance. f-stop start values: **f/5.6 general, f/2.8–5.6 portrait/product, f/8–11 street/interior, f/16–22 landscape.**
- **DOF is a scale cue.** Heavy background blur on a building or vehicle makes it look like a miniature. If the scene is at real scale with a real sensor (36 mm) and f-stop, the physics come out right without hand-tuning.
- **Aperture blades 6–8**, with slight rotation. Five blades give visible pentagons. Anamorphic look: camera bokeh ratio 2.
- **Lock camera and composition before detailing.** Try 4–7 candidate angles at blockout. Detail outside the frame, or too small or blurred to read, is wasted.
- Rule of thirds, subject off-centre; a deliberate colour scheme (complementary is most common; analogous reads natural).
- Background plates and backdrops must extend past every frame edge; a visible edge reads as a flat card.
- **Matching a real photo:** fSpy for a still (validate by snapping a plane to the photo's floor). Light-match with a plain sphere on a shadow catcher first, rotating the HDRI until highlights and shadow direction match the plate.

## 3. Colour management and render settings

- **AgX (4.0+) or Filmic (3.x), never Standard.** Standard clips at ~8 stops and pushes you into fake fill lights. AgX rolls highlights to white like film; its slightly desaturated first look is correct.
- **Look:** Medium High Contrast / High Contrast / AgX Punchy. "None" looks washed out. Very High is usually too much.
- **White balance** (4.3+): Color Management → White Balance sets temperature and tint at view level, like a camera's WB.
- **Check exposure with False Color**: temporarily set the view transform to *False Color*. Grey ≈ correct, cyan ≈ 1 stop under, green ≈ 1 stop over, red/white = clipping. Put it back after checking.
- **Bounces** (black patches in glass or liquid are ray starvation, not a mystery): glossy 20–40 for bumpy glass; transmission 12–32 for stacked glass (much more for lens stacks); volume ~12 for coloured liquids (default 0 leaves them grey); transparent ~64–128 for overlapping fog cards or leaves with alpha.
- **Escape hatch for deep glass:** Light Path → Ray Depth > ~10 → switch the glass shader to Transparent. Kills black holes cheaply.
- **Fireflies:** Filter Glossy 0.5–1.0; Clamp Indirect ~10 (lower only if fireflies persist; very low values darken bounce light).
- **Samples:** adaptive sampling; ~512–1024 for stills, 64–128 + denoise for animation. GPU with OptiX on RTX cards.
- **Denoise with data passes** (Normal + Albedo) or the compositor Denoise node; see `post-compositing.md`. OIDN on GPU (4.1+) with quality High.
- **Light Groups** (3.2+): each light to its own pass, so you can re-balance in the compositor without re-rendering.
- **Output:** OpenEXR Multilayer, half float, DWAA for anything you'll grade; PNG only for previews.
- **Caustics:** Shadow Caustics (MNEE, 3.2+) via flags on light, caster and receiver for glass-on-table or water patterns.
- **EEVEE:** fine for previews. For finals, EEVEE Next (4.2+) has real GI; Cycles still wins for SSS/skin and anything refractive.

## 4. Snippets

```python
import bpy, math

def blackbody_light(name, kelvin, energy, size=0.5, kind='AREA', loc=(0, 0, 2)):
    """Light coloured by a Blackbody node. Falls back to the light's own temperature setting on 4.5+ if present."""
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if hasattr(ld, "size"): ld.size = size
    if hasattr(ld, "shadow_soft_size"): ld.shadow_soft_size = max(size * 0.5, 0.01)
    if hasattr(ld, "use_temperature"):          # Blender 4.5+
        ld.use_temperature = True; ld.temperature = kelvin
    else:
        ld.use_nodes = True
        nt = ld.node_tree
        em = next(n for n in nt.nodes if n.type == 'EMISSION')
        bb = nt.nodes.new("ShaderNodeBlackbody"); bb.inputs["Temperature"].default_value = kelvin
        nt.links.new(bb.outputs["Color"], em.inputs["Color"])
    ob = bpy.data.objects.new(name, ld); ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob

def physical_camera(cam_ob, focus_target, lens=50, fstop=5.6, blades=7):
    c = cam_ob.data
    c.lens = lens; c.sensor_width = 36
    c.dof.use_dof = True; c.dof.focus_object = focus_target
    c.dof.aperture_fstop = fstop; c.dof.aperture_blades = blades
    c.dof.aperture_rotation = math.radians(10)
    print("Camera:", cam_ob.name, lens, "mm f/", fstop, "focus", focus_target.name)

def bounces_for_glass(sc, glossy=24, transmission=24, volume=12, transparent=64):
    cy = sc.cycles
    cy.glossy_bounces = glossy; cy.transmission_bounces = transmission
    cy.volume_bounces = volume; cy.transparent_max_bounces = transparent
    cy.max_bounces = max(cy.max_bounces, glossy, transmission)
    cy.blur_glossy = 0.75   # Filter Glossy
    print("Bounces set:", cy.max_bounces, glossy, transmission, volume, transparent)

# False Color exposure check: set, screenshot/render, then restore
def false_color(sc, on=True, _saved={}):
    vs = sc.view_settings
    if on:
        _saved["vt"], _saved["look"] = vs.view_transform, vs.look
        vs.view_transform = 'False Color'
    else:
        vs.view_transform = _saved.get("vt", 'AgX')
        try: vs.look = _saved.get("look", 'None')
        except TypeError: pass
    print("View transform:", vs.view_transform)
```

Light property names move between versions (`use_temperature` arrived in 4.5). Use `hasattr` checks as above and print what was set.
