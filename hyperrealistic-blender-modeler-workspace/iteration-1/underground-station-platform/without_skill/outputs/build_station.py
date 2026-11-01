import bpy, bmesh, math, random, os, sys
import numpy as np
from mathutils import Vector, Matrix

OUT = r"C:\Users\Hype\Desktop\hyperrealistic3d\hyperrealistic-blender-modeler-workspace\iteration-1\underground-station-platform\without_skill\outputs"
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = argv[0] if argv else 'test'
random.seed(7)

# ---------------- clear ----------------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
             bpy.data.curves, bpy.data.images, bpy.data.worlds):
    for d in list(coll):
        coll.remove(d)
scene = bpy.context.scene
col = scene.collection

R = 3.6; CZ = 1.2; Y0 = -12.0; Y1 = 45.0
PE = 0.2; TF = -1.0; TC = 1.3
RT_R = 1.85; RT_Z = 0.35; RT_LEN = 90.0
TILE_W = 0.152; TILE_H = 0.076

# ---------------- node helpers ----------------
S = bpy.types.NodeSocket

def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m, nt, b

def setv(nt, sock, v):
    if isinstance(v, S):
        nt.links.new(v, sock)
    else:
        sock.default_value = v

def bin_(nt, k, name, v):
    setv(nt, k.inputs[name], v)

