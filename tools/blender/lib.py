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
    elif kind == 'fuse':
        c = cyl(r * 0.6, length, (0, 0, 0), (0, 1, 0), ceram, 12)
        c.location = (0, 0, 0)
        pieces.append(c)
        for k in (-1, 1):
            e = cyl(r * 0.68, r * 0.9, (0, 0, 0), (0, 1, 0), zinc, 12)
            e.location = (0, 0, k * length / 2)
            pieces.append(e)
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


# ---------------------------------------------------------------- surfaces de carrosserie
def grid(P, mat=None, name='grid', close_i=False, close_j=False, keep=None, smooth_angle=50):
    """Surface à partir d'une grille de points P[i][j] (repère du site). keep(i, j) filtre les
    quadrilatères. Les normales sont laissées dans l'ordre de la grille (voir orient)."""
    bm = bmesh.new()
    ni, nj = len(P), len(P[0])
    V = [[bm.verts.new(T(*P[i][j])) for j in range(nj)] for i in range(ni)]
    for i in range(ni if close_i else ni - 1):
        for j in range(nj if close_j else nj - 1):
            if keep and not keep(i, j):
                continue
            i2, j2 = (i + 1) % ni, (j + 1) % nj
            bm.faces.new((V[i][j], V[i2][j], V[i2][j2], V[i][j2]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    o = _obj_from_bm(bm, name, mat)
    smooth(o, smooth_angle)
    return o


def orient(o, inside=(0.0, 0.9, 0.0)):
    """Oriente les normales vers l'extérieur (loin du point `inside`, repère du site)."""
    me = o.data
    c = T(*inside)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    score = sum((f.calc_center_median() - c).dot(f.normal) * f.calc_area() for f in bm.faces)
    if score < 0:
        for f in bm.faces:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    return o


def solidify(o, t, offset=-1.0):
    m = o.modifiers.new('solid', 'SOLIDIFY')
    m.thickness = t
    m.offset = offset
    m.use_even_offset = True
    m.use_quality_normals = True
    apply_all(o)
    return o


def prism(outline, axis, z0, z1, name='cut'):
    """Prisme fermé : contour 2D extrudé de z0 à z1 le long d'un axe du site.
    axis 'z' : contour en (x, y) ; 'x' : contour en (z, y) ; 'y' : contour en (x, z)."""
    bm = bmesh.new()

    def P3(u, v, w):
        if axis == 'z':
            return T(u, v, w)
        if axis == 'x':
            return T(w, v, u)
        return T(u, w, v)
    a = [bm.verts.new(P3(u, v, z0)) for u, v in outline]
    b = [bm.verts.new(P3(u, v, z1)) for u, v in outline]
    n = len(outline)
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj_from_bm(bm, name, None)


def cut(o, cutter, op='DIFFERENCE', keep_cutter=False):
    m = o.modifiers.new('bool', 'BOOLEAN')
    m.object = cutter
    m.operation = op
    m.solver = 'EXACT'
    apply_all(o)
    if not keep_cutter:
        delete(cutter)
    smooth(o, 40)
    return o


def copy(o, name=None):
    c = o.copy()
    c.data = o.data.copy()
    bpy.context.scene.collection.objects.link(c)
    if name:
        c.name = name
    return c


def mirror_z(o, name=None):
    """Copie symétrique par rapport au plan médian (z → -z du site)."""
    c = copy(o, name)
    apply_all(c)
    me = c.data
    for v in me.vertices:
        v.co.y = -v.co.y
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    me.update()
    return c


def outline_round(pts, r, n=5):
    """Arrondit les angles d'un polygone 2D (rayon r, ou liste de rayons par sommet)."""
    out = []
    m = len(pts)
    rs = r if isinstance(r, (list, tuple)) else [r] * m
    for i in range(m):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % m])
        ri = rs[i]
        if ri <= 0:
            out.append(tuple(p1))
            continue
        d1, d2 = (p0 - p1).normalized(), (p2 - p1).normalized()
        ang = d1.angle(d2)
        t = min(ri / math.tan(ang / 2), (p0 - p1).length * 0.49, (p2 - p1).length * 0.49)
        a, b = p1 + d1 * t, p1 + d2 * t
        for k in range(n + 1):
            s = k / n
            q = (a * (1 - s) + p1 * s) * (1 - s) + (p1 * (1 - s) + b * s) * s   # Bézier quadratique
            out.append((q.x, q.y))
    return out


