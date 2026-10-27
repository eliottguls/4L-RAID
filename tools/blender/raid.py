# Préparation 4L Trophy : équipements ajoutés à la voiture d'origine. Lancer :
#   python3 tools/blender/raid.py   →   models/raid.glb
#
# La RTA ne traite pas de ces pièces ; sources internet :
# - blindages « raid » R4 TL/GTL/Savane/Clan : acier galvanisé 3 mm, plaque moteur fixée sur les
#   4 écrous de la traverse avant / support de boîte, plaque de réservoir sur pattes arrière à écrous
#   cage, kit 8 vis pour les deux plaques, anneaux de remorquage avant et arrière dans le kit complet
#   (vehicules-anciens.fr, fiche « Raid protection plates Renault R4 ») ;
# - règlement 4L Trophy : anneaux de remorquage avant et arrière obligatoires, deux roues de secours,
#   ceintures d'origine ; recommandés : blindages, grillage devant le radiateur, second ventilateur
#   (chacun-sa-route.fr, « 4L Trophy : comment bien préparer son véhicule ») ;
# - liste d'équipement : extincteur 2 kg, jerrican 20 L, sangle de remorquage 5 m avec manille
#   (drivemetotheworld.com, « Check-list 4L Trophy ») ; jerrican 20 L normalisé 470 × 345 × 165 mm.
# Positions des fixations estimées d'après la plateforme (soubassement.py) : elles varient selon
# les fabricants de kits.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, box, cut, cyl, export, extrude, fasteners, lathe, reset, rounded_rect, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'raid.glb')

FLOOR = 0.370
FLOOR_R = 0.470
EX = 0.92                      # milieu du bloc moteur (bouchon de vidange en EX − 0,06)
RX, RY, RZ = -0.99, 0.37, 0.19  # centre du réservoir (soubassement.py)

galva = M('acier-galvanise', 0xa9aca8, 0.75, 0.45)
galva_sombre = M('acier-galvanise-terni', 0x8d908c, 0.7, 0.55)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
rouge = M('rouge-extincteur', 0xb3221c, 0.3, 0.35)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
alu = M('aluminium', 0xb9bdc0, 0.8, 0.35)
kaki = M('jerrican', 0x4c5a35, 0.35, 0.5)
sangle_m = M('sangle', 0xd0602a, 0.0, 0.85)
laiton = M('laiton', 0xc8a24a, 0.9, 0.3)


def sheet(line, t, depth, z, mat, name):
    """Tôle pliée : ligne brisée (x, y) en vue de côté épaissie de t vers le haut, sur la largeur depth."""
    pts = list(line) + [(x, y + t) for x, y in reversed(line)]
    return extrude(pts, depth, (0, 0, z), (0, 0, 1), mat, name, bev=0.0008, up=(0, 1, 0))


# =====================================================================================
# BLINDAGE MOTEUR / BOÎTE : tôle 3 mm de la traverse avant au carter d'huile
# =====================================================================================
bm = Part('blindage-moteur', (0, -0.35, 0))
T3 = 0.003
YB = 0.160                     # sous la traverse de boîte (dessous à 0,175)
side = [(0.70, YB + 0.035), (0.74, YB), (1.50, YB), (1.70, 0.370), (1.715, 0.394), (1.775, 0.394)]
W2 = 0.27                      # demi-largeur : entre les barres de torsion et les bras inférieurs
plate = sheet(side, T3, 2 * W2, 0, galva, 'tole-blindage')
# trou d'accès au bouchon de vidange et lumières d'aération sous le carter
cut(plate, cyl(0.030, 0.05, (EX - 0.06, YB, 0.02), (0, 1, 0), None, 32, name='trou'))
for x in (1.00, 1.16, 1.32):
    for s in (1, -1):
        cut(plate, extrude(rounded_rect(0.09, 0.022, 0.011), 0.05, (x, YB, s * 0.13), (0, 1, 0), None, 'lumiere', up=(1, 0, 0)))
