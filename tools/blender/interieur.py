# Habitacle de la Renault 4 GTL : sièges avant, banquette rabattable, planche de bord « nouvelle
# génération » (modèles 1983 et suivants), volant, levier « trombone », pédalier, frein à main.
# Lancer : python3 tools/blender/interieur.py   →   models/interieur.glb
#
# RTA : photo du poste de conduite depuis 1983 (p. XVIII) ; assise à 360 mm du plancher avant et
# 345 mm à l'arrière, profondeur d'assise 450 / 430 mm (plans p. XIX) ; banquette rabattable avec
# boutons crantés (p. XV) ; levier sortant de la planche, tige au-dessus du moteur (p.46) ;
# commande de frein à main par tirette et câbles (p.70). Formes des garnitures estimées.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, bevel, box, smooth, cyl, export, extrude, fastener, fasteners, lathe, reset, rounded_rect, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'interieur.glb')

FLOOR = 0.370
FLOOR_R = 0.470
DRIVER_Z = -0.33

tissu = M('tissu-siege', 0x5e5148, 0.0, 0.95)
tissu_cl = M('tissu-motif', 0x6b5d52, 0.0, 0.95)
skai = M('skai', 0x2b2826, 0.0, 0.7)
tube_m = M('tube-siege', 0x2b2b2b, 0.6, 0.4)
planche = M('planche', 0x2a2826, 0.0, 0.8)
planche_cl = M('planche-gris', 0x3a3734, 0.0, 0.75)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
cadran = M('cadran', 0x111214, 0.0, 0.4)
graduation = M('graduation', 0xe9e4d6, 0.0, 0.4)
temoin_r = M('temoin-rouge', 0x9c2a22, 0.0, 0.3)
temoin_v = M('temoin-vert', 0x2f7a3e, 0.0, 0.3)
temoin_o = M('temoin-orange', 0xc57a22, 0.0, 0.3)
glace_m = M('glace-compteur', 0xb8c6cf, 0.3, 0.05, alpha=0.25)
cable = M('cable', 0x2a2a2a, 0.3, 0.6)
reflecteur = M('reflecteur', 0xe8e9ea, 1.0, 0.08)


# =====================================================================================
# SIÈGES
# =====================================================================================
def cushion(c, w, d, h, mat, name):
    o = box((d, h, w), c, mat, 0, name)
    bevel(o, min(h, d, w) * 0.42, 5)
    smooth(o, 70)
    return o


def seat(part, x, z, w=0.47):
    """Siège avant : assise à 360 mm du plancher, dossier incliné, armature tube sur glissières."""
    yt = FLOOR + 0.36
    part.add(cushion((x, yt - 0.05, z), w, 0.47, 0.10, tissu, 'assise'))
    part.add(cushion((x + 0.01, yt - 0.003, z), w * 0.72, 0.36, 0.012, tissu_cl, 'motif'))
    bx, by = x - 0.25, yt + 0.27
    back = cushion((bx, by, z), w * 0.97, 0.10, 0.56, tissu, 'dossier')
    back.rotation_mode = 'XYZ'
    back.rotation_euler = (0, -0.20, 0)   # inclinaison vers l'arrière (rotation autour de z du site = -y Blender)
    part.add(back)
    for dz in (-w / 2 + 0.03, w / 2 - 0.03):
        zz = z + dz
        part.add(tube([(x + 0.20, yt - 0.11, zz), (x - 0.22, yt - 0.11, zz), (bx - 0.10, yt + 0.52, zz)], 0.011, tube_m, seg=8))
        part.add(tube([(x + 0.17, yt - 0.11, zz), (x + 0.17, FLOOR + 0.03, zz)], 0.011, tube_m, seg=8))
        part.add(tube([(x - 0.18, yt - 0.11, zz), (x - 0.18, FLOOR + 0.03, zz)], 0.011, tube_m, seg=8))
        part.add(box((0.52, 0.02, 0.035), (x, FLOOR + 0.012, zz), acier_noir, 0.004, 'glissiere'))
    part.add(box((0.03, 0.012, w - 0.08), (x + 0.22, yt - 0.13, z), tube_m, 0.004, 'barre-reglage'))


