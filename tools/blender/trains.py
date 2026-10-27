# Boîte-pont, transmissions, trains avant et arrière, direction et freins de la Renault 4 GTL,
# modélisés d'après la RTA. Lancer : python3 tools/blender/trains.py   →   models/trains.glb
#
# Cotes de la RTA (pages du PDF) : voies 1 280 / 1 248 mm, empattement droit 2 449 / gauche 2 401 mm,
# pneus 145 SR 13, jante 400 B 13 (p.82) ; disques Ø 228 × 10 mm, étrier DBA ou Girling Ø 45 (p.83) ;
# tambours arrière Ø 180 mm, cylindres Ø 20,6 (p.67) ; barres de torsion avant longitudinales,
# arrière transversales (planches 18 et 19, p.54 et 65) ; transmissions à joints tripode GI 62 côté
# boîte et GE 76 côté roue (p.50) ; carter de boîte-différentiel (planche 13, p.42) ; biellettes de
# direction horizontales, parallèles à l'axe du bras supérieur (p.52).
# Les formes non cotées (bras, carters) sont reprises des vues éclatées.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, box, cyl, export, extrude, fastener, fasteners, lathe, reset, torus, tube  # noqa: E402

reset()

AXLE_F = 1.306
AXLE_R = {1: -1.143, -1: -1.095}     # empattement droit / gauche (barres arrière décalées)
PIVOT_R = {1: -0.70, -1: -0.65}      # tubes d'articulation des bras arrière
WR = 0.285
DIFF_Y = 0.32

alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
tole = M('tole-noire', 0x2d3033, 0.5, 0.5)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
jaune = M('amortisseur', 0xc9a227, 0.2, 0.45)
chrome = M('chrome', 0xdfe2e5, 1.0, 0.15)
vert = M('barre-torsion', 0x4d7f57, 0.4, 0.45)
disque_m = M('disque', 0x8d9399, 0.9, 0.35)
fonte_frein = M('fonte-frein', 0x5c6166, 0.6, 0.55)
garniture = M('garniture', 0x6f5a4c, 0.0, 0.9)
cuivre = M('cuivre', 0xb87333, 0.9, 0.3)

# =====================================================================================
# BOÎTE-PONT (planche 13) : carter en deux demi-carters, différentiel, couvercles
# =====================================================================================
bt = Part('boite', (0.75, 0.15, 0))
XB0, XB1 = 1.235, 1.545
# demi-carters : profil (z, y) extrudé le long de x, plan de joint vertical au milieu
gprof = [(-0.115, -0.07), (0.115, -0.07), (0.125, 0.0), (0.12, 0.08), (0.09, 0.115), (-0.09, 0.115), (-0.12, 0.08), (-0.125, 0.0)]
bt.add(extrude(gprof, XB1 - XB0, ((XB0 + XB1) / 2, 0.43, 0), (1, 0, 0), alu, bev=0.02, up=(0, 1, 0)))
bt.add(box((XB1 - XB0 - 0.02, 0.012, 0.012), ((XB0 + XB1) / 2, 0.545, 0.0), alu, bev=0.004))   # nervure de joint
for k in range(5):
    x = XB0 + 0.04 + k * 0.06
    for s in (1, -1):
        bt.add(box((0.01, 0.12, 0.012), (x, 0.43, s * 0.124), alu, bev=0.003))
# carter de différentiel autour de l'axe des roues, écrous de réglage de chaque côté (repère 6)
bt.add(cyl(0.115, 0.30, (AXLE_F, DIFF_Y + 0.02, 0), (0, 0, 1), alu, 48))
for s in (1, -1):
    bt.add(cyl(0.06, 0.03, (AXLE_F, DIFF_Y, s * 0.165), (0, 0, 1), acier_noir, 12))
    bt.add(cyl(0.035, 0.012, (AXLE_F, DIFF_Y, s * 0.185), (0, 0, 1), caoutchouc, 24))   # joint à lèvre
    bt.add(box((0.015, 0.03, 0.006), (AXLE_F + 0.05, DIFF_Y + 0.04, s * 0.152), acier, bev=0.002))   # arrêtoir
