# Caisse de la Renault 4 GTL (berline R 1128) : coque, ailes, capot, portes, hayon, vitrages,
# pare-chocs, calandre, projecteurs, feux, essuie-glace.
# Lancer : python3 tools/blender/caisse.py   →   models/caisse.glb
#
# Cotes de la RTA : longueur hors tout 3 668 mm, largeur 1 509 mm, hauteur à vide 1 550 mm,
# porte-à-faux avant 528 mm, arrière 691 (droit) / 739 mm (gauche), empattement 2 449 / 2 401 mm
# (« Dimensions et poids », p.79). Silhouette relevée sur la photo de profil de la GTL (p. I) et sur
# les plans cotés des versions break et pick-up, dont l'avant est identique (p. XVIII et XIX) :
# ligne de ceinture 1 040 mm, haut des ailes 1 045 → 855 mm, passages de roue AV Ø 700 mm,
# hayon incliné, projecteurs Ø 168 mm à 670 mm du sol, pare-chocs entre 350 et 450 mm.
# Ce que la RTA ne cote pas (rayons, galbes, épaisseurs) est estimé d'après ces vues.
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (M, M_img, Part, T, box, quad, copy, cut, cyl, export, extrude, fastener, fasteners, grid, lathe,  # noqa: E402
                 mirror_z, orient, outline_round, prism, reset, solidify, torus, tube)

reset()

OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'caisse.glb')

peinture = M('peinture', 0xe9e6dc, 0.05, 0.38)
interieur = M('tole-interieure', 0xd9d5c8, 0.05, 0.6)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
joint = M('joint-vitre', 0x141516, 0.0, 0.7)
vitre = M('vitre', 0x9cc0d3, 0.3, 0.05, alpha=0.28)
gris_gtl = M('plastique-gris', 0x6a6d6f, 0.0, 0.7)
plastique_noir = M('plastique-noir', 0x232425, 0.0, 0.65)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
garniture = M('garniture-porte', 0x47413c, 0.0, 0.9)
cabochon_blanc = M('cabochon-blanc', 0xf4f1e4, 0.1, 0.1, alpha=0.75)
cabochon_rouge = M('cabochon-rouge', 0xb8302a, 0.1, 0.15, alpha=0.85)
cabochon_orange = M('cabochon-orange', 0xe07a2b, 0.1, 0.15, alpha=0.85)
reflecteur = M('reflecteur', 0xe8e9ea, 1.0, 0.08)


def plate_png(path, bg, text='1234 RT 33'):
    """Plaque minéralogique FNI (blanche à l'avant, jaune à l'arrière), texte fictif."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (520, 110), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((3, 3, 516, 106), outline=(20, 20, 20), width=5)
    font = None
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f):
            font = ImageFont.truetype(f, 78)
            break
    d.text((260, 58), text, fill=(15, 15, 15), font=font, anchor='mm')
    im.save(path)
    return path


_tmp = tempfile.mkdtemp(prefix='plaques-')
os.makedirs(_tmp, exist_ok=True)
plaque_m = M_img('plaque', plate_png(os.path.join(_tmp, 'av.png'), (241, 239, 230)))
plaque_j = M_img('plaque-jaune', plate_png(os.path.join(_tmp, 'ar.png'), (232, 198, 58)))
support = M('support-plaque', 0x202122, 0.0, 0.7)

GAP = 0.004          # jeu entre ouvrants
SKIN = 0.0012        # épaisseur de tôle (visuelle)


# =====================================================================================
# Lignes de caisse (repère du site, côté droit z > 0)
# =====================================================================================
def interp(pts, x):
    """Interpolation linéaire par morceaux sur une liste [(x, y)] triée."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def smooth_interp(pts, x):
    """Catmull-Rom sur une liste [(x, y)] triée (courbes plus douces que interp)."""
    n = len(pts)
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for k in range(n - 1):
        if pts[k][0] <= x <= pts[k + 1][0]:
            break
    p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, n - 1)]
    t = (x - p1[0]) / (p2[0] - p1[0])
    m1 = (p2[1] - p0[1]) / (p2[0] - p0[0]) * (p2[0] - p1[0])
    m2 = (p3[1] - p1[1]) / (p3[0] - p1[0]) * (p2[0] - p1[0])
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p1[1] + (t3 - 2 * t2 + t) * m1 + (-2 * t3 + 3 * t2) * p2[1] + (t3 - t2) * m2


X_NOSE = 1.762       # face avant (porte-à-faux 528 mm au pare-chocs : 1,834)
BELT = 1.040         # ligne de ceinture
R_SH = 0.022         # rayon de l'épaulement de ceinture
SILL_IN = 0.030      # retrait de la ceinture vers le vitrage
Y_BOT = 0.385        # bas de caisse (dessous des portes)
Y_ROOF = 1.500       # arête du pavillon (gouttières)
CROWN = 0.048        # bombé du pavillon (sommet 1 548 mm)

FENDER_TOP = [(0.60, 1.046), (1.00, 0.985), (1.42, 0.935), (1.62, 0.897), (1.72, 0.858), (1.80, 0.84)]
REAR = [(0.30, -1.772), (0.49, -1.755), (0.65, -1.722), (0.833, -1.668), (1.056, -1.585), (1.32, -1.470), (1.50, -1.372)]


def W(x):
    """Demi-largeur en plan (1 509 mm hors tout)."""
    w = 0.7545
    if x > 1.45:
        w -= 0.036 * ((x - 1.45) / 0.31) ** 2
    if x < -1.50:
        w -= 0.028 * ((-1.50 - x) / 0.27) ** 2
    return w


