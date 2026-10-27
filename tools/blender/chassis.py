# Roues et roue de secours de la Renault 4 GTL (plateforme, réservoir et échappement : voir
# soubassement.py). Lancer : python3 tools/blender/chassis.py   →   models/chassis.glb
#
# RTA : jante 400 B 13, pneus 145 SR 13, 3 écrous (p.82) ; roue de secours sur berceau sous le
# plancher arrière, face extérieure vers le sol, vis au centre de la traverse arrière (p. X).
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, M_img, Part, T, box, cut, cyl, export, extrude, fastener, lathe, reset, rounded_rect, torus, tube  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
import tempfile  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'chassis.glb')

AXLE_F = 1.306
AXLE_R = {1: -1.143, -1: -1.095}
TRACK = {'av': 0.640, 'ar': 0.624}
WR = 0.285
FLOOR_R = 0.470        # plancher de coffre

noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
pneu = M('pneu', 0x1c1d1e, 0.0, 0.9)
jante = M('jante', 0xb9bec2, 0.7, 0.35)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)

# =====================================================================================
# ROUES : jante tôle 400 B 13 à voile ajouré, pneu 145 SR 13
# =====================================================================================
def sidewall_png():
    """Marquages moulés du flanc (dimension, structure, sens), en relief gris sur caoutchouc noir.
    L'image fait le tour du pneu (u = angle) ; v va du talon vers la bande de roulement."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 4096, 160
    im = Image.new('RGB', (w, h), (29, 30, 31))
    d = ImageDraw.Draw(im)
    font = small = None
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f):
            font, small = ImageFont.truetype(f, 92), ImageFont.truetype(f, 46)
            break
    for k, (txt, fnt, x) in enumerate((('145 SR 13', font, 0.12), ('RADIAL  X', font, 0.45), ('TUBELESS', small, 0.70),
                                         ('145 SR 13', font, 0.80), ('M+S  73 S', small, 0.30), ('DOT  XU 4C  3488', small, 0.95))):
        d.text((x * w, h * 0.5), txt, fill=(54, 55, 57), font=fnt, anchor='mm')
    for y in (8, h - 8):
        d.line((0, y, w, y), fill=(44, 45, 47), width=4)
    path = os.path.join(tempfile.mkdtemp(prefix='flanc-'), 'flanc.png')
    im.save(path)
    return path


flanc_m = M_img('flanc-pneu', sidewall_png(), 0.0, 0.9)
valve_m = M('valve', 0x151515, 0.0, 0.7)
plomb = M('masse-equilibrage', 0x8d8f91, 0.6, 0.5)


def annulus(c, ax_s, r0, r1, off, mat, name='flanc', n=96):
    """Anneau plan texturé sur le flanc extérieur du pneu (repère du site, axe z)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    x, y, z = c
    ring = []
    for i in range(n + 1):
        a = -2 * math.pi * i / n * ax_s     # sens horaire vu de l'extérieur : texte lisible
        ring.append([bm.verts.new(T(x + r * math.cos(a), y + r * math.sin(a), z + ax_s * off(r))) for r in (r0, r1)])
    for i in range(n):
        f = bm.faces.new((ring[i][0], ring[i + 1][0], ring[i + 1][1], ring[i][1]))
        for lp, (u, v) in zip(f.loops, ((i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1))):
            lp[uv].uv = (u, v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    for p_ in me.polygons:
        p_.use_smooth = True
    return o


TIRE = [(0.168, -0.062), (0.180, -0.070), (0.215, -0.074), (0.255, -0.072), (0.274, -0.064), (0.282, -0.052),
        (0.2845, -0.040), (0.281, -0.034), (0.2845, -0.028), (0.2845, -0.010), (0.281, -0.005), (0.2845, 0.0),
        (0.2845, 0.010), (0.281, 0.016), (0.2845, 0.022), (0.2845, 0.040), (0.282, 0.052), (0.274, 0.064),
        (0.255, 0.072), (0.215, 0.074), (0.180, 0.070), (0.168, 0.062)]


def wheel(part, c, s, mount_off, set_id, idx0, nuts=True):
    """Roue centrée en c, face extérieure vers s (z du site) ; mount_off : décalage du voile."""
    x, y, z = c
    ax = (0, 0, s)
    part.add(lathe([(r, h) for r, h in TIRE], c, ax, pneu, 64, 'pneu'))
    # sculptures : rainures transversales sur la bande de roulement
    for k in range(40):
        a = 2 * math.pi * k / 40
        for hz in (-0.025, 0.025):
            part.add(box((0.006, 0.006, 0.020), (x + 0.2838 * math.cos(a), y + 0.2838 * math.sin(a), z + s * hz), caoutchouc, name='sculpture'))
    # jante : gorge, rebords, voile embouti
    rim = [(0.172, -0.052), (0.178, -0.056), (0.178, -0.050), (0.166, -0.046), (0.160, -0.030), (0.160, 0.030),
           (0.166, 0.046), (0.178, 0.050), (0.178, 0.056), (0.172, 0.052)]
    part.add(lathe(rim, c, ax, jante, 64, 'jante'))
    m = mount_off
    disc = [(0.158, 0.012), (0.140, 0.010), (0.120, m + 0.022), (0.095, m + 0.010), (0.085, m), (0.034, m), (0.034, m + 0.004),
            (0.085, m + 0.004), (0.095, m + 0.014), (0.120, m + 0.026), (0.140, 0.014), (0.158, 0.016)]
    d = lathe(disc, c, ax, jante, 64, 'voile')
    for k in range(6):     # ajours du voile
        a = 2 * math.pi * k / 6 + math.pi / 6
        cut(d, extrude(rounded_rect(0.022, 0.036, 0.008), 0.10, (x + 0.128 * math.cos(a), y + 0.128 * math.sin(a), z), (0, 0, 1), None, 'ajour', up=(math.cos(a), math.sin(a), 0)))
    part.add(d)
    for k in range(3):     # trous de goujons (entraxe 130)
        a = 2 * math.pi * k / 3 + math.pi / 2
        part.add(torus(0.010, 0.0025, (x + 0.065 * math.cos(a), y + 0.065 * math.sin(a), z + s * (m + 0.004)), ax, jante, 16, 6, 'portee'))
    part.add(lathe([(0.0, 0.020), (0.022, 0.018), (0.030, 0.010), (0.032, 0.0)], (x, y, z + s * (m + 0.03)), ax, chrome, 24, 'cache-moyeu'))
    # marquages du flanc extérieur (anneau entre 200 et 250 mm, posé sur le profil du pneu)
    part.add(annulus(c, s, 0.205, 0.245, lambda r: 0.0754 - (r - 0.215) * 0.05, flanc_m))
    # valve caoutchouc dans la gorge de jante, bouchon ; masses d'équilibrage agrafées au rebord
    va = math.radians(200)
    vp = (x + 0.150 * math.cos(va), y + 0.150 * math.sin(va), z + s * 0.035)
    part.add(cyl(0.0055, 0.032, vp, (math.cos(va) * 0.55, math.sin(va) * 0.55, s), valve_m, 12, r2=0.004, name='valve'))
    part.add(cyl(0.004, 0.009, (vp[0] - 0.006 * math.cos(va), vp[1] - 0.006 * math.sin(va), vp[2] + s * 0.016), (math.cos(va) * 0.55, math.sin(va) * 0.55, s), noir, 10, name='bouchon-valve'))
    for k, a in enumerate((math.radians(20), math.radians(32))):
        part.add(box((0.012, 0.006, 0.020), (x + 0.176 * math.cos(a), y + 0.176 * math.sin(a), z + s * 0.055), plomb, 0.0015, 'masse', axis=(math.cos(a), math.sin(a), 0)))
    if nuts:
        specs = []
        for k in range(3):
            a = 2 * math.pi * k / 3 + math.pi / 2
            specs.append(((x + 0.065 * math.cos(a), y + 0.065 * math.sin(a), z + s * (m + 0.006)), (0, 0, s)))
        for i, (p, dd) in enumerate(specs):
            fastener(part, set_id, p, dd, kind='nut', r=0.0095, length=0.025, travel=0.07, idx=idx0 + i)


n = 0
for key in ('av', 'ar'):
    for s in (1, -1):
        x = AXLE_F if key == 'av' else AXLE_R[s]
        mount = 0.585 if key == 'av' else 0.578
        zc = s * TRACK[key]
        p = Part('roues', (0, 0, 0.5 * s))
        wheel(p, (x, WR, zc), s, mount - TRACK[key], 'ecrous-roue', n)
        n += 3

# roue de secours sur son berceau, face extérieure vers le sol
sp = Part('roue-secours', (-0.6, -0.2, 0))
wheel(sp, (-1.47, 0.205, 0), 1, -0.055, 'ecrous-roue-secours', 0)
from mathutils import Matrix  # noqa: E402
from lib import T  # noqa: E402
piv = T(-1.47, 0.205, 0)
for o in sp.objs + sp.fasteners:   # axe de roue vertical, face extérieure vers le sol
    o.matrix_world = Matrix.Translation(piv) @ Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Translation(-piv) @ o.matrix_world
for f in sp.fasteners:
    f['dir'] = [0.0, -1.0, 0.0]
for z in (-0.20, 0.20):
    sp.add(tube([(-1.76, 0.33, z * 0.4), (-1.70, 0.135, z), (-1.20, 0.135, z), (-1.15, 0.30, z * 0.6)], 0.008, acier_noir, seg=8))
sp.add(box((0.60, 0.012, 0.03), (-1.47, 0.128, 0), acier_noir, 0.003))
fastener(sp, 'vis-berceau-secours', (-1.765, FLOOR_R - 0.01, 0), (0, 1, 0), kind='bolt', r=0.011, length=0.07, travel=0.06, idx=0)

export(OUT)
