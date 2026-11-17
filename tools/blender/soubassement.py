# Soubassement de la Renault 4 GTL : plateforme (cadre plancher) pièce par pièce, boulons de caisse,
# circuit de carburant (réservoir, jauge, goulotte, canalisation, filtre) et ligne d'échappement
# (descente, silencieux, tuyaux, colliers, suspentes). Lancer :
#   python3 tools/blender/soubassement.py   →   models/soubassement.glb
#
# RTA (pages du PDF) :
# - « Carrosserie boulonnée sur cadre plancher » ; réservoir 34 L de supercarburant ; garde au sol en
#   charge 175 mm (p.79) ;
# - cric de bord : deux encoches de chaque côté sous la carrosserie, près des roues ; levage latéral
#   sous le plancher à l'aplomb du pied milieu ; ponts à prise sous caisse : patins sur toute leur
#   surface (p.10, 11, 19) ;
# - échappement (planche 9, p.36) : collecteur (1), joint (2), goujons (3), tôle pare-chaleur (4),
#   bride à ressorts de la descente (5), descente (6), collier (7), silencieux (8) sous le compartiment
#   moteur, colliers (9), tuyau intermédiaire (10), suspente élastique à goujon (11), tuyau arrière (12) ;
# - pompe à essence mécanique à membrane, pression 0,17 à 0,265 bar (p.22) ; rhéostat de jauge à
#   essence sur le câblage arrière, raccordement « câblage réservoir » (p.76, 86).
# La RTA ne cote ni la plateforme, ni le réservoir, ni le tracé des tuyaux : sections, positions et
# nombre de boulons sont estimés d'après les vues de la RTA et l'implantation des trains (trains.py).
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, box, cyl, export, extrude, fasteners, lathe, reset, rounded_rect, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'soubassement.glb')

AXLE_F = 1.306
PIVOT_R = {1: -0.70, -1: -0.65}      # tubes d'articulation des bras arrière (voir trains.py)
FLOOR = 0.370          # dessus du plancher avant
FLOOR_R = 0.470        # plancher de coffre
TABLIER_X = 0.700
LZ = 0.665             # axe des longerons latéraux (bas de caisse)
EX, YD = 0.92, 0.596   # moteur : milieu du bloc, plan de joint (voir moteur.py)

tole = M('tole-plateforme', 0x34383b, 0.45, 0.55)
tole_cl = M('tole-plancher', 0x464b4f, 0.4, 0.6)
mastic = M('mastic-joint', 0x2b2c2a, 0.0, 0.9)
tapis = M('tapis', 0x1f1f20, 0.0, 0.95)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
zinc = M('zinc', 0xc9c4ae, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
ech = M('acier-echappement', 0x5b5853, 0.6, 0.6)
ech_chaud = M('acier-echappement-brule', 0x6b5545, 0.6, 0.55)
reservoir_m = M('reservoir', 0x2f3336, 0.5, 0.5)
durite = M('durite-essence', 0x26272a, 0.0, 0.8)
nylon = M('filtre-essence', 0xe8e4d2, 0.0, 0.3, alpha=0.55)
papier = M('papier', 0xd9cf9e, 0.0, 0.9)
essence = M('essence', 0xd8b54a, 0.0, 0.15, alpha=0.5)
laiton = M('laiton', 0xc8a24a, 0.9, 0.3)
fil = M('fil', 0x2a2a2a, 0.2, 0.6)
fil_vert = M('fil-vert', 0x3f7a4a, 0.1, 0.55)


def xbeam(prof, x0, x1, y, z, mat, name='poutre', bev=0.0):
    """Profil (u, v) extrudé le long de x entre x0 et x1 ; u vers -z du site, v vers le haut."""
    return extrude(prof, abs(x1 - x0), ((x0 + x1) / 2, y, z), (1, 0, 0), mat, name, bev=bev, up=(0, 1, 0))


def zbeam(prof, z0, z1, x, y, mat, name='traverse', bev=0.0):
    """Profil (u, v) extrudé le long de z entre z0 et z1 ; u vers +x du site, v vers le haut."""
    return extrude(prof, abs(z1 - z0), (x, y, (z0 + z1) / 2), (0, 0, 1), mat, name, bev=bev, up=(0, 1, 0))


def beam(p0, p1, w, h, mat, name='poutre', r=0.006):
    """Poutre caisson de section w × h entre deux points (non vertical)."""
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in d))
    mid = tuple((p0[i] + p1[i]) / 2 for i in range(3))
    return extrude(rounded_rect(w, h, r), ln, mid, tuple(c / ln for c in d), mat, name, up=(0, 1, 0))