def M(nt, op, a, b=0.0, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    setv(nt, n.inputs[0], a); setv(nt, n.inputs[1], b)
    return n.outputs[0]

def MR(nt, v, a, b, c=0.0, d=1.0, interp='LINEAR'):
    n = nt.nodes.new('ShaderNodeMapRange'); n.interpolation_type = interp; n.clamp = True
    setv(nt, n.inputs[0], v)
    n.inputs[1].default_value = a; n.inputs[2].default_value = b
    n.inputs[3].default_value = c; n.inputs[4].default_value = d
    return n.outputs[0]

def MIX(nt, fac, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend
    n.clamp_factor = True
    ins = {s.identifier: s for s in n.inputs}
    setv(nt, ins['Factor_Float'], fac)
    setv(nt, ins['A_Color'], a if isinstance(a, S) else tuple(a) + ((1.0,) if len(a) == 3 else ()))
    setv(nt, ins['B_Color'], b if isinstance(b, S) else tuple(b) + ((1.0,) if len(b) == 3 else ()))
    return {s.identifier: s for s in n.outputs}['Result_Color']

def NOISE(nt, vec, scale, detail=4.0, rough=0.55, dist=0.0):
    n = nt.nodes.new('ShaderNodeTexNoise')
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = dist
    return n

def POS(nt):
    return nt.nodes.new('ShaderNodeNewGeometry')

def SEP(nt, v):
    n = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(v, n.inputs[0]); return n.outputs

def COMB(nt, x, y, z):
    n = nt.nodes.new('ShaderNodeCombineXYZ')
    setv(nt, n.inputs[0], x); setv(nt, n.inputs[1], y); setv(nt, n.inputs[2], z)
    return n.outputs[0]

def VMUL(nt, v, s):
    n = nt.nodes.new('ShaderNodeVectorMath'); n.operation = 'MULTIPLY'
    nt.links.new(v, n.inputs[0]); n.inputs[1].default_value = s
    return n.outputs[0]

def BUMP(nt, height, strength, dist, normal=None):
    n = nt.nodes.new('ShaderNodeBump')
    setv(nt, n.inputs['Height'], height)
    n.inputs['Strength'].default_value = strength
    n.inputs['Distance'].default_value = dist
    if normal is not None:
        nt.links.new(normal, n.inputs['Normal'])
    return n.outputs[0]

def AO(nt, dist):
    n = nt.nodes.new('ShaderNodeAmbientOcclusion'); n.samples = 8
    n.inputs['Distance'].default_value = dist
    return n.outputs['AO']

def MAXN(nt, *vals):
    r = vals[0]
    for v in vals[1:]:
        r = M(nt, 'MAXIMUM', r, v)
    return r

def inrange(nt, v, a, b):
    return M(nt, 'MULTIPLY', M(nt, 'GREATER_THAN', v, a), M(nt, 'LESS_THAN', v, b))

def bsdf_set(b, **kw):
    names = {'base': 'Base Color', 'rough': 'Roughness', 'metal': 'Metallic',
             'spec': 'Specular IOR Level', 'normal': 'Normal', 'emc': 'Emission Color',
             'ems': 'Emission Strength', 'alpha': 'Alpha', 'coat': 'Coat Weight'}
    nt = b.id_data
    for k, v in kw.items():
        sock = b.inputs[names[k]]
        if isinstance(v, tuple) and len(v) == 3:
            v = v + (1.0,)
        setv(nt, sock, v)

# ---------------- band ranges (tile rows) ----------------
th0 = math.asin((TF - CZ) / R) - 0.03
th1 = math.pi - math.asin((0 - CZ) / R) + 0.03

def v_of(z, side):
    s = math.asin(max(-1, min(1, (z - CZ) / R)))
    th = s if side == 'R' else math.pi - s
    return R * (th - th0)

def snap(v):
    return round(v / TILE_H) * TILE_H

def ranges_for(z0, z1, mode):
    if mode == 'obj':
        return [(snap(z0), snap(z1))]
    out = []
    for side in ('R', 'L'):
        a, b = sorted((v_of(z0, side), v_of(z1, side)))
        out.append((snap(a), snap(b)))
    return out

# ---------------- materials ----------------
def tile_mat(name, mode):
    m, nt, b = new_mat(name)
    g = POS(nt); p = SEP(nt, g.outputs['Position']); z = p[2]
    if mode == 'uv':
        tc = nt.nodes.new('ShaderNodeTexCoord'); uvs = SEP(nt, tc.outputs['UV'])
        u, v = uvs[0], uvs[1]
    else:
        u, v = p[0], p[2]
    vec = COMB(nt, u, v, 0.0)
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.5; br.offset_frequency = 2
    nt.links.new(vec, br.inputs['Vector'])
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.0032
    br.inputs['Mortar Smooth'].default_value = 0.35
    br.inputs['Bias'].default_value = -0.3
    br.inputs['Brick Width'].default_value = TILE_W
    br.inputs['Row Height'].default_value = TILE_H
    br.inputs['Color1'].default_value = (0.64, 0.60, 0.50, 1)
    br.inputs['Color2'].default_value = (0.56, 0.53, 0.45, 1)
    br.inputs['Mortar'].default_value = (0.30, 0.28, 0.24, 1)
    mort = br.outputs['Fac']
    notm = M(nt, 'SUBTRACT', 1.0, mort, clamp=True)
    colr = br.outputs['Color']
    # green frieze band + dark border rows + skirting
    band = None; border = None
    for (a, bb) in ranges_for(2.45, 2.80, mode) + ranges_for(-0.2, 0.30, mode)[-1:]:
        f = inrange(nt, v, a + 0.001, bb - 0.001)
        band = f if band is None else M(nt, 'ADD', band, f)
    for (a, bb) in ranges_for(2.45, 2.80, mode):
        f = M(nt, 'ADD', inrange(nt, v, a - TILE_H + 0.001, a - 0.001), inrange(nt, v, bb + 0.001, bb + TILE_H - 0.001))
        border = f if border is None else M(nt, 'ADD', border, f)
    colr = MIX(nt, M(nt, 'MULTIPLY', band, notm), colr, (0.07, 0.27, 0.16), 'MULTIPLY')
    colr = MIX(nt, M(nt, 'MULTIPLY', border, notm), colr, (0.06, 0.06, 0.06), 'MULTIPLY')
    # grime layers
    sv = COMB(nt, M(nt, 'MULTIPLY', u, 5.0), M(nt, 'MULTIPLY', v, 0.35), 0.0)
    sn = NOISE(nt, sv, 1.0, 8, 0.6)
    streak = MR(nt, sn.outputs['Fac'], 0.47, 0.72, 0.0, 0.7)
    lown = NOISE(nt, g.outputs['Position'], 1.6, 6)
    low = M(nt, 'MULTIPLY', MR(nt, z, 0.9, -0.35), MR(nt, lown.outputs['Fac'], 0.3, 0.7, 0.6, 1.0))
    low = MAXN(nt, low, MR(nt, z, 0.15, -0.5, 0.0, 0.95))
    trk = M(nt, 'MULTIPLY', MR(nt, z, 1.15, 0.1, 0.0, 0.93), M(nt, 'GREATER_THAN', p[0], 0.5))
    low = MAXN(nt, low, M(nt, 'MULTIPLY', trk, MR(nt, lown.outputs['Fac'], 0.3, 0.7, 0.75, 1.0)))
    soot = M(nt, 'MULTIPLY', MR(nt, z, 2.9, 4.8, 0.0, 0.85), MR(nt, lown.outputs['Fac'], 0.3, 0.7, 0.6, 1.0))
    bl = MR(nt, NOISE(nt, g.outputs['Position'], 0.5, 5).outputs['Fac'], 0.45, 0.7, 0.0, 0.5)
    crev = MR(nt, AO(nt, 0.35), 1.0, 0.5, 0.0, 0.7)
    grime = MAXN(nt, streak, low, soot, bl, crev)
    colr = MIX(nt, M(nt, 'MULTIPLY', mort, 0.6), colr, (0.12, 0.10, 0.08))
    lk = NOISE(nt, COMB(nt, M(nt, 'MULTIPLY', u, 3.0), M(nt, 'MULTIPLY', v, 0.15), 0.0), 1.0, 6, 0.6)
    leak = M(nt, 'MULTIPLY', MR(nt, lk.outputs['Fac'], 0.6, 0.78, 0.0, 0.55), MR(nt, z, 1.2, 3.6))
    colr = MIX(nt, leak, colr, (0.30, 0.18, 0.08), 'MULTIPLY')
    colr = MIX(nt, grime, colr, (0.06, 0.048, 0.036))
    colr = MIX(nt, M(nt, 'MULTIPLY', trk, 0.85), colr, (0.018, 0.016, 0.014))
    rough = M(nt, 'ADD', MR(nt, mort, 0, 1, 0.09, 0.8), M(nt, 'MULTIPLY', grime, 0.55), clamp=True)
    rough = M(nt, 'ADD', rough, MR(nt, NOISE(nt, g.outputs['Position'], 6, 3).outputs['Fac'], 0.3, 0.7, 0.0, 0.08), clamp=True)
    nrm = BUMP(nt, notm, 0.4, 0.002)
    und = NOISE(nt, g.outputs['Position'], 25, 2)
    nrm = BUMP(nt, und.outputs['Fac'], 0.04, 0.01, nrm)
    bsdf_set(b, base=colr, rough=rough, normal=nrm, spec=0.55)
    return m

def concrete_mat(name, c1, c2, rough=0.8, scale=3.0, dirt=(0.05, 0.045, 0.04), dirt_amt=0.6, metal=0.0, bump=0.15):
    m, nt, b = new_mat(name)
    g = POS(nt); pos = g.outputs['Position']
    n1 = NOISE(nt, pos, scale, 8, 0.6)
    colr = MIX(nt, n1.outputs['Fac'], c1, c2)
    n2 = NOISE(nt, pos, scale * 0.25, 6)
    d = MR(nt, n2.outputs['Fac'], 0.45, 0.72, 0.0, dirt_amt)
    colr = MIX(nt, d, colr, dirt)
    r = M(nt, 'ADD', rough, M(nt, 'MULTIPLY', MR(nt, n1.outputs['Fac'], 0.3, 0.7, -0.1, 0.1), 1.0), clamp=True)
    nrm = BUMP(nt, NOISE(nt, pos, scale * 12, 4).outputs['Fac'], bump, 0.01)
    bsdf_set(b, base=colr, rough=r, metal=metal, normal=nrm)
    return m

def floor_mat():
    m, nt, b = new_mat('PlatformFloor')
    g = POS(nt); pos = g.outputs['Position']; p = SEP(nt, pos)
    n1 = NOISE(nt, pos, 3.0, 8, 0.6)
    colr = MIX(nt, n1.outputs['Fac'], (0.085, 0.08, 0.075), (0.15, 0.14, 0.13))
    n2 = NOISE(nt, pos, 0.7, 6)
    colr = MIX(nt, MR(nt, n2.outputs['Fac'], 0.45, 0.72, 0.0, 0.75), colr, (0.035, 0.032, 0.03))
    # chewing gum spots
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    nt.links.new(COMB(nt, p[0], p[1], 0.0), vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 7.0
    sc = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(vor.outputs['Color'], sc.inputs[0])
    gum = M(nt, 'MULTIPLY', M(nt, 'LESS_THAN', vor.outputs['Distance'], 0.05), M(nt, 'GREATER_THAN', sc.outputs[0], 0.55))
    colr = MIX(nt, gum, colr, (0.05, 0.05, 0.05))
    # worn polished walking line
    path = MR(nt, M(nt, 'ABSOLUTE', M(nt, 'ADD', p[0], 1.5)), 1.4, 0.2)
    path = M(nt, 'MULTIPLY', path, MR(nt, NOISE(nt, pos, 1.2, 4).outputs['Fac'], 0.35, 0.65))
    r = M(nt, 'SUBTRACT', 0.72, M(nt, 'MULTIPLY', path, 0.42))
    r = M(nt, 'ADD', r, M(nt, 'MULTIPLY', gum, -0.2))
    nrm = BUMP(nt, NOISE(nt, pos, 40, 4).outputs['Fac'], 0.12, 0.005)
    nrm = BUMP(nt, gum, 0.3, 0.002, nrm)
    bsdf_set(b, base=colr, rough=r, normal=nrm)
    return m

def coping_mat():
    m, nt, b = new_mat('Coping')
    g = POS(nt); pos = g.outputs['Position']; p = SEP(nt, pos)
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.0
    nt.links.new(COMB(nt, p[1], p[0], 0.0), br.inputs['Vector'])
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.9
    br.inputs['Row Height'].default_value = 2.0
    br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Color1'].default_value = (0.36, 0.34, 0.31, 1)
    br.inputs['Color2'].default_value = (0.30, 0.28, 0.26, 1)
    br.inputs['Mortar'].default_value = (0.08, 0.07, 0.06, 1)
    n = NOISE(nt, pos, 4, 8)
    colr = MIX(nt, MR(nt, n.outputs['Fac'], 0.4, 0.75, 0, 0.7), br.outputs['Color'], (0.12, 0.11, 0.10))
    # edge lip darker (scuffs)
    nrm = BUMP(nt, M(nt, 'SUBTRACT', 1.0, br.outputs['Fac']), 0.5, 0.004)
    nrm = BUMP(nt, NOISE(nt, pos, 50, 4).outputs['Fac'], 0.15, 0.003, nrm)
    bsdf_set(b, base=colr, rough=0.78, normal=nrm)
    return m

def paint_mat(name, c, wear=0.5):
    m, nt, b = new_mat(name)
    g = POS(nt); pos = g.outputs['Position']
    n = NOISE(nt, pos, 9, 8, 0.65)
    w = MR(nt, n.outputs['Fac'], 0.62 - wear * 0.2, 0.72 - wear * 0.2)
    n2 = NOISE(nt, pos, 2, 5)
    colr = MIX(nt, MR(nt, n2.outputs['Fac'], 0.4, 0.7, 0, 0.45), c, (0.15, 0.13, 0.1))
    colr = MIX(nt, w, colr, (0.22, 0.21, 0.19))
    bsdf_set(b, base=colr, rough=0.6)
    return m

def rail_mat(top_z):
    m, nt, b = new_mat('RailSteel')
    g = POS(nt); pos = g.outputs['Position']; p = SEP(nt, pos)
    nz = SEP(nt, g.outputs['Normal'])[2]
    top = M(nt, 'MULTIPLY', M(nt, 'GREATER_THAN', p[2], top_z - 0.006), M(nt, 'GREATER_THAN', nz, 0.3))
    n = NOISE(nt, pos, 30, 8)
    rust = MIX(nt, n.outputs['Fac'], (0.10, 0.05, 0.03), (0.22, 0.11, 0.05))
    colr = MIX(nt, top, rust, (0.62, 0.62, 0.63))
    bsdf_set(b, base=colr, metal=MR(nt, top, 0, 1, 0.25, 1.0), rough=MR(nt, top, 0, 1, 0.85, 0.16))
    return m

def wood_mat():
    m, nt, b = new_mat('BenchWood')
    g = POS(nt); p = SEP(nt, g.outputs['Position'])
    vec = COMB(nt, M(nt, 'MULTIPLY', p[0], 60.0), M(nt, 'MULTIPLY', p[1], 1.5), M(nt, 'MULTIPLY', p[2], 60.0))
    n = NOISE(nt, vec, 1.0, 6, 0.6, 2.0)
    colr = MIX(nt, n.outputs['Fac'], (0.10, 0.05, 0.025), (0.27, 0.14, 0.065))
    n2 = NOISE(nt, g.outputs['Position'], 3, 5)
    colr = MIX(nt, MR(nt, n2.outputs['Fac'], 0.5, 0.75, 0, 0.5), colr, (0.06, 0.04, 0.03))
    nrm = BUMP(nt, n.outputs['Fac'], 0.15, 0.002)
    bsdf_set(b, base=colr, rough=0.45, normal=nrm, coat=0.2)
    return m

def simple_mat(name, c, rough=0.5, metal=0.0, ems=0.0, emc=None):
    m, nt, b = new_mat(name)
    bsdf_set(b, base=c, rough=rough, metal=metal)
    if ems > 0:
        bsdf_set(b, emc=emc or c, ems=ems)
    return m

def emit_mat(name, c, strength):
    m, nt, b = new_mat(name)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.nodes.remove(b)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = c + (1.0,)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs['Surface'])
    return m

def poster_mat(name, img):
    m, nt, b = new_mat(name)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['UV'], t.inputs['Vector'])
    g = POS(nt); pos = g.outputs['Position']
    n = NOISE(nt, pos, 2.5, 6)
    uvs = SEP(nt, tc.outputs['UV'])
    edge = MAXN(nt, MR(nt, uvs[0], 0.05, 0.0), MR(nt, uvs[0], 0.95, 1.0), MR(nt, uvs[1], 0.12, 0.0))
    dirt = MAXN(nt, MR(nt, n.outputs['Fac'], 0.45, 0.75, 0, 0.55), M(nt, 'MULTIPLY', edge, 0.6))
    colr = MIX(nt, dirt, t.outputs['Color'], (0.12, 0.10, 0.08))
    colr = MIX(nt, 0.22, colr, (0.45, 0.42, 0.36))  # faded
    nrm = BUMP(nt, NOISE(nt, pos, 8, 4).outputs['Fac'], 0.05, 0.01)
    bsdf_set(b, base=colr, rough=MR(nt, dirt, 0, 1, 0.22, 0.6), normal=nrm)
    return m

MAT = {}
MAT['tile_uv'] = tile_mat('Tiles', 'uv')
MAT['tile_obj'] = tile_mat('TilesEndWall', 'obj')
MAT['floor'] = floor_mat()
MAT['coping'] = coping_mat()
MAT['yellow'] = paint_mat('YellowLine', (0.75, 0.52, 0.02), 0.5)
MAT['white_paint'] = paint_mat('WhitePaint', (0.72, 0.70, 0.64), 0.7)
MAT['plat_face'] = concrete_mat('PlatformFace', (0.12, 0.11, 0.10), (0.20, 0.19, 0.17), 0.85, 2.0, (0.03, 0.03, 0.03), 0.8)
MAT['trackbed'] = concrete_mat('TrackBed', (0.07, 0.065, 0.06), (0.13, 0.12, 0.105), 0.7, 2.5, (0.02, 0.018, 0.016), 0.8)
MAT['sleeper'] = concrete_mat('Sleeper', (0.05, 0.035, 0.025), (0.11, 0.075, 0.05), 0.8, 6.0, (0.02, 0.02, 0.02), 0.5)
MAT['iron'] = concrete_mat('TunnelIron', (0.035, 0.032, 0.03), (0.07, 0.06, 0.05), 0.65, 4.0, (0.015, 0.012, 0.01), 0.7, metal=0.4)
MAT['portal'] = concrete_mat('PortalConcrete', (0.10, 0.095, 0.09), (0.18, 0.17, 0.155), 0.85, 3.0, (0.02, 0.02, 0.02), 0.85)
MAT['rail'] = rail_mat(-0.73)
MAT['cond'] = concrete_mat('ConductorRail', (0.10, 0.09, 0.08), (0.2, 0.17, 0.14), 0.6, 20.0, (0.04, 0.03, 0.02), 0.4, metal=0.6)
MAT['insul'] = simple_mat('Insulator', (0.55, 0.52, 0.45), 0.3)
MAT['cable'] = concrete_mat('Cable', (0.015, 0.015, 0.015), (0.04, 0.04, 0.038), 0.55, 30.0, (0.08, 0.07, 0.06), 0.4)
MAT['wood'] = wood_mat()
MAT['steel_dark'] = concrete_mat('PaintedSteel', (0.03, 0.03, 0.035), (0.06, 0.06, 0.065), 0.45, 10.0, (0.1, 0.09, 0.08), 0.3, metal=0.3)
MAT['alu'] = simple_mat('Aluminium', (0.55, 0.55, 0.56), 0.35, 1.0)
MAT['housing'] = simple_mat('LampHousing', (0.18, 0.18, 0.18), 0.5, 0.6)
MAT['lamp_on'] = emit_mat('LampOn', (1.0, 0.93, 0.84), 9.0)
MAT['lamp_dim'] = emit_mat('LampDim', (1.0, 0.85, 0.7), 1.2)
MAT['lamp_off'] = simple_mat('LampOff', (0.35, 0.35, 0.33), 0.3)
MAT['red'] = simple_mat('RoundelRed', (0.62, 0.02, 0.02), 0.35)
MAT['blue'] = simple_mat('RoundelBlue', (0.0, 0.06, 0.32), 0.35)
MAT['white'] = simple_mat('SignWhite', (0.85, 0.85, 0.83), 0.35)
MAT['black'] = simple_mat('SignBlack', (0.01, 0.01, 0.01), 0.4)
MAT['dot'] = emit_mat('DotMatrix', (1.0, 0.45, 0.05), 6.0)
MAT['sig_red'] = emit_mat('SignalRed', (1.0, 0.03, 0.01), 40.0)
MAT['paper'] = concrete_mat('Litter', (0.55, 0.53, 0.48), (0.7, 0.68, 0.62), 0.8, 20.0, (0.2, 0.18, 0.15), 0.5)

# ---------------- mesh helpers ----------------
def link(obj):
    col.objects.link(obj); return obj

def mesh_obj(name, bm, mat=None, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    o = bpy.data.objects.new(name, me)
    if mat:
        o.data.materials.append(mat)
    return link(o)

def add_box(bm, c, s):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = Vector((v.co.x * s[0] + c[0], v.co.y * s[1] + c[1], v.co.z * s[2] + c[2]))

def boxes(name, items, mat, bevel=0.0):
    bm = bmesh.new()
    for c, s in items:
        add_box(bm, c, s)
    o = mesh_obj(name, bm, mat)
    if bevel > 0:
        md = o.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = 2
        md.limit_method = 'ANGLE'
    return o

def extrude_profile(name, prof, y0, y1, ox, oz, mat):
    bm = bmesh.new()
    a = [bm.verts.new((ox + x, y0, oz + z)) for x, z in prof]
    b = [bm.verts.new((ox + x, y1, oz + z)) for x, z in prof]
    n = len(prof)
    bm.faces.new(list(reversed(a))); bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat)

def cylinder_y(bm, cx, cz, r, y0, y1, seg=12):
    m = Matrix.Translation(((cx, (y0 + y1) / 2, cz))) @ Matrix.Rotation(math.radians(90), 4, 'X')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(y1 - y0), matrix=m)

