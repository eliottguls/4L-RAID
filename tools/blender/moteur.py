# Moteur Cléon-Fonte 688 (1108 cm³) de la Renault 4 GTL, modélisé d'après la RTA.
# Lancer : python3 tools/blender/moteur.py   (module bpy : pip install bpy)
# Sortie : models/moteur.glb
#
# Cotes reprises de la RTA (pages du PDF) :
#   alésage 70 mm, course 72 mm (p.20) ; entraxe de bielle 128 mm, axe de piston Ø 18 × 59 mm,
#   centrage d'embase de chemise Ø 75,5 mm, manetons Ø 44 mm, tourillons Ø 54,8 mm, 5 paliers (p.21) ;
#   hauteur de culasse 72 mm, tiges de culbuteurs 173 × Ø 5 mm, poussoirs Ø 19 mm, soupapes
#   têtes Ø 33,5 / 30,5 mm, queues Ø 7 mm, ressorts fil 3,4 mm, Ø int. 21,6 mm, longueur libre 42 mm (p.20) ;
#   arbre à cames latéral à 4 paliers Ø 38 mm, chaîne simple et tendeur (p.21) ; volant fixé par 7 vis (p.21).
#   Vues éclatées : culasse (planche 5, p.32), carter-cylindres (planche 6, p.33),
#   équipage mobile (planche 7, p.34), distribution (planche 8, p.35), échappement (planche 9, p.36),
#   graissage (planche 10, p.37), refroidissement (planche 11, p.38), compartiment moteur (photo p.6).
# Ce qui n'est pas coté dans la RTA (entraxe des cylindres, formes de fonderie) est estimé d'après
# les vues éclatées.
#
# Implantation (comme sur la 4L) : moteur longitudinal derrière l'essieu, volant et embrayage vers
# l'avant (boîte devant), distribution par chaîne vers l'habitacle, arbre à cames côté droit
# (allumeur, pompe à essence, filtre à huile), collecteur et bougies côté gauche, pompe à eau et
# poulie d'arbre à cames côté embrayage.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (M, Part, apply_all, bevel, boolean, box, cyl, delete, export, extrude, fastener,  # noqa: E402
                 fasteners, gear, hexagon, join, lathe, place, reset, rounded_rect, torus, tube)

reset()

EX = 0.92                 # milieu du bloc (repère du site)
YC = 0.40                 # axe du vilebrequin
PITCH = 0.080             # entraxe des cylindres (estimé)
CX = [EX + 0.12, EX + 0.04, EX - 0.04, EX - 0.12]   # cylindre n° 1 côté volant (avant)
BORE, STROKE, ROD = 0.070, 0.072, 0.128
YD = 0.596                # plan de joint du bloc
HEAD_H = 0.072
YH = YD + 0.0015 + HEAD_H  # dessus de culasse (joint 1,5 mm)
XF, XR = EX + 0.185, EX - 0.185   # faces avant (volant) et arrière (distribution) du bloc
CAM_Z, CAM_Y = 0.074, YC + 0.088  # arbre à cames latéral, côté droit
# Manivelles : 1 et 4 au PMH, 2 et 3 au PMB
CRANK_ANGLE = [0, math.pi, math.pi, 0]

fonte = M('fonte', 0x66717a, 0.35, 0.72)
fonte_usinee = M('fonte-usinee', 0x9aa1a6, 0.7, 0.35)
alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
alu_usine = M('alu-usine', 0xd2d5d6, 0.8, 0.25)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
tole = M('tole-noire', 0x2d3033, 0.5, 0.5)
rouge = M('peinture-rouge', 0x93302a, 0.3, 0.35)
bronze = M('coussinet', 0xc9a36a, 0.8, 0.3)
joint = M('joint', 0x8b6b45, 0.0, 0.8)
joint_cul = M('joint-culasse', 0x9a9fa3, 0.6, 0.45)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
bleu = M('filtre-bleu', 0x2c62a8, 0.35, 0.4)
fil_rouge = M('fil-rouge', 0x8a2a22, 0.1, 0.55)
bakelite = M('bakelite', 0x2a1f1b, 0.1, 0.35)
cuivre = M('cuivre', 0xb87333, 0.9, 0.3)
garniture = M('garniture', 0x6f5a4c, 0.0, 0.9)


def X(i):
    return CX[i]


# =====================================================================================
# CARTER-CYLINDRES (planche 6)
# =====================================================================================
bloc = Part('bloc', (0, 0.2, 0))
# Corps : partie haute (chemises humides, chambre d'eau) et jupe jusqu'à 45 mm sous l'axe.
body = box((XF - XR, YD - (YC - 0.045), 0.205), (EX, (YD + YC - 0.045) / 2, -0.004), fonte, bev=0.006)
# chambre des chemises : ouverte en haut (chemises humides), alésages d'embase
water = box((XF - XR - 0.03, 0.15, 0.17), (EX, YD - 0.075 + 0.001, -0.004), None)
boolean(body, water)
apply_all(body)
delete(water)
bloc.add(body)
# Plan de joint usiné, percé des 4 chemises
deck = extrude(rounded_rect(XF - XR, 0.205, 0.006), 0.006, (EX, YD - 0.003, -0.004), (0, 1, 0), fonte_usinee)
for i in range(4):
    c = cyl(0.0405, 0.05, (X(i), YD, 0), (0, 1, 0), None, 40)
    boolean(deck, c)
    apply_all(deck)
    delete(c)
bloc.add(deck)
# Nervures verticales côté gauche (entre cylindres) et côté droit
for x in [XF - 0.005, X(0) - PITCH / 2, X(1) - PITCH / 2, X(2) - PITCH / 2, XR + 0.005]:
    bloc.add(box((0.012, 0.20, 0.014), (x, YD - 0.12, -0.108), fonte, bev=0.003))
