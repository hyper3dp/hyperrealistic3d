# Run: blender --background file.blend --python blend_facts.py -- out.json
import bpy, re, sys, json
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
DEF = re.compile(r"^(Cube|Sphere|Cylinder|Cone|Plane|Torus|Circle|Icosphere|Suzanne|Mesh|Object|Text|Curve|BezierCurve|NurbsPath|Empty|Light|Camera|Area|Point|Sun|Spot)(\.\d+)?$")
dg = bpy.context.evaluated_depsgraph_get()
def dims(o):
    ev = o.evaluated_get(dg); pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    return [round(hi[i] - lo[i], 4) for i in range(3)], round(lo[2], 4)
meshes = [o for o in sc.objects if o.type in {'MESH', 'CURVE', 'FONT'} and not o.hide_render]
mats = {}
for m in bpy.data.materials:
    if not m.users or not m.use_nodes: continue
    b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
    if not b: mats[m.name] = {"principled": False, "nodes": len(m.node_tree.nodes)}; continue
    b = b[0]
    def v(s):
        i = b.inputs.get(s)
        if i is None: return None
        if i.is_linked: return "linked"
        d = i.default_value
        return [round(x, 3) for x in d][:3] if hasattr(d, "__len__") else round(d, 3)
    mats[m.name] = {"base": v("Base Color"), "metal": v("Metallic"), "rough": v("Roughness"), "coat": v("Coat Weight"),
                    "trans": v("Transmission Weight"), "nodes": len(m.node_tree.nodes),
                    "types": sorted({n.type for n in m.node_tree.nodes})}
cam = sc.camera; camd = None
if cam:
    e = cam.matrix_world.to_euler()
    camd = {"name": cam.name, "lens": cam.data.lens, "dof": cam.data.dof.use_dof, "fstop": round(cam.data.dof.aperture_fstop, 2),
            "z": round(cam.matrix_world.translation.z, 3), "rot_deg": [round(r * 57.2958, 1) for r in e], "shift_y": cam.data.shift_y}
lights = [(o.name, o.data.type, round(o.data.energy, 2)) for o in sc.objects if o.type == 'LIGHT' and not o.hide_render]
objs = []
for o in meshes:
    d, zmin = dims(o)
    objs.append({"n": o.name, "dim": d, "zmin": zmin, "mods": [m.type for m in o.modifiers],
                 "mats": [s.material.name for s in o.material_slots if s.material], "col": [c.name for c in o.users_collection]})
res = {"engine": sc.render.engine, "vt": sc.view_settings.view_transform, "look": sc.view_settings.look,
       "res": [sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage],
       "samples": getattr(sc.cycles, "samples", None), "n_obj": len(sc.objects),
       "nomat": [o.name for o in meshes if not any(s.material for s in o.material_slots)],
       "defaults": [o.name for o in sc.objects if DEF.match(o.name)],
       "n_bevelled": sum(1 for o in meshes if any(m.type == 'BEVEL' for m in o.modifiers) or (o.type == 'CURVE' and o.data.bevel_depth > 0)),
       "n_mesh": len(meshes), "collections": {c.name: len(c.all_objects) for c in bpy.data.collections},
       "materials": mats, "camera": camd, "n_lights": len(lights), "lights": lights[:20],
       "instances": sum(1 for i in dg.object_instances if i.is_instance),
       "shared_meshes": sum(1 for me in bpy.data.meshes if me.users > 1),
       "world": sorted({n.type for n in sc.world.node_tree.nodes}) if sc.world and sc.world.use_nodes else None,
       "objects": objs[:150], "n_objects_listed": min(len(objs), 150)}
json.dump(res, open(out, "w"), indent=1)