for z in (DRIVER_Z, -DRIVER_Z):
    p = Part('sieges-av', (0, 0.7, 0))
    seat(p, 0.08, z)

# banquette rabattable : assise sur le talon de plancher, dossier articulé, boutons crantés (p. XV)
bq = Part('banquette', (-0.2, 0.8, 0))
yb = FLOOR + 0.345
bq.add(cushion((-0.72, yb - 0.055, 0), 1.20, 0.43, 0.11, tissu, 'assise'))
for z in (-0.30, 0.30):
    bq.add(cushion((-0.71, yb - 0.003, z), 0.44, 0.33, 0.012, tissu_cl, 'motif'))
back = cushion((-0.98, yb + 0.29, 0), 1.24, 0.10, 0.58, tissu, 'dossier')
back.rotation_mode = 'XYZ'
back.rotation_euler = (0, -0.22, 0)
bq.add(back)
bq.add(tube([(-0.52, yb - 0.11, -0.58), (-0.92, yb - 0.11, -0.58), (-0.92, yb - 0.11, 0.58), (-0.52, yb - 0.11, 0.58)], 0.011, tube_m, seg=8))
for s in (1, -1):
    bq.add(tube([(-0.92, yb - 0.11, s * 0.60), (-0.94, yb + 0.20, s * 0.63), (-1.02, yb + 0.30, s * 0.64)], 0.008, acier, seg=8))   # barrettes
    bq.add(cyl(0.018, 0.02, (-1.02, yb + 0.30, s * 0.645), (0, 0, s), noir, 16))   # bouton cranté (B)
    bq.add(box((0.04, 0.04, 0.03), (-0.56, FLOOR + 0.03, s * 0.55), acier_noir, 0.005, 'charniere'))

# =====================================================================================
# PLANCHE DE BORD (1983 et suivants, photo p. XVIII)
# =====================================================================================
pb = Part('planche-bord', (-0.45, 0.35, 0))
# bandeau rembourré sur toute la largeur, sous le pare-brise
prof = [(0.630, 1.022), (0.560, 1.024), (0.505, 1.010), (0.488, 0.985), (0.495, 0.955), (0.530, 0.945), (0.640, 0.950)]
pb.add(extrude(prof, 1.40, (0, 0, 0), (0, 0, 1), planche, 'bandeau', bev=0.006, up=(0, 1, 0)))
# vide-poches inférieur pleine largeur
pb.add(extrude([(0.640, 0.840), (0.520, 0.835), (0.505, 0.860), (0.520, 0.868), (0.640, 0.872)], 1.32, (0, 0, 0), (0, 0, 1), planche, 'vide-poches', bev=0.004, up=(0, 1, 0)))
pb.add(box((0.10, 0.09, 1.30), (0.59, 0.90, 0), planche_cl, 0.01, 'facade'))
# combiné d'instruments devant le conducteur : compteur rond, jauge, témoins (3 × 4)
cz = DRIVER_Z + 0.01
pb.add(box((0.10, 0.13, 0.34), (0.51, 0.955, cz), planche, 0.02, 'combine'))
pb.add(box((0.05, 0.014, 0.34), (0.47, 1.024, cz), planche_cl, 0.006, 'visiere'))
ix = 0.457
pb.add(cyl(0.052, 0.006, (ix, 0.955, cz - 0.085), (1, 0, 0), cadran, 40, name='compteur'))
pb.add(torus(0.052, 0.004, (ix - 0.002, 0.955, cz - 0.085), (1, 0, 0), graduation, 40, 6, 'lunette'))
for k in range(11):
    a = math.radians(225 - k * 27)
    pb.add(box((0.002, 0.010, 0.002), (ix - 0.004, 0.955 + 0.042 * math.sin(a), cz - 0.085 + 0.042 * math.cos(a)), graduation, name='graduation'))