# Galerie d'arbre à cames côté droit et bossages des poussoirs
bloc.add(cyl(0.026, XF - XR - 0.01, (EX, CAM_Y, CAM_Z + 0.022), (1, 0, 0), fonte, 28))
bloc.add(box((XF - XR - 0.02, 0.06, 0.03), (EX, CAM_Y + 0.035, CAM_Z + 0.03), fonte, bev=0.005))
# Bossage d'allumeur / pompe à huile (arrière droit), de filtre et de pompe à essence
bloc.add(cyl(0.022, 0.05, (EX - 0.13, CAM_Y + 0.07, CAM_Z + 0.045), (0, 1, 0), fonte, 24))
bloc.add(cyl(0.038, 0.03, (EX - 0.075, YC + 0.035, 0.112), (0, 0, 1), fonte, 32))   # portée de filtre
bloc.add(cyl(0.030, 0.012, (EX - 0.075, YC + 0.035, 0.128), (0, 0, 1), fonte_usinee, 32))
bloc.add(box((0.06, 0.05, 0.02), (EX + 0.03, CAM_Y - 0.02, 0.112), fonte, bev=0.004))     # pompe à essence
# Paliers de vilebrequin vus de dessous (5 cloisons)
for x in [XF - 0.012, X(0) - PITCH / 2, EX, X(2) - PITCH / 2, XR + 0.012]:
    bloc.add(box((0.022, 0.03, 0.17), (x, YC + 0.005, 0), fonte, bev=0.003))
# Bouchons de dessablage (pastilles) côté gauche
for x in (X(0) - 0.02, X(3) + 0.02):
    bloc.add(cyl(0.016, 0.006, (x, YD - 0.085, -0.108), (0, 0, 1), acier_noir, 24))
# Supports moteur (planche 4) : pattes et tampons obliques
for s in (1, -1):
    bloc.add(box((0.07, 0.06, 0.03), (EX - 0.04, YC + 0.06, s * 0.118), fonte, bev=0.006))
    bloc.add(box((0.09, 0.008, 0.07), (EX - 0.04, YC + 0.035, s * 0.15), acier_noir, bev=0.002))
    bloc.add(cyl(0.028, 0.045, (EX - 0.04, YC + 0.0, s * 0.175), (0, -0.6, s), caoutchouc, 20))
# Manocontact de pression d'huile côté gauche (p.37)
bloc.add(extrude(hexagon(0.011), 0.01, (EX - 0.10, CAM_Y - 0.02, -0.112), (0, 0, -1), acier))
bloc.add(cyl(0.010, 0.022, (EX - 0.10, CAM_Y - 0.02, -0.128), (0, 0, -1), noir, 16))
fastener(bloc, 'bouchon-vidange-bloc', (EX + 0.03, YC + 0.045, -0.106), (0, 0, -1), kind='plug', r=0.008, length=0.02, travel=0.05)
# Vis d'assemblage boîte / moteur autour de la face avant
fix_b = []
for a in (30, 90, 150, 210, 270, 330):
    r = 0.165
    fix_b.append(((XF + 0.006, YC + 0.04 + r * 0.72 * math.sin(math.radians(a)), r * math.cos(math.radians(a))), (-1, 0, 0)))
fasteners(bloc, 'fix-boite', fix_b, r=0.009, length=0.05, travel=0.08)

# =====================================================================================
# CHEMISES ET PISTONS (planche 7)
# =====================================================================================
chem = Part('chemises-pistons', (0, 0.32, 0))
for i in range(4):
    x = X(i)
    # chemise humide : collerette en haut, embase centrée Ø 75,5 en bas, joint d'embase
    liner = lathe([(0.0355, YD - 0.142 - YD), (0.03775, YD - 0.142 - YD), (0.03775, -0.132), (0.0385, -0.128),
                   (0.0385, -0.0085), (0.0405, -0.008), (0.0405, 0.0004), (0.0355, 0.0004)],
                  (x, YD, 0), (0, 1, 0), fonte_usinee, 40)
    chem.add(liner)
    chem.add(torus(0.0378, 0.0012, (x, YD - 0.134, 0), (0, 1, 0), joint, 40, 6))
    # piston
    ang = CRANK_ANGLE[i]
    r = STROKE / 2
    yp_pin = YC + r * math.cos(ang) + math.sqrt(ROD ** 2 - (r * math.sin(ang)) ** 2)
    top = yp_pin + 0.029
    pist = lathe([(0, top - yp_pin), (0.0345, top - yp_pin), (0.0349, top - yp_pin - 0.004), (0.0349, -0.040), (0.033, -0.041), (0.0, -0.035)],
                 (x, yp_pin, 0), (0, 1, 0), alu_usine, 40)
    chem.add(pist)
    for k, h in enumerate((0.006, 0.0115, 0.018)):  # segments : coup de feu, étanchéité, racleur
        chem.add(torus(0.0349, 0.0011 if k < 2 else 0.0016, (x, top - h, 0), (0, 1, 0), acier_noir, 40, 6))
    chem.add(cyl(0.009, 0.059, (x, yp_pin, 0), (0, 0, 1), acier, 20))   # axe Ø 18 × 59

# =====================================================================================
# BIELLES (planche 7)
# =====================================================================================
biel = Part('bielles', (0, 0.26, 0.25))
rod_nuts = []
for i in range(4):
    x = X(i)
    ang = CRANK_ANGLE[i]
    r = STROKE / 2
    pin = (YC + r * math.cos(ang), r * math.sin(ang))         # maneton (y, z)
    yp_pin = YC + r * math.cos(ang) + math.sqrt(ROD ** 2 - (r * math.sin(ang)) ** 2)
    # pied (Ø 18), corps en I, tête (Ø 44) avec chapeau
    biel.add(cyl(0.015, 0.022, (x, yp_pin, 0), (0, 0, 1), acier, 24))
    shank = extrude([(-0.011, 0.0), (0.011, 0.0), (0.016, -ROD + 0.03), (-0.016, -ROD + 0.03)], 0.018, (x, yp_pin, 0), (1, 0, 0), acier, up=(0, 1, 0))
    biel.add(shank)
    biel.add(box((0.022, 0.02, 0.068), (x, pin[0] + 0.012, 0), acier, bev=0.004))
    cap = lathe([(0.022, -0.011), (0.034, -0.011), (0.034, 0.011), (0.022, 0.011)], (x, pin[0], 0), (1, 0, 0), acier, 32, angle=math.pi)
    biel.add(cap)
    biel.add(lathe([(0.022, -0.0105), (0.0225, -0.0105), (0.0225, 0.0105), (0.022, 0.0105)], (x, pin[0], 0), (1, 0, 0), bronze, 32))
    for s in (1, -1):
        rod_nuts.append(((x, pin[0] - 0.026, s * 0.027), (0, -1, 0)))
