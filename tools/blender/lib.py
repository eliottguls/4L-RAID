# Outils de modélisation pour Blender (module bpy), utilisés par les scripts de ce dossier.
# Toutes les fonctions prennent des coordonnées dans le repère du site :
# x vers l'avant, y vers le haut, z vers la droite du conducteur, en mètres.
# T() les convertit dans le repère de Blender (z vers le haut) ; l'export glTF (+Y en haut)
# redonne exactement le repère du site.
import math

import bpy  # noqa: I001 (bpy doit être importé avant bmesh)
import bmesh
from mathutils import Matrix, Quaternion, Vector


def T(x, y, z):
    return Vector((x, -z, y))


def TD(d):
    """Direction du repère du site vers Blender."""
    return Vector((d[0], -d[2], d[1])).normalized()


# ---------------------------------------------------------------- scène
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.curves):
        for b in list(c):
            c.remove(b)


_mats = {}


def M(name, color, metal=0.0, rough=0.6, alpha=1.0):
    """Matériau partagé (un seul par nom, pour limiter les appels de dessin)."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    r, g, b = ((color >> 16) & 255) / 255, ((color >> 8) & 255) / 255, (color & 255) / 255
    # Les couleurs sont données en sRGB : Blender attend du linéaire.
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    bsdf.inputs['Base Color'].default_value = (*lin, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if alpha < 1:
        bsdf.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            m.blend_method = 'BLEND'
    _mats[name] = m
    return m


def _obj_from_bm(bm, name, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        o.data.materials.append(mat)
    return o


def smooth(o, angle=35):
    """Ombrage lissé avec arêtes vives au-delà de `angle` degrés."""
    me = o.data
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(angle))
    except AttributeError:
        pass
    return o


def place(o, pos=(0, 0, 0), rot=None, axis=None):
    """Positionne un objet construit autour de l'origine. axis : axe local +Z orienté vers
    cette direction (repère du site). rot : quaternion Blender supplémentaire."""
    q = Quaternion()
    if axis is not None:
        q = Vector((0, 0, 1)).rotation_difference(TD(axis))
    if rot is not None:
        q = q @ rot
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = q
    o.location = T(*pos)
    return o


def bevel(o, width, segments=2, limit=30):
    m = o.modifiers.new('bevel', 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(limit)
    m.harden_normals = False
    return o


def subsurf(o, levels=1):
    m = o.modifiers.new('subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    return o


def boolean(o, cutter, op='DIFFERENCE'):
    m = o.modifiers.new('bool', 'BOOLEAN')
    m.object = cutter
    m.operation = op
    m.solver = 'EXACT'
    cutter.hide_set(True)
    cutter.hide_render = True
    return o


def apply_all(o):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError as e:
            print('modifier', m.name, 'failed on', o.name, e)
            o.modifiers.remove(m)


def delete(o):
    bpy.data.objects.remove(o, do_unlink=True)


# ---------------------------------------------------------------- primitives
def box(size, pos=(0, 0, 0), mat=None, bev=0.0, name='box', axis=None):
    """size : (sx, sy, sz) dans le repère du site."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)
    o = _obj_from_bm(bm, name, mat)
    if bev:
        bevel(o, bev, 2)
    return place(o, pos, axis=axis)


def cyl(r, length, pos=(0, 0, 0), axis=(0, 1, 0), mat=None, seg=24, r2=None, name='cyl', bev=0.0, cap=True):
    """Cylindre (ou tronc de cône si r2) centré sur pos, d'axe `axis`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=length)
    o = _obj_from_bm(bm, name, mat)
    if bev:
        bevel(o, bev, 2)
    smooth(o, 40)
    return place(o, pos, axis=axis)


def lathe(profile, pos=(0, 0, 0), axis=(0, 1, 0), mat=None, seg=32, name='lathe', angle=2 * math.pi):
    """Révolution d'un profil [(rayon, hauteur), ...] autour de l'axe."""
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, h)) for r, h in profile]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=angle, steps=seg, use_merge=abs(angle - 2 * math.pi) < 1e-6)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bm(bm, name, mat)
    smooth(o, 50)
    return place(o, pos, axis=axis)


def extrude(points2d, depth, pos=(0, 0, 0), axis=(0, 0, 1), mat=None, name='extr', bev=0.0, up=None):
    """Profil 2D (u, v) extrudé sur `depth` le long de axis (centré). Le profil est dans le
    plan local XY ; `up` (repère du site) oriente l'axe local Y."""
    bm = bmesh.new()
    vs = [bm.verts.new((u, v, -depth / 2)) for u, v in points2d]
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if f.normal.z > 0:
        f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bm(bm, name, mat)
    if bev:
        bevel(o, bev, 2)
    rot = None
    if up is not None:
        # on tourne autour de l'axe pour amener le Y local sur `up`
        q = Vector((0, 0, 1)).rotation_difference(TD(axis))
        y_now = q @ Vector((0, 1, 0))
        u = TD(up)
        u = (u - u.project(TD(axis))).normalized()
        ang = y_now.angle(u)
        if y_now.cross(u).dot(TD(axis)) < 0:
            ang = -ang
        rot = Quaternion(Vector((0, 0, 1)), ang)
    return place(o, pos, axis=axis, rot=rot)