pb.add(box((0.002, 0.004, 0.040), (ix - 0.005, 0.950, cz - 0.075), M('aiguille', 0xe0602a, 0.0, 0.4), name='aiguille'))
for r in range(3):
    for c in range(4):
        mat = (temoin_r, temoin_v, temoin_o, graduation)[(r + c) % 4]
        pb.add(cyl(0.010, 0.004, (ix - 0.001, 0.990 - r * 0.030, cz + 0.005 + c * 0.032), (1, 0, 0), mat, 16, name='temoin'))
pb.add(cyl(0.028, 0.004, (ix - 0.001, 0.955, cz + 0.135), (1, 0, 0), cadran, 28, name='jauge-essence'))
pb.add(box((0.004, 0.11, 0.30), (ix - 0.006, 0.955, cz + 0.02), glace_m, 0.004, 'glace'))
pb.add(extrude([(0, -0.02), (0.014, 0), (0, 0.02), (-0.014, 0)], 0.004, (ix + 0.0, 0.905, cz), (1, 0, 0), M('chrome', 0xdfe2e5, 1.0, 0.15), 'losange', up=(0, 1, 0)))
# commandes : interrupteurs à bascule, chauffage, cendrier, starter à gauche sous la planche
for k in range(4):
    pb.add(box((0.012, 0.03, 0.016), (0.537, 0.905, cz + 0.20 + k * 0.03), noir, 0.003, 'interrupteur'))
pb.add(box((0.012, 0.05, 0.20), (0.538, 0.91, 0.10), planche_cl, 0.006, 'commandes-chauffage'))
for k in range(3):
    pb.add(box((0.02, 0.012, 0.012), (0.528, 0.91, 0.03 + k * 0.06), chrome, 0.003, 'tirette'))
pb.add(box((0.02, 0.04, 0.10), (0.535, 0.87, 0.26), planche_cl, 0.006, 'cendrier'))
pb.add(cyl(0.010, 0.04, (0.52, 0.84, -0.58), (1, 0, 0), noir, 12, name='starter'))
pb.add(cyl(0.015, 0.012, (0.50, 0.84, -0.58), (1, 0, 0), chrome, 16, name='bouton-starter'))
# aérateurs sur le dessus, côté passager boîte à gants ouverte
for z in (-0.58, 0.58):
    pb.add(box((0.06, 0.006, 0.12), (0.585, 1.026, z), noir, 0.002, 'aerateur'))
pb.add(box((0.08, 0.07, 0.40), (0.545, 0.92, 0.42), planche_cl, 0.012, 'boite-a-gants'))
# rétroviseur intérieur au haut du pare-brise
pb.add(tube([(0.37, 1.465, 0.0), (0.39, 1.43, 0.0)], 0.005, noir))
pb.add(box((0.025, 0.055, 0.17), (0.395, 1.40, 0.0), noir, 0.012, 'retro-int'))
pb.add(box((0.003, 0.045, 0.155), (0.381, 1.40, 0.0), reflecteur, 0.006, 'miroir'))
# pare-soleil
for z in (-0.33, 0.33):
    pb.add(box((0.20, 0.012, 0.34), (0.26, 1.46, z), M('pare-soleil', 0x8a8178, 0.0, 0.9), 0.005, 'pare-soleil'))
fasteners(pb, 'vis-planche', [((0.488, 1.0, -0.62), (-1, 0, 0)), ((0.488, 1.0, 0.62), (-1, 0, 0)), ((0.505, 0.85, -0.2), (-1, 0, 0)), ((0.505, 0.85, 0.3), (-1, 0, 0))], kind='screw', r=0.005, length=0.025, travel=0.04)