def orient_mat(xa, ya, loc, scale=(1, 1, 1)):
    xa = Vector(xa).normalized(); ya = Vector(ya).normalized(); za = xa.cross(ya)
    m = Matrix((xa, ya, za)).transposed().to_4x4()
    m.translation = Vector(loc)
    return m @ Matrix.Diagonal(Vector(scale + (1,)))

def quad(name, w, h, mat, mw):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, l in enumerate(me.loops):
        uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][l.vertex_index]
    o = bpy.data.objects.new(name, me); o.data.materials.append(mat); o.matrix_world = mw
    return link(o)

def text(name, body, size, mat, mw, align='CENTER', extrude=0.0008, font=None):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size
    cu.align_x = align; cu.align_y = 'CENTER'; cu.extrude = extrude
    if font:
        cu.font = font
    o = bpy.data.objects.new(name, cu); o.data.materials.append(mat); o.matrix_world = mw
    return link(o)

FONT = None
for fp in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
    if os.path.exists(fp):
        try:
            FONT = bpy.data.fonts.load(fp); break
        except Exception:
            pass

# ---------------- tunnel shell ----------------
NP = 160
prof = []
for i in range(NP + 1):
    t = th0 + (th1 - th0) * i / NP
    prof.append((R * math.cos(t), CZ + R * math.sin(t), R * (t - th0)))
