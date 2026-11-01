"""Scene QA audit for photoreal Blender work.

Paste the whole file into Blender MCP's execute_blender_code. It changes nothing;
it prints a report of likely problems. Treat findings as leads to check in a
screenshot, not as certainties (e.g. some intersections are intentional).
"""
import bpy
import bmesh
import os
import re
from mathutils import Vector

DEFAULT_NAME = re.compile(r"^(Cube|Sphere|Cylinder|Cone|Plane|Torus|Circle|Icosphere|Suzanne|Mesh|Object|Material|Light|Camera|Empty)(\.\d+)?$")
issues = []
info = []


def warn(msg):
    issues.append(msg)


def world_bbox(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def overlap(a, b, tol=1e-4):
    (alo, ahi), (blo, bhi) = a, b
    return all(alo[i] < bhi[i] - tol and blo[i] < ahi[i] - tol for i in range(3))


def root(obj):
    while obj.parent:
        obj = obj.parent
    return obj


scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render and o.visible_get()]

# --- scene-level checks ---------------------------------------------------
info.append(f"Blender {bpy.app.version_string} | engine {scene.render.engine} | "
            f"view transform {scene.view_settings.view_transform} | look {scene.view_settings.look}")
if scene.render.engine != 'CYCLES':
    warn("Render engine is not Cycles (fine for previews, use Cycles for final photoreal output)")
if scene.view_settings.view_transform == 'Standard':
    warn("View transform is 'Standard' - switch to AgX/Filmic for photoreal tonemapping")
if scene.camera is None:
    warn("No active scene camera")
lights = [o for o in scene.objects if o.type == 'LIGHT' and not o.hide_render]
world_lit = bool(scene.world and scene.world.use_nodes and any(
    n.type in {'TEX_ENVIRONMENT', 'TEX_SKY'} for n in scene.world.node_tree.nodes))
info.append(f"{len(meshes)} renderable meshes, {len(lights)} lights, world HDRI/sky: {world_lit}")
if not lights and not world_lit:
    warn("No lights and no HDRI/sky in the world - scene relies on flat world color only")
if abs(scene.unit_settings.scale_length - 1.0) > 1e-6:
    warn(f"Unit scale is {scene.unit_settings.scale_length}, expected 1.0 (metres)")
if scene.render.engine == 'CYCLES' and scene.cycles.samples < 64:
    info.append(f"Cycles samples {scene.cycles.samples} (preview level)")

# --- images ---------------------------------------------------------------
for img in bpy.data.images:
    if img.source != 'FILE' or img.users == 0:
        continue
    path = bpy.path.abspath(img.filepath)
    if not img.packed_file and not os.path.exists(path):
        warn(f"Image '{img.name}' missing on disk: {path} (renders pink)")

# --- per-material checks ---------------------------------------------------
NONCOLOR_HINTS = ("rough", "normal", "nor_", "_nrm", "disp", "height", "metal", "spec", "_ao", "bump", "gloss")
for mat in bpy.data.materials:
    if mat.users == 0 or not mat.use_nodes:
        continue
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image:
            lname = n.image.name.lower()
            cs = n.image.colorspace_settings.name
            if any(h in lname for h in NONCOLOR_HINTS) and cs not in {'Non-Color', 'Linear', 'Raw', 'Linear Rec.709'}:
                warn(f"Material '{mat.name}': image '{n.image.name}' looks like data but is {cs} (should be Non-Color)")
        if n.type == 'BSDF_PRINCIPLED':
            r = n.inputs.get("Roughness")
            if r is not None and not r.is_linked:
                info.append(f"Material '{mat.name}': flat roughness {r.default_value:.2f} (no variation)")
            m = n.inputs.get("Metallic")
            if m is not None and not m.is_linked and 0.05 < m.default_value < 0.95:
                warn(f"Material '{mat.name}': metallic {m.default_value:.2f} - usually 0 or 1 unless masked")
            bc = n.inputs.get("Base Color")
            if bc is not None and not bc.is_linked:
                v = max(bc.default_value[:3])
                if v > 0.95 or v < 0.01:
                    info.append(f"Material '{mat.name}': base color value {v:.2f} is outside the usual 0.02-0.9 albedo range")
    if DEFAULT_NAME.match(mat.name):
        info.append(f"Material has a default name: '{mat.name}'")

