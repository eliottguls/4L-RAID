# Plateforme (cadre plancher), roues, roue de secours, réservoir et ligne d'échappement de la
# Renault 4 GTL. Lancer : python3 tools/blender/chassis.py   →   models/chassis.glb
#
# RTA : carrosserie boulonnée sur cadre plancher (p.79) ; garde au sol en charge 175 mm ; plancher à
# 360 mm sous l'assise des sièges (cote X des plans p. XIX) ; jante 400 B 13, pneus 145 SR 13,
# 3 écrous (p.82) ; roue de secours sur berceau sous le plancher arrière, face extérieure vers le sol,
# vis au centre de la traverse arrière (p. X) ; réservoir 34 L à l'arrière (p.79).
# Les sections des longerons et traverses ne sont pas cotées : elles sont estimées.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, box, cut, cyl, export, extrude, fastener, lathe, reset, rounded_rect, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'chassis.glb')

AXLE_F = 1.306
AXLE_R = {1: -1.143, -1: -1.095}
TRACK = {'av': 0.640, 'ar': 0.624}
WR = 0.285
FLOOR = 0.370          # dessus du plancher avant
FLOOR_R = 0.470        # plancher de coffre
TABLIER_X = 0.700

tole = M('tole-plateforme', 0x34383b, 0.45, 0.55)
tole_cl = M('tole-plancher', 0x464b4f, 0.4, 0.6)
tapis = M('tapis', 0x1f1f20, 0.0, 0.95)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
pneu = M('pneu', 0x1c1d1e, 0.0, 0.9)
jante = M('jante', 0xb9bec2, 0.7, 0.35)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
ech = M('acier-echappement', 0x5b5853, 0.6, 0.6)
reservoir_m = M('reservoir', 0x2f3336, 0.5, 0.5)
durite = M('durite-essence', 0x26272a, 0.0, 0.8)

# =====================================================================================
# PLATEFORME
# =====================================================================================
pl = Part('plateforme', (0, -0.45, 0))
# plancher avant avec nervures longitudinales, tapis caoutchouc
pl.add(box((TABLIER_X + 0.60, 0.004, 1.20), ((TABLIER_X - 0.60) / 2, FLOOR - 0.002, 0), tole_cl))
for z in (-0.45, -0.33, -0.15, 0.15, 0.33, 0.45):
    pl.add(box((TABLIER_X + 0.50, 0.010, 0.030), ((TABLIER_X - 0.60) / 2 - 0.02, FLOOR - 0.008, z), tole_cl, 0.004))
for s in (1, -1):
    pl.add(box((0.62, 0.006, 0.42), (0.25, FLOOR + 0.004, s * 0.32), tapis, 0.003))   # tapis avant
    pl.add(box((0.30, 0.006, 0.42), (-0.32, FLOOR + 0.004, s * 0.32), tapis, 0.003))   # tapis arrière
# longerons latéraux en caisson (bas de caisse), de passage de roue à passage de roue
for s in (1, -1):
    pl.add(extrude([(-0.06, -0.055), (0.06, -0.055), (0.06, 0.05), (0.03, 0.058), (-0.06, 0.058)], 1.74, (0.07, 0.325, s * 0.665), (1, 0, 0), tole, bev=0.006, up=(0, 1, 0)))
    pl.add(box((0.10, 0.003, 0.03), (0.0, 0.271, s * 0.665), acier_noir))      # point de levage latéral (pied milieu)
    pl.add(box((0.08, 0.003, 0.03), (0.85, 0.271, s * 0.665), acier_noir))
# brancards avant : du tablier à la traverse avant, relevés au droit des transmissions
for s in (1, -1):
    pl.add(tube([(TABLIER_X - 0.10, 0.33, s * 0.40), (0.95, 0.35, s * 0.40), (1.15, 0.41, s * 0.40), (1.45, 0.415, s * 0.40), (1.74, 0.42, s * 0.40)], 0.032, tole, seg=4, res=8))
    # supports de triangles : platines verticales
    pl.add(box((0.30, 0.30, 0.006), (AXLE_F, 0.34, s * 0.345), tole))
    pl.add(box((0.30, 0.06, 0.06), (AXLE_F, 0.48, s * 0.37), tole, 0.008))
    # tourelle d'amortisseur
    pl.add(box((0.08, 0.05, 0.10), (AXLE_F + 0.17, 0.645, s * 0.45), tole, 0.01))
    pl.add(tube([(AXLE_F + 0.17, 0.64, s * 0.40), (AXLE_F + 0.10, 0.45, s * 0.40)], 0.014, tole))