# couvercle supérieur (repère 1) et couvercle avant
bt.add(box((0.22, 0.012, 0.16), (1.40, 0.552, 0), alu, bev=0.004))
bt.add(extrude([(-0.09, -0.08), (0.09, -0.08), (0.10, 0.06), (0.06, 0.10), (-0.06, 0.10), (-0.10, 0.06)], 0.03, (XB1 + 0.012, 0.44, 0), (1, 0, 0), alu, bev=0.01, up=(0, 1, 0)))
bt.add(box((0.012, 0.04, 0.05), (XB1 + 0.03, 0.48, 0.05), M('plaque-alu', 0xd8dadb, 0.6, 0.4)))   # plaque d'identification
# tampon avant et support (planche 4)
bt.add(cyl(0.03, 0.05, (XB1 + 0.06, 0.40, 0), (1, 0, 0), caoutchouc, 24))
bt.add(box((0.03, 0.08, 0.14), (XB1 + 0.095, 0.40, 0), acier_noir, bev=0.004))
# commande des vitesses : renvoi sur le couvercle avant
bt.add(cyl(0.01, 0.06, (XB1 + 0.04, 0.53, 0), (1, 0, 0), acier, 14))
bt.add(box((0.012, 0.05, 0.012), (XB1 + 0.07, 0.55, 0), acier, bev=0.003))
fasteners(bt, 'bouchons-boite', [((AXLE_F + 0.05, DIFF_Y - 0.11, 0), (0, -1, 0)), ((1.42, 0.40, 0.128), (0, 0, 1))], kind='plug', r=0.010, length=0.02, travel=0.06)
fasteners(bt, 'vis-couvercle-boite', [((XB1 + 0.028, 0.44 + dy, dz), (1, 0, 0)) for dy, dz in ((0.07, 0.07), (-0.06, 0.08), (0.07, -0.07), (-0.06, -0.08), (0.09, 0.0))], r=0.006, length=0.03, travel=0.05)
fasteners(bt, 'vis-couvercle-sup-boite', [((x, 0.559, z), (0, 1, 0)) for x in (1.30, 1.40, 1.50) for z in (0.07, -0.07)], r=0.005, length=0.02, travel=0.04)

# =====================================================================================
# TRANSMISSIONS (joints tripode GI 62 côté boîte, GE 76 côté roue)
# =====================================================================================
tr = Part('transmissions', (0, -0.35, 0))
for s in (1, -1):
    zi, zo = s * 0.215, s * 0.505
    tr.add(lathe([(0.0, 0.0), (0.04, 0.0), (0.042, 0.02), (0.042, 0.05), (0.035, 0.056), (0.012, 0.058), (0.0, 0.058)], (AXLE_F, DIFF_Y, s * 0.19), (0, 0, s), acier, 32))   # tulipe
    tr.add(lathe([(0.035, 0.0), (0.04, 0.008), (0.03, 0.02), (0.038, 0.032), (0.026, 0.045), (0.032, 0.056), (0.016, 0.075), (0.013, 0.085)], (AXLE_F, DIFF_Y, s * 0.24), (0, 0, s), caoutchouc, 24))
    tr.add(tube([(AXLE_F, DIFF_Y, s * 0.25), (AXLE_F, WR, zo - s * 0.05)], 0.0125, acier, seg=12))
    tr.add(lathe([(0.013, 0.0), (0.03, 0.012), (0.04, 0.03), (0.032, 0.04), (0.042, 0.055), (0.045, 0.07)], (AXLE_F, WR + (DIFF_Y - WR) * 0.12, zo - s * 0.08), (0, 0, s), caoutchouc, 24))
    tr.add(lathe([(0.0, 0.0), (0.048, 0.0), (0.05, 0.02), (0.04, 0.045), (0.02, 0.05), (0.0, 0.05)], (AXLE_F, WR, zo - s * 0.01), (0, 0, s), acier, 32))   # bol de fusée
    tr.add(cyl(0.0125, 0.07, (AXLE_F, WR, zo + s * 0.065), (0, 0, s), acier, 16))   # fusée cannelée