def hat(w, h, f):
    """Section en oméga (profil embouti à bords tombés), ouverte vers le bas."""
    return [(-w / 2 - f, -h / 2), (-w / 2, -h / 2), (-w / 2 + 0.004, h / 2), (w / 2 - 0.004, h / 2), (w / 2, -h / 2), (w / 2 + f, -h / 2),
            (w / 2 + f, -h / 2 + 0.002), (w / 2 - 0.002, -h / 2 + 0.002), (w / 2 - 0.006, h / 2 - 0.002), (-w / 2 + 0.006, h / 2 - 0.002),
            (-w / 2 + 0.002, -h / 2 + 0.002), (-w / 2 - f, -h / 2 + 0.002)]


def plug(part, pos, r, up=1):
    """Obturateur caoutchouc d'un trou d'écoulement ou d'emboutissage."""
    part.add(cyl(r, 0.004, pos, (0, 1, 0), caoutchouc, 18, name='obturateur'))
    part.add(torus(r * 0.9, 0.0018, (pos[0], pos[1] - up * 0.002, pos[2]), (0, 1, 0), caoutchouc, 18, 6, 'levre'))


def collar(part, pos, axis, r, mat=zinc, name='collier'):
    """Collier à vis (durite) : bande, boîtier et vis."""
    part.add(torus(r + 0.0015, 0.0016, pos, axis, mat, 24, 6, name))
    part.add(box((0.008, 0.006, 0.010), (pos[0], pos[1] + r + 0.004, pos[2]), mat, 0.001, 'boitier-collier'))


# =====================================================================================
# PLATEFORME : plancher, longerons, brancards, traverses, supports
# =====================================================================================
pl = Part('plateforme', (0, -0.45, 0))
# ---- plancher avant : tôle et nervures embouties longitudinales et transversales
pl.add(box((TABLIER_X + 0.58, 0.003, 1.21), ((TABLIER_X - 0.58) / 2, FLOOR - 0.0015, 0), tole_cl, name='plancher-avant'))
for z in (-0.47, -0.36, -0.20, -0.07, 0.07, 0.20, 0.36, 0.47):
    pl.add(xbeam([(-0.018, 0.0), (-0.011, 0.007), (0.011, 0.007), (0.018, 0.0)], -0.54, 0.64, FLOOR - 0.001, z, tole_cl, 'nervure'))
for x in (0.42, -0.18):
    pl.add(zbeam([(-0.016, 0.0), (-0.010, 0.006), (0.010, 0.006), (0.016, 0.0)], -0.58, 0.58, x, FLOOR - 0.001, tole_cl, 'nervure-transversale'))
for x, z in ((0.55, 0.30), (0.55, -0.30), (0.10, 0.42), (0.10, -0.42), (-0.42, 0.28), (-0.42, -0.28)):
    plug(pl, (x, FLOOR - 0.002, z), 0.012)
# tapis caoutchouc posés sur le plancher (avant et places arrière)
for s in (1, -1):
    pl.add(box((0.62, 0.005, 0.42), (0.27, FLOOR + 0.0085, s * 0.32), tapis, 0.003, 'tapis-avant'))
    pl.add(box((0.30, 0.005, 0.42), (-0.32, FLOOR + 0.0085, s * 0.32), tapis, 0.003, 'tapis-arriere'))
    for k in range(9):   # stries du tapis avant
        pl.add(box((0.012, 0.002, 0.38), (0.06 + k * 0.05, FLOOR + 0.0115, s * 0.32), tapis, name='strie'))
# ---- longerons latéraux (bas de caisse) : caisson fermé, bord de soudure, trous d'écoulement
SILL = [(0.060, -0.058), (-0.050, -0.058), (-0.060, -0.048), (-0.060, 0.050), (-0.052, 0.058), (0.040, 0.058), (0.060, 0.040)]
for s in (1, -1):
    prof = [(-s * u, v) for u, v in SILL]
    pl.add(xbeam(prof if s > 0 else prof[::-1], -0.80, 0.98, 0.325, s * LZ, tole, 'longeron', bev=0.004))
    pl.add(xbeam([(-0.003, -0.02), (0.003, -0.02), (0.003, 0.0), (-0.003, 0.0)], -0.78, 0.96, 0.395, s * (LZ + 0.058), tole, 'bord-soudure'))
    for x in [-0.70 + k * (1.58 / 11) for k in range(12)]:
        pl.add(cyl(0.0035, 0.004, (x, 0.3895, s * (LZ + 0.058)), (0, 0, 1), acier_noir, 8, name='point-soudure'))
    for x in (-0.55, -0.10, 0.35, 0.80):
        pl.add(cyl(0.006, 0.003, (x, 0.2665, s * LZ), (0, 1, 0), noir, 12, name='trou-ecoulement'))
    for xe in (-0.80, 0.98):   # fermetures d'extrémité
        pl.add(box((0.004, 0.11, 0.115), (xe, 0.325, s * LZ), tole, 0.002, 'fermeture'))
    # encoches de cric (p.10) près des roues, renfort au pied milieu (levage latéral)
    for xj in (0.93, -0.62):
        pl.add(box((0.09, 0.012, 0.05), (xj, 0.262, s * LZ), acier_noir, 0.003, 'encoche-cric'))
        pl.add(box((0.05, 0.006, 0.018), (xj, 0.255, s * LZ), noir, 0.002, 'lumiere-cric'))
    pl.add(box((0.14, 0.006, 0.07), (0.0, 0.264, s * LZ), acier_noir, 0.002, 'renfort-pied-milieu'))