fasteners(biel, 'ecrous-bielles', rod_nuts, kind='nut', r=0.0065, length=0.012, travel=0.04)

# =====================================================================================
# VILEBREQUIN (planche 7) : 5 paliers, contrepoids venus de fonderie
# =====================================================================================
vil = Part('vilebrequin', (0, -0.3, 0))
journals = [XF - 0.012, X(0) - PITCH / 2, EX, X(2) - PITCH / 2, XR + 0.012]
for x in journals:
    vil.add(cyl(0.0274, 0.022, (x, YC, 0), (1, 0, 0), fonte_usinee, 32))
for i in range(4):
    x = X(i)
    ang = CRANK_ANGLE[i]
    r = STROKE / 2
    py, pz = YC + r * math.cos(ang), r * math.sin(ang)
    vil.add(cyl(0.022, 0.024, (x, py, pz), (1, 0, 0), fonte_usinee, 32))
    for s in (1, -1):  # bras de manivelle et contrepoids
        wx = x + s * 0.0175
        web = extrude([(-0.025, 0.045), (0.025, 0.045), (0.032, 0.0), (0.05, -0.03), (0.0, -0.058), (-0.05, -0.03), (-0.032, 0.0)],
                      0.011, (wx, YC, 0), (1, 0, 0), fonte, up=(0, math.cos(ang), math.sin(ang)))
        vil.add(bevel(web, 0.003))
# nez côté distribution (pignon) et plateau côté volant
vil.add(cyl(0.016, 0.03, (XR - 0.01, YC, 0), (1, 0, 0), acier, 24))
vil.add(cyl(0.035, 0.012, (XF + 0.004, YC, 0), (1, 0, 0), fonte_usinee, 40))
# Chapeaux de paliers et coussinets
pal = []
for x in journals:
    vil.add(lathe([(0.0275, -0.011), (0.0285, -0.011), (0.0285, 0.011), (0.0275, 0.011)], (x, YC, 0), (1, 0, 0), bronze, 32))
    for s in (1, -1):
        pal.append(((x, YC - 0.032, s * 0.045), (0, -1, 0)))
    vil.add(box((0.022, 0.03, 0.115), (x, YC - 0.02, 0), fonte, bev=0.004))
fasteners(vil, 'vis-paliers', pal, r=0.0085, length=0.06, travel=0.08)

# =====================================================================================
# VOLANT MOTEUR (7 vis) et COURONNE
# =====================================================================================
vol = Part('volant-moteur', (0.3, 0, 0))
vol.add(lathe([(0.012, 0), (0.12, 0), (0.125, 0.004), (0.125, 0.026), (0.10, 0.028), (0.06, 0.018), (0.012, 0.018)],
              (XF + 0.010, YC, 0), (1, 0, 0), fonte_usinee, 64))
vol.add(gear(0.127, 0.132, 96, 0.012, (XF + 0.03, YC, 0), (1, 0, 0), acier, 'couronne', hole=0.124))
vf = []
for k in range(7):
    a = 2 * math.pi * k / 7
    vf.append(((XF + 0.029, YC + 0.024 * math.cos(a), 0.024 * math.sin(a)), (1, 0, 0)))
fasteners(vol, 'vis-volant', vf, r=0.0055, length=0.025, travel=0.05)

# =====================================================================================
# EMBRAYAGE (disque, mécanisme à diaphragme, butée)
# =====================================================================================
emb = Part('embrayage', (0.5, 0.0, 0))
XE = XF + 0.036
emb.add(lathe([(0.03, -0.0035), (0.0905, -0.0035), (0.0905, 0.0035), (0.03, 0.0035)], (XE + 0.004, YC, 0), (1, 0, 0), garniture, 48))
emb.add(lathe([(0.012, -0.012), (0.03, -0.012), (0.03, 0.012), (0.012, 0.012)], (XE + 0.004, YC, 0), (1, 0, 0), acier, 24))   # moyeu
emb.add(lathe([(0.105, 0.0), (0.112, 0.0), (0.112, 0.004), (0.101, 0.004), (0.101, 0.026), (0.04, 0.034), (0.036, 0.03), (0.097, 0.022), (0.097, 0.008)],
              (XE + 0.007, YC, 0), (1, 0, 0), acier, 48))
for k in range(18):  # doigts du diaphragme
    a = 2 * math.pi * k / 18
    emb.add(box((0.002, 0.004, 0.045), (XE + 0.034, YC + 0.06 * math.cos(a), 0.06 * math.sin(a)), acier, axis=None))
emb.add(lathe([(0.016, 0), (0.033, 0), (0.033, 0.02), (0.016, 0.02)], (XE + 0.04, YC, 0), (1, 0, 0), acier_noir, 32))   # butée
vm = []
for k in range(6):
    a = 2 * math.pi * k / 6 + math.pi / 6
    vm.append(((XE + 0.012, YC + 0.106 * math.cos(a), 0.106 * math.sin(a)), (1, 0, 0)))
fasteners(emb, 'vis-mecanisme', vm, r=0.006, length=0.02, travel=0.05)
emb.add(tube([(1.26, 0.52, 0.12), (1.18, 0.64, 0.28), (0.98, 0.80, 0.28), (0.86, 0.80, 0.0), (0.84, 0.70, -0.40)], 0.004, noir, seg=8))   # câble
fasteners(emb, 'reglage-embrayage', [((1.27, 0.52, 0.12), (1, 0.3, 0.3)), ((1.285, 0.525, 0.125), (1, 0.3, 0.3))], kind='nut', r=0.007, length=0.015, travel=0.02)

# =====================================================================================
# ARBRE À CAMES (4 paliers Ø 38) et POUSSOIRS
# =====================================================================================
aac = Part('arbre-cames', (0, 0, 0.35))
aac.add(cyl(0.012, XF - XR + 0.06, (EX + 0.02, CAM_Y, CAM_Z), (1, 0, 0), fonte_usinee, 20))
for x in (XF - 0.02, EX + 0.04, EX - 0.06, XR + 0.02):
    aac.add(cyl(0.019, 0.02, (x, CAM_Y, CAM_Z), (1, 0, 0), fonte_usinee, 32))
VALVES = []  # (x, admission?)
for i in range(4):
    order = ('E', 'A') if i % 2 == 0 else ('A', 'E')
    for k, s in enumerate((0.017, -0.017)):
        VALVES.append((X(i) + s, order[k] == 'A'))
