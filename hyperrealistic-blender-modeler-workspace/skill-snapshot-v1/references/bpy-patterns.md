# bpy Patterns for Blender MCP

Working snippets to paste into `execute_blender_code`. They target Blender 3.6–4.x and guard version differences. Each call runs in a fresh-ish context, so re-define helpers you need in that call (or define them once in `bpy.app.driver_namespace` — see the end).

## Contents
1. Collections & naming
2. Primitives without bpy.ops context trouble
3. Modifiers: bevel, subdivision, solidify, weighted normal, boolean
4. Shading smooth (version-safe)
5. Materials: Principled helper and node helper
6. UVs
7. World / HDRI
8. Lights
9. Camera
10. Render & color management
11. Rendering to file, saving the .blend
12. Running bpy.ops with a context override
13. Sharing helpers across calls

## 1. Collections & naming

```python
import bpy

def get_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col

def move_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
```

## 2. Primitives

`bpy.ops.mesh.primitive_*` works in most MCP setups; afterwards grab `bpy.context.active_object` and rename immediately. For custom shapes use bmesh:

```python
import bpy, bmesh

def mesh_object(name, bm, col):
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me)
    col.objects.link(obj)
    return obj

bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=0.08, radius2=0.08, depth=0.2)
body = mesh_object("Mug_Body", bm, get_collection("Model_Mug"))
```

Remember: `create_cone` / `create_cube` sizes are in metres; `create_cube(size=…)` is edge length.

## 3. Modifiers

```python
from math import radians

def add_bevel(obj, width=0.002, segments=3, angle=30):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = width; m.segments = segments
    m.limit_method = 'ANGLE'; m.angle_limit = radians(angle)
    m.use_clamp_overlap = True
    try: m.harden_normals = True
    except AttributeError: pass
    return m

def add_subsurf(obj, view=1, render=2):
    m = obj.modifiers.new("Subdivision", 'SUBSURF')
    m.levels = view; m.render_levels = render
    return m

def add_solidify(obj, thickness=0.003):
    m = obj.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = thickness; m.offset = -1
    return m

def add_weighted_normal(obj):
    m = obj.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
    m.keep_sharp = True
    return m

def add_boolean(obj, cutter, op='DIFFERENCE'):
    m = obj.modifiers.new("Bool_" + cutter.name, 'BOOLEAN')
    m.object = cutter; m.operation = op; m.solver = 'EXACT'
    cutter.display_type = 'WIRE'; cutter.hide_render = True
    return m
```

Order: Boolean → Bevel → Subdivision → WeightedNormal (or Solidify → Bevel for shells).

## 4. Shade smooth (version-safe)

```python
def shade_smooth(obj, auto_angle=30):
    me = obj.data
    for p in me.polygons:
        p.use_smooth = True
    if hasattr(me, "use_auto_smooth"):          # Blender < 4.1
        me.use_auto_smooth = True
        me.auto_smooth_angle = radians(auto_angle)
    # 4.1+: rely on the Bevel harden_normals / WeightedNormal modifier, or mark sharp edges.
```

## 5. Materials

```python
def principled_material(name, **inputs):
    """principled_material("MAT_Steel", base_color=(0.56,0.57,0.58,1), metallic=1, roughness=0.3)"""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    # Map friendly names to candidate socket names across versions
    aliases = {
        "base_color": ["Base Color"], "metallic": ["Metallic"], "roughness": ["Roughness"],
        "ior": ["IOR"], "alpha": ["Alpha"],
        "transmission": ["Transmission Weight", "Transmission"],
        "subsurface": ["Subsurface Weight", "Subsurface"],
        "subsurface_radius": ["Subsurface Radius"],
        "coat": ["Coat Weight", "Clearcoat"], "coat_roughness": ["Coat Roughness", "Clearcoat Roughness"],
        "sheen": ["Sheen Weight", "Sheen"], "specular": ["Specular IOR Level", "Specular"],
        "anisotropic": ["Anisotropic"], "emission_color": ["Emission Color", "Emission"],
        "emission_strength": ["Emission Strength"],
    }
    for key, val in inputs.items():
        for sock in aliases.get(key, [key]):
            if sock in bsdf.inputs:
                bsdf.inputs[sock].default_value = val
                break
        else:
            print(f"[warn] {name}: no socket for {key}")
    return mat

def assign(obj, mat):
    if obj.data.materials: obj.data.materials[0] = mat
    else: obj.data.materials.append(mat)
```

Building node graphs:

```python
def node(nt, type_, loc=(0, 0), **props):
    n = nt.nodes.new(type_); n.location = loc
    for k, v in props.items():
        if k in getattr(n, "inputs", {}) and not hasattr(n, k):
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n

# Example: roughness variation
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
noise = node(nt, "ShaderNodeTexNoise", (-600, 0)); noise.inputs["Scale"].default_value = 8
ramp = node(nt, "ShaderNodeValToRGB", (-350, 0))
ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
ramp.color_ramp.elements[1].color = (0.40, 0.40, 0.40, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

# Micro bump
bump = node(nt, "ShaderNodeBump", (-200, -300)); bump.inputs["Strength"].default_value = 0.05
micro = node(nt, "ShaderNodeTexNoise", (-450, -300)); micro.inputs["Scale"].default_value = 600
nt.links.new(micro.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
```