# ---- brancards avant : caisson relevé au droit des transmissions jusqu'à la traverse avant
BR = 0.40
for s in (1, -1):
    pts = [(TABLIER_X - 0.12, 0.335), (0.95, 0.35), (1.12, 0.405), (1.50, 0.415), (1.74, 0.425)]
    for a, b in zip(pts, pts[1:]):
        pl.add(beam((a[0], a[1], s * BR), (b[0], b[1], s * BR), 0.055, 0.065, tole, 'brancard'))
        pl.add(beam((a[0], a[1] + 0.034, s * BR), (b[0], b[1] + 0.034, s * BR), 0.075, 0.004, tole, 'semelle', 0.001))
    # chapes du bras supérieur (axe y 0.48, z 0.36) : deux platines sur le brancard
    for x in (AXLE_F - 0.10, AXLE_F + 0.10):
        pl.add(box((0.012, 0.09, 0.07), (x + (0.03 if x > AXLE_F else -0.03), 0.455, s * 0.355), tole, 0.003, 'chape-bras-superieur'))
    pl.add(box((0.26, 0.012, 0.08), (AXLE_F, 0.50, s * 0.37), tole, 0.003, 'platine-chapes'))
    # chapes du bras inférieur (axe x AXLE_F − 0.13, y 0.205, z 0.30) : pattes descendantes
    for x in (AXLE_F - 0.235, AXLE_F - 0.015):
        pl.add(extrude([(-0.025, 0.0), (0.025, 0.0), (0.02, 0.20), (-0.035, 0.20)], 0.008, (x, 0.19, s * 0.33), (1, 0, 0), tole, 'chape-bras-inferieur', bev=0.002, up=(0, 1, 0)))
    pl.add(beam((AXLE_F - 0.24, 0.39, s * 0.37), (AXLE_F - 0.01, 0.39, s * 0.37), 0.04, 0.03, tole, 'renfort-chapes'))
    # tourelle d'amortisseur et gousset vers l'aile intérieure
    pl.add(box((0.08, 0.05, 0.10), (AXLE_F + 0.17, 0.645, s * 0.45), tole, 0.01, 'tourelle'))
    pl.add(beam((AXLE_F + 0.17, 0.62, s * 0.42), (AXLE_F + 0.10, 0.44, s * 0.40), 0.03, 0.03, tole, 'jambe-tourelle'))
    pl.add(box((0.06, 0.06, 0.07), (AXLE_F + 0.38, 0.41, s * 0.40), tole, 0.006, 'support-tirant'))
    plug(pl, (1.02, 0.3155, s * BR), 0.010, up=-1)
pl.add(beam((1.74, 0.43, -0.44), (1.74, 0.43, 0.44), 0.06, 0.06, tole, 'traverse-avant'))
for s in (1, -1):
    pl.add(box((0.06, 0.10, 0.10), (1.72, 0.47, s * 0.36), tole, 0.008, 'gousset-traverse'))
pl.add(beam((1.14, 0.20, -0.40), (1.14, 0.20, 0.40), 0.05, 0.05, tole, 'traverse-boite'))
for s in (1, -1):
    pl.add(box((0.04, 0.19, 0.04), (1.14, 0.29, s * 0.40), tole, 0.006, 'jambe-traverse'))
# tablier inférieur : bavolet soudé au plancher, entre les brancards
pl.add(box((0.006, 0.05, 1.12), (TABLIER_X + 0.003, FLOOR + 0.025, 0), tole_cl, 0.002, 'bavolet'))
# ---- traverse sous les sièges avant (ancrage des barres de torsion avant, p.55)
pl.add(zbeam(hat(0.10, 0.07, 0.02), -0.61, 0.61, 0.0, 0.33, tole, 'traverse-sieges', bev=0.002))
for s in (1, -1):
    pl.add(box((0.12, 0.08, 0.10), (0.0, 0.31, s * 0.30), tole, 0.008, 'chape-ancrage-barre'))