for n, (x, adm) in enumerate(VALVES):
    prof = []
    for k in range(36):
        a = 2 * math.pi * k / 36
        prof.append(((0.017 + 0.0065 * max(0.0, math.cos(a)) ** 2) * math.sin(a), (0.017 + 0.0065 * max(0.0, math.cos(a)) ** 2) * math.cos(a)))
    lobe = extrude(prof, 0.012, (x, CAM_Y, CAM_Z), (1, 0, 0), fonte_usinee, up=(0, math.cos(n * 1.3), math.sin(n * 1.3)))
    aac.add(lobe)
aac.add(gear(0.010, 0.012, 14, 0.014, (EX - 0.13, CAM_Y, CAM_Z), (1, 0, 0), acier, 'pignon-allumeur'))
aac.add(box((0.006, 0.03, 0.05), (XR - 0.004, CAM_Y, CAM_Z), acier_noir, bev=0.003))   # bride de butée
fasteners(aac, 'vis-bride-aac', [((XR - 0.008, CAM_Y + 0.017, CAM_Z), (-1, 0, 0)), ((XR - 0.008, CAM_Y - 0.017, CAM_Z), (-1, 0, 0))], r=0.005, length=0.015, travel=0.04)
# poulie d'arbre à cames côté embrayage (courroie de pompe à eau et d'alternateur)
aac.add(lathe([(0.012, -0.009), (0.05, -0.009), (0.05, -0.006), (0.044, 0.0), (0.05, 0.006), (0.05, 0.009), (0.012, 0.009)], (XF + 0.07, CAM_Y, CAM_Z), (1, 0, 0), acier_noir, 40))

culb = Part('culbuterie', (0, 0.7, 0.05))
# poussoirs Ø 19 au-dessus de l'arbre à cames, tiges 173 × Ø 5 jusqu'aux culbuteurs
ROCK_Y = YH + 0.044
ROCK_Z = 0.010
VALVE_Z = -0.008
PUSH_Z_TOP = 0.040
rockers_adj = []
for n, (x, adm) in enumerate(VALVES):
    yt = CAM_Y + 0.020
    culb.add(lathe([(0, 0), (0.0095, 0), (0.0095, 0.030), (0.006, 0.031), (0, 0.027)], (x, yt, CAM_Z), (0, 1, 0), acier, 20))
    bottom = (x, yt + 0.028, CAM_Z)
    topp = (x, ROCK_Y - 0.006, PUSH_Z_TOP)
    culb.add(tube([bottom, topp], 0.0025, acier, seg=6))
    # culbuteur : bras de la soupape (patin) jusqu'à la vis de réglage au-dessus de la tige
    zlen = PUSH_Z_TOP - VALVE_Z + 0.014
    culb.add(box((0.011, 0.011, zlen), (x, ROCK_Y + 0.001, (PUSH_Z_TOP + VALVE_Z) / 2), acier, bev=0.003))
    culb.add(box((0.011, 0.008, 0.012), (x, ROCK_Y - 0.006, VALVE_Z), acier, bev=0.003))   # patin sur la queue de soupape
    culb.add(cyl(0.0085, 0.013, (x, ROCK_Y, ROCK_Z), (1, 0, 0), acier, 20))
    rockers_adj.append(((x, ROCK_Y + 0.006, PUSH_Z_TOP), (0, 1, 0)))
culb.add(cyl(0.0095, XF - XR - 0.02, (EX, ROCK_Y, ROCK_Z), (1, 0, 0), fonte_usinee, 20))   # axe de culbuteurs
for x in (XF - 0.02, X(0) - PITCH / 2, EX, X(2) - PITCH / 2, XR + 0.02):   # paliers d'axe
    culb.add(box((0.016, 0.044, 0.03), (x, YH + 0.022, ROCK_Z), fonte, bev=0.003))
for x in [X(i) - PITCH / 2 + 0.005 for i in range(3)] + [X(i) + PITCH / 2 - 0.005 for i in range(3)]:   # ressorts d'écartement
    culb.add(cyl(0.0075, 0.012, (x, ROCK_Y, ROCK_Z), (1, 0, 0), acier_noir, 12))
fasteners(culb, 'vis-reglage-culbuteurs', rockers_adj, kind='nut', r=0.0055, length=0.022, travel=0.015)

# =====================================================================================
# SOUPAPES ET RESSORTS
# =====================================================================================
soup = Part('soupapes', (0, 0.95, 0))
for x, adm in VALVES:
    rh = 0.0335 / 2 if adm else 0.0305 / 2
    seat = YD + 0.0015 + 0.004
    soup.add(lathe([(0, 0), (rh, 0), (rh, 0.0015), (0.0045, 0.010), (0.0035, 0.014), (0.0035, 0.106), (0, 0.106)],
                   (x, seat, VALVE_Z), (0, 1, 0), acier, 24))
    # ressort : hélice
    pts = []
    turns, h0, h1 = 6.5, YH + 0.002, YH + 0.036
    for k in range(int(turns * 12) + 1):
        a = 2 * math.pi * k / 12
        pts.append((x + 0.0125 * math.cos(a), h0 + (h1 - h0) * k / (turns * 12), VALVE_Z + 0.0125 * math.sin(a)))
    soup.add(tube(pts, 0.0017, acier_noir, seg=6, res=2))
    soup.add(lathe([(0.0035, 0), (0.0145, 0), (0.0145, 0.003), (0.006, 0.005), (0.0035, 0.005)], (x, h1, VALVE_Z), (0, 1, 0), acier, 20))   # coupelle

# =====================================================================================
# JOINT DE CULASSE
# =====================================================================================
jc = Part('joint-culasse', (0, 0.45, 0))
gasket = extrude(rounded_rect(XF - XR - 0.004, 0.2, 0.01), 0.0015, (EX, YD + 0.00075, -0.004), (0, 1, 0), joint_cul)
for i in range(4):
    c = cyl(0.036, 0.02, (X(i), YD, 0), (0, 1, 0), None, 36)
    boolean(gasket, c)
    apply_all(gasket)
    delete(c)
jc.add(gasket)
for i in range(4):
    jc.add(torus(0.0365, 0.0012, (X(i), YD + 0.0008, 0), (0, 1, 0), acier, 40, 6))