# =====================================================================================
# TRAIN AVANT (planche 18) : bras inférieur, bras supérieur, porte-fusée, moyeu, disque
# =====================================================================================
tri = Part('triangles-av', (0, -0.25, 0))
pf = Part('porte-fusee', (0, -0.15, 0))
tbf = Part('barres-torsion-av', (0, -0.3, 0))
amf = Part('amortisseurs-av', (0, 0.25, 0))
dsk = Part('disques-av', (0, 0, 0.35))
etr = Part('etriers-av', (0, 0.15, 0.55))
stab = Part('barres-stabilisatrices', (0, -0.3, 0))
rot = []
fus = []
pal_t = []
amo = []
cla = []
purge = []
for s in (1, -1):
    # bras inférieur (8) : tôle emboutie en triangle, articulations sur paliers (11)
    pts = [(AXLE_F - 0.15, s * 0.29), (AXLE_F + 0.13, s * 0.29), (AXLE_F + 0.035, s * 0.505), (AXLE_F - 0.035, s * 0.51)]
    plate = extrude([(x, -z) for x, z in pts], 0.016, (0, 0.205, 0), (0, 1, 0), acier_noir, bev=0.006)
    tri.add(plate)
    for x in (AXLE_F - 0.15, AXLE_F + 0.13):
        tri.add(cyl(0.022, 0.05, (x, 0.205, s * 0.29), (1, 0, 0), caoutchouc, 20))
    tri.add(cyl(0.012, 0.32, (AXLE_F - 0.01, 0.205, s * 0.29), (1, 0, 0), acier, 14))   # axe d'articulation
    tri.add(lathe([(0.0, -0.02), (0.024, -0.015), (0.026, 0.0), (0.02, 0.018), (0.0, 0.022)], (AXLE_F, 0.205, s * 0.53), (0, 1, 0), acier, 20))   # rotule inférieure (9)
    # bras supérieur (23) en fourche
    for x in (AXLE_F - 0.10, AXLE_F + 0.10):
        tri.add(tube([(x, 0.48, s * 0.36), (AXLE_F + (x - AXLE_F) * 0.3, 0.465, s * 0.47), (AXLE_F, 0.455, s * 0.515)], 0.012, acier_noir, seg=10))
        tri.add(cyl(0.018, 0.04, (x, 0.48, s * 0.36), (1, 0, 0), caoutchouc, 18))
    tri.add(cyl(0.01, 0.24, (AXLE_F, 0.48, s * 0.36), (1, 0, 0), acier, 14))
    tri.add(lathe([(0.0, -0.02), (0.022, -0.015), (0.024, 0.0), (0.018, 0.018), (0.0, 0.022)], (AXLE_F, 0.455, s * 0.52), (0, 1, 0), acier, 20))   # rotule supérieure
    rot += [((AXLE_F, 0.18, s * 0.53), (0, -1, 0)), ((AXLE_F, 0.48, s * 0.52), (0, 1, 0))]
    # porte-fusée (6) avec levier de direction vers l'avant
    pf.add(tube([(AXLE_F, 0.215, s * 0.53), (AXLE_F - 0.012, 0.30, s * 0.545), (AXLE_F - 0.006, 0.40, s * 0.535), (AXLE_F, 0.445, s * 0.52)], 0.026, M('fonte-ductile', 0x5d646a, 0.5, 0.6), seg=14))
    pf.add(cyl(0.045, 0.05, (AXLE_F, WR, s * 0.555), (0, 0, 1), M('fonte-ductile', 0x5d646a, 0.5, 0.6), 32))   # logement de roulement
    pf.add(tube([(AXLE_F + 0.02, 0.43, s * 0.525), (AXLE_F + 0.08, 0.47, s * 0.515), (AXLE_F + 0.13, 0.50, s * 0.50)], 0.012, M('fonte-ductile', 0x5d646a, 0.5, 0.6), seg=10))
    # moyeu (1) à 3 goujons (entraxe 130 mm)
    pf.add(lathe([(0.0, 0.0), (0.075, 0.0), (0.075, 0.008), (0.035, 0.012), (0.03, 0.04), (0.0, 0.04)], (AXLE_F, WR, s * 0.575), (0, 0, s), acier, 40))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        pf.add(cyl(0.006, 0.03, (AXLE_F + 0.065 * math.cos(a), WR + 0.065 * math.sin(a), s * 0.595), (0, 0, 1), acier, 10))
    fus.append(((AXLE_F, WR, s * 0.62), (0, 0, s)))
    # barre de torsion avant (13) : longitudinale, du bras inférieur au palier d'ancrage (15) sous le plancher
    tbf.add(tube([(AXLE_F - 0.16, 0.205, s * 0.29), (0.20, 0.23, s * 0.31)], 0.0085, vert, seg=10))
    tbf.add(box((0.07, 0.06, 0.09), (0.18, 0.235, s * 0.31), acier_noir, bev=0.01))
    tbf.add(cyl(0.02, 0.02, (0.215, 0.235, s * 0.31), (1, 0, 0), acier, 12))   # came de réglage (16)
    pal_t += [((0.16, 0.268, s * 0.28), (0, 1, 0)), ((0.16, 0.268, s * 0.34), (0, 1, 0)), ((0.20, 0.268, s * 0.31), (0, 1, 0))]
    # amortisseur (36) : du bras inférieur à la caisse
    a0, a1 = (AXLE_F + 0.04, 0.23, s * 0.47), (AXLE_F + 0.16, 0.62, s * 0.45)
    mid = tuple(a0[i] + (a1[i] - a0[i]) * 0.55 for i in range(3))
    amf.add(tube([a0, mid], 0.022, jaune, seg=16))
    amf.add(tube([mid, a1], 0.008, chrome, seg=10))
    amf.add(cyl(0.028, 0.02, mid, tuple(a1[i] - a0[i] for i in range(3)), jaune, 20))
    for p in (a0, a1):
        amf.add(cyl(0.016, 0.03, p, (0, 0, 1), caoutchouc, 16))
    amo += [((a0[0], a0[1], s * 0.495), (0, 0, s)), ((a1[0], a1[1] + 0.02, a1[2]), (0, 1, 0))]
    # disque Ø 228 × 10, bol
    dsk.add(lathe([(0.04, -0.035), (0.075, -0.035), (0.075, -0.005), (0.114, -0.005), (0.114, 0.005), (0.068, 0.005), (0.068, -0.03), (0.04, -0.03)], (AXLE_F, WR, s * 0.548), (0, 0, s), disque_m, 64))
    # étrier DBA (chape + étrier coulissant), plaquettes, clavettes, vis de purge
    ex = AXLE_F - 0.078
    ey = WR + 0.078
    etr.add(box((0.10, 0.05, 0.025), (ex, ey, s * 0.528), fonte_frein, bev=0.008))   # côté piston
    etr.add(box((0.09, 0.04, 0.012), (ex, ey, s * 0.566), fonte_frein, bev=0.004))   # côté extérieur
    etr.add(box((0.10, 0.018, 0.05), (ex, ey + 0.03, s * 0.548), fonte_frein, bev=0.006))   # pont
    etr.add(cyl(0.0225, 0.03, (ex, ey, s * 0.51), (0, 0, 1), fonte_frein, 24))   # cylindre Ø 45
    for z in (0.538, 0.558):
        etr.add(box((0.075, 0.035, 0.005), (ex, ey - 0.004, s * z), garniture, bev=0.0015))
    etr.add(tube([(ex - 0.02, ey + 0.02, s * 0.51), (ex - 0.07, 0.45, s * 0.48), (AXLE_F - 0.20, 0.50, s * 0.40)], 0.004, caoutchouc, seg=8))   # flexible
    cla += [((ex, ey + 0.035, s * 0.548), (1, 0, 0)), ((ex, ey - 0.035, s * 0.548), (1, 0, 0))]
    purge.append(((ex - 0.03, ey + 0.03, s * 0.515), (0, 1, 0)))