# ---- talon de siège arrière, traverse arrière (passage des barres de torsion), plancher de coffre
pl.add(zbeam([(-0.58, FLOOR), (-0.60, FLOOR), (-0.78, FLOOR_R), (-0.76, FLOOR_R)], -0.60, 0.60, 0, 0, tole_cl, 'talon'))
pl.add(zbeam(rounded_rect(0.17, 0.09, 0.015), -0.66, 0.66, -0.675, 0.28, tole, 'traverse-arriere'))
for s in (1, -1):
    for xp in PIVOT_R.values():   # trous de passage des barres
        pl.add(cyl(0.016, 0.004, (xp, 0.275, s * 0.665), (0, 0, 1), noir, 16, name='passage-barre'))
    pl.add(box((0.20, 0.10, 0.006), (-0.675, 0.30, s * 0.665), tole, 0.002, 'flasque-traverse'))
pl.add(box((1.02, 0.003, 1.12), (-1.27, FLOOR_R - 0.0015, 0), tole_cl, name='plancher-coffre'))
for z in (-0.40, -0.25, -0.10, 0.10, 0.25, 0.40):
    pl.add(xbeam([(-0.016, 0.0), (-0.010, 0.006), (0.010, 0.006), (0.016, 0.0)], -1.72, -0.82, FLOOR_R - 0.001, z, tole_cl, 'nervure-coffre'))
pl.add(box((0.90, 0.005, 0.90), (-1.27, FLOOR_R + 0.0045, 0), tapis, 0.003, 'tapis-coffre'))
pl.add(cyl(0.05, 0.006, (-0.92, FLOOR_R + 0.008, 0.10), (0, 1, 0), tapis, 24, name='trappe-jauge'))   # accès à la jauge
for x, z in ((-1.00, -0.32), (-1.50, 0.32), (-1.50, -0.32)):
    plug(pl, (x, FLOOR_R - 0.002, z), 0.012)
for s in (1, -1):
    pl.add(beam((-0.78, 0.43, s * 0.45), (-1.77, 0.43, s * 0.45), 0.06, 0.07, tole, 'longeron-arriere'))
    pl.add(box((0.10, 0.05, 0.05), (-1.80, 0.425, s * 0.29), acier_noir, 0.006, 'patte-pare-chocs'))
    # platines des paliers de bras arrière (3 vis, trains.py) sous le longeron arrière
    for zz in (0.285, 0.535):
        pl.add(box((0.13, 0.008, 0.05), (PIVOT_R[s], 0.358, s * zz), tole, 0.002, 'platine-palier'))
pl.add(beam((-1.765, 0.42, -0.60), (-1.765, 0.42, 0.60), 0.05, 0.07, tole, 'traverse-seuil'))
# berceau de roue de secours : crémaillère sous la traverse
pl.add(box((0.03, 0.10, 0.05), (-1.76, 0.33, 0), acier_noir, 0.004, 'cremaillere-secours'))
for k in range(2):
    pl.add(box((0.012, 0.012, 0.05), (-1.745, 0.30 + k * 0.035, 0), acier, 0.002, 'cran'))
# cordons de mastic d'étanchéité caisse / plateforme
for s in (1, -1):
    pl.add(xbeam(rounded_rect(0.008, 0.004, 0.0015), -0.76, 0.94, 0.385, s * (LZ - 0.035), mastic, 'cordon-mastic'))

# ---- boulons de caisse sur plateforme : longerons, brancards, traverse avant et seuil (indicatif)
bc = []
for s in (1, -1):
    for x in (0.86, 0.50, 0.12, -0.28, -0.66):
        bc.append(((x, 0.266, s * (LZ - 0.02)), (0, -1, 0)))
for s in (1, -1):
    bc.append(((TABLIER_X - 0.08, 0.302, s * BR), (0, -1, 0)))
    bc.append(((1.74, 0.400, s * 0.30), (0, -1, 0)))
for z in (-0.40, 0.0, 0.40):
    bc.append(((-1.765, 0.385, z), (0, -1, 0)))
fasteners(pl, 'boulons-caisse', bc, kind='bolt', r=0.007, length=0.06, travel=0.08)

# =====================================================================================
# RÉSERVOIR 34 L sous le plancher arrière droit : coquilles agrafées, sangles, goulotte, mise à l'air
# =====================================================================================
RX, RY, RZ = -0.99, 0.37, 0.19          # centre du réservoir
rs = Part('reservoir', (0, -0.35, 0.2))
rs.add(box((0.34, 0.12, 0.40), (RX, RY, RZ), reservoir_m, 0.035, 'cuve'))
rs.add(box((0.37, 0.004, 0.43), (RX, RY + 0.005, RZ), reservoir_m, 0.0015, 'agrafage'))           # bord des deux coquilles
for k in range(3):                      # emboutis de rigidité du fond
    rs.add(box((0.26, 0.006, 0.03), (RX, RY - 0.061, RZ - 0.12 + k * 0.12), reservoir_m, 0.003, 'embouti'))
