# Embrayage, boîte-pont 354 et transmissions de la Renault 4 GTL (R 1128), pièce par pièce.
# Lancer : python3 tools/blender/transmission.py   →   models/transmission.glb
#
# Cotes et données de la RTA (pages du PDF) :
#   Embrayage Verto 180 DBR 285 : garnitures 181,5 × 127 × 3,2 mm, tarage 285 kg, disque à moyeu
#   amortisseur à 6 ressorts, butée à billes auto-centreuse, mécanisme à diaphragme fixé par 6 vis
#   (p.39) ; vue éclatée planche 12 : carter d'embrayage, fourchette sur axe goupillé, ressort de
#   butée (p.40) ; garde réglée par écrou et contre-écrou en bout de fourchette (p.40).
#   Boîte 354.146 (R 1128) : 4 rapports avant synchronisés (Renault en 1re-2e, Borg-Warner en
#   3e-4e), pignons toujours en prise ; 1re 12 × 44, 2e 17 × 38, 3e 24 × 35, 4e 38 × 39,
#   M. AR 11 × 39 (le baladeur de 3e-4e porte le pignon de M. AR) ; couple conique 10 × 31 ;
#   prise de tachymètre vis 6 dents, pignon 14 dents (p.41). Arbre primaire à 5 pignons
#   solidaires, arbre secondaire à 4 pignons fous et 2 synchroniseurs (p.41).
#   Carter et couvercles : planche 13 (p.42) ; coupes de la boîte et du différentiel (p.44) ;
#   pignonnerie : planche 14 (p.45) ; commande interne : planche 15 (p.46) ; arrêtoir d'arbre
#   primaire depuis 1982 (p.48).
#   Transmissions : joint tripode GI 62 côté boîte, GE 76 côté roue, planche 16 et vues
#   éclatées des deux joints (p.49 et 50).
# Ce que la RTA ne cote pas (entraxe des arbres, modules de denture, formes de fonderie) est
# estimé d'après les coupes et les vues éclatées : nombre de dents exact, proportions à l'œil.
#
# Implantation : boîte à l'avant du moteur, différentiel juste derrière l'axe des roues avant
# côté moteur, arbre d'embrayage passant au-dessus du différentiel jusqu'à l'arbre primaire
# (coupe p.44). Arbre secondaire sous le primaire, pignon d'attaque à l'arrière.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (M, Part, apply_all, ball_bearing, boolean, box, circlip, cyl, delete, export,  # noqa: E402
                 extrude, fastener, fasteners, lathe, reset, roller_bearing, rounded_rect, sphere, splined,
                 toothed, torus, tube)

reset()

# ------------------------------------------------------------------ repères (mètres, repère du site)
XF = 1.105                # face avant du bloc (côté volant)
YP = 0.40                 # axe vilebrequin = arbre d'embrayage = arbre primaire
AXLE_F = 1.306            # axe des roues avant = axe du différentiel
YS = 0.32                 # arbre secondaire (concourant avec l'axe de la couronne)
WR = 0.285                # centre des roues
ENTRAXE = YP - YS         # 80 mm (estimé)
XE = XF + 0.041           # disque d'embrayage (contre la face de friction du volant)
XBU = 1.192               # butée
XB0, XB1 = 1.235, 1.565   # carter de boîte (arrière / avant)
R_COUR = 0.060            # rayon primitif de la couronne (31 dents)
R_PIGN = R_COUR * 10 / 31  # pignon d'attaque (10 dents)
X_PIGN = AXLE_F + R_COUR  # milieu de la denture du pignon d'attaque
Z_COUR = -R_PIGN          # plan primitif de la couronne (couronne côté gauche)
HELIX = math.radians(22)

# Rapports (dents primaire × secondaire) et position des paires le long de l'arbre
GEARS = [('1re', 12, 44, 1.410), ('2e', 17, 38, 1.464), ('3e', 24, 35, 1.487), ('4e', 38, 39, 1.541)]
X_SY12, X_SY34 = 1.437, 1.514
GW = 0.014                # largeur de denture

alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
alu_usine = M('alu-usine', 0xd2d5d6, 0.8, 0.25)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_taille = M('acier-taille', 0xb7bcc0, 0.95, 0.22)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
bronze = M('bronze', 0xb8925a, 0.85, 0.3)
laiton = M('laiton', 0xc9a74e, 0.85, 0.3)
tole = M('tole-noire', 0x2d3033, 0.5, 0.5)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
garniture = M('garniture', 0x6f5a4c, 0.0, 0.9)
fonte = M('fonte', 0x66717a, 0.35, 0.72)
joint = M('joint', 0x8b6b45, 0.0, 0.8)
graisse = M('graisse', 0x3a3324, 0.1, 0.4)
ressort = M('ressort', 0x5b6a77, 0.75, 0.35)


def ring(r0, r1, w, pos, axis, mat, seg=40, name='bague'):
    return lathe([(r0, -w / 2), (r1, -w / 2), (r1, w / 2), (r0, w / 2)], pos, axis, mat, seg, name)


def helix_spring(p0, axis_u, r, length, turns, wire, mat, res=10):
    """Ressort hélicoïdal d'axe axis_u ('x', 'y' ou 'z') partant de p0."""
    pts = []
    for k in range(int(turns * res) + 1):
        a = 2 * math.pi * k / res
        t = length * k / (turns * res)
        c, s = r * math.cos(a), r * math.sin(a)
        if axis_u == 'x':
            pts.append((p0[0] + t, p0[1] + c, p0[2] + s))
        elif axis_u == 'y':
            pts.append((p0[0] + c, p0[1] + t, p0[2] + s))
        else:
            pts.append((p0[0] + c, p0[1] + s, p0[2] + t))
    return tube(pts, wire, mat, seg=6, res=2)


# =====================================================================================
# EMBRAYAGE : disque, mécanisme à diaphragme, butée et fourchette, câble (planche 12)
# =====================================================================================
dsq = Part('disque-embrayage', (0.38, 0.0, 0))
# garnitures 181,5 × 127 × 3,2 de chaque côté du disque porteur (rivets et rainures)
for dx in (-0.0035, 0.0035):
    dsq.add(ring(0.0635, 0.09075, 0.0032, (XE + dx, YP, 0), (1, 0, 0), garniture, 64, 'garniture'))