def zside(x, y):
    """Flanc sous la ceinture : léger galbe vertical, bas de caisse roulé vers l'intérieur."""
    z = W(x) * (1 - 0.012 * ((y - 0.74) / 0.30) ** 2)
    if y < 0.45:
        z -= 0.020 * ((0.45 - y) / 0.065) ** 2
    return z


def x_rear(y):
    return smooth_interp(REAR, y)


def x_ws(y):
    """Arête avant du vitrage (montant de pare-brise), incliné de 33°."""
    return 0.648 - (y - 1.03) * 0.66


def fender_top(x):
    return smooth_interp(FENDER_TOP, x)


def z_glass(y):
    """Flanc du pavillon (vitres) : rentré de 30 mm à la ceinture, 665 mm sous le pavillon."""
    z0 = zside(0, BELT - R_SH) - SILL_IN
    return z0 + (0.665 - z0) * (y - BELT) / (Y_ROOF - BELT)


def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def half_ring(y, z_of_x, xr, rc, x_front, front_face=None, ns=110, nc=12, nr=18, nf=14, rcf=0.04):
    """Demi-contour en plan (x, z) à la hauteur y, de l'avant vers l'axe arrière, avec les normales
    sortantes. front_face : None (bord libre à x_front) ou demi-largeur de la face avant (pare-brise)."""
    pts = []
    if front_face is not None:
        zf = z_of_x(x_front) - rcf
        for z in lin(0, zf, nf)[:-1]:
            pts.append(((x_front, z), (1, 0)))
        cx, cz = x_front - rcf, zf
        for a in lin(0, math.pi / 2, 8)[:-1]:
            pts.append(((cx + rcf * math.cos(a), cz + rcf * math.sin(a)), (math.cos(a), math.sin(a))))
        x0 = cx
    else:
        x0 = x_front
    for x in lin(x0, xr + rc, ns):
        pts.append(((x, z_of_x(x)), (0, 1)))
    cx, cz = xr + rc, z_of_x(xr + rc) - rc
    for a in lin(math.pi / 2, math.pi, nc)[1:]:
        pts.append(((cx + rc * math.cos(a), cz + rc * math.sin(a)), (math.cos(a), math.sin(a))))
    for z in lin(cz, 0, nr)[1:]:
        pts.append(((xr, z), (-1, 0)))
    return pts


RC_REAR = 0.11


def lower_rows():
    """Rangées du flanc bas : du bas de caisse à l'épaulement de ceinture."""
    rows = [(y, 0.0) for y in lin(Y_BOT, BELT - R_SH, 34)]
    for k in range(1, 7):
        th = k / 6 * math.pi / 2
        rows.append((BELT - R_SH + R_SH * math.sin(th), R_SH * (1 - math.cos(th))))
    rows.append((BELT, SILL_IN))
    return rows


def build_lower():
    P = []
    rows = lower_rows()
    for y, inset in rows:
        yy = min(y, BELT - R_SH)
        ring = half_ring(yy, lambda x: zside(x, yy), x_rear(yy), RC_REAR, 1.12)
        P.append([(x - nx * inset, y, z - nz * inset) for (x, z), (nx, nz) in ring])
    return P


def build_greenhouse():
    P = []
    for y in lin(BELT, Y_ROOF, 30):
        ring = half_ring(y, lambda x: z_glass(y), x_rear(y) + SILL_IN, RC_REAR, x_ws(y), front_face=True)
        P.append([(x, y, z) for (x, z), _ in ring])
    return P, ring


def build_roof(edge):
    """Pavillon : du contour du haut des vitres vers le centre, bombé de 48 mm."""
    full = [p for p, _ in edge] + [(x, -z) for (x, z), _ in reversed(edge[1:-1])]
    xf, xr = edge[0][0][0], edge[-1][0][0]
    cx = (xf + xr) / 2
    P = []
    for s in lin(1.0, 0.0, 16):
        row = []
        for x, z in full:
            px, pz = cx + (x - cx) * s, z * s
            ends = min((xf - px) / 0.18, (px - xr) / 0.22, 1.0)
            ends = max(ends, 0.0)
            y = Y_ROOF + CROWN * (1 - (pz / 0.665) ** 2) * (3 * ends ** 2 - 2 * ends ** 3) + 0.004 * (1 - s)
            row.append((px, y, pz))
        P.append(row)
    return grid(P, peinture, 'pavillon', close_j=True)


# =====================================================================================
# Coque
# =====================================================================================
lower_r = orient(grid(build_lower(), peinture, 'flanc'))
gh_pts, gh_top = build_greenhouse()
upper_r = orient(grid(gh_pts, peinture, 'pavillon-flanc'))
roof = orient(build_roof(gh_top), inside=(-0.5, 1.0, 0.0))

import bmesh  # noqa: E402
import bpy  # noqa: E402


def join_mirror(o, name):
    """Joint la moitié droite et sa symétrique (soudure dans le plan médian)."""
    m = mirror_z(o)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    m.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.join()
    o.name = name
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(o.data)
    bm.free()
    return o


def poly_glass(pts, mat=vitre, name='vitre'):
    """Vitre plane : polygone 3D (repère du site)."""
    bm = bmesh.new()
    vs = [bm.verts.new(T(*p)) for p in pts]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def seal(pts, r=0.006, mat=joint, name='joint'):
    return tube(pts + pts[:1], r, mat, name, seg=8, res=2)


def side_pts(outline, zf, inset=0.0):
    """Contour (x, y) posé sur une surface de flanc z = zf(x, y), côté droit."""
    return [(x, y, zf(x, y) - inset) for x, y in outline]


lower = join_mirror(lower_r, 'flanc')
upper = join_mirror(upper_r, 'vitrage-flanc')
for o in (lower, upper, roof):
    orient(o, inside=(-0.4, 0.9, 0.0))
    solidify(o, SKIN)