bm.add(plate)
# bords tombés latéraux (raidisseurs) et nervures embouties transversales
for s in (1, -1):
    bm.add(box((0.76, 0.028, T3), (1.12, YB + 0.014, s * (W2 - 0.0015)), galva, 0.001, 'bord-tombe'))
    bm.add(tube([(1.50, YB + 0.014, s * (W2 - 0.0015)), (1.69, 0.376, s * (W2 - 0.0015))], 0.003, galva, 'bord-tombe-rampe', seg=6))
for x in (0.80, 1.08, 1.42):
    bm.add(box((0.022, 0.006, 2 * W2 - 0.06), (x, YB - 0.002, 0), galva, 0.002, 'nervure'))
bm.add(box((0.08, 0.008, 0.10), (EX - 0.06, YB - 0.0035, 0.02), galva_sombre, 0.002, 'renfort-trou'))
# entretoises sous la traverse de boîte
for s in (1, -1):
    bm.add(cyl(0.012, 0.012, (1.14, YB + T3 + 0.006, s * 0.20), (0, 1, 0), galva_sombre, 16, name='entretoise'))
vb = [((1.745, 0.390, s * 0.20), (0, -1, 0)) for s in (1, -1)]
vb += [((1.14, YB - 0.003, s * 0.20), (0, -1, 0)) for s in (1, -1)]
fasteners(bm, 'vis-blindage-moteur', vb, kind='bolt', r=0.006, length=0.035, travel=0.06)

# =====================================================================================
# BLINDAGE RÉSERVOIR : plaque sous la cuve, patte avant sous la traverse arrière, pattes arrière
# =====================================================================================
br = Part('blindage-reservoir', (0, -0.3, 0.1))
YT = 0.285                     # 25 mm sous le fond de cuve
z0, z1 = -0.045, 0.395
side = [(-1.215, YT + 0.03), (-1.19, YT), (-0.80, YT), (-0.74, 0.229), (-0.62, 0.229)]
br.add(sheet(side, T3, z1 - z0, (z0 + z1) / 2, galva, 'tole-blindage'))
for k in range(4):
    br.add(box((0.32, 0.006, 0.022), (-1.00, YT - 0.002, z0 + 0.06 + k * 0.105), galva, 0.002, 'nervure'))
for zz in (z0 + 0.0015, z1 - 0.0015):
    br.add(box((0.39, 0.024, T3), (-1.00, YT + 0.012, zz), galva, 0.001, 'bord-tombe'))
# pattes arrière soudées à écrou cage : vers le longeron arrière droit et le plancher de coffre
for zz, ytop in ((0.37, 0.395), (0.0, FLOOR_R - 0.004)):
    br.add(box((0.04, ytop - YT, 0.004), (-1.17, (YT + ytop) / 2, zz), galva_sombre, 0.001, 'patte-arriere'))
    br.add(box((0.05, 0.004, 0.05), (-1.17, ytop - 0.002, zz), galva_sombre, 0.001, 'semelle-patte'))
    br.add(box((0.018, 0.010, 0.018), (-1.17, ytop + 0.005, zz), acier_noir, 0.002, 'ecrou-cage'))
vr = [((-0.68, 0.226, zz), (0, -1, 0)) for zz in (0.05, 0.30)]
vr += [((-1.17, 0.392, 0.37), (0, -1, 0)), ((-1.17, FLOOR_R - 0.007, 0.0), (0, -1, 0))]
fasteners(br, 'vis-blindage-reservoir', vr, kind='bolt', r=0.006, length=0.03, travel=0.06)

# =====================================================================================
# ANNEAUX DE REMORQUAGE : platine boulonnée sous la traverse avant / le longeron arrière droit
# =====================================================================================
ar = Part('anneaux-remorquage', (0, -0.15, 0))
for xs, yp, zr, sgn in ((1.74, 0.397, 0.33, 1), (-1.74, 0.392, 0.45, -1)):
    ar.add(box((0.13, 0.010, 0.06), (xs, yp - 0.005, zr), acier_noir, 0.003, 'platine'))
    ar.add(box((0.10, 0.016, 0.016), (xs + sgn * 0.11, yp - 0.050, zr), acier_noir, 0.004, 'bras'))
    ar.add(tube([(xs + sgn * 0.04, yp - 0.010, zr), (xs + sgn * 0.07, yp - 0.045, zr)], 0.010, acier_noir, 'jambe', seg=10))
    ar.add(torus(0.032, 0.009, (xs + sgn * 0.19, yp - 0.050, zr), (0, 1, 0), acier_noir, 28, 10, 'anneau'))