def tube(points, r, mat=None, name='tube', seg=10, res=6, closed=False):
    """Tube passant par des points (repère du site), section ronde."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = max(1, seg // 4 - 1)
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS' if len(points) > 2 else 'POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        v = T(*p)
        sp.points[i].co = (v.x, v.y, v.z, 1)
    if len(points) > 2:
        sp.order_u = min(4, len(points))
        sp.use_endpoint_u = True
        sp.resolution_u = res
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        o.data.materials.append(mat)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    o.select_set(False)
    smooth(o, 60)
    return o


def torus(R, r, pos=(0, 0, 0), axis=(0, 1, 0), mat=None, seg=32, rseg=10, name='torus'):
    bm = bmesh.new()
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(seg):
        for j in range(rseg):
            a = i * rseg + j
            b = ((i + 1) % seg) * rseg + j
            c = ((i + 1) % seg) * rseg + (j + 1) % rseg
            d = i * rseg + (j + 1) % rseg
            bm.faces.new((bm.verts[a], bm.verts[b], bm.verts[c], bm.verts[d]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bm(bm, name, mat)
    smooth(o, 80)
    return place(o, pos, axis=axis)


def gear(r_root, r_tip, teeth, width, pos=(0, 0, 0), axis=(1, 0, 0), mat=None, name='gear', hole=0.0):
    pts = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        for f, rr in ((0.0, r_root), (0.2, r_tip), (0.5, r_tip), (0.7, r_root)):
            a = a0 + f * da
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    o = extrude(pts, width, pos, axis, mat, name)
    if hole:
        c = cyl(hole, width * 3, pos, axis, None, 24, name='cut')
        boolean(o, c)
        apply_all(o)
        delete(c)
    return o


def hexagon(r):
    return [(r * math.cos(math.pi / 6 + i * math.pi / 3), r * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]


def circle(r, n=24, cx=0, cy=0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rounded_rect(w, h, r, n=4):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def join(objs, name):
    objs = [o for o in objs if o is not None]
    for o in objs:
        apply_all(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    # applique la transformation : les sommets passent en coordonnées absolues
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.select_set(False)
    return o


# ---------------------------------------------------------------- pièces et fixations
class Part:
    """Une pièce du site : un nœud glTF nommé `id` portant extras.partId. Les maillages
    ajoutés sont fusionnés par matériau à l'export (moins d'appels de dessin)."""

    registry = []

    def __init__(self, pid, explode=(0, 0, 0)):
        self.id = pid
        self.explode = explode
        self.objs = []
        self.fasteners = []
        Part.registry.append(self)

    def add(self, *objs):
        for o in objs:
            if isinstance(o, (list, tuple)):
                self.add(*o)
            elif o is not None:
                self.objs.append(o)
        return objs[0] if len(objs) == 1 else objs

    def finish(self):
        root = bpy.data.objects.new(self.id, None)
        bpy.context.scene.collection.objects.link(root)
        root['partId'] = self.id
        root['explode'] = list(self.explode)
        by_mat = {}
        for o in self.objs:
            apply_all(o)
            key = o.data.materials[0].name if o.data.materials else '_'
            by_mat.setdefault(key, []).append(o)
        for i, (k, objs) in enumerate(by_mat.items()):
            j = join(objs, f'{self.id}.{k}')
            j.parent = root
        for f in self.fasteners:
            f.parent = root
        return root


def fastener(part, set_id, pos, d, kind='bolt', r=0.008, length=0.04, travel=None, idx=0, washer=True):
    """Vis / écrou / bouchon construit le long de son axe de dévissage `d` (repère du site).
    Exporté comme un nœud nommé `fx.<jeu>.<n>`, avec extras fx, kind, travel et dir."""
    zinc = M('zinc', 0xc9c4ae, 0.85, 0.3)
    dark = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
    ceram = M('ceramique', 0xf2efe6, 0.0, 0.25)
    black = M('noir', 0x1b1c1d, 0.1, 0.6)
    pieces = []
    if kind == 'spark':
        pieces.append(cyl(r * 0.55, length * 0.5, (0, 0, 0), (0, 1, 0), zinc, 10, name='filet'))
        pieces[-1].location = (0, 0, -length * 0.25)
        h = extrude(hexagon(r * 1.05), r * 1.0, (0, 0, 0), (0, 1, 0), zinc)
        h.location = (0, 0, r * 0.5)
        pieces.append(h)
        ins = lathe([(0, 0), (r * 0.75, 0), (r * 0.72, length * 0.15), (r * 0.6, length * 0.2)] + [(r * (0.6 if i % 2 else 0.68), length * (0.2 + 0.07 * i)) for i in range(1, 6)] + [(r * 0.35, length * 0.62), (0, length * 0.62)], (0, 0, 0), (0, 1, 0), ceram, 16)
        ins.location = (0, 0, r)
        pieces.append(ins)
        cap = cyl(r * 0.45, r * 1.2, (0, 0, 0), (0, 1, 0), black, 12)
        cap.location = (0, 0, r + length * 0.62)
        pieces.append(cap)
    elif kind == 'pin':
        p = cyl(r, length, (0, 0, 0), (0, 1, 0), zinc, 10)
        p.location = (0, 0, -length / 2)
        ring = torus(r * 1.8, r * 0.35, (0, 0, 0), (1, 0, 0), zinc, 16, 6)
        ring.location = (0, 0, r * 1.8)
        pieces += [p, ring]
    elif kind == 'plug':
        h = extrude(rounded_rect(r * 1.6, r * 1.6, r * 0.15, 1), r * 0.9, (0, 0, 0), (0, 1, 0), dark)
        h.location = (0, 0, r * 0.45 + r * 0.25)
        fl = cyl(r * 1.25, r * 0.25, (0, 0, 0), (0, 1, 0), dark, 20)
        fl.location = (0, 0, r * 0.125)
        th = cyl(r * 0.95, length, (0, 0, 0), (0, 1, 0), dark, 16)
        th.location = (0, 0, -length / 2)
        pieces += [h, fl, th]
    elif kind == 'screw':
        hd = lathe([(0, 0), (r, 0), (r, r * 0.25), (r * 0.8, r * 0.55), (0, r * 0.6)], (0, 0, 0), (0, 1, 0), zinc, 20)
        slot = box((r * 1.6, r * 0.5, r * 0.22), (0, 0, 0), black)
        slot.location = (0, 0, r * 0.55)
        th = cyl(r * 0.5, length, (0, 0, 0), (0, 1, 0), zinc, 10)
        th.location = (0, 0, -length / 2)
        pieces += [hd, slot, th]
    else:  # bolt / nut
        hh = r * (0.8 if kind == 'nut' else 0.7)
        h = extrude(hexagon(r), hh, (0, 0, 0), (0, 1, 0), zinc, bev=r * 0.08)
        h.location = (0, 0, hh / 2 + (r * 0.18 if washer else 0))
        pieces.append(h)
        if washer:
            w = cyl(r * 1.45, r * 0.18, (0, 0, 0), (0, 1, 0), zinc, 20)
            w.location = (0, 0, r * 0.09)
            pieces.append(w)
        th = cyl(r * 0.55, length, (0, 0, 0), (0, 1, 0), zinc, 10)
        th.location = (0, 0, -length / 2 + (hh + r * 0.6 if kind == 'nut' else 0))
        pieces.append(th)
    for p in pieces:
        if not p.name.startswith('torus'):
            p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion()
    o = join(pieces, f'fx.{set_id}.{idx}')
    place(o, pos, axis=d)
    o['fx'] = set_id
    o['kind'] = kind
    o['travel'] = travel if travel is not None else length + 0.05
    o['dir'] = list(Vector(d).normalized())
    part.fasteners.append(o)
    return o


def fasteners(part, set_id, specs, **kw):
    for i, (p, d) in enumerate(specs):
        fastener(part, set_id, p, d, idx=i, **kw)


def export(path):
    roots = [p.finish() for p in Part.registry]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', export_extras=True, export_yup=True,
        export_apply=True, export_normals=True, export_materials='EXPORT',
        export_draco_mesh_compression_enable=False,
    )
    tris = 0
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
    print(f'export {path}: {len(roots)} pièces, {tris} triangles')