# ---------------------------------------------------------------- ailes avant (boulonnées)
RCF = 0.10
R_FS = 0.030


def HW(x):
    """Demi-largeur du capot."""
    return W(x) - 0.150


def fender_half():
    path = []
    xs = lin(0.56, X_NOSE - RCF, 70)
    for x in xs:
        path.append((x, None, (0.0, 1.0), 1.0))
    cx = X_NOSE - RCF
    for k, a in enumerate(lin(math.pi / 2, 0.0, 12)[1:]):
        path.append((cx, a, (math.cos(a), math.sin(a)), 1.0 - (k + 1) / 11 * 0.8))
    P = []
    for x0, a, (nx, nz), lscale in path:
        col = []
        xb = x0 if a is None else cx + RCF * math.cos(a)
        yt = fender_top(xb)
        yb = 0.40 + 0.07 * max(0.0, (xb - 1.50) / 0.26) ** 1.5
        for y in lin(yb, yt - R_FS, 26):
            if a is None:
                col.append((x0, y, zside(x0, y)))
            else:
                rz = RCF + zside(cx, y) - W(cx)
                cz = W(cx) - RCF
                col.append((cx + rz * math.cos(a), y, cz + rz * math.sin(a)))
        bx, by, bz = col[-1]
        for k in range(1, 7):
            th = k / 6 * math.pi / 2
            d = R_FS * (1 - math.cos(th))
            col.append((bx - nx * d, yt - R_FS + R_FS * math.sin(th), bz - nz * d))
        tx, ty, tz = col[-1]
        flat = (bz - R_FS - HW(xb) - GAP) * lscale if a is None else (zside(cx, yt) - R_FS - HW(xb) - GAP) * lscale
        for k in range(1, 6):
            d = flat * k / 5
            col.append((tx - nx * d, ty, tz - nz * d))
        P.append(col)
    return P


fender_r = orient(grid(fender_half(), peinture, 'aile'), inside=(1.2, 0.6, 0.3))
fender_l = mirror_z(fender_r, 'aile-g')
bpy.ops.object.select_all(action='DESELECT')
fender_r.select_set(True)
fender_l.select_set(True)
bpy.context.view_layer.objects.active = fender_r
bpy.ops.object.join()
fender = fender_r
fender.name = 'ailes'
solidify(fender, SKIN)

# séparation aile / pied avant : ligne oblique du haut de l'aile au passage de roue (photo p. I)
SLANT = [(0.62, 1.046), (1.085, 0.38)]


def slant_outline(off, front=True):
    (x0, y0), (x1, y1) = SLANT
    if front:
        return [(x0 + off, y0 + 0.08), (x1 + off + 0.05 * 0.70, y1 - 0.05), (2.2, y1 - 0.05), (2.2, y0 + 0.08)]
    return [(x0 + off, y0 + 0.08), (x1 + off + 0.05 * 0.70, y1 - 0.05), (0.2, y1 - 0.05), (0.2, y0 + 0.08)]


cut(lower, prism(slant_outline(-GAP / 2), 'z', -1.0, 1.0))
cut(fender, prism(slant_outline(GAP / 2, False), 'z', -1.0, 1.0))

# passages de roue (avant Ø 700 mm au sommet, arrière plus bas et plus large)
ARCH_F = (1.31, 0.35, 0.350)
ARCH_R = (-1.125, 0.27, 0.370)


def arch_cut(o, a, grow=0.0):
    x, y, r = a
    c = cyl(r + grow, 2.0, (x, y, 0), (0, 0, 1), None, 72, name='arche')
    cut(o, c)


arch_cut(fender, ARCH_F)
arch_cut(lower, ARCH_F)
arch_cut(lower, ARCH_R)
# derrière la roue arrière, le bas de caisse remonte (photo p. I) ; la jupe arrière reste basse
for s in (1, -1):
    cut(lower, prism([(-1.40, 0.30), (-1.40, 0.445), (-2.0, 0.445), (-2.0, 0.30)], 'z', *((0.625, 1.0) if s > 0 else (-1.0, -0.625))))

# ---------------------------------------------------------------- portes
FD_FRONT = [(0.700, 0.79), (0.692, 0.86), (0.668, 0.935), (0.640, 0.995), (0.615, 1.045)]


def front_door_outline():
    pts = [(0.700, 0.30)] + FD_FRONT
    for y in lin(1.06, 1.470, 6):
        pts.append((x_ws(y) - 0.072, y))
    pts += [(-0.205, 1.470), (-0.205, 0.30)]
    return pts


def rear_door_outline():
    return [(-0.225, 0.30), (-0.225, 1.470), (-0.886, 1.470), (-0.832, 1.040), (-0.800, 0.30)]


def offset_outline(pts, d):
    """Décale un contour 2D vers l'extérieur (d > 0) ou l'intérieur (d < 0)."""
    from mathutils import Vector
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n1, n2 = Vector((e1.y, -e1.x)) * sgn, Vector((e2.y, -e2.x)) * sgn
        b = (n1 + n2)
        b = b.normalized() if b.length > 1e-6 else n1
        k = d / max(b.dot(n1), 0.3)
        q = p1 + b * k
        out.append((q.x, q.y))
    return out


DOORS = [('portes-avd', front_door_outline(), 1), ('portes-ard', rear_door_outline(), 1),
         ('portes-avg', front_door_outline(), -1), ('portes-arg', rear_door_outline(), -1)]
door_skins = {}
for name, ol, s in DOORS:
    zr = (0.40, 1.0) if s > 0 else (-1.0, -0.40)
    skins = []
    for src in (lower, upper):
        d = copy(src, name)
        cut(d, prism(offset_outline(ol, -GAP / 2), 'z', *zr), 'INTERSECT')
        skins.append(d)
    door_skins[name] = skins
    for src in (lower, upper):
        cut(src, prism(offset_outline(ol, GAP / 2), 'z', *zr))