# =====================================================================================
# VOLANT ET COLONNE (joint souple vers le boîtier de crémaillère)
# =====================================================================================
vo = Part('volant', (-0.45, 0.45, 0))
c0, c1 = (0.80, 0.76, DRIVER_Z), (0.43, 1.03, DRIVER_Z)
d = (c1[0] - c0[0], c1[1] - c0[1], 0)
ln = math.hypot(d[0], d[1])
u = (d[0] / ln, d[1] / ln, 0)
vo.add(tube([c0, c1], 0.017, acier_noir, seg=12))
vo.add(tube([(c0[0] + u[0] * 0.30, c0[1] + u[1] * 0.30, DRIVER_Z), (c1[0] - u[0] * 0.02, c1[1] - u[1] * 0.02, DRIVER_Z)], 0.030, planche, seg=16))   # carénage
vo.add(box((0.07, 0.06, 0.05), (0.50, 0.975, DRIVER_Z + 0.06), planche, 0.012, 'antivol'))
for k in range(2):   # commodos
    vo.add(tube([(0.50, 0.985 - k * 0.02, DRIVER_Z + (0.03 if k else -0.03)), (0.47, 0.99 - k * 0.02, DRIVER_Z + (0.16 if k else -0.16))], 0.005, noir, seg=6))
wc = (c1[0] - u[0] * 0.035, c1[1] - u[1] * 0.035, DRIVER_Z)
ax = (-u[0], -u[1], 0)
vo.add(torus(0.195, 0.013, wc, ax, noir, 56, 10, 'jante'))
vo.add(lathe([(0.0, 0.035), (0.045, 0.030), (0.06, 0.010), (0.055, -0.010), (0.0, -0.012)], wc, ax, noir, 28, 'moyeu'))
# deux branches basses
import mathutils  # noqa: E402
n = mathutils.Vector(ax)
side = mathutils.Vector((0, 0, 1))
up = n.cross(side).normalized()
if up.y < 0:
    up = -up
for sgn in (1, -1):
    a = math.radians(-30)
    tip = mathutils.Vector(wc) + side * (sgn * 0.19 * math.cos(a)) + up * (0.19 * math.sin(a))
    vo.add(tube([wc, tuple((mathutils.Vector(wc) + tip) / 2 + n * 0.01), tuple(tip)], 0.011, noir, seg=8))
vo.add(cyl(0.04, 0.03, (0.92, 0.66, DRIVER_Z + 0.03), (1, -0.5, 0.2), caoutchouc, 20, name='joint-souple'))
fastener(vo, 'ecrou-volant', (wc[0] - u[0] * 0.03, wc[1] - u[1] * 0.03, wc[2]), ax, kind='nut', r=0.011, length=0.03, travel=0.06)

# =====================================================================================
# LEVIER « TROMBONE » : sort de la planche, tige au-dessus du moteur jusqu'au renvoi de boîte
# =====================================================================================
lv = Part('levier-vitesses', (0, 0.45, 0))
lv.add(tube([(0.64, 0.875, 0.035), (0.55, 0.875, 0.035), (0.47, 0.862, 0.045), (0.44, 0.85, 0.05)], 0.008, chrome, seg=10))
lv.add(lathe([(0.0, -0.03), (0.018, -0.028), (0.026, -0.005), (0.024, 0.02), (0.012, 0.035), (0.0, 0.036)], (0.43, 0.85, 0.05), (-0.8, -0.3, 0.1), noir, 20, 'pommeau'))
lv.add(cyl(0.026, 0.04, (0.66, 0.875, 0.035), (1, 0, 0), caoutchouc, 18, name='soufflet'))
lv.add(tube([(0.64, 0.875, 0.035), (0.80, 0.87, 0.035), (1.05, 0.81, 0.04), (1.35, 0.68, 0.03), (1.56, 0.56, 0.01), (1.585, 0.545, 0.0)], 0.008, acier, seg=8, res=14))
lv.add(box((0.05, 0.05, 0.07), (0.71, 0.875, 0.035), acier_noir, 0.008, 'palier-tablier'))