for s in (1, -1):                       # pattes de fixation avant
    rs.add(box((0.03, 0.004, 0.06), (RX + s * 0.20, RY + 0.005, RZ + 0.16), reservoir_m, 0.001, 'patte'))
rs.add(cyl(0.012, 0.03, (RX + 0.10, RY - 0.05, RZ - 0.15), (1, 0, 0), laiton, 14, name='depart-essence'))   # tube de départ
rs.add(lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.004), (0.0, 0.004)], (RX, RY - 0.064, RZ + 0.12), (0, 1, 0), reservoir_m, 20, 'bossage-vidange'))
# goulotte : manchon caoutchouc sur la cuve, tube rigide vers la trappe arrière droite, bouchon
rs.add(cyl(0.030, 0.04, (RX - 0.13, RY + 0.06, RZ + 0.17), (-0.6, 0.4, 0.5), reservoir_m, 24, name='tubulure'))
gl = [(RX - 0.15, RY + 0.075, RZ + 0.185), (-1.22, 0.48, 0.43), (-1.40, 0.58, 0.55), (-1.52, 0.68, 0.64), (-1.585, 0.79, 0.705)]
rs.add(tube(gl[:2], 0.026, caoutchouc, 'manchon-goulotte', seg=16))
rs.add(tube(gl[1:], 0.021, acier_noir, 'goulotte', seg=14, res=10))
rs.add(tube([(RX - 0.10, RY + 0.06, RZ + 0.19), (-1.20, 0.50, 0.40), (-1.45, 0.66, 0.57), (-1.56, 0.76, 0.66)], 0.004, caoutchouc, 'mise-a-l-air', seg=6, res=10))
for p in (gl[0], gl[1]):
    collar(rs, p, (-0.6, 0.4, 0.5), 0.027)
rs.add(lathe([(0.0, 0.0), (0.030, 0.0), (0.032, 0.006), (0.032, 0.018), (0.024, 0.024), (0.0, 0.026)], (-1.592, 0.80, 0.712), (-0.3, 0.3, 1), acier_noir, 28, 'bouchon'))
rs.add(box((0.032, 0.006, 0.010), (-1.585, 0.812, 0.725), acier_noir, 0.002, 'oreille-bouchon'))
# sangles de maintien sous la cuve, vissées dans le plancher de coffre
for x in (RX - 0.10, RX + 0.10):
    rs.add(box((0.03, 0.003, 0.44), (x, RY - 0.0625, RZ), acier_noir, 0.001, 'sangle'))
    for zz in (RZ - 0.22, RZ + 0.22):
        rs.add(box((0.03, 0.09, 0.003), (x, RY + 0.0, zz), acier_noir, 0.001, 'retour-sangle'))
sv = []
for x in (RX - 0.10, RX + 0.10):
    for zz in (RZ - 0.225, RZ + 0.225):
        sv.append(((x, RY + 0.05, zz + (0.012 if zz > RZ else -0.012)), (0, -1, 0)))
fasteners(rs, 'vis-sangles-reservoir', sv, kind='bolt', r=0.006, length=0.05, travel=0.06)
fasteners(rs, 'colliers-goulotte', [((gl[0][0], gl[0][1] + 0.031, gl[0][2]), (0, 1, 0)), ((gl[1][0], gl[1][1] + 0.031, gl[1][2]), (0, 1, 0))], kind='screw', r=0.003, length=0.012, travel=0.02)

# ---- jauge (émetteur à rhéostat) sur le dessus de la cuve, sous la trappe du plancher de coffre
jg = Part('jauge-carburant', (0, 0.25, 0))
JX, JY, JZ = -0.92, RY + 0.062, 0.10
jg.add(lathe([(0.0, 0.0), (0.034, 0.0), (0.034, 0.006), (0.026, 0.010), (0.0, 0.011)], (JX, JY, JZ), (0, 1, 0), zinc, 28, 'platine-jauge'))
jg.add(torus(0.038, 0.003, (JX, JY + 0.002, JZ), (0, 1, 0), caoutchouc, 28, 6, 'joint-jauge'))
jg.add(lathe([(0.033, 0.0), (0.044, 0.0), (0.044, 0.008), (0.033, 0.008)], (JX, JY + 0.004, JZ), (0, 1, 0), acier_noir, 32, 'bague'))
for k in range(4):     # ergots de la bague à baïonnette
    a = 2 * math.pi * k / 4 + 0.3
    jg.add(box((0.012, 0.007, 0.010), (JX + 0.047 * math.cos(a), JY + 0.008, JZ + 0.047 * math.sin(a)), acier_noir, 0.002, 'ergot', axis=(math.cos(a), 0, math.sin(a))))