pl.add(box((0.06, 0.06, 0.88), (1.74, 0.43, 0), tole, 0.01))                 # traverse avant (support de radiateur)
pl.add(box((0.05, 0.05, 0.80), (1.14, 0.20, 0), tole, 0.01))                 # traverse sous la boîte
pl.add(box((0.10, 0.07, 1.22), (0.18, 0.32, 0), tole, 0.012))                # traverse d'ancrage des barres AV
# talon de siège arrière, traverse arrière (tubes des barres de torsion), plancher de coffre
pl.add(extrude([(-0.58, FLOOR), (-0.60, FLOOR), (-0.78, FLOOR_R), (-0.76, FLOOR_R)], 1.12, (0, 0, 0), (0, 0, 1), tole_cl, up=(0, 1, 0)))
pl.add(box((0.17, 0.09, 1.30), (-0.675, 0.28, 0), tole, 0.015))
pl.add(box((1.02, 0.004, 1.12), (-1.27, FLOOR_R - 0.002, 0), tole_cl))
for z in (-0.30, -0.10, 0.10, 0.30):
    pl.add(box((0.90, 0.009, 0.03), (-1.27, FLOOR_R - 0.007, z), tole_cl, 0.004))
pl.add(box((0.90, 0.006, 0.90), (-1.27, FLOOR_R + 0.004, 0), tapis, 0.003))
for s in (1, -1):
    pl.add(box((1.02, 0.07, 0.06), (-1.27, FLOOR_R - 0.04, s * 0.45), tole, 0.008))   # longerons arrière
    pl.add(box((0.10, 0.05, 0.05), (-1.80, 0.425, s * 0.29), acier_noir, 0.006))       # pattes de pare-chocs
pl.add(box((0.05, 0.07, 1.20), (-1.765, 0.42, 0), tole, 0.01))                 # traverse arrière (seuil de hayon)
# berceau de la roue de secours : crémaillère sous la traverse
pl.add(box((0.03, 0.10, 0.05), (-1.76, 0.33, 0), acier_noir, 0.004))
for k in range(2):
    pl.add(box((0.012, 0.012, 0.05), (-1.745, 0.30 + k * 0.035, 0), acier, 0.002))

# =====================================================================================
# ROUES : jante tôle 400 B 13 à voile ajouré, pneu 145 SR 13
# =====================================================================================
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

# =====================================================================================
# RÉSERVOIR (34 L) sous le plancher arrière, goulotte vers la trappe arrière droite
# =====================================================================================
rs = Part('reservoir', (0, -0.35, 0.2))
rs.add(box((0.36, 0.13, 0.42), (-0.99, 0.37, 0.19), reservoir_m, 0.03))
rs.add(box((0.37, 0.012, 0.43), (-0.99, 0.37, 0.19), reservoir_m, 0.004))            # agrafage
for z in (0.02, 0.36):
    rs.add(box((0.40, 0.006, 0.025), (-0.99, 0.302, z), acier_noir))                 # sangles
rs.add(cyl(0.035, 0.015, (-0.92, 0.442, 0.10), (0, 1, 0), acier, 24))                  # jauge (rhéostat)
rs.add(tube([(-1.12, 0.42, 0.38), (-1.30, 0.50, 0.46), (-1.52, 0.66, 0.60), (-1.585, 0.79, 0.715)], 0.022, caoutchouc, seg=14))
rs.add(cyl(0.028, 0.03, (-1.585, 0.80, 0.70), (0, 0, 1), acier_noir, 24))            # bouchon
rs.add(tube([(-0.90, 0.40, 0.04), (-0.60, 0.33, 0.10), (0.0, 0.33, 0.20), (0.60, 0.34, 0.22), (0.80, 0.42, 0.22), (0.93, 0.44, 0.19)], 0.004, durite, seg=6, res=10))

# =====================================================================================
# LIGNE D'ÉCHAPPEMENT : descente, tube sous plancher côté gauche, silencieux, sortie arrière gauche
# =====================================================================================
ex = Part('echappement', (0, -0.35, -0.2))
ex.add(tube([(0.94, 0.515, -0.16), (0.94, 0.42, -0.18), (0.86, 0.30, -0.20), (0.60, 0.255, -0.20), (0.0, 0.235, -0.21),
             (-0.60, 0.21, -0.24), (-0.80, 0.21, -0.26), (-0.90, 0.25, -0.28)], 0.020, ech, seg=12, res=10))
ex.add(lathe([(0.0, 0.18), (0.05, 0.18), (0.075, 0.165), (0.08, 0.14), (0.08, -0.14), (0.075, -0.165), (0.05, -0.18), (0.0, -0.18)], (-1.08, 0.25, -0.28), (1, 0, 0), ech, 28))
ex.add(tube([(-1.26, 0.25, -0.28), (-1.45, 0.255, -0.40), (-1.75, 0.26, -0.42), (-1.88, 0.262, -0.42)], 0.018, ech, seg=12, res=8))
for x in (0.40, -0.50, -1.60):
    ex.add(cyl(0.018, 0.012, (x, 0.29, -0.21 if x > 0 else -0.30), (1, 0, 0), caoutchouc, 14))   # silentblocs de suspente
ex.add(cyl(0.032, 0.012, (0.94, 0.505, -0.16), (0, 1, 0), acier, 20))                 # bride de descente

export(OUT)