# la porte arrière est échancrée par le passage de roue
for name in ('portes-ard', 'portes-arg'):
    for d in door_skins[name]:
        arch_cut(d, ARCH_R, GAP)

# vitres des portes (coulissantes) et vitres de custode
FD_WIN = outline_round([(x_ws(1.075) - 0.105, 1.075), (-0.178, 1.075), (-0.178, 1.445), (x_ws(1.445) - 0.105, 1.445)], 0.035)
RD_WIN = outline_round([(-0.252, 1.075), (-0.818, 1.075), (-0.858, 1.445), (-0.252, 1.445)], 0.035)
Q_WIN = outline_round([(-0.928, 1.080), (-1.335, 1.080), (-1.272, 1.440), (-0.946, 1.440)], [0.035, 0.05, 0.06, 0.035])
for name, _, s in DOORS:
    win = FD_WIN if 'av' in name else RD_WIN
    zr = (0.5, 1.0) if s > 0 else (-1.0, -0.5)
    cut(door_skins[name][1], prism(win, 'z', *zr))
for s in (1, -1):
    cut(upper, prism(Q_WIN, 'z', *((0.5, 1.0) if s > 0 else (-1.0, -0.5))))

# pare-brise (plan incliné entre les montants)
WS_OUT = outline_round([(-0.612, 1.065), (0.612, 1.065), (0.585, 1.468), (-0.585, 1.468)], 0.05)
cut(upper, prism(WS_OUT, 'x', 0.20, 0.95))

# hayon : découpé dans la face arrière
HATCH = outline_round([(-0.598, 0.455), (0.598, 0.455), (0.590, 1.04), (0.540, 1.478), (-0.540, 1.478), (-0.590, 1.04)], [0.05, 0.05, 0.0, 0.10, 0.10, 0.0])
hatch_skins = []
for src in (lower, upper):
    h = copy(src, 'hayon')
    cut(h, prism(offset_outline(HATCH, -GAP / 2), 'x', -2.1, -1.25), 'INTERSECT')
    hatch_skins.append(h)
    cut(src, prism(offset_outline(HATCH, GAP / 2), 'x', -2.1, -1.25))
HATCH_WIN = outline_round([(-0.535, 1.085), (0.535, 1.085), (0.492, 1.432), (-0.492, 1.432)], 0.06)
cut(hatch_skins[1], prism(HATCH_WIN, 'x', -2.1, -1.25))
cut(hatch_skins[0], prism(HATCH_WIN, 'x', -2.1, -1.25))


# ---------------------------------------------------------------- capot (articulé à l'avant)
def hood_points():
    xs = lin(0.672, 1.680, 56)
    cols = []
    for v in lin(-1.0, 1.0, 31):
        col = []
        for x in xs:
            y = fender_top(x) + 0.003 + 0.034 * (1 - v * v)
            col.append((x, y, v * HW(x)))
        x1, y1 = xs[-1], col[-1][1]
        ylow = 0.818 + 0.032 * v * v
        p0, p1, p2, p3 = (x1, y1), (1.735, y1), (X_NOSE - 0.003, y1 - 0.025), (X_NOSE - 0.003, ylow)
        for k in range(1, 15):
            t = k / 14
            bx = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            by = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
            col.append((bx, by, v * HW(min(bx, X_NOSE - 0.02))))
        cols.append(col)
    return cols


hood = orient(grid(hood_points(), peinture, 'capot'), inside=(1.2, 0.6, 0.0))
solidify(hood, SKIN * 1.5)
hood_frame = []
for s in (1, -1):   # renforts sous le capot et charnières avant
    hood_frame.append(tube([(0.70, fender_top(0.70) - 0.004, s * 0.52), (1.20, fender_top(1.2) - 0.004, s * 0.55), (1.66, fender_top(1.66) - 0.004, s * 0.52)], 0.009, interieur, 'renfort'))
    hood_frame.append(box((0.04, 0.025, 0.03), (1.725, 0.83, s * 0.45), acier_noir, 0.004, 'charniere'))
    hood_frame.append(cyl(0.007, 0.05, (1.735, 0.82, s * 0.45), (0, 0, 1), acier, 12, name='axe'))
hood_frame.append(tube([(0.70, fender_top(0.70) + 0.005, -0.40), (0.70, fender_top(0.70) + 0.012, 0.0), (0.70, fender_top(0.70) + 0.005, 0.40)], 0.008, interieur, 'renfort-ar'))
hood_frame.append(box((0.03, 0.02, 0.05), (0.69, fender_top(0.69) - 0.005, 0), acier_noir, 0.003, 'gache'))   # gâche de serrure

# ---------------------------------------------------------------- face avant, auvent, tablier, ailes intérieures
TABLIER_X = 0.700
front_bits = []
fp = box((0.003, 0.40, 1.28), (X_NOSE - 0.008, 0.625, 0), peinture, 0, 'face-avant')
for s in (1, -1):
    cut(fp, cyl(0.078, 0.2, (X_NOSE, 0.671, s * 0.417), (1, 0, 0), None, 40, name='trou-phare'))
