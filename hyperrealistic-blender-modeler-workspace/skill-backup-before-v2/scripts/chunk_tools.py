"""Helpers for building a scene in chunks (see references/chunked-workflow.md).

Paste this file into execute_blender_code once per call that needs it (or stash the
functions in bpy.app.driver_namespace). Nothing runs on import except definitions.

Chunk = one collection named CHUNK_<Name> plus an entry in a JSON manifest that
records its bounds, status and files. Each chunk can be isolated, given its own
preview camera, rendered alone, saved to its own .blend, and later linked or
appended back into the master scene.
"""
import bpy
import json
import os
from mathutils import Vector

STATUSES = ("planned", "blockout", "modeled", "shaded", "approved")


# --- manifest -----------------------------------------------------------------
def manifest_path(project_dir):
    return os.path.join(project_dir, "chunks_manifest.json")


def load_manifest(project_dir):
    p = manifest_path(project_dir)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"project_dir": project_dir, "chunks": {}}


def save_manifest(m):
    os.makedirs(m["project_dir"], exist_ok=True)
    with open(manifest_path(m["project_dir"]), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    return manifest_path(m["project_dir"])


def plan_chunk(m, name, bounds_min, bounds_max, notes="", depends_on=()):
    """Register a chunk's footprint (world-space metres) before building it."""
    m["chunks"][name] = {
        "collection": f"CHUNK_{name}",
        "bounds_min": list(bounds_min), "bounds_max": list(bounds_max),
        "status": "planned", "notes": notes, "depends_on": list(depends_on),
        "renders": [], "blend": None,
    }
    return m["chunks"][name]


def set_status(m, name, status):
    assert status in STATUSES, status
    m["chunks"][name]["status"] = status


# --- collections ----------------------------------------------------------------
def chunk_collection(name, parent=None):
    cname = f"CHUNK_{name}"
    col = bpy.data.collections.get(cname)
    if col is None:
        col = bpy.data.collections.new(cname)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def _layer_col(layer_coll, name):
    if layer_coll.collection.name == name:
        return layer_coll
    for child in layer_coll.children:
        found = _layer_col(child, name)
        if found:
            return found
    return None


def isolate_chunks(names, keep=("Lights", "Cameras", "World_Helpers")):
    """Exclude every top-level CHUNK_ collection except `names` from the active view layer.
    Collections in `keep` stay as they are. Returns the previous exclude state for restore()."""
    vl = bpy.context.view_layer
    state = {}
    wanted = {f"CHUNK_{n}" for n in names}
    for lc in vl.layer_collection.children:
        cname = lc.collection.name
        if cname.startswith("CHUNK_"):
            state[cname] = lc.exclude
            lc.exclude = cname not in wanted
    return state


def restore(state):
    vl = bpy.context.view_layer
    for cname, excl in state.items():
        lc = _layer_col(vl.layer_collection, cname)
        if lc:
            lc.exclude = excl


def chunk_bounds(name):
    """World-space bounds of everything renderable in the chunk (after modifiers)."""
    col = bpy.data.collections[f"CHUNK_{name}"]
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in col.all_objects:
        if o.type in {'MESH', 'CURVE', 'FONT', 'EMPTY'} and not o.hide_render:
            ev = o.evaluated_get(dg)
            if o.type == 'EMPTY' and o.instance_type != 'COLLECTION':
                continue
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def chunk_camera(name, lens=35, direction=(1.0, -1.0, 0.6)):
    """Create/refresh CAM_Chunk_<name>, framing the chunk's bounds from `direction`."""
    b = chunk_bounds(name)
    if b is None:
        raise ValueError(f"chunk {name} has nothing renderable")
    lo, hi = b
    centre = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.05)
    cam_name = f"CAM_Chunk_{name}"
    cam_obj = bpy.data.objects.get(cam_name)
    if cam_obj is None:
        cam_obj = bpy.data.objects.new(cam_name, bpy.data.cameras.new(cam_name))
        cams = bpy.data.collections.get("Cameras") or bpy.data.collections.new("Cameras")
        if cams.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(cams)
        cams.objects.link(cam_obj)
    cam_obj.data.lens = lens
    cam_obj.data.clip_end = max(1000.0, radius * 20)
    d = Vector(direction).normalized()
    # distance so the bounding sphere fits the horizontal FOV
    import math
    fov = 2 * math.atan(cam_obj.data.sensor_width / (2 * lens))
    dist = radius / math.sin(fov / 2) * 1.1
    cam_obj.location = centre + d * dist
    cam_obj.rotation_euler = (centre - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    return cam_obj


def render_chunk(m, name, out_dir=None, percent=50, samples=64, camera=None, tag="preview"):
    """Render one chunk in isolation to <project>/chunks/<name>/<tag>_NN.png. Restores the
    scene camera, samples, resolution and view-layer state afterwards."""
    sc = bpy.context.scene
    out_dir = out_dir or os.path.join(m["project_dir"], "chunks", name)
    os.makedirs(out_dir, exist_ok=True)
    prev = (sc.camera, sc.render.resolution_percentage, getattr(sc.cycles, "samples", None), sc.render.filepath)
    state = isolate_chunks([name])
    try:
        sc.camera = camera or chunk_camera(name)
        sc.render.resolution_percentage = percent
        if sc.render.engine == 'CYCLES':
            sc.cycles.samples = samples
        n = len(m["chunks"][name]["renders"]) + 1
        path = os.path.join(out_dir, f"{tag}_{n:02d}.png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
    finally:
        restore(state)
        sc.camera, sc.render.resolution_percentage = prev[0], prev[1]
        if prev[2] is not None:
            sc.cycles.samples = prev[2]
        sc.render.filepath = prev[3]
    ok = os.path.exists(path)
    if ok:
        m["chunks"][name]["renders"].append(path)
    return {"path": path, "exists": ok}


# --- per-chunk files ------------------------------------------------------------
def save_chunk_file(m, name):
    """Write the chunk's collection (objects, meshes, materials, images it uses) to
    <project>/chunks/<name>/<name>.blend without touching the open file."""
    col = bpy.data.collections[f"CHUNK_{name}"]
    out_dir = os.path.join(m["project_dir"], "chunks", name)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.blend")
    bpy.data.libraries.write(path, {col}, fake_user=True, compress=True)
    m["chunks"][name]["blend"] = path
    return {"path": path, "exists": os.path.exists(path)}


def remove_chunk(name):
    """Delete CHUNK_<name> and the objects only it uses (call before re-appending a chunk,
    otherwise the old objects linger and the new ones arrive as Name.001)."""
    col = bpy.data.collections.get(f"CHUNK_{name}")
    if col is None:
        return 0
    objs = [o for o in col.all_objects if all(c == col or c.name.startswith(col.name) for c in o.users_collection)]
    for child in list(col.children_recursive):
        bpy.data.collections.remove(child)
    for o in objs:
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(col)
    return len(objs)


def bring_in_chunk(path, name, link=False, parent=None):
    """Append (default) or link CHUNK_<name> from a chunk .blend into the open scene.
    If the chunk is already in the scene, call remove_chunk(name) first."""
    cname = f"CHUNK_{name}"
    with bpy.data.libraries.load(path, link=link) as (src, dst):
        dst.collections = [c for c in src.collections if c == cname]
    col = dst.collections[0] if dst.collections else None
    if col is None:
        raise ValueError(f"{cname} not found in {path}")
    target = parent or bpy.context.scene.collection
    if link:
        inst = bpy.data.objects.new(cname, None)
        inst.instance_type = 'COLLECTION'
        inst.instance_collection = col
        target.objects.link(inst)
        return inst
    if col.name not in target.children:
        target.children.link(col)
    return col


def dedupe_materials():
    """Remap duplicate materials such as Brick.001/Brick.002 onto Brick (common after
    importing the same asset several times) and report what was merged."""
    merged = {}
    for mat in list(bpy.data.materials):
        base, _, suffix = mat.name.rpartition(".")
        if base and suffix.isdigit() and base in bpy.data.materials:
            mat.user_remap(bpy.data.materials[base])
            merged[mat.name] = base
            bpy.data.materials.remove(mat)
    return merged


def checkpoint(m, label="checkpoint"):
    """Save the master file plus manifest so a crash costs at most one chunk of work."""
    if not bpy.data.filepath:
        path = os.path.join(m["project_dir"], "master.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
    else:
        bpy.ops.wm.save_mainfile()
    save_manifest(m)
    return {"blend": bpy.data.filepath, "manifest": manifest_path(m["project_dir"]), "label": label}