fasteners(tri, 'ecrous-rotules', rot, kind='nut', r=0.009, length=0.03, travel=0.05)
fasteners(pf, 'ecrou-fusee-av', fus, kind='nut', r=0.014, length=0.03, travel=0.06)
fasteners(tbf, 'vis-palier-torsion', pal_t, r=0.008, length=0.035, travel=0.05)
fasteners(amf, 'fix-amortisseurs-av', amo, kind='nut', r=0.008, length=0.03, travel=0.04)
fasteners(etr, 'clavettes-dba', cla, kind='pin', r=0.0035, length=0.08, travel=0.10)
# barre stabilisatrice avant (33)
stab.add(tube([(AXLE_F - 0.05, 0.215, 0.50), (AXLE_F - 0.12, 0.25, 0.42), (AXLE_F - 0.14, 0.27, 0.0), (AXLE_F - 0.12, 0.25, -0.42), (AXLE_F - 0.05, 0.215, -0.50)], 0.009, acier_noir, seg=10, res=10))
for s in (1, -1):
    stab.add(box((0.03, 0.03, 0.04), (AXLE_F - 0.135, 0.27, s * 0.30), caoutchouc, bev=0.006))

# =====================================================================================
# DIRECTION À CRÉMAILLÈRE (planche 17) sur le dessus de la boîte, biellettes horizontales
# =====================================================================================
dr = Part('direction', (0, 0.25, 0))
RX, RY = 1.43, 0.575
dr.add(cyl(0.024, 0.50, (RX, RY, 0.04), (0, 0, 1), alu, 24))
dr.add(cyl(0.035, 0.08, (RX, RY, -0.12), (0, 0, 1), alu, 24))   # boîtier de pignon
dr.add(cyl(0.016, 0.06, (RX - 0.025, RY + 0.035, -0.12), (-0.6, 0.6, 0), alu, 16))   # poussoir
for s in (1, -1):
    dr.add(lathe([(0.022, 0.0), (0.03, 0.01), (0.022, 0.02), (0.03, 0.03), (0.022, 0.04), (0.03, 0.05), (0.014, 0.07)], (RX, RY, s * 0.29), (0, 0, s), caoutchouc, 20))
    dr.add(tube([(RX, RY, s * 0.36), (RX - 0.02, RY - 0.03, s * 0.44), (AXLE_F + 0.13, 0.50, s * 0.49)], 0.0085, acier, seg=10))
    dr.add(lathe([(0, -0.012), (0.014, -0.008), (0.015, 0.006), (0, 0.014)], (AXLE_F + 0.13, 0.50, s * 0.49), (0, 1, 0), acier, 16))   # rotule