cut(fp, prism(outline_round([(-0.30, 0.60), (0.30, 0.60), (0.30, 0.75), (-0.30, 0.75)], 0.01), 'x', X_NOSE - 0.1, X_NOSE + 0.1))
front_bits.append(fp)
front_bits.append(box((0.05, 0.003, 1.26), (X_NOSE - 0.03, 0.826, 0), peinture, 0, 'traverse-sup'))
front_bits.append(box((0.04, 0.04, 1.20), (X_NOSE - 0.025, 0.44, 0), peinture, 0.008, 'traverse-inf'))
# auvent avec grille d'entrée d'air
front_bits.append(box((0.046, 0.010, 1.40), (0.650, 1.034, 0), peinture, 0.003, 'auvent'))
front_bits.append(box((0.030, 0.006, 0.64), (0.652, 1.040, 0), plastique_noir, 0.002, 'grille-auvent'))
for k in range(11):
    front_bits.append(box((0.026, 0.004, 0.006), (0.652, 1.043, -0.30 + k * 0.06), peinture, 0, 'lame'))
# tablier (cloison moteur / habitacle), incliné vers l'auvent
tab = extrude([(TABLIER_X, 0.38), (TABLIER_X, 0.86), (0.655, 1.028), (0.640, 1.028), (TABLIER_X - 0.006, 0.86), (TABLIER_X - 0.006, 0.38)], 1.12, (0, 0, 0), (0, 0, 1), peinture, 'tablier', up=(0, 1, 0))
front_bits.append(tab)
# ailes intérieures et passages de roue
for s in (1, -1):
    wall = extrude([(TABLIER_X, 0.40), (1.745, 0.40), (1.745, 0.80), (1.60, fender_top(1.60) - 0.03), (1.0, fender_top(1.0) - 0.03), (TABLIER_X, fender_top(TABLIER_X) - 0.03)], 0.003, (0, 0, s * 0.556), (0, 0, 1), peinture, 'aile-int', up=(0, 1, 0))
    cut(wall, cyl(0.36, 0.2, (ARCH_F[0], ARCH_F[1], s * 0.556), (0, 0, 1), None, 64, name='arche'))
    front_bits.append(wall)
for s in (1, -1):
    for (ax, ay, ar), z0, z1, mat in ((ARCH_F, 0.556, 0.742, peinture), (ARCH_R, 0.56, 0.745, peinture)):
        prof = []
        for a in lin(0.12, math.pi - 0.12, 40):
            prof.append((ax + (ar - 0.004) * math.cos(a), ay + (ar - 0.004) * math.sin(a)))
        inner = [(ax + (ar - 0.001) * math.cos(a), ay + (ar - 0.001) * math.sin(a)) for a in lin(math.pi - 0.12, 0.12, 40)]
        liner = extrude(prof + inner, z1 - z0, (0, 0, s * (z0 + z1) / 2), (0, 0, 1), M('passage-roue', 0x2a2b2c, 0.1, 0.8), 'passage', up=(0, 1, 0))
        front_bits.append(liner)

# ---------------------------------------------------------------- vitrages fixes et joints
ws_glass = poly_glass([(x_ws(y) - 0.006, y, z) for z, y in offset_outline(WS_OUT, 0.008)], vitre, 'pare-brise')
ws_seal = seal([(x_ws(y) + 0.001, y, z) for z, y in WS_OUT], 0.007)
q_glass, q_seal = [], []
for s in (1, -1):
    q_glass.append(poly_glass([(x, y, s * (z_glass(y) - 0.006)) for x, y in offset_outline(Q_WIN, 0.008)], vitre, 'custode'))
    q_seal.append(seal([(x, y, s * (z_glass(y) + 0.001)) for x, y in Q_WIN], 0.006))
gutters = []
for s in (1, -1):
    gutters.append(tube([(x_ws(Y_ROOF) - 0.03, Y_ROOF - 0.002, s * 0.672), (-0.5, Y_ROOF - 0.002, s * 0.673), (x_rear(Y_ROOF) + 0.16, Y_ROOF - 0.002, s * 0.672)], 0.007, peinture, 'gouttiere'))


# ---------------------------------------------------------------- vitres coulissantes, garnitures, poignées
def clip_x(pts, xm, keep_front):
    """Découpe un polygone 2D (x, y) par la droite x = xm."""
    out = []
    n = len(pts)
    inside = (lambda p: p[0] >= xm) if keep_front else (lambda p: p[0] <= xm)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (xm - a[0]) / (b[0] - a[0])
            out.append((xm, a[1] + (b[1] - a[1]) * t))
    return out


door_extra = {}
for name, ol, s in DOORS:
    front = 'av' in name
    win = FD_WIN if front else RD_WIN
    big = offset_outline(win, 0.010)
    xm = 0.10 if front else -0.555
    bits = []
    for keep_front, inset in ((True, 0.008), (False, 0.016)):
        half = clip_x(big, xm - 0.012 if keep_front else xm + 0.012, keep_front)
        bits.append(poly_glass([(x, y, s * (z_glass(y) - inset)) for x, y in half], vitre, 'glace'))
    bits.append(seal([(x, y, s * (z_glass(y) + 0.001)) for x, y in win], 0.006))
    bits.append(box((0.012, 0.36, 0.012), (xm, 1.26, s * (z_glass(1.26) - 0.012)), joint, 0.002, 'rail'))
    bits.append(box((0.02, 0.012, 0.03), (xm, 1.065, s * (z_glass(1.07) - 0.01)), joint, 0.002, 'coulisse'))
    # garniture intérieure, accoudoir, poignée intérieure
    x0, x1 = (0.66, -0.19) if front else (-0.24, -0.79)
    trim = box((abs(x1 - x0), 0.58, 0.008), ((x0 + x1) / 2, 0.73, s * 0.712), garniture, 0.004, 'garniture')
    bits.append(trim)
    bits.append(box((0.22, 0.03, 0.04), ((x0 + x1) / 2 - 0.05, 0.86, s * 0.69), garniture, 0.01, 'accoudoir'))
    bits.append(box((0.05, 0.02, 0.012), (x1 + 0.10 * (1 if front else -1) * -1, 0.93, s * 0.705), chrome, 0.004, 'poignee-int'))
    # poignée extérieure (à palette), à l'arrière de chaque porte
    hx = -0.10 if front else -0.70
    bits.append(box((0.12, 0.022, 0.016), (hx, 0.955, s * (zside(hx, 0.955) + 0.006)), chrome, 0.006, 'poignee'))
    bits.append(box((0.06, 0.012, 0.008), (hx + 0.02, 0.952, s * (zside(hx, 0.955) + 0.016)), plastique_noir, 0.003, 'palette'))
    if front:
        bits.append(cyl(0.009, 0.006, (hx - 0.075, 0.955, s * (zside(hx, 0.955) + 0.004)), (0, 0, s), chrome, 16, name='barillet'))
    # charnières apparentes (2 par porte, à l'avant)
    hx0 = 0.705 if front else -0.218
    for hy in (0.56, 0.90):
        bits.append(cyl(0.008, 0.06, (hx0, hy, s * (zside(hx0, hy) + 0.010)), (0, 1, 0), acier, 14, name='charniere'))
        bits.append(box((0.045, 0.04, 0.006), (hx0 - 0.02, hy, s * (zside(hx0, hy) + 0.004)), peinture, 0.002, 'patte'))
    door_extra[name] = bits