fasteners(ar, 'vis-anneaux-remorquage', [((x, yp - 0.010, zr + dz), (0, -1, 0))
                                          for x, yp, zr in ((1.71, 0.397, 0.33), (1.77, 0.397, 0.33), (-1.71, 0.392, 0.45), (-1.77, 0.392, 0.45))
                                          for dz in (0.0,)], kind='bolt', r=0.007, length=0.04, travel=0.06)

# =====================================================================================
# GRILLAGE DE CALANDRE : maille alu derrière la grille, contre le sable et les cailloux
# =====================================================================================
gc = Part('grillage-calandre', (0.35, 0, 0))
GXM = 1.752                    # juste derrière la calandre (face avant à 1,766)
Y0, Y1, ZW = 0.592, 0.760, 0.312
gc.add(box((0.004, Y1 - Y0 + 0.02, 0.012), (GXM, (Y0 + Y1) / 2, ZW + 0.004), alu, 0.001, 'cadre'))
gc.add(box((0.004, Y1 - Y0 + 0.02, 0.012), (GXM, (Y0 + Y1) / 2, -ZW - 0.004), alu, 0.001, 'cadre'))
gc.add(box((0.004, 0.012, 2 * ZW + 0.02), (GXM, Y0 - 0.004, 0), alu, 0.001, 'cadre'))
gc.add(box((0.004, 0.012, 2 * ZW + 0.02), (GXM, Y1 + 0.004, 0), alu, 0.001, 'cadre'))
H = Y1 - Y0
PITCH = 0.018                  # maille losangée : fils croisés à ±45°, découpés au cadre
for d in (1, -1):
    c = -ZW - H
    while c < ZW + H:
        # fil z = c + d·(y − Y0) borné au cadre
        ya = max(Y0, Y0 + (-ZW - c) / d if d > 0 else Y0 + (ZW - c) / d)
        yb = min(Y1, Y0 + (ZW - c) / d if d > 0 else Y0 + (-ZW - c) / d)
        if yb - ya > 0.004:
            gc.add(tube([(GXM, ya, c + d * (ya - Y0)), (GXM, yb, c + d * (yb - Y0))], 0.0009, alu, 'fil', seg=4))
        c += PITCH
gc_fx = [((GXM - 0.004, y, s * ZW), (-1, 0, 0)) for y in (Y0 + 0.02, Y1 - 0.02) for s in (1, -1)]
fasteners(gc, 'colliers-grillage', gc_fx, kind='pin', r=0.002, length=0.012, travel=0.03)

# =====================================================================================
# EXTINCTEUR 2 kg à poudre : couché entre les sièges avant sur un support à deux colliers
# =====================================================================================
ext = Part('extincteur', (0, 0.4, 0))
EC = (0.32, FLOOR + 0.072, 0.0)
ext.add(lathe([(0.0, 0.0), (0.050, 0.0), (0.055, 0.008), (0.055, 0.26), (0.048, 0.29), (0.022, 0.305), (0.0, 0.305)], (EC[0] - 0.16, EC[1], EC[2]), (1, 0, 0), rouge, 40, 'bouteille'))
ext.add(cyl(0.017, 0.03, (EC[0] + 0.16, EC[1], 0), (1, 0, 0), laiton, 16, name='tete'))
ext.add(box((0.06, 0.014, 0.022), (EC[0] + 0.19, EC[1] + 0.022, 0), noir, 0.004, 'poignee'))
ext.add(box((0.05, 0.010, 0.018), (EC[0] + 0.19, EC[1] + 0.040, 0), noir, 0.003, 'gachette'))
ext.add(cyl(0.010, 0.012, (EC[0] + 0.175, EC[1] + 0.03, 0.026), (0, 0, 1), alu, 16, name='manometre'))
ext.add(tube([(EC[0] + 0.19, EC[1], -0.012), (EC[0] + 0.15, EC[1] - 0.02, -0.05), (EC[0] - 0.10, EC[1] - 0.02, -0.058)], 0.006, noir, 'flexible', seg=8))
ext.add(box((0.30, 0.004, 0.10), (EC[0], FLOOR + 0.006, 0), acier_noir, 0.001, 'semelle-support'))
for dx in (-0.09, 0.09):
    ext.add(torus(0.057, 0.004, (EC[0] + dx, EC[1], 0), (1, 0, 0), acier_noir, 32, 6, 'collier'))
    ext.add(box((0.018, 0.012, 0.03), (EC[0] + dx, EC[1] + 0.06, 0), acier_noir, 0.002, 'agrafe'))