for z in (0.24, -0.16):   # brides de fixation
    dr.add(box((0.05, 0.012, 0.04), (RX, RY - 0.028, z), acier_noir, bev=0.003))
# colonne : joint souple puis axe vers le volant, côté gauche
dr.add(cyl(0.032, 0.012, (RX - 0.05, RY + 0.06, -0.17), (-1, 0.5, -0.1), caoutchouc, 24))
dr.add(tube([(RX - 0.06, RY + 0.065, -0.17), (1.10, 0.70, -0.24), (0.80, 0.76, -0.33)], 0.012, acier_noir, seg=10))
fasteners(dr, 'fix-direction', [((RX, RY - 0.02, z), (0, 1, 0)) for z in (0.255, 0.225, -0.145, -0.175)], r=0.008, length=0.04, travel=0.05)

# =====================================================================================
# TRAIN ARRIÈRE (planche 19) : bras tirés, barres de torsion transversales, amortisseurs
# =====================================================================================
bra = Part('bras-ar', (0, -0.25, 0))
tbr = Part('barres-torsion-ar', (0, -0.35, 0))
amr = Part('amortisseurs-ar', (0, 0.2, 0))
tam = Part('tambours-ar', (0, 0, 0.4))
fr_ar = []
amo_r = []
for s in (1, -1):
    x0, xp = AXLE_R[s], PIVOT_R[s]
    # tube d'articulation et bras (13) en caisson
    bra.add(cyl(0.035, 0.30, (xp, 0.275, s * 0.40), (0, 0, 1), acier_noir, 24))
    bra.add(extrude([(-0.03, -0.035), (0.035, -0.03), (0.035, 0.03), (-0.03, 0.04)], abs(x0 - xp) + 0.02, ((x0 + xp) / 2, 0.28, s * 0.50), (1, 0, 0), acier_noir, bev=0.008, up=(0, 1, 0)))
    bra.add(box((0.10, 0.10, 0.012), (x0 + 0.02, WR, s * 0.505), acier_noir, bev=0.006))   # platine de fusée
    for z in (0.28, 0.52):
        bra.add(cyl(0.04, 0.03, (xp, 0.275, s * z), (0, 0, 1), caoutchouc, 24))   # paliers (22, 23)
    bra.add(cyl(0.015, 0.06, (x0, WR, s * 0.54), (0, 0, 1), acier, 16))   # fusée
    # barre de torsion (14) : du bras jusqu'au palier d'ancrage côté opposé
    tbr.add(tube([(xp, 0.275, s * 0.52), (xp, 0.275, -s * 0.60)], 0.0095, vert, seg=10))
    tbr.add(box((0.08, 0.07, 0.05), (xp, 0.30, -s * 0.62), acier_noir, bev=0.01))   # palier d'ancrage (15)
    # amortisseur (12) presque horizontal
    a0, a1 = (x0 + 0.04, 0.26, s * 0.45), (x0 + 0.58, 0.36, s * 0.45)
    mid = tuple(a0[i] + (a1[i] - a0[i]) * 0.5 for i in range(3))
    amr.add(tube([a0, mid], 0.021, jaune, seg=16))
    amr.add(tube([mid, a1], 0.008, chrome, seg=10))
    for p in (a0, a1):
        amr.add(cyl(0.016, 0.03, p, (0, 0, 1), caoutchouc, 16))
    amo_r += [((a0[0], a0[1], s * 0.478), (0, 0, s)), ((a1[0], a1[1], s * 0.478), (0, 0, s))]
    # tambour Ø 180 et flasque avec cylindre de roue
    tam.add(lathe([(0.0, -0.035), (0.098, -0.035), (0.098, 0.03), (0.092, 0.036), (0.04, 0.036), (0.03, 0.05), (0.0, 0.05)], (x0, WR, s * 0.54), (0, 0, s), fonte_frein, 64))
    for k in range(8):   # ailettes
        a = 2 * math.pi * k / 8
        tam.add(box((0.004, 0.004, 0.05), (x0 + 0.099 * math.cos(a), WR + 0.099 * math.sin(a), s * 0.54), fonte_frein))
    tam.add(cyl(0.104, 0.004, (x0, WR, s * 0.503), (0, 0, 1), tole, 48))   # flasque (5)
    tam.add(cyl(0.012, 0.05, (x0, WR + 0.075, s * 0.495), (1, 0, 0), fonte_frein, 16))   # cylindre de roue (4)
    tam.add(cyl(0.022, 0.02, (x0, WR, s * 0.595), (0, 0, s), acier, 24))   # bouchon de moyeu
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        tam.add(cyl(0.006, 0.03, (x0 + 0.065 * math.cos(a), WR + 0.065 * math.sin(a), s * 0.59), (0, 0, 1), acier, 10))
    fr_ar.append(((x0, WR, s * 0.61), (0, 0, s)))
    purge.append(((x0 + 0.02, WR + 0.08, s * 0.49), (0, 0, -s)))
fasteners(amr, 'fix-amortisseurs-ar', amo_r, kind='nut', r=0.008, length=0.03, travel=0.04)
fasteners(tam, 'ecrou-fusee-ar', fr_ar, kind='nut', r=0.013, length=0.02, travel=0.06)
# barre stabilisatrice arrière (17)
stab.add(tube([(AXLE_R[1] + 0.06, 0.26, 0.49), (-0.85, 0.24, 0.45), (-0.85, 0.24, -0.45), (AXLE_R[-1] + 0.06, 0.26, -0.49)], 0.008, acier_noir, seg=10, res=10))

# vis de purge : avant (étriers) puis arrière (tambours), un seul jeu comme sur le site
pv = Part('etriers-av', (0, 0.15, 0.55))
for i, (p, d) in enumerate(purge):
    target = etr if i < 2 else tam
    fastener(target, 'vis-purge-freins', p, d, r=0.005, length=0.015, travel=0.008, idx=i)
Part.registry.remove(pv)

export(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'trains.glb'))