# baguettes de protection GTL : du pied avant à l'arrière de la porte arrière (photo p. I)
STRIP_Y = (0.41, 0.54)


def gtl_strip(x0, x1, s, name='baguette'):
    xs = lin(x0, x1, 40)
    ys = lin(*STRIP_Y, 7)
    P = []
    for x in xs:
        col = []
        for k, y in enumerate(ys):
            bulge = 0.010 + 0.006 * math.sin(math.pi * k / (len(ys) - 1))
            col.append((x, y, s * (zside(x, y) + bulge)))
        P.append(col)
    o = orient(grid(P, gris_gtl, name), inside=(x0, 0.47, 0))
    solidify(o, 0.006)
    return o


for name, _, s in DOORS:
    if 'av' in name:
        door_extra[name].append(gtl_strip(-0.198, 0.690, s))
    else:
        door_extra[name].append(gtl_strip(-0.780, -0.232, s))
strips_body = [gtl_strip(0.710, 0.96, s) for s in (1, -1)]

# rétroviseur extérieur côté conducteur (porte avant gauche)
mirror_bits = [tube([(0.560, 1.080, -0.735), (0.555, 1.10, -0.79)], 0.008, plastique_noir, 'bras-retro'),
               box((0.035, 0.085, 0.13), (0.565, 1.13, -0.845), plastique_noir, 0.02, 'retro'),
               box((0.004, 0.07, 0.11), (0.585, 1.13, -0.845), reflecteur, 0.01, 'miroir')]
door_extra['portes-avg'] += mirror_bits

# ---------------------------------------------------------------- hayon : vitre, poignée, plaque, monogramme
hatch_bits = []
xr_at = lambda y: x_rear(y) + (SILL_IN if y >= BELT else 0.0)   # noqa: E731
hatch_bits.append(poly_glass([(xr_at(y) + 0.006, y, z) for z, y in offset_outline(HATCH_WIN, 0.008)], vitre, 'lunette'))
hatch_bits.append(seal([(xr_at(y) - 0.001, y, z) for z, y in HATCH_WIN], 0.007))
hatch_bits.append(box((0.03, 0.03, 0.20), (x_rear(0.90) - 0.012, 0.90, 0), chrome, 0.01, 'poignee-hayon'))
hatch_bits.append(cyl(0.011, 0.008, (x_rear(0.90) - 0.028, 0.90, 0.13), (-1, 0, 0), chrome, 16, name='serrure'))
hatch_bits.append(box((0.006, 0.112, 0.522), (x_rear(0.655) - 0.006, 0.655, 0), support, 0.002, 'support-ar'))
hatch_bits.append(quad((x_rear(0.655) - 0.0095, 0.655, 0), 0.52, 0.11, (-1, 0, 0), plaque_j, 'plaque-ar'))
hatch_bits.append(box((0.03, 0.025, 0.12), (x_rear(0.73) - 0.012, 0.735, 0), plastique_noir, 0.006, 'eclaireur-plaque'))
hatch_bits.append(box((0.006, 0.022, 0.16), (x_rear(0.97) - 0.004, 0.975, 0.36), chrome, 0.003, 'monogramme'))
for s in (1, -1):   # charnières en haut du hayon
    hatch_bits.append(cyl(0.008, 0.07, (x_rear(1.485) - 0.002 + SILL_IN, 1.488, s * 0.40), (0, 0, 1), acier, 14, name='charniere-hayon'))
    hatch_bits.append(tube([(x_rear(1.40) + SILL_IN + 0.02, 1.40, s * 0.55), (x_rear(1.40) + SILL_IN + 0.12, 1.47, s * 0.60)], 0.007, acier_noir, 'compas'))

# trappe de carburant (arrière droit)
filler = [cyl(0.036, 0.012, (-1.585, 0.80, zside(-1.585, 0.80) + 0.004), (0, 0, 1), peinture, 32, name='trappe'),
          torus(0.036, 0.003, (-1.585, 0.80, zside(-1.585, 0.80) + 0.004), (0, 0, 1), joint, 32, 6, 'joint-trappe')]