# --- per-object checks ------------------------------------------------------
bboxes = {}
min_z_floor = None
for obj in meshes:
    name = obj.name
    if DEFAULT_NAME.match(name):
        warn(f"Object '{name}' has a default name")
    s = obj.scale
    if any(c < 0 for c in s):
        warn(f"'{name}' has negative scale {tuple(round(c, 3) for c in s)} - can flip normals")
    elif any(abs(c - 1) > 1e-3 for c in s) and any(m.type in {'BEVEL', 'SOLIDIFY'} for m in obj.modifiers):
        warn(f"'{name}' has unapplied scale {tuple(round(c, 3) for c in s)} with bevel/solidify - widths will be distorted")
    if not obj.material_slots or all(sl.material is None for sl in obj.material_slots):
        warn(f"'{name}' has no material")
    uses_image = any(sl.material and sl.material.use_nodes and any(
        n.type == 'TEX_IMAGE' for n in sl.material.node_tree.nodes) for sl in obj.material_slots)
    if uses_image and not obj.data.uv_layers:
        warn(f"'{name}' uses image textures but has no UV map")

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    has_subsurf = any(m.type == 'SUBSURF' for m in obj.modifiers)
    if ngons and has_subsurf:
        warn(f"'{name}': {ngons} n-gons under a Subdivision modifier - may pinch")
    if loose:
        warn(f"'{name}': {loose} loose vertices")
    if degenerate:
        warn(f"'{name}': {degenerate} zero-area faces (shading artifacts)")
    if bm.faces and non_manifold == 0:
        vol = bm.calc_volume(signed=True)
        if vol < 0:
            warn(f"'{name}': closed mesh with inward-facing normals (recalculate outside)")
    bm.free()

    lo, hi = world_bbox(obj, depsgraph)
    bboxes[obj] = (lo, hi)
    dims = hi - lo
    if max(dims) > 1000 or (max(dims) < 1e-3 and len(obj.data.vertices) > 0):
        warn(f"'{name}': size {tuple(round(d, 4) for d in dims)} m looks implausible - check real-world scale")
    lname = name.lower()
    if any(k in lname for k in ("floor", "ground", "backdrop", "sweep", "table")):
        min_z_floor = hi.z if min_z_floor is None else max(min_z_floor, hi.z)

# --- floating / sinking against the floor -------------------------------------
if min_z_floor is not None:
    for obj, (lo, hi) in bboxes.items():
        lname = obj.name.lower()
        if any(k in lname for k in ("floor", "ground", "backdrop", "sweep", "table", "wall")):
            continue
        if obj.parent is None and lo.z - min_z_floor > 0.002:
            info.append(f"'{obj.name}' bottom is {lo.z - min_z_floor:.3f} m above the floor/top surface - floating?")
        if lo.z < min_z_floor - 0.002 and hi.z > min_z_floor:
            info.append(f"'{obj.name}' extends {min_z_floor - lo.z:.3f} m below the floor/top surface - sinking?")

# --- possible unintended intersections between separate assemblies -------------
objs = list(bboxes)
pairs = []
for i, a in enumerate(objs):
    for b in objs[i + 1:]:
        if root(a) is root(b):
            continue
        names = (a.name.lower(), b.name.lower())
        if any(k in n for n in names for k in ("floor", "ground", "backdrop", "sweep", "wall")):
            continue
        if overlap(bboxes[a], bboxes[b]):
            pairs.append(f"{a.name} <-> {b.name}")
if pairs:
    info.append("Bounding boxes overlap between separate assemblies (check for clipping): " + "; ".join(pairs[:15])
                + (" ..." if len(pairs) > 15 else ""))

# --- report --------------------------------------------------------------------
print("=== SCENE AUDIT ===")
for line in info:
    print("  i ", line)
print(f"--- {len(issues)} issue(s) ---")
for line in issues:
    print("  ! ", line)
if not issues:
    print("  No hard issues found. Still inspect screenshots from several angles and a test render.")