# =====================================================================================
# CULASSE (planche 5)
# =====================================================================================
cul = Part('culasse', (0, 0.55, 0))
hb = box((XF - XR + 0.006, HEAD_H, 0.21), (EX, YD + 0.0015 + HEAD_H / 2, -0.004), alu, bev=0.005)
# chambre des culbuteurs : creusée dans le dessus
pocket = box((XF - XR - 0.02, 0.03, 0.15), (EX, YH, 0.0), None)
boolean(hb, pocket)
apply_all(hb)
delete(pocket)
cul.add(hb)
# Nervures et bossages latéraux (côté gauche : conduits ; côté droit : passages de tiges)
for i in range(4):
    cul.add(box((0.05, 0.034, 0.012), (X(i), YD + 0.035, -0.111), alu, bev=0.004))   # brides d'échappement
for x in (EX + 0.08, EX - 0.08):
    cul.add(box((0.05, 0.03, 0.012), (x, YD + 0.06, -0.111), alu, bev=0.004))           # brides d'admission (siamoises)
for i in range(4):  # puits de bougies côté gauche
    cul.add(cyl(0.012, 0.03, (X(i), YD + 0.03, -0.1), (0, 0.35, -1), alu, 20))
for i in range(5):
    cul.add(box((0.008, HEAD_H - 0.01, 0.008), (XR + 0.02 + i * 0.0825, YD + 0.038, 0.104), alu, bev=0.002))
# sortie d'eau vers la pompe, côté volant
cul.add(box((0.02, 0.05, 0.08), (XF + 0.008, YD + 0.04, 0.02), alu, bev=0.005))
# goujons du cache-culbuteurs
for x in (EX + 0.06, EX - 0.06):
    cul.add(cyl(0.0035, 0.10, (x, YH + 0.04, -0.03), (0, 1, 0), acier, 10))
# Vis de culasse : rangée gauche 7 5 2 4 10, rangée droite 9 3 1 6 8 (de l'avant vers l'arrière)
HBX = [EX + 0.16, EX + 0.08, EX, EX - 0.08, EX - 0.16]
hbolts = [((x, YH - 0.012, -0.072), (0, 1, 0)) for x in HBX] + [((x, YH - 0.012, 0.062), (0, 1, 0)) for x in HBX]
fasteners(cul, 'vis-culasse', hbolts, r=0.0095, length=0.105, travel=0.17)
fastener(cul, 'thermocontact', (XR - 0.002, YD + 0.05, 0.04), (-1, 0, 0), kind='bolt', r=0.009, length=0.015, travel=0.04)

# =====================================================================================
# CACHE-CULBUTEURS (planche 5) : couvercle nervuré, bouchon de remplissage, 2 écrous
# =====================================================================================
cc = Part('cache-culbuteurs', (0, 0.85, 0))
XCC = XF - XR - 0.012
# carter allongé : profil (z, y) extrudé le long de x, extrémités arrondies par biseau
prof = [(-0.088, 0.0), (0.088, 0.0), (0.087, 0.012), (0.083, 0.04), (0.072, 0.056), (0.05, 0.064), (-0.05, 0.064), (-0.072, 0.056), (-0.083, 0.04), (-0.087, 0.012)]
cover = extrude(prof, XCC, (EX, YH + 0.002, -0.004), (1, 0, 0), rouge, bev=0.012, up=(0, 1, 0))
cc.add(cover)
for k in range(3):   # nervures latérales (planche 5)
    for s in (1, -1):
        cc.add(box((XCC - 0.05, 0.004, 0.004), (EX, YH + 0.012 + k * 0.012, -0.004 + s * 0.087), rouge, bev=0.0015))
cc.add(box((XCC + 0.008, 0.005, 0.184), (EX, YH + 0.0025, -0.004), joint, bev=0.0015))   # joint
cc.add(cyl(0.024, 0.008, (EX - 0.10, YH + 0.068, 0.02), (0, 1, 0), rouge, 28))           # embase du bouchon
cc.add(cyl(0.009, 0.03, (EX + 0.12, YH + 0.045, 0.085), (0.3, 0.5, 1), noir, 14))         # reniflard
fasteners(cc, 'fix-cache-culbuteurs', [((x, YH + 0.067, -0.03), (0, 1, 0)) for x in (EX + 0.06, EX - 0.06)], kind='nut', r=0.0065, length=0.01, travel=0.05)
fastener(cc, 'bouchon-remplissage-huile', (EX - 0.10, YH + 0.072, 0.02), (0, 1, 0), kind='screw', r=0.024, length=0.012, travel=0.06)

# =====================================================================================
# CARTER INFÉRIEUR (planche 6) : tôle emboutie, bouchon de vidange
# =====================================================================================
sump = Part('carter-huile', (0, -0.45, 0))
YS = YC - 0.045
sprof = [(-0.105, 0.0), (0.105, 0.0), (0.104, -0.01), (0.10, -0.02), (0.095, -0.115), (0.085, -0.125), (-0.085, -0.125), (-0.095, -0.115), (-0.10, -0.02), (-0.104, -0.01)]
pan = extrude(sprof, XF - XR - 0.012, (EX, YS, -0.004), (1, 0, 0), tole, bev=0.015, up=(0, 1, 0))
sump.add(pan)
sump.add(box((XF - XR + 0.004, 0.004, 0.222), (EX, YS - 0.002, -0.004), tole, bev=0.001))   # rebord
for k in range(2):   # bossages d'emboutissage
    for s in (1, -1):
        sump.add(box((XF - XR - 0.08, 0.008, 0.006), (EX, YS - 0.05 - k * 0.03, -0.004 + s * 0.0975), tole, bev=0.003))
sump.add(box((XF - XR + 0.004, 0.003, 0.226), (EX, YS + 0.0015, -0.004), joint))
fastener(sump, 'bouchon-vidange', (EX - 0.06, YS - 0.125, 0.02), (0, -1, 0), kind='plug', r=0.011, length=0.016, travel=0.08)
sv = []
for k in range(7):
    x = XR + 0.015 + k * (XF - XR - 0.03) / 6
    for s in (1, -1):
        sv.append(((x, YS - 0.004, -0.004 + s * 0.108), (0, -1, 0)))
fasteners(sump, 'vis-carter-huile', sv, r=0.005, length=0.015, travel=0.03)