# =====================================================================================
# Pare-chocs gris enveloppants (GTL), butoirs caoutchouc
# =====================================================================================
def bumper(sign):
    """Section 100 × 70 mm balayée le long d'un tracé en plan qui revient sur les ailes."""
    xb = 1.834 if sign > 0 else -1.834
    path = []
    for z in lin(-0.60, 0.60, 25):
        path.append((xb - sign * 0.010 * (z / 0.6) ** 2, z))
    for s in (1, -1):
        cx, cz = xb - sign * 0.09, s * 0.60
        for a in lin(0, math.pi / 2, 9)[1:]:
            pt = (cx + sign * 0.09 * math.cos(a) - sign * 0.0, cz + s * 0.09 * math.sin(a))
            pt = (xb - sign * 0.010 - sign * 0.09 * (1 - math.cos(a)), s * (0.60 + 0.09 * math.sin(a)))
            if s > 0:
                path.append(pt)
            else:
                path.insert(0, pt)
        end = (xb - sign * 0.10 - sign * 0.10, s * 0.705)
        if s > 0:
            path.append(end)
        else:
            path.insert(0, end)
    sec = [(0.0, -0.050), (0.012, -0.046), (0.020, -0.030), (0.024, 0.0), (0.020, 0.030), (0.012, 0.046), (0.0, 0.050), (-0.045, 0.048), (-0.050, 0.0), (-0.045, -0.048)]
    yc = 0.400 if sign > 0 else 0.425
    P = []
    for i, (x, z) in enumerate(path):
        a = path[min(i + 1, len(path) - 1)]
        b = path[max(i - 1, 0)]
        tx, tz = a[0] - b[0], a[1] - b[1]
        ln = math.hypot(tx, tz)
        nx, nz = tz / ln * sign, -tx / ln * sign   # normale sortante en plan
        if sign < 0:
            nx, nz = -nx, -nz
        P.append([(x + nx * u, yc + v, z + nz * u) for u, v in sec])
    o = grid(P, gris_gtl, 'pare-chocs', close_j=True)
    orient(o, inside=(xb - sign * 0.3, yc, 0))
    return o


bump = {}
for sign in (1, -1):
    xb = 1.834 if sign > 0 else -1.834
    yc = 0.400 if sign > 0 else 0.425
    bits = [bumper(sign)]
    for s in (1, -1):
        bits.append(box((0.03, 0.115, 0.06), (xb + sign * 0.018, yc, s * 0.29), caoutchouc, 0.012, 'butoir'))
        bits.append(box((0.10, 0.03, 0.04), (xb - sign * 0.09, yc - 0.04, s * 0.29), acier_noir, 0.004, 'patte-pare-chocs'))
    if sign > 0:
        bits.append(box((0.006, 0.112, 0.522), (xb + 0.025, 0.40, 0), support, 0.002, 'support-av'))
        bits.append(quad((xb + 0.0285, 0.40, 0), 0.52, 0.11, (1, 0, 0), plaque_m, 'plaque-av'))
    bump[sign] = bits

# =====================================================================================
# Calandre plastique pleine largeur (GTL), projecteurs ronds Ø 168, feux avant
# =====================================================================================
GX = X_NOSE + 0.004
grille_bits = []
surround = outline_round([(-0.535, 0.465), (0.535, 0.465), (0.535, 0.780), (-0.535, 0.780)], 0.045)
gr = extrude(surround, 0.030, (GX + 0.015, 0, 0), (1, 0, 0), plastique_noir, 'calandre', bev=0.004, up=(0, 1, 0))
for s in (1, -1):
    cut(gr, cyl(0.086, 0.2, (GX, 0.671, s * 0.417), (1, 0, 0), None, 48, name='trou'))
    cut(gr, prism(outline_round([(s * 0.425, 0.482), (s * 0.545, 0.482), (s * 0.545, 0.528), (s * 0.425, 0.528)], 0.008), 'x', GX - 0.1, GX + 0.1))
cut(gr, prism(outline_round([(-0.30, 0.598), (0.30, 0.598), (0.30, 0.752), (-0.30, 0.752)], 0.012), 'x', GX - 0.1, GX + 0.1))
grille_bits.append(gr)
for k in range(7):     # grille à mailles : barreaux horizontaux et verticaux
    grille_bits.append(box((0.016, 0.006, 0.60), (GX + 0.012, 0.606 + k * 0.024, 0), plastique_noir, 0.001, 'barreau'))
for k in range(13):
    grille_bits.append(box((0.016, 0.154, 0.006), (GX + 0.012, 0.675, -0.288 + k * 0.048), plastique_noir, 0.001, 'barreau'))
losange = extrude([(0, -0.038), (0.026, 0), (0, 0.038), (-0.026, 0)], 0.012, (GX + 0.028, 0.675, 0), (1, 0, 0), chrome, 'losange', bev=0.002, up=(0, 1, 0))
cut(losange, extrude([(0, -0.024), (0.014, 0), (0, 0.024), (-0.014, 0)], 0.05, (GX + 0.028, 0.675, 0), (1, 0, 0), None, 'creux', up=(0, 1, 0)))
grille_bits.append(losange)
for s in (1, -1):
    grille_bits.append(torus(0.088, 0.006, (GX + 0.030, 0.671, s * 0.417), (1, 0, 0), chrome, 48, 8, 'enjoliveur'))

phare_bits = []
for s in (1, -1):
    c = (GX + 0.022, 0.671, s * 0.417)
    phare_bits.append(lathe([(0.0, 0.012), (0.04, 0.010), (0.07, 0.005), (0.082, 0.0), (0.084, -0.006)], c, (1, 0, 0), cabochon_blanc, 40, 'glace-phare'))
    phare_bits.append(lathe([(0.084, -0.004), (0.084, -0.010), (0.075, -0.030), (0.045, -0.075), (0.02, -0.09), (0.0, -0.092)], c, (1, 0, 0), reflecteur, 40, 'reflecteur'))
    phare_bits.append(lathe([(0.086, 0.0), (0.086, -0.02), (0.078, -0.04), (0.05, -0.095), (0.03, -0.11), (0.0, -0.112)], c, (1, 0, 0), plastique_noir, 40, 'cuvelage'))
    phare_bits.append(cyl(0.032, 0.03, (GX - 0.10, 0.671, s * 0.417), (1, 0, 0), caoutchouc, 24, name='capuchon'))
    for dy, dz in ((0.07, 0.07), (-0.07, -0.07)):   # vis de réglage (haut : site, bas : direction)
        phare_bits.append(cyl(0.006, 0.04, (GX - 0.05, 0.671 + dy, s * 0.417 + dz), (1, 0, 0), acier, 10, name='vis-reglage'))