dsq.add(ring(0.05, 0.088, 0.0012, (XE, YP, 0), (1, 0, 0), acier, 64, 'tole-porteuse'))
for k in range(16):   # rainures des garnitures
    a = 2 * math.pi * k / 16
    for dx in (-0.0052, 0.0052):
        dsq.add(box((0.0008, 0.026, 0.002), (XE + dx, YP + 0.077 * math.cos(a), 0.077 * math.sin(a)), acier_noir, axis=None))
for k in range(24):   # rivets
    a = 2 * math.pi * (k + 0.5) / 24
    for rr in (0.069, 0.083):
        dsq.add(cyl(0.0018, 0.0112, (XE, YP + rr * math.cos(a), rr * math.sin(a)), (1, 0, 0), laiton, 8))
# moyeu amortisseur : flasques, 6 ressorts tangentiels, moyeu cannelé (déport côté boîte)
dsq.add(ring(0.024, 0.052, 0.002, (XE - 0.003, YP, 0), (1, 0, 0), acier, 48, 'flasque'))
dsq.add(ring(0.024, 0.052, 0.002, (XE + 0.003, YP, 0), (1, 0, 0), acier, 48, 'flasque'))
for k in range(6):
    a = 2 * math.pi * k / 6
    c = (XE, YP + 0.038 * math.cos(a), 0.038 * math.sin(a))
    t = (0, -math.sin(a), math.cos(a))
    p0 = tuple(c[i] - t[i] * 0.011 for i in range(3))
    pts = []
    for j in range(61):
        b = 2 * math.pi * j / 10
        s = 0.022 * j / 60
        u = (1, 0, 0)
        v = (0, math.cos(a), math.sin(a))
        pts.append(tuple(p0[i] + t[i] * s + u[i] * 0.0045 * math.cos(b) + v[i] * 0.0045 * math.sin(b) for i in range(3)))
    dsq.add(tube(pts, 0.0009, ressort, seg=6, res=2))
dsq.add(lathe([(0.0115, -0.004), (0.022, -0.004), (0.022, 0.016), (0.0115, 0.016)], (XE, YP, 0), (1, 0, 0), acier, 32))
dsq.add(splined(0.0118, 0.02, (XE + 0.006, YP, 0), (1, 0, 0), acier_noir, 20, 'cannelures-moyeu'))

emb = Part('embrayage', (0.5, 0.0, 0))
XM = XE + 0.006
# plateau de pression en fonte
emb.add(lathe([(0.064, 0.0), (0.0915, 0.0), (0.0915, 0.011), (0.086, 0.013), (0.07, 0.013), (0.064, 0.011)], (XM, YP, 0), (1, 0, 0), fonte, 64))
for k in range(3):   # bossages de sangles
    a = 2 * math.pi * k / 3
    emb.add(box((0.012, 0.016, 0.02), (XM + 0.007, YP + 0.095 * math.cos(a), 0.095 * math.sin(a)), fonte, bev=0.002))
# couvercle embouti : bride de fixation, jupe, fond percé de fenêtres
emb.add(lathe([(0.112, -0.002), (0.12, -0.002), (0.12, 0.002), (0.103, 0.002), (0.099, 0.006), (0.099, 0.022),
               (0.094, 0.028), (0.062, 0.031), (0.062, 0.028), (0.093, 0.025), (0.096, 0.021), (0.096, 0.006), (0.112, 0.002)],
              (XM - 0.002, YP, 0), (1, 0, 0), acier, 64, 'couvercle'))
for k in range(6):   # fenêtres d'aération du couvercle
    a = 2 * math.pi * (k + 0.5) / 6
    emb.add(box((0.004, 0.03, 0.014), (XM + 0.02, YP + 0.098 * math.cos(a), 0.098 * math.sin(a)), acier_noir, axis=None))
# diaphragme : couronne conique et 18 doigts
emb.add(lathe([(0.06, 0.0), (0.085, -0.004), (0.085, -0.0025), (0.06, 0.0015)], (XM + 0.028, YP, 0), (1, 0, 0), ressort, 64, 'diaphragme'))
for k in range(18):
    a = 2 * math.pi * k / 18
    r0, r1 = 0.06, 0.022
    p0 = (XM + 0.028, YP + r0 * math.cos(a), r0 * math.sin(a))
    p1 = (XM + 0.033, YP + r1 * math.cos(a), r1 * math.sin(a))
    mid = tuple((p0[i] + p1[i]) / 2 for i in range(3))
    f = box((0.0018, 0.0075, math.dist(p0, p1)), mid, ressort, axis=tuple(p1[i] - p0[i] for i in range(3)))
    emb.add(f)
for k in range(9):   # rivets d'articulation du diaphragme
    a = 2 * math.pi * k / 9
    emb.add(cyl(0.0022, 0.008, (XM + 0.028, YP + 0.066 * math.cos(a), 0.066 * math.sin(a)), (1, 0, 0), acier_noir, 8))
vm = []
for k in range(6):
    a = 2 * math.pi * k / 6 + math.pi / 6
    vm.append(((XM, YP + 0.1155 * math.cos(a), 0.1155 * math.sin(a)), (1, 0, 0)))
fasteners(emb, 'vis-mecanisme', vm, r=0.006, length=0.02, travel=0.05)

but = Part('butee-embrayage', (0.62, 0.1, 0))
# butée à billes auto-centreuse sur son guide, fourchette goupillée sur son axe, ressort
but.add(ball_bearing(0.019, 0.033, 0.012, (XBU, YP, 0), (1, 0, 0), acier, acier_taille))
but.add(lathe([(0.02, 0.0), (0.036, 0.0), (0.036, 0.016), (0.034, 0.018), (0.02, 0.018)], (XBU + 0.004, YP, 0), (1, 0, 0), acier_noir, 40, 'support-butee'))
for s in (1, -1):   # tétons d'appui de la fourchette
    but.add(cyl(0.004, 0.008, (XBU + 0.014, YP, s * 0.039), (0, 0, 1), acier_noir, 10))
# axe transversal au-dessus de la butée, fourchette en deux bras, levier vers le bas (côté droit)
YAX = YP + 0.068
but.add(cyl(0.0065, 0.15, (XBU + 0.016, YAX, 0.0), (0, 0, 1), acier, 16, name='axe-fourchette'))
for s in (1, -1):
    but.add(tube([(XBU + 0.016, YAX, s * 0.032), (XBU + 0.018, YP + 0.03, s * 0.044), (XBU + 0.017, YP + 0.002, s * 0.044)], 0.0042, acier_noir, seg=8))