# =====================================================================================
# PÉDALIER : pédales suspendues, axe sous la planche ; tige de poussée du maître-cylindre
# =====================================================================================
pd = Part('pedalier', (-0.3, 0.2, -0.3))
pd.add(cyl(0.008, 0.30, (0.64, 0.86, -0.36), (0, 0, 1), acier, 12))
pd.add(box((0.06, 0.10, 0.30), (0.67, 0.86, -0.36), acier_noir, 0.006, 'support'))
for z, w, nm in ((-0.465, 0.075, 'embrayage'), (-0.355, 0.075, 'frein'), (-0.245, 0.05, 'accelerateur')):
    if nm == 'accelerateur':
        pd.add(tube([(0.64, 0.86, z), (0.60, 0.68, z), (0.53, 0.52, z)], 0.006, acier_noir, seg=8))
        pd.add(box((0.02, 0.11, w), (0.52, 0.47, z), caoutchouc, 0.006, 'patin'))
    else:
        pd.add(tube([(0.64, 0.86, z), (0.61, 0.70, z), (0.54, 0.55, z), (0.51, 0.50, z)], 0.008, acier_noir, seg=8))
        pd.add(box((0.022, 0.07, w), (0.505, 0.49, z), caoutchouc, 0.008, 'patin'))
pd.add(tube([(0.62, 0.78, -0.355), (0.70, 0.80, -0.38), (0.78, 0.82, -0.42)], 0.005, acier, seg=6))   # tige de poussée
pd.add(tube([(0.63, 0.80, -0.465), (0.70, 0.74, -0.42), (0.84, 0.70, -0.40)], 0.004, cable, seg=6))     # câble d'embrayage
pd.add(tube([(0.62, 0.74, -0.245), (0.70, 0.76, -0.32), (0.83, 0.75, -0.40)], 0.0025, cable, seg=6))   # câble d'accélérateur
fastener(pd, 'garde-frein', (0.70, 0.80, -0.38), (-1, -0.25, 0.3), kind='nut', r=0.007, length=0.02, travel=0.03)

# =====================================================================================
# FREIN À MAIN : tirette sous la planche, renvoi, palonnier, câbles vers les mâchoires arrière
# =====================================================================================
fm = Part('frein-main', (0, -0.25, 0))
fm.add(tube([(0.64, 0.83, -0.12), (0.50, 0.83, -0.12)], 0.008, chrome, seg=10))
fm.add(box((0.025, 0.035, 0.10), (0.49, 0.83, -0.12), noir, 0.01, 'poignee'))
fm.add(box((0.06, 0.05, 0.05), (0.66, 0.83, -0.12), acier_noir, 0.006, 'guide'))
fm.add(tube([(0.66, 0.83, -0.12), (0.69, 0.60, -0.12), (0.66, 0.40, -0.10), (0.40, 0.345, -0.05), (-0.40, 0.345, 0.0), (-0.86, 0.345, 0.0)], 0.005, cable, seg=6, res=10))
fm.add(box((0.05, 0.02, 0.14), (-0.88, 0.345, 0), acier_noir, 0.004, 'palonnier'))
for s, x0 in ((1, -1.143), (-1, -1.095)):
    fm.add(tube([(-0.88, 0.345, s * 0.06), (-0.98, 0.33, s * 0.30), (x0 + 0.05, 0.30, s * 0.47), (x0 + 0.02, 0.29, s * 0.50)], 0.004, cable, seg=6, res=10))
fastener(fm, 'reglage-frein-main', (-0.85, 0.345, 0), (1, 0, 0), kind='nut', r=0.007, length=0.025, travel=0.03)

export(OUT)