# =====================================================================================
# POMPE À HUILE (planche 10) : dans le carter, entraînée par l'arbre à cames
# =====================================================================================
ph = Part('pompe-huile', (0, -0.3, 0.2))
ph.add(box((0.05, 0.04, 0.05), (EX - 0.13, YC - 0.01, 0.06), alu, bev=0.006))
ph.add(cyl(0.005, 0.12, (EX - 0.13, CAM_Y - 0.04, CAM_Z + 0.03), (0, 1, 0.15), acier, 10))   # arbre de commande
ph.add(tube([(EX - 0.13, YC - 0.03, 0.06), (EX - 0.12, YC - 0.07, 0.04), (EX - 0.10, YS - 0.10, 0.02)], 0.008, acier_noir, seg=8))
ph.add(cyl(0.03, 0.012, (EX - 0.095, YS - 0.112, 0.02), (0, 1, 0), acier_noir, 24))   # crépine
fasteners(ph, 'vis-pompe-huile', [((EX - 0.13 + dx, YC + 0.012, 0.06 + dz), (0, 1, 0)) for dx, dz in ((0.018, 0.018), (-0.018, -0.018))], r=0.005, length=0.03, travel=0.04)

# =====================================================================================
# DISTRIBUTION (planche 8) : pignons, chaîne simple, tendeur, carter nervuré en tôle
# =====================================================================================
ch = Part('chaine-distribution', (-0.25, 0.05, 0))
XD = XR - 0.012
ch.add(gear(0.019, 0.0215, 19, 0.008, (XD, YC, 0), (1, 0, 0), acier, 'pignon-vilebrequin', hole=0.008))
ch.add(gear(0.040, 0.0425, 38, 0.008, (XD, CAM_Y, CAM_Z), (1, 0, 0), acier, 'pignon-aac', hole=0.012))
# chaîne : boucle tangente aux deux pignons
cy0, cz0, r0 = YC, 0.0, 0.0215
cy1, cz1, r1 = CAM_Y, CAM_Z, 0.0425
dy, dz = cy1 - cy0, cz1 - cz0
d = math.hypot(dy, dz)
base = math.atan2(dz, dy)
phi = math.acos((r0 - r1) / d)          # brins tangents extérieurs
loop = []
for k in range(33):                     # grand pignon : arc côté opposé au vilebrequin
    a = base + phi - 2 * phi * k / 32
    loop.append((XD, cy1 + r1 * math.cos(a), cz1 + r1 * math.sin(a)))
for k in range(13):                     # petit pignon
    a = base - phi - (2 * math.pi - 2 * phi) * k / 12
    loop.append((XD, cy0 + r0 * math.cos(a), cz0 + r0 * math.sin(a)))
ch.add(tube(loop, 0.003, acier_noir, seg=6, res=3, closed=True))
ch.add(box((0.012, 0.06, 0.012), (XD, (YC + CAM_Y) / 2, -0.03), acier_noir, bev=0.003))   # patin de tendeur
ch.add(box((0.02, 0.03, 0.02), (XD + 0.004, YC + 0.035, -0.045), fonte_usinee, bev=0.003))
fasteners(ch, 'vis-tendeur-chaine', [((XD - 0.006, YC + 0.035, -0.045 + s * 0.012), (-1, 0, 0)) for s in (1, -1)], r=0.005, length=0.02, travel=0.04)
fasteners(ch, 'vis-pignon-aac', [((XD - 0.004, CAM_Y + s * 0.012, CAM_Z), (-1, 0, 0)) for s in (1, -1)], r=0.005, length=0.02, travel=0.04)

dist = Part('distribution', (-0.35, 0.1, 0))
dprof = [(-0.09, -0.06), (0.09, -0.06), (0.11, 0.0), (0.12, 0.08), (0.11, 0.15), (0.06, 0.165), (-0.05, 0.155), (-0.09, 0.11), (-0.10, 0.04)]
dc = extrude([(z, y) for z, y in dprof], 0.022, (XR - 0.025, YC, 0), (-1, 0, 0), tole, bev=0.008, up=(0, 1, 0))
dist.add(dc)
for k in range(5):   # nervures du carter
    dist.add(box((0.004, 0.17, 0.006), (XR - 0.037, YC + 0.05, -0.07 + k * 0.04), tole, bev=0.002))
dist.add(cyl(0.022, 0.006, (XR - 0.037, YC, 0), (1, 0, 0), caoutchouc, 24))   # joint à lèvres de vilebrequin
dv = []
for z, y in dprof:
    dv.append(((XR - 0.037, YC + y * 0.92, z * 0.92), (-1, 0, 0)))
fasteners(dist, 'vis-carter-distribution', dv, r=0.005, length=0.015, travel=0.03)

# =====================================================================================
# POMPE À EAU (planche 11) sur la culasse côté volant, poulie et thermostat
# =====================================================================================
wp = Part('pompe-eau', (0.25, 0.4, 0))
WX, WY, WZ = XF + 0.03, YD + 0.03, 0.02
wp.add(box((0.04, 0.09, 0.12), (WX, WY, WZ), alu, bev=0.012))
wp.add(cyl(0.032, 0.04, (WX + 0.035, WY, WZ), (1, 0, 0), alu, 28))
wp.add(cyl(0.015, 0.03, (WX + 0.06, WY, WZ), (1, 0, 0), alu, 20))
wp.add(lathe([(0.012, -0.009), (0.06, -0.009), (0.06, -0.006), (0.054, 0.0), (0.06, 0.006), (0.06, 0.009), (0.012, 0.009)], (XF + 0.07, WY, WZ), (1, 0, 0), acier_noir, 40))
wp.add(cyl(0.02, 0.04, (WX, WY + 0.045, WZ - 0.04), (0, 1, 0), alu, 24))   # boîtier de thermostat
wp.add(cyl(0.017, 0.04, (WX + 0.03, WY + 0.06, WZ - 0.04), (1, 0.4, 0), alu, 20))
fasteners(wp, 'vis-pompe-eau', [((WX + 0.021, WY + dy, WZ + dz), (1, 0, 0)) for dy, dz in ((0.035, 0.05), (-0.035, 0.05), (0.035, -0.05), (-0.035, -0.05), (0.0, 0.055))], r=0.006, length=0.04, travel=0.06)
fasteners(wp, 'vis-poulie-pompe', [((XF + 0.08, WY + 0.022 * math.cos(a), WZ + 0.022 * math.sin(a)), (1, 0, 0)) for a in (0, 2.094, 4.189)], r=0.005, length=0.02, travel=0.04)