but.add(box((0.012, 0.02, 0.07), (XBU + 0.016, YAX, 0), acier_noir, bev=0.003))   # moyeu de fourchette
but.add(tube([(XBU + 0.016, YAX, 0.04), (XBU + 0.02, YP - 0.05, 0.075), (XBU + 0.024, YP - 0.135, 0.085)], 0.0055, acier_noir, seg=8, res=8))
but.add(cyl(0.0075, 0.012, (XBU + 0.016, YAX, 0.072), (0, 0, 1), caoutchouc, 14))   # caoutchouc d'étanchéité
for z in (-0.012, 0.012):   # goupilles (dépassement 1 mm)
    but.add(cyl(0.0018, 0.022, (XBU + 0.016, YAX + 0.0, z), (1, 0, 0), acier, 8))
but.add(helix_spring((XBU + 0.006, YP + 0.036, -0.02), 'z', 0.003, 0.04, 9, 0.0006, ressort))   # ressort de butée
# guide de butée : tube venu du carter d'embrayage autour de l'arbre
but.add(lathe([(0.0135, 0.0), (0.0175, 0.0), (0.0175, 0.032), (0.03, 0.034), (0.03, 0.038), (0.0135, 0.038)], (XBU - 0.006, YP, 0), (1, 0, 0), alu_usine, 32, 'guide-butee'))

cab = Part('cable-embrayage', (-0.05, 0.12, 0.25))
LEV = (XBU + 0.024, YP - 0.135, 0.085)   # extrémité du levier de fourchette
STOP = (XF + 0.012, YP - 0.135, 0.085)   # butée de gaine sur le carter d'embrayage
cab.add(tube([LEV, STOP], 0.0018, acier, seg=6))                            # câble nu et embout fileté
cab.add(box((0.012, 0.03, 0.03), STOP, acier_noir, bev=0.003))               # patte d'arrêt de gaine
cab.add(tube([STOP, (XF - 0.04, YP - 0.12, 0.13), (0.98, 0.42, 0.24), (0.95, 0.66, 0.28), (0.90, 0.80, 0.18), (0.86, 0.80, 0.0), (0.84, 0.70, -0.40)], 0.0042, noir, seg=8, res=14))
fasteners(cab, 'reglage-embrayage', [((LEV[0] - 0.008, LEV[1], LEV[2]), (-1, 0, 0)), ((LEV[0] - 0.016, LEV[1], LEV[2]), (-1, 0, 0))], kind='nut', r=0.006, length=0.012, travel=0.025)

# =====================================================================================
# CARTER D'EMBRAYAGE (planche 12, repère 7)
# =====================================================================================
ce = Part('carter-embrayage', (0.3, 0.32, 0))
bell = lathe([(0.135, 0.0), (0.175, 0.0), (0.178, 0.008), (0.17, 0.05), (0.15, 0.10), (0.13, 0.12), (0.125, 0.12), (0.145, 0.10), (0.162, 0.05), (0.168, 0.008), (0.135, 0.008)],
             (XF + 0.006, YP + 0.035, 0), (1, 0, 0), alu, 56)
# fenêtre du démarreur (côté GAUCHE, sous le collecteur : RTA p.73) et lumière du levier de fourchette
for c in (cyl(0.038, 0.07, (XF + 0.04, 0.412, -0.141), (1, 0, 0), None, 28), box((0.05, 0.06, 0.08), (XBU + 0.024, YP - 0.11, 0.1), None)):
    boolean(bell, c)
    apply_all(bell)
    delete(c)
ce.add(bell)
# bossage du démarreur : manchon venu de fonderie qui enveloppe le nez du démarreur (côté gauche)
ce.add(lathe([(0.0375, 0.0), (0.045, 0.0), (0.045, 0.060), (0.040, 0.066), (0.0375, 0.066)], (XF + 0.006, 0.412, -0.141), (1, 0, 0), alu, 32, 'bossage-demarreur'))
front = lathe([(0.03, -0.004), (0.127, -0.004), (0.127, 0.004), (0.03, 0.004)], (XF + 0.122, YP + 0.035, 0), (1, 0, 0), alu, 56)
c = cyl(0.03, 0.05, (XF + 0.122, YP, 0), (1, 0, 0), None, 24)
boolean(front, c)
apply_all(front)
delete(c)
ce.add(front)
for k in range(8):   # nervures de raidissement
    a = 2 * math.pi * (k + 0.5) / 8
    ce.add(box((0.10, 0.006, 0.012), (XF + 0.06, YP + 0.035 + 0.158 * math.cos(a), 0.158 * math.sin(a)), alu, bev=0.002,
               axis=None))
ce.add(cyl(0.012, 0.02, (XBU + 0.016, YP + 0.068, 0.085), (0, 0, 1), alu, 16))   # bossage d'axe de fourchette
ce.add(box((0.04, 0.03, 0.05), (XF + 0.03, YP - 0.135, 0.085), alu, bev=0.004))  # patte de câble
ce.add(cyl(0.01, 0.12, (XF + 0.07, YP + 0.035 - 0.16, 0.0), (1, 0, 0), alu, 12))  # trou de visite
vce = []
for a in (20, 70, 110, 160, 200, 250, 290, 340):
    r = 0.12
    vce.append(((XF + 0.13, YP + 0.035 + r * math.sin(math.radians(a)), r * math.cos(math.radians(a))), (1, 0, 0)))
fasteners(ce, 'vis-carter-embrayage', vce, r=0.0075, length=0.035, travel=0.06)

# =====================================================================================
# CARTER DE BOÎTE ET DIFFÉRENTIEL (planche 13)
# =====================================================================================
bt = Part('boite', (0.75, 0.15, 0))
YB0, YB1 = 0.245, 0.49    # dessous / plan du couvercle supérieur
ZB = 0.10
outer = box((XB1 - XB0, YB1 - YB0, 2 * ZB), ((XB0 + XB1) / 2, (YB0 + YB1) / 2, 0), alu, bev=0.012)
apply_all(outer)
drum = cyl(0.092, 0.30, (AXLE_F, YS, 0), (0, 0, 1), None, 48)
boolean(outer, drum, 'UNION')
apply_all(outer)
delete(drum)
for s in (1, -1):
    b = cyl(0.07, 0.03, (AXLE_F, YS, s * 0.162), (0, 0, 1), None, 40)
    boolean(outer, b, 'UNION')
    apply_all(outer)
    delete(b)