fasteners(ext, 'vis-support-extincteur', [((EC[0] + dx, FLOOR + 0.009, dz), (0, 1, 0)) for dx in (-0.13, 0.13) for dz in (-0.035, 0.035)],
          kind='bolt', r=0.004, length=0.02, travel=0.04)

# =====================================================================================
# JERRICAN 20 L (470 × 345 × 165 mm) debout dans le coffre, côté gauche, sanglé
# =====================================================================================
jc = Part('jerrican', (-0.3, 0.3, 0))
JC = (-1.40, FLOOR_R + 0.008 + 0.235, -0.33)
body = box((0.345, 0.43, 0.165), (JC[0], JC[1] - 0.02, JC[2]), kaki, 0.018, 'jerrican')
jc.add(body)
for s in (1, -1):                 # embouti en X des flancs
    for d in (1, -1):
        jc.add(tube([(JC[0] - 0.13, JC[1] - 0.18, JC[2] + s * 0.083), (JC[0] + 0.13, JC[1] + 0.13, JC[2] + s * 0.083)] if d > 0 else
                    [(JC[0] + 0.13, JC[1] - 0.18, JC[2] + s * 0.083), (JC[0] - 0.13, JC[1] + 0.13, JC[2] + s * 0.083)], 0.006, kaki, 'embouti', seg=6))
for dx in (-0.09, 0.0, 0.09):     # trois poignées
    jc.add(box((0.022, 0.035, 0.05), (JC[0] + dx, JC[1] + 0.215, JC[2]), kaki, 0.006, 'poignee'))
jc.add(cyl(0.022, 0.03, (JC[0] + 0.14, JC[1] + 0.21, JC[2]), (0.6, 1, 0), kaki, 20, name='bec'))
jc.add(box((0.03, 0.018, 0.05), (JC[0] + 0.15, JC[1] + 0.235, JC[2]), kaki, 0.004, 'levier-bouchon'))
jc.add(box((0.36, 0.035, 0.004), (JC[0], JC[1] - 0.02, JC[2] - 0.085), sangle_m, 0.001, 'sangle'))
jc.add(box((0.36, 0.035, 0.004), (JC[0], JC[1] - 0.02, JC[2] + 0.085), sangle_m, 0.001, 'sangle'))
jc.add(box((0.004, 0.035, 0.17), (JC[0] - 0.175, JC[1] - 0.02, JC[2]), sangle_m, 0.001, 'sangle'))
jc.add(box((0.004, 0.035, 0.17), (JC[0] + 0.175, JC[1] - 0.02, JC[2]), sangle_m, 0.001, 'sangle'))
jc.add(box((0.04, 0.012, 0.025), (JC[0] + 0.178, JC[1] - 0.02, JC[2] + 0.04), acier_noir, 0.003, 'boucle'))
for dz in (-0.12, 0.12):
    jc.add(box((0.03, 0.004, 0.03), (JC[0] - 0.19, FLOOR_R + 0.010, JC[2] + dz), acier_noir, 0.001, 'ancrage'))
fasteners(jc, 'ancrages-jerrican', [((JC[0] - 0.19, FLOOR_R + 0.012, JC[2] + dz), (0, 1, 0)) for dz in (-0.12, 0.12)],
          kind='bolt', r=0.004, length=0.02, travel=0.04)

export(OUT)