def M_img(name, png, metal=0.0, rough=0.5):
    """Matériau à texture (image PNG intégrée au glb)."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png)
    tex.image.pack()
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    _mats[name] = m
    return m


def quad(center, w, h, normal, mat, name='quad'):
    """Rectangle texturé w × h (u horizontal, v vers le haut), face tournée vers `normal`
    (axe du site : (±1, 0, 0) ou (0, 0, ±1))."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    nx, _, nz = normal
    # axe horizontal du rectangle vu de face (vers la droite de l'observateur)
    ux, uz = (0, -1) if nx > 0 else (0, 1) if nx < 0 else (1, 0) if nz > 0 else (-1, 0)
    cx, cy, cz = center
    corners = [(-w / 2, -h / 2, 0, 0), (w / 2, -h / 2, 1, 0), (w / 2, h / 2, 1, 1), (-w / 2, h / 2, 0, 1)]
    vs = [bm.verts.new(T(cx + ux * a, cy + b, cz + uz * a)) for a, b, _, _ in corners]
    f = bm.faces.new(vs)
    for loop, (_, _, u, v) in zip(f.loops, corners):
        loop[uv].uv = (u, v)
    o = _obj_from_bm(bm, name, mat)
    return o


def uv_box(o, scale=1.0):
    """UV par projection cubique (coordonnées monde × scale) : textures répétées (tissus…)."""
    bpy.context.view_layer.update()
    mw = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        n = mw.to_3x3() @ f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for lp in f.loops:
            w = mw @ lp.vert.co
            lp[uv].uv = (w[a] * scale, w[b] * scale)
    bm.to_mesh(o.data)
    bm.free()
    return o