# vides : chambre des pignons (ouverte en haut et à l'avant), chambre du différentiel, passages
cuts = [box((XB1 - XB0 - 0.006 + 0.02, YB1 - YB0, 2 * ZB - 0.012), ((XB0 + XB1) / 2 + 0.013, (YB0 + YB1) / 2 + 0.007, 0), None),
        cyl(0.083, 0.27, (AXLE_F, YS, 0), (0, 0, 1), None, 48),
        cyl(0.058, 0.40, (AXLE_F, YS, 0), (0, 0, 1), None, 40),
        cyl(0.03, 0.12, (XB0, YP, 0), (1, 0, 0), None, 24)]
for c in cuts:
    boolean(outer, c)
    apply_all(outer)
    delete(c)
bt.add(outer)
# cloison intermédiaire portant les roulements arrière des arbres (coupe p.44)
wall = box((0.012, YB1 - YB0 - 0.03, 2 * ZB - 0.012), (1.392, (YB0 + YB1) / 2, 0), alu)
for c in (cyl(0.031, 0.05, (1.392, YP, 0), (1, 0, 0), None, 32), cyl(0.0345, 0.05, (1.392, YS, 0), (1, 0, 0), None, 32),
          box((0.05, 0.08, 0.06), (1.392, YB1 - 0.02, 0), None)):
    boolean(wall, c)
    apply_all(wall)
    delete(c)
bt.add(wall)
# nervures extérieures et bride du couvercle supérieur
for k in range(5):
    x = XB0 + 0.13 + k * 0.045
    for s in (1, -1):
        bt.add(box((0.008, YB1 - YB0 - 0.03, 0.01), (x, (YB0 + YB1) / 2, s * (ZB + 0.004)), alu, bev=0.002))
bt.add(extrude(rounded_rect(XB1 - XB0 - 0.13, 2 * ZB + 0.012, 0.012), 0.008, ((XB0 + XB1) / 2 + 0.065, YB1 - 0.004, 0), (0, 1, 0), alu))
# fûts des écrous de réglage du différentiel, arrêtoirs (frein, repère 5)
for s in (1, -1):
    bt.add(cyl(0.074, 0.008, (AXLE_F, YS, s * 0.18), (0, 0, 1), alu, 40))
# supports : tampon avant et traverse (planche 4)
bt.add(cyl(0.03, 0.05, (XB1 + 0.06, 0.40, 0), (1, 0, 0), caoutchouc, 24))
bt.add(box((0.03, 0.08, 0.14), (XB1 + 0.095, 0.40, 0), acier_noir, bev=0.004))
# prise de tachymètre (côté droit, à l'avant) et reniflard
bt.add(cyl(0.011, 0.03, (XB1 - 0.03, YS + 0.02, ZB + 0.012), (0, 0, 1), alu, 16))
bt.add(tube([(XB1 - 0.03, YS + 0.02, ZB + 0.026), (XB1 - 0.03, YS + 0.07, ZB + 0.06), (1.40, 0.62, 0.20), (0.90, 0.80, 0.30)], 0.003, noir, seg=6))
bt.add(cyl(0.006, 0.02, (1.30, YB1 + 0.01, -0.06), (0, 1, 0), acier, 10))
fasteners(bt, 'bouchons-boite', [((AXLE_F + 0.025, YS - 0.088, 0), (0, -1, 0)), ((1.42, 0.30, ZB + 0.006), (0, 0, 1))], kind='plug', r=0.010, length=0.02, travel=0.06)

ca = Part('couvercle-avant-boite', (0.4, 0.05, 0))
XCA = XB1 + 0.011
cav = extrude([(-0.096, YB0 - 0.43 + 0.01), (0.096, YB0 - 0.43 + 0.01), (0.10, 0.03), (0.08, YB1 - 0.43 - 0.005), (-0.08, YB1 - 0.43 - 0.005), (-0.10, 0.03)],
              0.022, (XCA, 0.43, 0), (1, 0, 0), alu, bev=0.006, up=(0, 1, 0))
ca.add(cav)
ca.add(cyl(0.036, 0.016, (XCA + 0.016, YS, 0), (1, 0, 0), alu, 32))   # logement d'écrou de réglage
ca.add(cyl(0.032, 0.012, (XCA + 0.014, YP, 0), (1, 0, 0), alu, 32))
ca.add(box((0.004, 0.022, 0.012), (XCA + 0.013, 0.47, 0.06), M('plaque-alu', 0xd8dadb, 0.6, 0.4)))   # plaque (indice, n°)
ca.add(box((0.0015, YB1 - YB0 - 0.01, 2 * ZB - 0.01), (XCA - 0.0115, (YB0 + YB1) / 2, 0), joint))   # joint papier
fasteners(ca, 'vis-couvercle-boite', [((XCA + 0.012, YS + dy, dz), (1, 0, 0)) for dy, dz in ((-0.055, 0.08), (-0.055, -0.08), (0.06, 0.09), (0.06, -0.09), (0.14, 0.07), (0.14, -0.07))], r=0.006, length=0.03, travel=0.05)

cs = Part('couvercle-boite', (0.05, 0.5, 0))
XCS0, XCS1 = XB0 + 0.13, XB1 - 0.004
YCS = YB1 + 0.004
cs.add(extrude(rounded_rect(XCS1 - XCS0, 2 * ZB + 0.008, 0.012), 0.006, ((XCS0 + XCS1) / 2, YCS + 0.003, 0), (0, 1, 0), alu))
for k in range(7):   # nervures croisées du couvercle (planche 13)
    cs.add(box((0.005, 0.008, 2 * ZB - 0.02), (XCS0 + 0.02 + k * (XCS1 - XCS0 - 0.04) / 6, YCS + 0.01, 0), alu, bev=0.002))
for z in (-0.06, 0.0, 0.06):
    cs.add(box((XCS1 - XCS0 - 0.03, 0.006, 0.005), ((XCS0 + XCS1) / 2, YCS + 0.009, z), alu, bev=0.002))