ys = [Y0 + (Y1 - Y0) * k / 12 for k in range(13)]
bm = bmesh.new()
grid = [[bm.verts.new((x, y, z)) for (x, z, v) in prof] for y in ys]
uvl = bm.loops.layers.uv.new()
for k in range(len(ys) - 1):
    for i in range(NP):
        f = bm.faces.new((grid[k][i], grid[k + 1][i], grid[k + 1][i + 1], grid[k][i + 1]))
        for l in f.loops:
            co = l.vert.co
            ii = i if l.vert in (grid[k][i], grid[k + 1][i]) else i + 1
            l[uvl].uv = (co.y, prof[ii][2])
bm.normal_update(); bm.faces.ensure_lookup_table()
f0 = bm.faces[NP * 3 + NP // 2]
radial = f0.calc_center_median() - Vector((0, f0.calc_center_median().y, CZ))
if f0.normal.dot(radial) > 0:
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
tun = mesh_obj('TunnelShell', bm, MAT['tile_uv'], smooth=True)
sd = tun.modifiers.new('solid', 'SOLIDIFY'); sd.thickness = 0.2; sd.offset = -1.0

# end wall with running-tunnel mouth (square annulus)
def end_wall(name, y, hole, face_dir):
    bm = bmesh.new(); N = 64
    if hole:
        inner = []; outer = []
        for i in range(N):
            a = 2 * math.pi * i / N
            d = Vector((math.cos(a), math.sin(a)))
            inner.append(bm.verts.new((TC + d.x * RT_R, y, RT_Z + d.y * RT_R)))
            s = 7.0 / max(abs(d.x), abs(d.y))
            outer.append(bm.verts.new((TC + d.x * s, y, RT_Z + d.y * s)))
        for i in range(N):
            j = (i + 1) % N
            bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    else:
        vs = [bm.verts.new((x, y, z)) for x, z in ((-7, -4), (7, -4), (7, 8), (-7, 8))]
        bm.faces.new(vs)
    bm.normal_update(); bm.faces.ensure_lookup_table()
    if bm.faces[0].normal.y * face_dir < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    o = mesh_obj(name, bm, MAT['tile_obj'])
    s = o.modifiers.new('solid', 'SOLIDIFY'); s.thickness = 0.25; s.offset = -1.0
    return o

end_wall('EndWall', Y1, True, -1)
end_wall('BackWall', Y0, False, 1)

# portal ring
bm = bmesh.new(); N = 64
ring_in = []; ring_out = []
for i in range(N):
    a = 2 * math.pi * i / N
    for (lst, rr) in ((ring_in, RT_R), (ring_out, RT_R + 0.22)):
        lst.append([bm.verts.new((TC + math.cos(a) * rr, Y1 + dy, RT_Z + math.sin(a) * rr)) for dy in (-0.12, 0.3)])
for i in range(N):
    j = (i + 1) % N
    bm.faces.new((ring_in[i][0], ring_in[j][0], ring_out[j][0], ring_out[i][0]))
    bm.faces.new((ring_in[i][0], ring_in[i][1], ring_in[j][1], ring_in[j][0]))
    bm.faces.new((ring_out[i][0], ring_out[j][0], ring_out[j][1], ring_out[i][1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mesh_obj('PortalRing', bm, MAT['portal'], smooth=True)

# running tunnel
bm = bmesh.new(); N = 48
ringsv = []
for yy in (Y1, Y1 + RT_LEN):
    ringsv.append([bm.verts.new((TC + math.cos(2 * math.pi * i / N) * RT_R, yy, RT_Z + math.sin(2 * math.pi * i / N) * RT_R)) for i in range(N)])
for i in range(N):
    j = (i + 1) % N
    bm.faces.new((ringsv[0][i], ringsv[1][i], ringsv[1][j], ringsv[0][j]))
bm.normal_update(); bm.faces.ensure_lookup_table()
if bm.faces[0].normal.dot(bm.faces[0].calc_center_median() - Vector((TC, bm.faces[0].calc_center_median().y, RT_Z))) > 0:
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
rt = mesh_obj('RunningTunnel', bm, MAT['iron'], smooth=True)
s = rt.modifiers.new('solid', 'SOLIDIFY'); s.thickness = 0.15; s.offset = -1.0
cap = boxes('RunningTunnelCap', [((TC, Y1 + RT_LEN + 0.2, RT_Z), (5, 0.2, 5))], MAT['iron'])

# ribs (cast-iron segment flanges)
bm = bmesh.new()
y = Y1 + 0.6
while y < Y1 + RT_LEN:
    for i in range(36):
        a0 = 2 * math.pi * i / 36; a1 = 2 * math.pi * (i + 1) / 36
        pts = []
        for a in (a0, a1):
            for rr in (RT_R, RT_R - 0.07):
                for dy in (-0.025, 0.025):
                    pts.append(bm.verts.new((TC + math.cos(a) * rr, y + dy, RT_Z + math.sin(a) * rr)))
        # pts index: a,r,dy -> 0..7
        q = pts
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (1, 5, 7, 3), (0, 2, 6, 4)):
            try:
                bm.faces.new([q[k] for k in f])
            except ValueError:
                pass
    y += 0.55
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mesh_obj('TunnelRibs', bm, MAT['iron'])

# ---------------- platform ----------------
plat = boxes('Platform', [((-1.7, (Y0 + Y1) / 2, -0.6), (3.8, Y1 - Y0, 1.2))], MAT['plat_face'])
plat.data.materials.append(MAT['floor'])
for p in plat.data.polygons:
    if p.normal.z > 0.9:
        p.material_index = 1
boxes('PlatformCoping', [((0.0, (Y0 + Y1) / 2, 0.006), (0.5, Y1 - Y0, 0.012)),
                         ((0.235, (Y0 + Y1) / 2, -0.04), (0.07, Y1 - Y0, 0.09))], MAT['coping'], bevel=0.004)
boxes('YellowLine', [((-0.62, (Y0 + Y1) / 2, 0.0015), (0.09, Y1 - Y0, 0.003))], MAT['yellow'])
# under-platform recess shadow lip
boxes('PlatformRecess', [((0.12, (Y0 + Y1) / 2, -0.75), (0.2, Y1 - Y0, 0.5))], MAT['trackbed'])

# ---------------- track ----------------
YE = Y1 + RT_LEN
boxes('TrackBed', [((1.55, (Y0 + Y1) / 2, TF - 0.05), (2.9, Y1 - Y0, 0.1)),
                   ((TC, (Y1 + YE) / 2, TF - 0.05), (2.7, RT_LEN, 0.1))], MAT['trackbed'])
# drainage pit between rails
boxes('PitWalls', [((TC - 0.48, (Y0 + YE) / 2, TF + 0.03), (0.12, YE - Y0, 0.06)),
                   ((TC + 0.48, (Y0 + YE) / 2, TF + 0.03), (0.12, YE - Y0, 0.06))], MAT['trackbed'])
items = []
yy = Y0 + 0.3
while yy < YE:
    j = random.uniform(-0.02, 0.02)
    items.append(((TC + j, yy, -0.94), (1.95, 0.24, 0.12)))
    yy += 0.68
boxes('Sleepers', items, MAT['sleeper'], bevel=0.01)
rail_prof = [(-0.065, 0), (0.065, 0), (0.065, 0.012), (0.009, 0.03), (0.009, 0.11), (0.035, 0.116),
             (0.035, 0.15), (-0.035, 0.15), (-0.035, 0.116), (-0.009, 0.11), (-0.009, 0.03), (-0.065, 0.012)]
for nm, rx in (('RailL', TC - 0.7175), ('RailR', TC + 0.7175)):
    extrude_profile(nm, rail_prof, Y0, YE, rx, -0.88, MAT['rail'])
# conductor rails
rect = [(-0.035, 0), (0.035, 0), (0.035, 0.1), (-0.035, 0.1)]
extrude_profile('NegRail', rect, Y0, YE, TC, -0.84, MAT['cond'])
extrude_profile('PosRail', rect, Y0, YE, TC + 1.12, -0.80, MAT['cond'])
bm = bmesh.new()
yy = Y0 + 1.0
while yy < YE:
    m1 = Matrix.Translation((TC, yy, -0.86))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.05, radius2=0.035, depth=0.06, matrix=m1)
    m2 = Matrix.Translation((TC + 1.12, yy, -0.84))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.055, radius2=0.04, depth=0.1, matrix=m2)
    yy += 2.72
mesh_obj('Insulators', bm, MAT['insul'], smooth=True)

# cables on track-side wall
bm = bmesh.new()
for k, (cz, cr) in enumerate(((-0.55, 0.035), (-0.45, 0.028), (-0.37, 0.03), (-0.28, 0.022), (-0.2, 0.04), (0.0, 0.026))):
    cx = math.sqrt(R ** 2 - (cz - CZ) ** 2) - cr - 0.08
    cylinder_y(bm, cx, cz, cr, Y0, Y1, 10)
mesh_obj('Cables', bm, MAT['cable'], smooth=True)
items = []
yy = Y0 + 0.5
while yy < Y1:
    items.append(((math.sqrt(R ** 2 - (-0.3 - CZ) ** 2) - 0.07, yy, -0.3), (0.04, 0.03, 0.75)))
    yy += 1.5
boxes('CableBrackets', items, MAT['steel_dark'])

# ---------------- lighting rigs ----------------
def luminaire(x, y, z, length, state, power):
    boxes('LumHousing', [((x, y, z + 0.06), (0.26, length, 0.1))], MAT['housing'], bevel=0.008)
    ceil = CZ + math.sqrt(R ** 2 - x ** 2)
    boxes('LumRod', [((x, y - length / 3, (z + ceil) / 2 + 0.05), (0.02, 0.02, ceil - z)),
                     ((x, y + length / 3, (z + ceil) / 2 + 0.05), (0.02, 0.02, ceil - z))], MAT['steel_dark'])
    mat = {'on': MAT['lamp_on'], 'dim': MAT['lamp_dim'], 'off': MAT['lamp_off']}[state]
    boxes('LumDiffuser', [((x, y, z + 0.005), (0.2, length - 0.05, 0.012))], mat)
    if state != 'off':
        ld = bpy.data.lights.new('LumLight', 'AREA'); ld.shape = 'RECTANGLE'
        ld.size = 0.2; ld.size_y = length - 0.05
        ld.energy = power if state == 'on' else power * 0.12
        ld.color = (1.0, 0.92, 0.82)
        lo = bpy.data.objects.new('LumLight', ld); lo.location = (x, y, z - 0.01)
        link(lo)
        try:
            lo.visible_camera = False
        except Exception:
            pass

yy = Y0 + 2.0
idx = 0
while yy < Y1 - 1.0:
    state = 'on'
    if idx == 9:
        state = 'off'
    elif idx == 5:
        state = 'dim'
    luminaire(-1.2, yy, 4.15, 2.4, state, 160)
    if idx % 2 == 0:
        luminaire(1.6, yy + 1.4, 4.05, 2.4, 'on' if idx != 12 else 'off', 90)
    yy += 3.0
    idx += 1

# deep tunnel lights
for (lx, ly, lz, e, c) in ((TC - 1.1, Y1 + 18, 1.6, 6, (1.0, 0.75, 0.45)), (TC - 1.1, Y1 + 55, 1.6, 5, (1.0, 0.75, 0.45))):
    ld = bpy.data.lights.new('TunnelLamp', 'POINT'); ld.energy = e; ld.color = c; ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new('TunnelLamp', ld); lo.location = (lx, ly, lz); link(lo)
    boxes('TunnelLampHousing', [((lx - 0.03, ly, lz), (0.06, 0.12, 0.12))], MAT['lamp_dim'])
# signal
boxes('SignalHead', [((TC - 1.05, Y1 + 9, 0.9), (0.2, 0.15, 0.5))], MAT['black'])
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.04, matrix=Matrix.Translation((TC - 1.05, Y1 + 8.92, 1.05)))
mesh_obj('SignalLamp', bm, MAT['sig_red'], smooth=True)
ld = bpy.data.lights.new('SignalGlow', 'POINT'); ld.energy = 3; ld.color = (1, 0.05, 0.02); ld.shadow_soft_size = 0.05
lo = bpy.data.objects.new('SignalGlow', ld); lo.location = (TC - 1.05, Y1 + 8.8, 1.05); link(lo)