# =====================================================================================
# COLLECTEUR ADMISSION-ÉCHAPPEMENT (planche 9), côté gauche
# =====================================================================================
col = Part('echappement', (0, 0.0, -0.35))
fonte_ech = M('fonte-echappement', 0x4b4845, 0.5, 0.65)
for i in range(4):   # pipes d'échappement vers la descente
    x = X(i)
    col.add(tube([(x, YD + 0.035, -0.115), (x, YD + 0.03, -0.14), (EX + (x - EX) * 0.35, YD - 0.02, -0.16), (EX + 0.02, YD - 0.08, -0.16)], 0.016, fonte_ech, seg=12, res=6))
col.add(cyl(0.024, 0.06, (EX + 0.02, YD - 0.10, -0.16), (0, 1, 0), fonte_ech, 24))
col.add(cyl(0.035, 0.008, (EX + 0.02, YD - 0.13, -0.16), (0, 1, 0), fonte_ech, 24))   # bride de descente
col.add(tube([(EX - 0.08, YD + 0.06, -0.12), (EX - 0.05, YD + 0.085, -0.16), (EX, YD + 0.09, -0.175), (EX + 0.05, YD + 0.085, -0.16), (EX + 0.08, YD + 0.06, -0.12)], 0.017, alu, seg=12, res=8))
col.add(cyl(0.03, 0.03, (EX, YD + 0.095, -0.175), (0, 1, 0), alu, 28))   # pipe d'admission sous le carburateur
col.add(box((0.16, 0.004, 0.07), (EX + 0.02, YD - 0.035, -0.205), M('tole-alu', 0xc7cccf, 0.8, 0.35), bev=0.001))   # tôle pare-chaleur
col.add(box((XF - XR - 0.04, 0.07, 0.004), (EX, YD + 0.045, -0.1135), joint))   # joint de collecteur
ec = [((x, YD + y, -0.123), (0, 0, -1)) for x, y in ((EX + 0.16, 0.05), (EX + 0.08, 0.025), (EX, 0.05), (EX - 0.08, 0.025), (EX - 0.16, 0.05), (EX, 0.015))]
fasteners(col, 'ecrous-collecteur', ec, kind='nut', r=0.007, length=0.03, travel=0.05)

# =====================================================================================
# CARBURATEUR (Solex / Zenith) et FILTRE À AIR rond
# =====================================================================================
carb = Part('carburateur', (0, 0.35, -0.35))
CY = YD + 0.11
carb.add(box((0.065, 0.012, 0.055), (EX, CY, -0.175), alu, bev=0.003))                      # embase isolante
carb.add(box((0.06, 0.05, 0.055), (EX, CY + 0.031, -0.175), M('zamak', 0xbcb6a3, 0.6, 0.4), bev=0.008))  # corps
carb.add(box((0.04, 0.045, 0.04), (EX + 0.045, CY + 0.026, -0.175), M('zamak', 0xbcb6a3, 0.6, 0.4), bev=0.008))   # cuve
carb.add(cyl(0.028, 0.012, (EX, CY + 0.062, -0.175), (0, 1, 0), M('zamak', 0xbcb6a3, 0.6, 0.4), 28))   # buse
carb.add(cyl(0.018, 0.006, (EX - 0.034, CY + 0.02, -0.175), (1, 0, 0), acier, 18))   # secteur d'accélérateur
carb.add(tube([(EX - 0.04, CY + 0.02, -0.19), (EX - 0.09, CY + 0.06, -0.3), (0.83, 0.75, -0.40)], 0.0025, noir, seg=6))   # câble
fasteners(carb, 'ecrous-carbu', [((EX + 0.028, CY + 0.008, -0.15), (0, 1, 0)), ((EX - 0.028, CY + 0.008, -0.20), (0, 1, 0))], kind='nut', r=0.006, length=0.02, travel=0.04)
fasteners(carb, 'vis-ralenti', [((EX + 0.012, CY + 0.012, -0.205), (0, 0, -1)), ((EX - 0.012, CY + 0.012, -0.205), (0, 0, -1))], kind='screw', r=0.004, length=0.02, travel=0.012)

af = Part('filtre-air', (0, 0.7, -0.15))
AY = CY + 0.068
af.add(lathe([(0.028, 0.0), (0.13, 0.0), (0.142, 0.006), (0.145, 0.02), (0.142, 0.034), (0.13, 0.04), (0.028, 0.04)], (EX, AY, -0.175), (0, 1, 0), noir, 48))
af.add(lathe([(0.0, 0.058), (0.10, 0.055), (0.135, 0.046), (0.146, 0.036), (0.146, 0.03), (0.0, 0.03)], (EX, AY, -0.175), (0, 1, 0), noir, 48))   # couvercle
for k in range(16):
    a = 2 * math.pi * k / 16
    af.add(box((0.05, 0.004, 0.006), (EX + 0.085 * math.cos(a), AY + 0.059, -0.175 + 0.085 * math.sin(a)), noir, bev=0.0015))
af.add(lathe([(0.11, 0.0), (0.13, 0.0), (0.13, 0.036), (0.11, 0.036)], (EX, AY + 0.002, -0.175), (0, 1, 0), M('papier', 0xd9cf9e, 0.0, 0.9), 48))   # élément filtrant
af.add(tube([(EX + 0.13, AY + 0.02, -0.21), (EX + 0.22, AY + 0.015, -0.30), (1.30, AY - 0.02, -0.40)], 0.035, noir, seg=14, res=8))   # prise d'air
fastener(af, 'ecrou-filtre-air', (EX, AY + 0.062, -0.175), (0, 1, 0), kind='nut', r=0.013, length=0.03, travel=0.06, washer=False)

# =====================================================================================
# ALLUMAGE : allumeur, bougies, fils
# =====================================================================================
dl = Part('allumeur', (0, 0.5, 0.25))
DX, DZ = EX - 0.13, CAM_Z + 0.045
DY0 = CAM_Y + 0.095
dl.add(cyl(0.022, 0.07, (DX, DY0 + 0.035, DZ), (0, 1, 0), alu, 24))
dl.add(cyl(0.036, 0.025, (DX, DY0 + 0.08, DZ), (0, 1, 0), alu, 32))
dl.add(lathe([(0.0, 0.05), (0.02, 0.05), (0.03, 0.04), (0.038, 0.02), (0.04, 0.0), (0.0, 0.0)], (DX, DY0 + 0.092, DZ), (0, 1, 0), bakelite, 32))   # tête
for k in range(4):
    a = 2 * math.pi * k / 4 + math.pi / 4
    dl.add(cyl(0.007, 0.02, (DX + 0.02 * math.cos(a), DY0 + 0.145, DZ + 0.02 * math.sin(a)), (0, 1, 0), bakelite, 14))