for k, mat in enumerate((fil_vert, fil)):   # cosses : rhéostat et masse
    jg.add(box((0.006, 0.010, 0.004), (JX - 0.010 + k * 0.020, JY + 0.016, JZ), laiton, 0.001, 'cosse'))
    jg.add(tube([(JX - 0.010 + k * 0.020, JY + 0.020, JZ), (JX - 0.03 + k * 0.02, JY + 0.03, JZ - 0.06), (-0.80, 0.42, -0.05), (-0.70, 0.44, -0.45), (-0.60, 0.40, -0.60)], 0.0022, mat, 'fil-jauge', seg=6, res=8))
# dans la cuve : tube plongeur, crépine, bras et flotteur, piste du rhéostat
jg.add(tube([(JX, JY, JZ), (JX, RY - 0.050, JZ)], 0.004, laiton, 'tube-plongeur', seg=8))
jg.add(cyl(0.010, 0.02, (JX, RY - 0.050, JZ), (0, 1, 0), M('crepine', 0x8a8f74, 0.4, 0.6), 14, name='crepine'))
jg.add(box((0.012, 0.030, 0.004), (JX, JY - 0.025, JZ + 0.012), M('rheostat', 0x6a4e3a, 0.2, 0.6), 0.001, 'rheostat'))
jg.add(tube([(JX, JY - 0.025, JZ + 0.016), (JX - 0.05, RY - 0.01, JZ + 0.06), (JX - 0.10, RY - 0.02, JZ + 0.10)], 0.0015, acier, 'bras-flotteur', seg=6))
jg.add(box((0.05, 0.02, 0.03), (JX - 0.115, RY - 0.02, JZ + 0.11), M('flotteur', 0xc4a35a, 0.0, 0.7), 0.006, 'flotteur'))
jg.add(box((0.30, 0.004, 0.36), (RX, RY - 0.025, RZ), essence, 0.0, 'niveau-essence'))
fasteners(jg, 'bague-jauge', [((JX, JY + 0.010, JZ), (0, 1, 0))], kind='nut', r=0.042, length=0.008, travel=0.05, washer=False)

# =====================================================================================
# CANALISATION D'ESSENCE : réservoir → plancher (côté droit) → compartiment moteur → filtre → pompe
# =====================================================================================
FIL = (0.86, 0.555, 0.25)              # filtre à essence en ligne, axe x
ce = Part('canalisation-essence', (0, -0.2, 0.15))
dep = (RX + 0.115, RY - 0.05, RZ - 0.15)
ce.add(tube([dep, (RX + 0.16, RY - 0.05, RZ - 0.15), (RX + 0.19, RY - 0.06, RZ - 0.12)], 0.0045, durite, 'durite-reservoir', seg=8))
collar(ce, (RX + 0.13, RY - 0.05, RZ - 0.15), (1, 0, 0), 0.0045)
line = [(RX + 0.19, RY - 0.06, RZ - 0.12), (-0.80, 0.30, 0.14), (-0.77, 0.225, 0.16), (-0.58, 0.225, 0.18), (-0.52, 0.34, 0.20),
        (-0.15, 0.352, 0.21), (-0.07, 0.285, 0.21), (0.07, 0.285, 0.21), (0.15, 0.352, 0.21), (0.55, 0.352, 0.21), (0.66, 0.36, 0.215), (0.72, 0.42, 0.225), (0.75, 0.50, 0.24), (0.775, 0.54, 0.25)]
ce.add(tube(line, 0.003, acier, 'tube-rigide', seg=8, res=16))
clips = []
for x in (-0.40, -0.10, 0.20, 0.50):    # agrafes sous le plancher
    ce.add(box((0.012, 0.010, 0.016), (x, 0.355, 0.21), M('agrafe', 0x2b2b2b, 0.0, 0.7), 0.002, 'agrafe'))
    clips.append(((x, 0.346, 0.21), (0, -1, 0)))
ce.add(tube([(0.775, 0.54, 0.25), (0.79, 0.55, 0.25), (FIL[0] - 0.045, FIL[1], FIL[2])], 0.0045, durite, 'durite-filtre', seg=8))
collar(ce, (0.785, 0.546, 0.25), (1, 0, 0), 0.0045)
fasteners(ce, 'agrafes-canalisation', clips, kind='pin', r=0.003, length=0.012, travel=0.02)

fe = Part('filtre-essence', (0, 0.25, 0.1))
fe.add(lathe([(0.0, -0.040), (0.004, -0.040), (0.004, -0.030), (0.016, -0.022), (0.016, 0.022), (0.004, 0.030), (0.004, 0.040), (0.0, 0.040)],
             FIL, (1, 0, 0), nylon, 28, 'corps-filtre'))