# ---------------- posters ----------------
tex_dir = os.path.join(OUT, 'textures'); os.makedirs(tex_dir, exist_ok=True)

def poster_image(name, w, h, seed):
    rng = np.random.default_rng(seed)
    yy_, xx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    pal = [np.array(c) for c in ([0.9, 0.35, 0.1], [0.05, 0.2, 0.55], [0.95, 0.8, 0.15], [0.1, 0.45, 0.3],
                                  [0.8, 0.1, 0.25], [0.15, 0.12, 0.2], [0.9, 0.88, 0.82], [0.3, 0.65, 0.85])]
    i1, i2, i3 = rng.choice(len(pal), 3, replace=False)
    t = (yy_ / h)[..., None]
    img = pal[i1] * (1 - t) + pal[i2] * t
    cx, cy, rr = rng.uniform(0.25, 0.75) * w, rng.uniform(0.35, 0.65) * h, rng.uniform(0.18, 0.35) * min(w, h)
    d = np.sqrt((xx_ - cx) ** 2 + (yy_ - cy) ** 2)
    img = np.where((d < rr)[..., None], pal[i3], img)
    # diagonal stripe
    k = rng.uniform(-0.8, 0.8)
    band = np.abs((yy_ - h * 0.45) - k * (xx_ - w / 2)) < h * rng.uniform(0.02, 0.06)
    img = np.where(band[..., None], img * 0.4 + 0.6, img)
    # text blocks
    tc = np.array([0.97, 0.97, 0.95]) if img.mean() < 0.5 else np.array([0.05, 0.05, 0.06])
    for row in range(rng.integers(2, 4)):
        y0 = int(h * (0.08 + row * 0.045)); x1 = int(w * rng.uniform(0.5, 0.9))
        img[y0:y0 + int(h * 0.025), int(w * 0.08):x1] = tc
    img[int(h * 0.04):int(h * 0.05), int(w * 0.08):int(w * 0.3)] = tc
    # logo block
    img[int(h * 0.85):int(h * 0.93), int(w * 0.75):int(w * 0.92)] = pal[(i1 + 3) % len(pal)]
    rgba = np.concatenate([img, np.ones((h, w, 1))], axis=2).astype(np.float32)
    im = bpy.data.images.new(name, w, h)
    im.pixels.foreach_set(rgba.ravel())
    path = os.path.join(tex_dir, name + '.png')
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    im.pack()
    return im