cs.add(box((XCS1 - XCS0, 0.0015, 2 * ZB + 0.004), ((XCS0 + XCS1) / 2, YCS - 0.0005, 0), joint))
# levier de commande (repère 1) : rotule dans le couvercle, capuchon caoutchouc, doigt sous le couvercle
XL = XB1 - 0.03
cs.add(cyl(0.022, 0.02, (XL, YCS + 0.016, 0.0), (0, 1, 0), alu, 28))
cs.add(lathe([(0.0, 0.035), (0.008, 0.033), (0.024, 0.006), (0.024, 0.0), (0.0, 0.0)], (XL, YCS + 0.026, 0), (0, 1, 0), caoutchouc, 28, 'capuchon'))
cs.add(sphere(0.012, (XL, YCS + 0.02, 0), acier, 12, 8))
cs.add(tube([(XL, YCS - 0.055, 0.0), (XL, YCS + 0.02, 0.0), (XL + 0.01, YCS + 0.045, 0.0), (1.585, 0.545, 0.0)], 0.0055, acier, seg=8, res=6))
cs.add(box((0.012, 0.03, 0.01), (XL, YCS - 0.06, 0.0), acier_noir, bev=0.002))
cs.add(circlip(0.013, (XL, YCS + 0.006, 0), (0, 1, 0), acier_noir))
fasteners(cs, 'vis-couvercle-sup-boite', [((x, YCS + 0.006, z), (0, 1, 0)) for x in (XCS0 + 0.012, (XCS0 + XCS1) / 2, XCS1 - 0.012) for z in (ZB - 0.006, -ZB + 0.006)],
          r=0.0045, length=0.02, travel=0.04)

# =====================================================================================
# ARBRE D'EMBRAYAGE ET ARBRE PRIMAIRE (planche 14, coupe p.44)
# =====================================================================================
ap = Part('arbre-primaire', (0.15, 0.35, 0))
# arbre d'embrayage : du bout du vilebrequin (bague bronze) au manchon de l'arbre primaire
ap.add(cyl(0.0105, 1.385 - (XF - 0.012), ((1.385 + XF - 0.012) / 2, YP, 0), (1, 0, 0), acier, 20, name='arbre-embrayage'))
ap.add(splined(0.0118, 0.03, (XE + 0.008, YP, 0), (1, 0, 0), acier_taille, 20))
ap.add(splined(0.0112, 0.025, (1.37, YP, 0), (1, 0, 0), acier_taille, 18))
ap.add(lathe([(0.0115, -0.018), (0.017, -0.018), (0.017, 0.018), (0.0115, 0.018)], (1.378, YP, 0), (1, 0, 0), acier, 28, 'manchon'))
ap.add(cyl(0.0022, 0.04, (1.37, YP, 0), (0, 0, 1), acier_noir, 8, name='goupille-A'))   # goupille d'arbre d'embrayage
ap.add(helix_spring((1.37, YP + 0.018, -0.008), 'z', 0.0022, 0.016, 6, 0.0005, ressort))   # ressort de retenue
ap.add(ring(0.0175, 0.019, 0.003, (1.39, YP, 0), (1, 0, 0), acier_noir, 28, 'rondelle'))   # rondelle + anneau d'arrêt (1982)
ap.add(circlip(0.0175, (1.384, YP, 0), (1, 0, 0), acier_noir))
# arbre primaire : 5 pignons solidaires, roulements, cales de réglage, plaque de retenue et arrêtoir
ap.add(cyl(0.012, 1.575 - 1.385, ((1.575 + 1.385) / 2, YP, 0), (1, 0, 0), acier, 24, name='arbre-primaire'))
for i, (nom, zp, zs, x) in enumerate(GEARS):
    rp = ENTRAXE * zp / (zp + zs)
    ap.add(toothed(zp, rp, GW, (x, YP, 0), (1, 0, 0), acier_taille, hole=0.0115, helix=-HELIX, name=f'pignon-{nom}'))
    if rp > 0.024:
        ap.add(ring(0.012, rp - 0.006, 0.006, (x - GW / 2 - 0.003, YP, 0), (1, 0, 0), acier, 32, 'toile'))
# 2 gorges sur le pignon de 4e (identification de l'arbre primaire)
for dx in (-0.003, 0.003):
    ap.add(torus(ENTRAXE * 38 / 77 + 0.0028, 0.0006, (1.541 + dx, YP, 0), (1, 0, 0), acier_noir, 48, 6))
ap.add(toothed(11, 0.0157, 0.012, (X_SY34, YP, 0), (1, 0, 0), acier_taille, hole=0.0115, name='pignon-mar'))   # M. AR (droit)
ap.add(ball_bearing(0.012, 0.031, 0.012, (1.392, YP, 0), (1, 0, 0), acier, acier_taille))   # roulement arrière (E)
ap.add(ball_bearing(0.012, 0.028, 0.011, (1.562, YP, 0), (1, 0, 0), acier, acier_taille))   # roulement avant (G)
for k in range(2):   # cales de réglage du roulement avant (H)
    ap.add(ring(0.02, 0.028, 0.0008, (1.5685 + k * 0.0009, YP, 0), (1, 0, 0), acier_noir, 32, 'cale'))
ap.add(extrude([(-0.045, -0.018), (0.045, -0.018), (0.045, 0.012), (0.02, 0.03), (-0.02, 0.03), (-0.045, 0.012)], 0.004,
               (1.4, YP + 0.005, 0), (1, 0, 0), acier_noir, up=(0, 1, 0)))   # plaque de retenue (F)
ap.add(box((0.0025, 0.012, 0.03), (1.403, YP + 0.03, 0), acier, bev=0.001))   # arrêtoir (A, 1982)
fasteners(ap, 'vis-plaque-roulement', [((1.403, YP + 0.022, s * 0.032), (1, 0, 0)) for s in (1, -1)], r=0.0055, length=0.018, travel=0.035)