fe.add(lathe([(0.006, -0.018), (0.012, -0.018), (0.012, 0.018), (0.006, 0.018)], FIL, (1, 0, 0), papier, 20, 'element'))
for k in range(10):     # plis du papier
    a = 2 * math.pi * k / 10
    fe.add(box((0.034, 0.002, 0.002), (FIL[0], FIL[1] + 0.012 * math.cos(a), FIL[2] + 0.012 * math.sin(a)), papier, name='pli'))
fe.add(cyl(0.0135, 0.010, (FIL[0] + 0.012, FIL[1], FIL[2]), (1, 0, 0), essence, 18, name='essence'))
fe.add(cyl(0.003, 0.008, (FIL[0], FIL[1] + 0.017, FIL[2]), (1, 0, 0), noir, 6, r2=0.0005, name='fleche-sens'))
collar(fe, (FIL[0] + 0.035, FIL[1], FIL[2]), (1, 0, 0), 0.0045)
fasteners(fe, 'colliers-filtre-essence', [((FIL[0] - 0.035, FIL[1] + 0.009, FIL[2]), (0, 1, 0)), ((FIL[0] + 0.035, FIL[1] + 0.009, FIL[2]), (0, 1, 0))], kind='screw', r=0.0025, length=0.01, travel=0.02)

# =====================================================================================
# ÉCHAPPEMENT (planche 9) : descente à bride à ressorts, silencieux sous le compartiment moteur,
# tuyau intermédiaire, tuyau arrière sur suspente, sortie arrière gauche
# =====================================================================================
B0 = (EX + 0.02, YD - 0.13, -0.19)      # bride du collecteur (moteur.py), au-dessus du démarreur
ZI = -0.225                             # entrée du silencieux, à l'extérieur du démarreur
MX0, MX1, MY, MZ = 0.74, 1.08, 0.315, -0.20   # silencieux (sous le démarreur)
ex = Part('echappement', (0, -0.35, -0.2))
# ---- descente (6) : rotule à portée sphérique, bride (5), ressorts et écrous
ex.add(lathe([(0.017, 0.0), (0.024, 0.0), (0.027, 0.008), (0.022, 0.014), (0.017, 0.014)], (B0[0], B0[1] - 0.004, B0[2]), (0, -1, 0), ech_chaud, 24, 'portee-spherique'))
ex.add(extrude([(-0.055, -0.016), (0.055, -0.016), (0.062, 0.0), (0.055, 0.016), (-0.055, 0.016), (-0.062, 0.0)], 0.005, (B0[0], B0[1] - 0.022, B0[2]), (0, 1, 0), acier_noir, 'bride-descente', bev=0.002))
for s in (1, -1):
    ex.add(tube([(B0[0] + s * 0.045, B0[1] - 0.025 - 0.0035 * k, B0[2]) for k in range(2)], 0.002, acier, 'goujon', seg=6))
    pts = []
    for i in range(41):
        a = 2 * math.pi * 5 * i / 40
        pts.append((B0[0] + s * 0.045 + 0.007 * math.cos(a), B0[1] - 0.028 - 0.020 * i / 40, B0[2] + 0.007 * math.sin(a)))
    ex.add(tube(pts, 0.0012, M('ressort', 0x6d7d8a, 0.8, 0.35), 'ressort-bride', seg=4, res=2))
# la descente plonge vers l'extérieur pour contourner le démarreur et son écran thermique
desc = [(B0[0], B0[1] - 0.018, B0[2]), (B0[0] + 0.002, B0[1] - 0.04, B0[2] - 0.018), (0.955, 0.405, ZI), (0.985, 0.39, ZI), (1.01, MY + 0.05, ZI)]
ex.add(tube(desc, 0.019, ech_chaud, 'descente', seg=14, res=10))
fasteners(ex, 'ecrous-descente', [((B0[0] + s * 0.045, B0[1] - 0.050, B0[2]), (0, -1, 0)) for s in (1, -1)], kind='nut', r=0.006, length=0.012, travel=0.04)
# ---- tuyau intermédiaire (10) : sortie du silencieux par-dessous, descente sous le plancher
tint = [(0.78, MY - 0.06, MZ), (0.775, 0.25, MZ), (0.72, 0.24, MZ), (0.55, 0.24, MZ), (0.38, 0.24, MZ)]
ex.add(tube(tint, 0.0185, ech, 'tuyau-intermediaire', seg=14, res=10))
# ---- tuyau arrière (12) : sous le plancher côté gauche, sous la traverse et les barres arrière, sortie
tarr = [(0.36, 0.24, MZ), (0.0, 0.24, MZ), (-0.45, 0.235, MZ), (-0.675, 0.205, MZ), (-0.90, 0.215, -0.24),
        (-1.10, 0.23, -0.35), (-1.30, 0.232, -0.375), (-1.60, 0.234, -0.375), (-1.78, 0.236, -0.375), (-1.86, 0.236, -0.375)]
