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
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, M_img, Part, uv_box, bevel, box, smooth, cyl, export, extrude, fastener, fasteners, lathe, reset, rounded_rect, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'interieur.glb')

FLOOR = 0.370
FLOOR_R = 0.470
DRIVER_Z = -0.33



def fabric_png():
    """Tissu à carreaux des sièges (photo p. XVIII) : carreaux de 40 mm clairs et foncés, trame fine.
    L'image couvre 80 mm × 80 mm (2 × 2 carreaux)."""
    n = 256
    im = Image.new('RGB', (n, n))
    px = im.load()
    for y in range(n):
        for x in range(n):
            dark = ((x // (n // 2)) + (y // (n // 2))) % 2
            base = (78, 74, 70) if dark else (118, 112, 104)
            weave = 6 if (x + y) % 4 < 2 else -6          # trame diagonale
            line = -14 if (x % (n // 2) < 3 or y % (n // 2) < 3) else 0
            px[x, y] = tuple(max(0, min(255, c + weave + line)) for c in base)
    path = os.path.join(tempfile.mkdtemp(prefix='tissu-'), 'tissu.png')
    im.save(path)
    return path


tissu = M_img('tissu-siege', fabric_png(), 0.0, 0.95)
TISSU_UV = 1 / 0.08
skai = M('skai', 0x2b2826, 0.0, 0.7)
tube_m = M('tube-siege', 0x2b2b2b, 0.6, 0.4)
planche = M('planche', 0x8e8a82, 0.0, 0.75)          # planche claire (photo p. XVIII)
planche_cl = M('planche-creux', 0x77736c, 0.0, 0.8)
planche_f = M('planche-fonce', 0x2a2826, 0.0, 0.7)
volant_m = M('volant', 0x8a867e, 0.0, 0.55)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
cadran = M('cadran', 0x111214, 0.0, 0.4)
graduation = M('graduation', 0xe9e4d6, 0.0, 0.4)
temoin_r = M('temoin-rouge', 0x6a1e1a, 0.0, 0.3)
temoin_v = M('temoin-vert', 0x1f4a2a, 0.0, 0.3)
temoin_o = M('temoin-orange', 0x7a4a18, 0.0, 0.3)
temoin_b = M('temoin-bleu', 0x1e3a6a, 0.0, 0.3)
aiguille = M('aiguille', 0xe0602a, 0.0, 0.4)
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
    if mat is tissu:
        uv_box(o, TISSU_UV)
    return o


def seat(part, x, z, w=0.47):
    """Siège avant : assise à 360 mm du plancher, dossier incliné, armature tube sur glissières."""
    yt = FLOOR + 0.36
    part.add(cushion((x, yt - 0.05, z), w, 0.47, 0.10, tissu, 'assise'))
    part.add(cushion((x + 0.01, yt - 0.003, z), w * 0.72, 0.36, 0.012, tissu, 'motif'))
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
    bq.add(cushion((-0.71, yb - 0.003, z), 0.44, 0.33, 0.012, tissu, 'motif'))
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
# PLANCHE DE BORD (1983 et suivants) d'après la photo du poste de conduite (RTA p. XVIII) :
# un grand panneau clair sur toute la largeur, combiné sombre devant le conducteur qui déborde
# sous le panneau (losange Renault), emplacement radio et cendrier au centre, vide-poches côté
# passager, fente de désembuage sur le dessus. Rien sous le panneau à part les commandes.
# =====================================================================================
pb = Part('planche-bord', (-0.45, 0.35, 0))
prof = [(0.636, 1.010), (0.560, 1.013), (0.515, 1.007), (0.500, 0.990), (0.500, 0.860),
        (0.508, 0.842), (0.530, 0.836), (0.636, 0.838)]
pb.add(extrude(prof, 1.30, (0, 0, 0), (0, 0, 1), planche, 'panneau', bev=0.010, up=(0, 1, 0)))
for s_ in (1, -1):   # joues arrondies contre les montants de pare-brise
    pb.add(cyl(0.085, 0.03, (0.56, 0.925, s_ * 0.655), (0, 0, 1), planche, 28, name='joue', bev=0.008))
pb.add(box((0.018, 0.004, 1.10), (0.590, 1.0135, 0), noir, 0.0015, 'fente-desembuage'))
for z in (-0.60, 0.60):
    pb.add(box((0.04, 0.005, 0.07), (0.585, 1.013, z), noir, 0.002, 'aerateur'))

# combiné d'instruments : boîtier sombre, visière, compteur rond, témoins 4 × 3, interrupteurs
cz = DRIVER_Z + 0.03
pb.add(box((0.075, 0.190, 0.345), (0.495, 0.915, cz), planche_f, 0.014, 'combine'))
pb.add(box((0.045, 0.014, 0.355), (0.468, 1.004, cz), planche_f, 0.006, 'visiere'))
ix = 0.4565
oz = cz - 0.090                       # compteur à gauche du combiné
pb.add(cyl(0.052, 0.004, (ix, 0.940, oz), (1, 0, 0), cadran, 48, name='compteur'))
pb.add(torus(0.053, 0.0035, (ix - 0.001, 0.940, oz), (1, 0, 0), graduation, 48, 6, 'lunette'))
for k in range(15):                   # graduations 0 → 140 km/h
    a = math.radians(225 - k * 270 / 14)
    ln = 0.010 if k % 2 == 0 else 0.006
    pb.add(box((0.0015, ln, 0.0018), (ix - 0.003, 0.940 + (0.044 - ln / 2) * math.sin(a), oz + (0.044 - ln / 2) * math.cos(a)), graduation, name='graduation'))
pb.add(box((0.0015, 0.0035, 0.040), (ix - 0.004, 0.952, oz + 0.012), aiguille, name='aiguille'))
pb.add(cyl(0.006, 0.004, (ix - 0.004, 0.940, oz), (1, 0, 0), noir, 12, name='axe-aiguille'))
pb.add(box((0.002, 0.008, 0.024), (ix - 0.002, 0.912, oz), graduation, name='totalisateur'))
lamps = [temoin_r, temoin_o, temoin_v, temoin_b, temoin_o, temoin_r, temoin_v, temoin_o, temoin_b, temoin_r, temoin_o, temoin_v]
for r in range(3):
    for c in range(4):
        zz, yy = cz - 0.020 + c * 0.028, 0.968 - r * 0.028
        pb.add(box((0.004, 0.021, 0.021), (ix + 0.001, yy, zz), noir, 0.002, 'cadre-temoin'))
        pb.add(box((0.003, 0.016, 0.016), (ix - 0.001, yy, zz), lamps[r * 4 + c], 0.002, 'temoin'))
pb.add(box((0.003, 0.010, 0.10), (ix - 0.001, 0.896, cz + 0.022), cadran, 0.002, 'jauge-essence'))
pb.add(box((0.002, 0.008, 0.003), (ix - 0.003, 0.896, cz + 0.050), aiguille, name='index-jauge'))
for r in range(4):                    # interrupteurs à bascule à droite du combiné
    for c in range(2):
        pb.add(box((0.010, 0.020, 0.018), (ix - 0.002, 0.975 - r * 0.026, cz + 0.105 + c * 0.024), noir, 0.003, 'interrupteur'))
pb.add(box((0.004, 0.17, 0.33), (ix + 0.003, 0.920, cz), glace_m, 0.004, 'glace'))
# bas du combiné sous le panneau, avec le losange Renault
pb.add(box((0.06, 0.05, 0.22), (0.500, 0.832, cz - 0.03), planche_f, 0.014, 'combine-bas'))
pb.add(extrude([(0, -0.018), (0.012, 0), (0, 0.018), (-0.012, 0)], 0.004, (0.469, 0.832, cz - 0.03), (1, 0, 0), chrome, 'losange', up=(0, 1, 0), bev=0.001))

# centre : emplacement radio (obturateur) et cendrier ; commandes de chauffage sous le panneau
pb.add(box((0.004, 0.050, 0.044), (0.4985, 0.958, -0.070), planche_f, 0.003, 'obturateur-radio'))
pb.add(box((0.006, 0.058, 0.180), (0.4975, 0.958, 0.042), planche_cl, 0.005, 'cendrier'))
pb.add(box((0.004, 0.010, 0.05), (0.4945, 0.958, 0.042), chrome, 0.002, 'poignee-cendrier'))
for k, z in enumerate((0.055, 0.095)):
    pb.add(box((0.06, 0.02, 0.012), (0.53, 0.825, z), noir, 0.003, 'tirette-chauffage'))
    pb.add(box((0.02, 0.018, 0.022), (0.497, 0.825, z), noir, 0.005, 'bouton-chauffage'))
# vide-poches côté passager (creux dans le panneau)
pb.add(box((0.004, 0.125, 0.43), (0.4995, 0.930, 0.355), planche_cl, 0.008, 'vide-poches'))
pb.add(box((0.020, 0.008, 0.43), (0.505, 0.866, 0.355), planche, 0.003, 'rebord-vide-poches'))
# starter à gauche sous la planche
pb.add(cyl(0.010, 0.04, (0.52, 0.825, -0.56), (1, 0, 0), noir, 12, name='starter'))
pb.add(cyl(0.015, 0.012, (0.50, 0.825, -0.56), (1, 0, 0), chrome, 16, name='bouton-starter'))
# rétroviseur intérieur (rectangle arrondi large) au haut du pare-brise
pb.add(tube([(0.37, 1.465, 0.0), (0.39, 1.43, 0.0)], 0.005, noir))
pb.add(extrude(rounded_rect(0.20, 0.055, 0.025), 0.022, (0.395, 1.405, 0.0), (1, 0, 0), noir, 'retro-int', bev=0.004))
pb.add(extrude(rounded_rect(0.188, 0.045, 0.02), 0.002, (0.383, 1.405, 0.0), (1, 0, 0), reflecteur, 'miroir'))
# pare-soleil
for z in (-0.33, 0.33):
    pb.add(box((0.20, 0.012, 0.34), (0.26, 1.46, z), M('pare-soleil', 0x8a8178, 0.0, 0.9), 0.005, 'pare-soleil'))
fasteners(pb, 'vis-planche', [((0.499, 0.99, -0.60), (-1, 0, 0)), ((0.499, 0.99, 0.60), (-1, 0, 0)), ((0.507, 0.845, -0.05), (-1, 0, 0)), ((0.507, 0.845, 0.20), (-1, 0, 0))], kind='screw', r=0.005, length=0.025, travel=0.04)

# =====================================================================================
# VOLANT ET COLONNE (joint souple vers le boîtier de crémaillère). Volant 1983 : jante claire,
# branche basse large qui relie la jante à 4 h et 8 h, moyeu sous cache (photo p. XVIII).
# =====================================================================================
import mathutils  # noqa: E402
vo = Part('volant', (-0.45, 0.45, 0))
c0, c1 = (0.80, 0.76, DRIVER_Z), (0.43, 1.03, DRIVER_Z)
d = (c1[0] - c0[0], c1[1] - c0[1], 0)
ln = math.hypot(d[0], d[1])
u = (d[0] / ln, d[1] / ln, 0)
vo.add(tube([c0, (c1[0] - u[0] * 0.05, c1[1] - u[1] * 0.05, DRIVER_Z)], 0.017, acier_noir, seg=12))   # arbre (s'arrête dans le moyeu)
vo.add(tube([(c0[0] + u[0] * 0.30, c0[1] + u[1] * 0.30, DRIVER_Z), (c1[0] - u[0] * 0.02, c1[1] - u[1] * 0.02, DRIVER_Z)], 0.030, planche_f, seg=16))   # carénage
vo.add(box((0.07, 0.06, 0.05), (0.50, 0.975, DRIVER_Z + 0.06), planche_f, 0.012, 'antivol'))
for k in range(2):   # commodos
    vo.add(tube([(0.50, 0.985 - k * 0.02, DRIVER_Z + (0.03 if k else -0.03)), (0.47, 0.99 - k * 0.02, DRIVER_Z + (0.16 if k else -0.16))], 0.005, noir, seg=6))
wc = (c1[0] - u[0] * 0.035, c1[1] - u[1] * 0.035, DRIVER_Z)
ax = (-u[0], -u[1], 0)
n = mathutils.Vector(ax)
side = mathutils.Vector((0, 0, 1))
up = n.cross(side).normalized()
if up.y < 0:
    up = -up
W0 = mathutils.Vector(wc)


def wpt(h, v, depth=0.0):
    """Point dans le plan du volant : h vers la droite, v vers le haut, depth vers le conducteur."""
    return tuple(W0 + side * h + up * v - n * depth)


vo.add(torus(0.195, 0.014, wc, ax, volant_m, 64, 12, 'jante'))
vo.add(lathe([(0.0, 0.030), (0.038, 0.026), (0.045, 0.008), (0.040, -0.012), (0.0, -0.014)], wc, ax, noir, 28, 'moyeu'))
# branche basse : plaque rembourrée entre 8 h et 4 h, reliée au moyeu par une âme
bar = extrude(rounded_rect(0.29, 0.060, 0.026), 0.026, wpt(0, -0.118, 0.006), ax, volant_m, 'branche', bev=0.008, up=tuple(up))
vo.add(bar)
for sgn in (1, -1):
    vo.add(tube([wpt(sgn * 0.13, -0.110, 0.006), wpt(sgn * 0.165, -0.103, 0.003), wpt(sgn * 0.185, -0.07, 0.0)], 0.012, volant_m, seg=10))
vo.add(tube([wpt(0, -0.02, 0.0), wpt(0, -0.06, 0.006), wpt(0, -0.095, 0.008)], 0.016, volant_m, seg=10))
vo.add(cyl(0.034, 0.010, wpt(0, 0, 0.024), ax, volant_m, 28, name='cache-moyeu', bev=0.003))
vo.add(extrude([(0, -0.011), (0.008, 0), (0, 0.011), (-0.008, 0)], 0.002, wpt(0, -0.118, 0.020), ax, chrome, 'losange-volant', up=tuple(up)))
vo.add(cyl(0.04, 0.03, (0.92, 0.66, DRIVER_Z + 0.03), (1, -0.5, 0.2), caoutchouc, 20, name='joint-souple'))
fastener(vo, 'ecrou-volant', wpt(0, 0, -0.004), ax, kind='nut', r=0.011, length=0.03, travel=0.06)

# =====================================================================================
# LEVIER « TROMBONE » : sort sous la planche au centre, pommeau relevé (photo p. XVIII) ;
# tige au-dessus du moteur jusqu'au renvoi de boîte
# =====================================================================================
lv = Part('levier-vitesses', (0, 0.45, 0))
lv.add(tube([(0.64, 0.845, 0.035), (0.55, 0.845, 0.035), (0.50, 0.848, 0.036), (0.475, 0.875, 0.036), (0.468, 0.915, 0.036)], 0.008, chrome, seg=10, res=10))
lv.add(lathe([(0.0, -0.032), (0.015, -0.030), (0.022, -0.008), (0.021, 0.018), (0.011, 0.034), (0.0, 0.036)], (0.466, 0.945, 0.036), (-0.15, 1, 0), noir, 24, 'pommeau'))
lv.add(cyl(0.026, 0.04, (0.66, 0.845, 0.035), (1, 0, 0), caoutchouc, 18, name='soufflet'))
lv.add(tube([(0.64, 0.845, 0.035), (0.80, 0.85, 0.035), (1.05, 0.80, 0.04), (1.35, 0.68, 0.03), (1.56, 0.56, 0.01), (1.585, 0.545, 0.0)], 0.008, acier, seg=8, res=14))
lv.add(box((0.05, 0.05, 0.07), (0.71, 0.85, 0.035), acier_noir, 0.008, 'palier-tablier'))

# =====================================================================================
# PÉDALIER : pédales suspendues, axe sous la planche ; tige de poussée du maître-cylindre
# =====================================================================================
pd = Part('pedalier', (-0.3, 0.2, -0.3))
pd.add(cyl(0.008, 0.30, (0.64, 0.86, -0.36), (0, 0, 1), acier, 12))
pd.add(box((0.06, 0.10, 0.30), (0.67, 0.86, -0.36), acier_noir, 0.006, 'support'))


def arm(path, w0, w1):
    """Bras de pédale embouti : contour plan (x, y) le long de `path`, largeur w0 → w1."""
    left, right = [], []
    for k, (x, y) in enumerate(path):
        xa, ya = path[max(k - 1, 0)]
        xb, yb = path[min(k + 1, len(path) - 1)]
        tx, ty = xb - xa, yb - ya
        ln_ = math.hypot(tx, ty)
        nx, ny = -ty / ln_, tx / ln_
        w = (w0 + (w1 - w0) * k / (len(path) - 1)) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


for z, w, nm in ((-0.465, 0.075, 'embrayage'), (-0.355, 0.075, 'frein'), (-0.245, 0.05, 'accelerateur')):
    if nm == 'accelerateur':
        path = [(0.64, 0.86), (0.61, 0.72), (0.565, 0.60), (0.53, 0.53)]
        pd.add(extrude(arm(path, 0.020, 0.012), 0.006, (0, 0, z), (0, 0, 1), acier_noir, 'bras-' + nm, bev=0.001, up=(0, 1, 0)))
        pd.add(box((0.02, 0.11, w), (0.52, 0.47, z), caoutchouc, 0.006, 'patin'))
    else:
        path = [(0.64, 0.86), (0.615, 0.72), (0.565, 0.59), (0.52, 0.52)]
        pd.add(extrude(arm(path, 0.034, 0.020), 0.008, (0, 0, z), (0, 0, 1), acier_noir, 'bras-' + nm, bev=0.0015, up=(0, 1, 0)))
        pd.add(box((0.010, 0.075, w + 0.006), (0.516, 0.49, z), acier_noir, 0.003, 'semelle'))
        pd.add(box((0.012, 0.07, w), (0.507, 0.49, z), caoutchouc, 0.004, 'patin'))
        for k in range(5):   # stries du patin
            pd.add(box((0.003, 0.004, w - 0.01), (0.5005, 0.465 + k * 0.012, z), caoutchouc, 0, 'strie'))
    pd.add(cyl(0.016, 0.03, (0.64, 0.86, z), (0, 0, 1), acier_noir, 16, name='moyeu-pedale'))
pd.add(tube([(0.60, 0.80, -0.465), (0.66, 0.70, -0.50), (0.70, 0.45, -0.52)], 0.004, acier, seg=6))   # ressort de rappel (simplifié)
pd.add(tube([(0.62, 0.78, -0.355), (0.70, 0.80, -0.38), (0.78, 0.82, -0.42)], 0.005, acier, seg=6))   # tige de poussée
pd.add(tube([(0.63, 0.80, -0.465), (0.70, 0.74, -0.42), (0.84, 0.70, -0.40)], 0.004, cable, seg=6))     # câble d'embrayage
pd.add(tube([(0.62, 0.74, -0.245), (0.70, 0.76, -0.32), (0.83, 0.75, -0.40)], 0.0025, cable, seg=6))   # câble d'accélérateur
fastener(pd, 'garde-frein', (0.70, 0.80, -0.38), (-1, -0.25, 0.3), kind='nut', r=0.007, length=0.02, travel=0.03)

# =====================================================================================
# FREIN À MAIN : tirette sous la planche, renvoi, palonnier, câbles vers les mâchoires arrière
# =====================================================================================
fm = Part('frein-main', (0, -0.25, 0))
fm.add(tube([(0.64, 0.815, -0.12), (0.50, 0.815, -0.12)], 0.008, chrome, seg=10))
fm.add(box((0.025, 0.035, 0.10), (0.49, 0.815, -0.12), noir, 0.01, 'poignee'))
fm.add(box((0.06, 0.05, 0.05), (0.66, 0.815, -0.12), acier_noir, 0.006, 'guide'))
fm.add(tube([(0.66, 0.815, -0.12), (0.69, 0.60, -0.12), (0.66, 0.40, -0.10), (0.40, 0.345, -0.05), (-0.40, 0.345, 0.0), (-0.86, 0.345, 0.0)], 0.005, cable, seg=6, res=10))
fm.add(box((0.05, 0.02, 0.14), (-0.88, 0.345, 0), acier_noir, 0.004, 'palonnier'))
for s, x0 in ((1, -1.143), (-1, -1.095)):
    fm.add(tube([(-0.88, 0.345, s * 0.06), (-0.98, 0.33, s * 0.30), (x0 + 0.05, 0.30, s * 0.47), (x0 + 0.02, 0.29, s * 0.50)], 0.004, cable, seg=6, res=10))
fastener(fm, 'reglage-frein-main', (-0.85, 0.345, 0), (1, 0, 0), kind='nut', r=0.007, length=0.025, travel=0.03)

export(OUT)