# =====================================================================================
# ARBRE SECONDAIRE : pignon d'attaque, pignons fous, synchros, écrou de réglage (planche 14)
# =====================================================================================
asc = Part('arbre-secondaire', (0.3, -0.25, 0))
asc.add(cyl(0.0125, 1.585 - (X_PIGN + 0.009), ((1.585 + X_PIGN + 0.009) / 2, YS, 0), (1, 0, 0), acier, 24, name='arbre-secondaire'))
asc.add(splined(0.0135, 0.05, (X_SY12, YS, 0), (1, 0, 0), acier_taille, 20))
asc.add(splined(0.0135, 0.05, (X_SY34, YS, 0), (1, 0, 0), acier_taille, 20))
# pignon d'attaque conique (10 dents) : grande base vers l'avant, sommet sur l'axe des roues
asc.add(toothed(10, R_PIGN, 0.018, (X_PIGN, YS, 0), (-1, 0, 0), acier_taille, taper=0.68, helix=math.radians(30), depth=0.0042, name='pignon-attaque'))
asc.add(cyl(0.017, 0.008, (X_PIGN + 0.013, YS, 0), (1, 0, 0), acier_taille, 28))
asc.add(roller_bearing(0.0135, 0.034, 0.016, (1.392, YS, 0), (1, 0, 0), acier, acier_taille))   # roulement sous tête de pignon
for i, (nom, zp, zs, x) in enumerate(GEARS):
    rs = ENTRAXE * zs / (zp + zs)
    asc.add(toothed(zs, rs, GW, (x, YS, 0), (1, 0, 0), acier_taille, hole=0.0128, helix=HELIX, name=f'pignon-fou-{nom}'))
    asc.add(ring(0.0128, 0.0175, GW + 0.002, (x, YS, 0), (1, 0, 0), bronze, 28, 'bague'))   # douille / cage à aiguilles
    if rs > 0.03:
        asc.add(ring(0.0175, rs - 0.007, GW - 0.004, (x, YS, 0), (1, 0, 0), acier, 40, 'toile'))
    # denture de crabotage et cône de synchro côté synchroniseur
    xs = X_SY12 if i < 2 else X_SY34
    side = 1 if xs > x else -1
    asc.add(toothed(28, 0.026, 0.004, (x + side * (GW / 2 + 0.002), YS, 0), (1, 0, 0), acier_taille, hole=0.0128, depth=0.0012, name='crabots'))
    asc.add(cyl(0.021, 0.006, (x + side * (GW / 2 + 0.006), YS, 0), (1, 0, 0), acier, 32, r2=0.019))
# 2 gorges sur le pignon fou de 2e et de 3e (identification)
for x, zp, zs in ((1.464, 17, 38), (1.487, 24, 35)):
    for dx in (-0.003, 0.003):
        asc.add(torus(ENTRAXE * zs / (zp + zs) + 0.0028, 0.0006, (x + dx, YS, 0), (1, 0, 0), acier_noir, 48, 6))
for xs, mar in ((X_SY12, False), (X_SY34, True)):
    # moyeu cannelé, baladeur avec gorge de fourchette, anneaux de synchro de part et d'autre
    asc.add(toothed(30, 0.024, 0.018, (xs, YS, 0), (1, 0, 0), acier, hole=0.0136, depth=0.0015, name='moyeu-synchro'))
    if mar:   # baladeur de 3e-4e : porte le pignon de M. AR (39 dents, droit)
        asc.add(toothed(39, 0.0557, 0.012, (xs, YS, 0), (1, 0, 0), acier_taille, hole=0.03, name='baladeur-3-4'))
        asc.add(lathe([(0.0255, -0.012), (0.034, -0.012), (0.034, -0.007), (0.03, -0.006), (0.03, -0.004), (0.034, -0.004), (0.034, 0.012), (0.0255, 0.012)],
                      (xs, YS, 0), (1, 0, 0), acier, 40, 'gorge'))
    else:
        asc.add(lathe([(0.0255, -0.012), (0.036, -0.012), (0.036, -0.003), (0.031, -0.003), (0.031, 0.003), (0.036, 0.003), (0.036, 0.012), (0.0255, 0.012)],
                      (xs, YS, 0), (1, 0, 0), acier, 40, 'baladeur-1-2'))
    for s in (1, -1):
        asc.add(toothed(28, 0.0245, 0.005, (xs + s * 0.0145, YS, 0), (1, 0, 0), laiton, hole=0.018, depth=0.0011, taper=0.95, name='anneau-synchro'))
    for k in range(3):   # clavettes et ressorts (Borg-Warner)
        a = 2 * math.pi * k / 3
        asc.add(box((0.016, 0.004, 0.004), (xs, YS + 0.0255 * math.cos(a), 0.0255 * math.sin(a)), acier_noir, axis=None))
asc.add(ball_bearing(0.0125, 0.03, 0.012, (1.562, YS, 0), (1, 0, 0), acier, acier_taille))   # roulement avant
asc.add(extrude([(0.024 * math.cos(math.pi / 12 + k * math.pi / 6) * (1 if k % 2 else 0.86), 0.024 * math.sin(math.pi / 12 + k * math.pi / 6) * (1 if k % 2 else 0.86)) for k in range(12)],
                0.008, (1.573, YS, 0), (1, 0, 0), acier_noir))   # écrou de réglage à créneaux (6)
asc.add(box((0.002, 0.02, 0.008), (1.578, YS + 0.026, 0), acier, bev=0.0008))   # arrêtoir
asc.add(toothed(14, 0.0085, 0.006, (1.585, YS + 0.022, 0.012), (0, 0, 1), laiton, name='pignon-tachymetre'))
fastener(asc, 'vis-tachymetre', (1.578, YS, 0), (1, 0, 0), r=0.014, length=0.012, travel=0.05)

# =====================================================================================
# MARCHE ARRIÈRE : arbre et pignon intermédiaire (planche 14, repère 5)
# =====================================================================================
mar = Part('marche-arriere', (0.15, 0.1, 0.3))
# pignon fou intermédiaire : engrène le pignon de M. AR du primaire et le baladeur de 3e-4e
YI, ZI = YP - 0.01215, 0.0336
mar.add(cyl(0.0075, 1.56 - 1.40, ((1.56 + 1.40) / 2, YI, ZI), (1, 0, 0), acier, 16, name='arbre-mar'))
mar.add(toothed(14, 0.020, 0.012, (X_SY34 - 0.016, YI, ZI), (1, 0, 0), acier_taille, hole=0.0076, name='pignon-mar-inter'))   # au point mort : dégagé
mar.add(lathe([(0.0076, -0.004), (0.016, -0.004), (0.016, 0.004), (0.0076, 0.004)], (X_SY34 - 0.026, YI, ZI), (1, 0, 0), acier, 24, 'gorge-mar'))
for x in (1.40, 1.56):
    mar.add(cyl(0.0022, 0.03, (x, YI, ZI), (0, 1, 0), acier_noir, 8, name='goupille'))