feux_bits = []
feux_fx = {'vis-feux-av': [], 'vis-feux-ar': []}
for s in (1, -1):
    # clignotants avant dans la calandre
    feux_bits.append(box((0.028, 0.044, 0.118), (GX + 0.020, 0.505, s * 0.485), cabochon_orange, 0.006, 'clignotant-av'))
    feux_bits.append(box((0.03, 0.04, 0.11), (GX - 0.002, 0.505, s * 0.485), plastique_noir, 0.006, 'boitier'))
    feux_fx['vis-feux-av'].append(((GX + 0.035, 0.505, s * 0.485), (1, 0, 0)))
    # répétiteurs latéraux sur les ailes
    rx = 1.14
    feux_bits.append(box((0.05, 0.02, 0.010), (rx, 0.80, s * (zside(rx, 0.80) + 0.004)), cabochon_orange, 0.004, 'repetiteur'))
    # feux arrière verticaux sur les angles (position/stop rouge, clignotant orange en haut)
    for y0, y1, mat in ((0.675, 0.835, cabochon_rouge), (0.835, 0.905, cabochon_orange)):
        prof = []
        for a in lin(0, math.pi / 2, 9):
            cx, cz = x_rear(0.80) + RC_REAR, zside(x_rear(0.80) + RC_REAR, 0.80) - RC_REAR
            prof.append((cx - (RC_REAR + 0.012) * math.cos(a) * 1.0, cz + (RC_REAR + 0.012) * math.sin(a)))
        pts = [(prof[k][0], (y0 + y1) / 2, s * prof[k][1]) for k in range(len(prof))]
        sec = [(0, y0 - (y0 + y1) / 2), (0, y1 - (y0 + y1) / 2)]
        P = [[(x, (y0 + y1) / 2 + dy, z) for _, dy in sec] for x, _, z in pts]
        lamp = grid(P, mat, 'feu-ar')
        solidify(lamp, 0.012, 0.0)
        feux_bits.append(lamp)
    feux_fx['vis-feux-ar'] += [((x_rear(0.88) - 0.014, 0.88, s * 0.668), (-1, 0, 0)), ((x_rear(0.70) - 0.014, 0.70, s * 0.668), (-1, 0, 0))]

# =====================================================================================
# Essuie-glace : moteur derrière la planche de bord, deux bras au repos vers la gauche
# =====================================================================================
wiper_bits = []
for zp in (-0.20, 0.13):
    p0 = (0.655, 1.046, zp)
    wiper_bits.append(cyl(0.012, 0.03, p0, (0, 1, 0), plastique_noir, 16, name='axe-essuie'))
    tip = (x_ws(1.09) + 0.012, 1.09, zp - 0.40)
    wiper_bits.append(tube([p0, ((p0[0] + tip[0]) / 2 + 0.01, 1.07, (zp + tip[2]) / 2), tip], 0.0055, plastique_noir, 'bras'))
    wiper_bits.append(tube([(x_ws(1.075) + 0.010, 1.075, zp - 0.62), (x_ws(1.095) + 0.012, 1.095, zp - 0.18)], 0.006, caoutchouc, 'balai'))
wiper_bits.append(box((0.08, 0.06, 0.10), (0.60, 0.97, 0.20), acier_noir, 0.01, 'moteur-essuie'))
wiper_bits.append(tube([(0.60, 0.99, 0.20), (0.63, 1.02, 0.15), (0.655, 1.035, 0.13)], 0.004, acier, 'biellette'))
wiper_bits.append(tube([(0.60, 0.99, 0.18), (0.64, 1.025, -0.05), (0.655, 1.035, -0.20)], 0.004, acier, 'biellette'))

# =====================================================================================
# Pièces du site
# =====================================================================================
pc = Part('caisse', (0, 0.25, 0))
pc.add(lower, upper, roof, fender, *front_bits, *gutters, *q_seal, *strips_body, *filler, ws_seal)
for name, _, s in DOORS:
    p = Part('portes', (0, 0, 0.6 * s))
    p.add(*door_skins[name], *door_extra[name])
ph = Part('hayon', (-0.55, 0.35, 0))
ph.add(*hatch_skins, *hatch_bits)
pk = Part('capot', (0.35, 0.65, 0))
pk.add(hood, *hood_frame)
pv = Part('vitrage', (0, 0.6, 0))
pv.add(ws_glass, *q_glass)
for sign in (1, -1):
    pb = Part('pare-chocs', (0.45 * sign, 0, 0))
    pb.add(*bump[sign])
pg = Part('calandre', (0.4, 0, 0))
pg.add(*grille_bits)
pp = Part('phares', (0.4, 0.15, 0))
pp.add(*phare_bits)
pf = Part('feux', (0, 0.15, 0))
pf.add(*feux_bits)
fasteners(pf, 'vis-feux-av', feux_fx['vis-feux-av'], kind='screw', r=0.004, length=0.02, travel=0.03)
fasteners(pf, 'vis-feux-ar', feux_fx['vis-feux-ar'], kind='screw', r=0.004, length=0.02, travel=0.03)
pw = Part('essuie-glace', (0.2, 0.4, 0))
pw.add(*wiper_bits)

export(OUT)