# ---------------------------------------------------------------- mécanique : pignons, roulements
def toothed(teeth, r_pitch, width, pos=(0, 0, 0), axis=(1, 0, 0), mat=None, hole=0.0, helix=0.0, taper=1.0,
            depth=None, name='pignon', phase=0.0):
    """Pignon taillé construit directement en maillage (sans booléen) : `teeth` dents sur le
    rayon primitif `r_pitch`, alésage `hole`. helix : angle d'hélice (rad) des dentures
    hélicoïdales ; taper : rapport des rayons face arrière / face avant (pignons coniques,
    couronne). La face avant (taper 1) est du côté -axis."""
    m = 2 * r_pitch / teeth
    tip, root = r_pitch + (depth or m) * 0.9, r_pitch - (depth or m) * 1.1
    prof = []
    for i in range(teeth):
        for f, rr in ((0.0, root), (0.14, root), (0.34, tip), (0.62, tip), (0.82, root)):
            prof.append((2 * math.pi * (i + f) / teeth + phase, rr))
    twist = width * math.tan(helix) / r_pitch if helix else 0.0
    bm = bmesh.new()
    n = len(prof)
    rings = []
    for z, sc, tw in ((-width / 2, 1.0, 0.0), (width / 2, taper, twist)):
        outer = [bm.verts.new((r * sc * math.cos(a + tw), r * sc * math.sin(a + tw), z)) for a, r in prof]
        if hole:
            inner = [bm.verts.new((hole * math.cos(a + tw), hole * math.sin(a + tw), z)) for a, _ in prof]
        else:
            inner = [bm.verts.new((0, 0, z))]
        rings.append((outer, inner))
    for k, (outer, inner) in enumerate(rings):
        for i in range(n):
            j = (i + 1) % n
            if hole:
                q = (outer[i], outer[j], inner[j], inner[i])
            else:
                q = (outer[i], outer[j], inner[0])
            bm.faces.new(q if k else q[::-1])
    (o0, i0), (o1, i1) = rings
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((o0[i], o0[j], o1[j], o1[i]))
        if hole:
            bm.faces.new((i0[j], i0[i], i1[i], i1[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj_from_bm(bm, name, mat)
    smooth(o, 30)
    return place(o, pos, axis=axis)


def sphere(r, pos=(0, 0, 0), mat=None, seg=10, rings=6, name='bille'):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    o = _obj_from_bm(bm, name, mat)
    smooth(o, 80)
    return place(o, pos)


def ball_bearing(r_in, r_out, width, pos, axis, race_mat, ball_mat=None, balls=None, seg=32):
    """Roulement à billes : bagues intérieure et extérieure, billes visibles entre les deux."""
    rb = (r_out - r_in) * 0.28
    rm = (r_in + r_out) / 2
    w = width / 2
    out = [lathe([(r_in, -w), (rm - rb * 0.7, -w), (rm - rb * 0.7, w), (r_in, w)], pos, axis, race_mat, seg, 'bague-int'),
           lathe([(rm + rb * 0.7, -w), (r_out, -w), (r_out, w), (rm + rb * 0.7, w)], pos, axis, race_mat, seg, 'bague-ext')]
    a = Vector(axis).normalized()
    u = a.cross(Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))).normalized()
    v = a.cross(u)
    nb = balls or max(7, int(2 * math.pi * rm / (rb * 2.6)))
    for k in range(nb):
        t = 2 * math.pi * k / nb
        p = Vector(pos) + (u * math.cos(t) + v * math.sin(t)) * rm
        out.append(sphere(rb, tuple(p), ball_mat or race_mat, 8, 5))
    return out


def roller_bearing(r_in, r_out, width, pos, axis, race_mat, roller_mat=None, cone=0.25, rollers=None, seg=32):
    """Roulement à rouleaux coniques : cône (bague intérieure), cuvette et rouleaux inclinés.
    La grande base des rouleaux est du côté +axis."""
    w = width / 2
    rm = (r_in + r_out) / 2
    rr = (r_out - r_in) * 0.24
    dr = width * math.tan(cone) / 2
    out = [lathe([(r_in, -w), (rm - rr - dr, -w), (rm - rr + dr, w * 0.8), (r_in, w)], pos, axis, race_mat, seg, 'cone'),
           lathe([(rm + rr - dr, -w), (r_out, -w), (r_out, w), (rm + rr + dr, w)], pos, axis, race_mat, seg, 'cuvette')]
    a = Vector(axis).normalized()
    u = a.cross(Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))).normalized()
    v = a.cross(u)
    nr = rollers or max(9, int(2 * math.pi * rm / (rr * 2.4)))
    for k in range(nr):
        t = 2 * math.pi * k / nr
        rad = u * math.cos(t) + v * math.sin(t)
        p0 = Vector(pos) + rad * (rm - dr) - a * w * 0.85
        p1 = Vector(pos) + rad * (rm + dr) + a * w * 0.85
        c = cyl(rr * 0.8, (p1 - p0).length, tuple((p0 + p1) / 2), tuple(p1 - p0), roller_mat or race_mat, 8, r2=rr)
        out.append(c)
    return out


def splined(r, length, pos, axis, mat, splines=18, name='cannelures'):
    """Portée cannelée (arbre ou moyeu)."""
    return toothed(splines, r, length, pos, axis, mat, depth=r * 0.12, name=name)


def circlip(r, pos, axis, mat, t=0.0012, name='circlip'):
    """Anneau élastique ouvert, avec ses deux oreilles."""
    o = lathe([(r, -t / 2), (r + t * 1.6, -t / 2), (r + t * 1.6, t / 2), (r, t / 2)], pos, axis, mat, 24, name, angle=math.radians(330))
    return o