ex.add(tube(tarr, 0.0185, ech, 'tuyau-arriere', seg=14, res=12))
ex.add(lathe([(0.0175, 0.0), (0.0195, 0.0), (0.0195, 0.03), (0.0175, 0.03)], (-1.86, 0.236, -0.375), (1, 0, 0), ech_chaud, 20, 'embout-sortie'))
ex.add(lathe([(0.0185, 0.0), (0.0215, 0.0), (0.0215, 0.05), (0.0185, 0.05)], (0.40, 0.24, MZ), (1, 0, 0), ech, 20, 'emmanchement'))   # tuyau 12 sur tuyau 10
# ---- colliers (7, 9) : étrier en U, platine, écrous ; suspentes élastiques (11)
cx_ = []
for p in ((1.01, MY + 0.07, ZI), (0.42, 0.24, MZ)):
    vertical = p[0] > 1.0
    ax = (0, 1, 0) if vertical else (1, 0, 0)
    ex.add(torus(0.0215, 0.003, p, ax, acier, 24, 6, 'collier-etrier'))
    if vertical:
        ex.add(box((0.012, 0.010, 0.06), (p[0] + 0.024, p[1], p[2]), acier_noir, 0.002, 'platine-collier'))
        cx_ += [((p[0] + 0.024, p[1], p[2] + 0.024 * s), (1, 0, 0)) for s in (1, -1)]
    else:
        ex.add(box((0.012, 0.012, 0.06), (p[0], p[1] - 0.024, p[2]), acier_noir, 0.002, 'platine-collier'))
        cx_ += [((p[0], p[1] - 0.024, p[2] + 0.024 * s), (0, -1, 0)) for s in (1, -1)]
fasteners(ex, 'colliers-echappement', cx_, kind='nut', r=0.005, length=0.012, travel=0.04)
sus = []
for x, z in ((0.10, MZ), (-1.45, -0.375)):
    ytop = FLOOR - 0.004 if x > -0.6 else FLOOR_R - 0.025
    y0 = 0.24 if x > 0 else 0.233
    ex.add(box((0.04, 0.004, 0.03), (x, y0 + 0.020, z), acier_noir, 0.001, 'collier-suspente'))
    ex.add(tube([(x, y0 + 0.022, z), (x, ytop - 0.045, z)], 0.003, acier, 'goujon-suspente', seg=6))
    ex.add(cyl(0.014, 0.028, (x, ytop - 0.03, z), (0, 1, 0), caoutchouc, 18, name='tampon-suspente'))
    ex.add(box((0.05, 0.004, 0.04), (x, ytop - 0.014, z), acier_noir, 0.001, 'patte-plancher'))
    sus.append(((x, y0 + 0.026, z), (0, -1, 0)))
# suspente du silencieux : anneau caoutchouc vers le brancard gauche
ex.add(torus(0.020, 0.006, (0.80, MY + 0.03, -0.33), (1, 0, 0), caoutchouc, 20, 8, 'anneau-suspente'))
ex.add(box((0.02, 0.04, 0.006), (0.80, MY + 0.03, -0.366), acier_noir, 0.001, 'patte-silencieux'))
fasteners(ex, 'suspentes-echappement', sus, kind='nut', r=0.005, length=0.012, travel=0.04)

# ---- silencieux (8) : enveloppe ovale à nervures embouties, flasques serties
si = Part('silencieux', (0, -0.3, -0.25))
L = MX1 - MX0
si.add(extrude(rounded_rect(0.17, 0.10, 0.045, 6), L - 0.02, ((MX0 + MX1) / 2, MY, MZ), (1, 0, 0), ech, 'enveloppe'))
for xe in (MX0 + 0.006, MX1 - 0.006):
    si.add(extrude(rounded_rect(0.176, 0.106, 0.047, 6), 0.012, (xe, MY, MZ), (1, 0, 0), ech_chaud, 'flasque-sertie', bev=0.002))
for k in range(5):   # nervures transversales
    si.add(extrude(rounded_rect(0.174, 0.104, 0.046, 6), 0.010, (MX0 + 0.05 + k * (L - 0.10) / 4, MY, MZ), (1, 0, 0), ech, 'nervure'))
si.add(box((L - 0.06, 0.003, 0.05), ((MX0 + MX1) / 2, MY + 0.051, MZ), ech, 0.001, 'agrafure'))
si.add(cyl(0.021, 0.035, (1.01, MY + 0.052, ZI), (0, 1, 0), ech, 18, name='entree'))
si.add(cyl(0.021, 0.035, (0.78, MY - 0.052, MZ), (0, 1, 0), ech, 18, name='sortie'))
si.add(box((0.03, 0.006, 0.03), (0.80, MY + 0.03, MZ - 0.095), acier_noir, 0.002, 'oreille-suspente'))

export(OUT)