HEADLINES = ['LATE NIGHT AT THE MUSEUM', 'NEW SEASON', 'ESCAPE TO THE COAST', 'THE MUSICAL',
             'FRESH. FAST. FOLDED.', 'SALE NOW ON', 'BOOK YOUR SUMMER', 'MIND YOUR MONEY',
             'OPENING FRIDAY', 'TASTE THE CITY', 'DOWNLOAD THE APP', 'COFFEE THAT WORKS']

# platform wall (left) posters: portrait, flat panels at x
PX = -3.37
ylist = []
yy = Y0 + 4.0
while yy < Y1 - 1.5:
    ylist.append(yy); yy += 3.1
roundel_at = set(ylist[2::4])
pi = 0
for i, yy in enumerate(ylist):
    if yy in roundel_at:
        continue
    pw, ph = 1.02, 1.52
    img = poster_image('poster_%02d' % pi, 384, 576, 100 + pi)
    pm = poster_mat('PosterMat%02d' % pi, img)
    mw = orient_mat((0, 1, 0), (0, 0, 1), (PX + 0.012, yy, 1.62))
    quad('Poster%02d' % pi, pw, ph, pm, mw)
    # frame
    boxes('PosterFrame', [((PX, yy, 1.62 + ph / 2 + 0.02), (0.03, pw + 0.08, 0.04)),
                          ((PX, yy, 1.62 - ph / 2 - 0.02), (0.03, pw + 0.08, 0.04)),
                          ((PX, yy - pw / 2 - 0.02, 1.62), (0.03, 0.04, ph + 0.08)),
                          ((PX, yy + pw / 2 + 0.02, 1.62), (0.03, 0.04, ph + 0.08))], MAT['alu'], bevel=0.004)
    boxes('PosterBack', [((PX - 0.01, yy, 1.62), (0.02, pw + 0.04, ph + 0.04))], MAT['black'])
    tc = MAT['white'] if pi % 2 == 0 else MAT['black']
    text('PosterHead%02d' % pi, HEADLINES[pi % len(HEADLINES)], 0.065, tc,
         orient_mat((0, 1, 0), (0, 0, 1), (PX + 0.016, yy, 1.62 + ph * 0.38)), font=FONT)
    pi += 1