# =====================================================================================
# COMMANDE INTERNE : axes et fourchettes, sélecteur de M. AR, verrouillage (planche 15)
# =====================================================================================
fo = Part('fourchettes', (0.1, 0.25, -0.3))
ZR, YR12, YR34 = -0.078, 0.36, 0.40
for y, xs, label in ((YR12, X_SY12, '1-2'), (YR34, X_SY34, '3-4')):
    fo.add(cyl(0.006, 0.30, (1.415, y, ZR), (1, 0, 0), acier, 16, name=f'axe-{label}'))
    # coulisseau sur l'axe, bras vers le baladeur, fourchette en demi-cercle dans la gorge
    fo.add(box((0.026, 0.02, 0.02), (xs, y, ZR), acier_noir, bev=0.003))
    rr = 0.033 if label == '1-2' else 0.032
    fo.add(tube([(xs, y, ZR + 0.006), (xs, (y + YS) / 2 + 0.01, -0.05), (xs, YS, -rr - 0.006)], 0.0045, acier_noir, seg=8))
    fo.add(tube([(xs, YS + (rr + 0.003) * math.sin(math.radians(a)), -(rr + 0.003) * math.cos(math.radians(a))) for a in range(-80, 81, 10)],
                0.0032, M('fourchette', 0x8b6a3f, 0.7, 0.4), seg=8, res=2))
    for a in (-80, 80):   # patins aux extrémités
        fo.add(box((0.006, 0.008, 0.008), (xs, YS + rr * math.sin(math.radians(a)), -rr * math.cos(math.radians(a))), acier_noir, bev=0.001))
    fo.add(cyl(0.0018, 0.03, (xs, y, ZR), (0, 1, 0), acier, 8, name='goupille-fourchette'))
    # bille et ressort de verrouillage dans le carter
    fo.add(sphere(0.0035, (xs + 0.02, y + 0.008, ZR - 0.003), acier_taille, 10, 6))
    fo.add(helix_spring((xs + 0.02, y + 0.012, ZR - 0.003), 'y', 0.003, 0.02, 7, 0.0005, ressort))
# disque d'interverrouillage entre les axes
fo.add(cyl(0.007, 0.006, (1.53, (YR12 + YR34) / 2, ZR), (0, 0, 1), acier, 16))
# sélecteur et inverseur de M. AR, renvoi (repère 8)
fo.add(cyl(0.005, 0.10, (1.51, YR34 + 0.04, 0.04), (1, 0, 0), acier, 12, name='axe-mar'))
fo.add(box((0.012, 0.05, 0.012), (X_SY34 - 0.026, YR34 + 0.005, 0.035), acier_noir, bev=0.002))
fo.add(box((0.02, 0.012, 0.03), (1.535, YR34 + 0.045, 0.02), acier_noir, bev=0.002))
fastener(fo, 'vis-inverseur-mar', (1.535, YB1 - 0.002, 0.04), (0, 1, 0), r=0.006, length=0.03, travel=0.05)

# =====================================================================================
# DIFFÉRENTIEL ET COUPLE CONIQUE (planche 14, coupes p.44)
# =====================================================================================
df = Part('differentiel', (0.0, -0.22, 0))
C = (AXLE_F, YS, 0.0)
# boîtier : moyeux porte-roulements, corps percé de fenêtres, bride de couronne côté gauche
df.add(lathe([(0.017, -0.095), (0.024, -0.095), (0.024, -0.062), (0.03, -0.055), (0.048, -0.05), (0.052, -0.04), (0.052, -0.03),
              (0.046, -0.028), (0.046, 0.03), (0.034, 0.045), (0.024, 0.055), (0.024, 0.09), (0.017, 0.09)], C, (0, 0, 1), fonte, 48, 'boitier'))
# couronne (31 dents) boulonnée sur la bride, denture tournée vers le pignon d'attaque
df.add(toothed(31, R_COUR, 0.0065, (AXLE_F, YS, Z_COUR - 0.0015), (0, 0, 1), acier_taille, hole=0.036, taper=0.78, helix=math.radians(-30), depth=0.0045, name='couronne'))
df.add(ring(0.036, 0.054, 0.012, (AXLE_F, YS, Z_COUR - 0.011), (0, 0, 1), acier_taille, 48, 'voile-couronne'))
vc = []
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    vc.append(((AXLE_F + 0.044 * math.cos(a), YS + 0.044 * math.sin(a), Z_COUR - 0.019), (0, 0, -1)))
fasteners(df, 'vis-couronne', vc, r=0.0055, length=0.02, travel=0.04)
# axe des satellites (repère 9), 2 satellites, 2 planétaires cannelés, rondelles bakélisées
df.add(cyl(0.0075, 0.098, C, (0, 1, 0), acier, 16, name='axe-satellites'))
df.add(cyl(0.0022, 0.03, (AXLE_F + 0.03, YS + 0.04, 0), (1, 0, 0), acier_noir, 8, name='goupille-axe'))
for s in (1, -1):
    df.add(toothed(10, 0.017, 0.012, (AXLE_F, YS + s * 0.027, 0), (0, s, 0), acier_taille, hole=0.0076, taper=0.62, depth=0.0035, name='satellite'))
    df.add(ring(0.008, 0.019, 0.0015, (AXLE_F, YS + s * 0.035, 0), (0, 1, 0), bronze, 24, 'coussinet'))
    df.add(toothed(14, 0.024, 0.012, (AXLE_F, YS, s * 0.025), (0, 0, s), acier_taille, hole=0.011, taper=0.66, depth=0.0035, name='planetaire'))
    df.add(ring(0.012, 0.026, 0.0015, (AXLE_F, YS, s * 0.0335), (0, 0, 1), M('bakelite', 0x2a1f1b, 0.1, 0.35), 32, 'rondelle-bakelisee'))
    # roulements coniques sur les moyeux, écrous de réglage (1, 2) avec joint d'étanchéité, arrêtoirs
    df.add(roller_bearing(0.024, 0.042, 0.016, (AXLE_F, YS, s * 0.072), (0, 0, s), acier, acier_taille))
    nut = lathe([(0.03, -0.012), (0.058, -0.012), (0.058, 0.012), (0.03, 0.012)], (AXLE_F, YS, s * 0.155), (0, 0, s), acier_noir, 48, 'ecrou-reglage')
    df.add(nut)
    for k in range(12):   # créneaux de la clé B.Vi. 494
        a = 2 * math.pi * k / 12
        df.add(box((0.004, 0.006, 0.004), (AXLE_F + 0.052 * math.cos(a), YS + 0.052 * math.sin(a), s * 0.168), acier_noir, axis=None))
    df.add(ring(0.018, 0.03, 0.008, (AXLE_F, YS, s * 0.163), (0, 0, s), caoutchouc, 32, 'joint-etancheite'))
    df.add(box((0.032, 0.012, 0.004), (AXLE_F + 0.06, YS + 0.03, s * 0.185), acier, bev=0.001))   # arrêtoir (frein, 5)
    # sortie de planétaire vers la tulipe du joint GI 62
    df.add(splined(0.0105, 0.15, (AXLE_F, YS, s * 0.11), (0, 0, 1), acier_taille, 16))