Image textures:

```python
def image_node(nt, path, non_color=False, loc=(-600, 0)):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color: img.colorspace_settings.name = 'Non-Color'
    n = nt.nodes.new("ShaderNodeTexImage"); n.image = img; n.location = loc
    return n
```

Displacement: link Displacement node → Material Output "Displacement", then
```python
try: mat.displacement_method = 'BOTH'          # 4.x
except AttributeError: mat.cycles.displacement_method = 'BOTH'
```

## 6. UVs

```python
def smart_uv(obj, angle=66, margin=0.02):
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects: o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=radians(angle), island_margin=margin)
    bpy.ops.object.mode_set(mode='OBJECT')
```

If `uv.smart_project` errors with a context problem, use the override in §12. For textures without UVs, use Texture Coordinate → Object/Generated with Image Texture projection `'BOX'` and `projection_blend = 0.2`.

## 7. World / HDRI

```python
def world_hdri(path, strength=1.0, rotation_z=0.0):
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapn = nt.nodes.new("ShaderNodeMapping"); mapn.inputs["Rotation"].default_value[2] = rotation_z
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
```

Physical sky fallback: `ShaderNodeTexSky` with `sky_type = 'NISHITA'` (renamed in 4.x+ in some builds — check `sky.bl_rna.properties['sky_type'].enum_items.keys()`), sun_elevation in radians, Background strength ~0.3–1.

## 8. Lights

```python
def area_light(name, loc, rot, size=1.0, size_y=None, power=200, col=None):
    data = bpy.data.lights.new(name, 'AREA'); data.size = size; data.energy = power
    if size_y:
        data.shape = 'RECTANGLE'; data.size_y = size_y
    obj = bpy.data.objects.new(name, data); obj.location = loc; obj.rotation_euler = rot
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj
```

Aim lights at the subject with a Track To constraint (`obj.constraints.new('TRACK_TO')`, `target`, `track_axis='TRACK_NEGATIVE_Z'`, `up_axis='UP_Y'`).

## 9. Camera

```python
def hero_camera(name, loc, target, lens=85, fstop=4.0, col=None):
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36
    cam.dof.use_dof = True; cam.dof.focus_object = target; cam.dof.aperture_fstop = fstop
    obj = bpy.data.objects.new(name, cam); obj.location = loc
    (col or bpy.context.scene.collection).objects.link(obj)
    c = obj.constraints.new('TRACK_TO'); c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    bpy.context.scene.camera = obj
    return obj
```

Use an Empty at the subject's focal point as `target` so you can aim and focus precisely.

## 10. Render & color management

```python
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 256
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except TypeError: pass
sc.cycles.sample_clamp_indirect = 10
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50          # previews; 100 for final

# GPU if available
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dev_type in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            if any(d.type == dev_type for d in prefs.devices):
                for d in prefs.devices: d.use = True
                sc.cycles.device = 'GPU'; break
        except TypeError:
            continue
except Exception as e:
    print("GPU setup skipped:", e)
print("Cycles device:", sc.cycles.device)

vt = sc.view_settings.bl_rna.properties['view_transform'].enum_items.keys()
sc.view_settings.view_transform = 'AgX' if 'AgX' in vt else 'Filmic'
looks = sc.view_settings.bl_rna.properties['look'].enum_items.keys()
for want in ('AgX - Medium High Contrast', 'Medium High Contrast', 'Filmic - Medium High Contrast'):
    if want in looks: sc.view_settings.look = want; break
print("View transform:", sc.view_settings.view_transform, "| look:", sc.view_settings.look)
```

## 11. Rendering to file, saving the .blend

```python
import os
out = os.path.join(os.path.expanduser("~"), "Documents", "BlenderRenders", "mug_hero.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
sc.render.filepath = out
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("Render exists:", os.path.exists(out), out)
```

Long final renders may exceed the MCP call timeout. Render previews at low samples/resolution first; for the final, tell the user if it timed out and offer the settings so they can press F12 themselves.

```python
blend = os.path.join(os.path.expanduser("~"), "Documents", "mug_photoreal.blend")
try: bpy.ops.file.pack_all()
except RuntimeError as e: print("pack_all:", e)
bpy.ops.wm.save_as_mainfile(filepath=blend)
print("Saved:", bpy.data.filepath, os.path.exists(bpy.data.filepath))
```

## 12. Running bpy.ops with a context override

MCP code often runs without a 3D viewport in context. In Blender 3.2+:

```python
def with_view3d(fn):
    win = bpy.context.window_manager.windows[0]
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=win, area=area, region=region):
                return fn()
    return fn()

with_view3d(lambda: bpy.ops.object.transform_apply(location=False, rotation=False, scale=True))
```

## 13. Sharing helpers across calls

Each `execute_blender_code` call is usually a separate `exec`. To avoid re-sending helpers, stash them once:

```python
import bpy
ns = bpy.app.driver_namespace
ns["principled_material"] = principled_material
ns["get_collection"] = get_collection
```
Then in later calls: `principled_material = bpy.app.driver_namespace["principled_material"]`. If a later call raises `KeyError`, the session restarted — re-send the helpers.