# roundels
STATION = 'ALDER CROSS'
def roundel(loc, xa, scale=1.0):
    xa = Vector(xa); ya = Vector((0, 0, 1)); za = xa.cross(ya)
    bm = bmesh.new(); N = 64; ri = 0.33 * scale; ro = 0.47 * scale
    vi = []; vo = []
    for i in range(N):
        a = 2 * math.pi * i / N
        vi.append(bm.verts.new((math.cos(a) * ri, math.sin(a) * ri, 0)))
        vo.append(bm.verts.new((math.cos(a) * ro, math.sin(a) * ro, 0)))
    for i in range(N):
        j = (i + 1) % N
        bm.faces.new((vi[i], vi[j], vo[j], vo[i]))
    o = mesh_obj('RoundelRing', bm, MAT['red'])
    o.matrix_world = orient_mat(tuple(xa), (0, 0, 1), loc)
    sd = o.modifiers.new('s', 'SOLIDIFY'); sd.thickness = 0.02
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.012), (1.25 * scale, 0.19 * scale, 0.02))
    b = mesh_obj('RoundelBar', bm, MAT['blue']); b.matrix_world = orient_mat(tuple(xa), (0, 0, 1), loc)
    text('RoundelText', STATION, 0.11 * scale, MAT['white'],
         orient_mat(tuple(xa), (0, 0, 1), Vector(loc) + za * 0.024), font=FONT)
    # backing board
    bm = bmesh.new(); add_box(bm, (0, 0, -0.015), (1.45 * scale, 1.05 * scale, 0.02))
    bb = mesh_obj('RoundelBoard', bm, MAT['white']); bb.matrix_world = orient_mat(tuple(xa), (0, 0, 1), loc)

for yy in roundel_at:
    roundel((PX + 0.035, yy, 1.75), (0, 1, 0))

# cross-track posters (right wall), landscape
QZ = 1.25
qx = math.sqrt(R ** 2 - (QZ + 0.55 - CZ) ** 2) - 0.05
yy = Y0 + 3.5; qi = 0
while yy < Y1 - 3:
    if qi % 3 == 1:
        roundel((qx - 0.04, yy, QZ + 0.2), (0, -1, 0), 1.25)
    else:
        img = poster_image('xtrack_%02d' % qi, 768, 384, 300 + qi)
        pm = poster_mat('XPosterMat%02d' % qi, img)
        quad('XPoster%02d' % qi, 3.0, 1.5, pm, orient_mat((0, -1, 0), (0, 0, 1), (qx - 0.012, yy, QZ)))
        boxes('XFrame', [((qx, yy, QZ + 0.77), (0.03, 3.08, 0.04)), ((qx, yy, QZ - 0.77), (0.03, 3.08, 0.04)),
                         ((qx, yy - 1.52, QZ), (0.03, 0.04, 1.58)), ((qx, yy + 1.52, QZ), (0.03, 0.04, 1.58))], MAT['alu'])
        boxes('XBack', [((qx + 0.01, yy, QZ), (0.02, 3.04, 1.54))], MAT['black'])
        tc = MAT['white'] if qi % 2 == 0 else MAT['black']
        text('XHead%02d' % qi, HEADLINES[(qi + 5) % len(HEADLINES)], 0.13, tc,
             orient_mat((0, -1, 0), (0, 0, 1), (qx - 0.016, yy, QZ + 0.52)), font=FONT)
    yy += 4.2; qi += 1