fasteners(df, 'arretoirs-differentiel', [((AXLE_F + 0.07, YS + 0.03, s * 0.188), (0, 0, s)) for s in (1, -1)], r=0.0055, length=0.016, travel=0.035)

# =====================================================================================
# TRANSMISSIONS : joint tripode GI 62 côté boîte, GE 76 côté roue (planche 16, p.50)
# =====================================================================================
tr = Part('transmissions', (0, -0.35, 0))
etoile = M('etoile-retenue', 0x6d7d8a, 0.8, 0.35)
for s in (1, -1):
    zi, zo = s * 0.215, s * 0.505
    pi_, po = (AXLE_F, YS, zi), (AXLE_F, WR, zo)
    d = tuple(po[i] - pi_[i] for i in range(3))
    L = math.dist(pi_, po)
    u = tuple(c / L for c in d)
    P = lambda t, r=0.0: tuple(pi_[i] + u[i] * t for i in range(3))   # noqa: E731

    # ---- GI 62 : tulipe sur le planétaire, tripode à 3 galets, plaquette anti-déboîtage,
    # capot tôle, ressort et coupelle, soufflet et bracelet
    tul = lathe([(0.0, -0.035), (0.015, -0.035), (0.017, -0.028), (0.041, -0.022), (0.042, 0.018), (0.040, 0.022), (0.0, 0.022)], (AXLE_F, YS, s * 0.205), (0, 0, s), acier, 40, 'tulipe')
    for k in range(3):   # gorges des galets (vues en creux)
        a = 2 * math.pi * k / 3 + math.pi / 2
        c = cyl(0.0125, 0.05, (AXLE_F + 0.026 * math.cos(a), YS + 0.026 * math.sin(a), s * 0.215), (0, 0, 1), None, 16)
        boolean(tul, c)
        apply_all(tul)
        delete(c)
    tr.add(tul)
    for k in range(3):   # tripode : étoile à 3 tourillons et galets en tonneau
        a = 2 * math.pi * k / 3 + math.pi / 2
        dir_ = (math.cos(a), math.sin(a), 0)
        tr.add(cyl(0.007, 0.026, (AXLE_F + 0.013 * dir_[0], YS + 0.013 * dir_[1], zi), dir_, acier_taille, 12))
        tr.add(lathe([(0.0072, -0.007), (0.0105, -0.0065), (0.0118, 0.0), (0.0105, 0.0065), (0.0072, 0.007)],
                     (AXLE_F + 0.026 * dir_[0], YS + 0.026 * dir_[1], zi), dir_, acier_taille, 16, 'galet'))
    tr.add(cyl(0.0135, 0.014, (AXLE_F, YS, zi), (0, 0, 1), acier_taille, 6, name='moyeu-tripode'))
    tr.add(circlip(0.0105, P(0.011), u, acier_noir))
    tr.add(lathe([(0.03, 0.0), (0.043, 0.0), (0.043, 0.01), (0.036, 0.012), (0.03, 0.012)], (AXLE_F, YS, s * 0.227), (0, 0, s), tole, 40, 'capot-tole'))
    tr.add(ring(0.040, 0.044, 0.003, (AXLE_F, YS, s * 0.226), (0, 0, s), bronze, 40, 'plaquette-anti-deboitage'))
    tr.add(helix_spring((AXLE_F, YS, s * 0.19 if s > 0 else -0.21), 'z', 0.005, 0.02, 5, 0.0007, ressort))
    tr.add(lathe([(0.039, 0.0), (0.044, 0.008), (0.031, 0.018), (0.039, 0.028), (0.026, 0.040), (0.033, 0.050), (0.019, 0.066), (0.0135, 0.082), (0.0135, 0.09)], P(0.02), u, caoutchouc, 32, 'soufflet-gi62'))
    tr.add(ring(0.0135, 0.016, 0.006, P(0.106), u, acier, 20, 'bracelet'))
    # ---- arbre de transmission
    tr.add(tube([P(0.006), P(L - 0.06)], 0.0118, acier, seg=14))
    tr.add(splined(0.0125, 0.024, P(0.012), u, acier_taille, 18))
    # ---- GE 76 : bol-fusée, étoile de retenue, tripode, arbre-tulipe, soufflet et collier
    tr.add(lathe([(0.0125, -0.075), (0.019, -0.065), (0.04, -0.035), (0.046, -0.018), (0.046, 0.004), (0.036, 0.012), (0.0, 0.012)],
                 po, u, caoutchouc, 32, 'soufflet-ge76'))
    tr.add(ring(0.0125, 0.0155, 0.007, P(L - 0.074), u, acier, 20, 'collier'))
    tr.add(lathe([(0.0, 0.0), (0.035, 0.0), (0.044, 0.004), (0.048, 0.016), (0.048, 0.036), (0.04, 0.046), (0.022, 0.05), (0.018, 0.058), (0.0, 0.058)], P(L - 0.008), (0, 0, s), acier, 40, 'bol-fusee'))
    tr.add(lathe([(0.0, -0.02), (0.03, -0.02), (0.034, -0.012), (0.034, 0.004), (0.0, 0.004)], P(L - 0.015), u, acier_taille, 32, 'arbre-tulipe'))
    for k in range(3):   # étoile de retenue (3 branches) et tripode du GE 76
        a = 2 * math.pi * k / 3 + math.pi / 6
        dir_ = (math.cos(a), math.sin(a), 0)
        tip = tuple(po[i] + dir_[i] * 0.043 + (0, 0, s * 0.03)[i] for i in range(3))
        tr.add(tube([(po[0], po[1], po[2] + s * 0.05), tip], 0.0016, etoile, seg=6))
        tr.add(lathe([(0.006, -0.006), (0.0095, -0.005), (0.0105, 0.0), (0.0095, 0.005), (0.006, 0.006)],
                     (po[0] + 0.024 * dir_[0], po[1] + 0.024 * dir_[1], po[2] + s * 0.02), dir_, acier_taille, 14, 'galet'))
    tr.add(sphere(0.008, (po[0], po[1], po[2] + s * 0.035), acier_taille, 12, 8))   # rotule d'appui
    tr.add(splined(0.0125, 0.07, (AXLE_F, WR, zo + s * 0.083), (0, 0, s), acier_taille, 20))   # fusée cannelée
    tr.add(cyl(0.009, 0.02, (AXLE_F, WR, zo + s * 0.128), (0, 0, s), acier, 12))   # bout fileté

export(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'transmission.glb'))