dl.add(cyl(0.007, 0.02, (DX, DY0 + 0.15, DZ), (0, 1, 0), bakelite, 14))
dl.add(cyl(0.02, 0.03, (DX + 0.045, DY0 + 0.075, DZ - 0.01), (1, 0, -0.3), alu, 24))   # capsule à dépression
dl.add(box((0.05, 0.006, 0.03), (DX, DY0 + 0.004, DZ + 0.02), acier_noir, bev=0.002))   # bride
fastener(dl, 'fix-allumeur', (DX, DY0 + 0.007, DZ + 0.03), (0, 1, 0), r=0.006, length=0.02, travel=0.04)

bg = Part('bougies', (0, 0.25, -0.4))
plug_specs = []
for i in range(4):
    p = (X(i), YD + 0.04, -0.112)
    plug_specs.append((p, (0, 0.35, -1)))
fasteners(bg, 'bougies', plug_specs, kind='spark', r=0.0105, length=0.07, travel=0.10)
# fils d'allumage : tête d'allumeur → bougies (passent au-dessus du cache-culbuteurs)
ign = Part('allumeur', (0, 0.5, 0.25))
order_cap = [0, 2, 3, 1]
for k, i in enumerate(order_cap):
    a = 2 * math.pi * k / 4 + math.pi / 4
    start = (DX + 0.02 * math.cos(a), DY0 + 0.155, DZ + 0.02 * math.sin(a))
    end = (X(i), YD + 0.07, -0.20)
    ign.add(tube([start, (start[0], DY0 + 0.20, start[2]), ((start[0] + end[0]) / 2, YH + 0.10, 0.0), (end[0], YH + 0.06, -0.12), end], 0.0045, fil_rouge, seg=8, res=6))
ign.add(tube([(DX, DY0 + 0.16, DZ), (DX + 0.05, DY0 + 0.22, DZ + 0.12), (0.86, 0.80, 0.42)], 0.0045, fil_rouge, seg=8, res=6))

# =====================================================================================
# POMPE À ESSENCE (mécanique, côté droit) et FILTRE À HUILE
# =====================================================================================
pe = Part('pompe-essence', (0, 0, 0.4))
pe.add(box((0.05, 0.04, 0.018), (EX + 0.03, CAM_Y - 0.02, 0.13), alu, bev=0.004))
pe.add(cyl(0.035, 0.03, (EX + 0.03, CAM_Y - 0.02, 0.155), (0, 0, 1), alu, 32))
pe.add(cyl(0.038, 0.006, (EX + 0.03, CAM_Y - 0.02, 0.155), (0, 0, 1), acier, 32))
pe.add(cyl(0.025, 0.012, (EX + 0.03, CAM_Y - 0.02, 0.176), (0, 0, 1), acier, 28))
for s in (1, -1):
    pe.add(cyl(0.004, 0.02, (EX + 0.03 + s * 0.02, CAM_Y + 0.01, 0.16), (0, 1, 0), alu, 10))
pe.add(tube([(EX + 0.05, CAM_Y + 0.02, 0.16), (EX + 0.04, YD + 0.06, 0.13), (EX + 0.03, YH + 0.07, 0.0), (EX + 0.04, CY + 0.03, -0.14)], 0.0035, caoutchouc, seg=6))
pe.add(tube([(EX + 0.01, CAM_Y + 0.02, 0.16), (EX - 0.05, CAM_Y + 0.02, 0.21), (0.20, 0.25, 0.18), (-0.84, 0.25, -0.20)], 0.0035, caoutchouc, seg=6))
fasteners(pe, 'fix-pompe-essence', [((EX + 0.03 + s * 0.02, CAM_Y - 0.02, 0.139), (0, 0, 1)) for s in (1, -1)], kind='nut', r=0.006, length=0.02, travel=0.04)

fh = Part('filtre-huile', (0, -0.05, 0.45))
filt = lathe([(0.0, 0.0), (0.04, 0.0), (0.046, 0.006), (0.046, 0.09), (0.042, 0.098), (0.0, 0.1)], (0, 0, 0), (0, 1, 0), bleu, 40)
filt = join([filt, lathe([(0.03, -0.004), (0.036, -0.004), (0.036, 0.001), (0.03, 0.001)], (0, 0, 0), (0, 1, 0), caoutchouc, 32)], 'fx.filtre-huile-cartouche.0')
place(filt, (EX - 0.075, YC + 0.035, 0.135), axis=(0, 0, 1))
filt['fx'] = 'filtre-huile-cartouche'
filt['kind'] = 'filter'
filt['travel'] = 0.12
filt['dir'] = [0, 0, 1]
fh.fasteners.append(filt)

jg = Part('jauge', (0, 0.45, 0.1))
jg.add(tube([(EX + 0.06, YC + 0.0, 0.112), (EX + 0.075, YD - 0.02, 0.13), (EX + 0.085, YH + 0.06, 0.15), (EX + 0.09, YH + 0.11, 0.155)], 0.0045, acier_noir, seg=6))
jg.add(torus(0.014, 0.004, (EX + 0.09, YH + 0.128, 0.155), (0, 0, 1), M('jaune', 0xd2ae35, 0.1, 0.5), 20, 8))

# =====================================================================================
# CARTER D'EMBRAYAGE (côté boîte) : ajouté à la pièce « boîte »
# =====================================================================================
bt = Part('boite', (0.75, 0.15, 0))
bell = lathe([(0.135, 0.0), (0.175, 0.0), (0.178, 0.008), (0.17, 0.05), (0.15, 0.10), (0.13, 0.12), (0.125, 0.12), (0.145, 0.10), (0.162, 0.05), (0.168, 0.008), (0.135, 0.008)],
             (XF + 0.006, YC + 0.035, 0), (1, 0, 0), alu, 48)
bt.add(bell)

export(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'moteur.glb'))