# ---------------- benches ----------------
def bench(y0):
    L = 2.0
    slats = []
    for k in range(4):
        slats.append(((-3.30 + 0.105 * k + 0.045, y0, 0.45), (0.09, L, 0.03)))
    for k, zz in enumerate((0.62, 0.75)):
        slats.append(((-3.40 + 0.01 * k, y0, zz), (0.03, L, 0.1)))
    boxes('BenchSlats', slats, MAT['wood'], bevel=0.006)
    fr = []
    for yy in (y0 - L / 2 + 0.2, y0 + L / 2 - 0.2):
        fr += [((-2.95, yy, 0.21), (0.05, 0.05, 0.42)), ((-3.33, yy, 0.21), (0.05, 0.05, 0.42)),
               ((-3.14, yy, 0.425), (0.45, 0.05, 0.03)), ((-3.43, yy, 0.64), (0.04, 0.05, 0.4)),
               ((-3.14, yy, 0.012), (0.5, 0.12, 0.024))]
    boxes('BenchFrame', fr, MAT['steel_dark'], bevel=0.006)

bench(Y0 + 8.65)
bench(Y0 + 20.05)
bench(Y0 + 33.4)

# litter bin-free: litter pieces
def litter(x, y, z, s, rot):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=5, y_segments=5, size=s)
    for v in bm.verts:
        v.co.z += random.uniform(0, s * 0.35)
    bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(rot, 3, 'Z'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, z))
    mesh_obj('Litter', bm, MAT['paper'], smooth=True)

for _ in range(7):
    litter(random.uniform(0.4, 2.6), random.uniform(Y0 + 6, Y1 - 2), -0.99, random.uniform(0.06, 0.12), random.uniform(0, 6))
for _ in range(4):
    litter(random.uniform(-3.0, -0.8), random.uniform(Y0 + 10, Y1 - 4), 0.002, random.uniform(0.04, 0.08), random.uniform(0, 6))

# ---------------- MIND THE GAP ----------------
for yy in (Y0 + 14, Y0 + 26, Y0 + 38, Y0 + 50):
    text('MindTheGap', 'MIND THE GAP', 0.2, MAT['white_paint'],
         orient_mat((0, -1, 0), (1, 0, 0), (-0.33, yy, 0.0025)), extrude=0.0003, font=FONT)

# ---------------- dot-matrix indicator ----------------
DY = Y0 + 21.0; DZ = 3.25
boxes('IndicatorBox', [((-1.2, DY, DZ), (1.5, 0.14, 0.34))], MAT['black'], bevel=0.01)
ceil = CZ + math.sqrt(R ** 2 - 1.2 ** 2)
boxes('IndicatorRods', [((-1.75, DY, (DZ + ceil) / 2), (0.025, 0.025, ceil - DZ)),
                        ((-0.65, DY, (DZ + ceil) / 2), (0.025, 0.025, ceil - DZ))], MAT['steel_dark'])
fm = orient_mat((1, 0, 0), (0, 0, 1), (-1.88, DY - 0.072, DZ + 0.07))
text('Dot1', '1  Hollins Park     2 min', 0.075, MAT['dot'], fm, align='LEFT', font=FONT)
fm = orient_mat((1, 0, 0), (0, 0, 1), (-1.88, DY - 0.072, DZ - 0.07))
text('Dot2', '2  Easton Vale       6 min', 0.075, MAT['dot'], fm, align='LEFT', font=FONT)

# CCTV / speakers on lamp line
boxes('Speakers', [((-1.2, Y0 + 12.5, 3.98), (0.18, 0.12, 0.2)), ((-1.2, Y0 + 30.5, 3.98), (0.18, 0.12, 0.2))], MAT['housing'])
# ceiling conduit
bm = bmesh.new()
cylinder_y(bm, -0.3, CZ + math.sqrt(R ** 2 - 0.09) - 0.12, 0.03, Y0, Y1, 10)
cylinder_y(bm, -0.42, CZ + math.sqrt(R ** 2 - 0.42 ** 2) - 0.1, 0.02, Y0, Y1, 10)
mesh_obj('Conduit', bm, MAT['steel_dark'], smooth=True)

# ---------------- haze volume ----------------
vm = bpy.data.materials.new('Haze')
try:
    vm.use_nodes = True
except Exception:
    pass
nt = vm.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); pv = nt.nodes.new('ShaderNodeVolumePrincipled')
pv.inputs['Density'].default_value = 0.0035
pv.inputs['Color'].default_value = (0.9, 0.85, 0.78, 1)
pv.inputs['Anisotropy'].default_value = 0.3
nt.links.new(pv.outputs[0], o_.inputs['Volume'])
hz = boxes('Haze', [((0.0, (Y0 + YE) / 2, 1.0), (8, YE - Y0 + 1, 7))], vm)

# ---------------- world / camera / render ----------------
w = bpy.data.worlds.new('World'); scene.world = w
try:
    w.use_nodes = True
except Exception:
    pass
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); bg.inputs['Strength'].default_value = 0.0

camd = bpy.data.cameras.new('Camera'); camd.lens = 26; camd.sensor_width = 36
camd.dof.use_dof = True; camd.dof.focus_distance = 9.0; camd.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new('Camera', camd); link(cam)
cam.location = Vector((-1.45, -3.0, 1.62))
tgt = Vector((0.15, 40.0, 1.25))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

r = scene.render
r.engine = 'CYCLES'
r.resolution_x = 1920; r.resolution_y = 1080; r.resolution_percentage = 100
cy = scene.cycles
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dt in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == dt]
            if devs:
                for d in prefs.devices:
                    d.use = (d.type == dt)
                print('GPU DEVICE', dt, [d.name for d in devs])
                break
        except Exception as e:
            print('dev err', e)
    cy.device = 'GPU'
except Exception as e:
    print('GPU setup failed', e)
cy.samples = 512 if MODE == 'final' else 96
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.015
cy.use_denoising = True
try:
    cy.denoiser = 'OPTIX'
except Exception:
    pass
cy.max_bounces = 8; cy.diffuse_bounces = 4; cy.glossy_bounces = 4; cy.transmission_bounces = 4
cy.volume_bounces = 0; cy.volume_step_rate = 4.0
cy.sample_clamp_indirect = 8.0
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception as e:
    print('cm', e)
scene.view_settings.exposure = float(argv[1]) if len(argv) > 1 else 0.0
r.image_settings.file_format = 'PNG'

if MODE == 'test':
    r.resolution_percentage = 50
    r.filepath = os.path.join(r"C:\Users\Hype\AppData\Local\Temp\usp_base", 'test.png')
else:
    r.filepath = os.path.join(OUT, 'final_render.png')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'underground_station_platform.blend'))
import time
t0 = time.time()
bpy.ops.render.render(write_still=True)
print('RENDER_TIME', time.time() - t0)
