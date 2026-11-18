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
#   Sièges de soupapes rapportés Ø ext. 34,5 / 31,3 mm, guides Ø 7 × 11 mm (p.20) ; segments de 2, 2 et
#   3,5 mm, flasques de butée de 2,80 à 2,95 mm de part et d'autre du palier central, joint à lèvres
#   80 × 100 × 13 côté volant, joint d'arbre à cames 30 × 42 × 8 (p.21) ; pompe à huile à pignons
#   avec clapet de décharge à bille et crépine (planche 10, p.37) ; volant centré par 3 goupilles
#   dépassant de 7 mm (p.40) ; pignon de commande d'allumeur, gros déport côté embrayage (p.36).
#   Vues éclatées : culasse (planche 5, p.32), carter-cylindres (planche 6, p.33),
#   équipage mobile (planche 7, p.34), distribution (planche 8, p.35), échappement (planche 9, p.36),
#   graissage (planche 10, p.37), refroidissement (planche 11, p.38), compartiment moteur (photo p.6).
# Ce qui n'est pas coté dans la RTA (entraxe des cylindres, formes de fonderie) est estimé d'après
# les vues éclatées.
#
# Section transversale recalée sur la coupe du MR 175 (page B-21, « Moteur 688 — Coupe », PDF
# manuels/MR175-mecanique-p001-350.pdf p.34), mise à l'échelle sur l'alésage de 70 mm : plan de
# joint à 188 mm au-dessus de l'axe du vilebrequin, carter-cylindres de 159 mm de large au plan de
# joint (84 mm côté arbre à cames, 75 mm côté collecteur), jupe évasée jusqu'à un plan de joint de
# carter inférieur à l'axe du vilebrequin (238 mm de large), arbre à cames à 116 mm au-dessus et
# 77 mm sur le côté de l'axe, culasse de 153 mm de large, cache-culbuteurs en dôme de 114 mm,
# carter inférieur profond de 134 mm, décalé côté arbre à cames. Coupe longitudinale B-20 (p.33) :
# entraxe des cylindres ≈ 78-80 mm, pompe à eau en bout de culasse côté volant, chaîne à l'opposé.
#
# Implantation (comme sur la 4L) : moteur longitudinal derrière l'essieu, volant et embrayage vers
# l'avant (boîte devant), distribution par chaîne vers l'habitacle, arbre à cames côté droit
# (allumeur, pompe à essence, filtre à huile, plaque moteur), collecteurs, carburateur,
# mano-contact d'huile et bouchon de vidange d'eau côté gauche, démarreur à gauche sous le
# collecteur (equipements.py), pompe à eau et poulie d'arbre à cames côté embrayage. Bougies côté
# droit, du côté des tiges de culbuteurs et à l'opposé des collecteurs (coupes MR 175 B-21 et B-50) ;
# allumeur entre les bougies 2 et 3 (B-50 : « déposer l'allumeur pour les cylindres 2 et 3 »).
# Contrôle des côtés : photos du compartiment moteur RTA p. V et VI (prises depuis l'aile droite),
# p.23 (« manocontact, côté gauche du carter-cylindres »), p.59 (dépose du démarreur).
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (M, M_img, Part, quad, apply_all, bevel, boolean, box, cyl, delete, export, extrude, fastener,  # noqa: E402
                 fasteners, gear, hexagon, join, lathe, place, reset, rounded_rect, sphere, toothed, torus, tube)

reset()

EX = 0.92                 # milieu du bloc (repère du site)
YC = 0.40                 # axe du vilebrequin
PITCH = 0.080             # entraxe des cylindres (estimé)
CX = [EX + 0.12, EX + 0.04, EX - 0.04, EX - 0.12]   # cylindre n° 1 côté volant (avant)
BORE, STROKE, ROD = 0.070, 0.072, 0.128
YD = YC + 0.188           # plan de joint du bloc (MR 175 B-21)
HEAD_H = 0.072
YH = YD + 0.0015 + HEAD_H  # dessus de culasse (joint 1,5 mm)
XF, XR = EX + 0.185, EX - 0.185   # faces avant (volant) et arrière (distribution) du bloc
CAM_Z, CAM_Y = 0.077, YC + 0.116  # arbre à cames latéral, côté droit (MR 175 B-21)
ZB_CAM, ZB_COL = 0.084, -0.075    # flancs du carter-cylindres au plan de joint (côté arbre à cames / collecteur)
ZH_CAM, ZH_COL = 0.081, -0.072    # flancs de la culasse
ZC = (ZB_CAM + ZB_COL) / 2        # milieu du plan de joint
# Démarreur (equipements.py) : côté GAUCHE, sous le collecteur, nez dans le carter d'embrayage.
# RTA p.59 (imprimée) : pour le déposer il faut ôter le filtre à air, la bride du tuyau
# d'échappement et l'écran de protection du démarreur → il est du côté du collecteur.
# Son axe est à 141,5 mm de celui du vilebrequin (couronne Ø 259 + pignon 9 dents).
SA_Y, SA_Z = 0.412, -0.141
# Manivelles : 1 et 4 au PMH, 2 et 3 au PMB
CRANK_ANGLE = [0, math.pi, math.pi, 0]

fonte = M('fonte', 0x66717a, 0.35, 0.72)
fonte_usinee = M('fonte-usinee', 0x9aa1a6, 0.7, 0.35)
alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
alu_usine = M('alu-usine', 0xd2d5d6, 0.8, 0.25)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_taille = M('acier-taille', 0xb7bcc0, 0.95, 0.22)
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
# Corps : section relevée sur la coupe MR 175 B-21 (z, hauteur au-dessus de l'axe) : flanc côté
# arbre à cames bombé par la galerie, jupe évasée vers le plan de joint du carter inférieur, posé
# à l'axe du vilebrequin ; côté collecteur plus droit.
BLOCK_SEC = [(ZB_CAM, 0.188), (0.088, 0.172), (0.100, 0.150), (0.102, 0.116), (0.100, 0.090), (0.090, 0.068),
             (0.092, 0.045), (0.112, 0.024), (0.136, 0.008), (0.138, -0.005), (-0.100, -0.005), (-0.100, 0.008),
             (-0.092, 0.030), (-0.081, 0.075), (-0.078, 0.150), (ZB_COL, 0.188)]
body = extrude([(-z, h) for z, h in BLOCK_SEC], XF - XR, (EX, YC, 0), (1, 0, 0), fonte, bev=0.004, up=(0, 1, 0))


def drill(o, cutters):
    for c in cutters:
        boolean(o, c)
        apply_all(o)
        delete(c)


def rod_line(a, b, r, ext=0.0, seg=12):
    """Cylindre de perçage le long du segment a-b (prolongé de ext à chaque bout)."""
    d = [b[k] - a[k] for k in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    u = [v / L for v in d]
    mid = [(a[k] + b[k]) / 2 for k in range(3)]
    return cyl(r, L + 2 * ext, tuple(mid), tuple(u), None, seg)


# Intérieur (fonte creuse, coupe B-21). Chemises humides : la chambre d'eau entoure les chemises
# sur toute leur hauteur, de leur embase (plancher percé à Ø 75,5 sur lequel porte le joint d'embase)
# jusqu'au plan de joint ; sous le plancher, le carter-vilebrequin ouvert vers le carter inférieur.
H_EMB = 0.046                 # dessous du plancher d'embase (bas des chemises), au-dessus de l'axe
H_WAT = H_EMB + 0.010         # dessus du plancher = fond de la chambre d'eau
WZ0, WZ1 = -0.066, 0.052      # flancs intérieurs de la chambre d'eau (côté collecteur / côté arbre à cames)
CRANK_SEC = [(0.085, H_EMB), (0.085, 0.030), (0.104, 0.016), (0.128, 0.004), (0.128, -0.010),
             (-0.092, -0.010), (-0.092, 0.010), (-0.085, 0.030), (-0.080, H_EMB)]
cav = extrude([(-z, h) for z, h in CRANK_SEC], XF - XR - 0.016, (EX, YC, 0), (1, 0, 0), None, up=(0, 1, 0))
water = box((XF - XR - 0.022, YD - YC - H_WAT + 0.002, WZ1 - WZ0), (EX, YC + (H_WAT + YD - YC + 0.002) / 2, (WZ0 + WZ1) / 2), None)
seats = [cyl(0.0378, 0.03, (X(i), YC + H_EMB + 0.005, 0), (0, 1, 0), None, 40) for i in range(4)]
# galerie d'arbre à cames (alésages des paliers Ø 39) et galerie principale de graissage côté arbre à cames
cam_bore = cyl(0.0196, XF - XR + 0.02, (EX, CAM_Y, CAM_Z), (1, 0, 0), None, 28)
OIL_G = (YC + 0.075, 0.074)   # galerie principale : (y, z), percée de bout en bout
gallery = cyl(0.0045, XF - XR + 0.01, (EX, OIL_G[0], OIL_G[1]), (1, 0, 0), None, 12)
drill(body, [cav, water, cam_bore, gallery] + seats)
# dégagement venu de fonderie le long du démarreur (flanc gauche, côté volant)
pocket = cyl(0.044, 0.19, (XF - 0.085, SA_Y, SA_Z), (1, 0, 0), None, 28)
boolean(body, pocket)
apply_all(body)
delete(pocket)
# Tiges de culbuteurs : passent du bossage des poussoirs à la culasse en traversant le plan de joint
PUSH_Z_TOP = 0.040
ROCK_Y = YH + 0.050


def pushrod_ends(x):
    return (x, CAM_Y + 0.048, CAM_Z), (x, ROCK_Y - 0.006, PUSH_Z_TOP)


VALVE_X = [X(i) + s for i in range(4) for s in (0.017, -0.017)]
# passages d'eau du plan de joint vers la culasse (entre la chemise et la paroi, des deux côtés)
WATER_HOLES = [(X(i) + dx, z) for i in range(4) for dx, z in ((0.0, WZ1 - 0.006), (0.0, WZ0 + 0.007))] + [(XR + 0.012, 0.0), (XF - 0.012, 0.0)]
drill(body, [rod_line(*pushrod_ends(x), 0.0055) for x in VALVE_X])
bloc.add(body)
# Plan de joint usiné, percé des 4 chemises, des passages d'eau et des 8 tiges de culbuteurs
deck = extrude(rounded_rect(XF - XR, ZB_CAM - ZB_COL, 0.006), 0.006, (EX, YD - 0.003, ZC), (0, 1, 0), fonte_usinee)
drill(deck, [cyl(0.0405, 0.05, (X(i), YD, 0), (0, 1, 0), None, 40) for i in range(4)]
      + [cyl(0.0045, 0.03, (x, YD, z), (0, 1, 0), None, 12) for x, z in WATER_HOLES]
      + [rod_line(*pushrod_ends(x), 0.0055) for x in VALVE_X])
bloc.add(deck)
# Cloisons de paliers (5) : voiles de fonte qui ferment le carter-vilebrequin au droit de chaque
# tourillon, alésées pour les coussinets (Ø 57) ; les chapeaux sont avec le vilebrequin
JOURNALS = [XF - 0.012, X(0) - PITCH / 2, EX, X(2) - PITCH / 2, XR + 0.012]
WEB_SEC = [(z, max(h, -0.005)) for z, h in CRANK_SEC]
for x in JOURNALS:
    web = extrude([(-z, h) for z, h in WEB_SEC], 0.020, (x, YC, 0), (1, 0, 0), fonte, up=(0, 1, 0))
    drill(web, [cyl(0.0285, 0.03, (x, YC, 0), (1, 0, 0), None, 40),
                rod_line((x, OIL_G[0], OIL_G[1]), (x, YC + 0.022, 0.018), 0.0028)])   # perçage d'huile galerie → palier
    bloc.add(web)
# bouchons de galerie de graissage et de galerie d'arbre à cames (bouts)
for x in (XF + 0.001, XR - 0.001):
    bloc.add(cyl(0.006, 0.004, (x, OIL_G[0], OIL_G[1]), (1, 0, 0), acier_noir, 12))
# Nervures verticales côté gauche (entre cylindres) et côté droit
for x in [XF - 0.005, X(0) - PITCH / 2, X(1) - PITCH / 2, X(2) - PITCH / 2, XR + 0.005]:
    bloc.add(box((0.012, 0.11, 0.010), (x, YD - 0.075, ZB_COL - 0.007), fonte, bev=0.003))
# Galerie d'arbre à cames côté droit (alésée Ø 39) et bossage des poussoirs (alésages Ø 19)
gal = cyl(0.026, XF - XR - 0.01, (EX, CAM_Y, CAM_Z), (1, 0, 0), fonte, 28)
drill(gal, [cyl(0.0196, XF - XR + 0.02, (EX, CAM_Y, CAM_Z), (1, 0, 0), None, 28)])
bloc.add(gal)
tb = box((XF - XR - 0.02, 0.05, 0.03), (EX, CAM_Y + 0.035, CAM_Z + 0.01), fonte, bev=0.005)
drill(tb, [cyl(0.0098, 0.07, (x, CAM_Y + 0.04, CAM_Z), (0, 1, 0), None, 20) for x in VALVE_X]
      + [cyl(0.0196, XF - XR + 0.02, (EX, CAM_Y, CAM_Z), (1, 0, 0), None, 28)])
bloc.add(tb)
# Bossage d'allumeur et colonne de l'arbre de commande de pompe à huile (droite, entre les cylindres
# 2 et 3), venus de fonderie, alésés pour l'arbre
PX, PZ = EX, CAM_Z + 0.032
for o in (cyl(0.022, 0.05, (EX, CAM_Y + 0.07, PZ), (0, 1, 0), fonte, 24),
          cyl(0.014, CAM_Y - YC - 0.01, (EX, (CAM_Y + YC - 0.005) / 2 - 0.004, PZ), (0, 1, 0), fonte, 20)):
    drill(o, [cyl(0.0058, 0.3, (EX, CAM_Y, PZ), (0, 1, 0), None, 14)])
    bloc.add(o)
bloc.add(cyl(0.038, 0.03, (EX - 0.075, YC + 0.052, 0.112), (0, 0, 1), fonte, 32))   # portée de filtre
bloc.add(cyl(0.030, 0.012, (EX - 0.075, YC + 0.052, 0.128), (0, 0, 1), fonte_usinee, 32))
bloc.add(box((0.06, 0.05, 0.02), (EX + 0.03, CAM_Y - 0.02, 0.105), fonte, bev=0.004))     # pompe à essence
# Bouchons de dessablage (pastilles) côté gauche
for x in (X(0) - 0.02, X(3) + 0.02):
    bloc.add(cyl(0.016, 0.006, (x, YD - 0.085, ZB_COL - 0.005), (0, 0, 1), acier_noir, 24))
# Supports moteur (planche 4) : pattes et tampons obliques
for s in (1, -1):
    bloc.add(box((0.07, 0.06, 0.075), (EX - 0.04, YC + 0.06, s * 0.115), fonte, bev=0.006))
    bloc.add(box((0.09, 0.008, 0.07), (EX - 0.04, YC + 0.035, s * 0.15), acier_noir, bev=0.002))
    bloc.add(cyl(0.028, 0.045, (EX - 0.04, YC + 0.0, s * 0.175), (0, -0.6, s), caoutchouc, 20))
# Plaque moteur rivée sur le flanc droit, en arrière de l'alternateur (RTA p.5) : type 688 D7 12 et numéro
def _plaque_moteur():
    import tempfile
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (320, 150), (205, 205, 196))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 2, 317, 147), outline=(90, 90, 90), width=4)
    fp = next((f for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if os.path.exists(f)), None)
    f = ImageFont.truetype(fp, 46) if fp else None
    d.text((160, 48), '688 D7 / 12', fill=(25, 25, 25), font=f, anchor='mm')
    d.text((160, 108), 'N° ·········', fill=(25, 25, 25), font=f, anchor='mm')
    path = os.path.join(tempfile.mkdtemp(prefix='pm-'), 'plaque-moteur.png')
    im.save(path)
    return path


bloc.add(quad((EX + 0.065, YD - 0.022, 0.0925), 0.064, 0.030, (0, 0, 1), M_img('plaque-moteur', _plaque_moteur(), 0.6, 0.4), 'plaque-moteur'))
for dx in (-0.028, 0.028):
    bloc.add(cyl(0.0025, 0.003, (EX + 0.065 + dx, YD - 0.022, 0.093), (0, 0, 1), acier, 10))
# Manocontact de pression d'huile côté gauche (p.37)
bloc.add(extrude(hexagon(0.011), 0.01, (EX - 0.10, CAM_Y - 0.02, -0.083), (0, 0, -1), acier))
bloc.add(cyl(0.010, 0.022, (EX - 0.10, CAM_Y - 0.02, -0.099), (0, 0, -1), noir, 16))
bloc.add(lathe([(0.040, -0.0065), (0.050, -0.0065), (0.050, 0.0065), (0.046, 0.0065), (0.041, 0.002), (0.040, 0.002)],
              (XF - 0.004, YC, 0), (1, 0, 0), caoutchouc, 40, 'joint-vilebrequin'))   # 80 × 100 × 13
bloc.add(lathe([(0.015, -0.004), (0.021, -0.004), (0.021, 0.004), (0.015, 0.004)], (XF - 0.004, CAM_Y, CAM_Z), (1, 0, 0), caoutchouc, 24, 'joint-aac'))   # 30 × 42 × 8
fastener(bloc, 'bouchon-vidange-bloc', (EX + 0.03, YC + 0.045, -0.090), (0, 0, -1), kind='plug', r=0.008, length=0.02, travel=0.05)
# Vis d'assemblage boîte / moteur autour de la face avant
fix_b = []
for a in (30, 90, 150, 238, 270, 330):   # à 210° : bride du démarreur
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
    top = yp_pin + 0.0235   # hauteur de compression : piston au PMH à 0,5 mm sous le plan de joint (B-21)
    # piston creux : calotte plate de 7 mm, jupe de 3,5 mm, deux bossages d'axe venus de fonderie
    ct = top - yp_pin
    pist = lathe([(0, ct), (0.0345, ct), (0.0349, ct - 0.004), (0.0349, -0.040), (0.0314, -0.040), (0.0314, ct - 0.024),
                  (0.030, ct - 0.007), (0.0, ct - 0.007)], (x, yp_pin, 0), (0, 1, 0), alu_usine, 40)
    chem.add(pist)
    for sz in (1, -1):
        chem.add(cyl(0.012, 0.019, (x, yp_pin + 0.002, sz * 0.0215), (0, 0, 1), alu_usine, 20))
        chem.add(box((0.016, ct - 0.007 - 0.002, 0.008), (x, yp_pin + 0.002 + (ct - 0.007 - 0.002) / 2, sz * 0.024), alu_usine))   # nervure bossage → calotte
        chem.add(torus(0.0085, 0.0008, (x, yp_pin, sz * 0.0285), (0, 0, 1), acier_noir, 16, 4))   # jonc d'arrêt d'axe
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
    # section en I : un évidement sur chaque face, l'âme fait 6 mm
    drill(shank, [box((0.006, ROD - 0.07, 0.014), (x + sx * 0.0075, yp_pin - ROD / 2 + 0.005, 0), None) for sx in (1, -1)])
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
for dx in (-0.0125, 0.0125):   # demi-flasques de butée (jeu latéral) du palier central
    vil.add(lathe([(0.029, -0.0014), (0.042, -0.0014), (0.042, 0.0014), (0.029, 0.0014)], (EX + dx, YC, 0), (1, 0, 0), bronze, 32, 'flasque-butee', angle=math.pi))
vil.add(lathe([(0.0105, 0.0), (0.016, 0.0), (0.016, 0.022), (0.0105, 0.022)], (XF - 0.012, YC, 0), (1, 0, 0), bronze, 24, 'douille'))   # bague de centrage d'arbre primaire

# =====================================================================================
# VOLANT MOTEUR (7 vis) et COURONNE
# =====================================================================================
vol = Part('volant-moteur', (0.3, 0, 0))
vol.add(lathe([(0.012, 0), (0.12, 0), (0.125, 0.004), (0.125, 0.034), (0.098, 0.034), (0.095, 0.026), (0.06, 0.026), (0.05, 0.018), (0.012, 0.018)],
              (XF + 0.010, YC, 0), (1, 0, 0), fonte_usinee, 64))
vol.add(gear(0.127, 0.132, 96, 0.012, (XF + 0.03, YC, 0), (1, 0, 0), acier, 'couronne', hole=0.124))
vf = []
for k in range(7):
    a = 2 * math.pi * k / 7
    vf.append(((XF + 0.029, YC + 0.024 * math.cos(a), 0.024 * math.sin(a)), (1, 0, 0)))
fasteners(vol, 'vis-volant', vf, r=0.0055, length=0.025, travel=0.05)
for k in range(3):
    a = 2 * math.pi * k / 3 + math.pi / 2
    vol.add(cyl(0.004, 0.014, (XF + 0.044, YC + 0.110 * math.cos(a), 0.110 * math.sin(a)), (1, 0, 0), acier, 10))
vol.add(lathe([(0.06, 0.0), (0.094, 0.0), (0.094, 0.0012), (0.06, 0.0012)], (XF + 0.0367, YC, 0), (1, 0, 0), fonte_usinee, 64, 'face-friction'))

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
aac.add(toothed(13, 0.016, 0.014, (EX, CAM_Y, CAM_Z), (1, 0, 0), acier, helix=math.radians(45), depth=0.0018, name='pignon-allumeur'))
aac.add(box((0.006, 0.03, 0.05), (XR - 0.004, CAM_Y, CAM_Z), acier_noir, bev=0.003))   # bride de butée
fasteners(aac, 'vis-bride-aac', [((XR - 0.008, CAM_Y + 0.017, CAM_Z), (-1, 0, 0)), ((XR - 0.008, CAM_Y - 0.017, CAM_Z), (-1, 0, 0))], r=0.005, length=0.015, travel=0.04)
# poulie d'arbre à cames côté embrayage (courroie de pompe à eau et d'alternateur)
aac.add(lathe([(0.012, -0.009), (0.05, -0.009), (0.05, -0.006), (0.044, 0.0), (0.05, 0.006), (0.05, 0.009), (0.012, 0.009)], (XF + 0.07, CAM_Y, CAM_Z), (1, 0, 0), acier_noir, 40))

culb = Part('culbuterie', (0, 0.7, 0.05))
# poussoirs Ø 19 au-dessus de l'arbre à cames, tiges 173 × Ø 5 jusqu'aux culbuteurs
ROCK_Z = 0.010
VALVE_Z = -0.008
CH_D = 0.009          # profondeur des chambres « baignoire » (volume 33,3 cm³, p.20)
rockers_adj = []
for n, (x, adm) in enumerate(VALVES):
    yt = CAM_Y + 0.020
    culb.add(lathe([(0, 0), (0.0095, 0), (0.0095, 0.030), (0.006, 0.031), (0, 0.027)], (x, yt, CAM_Z), (0, 1, 0), acier, 20))
    bottom = (x, yt + 0.028, CAM_Z)
    topp = (x, ROCK_Y - 0.006, PUSH_Z_TOP)
    culb.add(tube([bottom, topp], 0.0025, acier, seg=6))
    # culbuteur : bras de la soupape (patin) jusqu'à la vis de réglage au-dessus de la tige
    # profil (z, y) relatif à l'axe : bossage d'axe, bras de vis de réglage, bras de patin
    arm = [(PUSH_Z_TOP - ROCK_Z + 0.007, 0.004), (PUSH_Z_TOP - ROCK_Z + 0.007, 0.0115), (0.006, 0.011), (-0.005, 0.0105),
           (VALVE_Z - ROCK_Z - 0.002, 0.004), (VALVE_Z - ROCK_Z - 0.007, -0.002), (VALVE_Z - ROCK_Z - 0.004, -0.0085),
           (VALVE_Z - ROCK_Z + 0.004, -0.006), (-0.006, -0.009), (0.006, -0.0095), (PUSH_Z_TOP - ROCK_Z - 0.006, -0.002)]
    culb.add(extrude(arm, 0.010, (x, ROCK_Y, ROCK_Z), (1, 0, 0), acier, bev=0.0015, up=(0, 1, 0)))
    culb.add(cyl(0.0088, 0.013, (x, ROCK_Y, ROCK_Z), (1, 0, 0), acier, 20))
    culb.add(cyl(0.0035, 0.004, (x, ROCK_Y - 0.0095, VALVE_Z), (0, 1, 0), acier_noir, 10))   # patin trempé
    rockers_adj.append(((x, ROCK_Y + 0.006, PUSH_Z_TOP), (0, 1, 0)))
culb.add(cyl(0.0095, XF - XR - 0.02, (EX, ROCK_Y, ROCK_Z), (1, 0, 0), fonte_usinee, 20))   # axe de culbuteurs
for x in (XF - 0.02, X(0) - PITCH / 2, EX, X(2) - PITCH / 2, XR + 0.02):   # paliers d'axe
    culb.add(box((0.016, 0.05, 0.03), (x, YH + 0.025, ROCK_Z), fonte, bev=0.003))
for x in [X(i) - PITCH / 2 + 0.005 for i in range(3)] + [X(i) + PITCH / 2 - 0.005 for i in range(3)]:   # ressorts d'écartement
    culb.add(cyl(0.0075, 0.012, (x, ROCK_Y, ROCK_Z), (1, 0, 0), acier_noir, 12))
fasteners(culb, 'vis-reglage-culbuteurs', rockers_adj, kind='nut', r=0.0055, length=0.022, travel=0.015)

# =====================================================================================
# SOUPAPES ET RESSORTS
# =====================================================================================
soup = Part('soupapes', (0, 0.95, 0))
SEATS = []   # sièges rapportés, posés avec la culasse
for x, adm in VALVES:
    rh = 0.0335 / 2 if adm else 0.0305 / 2
    seat = YD + 0.0015 + CH_D   # plafond de la chambre de combustion
    soup.add(lathe([(0, 0), (rh, 0), (rh, 0.0015), (0.0045, 0.010), (0.0035, 0.014), (0.0035, 0.1015), (0, 0.1015)],
                   (x, seat, VALVE_Z), (0, 1, 0), acier, 24))
    # ressort : hélice
    pts = []
    turns, h0, h1 = 6.0, YH + 0.002, YH + 0.030
    for k in range(int(turns * 12) + 1):
        a = 2 * math.pi * k / 12
        pts.append((x + 0.0125 * math.cos(a), h0 + (h1 - h0) * k / (turns * 12), VALVE_Z + 0.0125 * math.sin(a)))
    soup.add(tube(pts, 0.0017, acier_noir, seg=6, res=2))
    soup.add(lathe([(0.0035, 0), (0.0145, 0), (0.0145, 0.003), (0.006, 0.005), (0.0035, 0.005)], (x, h1, VALVE_Z), (0, 1, 0), acier, 20))   # coupelle
    soup.add(lathe([(0.0055, 0), (0.0145, 0), (0.0145, 0.0015), (0.0055, 0.0015)], (x, h0 - 0.0015, VALVE_Z), (0, 1, 0), acier_noir, 20))   # coupelle inférieure
    soup.add(lathe([(0.0036, 0.0), (0.0062, 0.0), (0.0052, 0.008), (0.0036, 0.007)], (x, h1, VALVE_Z), (0, 1, 0), acier_noir, 12, 'clavettes'))   # 2 demi-cônes
    soup.add(lathe([(0.0035, 0.0), (0.0055, 0.0), (0.0055, 0.035), (0.0035, 0.035)], (x, seat + 0.014, VALVE_Z), (0, 1, 0), M('fonte-guide', 0x7c7468, 0.5, 0.6), 16, 'guide'))   # guide Ø 7 × 11
    soup.add(lathe([(0.0035, 0.0), (0.0062, 0.0), (0.0062, 0.005), (0.0035, 0.006)], (x, seat + 0.049, VALVE_Z), (0, 1, 0), caoutchouc, 16, 'joint-queue'))
    SEATS.append((x, seat, rh, 0.0345 / 2 if adm else 0.0313 / 2))

# =====================================================================================
# JOINT DE CULASSE
# =====================================================================================
jc = Part('joint-culasse', (0, 0.45, 0))
gasket = extrude(rounded_rect(XF - XR - 0.004, ZB_CAM - ZB_COL - 0.004, 0.01), 0.0015, (EX, YD + 0.00075, ZC), (0, 1, 0), joint_cul)
drill(gasket, [cyl(0.036, 0.02, (X(i), YD, 0), (0, 1, 0), None, 36) for i in range(4)]
       + [cyl(0.0045, 0.02, (x, YD, z), (0, 1, 0), None, 12) for x, z in WATER_HOLES]
       + [rod_line(*pushrod_ends(x), 0.0055) for x in VALVE_X])
jc.add(gasket)
for i in range(4):
    jc.add(torus(0.0365, 0.0012, (X(i), YD + 0.0008, 0), (0, 1, 0), acier, 40, 6))

# =====================================================================================
# CULASSE (planche 5)
# =====================================================================================
cul = Part('culasse', (0, 0.55, 0))
hb = box((XF - XR + 0.006, HEAD_H, ZH_CAM - ZH_COL), (EX, YD + 0.0015 + HEAD_H / 2, (ZH_CAM + ZH_COL) / 2), alu, bev=0.005)
# chambre des culbuteurs : creusée dans le dessus
pocket = box((XF - XR - 0.02, 0.03, 0.11), (EX, YH, 0.002), None)
boolean(hb, pocket)
apply_all(hb)
delete(pocket)
# chambre d'eau : noyaux entre les cylindres et aux bouts (au-dessus des passages du joint), dégagés
# des vis de culasse ; passages des tiges de culbuteurs vers la rampe
drill(hb, [box((0.012, 0.034, 0.07), (x, YD + 0.0035 + 0.017, 0.0), None) for x in [X(0) + PITCH / 2] + [X(i) - PITCH / 2 for i in range(4)]]
      + [box((XF - XR - 0.03, 0.012, 0.008), (EX, YD + 0.008, WZ1 - 0.006), None)]
      + [rod_line(*pushrod_ends(x), 0.0055) for x in VALVE_X])
# chambres de combustion en baignoire sous chaque paire de soupapes, conduits d'admission et d'échappement
for i in range(4):
    for c in (box((0.064, 0.02, 0.044), (X(i), YD + 0.0015 + CH_D - 0.01, VALVE_Z - 0.004), None, bev=0.008),
              cyl(0.0125, 0.12, (X(i) + (0.017 if i % 2 == 0 else -0.017), YD + 0.034, -0.07), (0, 0, 1), None, 16)):
        boolean(hb, c)
        apply_all(hb)
        delete(c)
cul.add(hb)
for x, seat, rh, rs in SEATS:   # sièges rapportés (fonte spéciale, emmanchés à force)
    cul.add(lathe([(rh - 0.002, 0.0), (rs, 0.0), (rs, 0.0045), (rh - 0.0005, 0.0045)], (x, seat - 0.0005, VALVE_Z), (0, 1, 0), M('fonte-siege', 0x6b6f72, 0.6, 0.5), 32, 'siege'))
# Nervures et bossages latéraux (côté gauche : conduits ; côté droit : passages de tiges)
for i in range(4):
    cul.add(box((0.05, 0.034, 0.012), (X(i), YD + 0.035, ZH_COL - 0.005), alu, bev=0.004))   # brides d'échappement
for x in (EX + 0.08, EX - 0.08):
    cul.add(box((0.05, 0.03, 0.012), (x, YD + 0.06, ZH_COL - 0.005), alu, bev=0.004))           # brides d'admission (siamoises)
for i in range(4):  # puits de bougies côté droit, entre les tiges de culbuteurs (B-21, B-50)
    cul.add(cyl(0.012, 0.03, (X(i), YD + 0.03, ZH_CAM - 0.008), (0, 0.45, 1), alu, 20))
for i in (0, 1, 3, 4):  # nervures verticales côté tiges de culbuteurs (vue MR 175 B-23), dégagées au droit de l'allumeur
    cul.add(box((0.008, HEAD_H - 0.01, 0.008), (XR + 0.02 + i * 0.0825, YD + 0.038, ZH_CAM + 0.002), alu, bev=0.002))
# sortie d'eau vers la pompe, côté volant
cul.add(box((0.02, 0.05, 0.08), (XF + 0.008, YD + 0.04, 0.02), alu, bev=0.005))
# goujons du cache-culbuteurs
for x in (EX + 0.06, EX - 0.06):
    cul.add(cyl(0.0035, 0.11, (x, YH + 0.04, -0.01), (0, 1, 0), acier, 10))
# Vis de culasse : rangée gauche 7 5 2 4 10, rangée droite 9 3 1 6 8 (de l'avant vers l'arrière)
HBX = [EX + 0.16, EX + 0.08, EX, EX - 0.08, EX - 0.16]
hbolts = [((x, YH - 0.012, -0.050), (0, 1, 0)) for x in HBX] + [((x, YH - 0.012, 0.062), (0, 1, 0)) for x in HBX]
fasteners(cul, 'vis-culasse', hbolts, r=0.0095, length=0.105, travel=0.17)
fastener(cul, 'thermocontact', (XR - 0.002, YD + 0.05, 0.04), (-1, 0, 0), kind='bolt', r=0.009, length=0.015, travel=0.04)

# =====================================================================================
# CACHE-CULBUTEURS (planche 5) : couvercle nervuré, bouchon de remplissage, 2 écrous
# =====================================================================================
cc = Part('cache-culbuteurs', (0, 0.85, 0))
XCC = XF - XR - 0.012
# carter allongé : profil (z, y) extrudé le long de x, extrémités arrondies par biseau
# dôme étroit de la coupe MR 175 B-21 : flancs presque droits puis dessus arrondi (114 mm de large)
prof = [(-0.058, 0.0), (0.058, 0.0), (0.058, 0.026), (0.055, 0.046), (0.047, 0.060), (0.032, 0.070), (0.012, 0.074),
        (-0.012, 0.074), (-0.032, 0.070), (-0.047, 0.060), (-0.055, 0.046), (-0.058, 0.026)]
cover = extrude(prof, XCC, (EX, YH + 0.004, 0.002), (1, 0, 0), rouge, bev=0.010, up=(0, 1, 0))
cc.add(cover)
cc.add(box((XCC + 0.012, 0.004, 0.128), (EX, YH + 0.003, 0.002), rouge, bev=0.0015))   # rebord de pose
for k in range(4):   # nervures longitudinales des flancs (vue MR 175 B-23)
    for s in (1, -1):
        cc.add(box((XCC - 0.05, 0.004, 0.004), (EX, YH + 0.012 + k * 0.011, 0.002 + s * 0.0585), rouge, bev=0.0015))
cc.add(box((XCC + 0.012, 0.003, 0.126), (EX, YH + 0.0015, 0.002), joint, bev=0.001))   # joint
cc.add(cyl(0.024, 0.008, (EX - 0.10, YH + 0.078, 0.012), (0, 1, 0), rouge, 28))           # embase du bouchon
cc.add(cyl(0.009, 0.03, (EX + 0.12, YH + 0.045, 0.062), (0.3, 0.5, 1), noir, 14))         # reniflard
fasteners(cc, 'fix-cache-culbuteurs', [((x, YH + 0.077, -0.01), (0, 1, 0)) for x in (EX + 0.06, EX - 0.06)], kind='nut', r=0.0065, length=0.01, travel=0.05)
fastener(cc, 'bouchon-remplissage-huile', (EX - 0.10, YH + 0.082, 0.012), (0, 1, 0), kind='screw', r=0.024, length=0.012, travel=0.06)

# =====================================================================================
# CARTER INFÉRIEUR (planche 6) : tôle emboutie, bouchon de vidange
# =====================================================================================
sump = Part('carter-huile', (0, -0.45, 0))
# coupe MR 175 B-21 : plan de joint à l'axe du vilebrequin, cuve profonde de 134 mm décalée côté
# arbre à cames (de -82 à +122 mm), large rebord de pose (-100 à +138 mm)
YS = YC - 0.005
SZ0, SZ1 = -0.082, 0.126   # côté droit : 4 mm de plus que B-21 pour loger la pompe à huile
sprof = [(-0.100, 0.0), (0.138, 0.0), (0.138, -0.004), (SZ1 + 0.004, -0.008), (SZ1, -0.016), (SZ1, -0.112), (SZ1 - 0.022, -0.134),
         (SZ0 + 0.022, -0.134), (SZ0, -0.112), (SZ0, -0.016), (SZ0 - 0.004, -0.008), (-0.100, -0.004)]
pan = extrude([(-z, h) for z, h in sprof], XF - XR - 0.03, (EX, YS, 0), (1, 0, 0), tole, bev=0.010, up=(0, 1, 0))
# cuve en tôle emboutie de 1,5 mm, ouverte en haut
T_S = 0.0015
inner = [(SZ1 - T_S, 0.012), (SZ1 - T_S, -0.112), (SZ1 - 0.022, -0.134 + T_S), (SZ0 + 0.022, -0.134 + T_S), (SZ0 + T_S, -0.112), (SZ0 + T_S, 0.012)]
drill(pan, [extrude([(-z, h) for z, h in inner], XF - XR - 0.03 - 2 * T_S, (EX, YS, 0), (1, 0, 0), None, up=(0, 1, 0))])
sump.add(pan)
def OPEN():
    return box((XF - XR - 0.03 - 2 * T_S - 0.004, 0.02, SZ1 - SZ0 - 2 * T_S - 0.004), (EX, YS, (SZ0 + SZ1) / 2), None)



rebord = box((XF - XR - 0.03, 0.004, 0.238), (EX, YS - 0.002, 0.019), tole, bev=0.001)   # rebord (arrêté avant les joints de bout de vilebrequin)
drill(rebord, [OPEN()])
sump.add(rebord)
for k in range(2):   # bossages d'emboutissage
    for zz in (SZ1 + 0.0005, SZ0 - 0.0005):
        sump.add(box((XF - XR - 0.08, 0.008, 0.006), (EX, YS - 0.05 - k * 0.03, zz), tole, bev=0.003))
jt = box((XF - XR - 0.03, 0.003, 0.240), (EX, YS + 0.0015, 0.019), joint)
drill(jt, [OPEN()])
sump.add(jt)
fastener(sump, 'bouchon-vidange', (EX - 0.06, YS - 0.134, 0.02), (0, -1, 0), kind='plug', r=0.011, length=0.016, travel=0.08)
sv = []
for k in range(7):
    x = XR + 0.015 + k * (XF - XR - 0.03) / 6
    for zz in (0.133, -0.092):
        sv.append(((x, YS - 0.004, zz), (0, -1, 0)))
fasteners(sump, 'vis-carter-huile', sv, r=0.005, length=0.015, travel=0.03)

# =====================================================================================
# POMPE À HUILE (planche 10) : dans le carter, entraînée par l'arbre à cames
# =====================================================================================
ph = Part('pompe-huile', (0, -0.3, 0.2))
# MR 175 B-84 : corps vertical en alu boulonné sous le carter-cylindres par 3 vis, au pied de la
# colonne de l'arbre de commande ; pignons menant et mené, couvercle, clapet de décharge (bille,
# ressort, bouchon serti), crépine en cloche sous le couvercle. Arbre de commande long, pignon
# hélicoïdal en haut engrené sur l'arbre à cames (il entraîne aussi l'allumeur par sa fente).
PX, PZ = EX, CAM_Z + 0.032
PT = YC - 0.005                    # plan de pose sous le carter-cylindres
PB = YC - 0.088                    # bas du corps (plan du couvercle)
ph.add(toothed(13, 0.016, 0.016, (PX, CAM_Y, PZ), (0, 1, 0), acier, hole=0.004, helix=math.radians(-45), depth=0.0018, name='pignon-commande'))
ph.add(box((0.022, 0.004, 0.003), (PX + 0.002, CAM_Y + 0.0095, PZ), acier_noir))   # fente d'entraînement de l'allumeur
ph.add(cyl(0.0045, CAM_Y - PB - 0.01, (PX, (CAM_Y + PB + 0.01) / 2, PZ), (0, 1, 0), acier, 12, name='arbre-commande'))
# bride triangulaire à 3 trous et colonne (profil v -> -z : pointe vers le centre du carter)
ph.add(extrude([(0.0, 0.026), (0.024, -0.014), (-0.024, -0.014)], 0.006, (PX, PT - 0.003, PZ - 0.004), (0, 1, 0), alu, bev=0.003))
ph.add(cyl(0.012, PT - PB - 0.03, (PX, (PT + PB + 0.03) / 2, PZ), (0, 1, 0), alu, 20, name='colonne'))
# corps des pignons, décalé vers l'intérieur du carter, et couvercle
GZ = PZ - 0.0065
ph.add(box((0.052, 0.030, 0.040), (PX + 0.010, PB + 0.015, GZ), alu, bev=0.003))
ph.add(toothed(8, 0.0105, 0.012, (PX, PB + 0.012, PZ), (0, 1, 0), acier_taille, hole=0.0045, depth=0.0028, name='pignon-menant'))
ph.add(toothed(8, 0.0105, 0.012, (PX + 0.021, PB + 0.012, PZ), (0, 1, 0), acier_taille, hole=0.004, depth=0.0028, phase=math.pi / 8, name='pignon-mene'))
ph.add(cyl(0.004, 0.02, (PX + 0.021, PB + 0.015, PZ), (0, 1, 0), acier, 10, name='axe-pignon-fou'))
ph.add(box((0.052, 0.005, 0.040), (PX + 0.010, PB - 0.0025, GZ), alu, bev=0.002))   # couvercle
# clapet de décharge : alésage latéral, bille, ressort, bouchon
ph.add(cyl(0.007, 0.022, (PX + 0.042, PB + 0.012, GZ), (1, 0, 0), alu, 14, name='logement-clapet'))
ph.add(sphere(0.0038, (PX + 0.034, PB + 0.012, GZ), acier_taille, 10, 6))
ph.add(tube([(PX + 0.037 + 0.012 * k / 48, PB + 0.012 + 0.0028 * math.cos(2 * math.pi * k / 8), GZ + 0.0028 * math.sin(2 * math.pi * k / 8)) for k in range(49)], 0.0005, acier_noir, seg=5, res=1))
ph.add(cyl(0.0075, 0.004, (PX + 0.054, PB + 0.012, GZ), (1, 0, 0), acier, 14, name='bouchon-clapet'))
# crépine en cloche sous le couvercle (grillage dans une coupelle emboutie)
CR = (PX - 0.004, YS - 0.118, PZ - 0.040)
ph.add(tube([(PX + 0.002, PB - 0.005, GZ - 0.006), (PX, PB - 0.016, GZ - 0.014), (CR[0], CR[1] + 0.016, CR[2])], 0.007, acier_noir, seg=10))
ph.add(lathe([(0.0, 0.0), (0.032, 0.0), (0.034, 0.006), (0.034, 0.012), (0.012, 0.016), (0.0, 0.016)], CR, (0, 1, 0), acier_noir, 32, 'crepine'))
ph.add(lathe([(0.026, -0.0005), (0.033, -0.0005), (0.033, 0.0005), (0.026, 0.0005)], (CR[0], CR[1] + 0.001, CR[2]), (0, 1, 0), M('grillage', 0x8a8f93, 0.8, 0.5), 32))
fasteners(ph, 'vis-pompe-huile', [((PX + dx, PT - 0.006, PZ - 0.004 + dz), (0, -1, 0)) for dx, dz in ((0.0, -0.020), (0.018, 0.010), (-0.018, 0.010))], r=0.005, length=0.03, travel=0.04)

# =====================================================================================
# DISTRIBUTION (planche 8) : pignons, chaîne simple, tendeur, carter nervuré en tôle
# =====================================================================================
ch = Part('chaine-distribution', (-0.25, 0.05, 0))
XD = XR - 0.012
ch.add(toothed(19, 0.0205, 0.008, (XD, YC, 0), (1, 0, 0), acier, hole=0.008, depth=0.0018, name='pignon-vilebrequin'))
ch.add(lathe([(0.008, -0.004), (0.014, -0.004), (0.014, 0.007), (0.008, 0.007)], (XD, YC, 0), (1, 0, 0), acier, 24))   # moyeu
ch.add(box((0.012, 0.0025, 0.004), (XD, YC + 0.008, 0), acier_noir))   # clavette
sp = toothed(38, 0.0412, 0.007, (XD, CAM_Y, CAM_Z), (1, 0, 0), acier, hole=0.012, depth=0.0018, name='pignon-aac')
for k in range(5):   # allégements du pignon d'arbre à cames (photo p.36)
    a = 2 * math.pi * k / 5 + 0.3
    c = cyl(0.0075, 0.03, (XD, CAM_Y + 0.025 * math.cos(a), CAM_Z + 0.025 * math.sin(a)), (1, 0, 0), None, 16)
    boolean(sp, c)
    apply_all(sp)
    delete(c)
ch.add(sp)
# repères de calage alignés sur l'axe vilebrequin – arbre à cames
ux, uz = (CAM_Y - YC), CAM_Z
nrm = math.hypot(ux, uz)
for (cy, cz, r) in ((YC, 0.0, 0.016), (CAM_Y, CAM_Z, -0.035)):
    ch.add(sphere(0.0018, (XD - 0.004, cy + r * ux / nrm, cz + r * uz / nrm), M('repere', 0xe9e4d4, 0.2, 0.4), 8, 5))
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
ch.add(box((0.012, 0.06, 0.006), (XD, (YC + CAM_Y) / 2, -0.03), M('patin', 0x2a2a2a, 0.0, 0.7), bev=0.002))   # patin de tendeur
ch.add(box((0.008, 0.012, 0.014), (XD, (YC + CAM_Y) / 2, -0.039), acier_noir, bev=0.002))   # porte-patin
ch.add(cyl(0.007, 0.022, (XD + 0.002, (YC + CAM_Y) / 2, -0.052), (0, 0, 1), fonte_usinee, 16))   # cylindre de retenue
ch.add(box((0.006, 0.04, 0.034), (XD + 0.006, YC + 0.035, -0.05), acier_noir, bev=0.002))   # plaque d'appui
ch.add(box((0.02, 0.03, 0.02), (XD + 0.004, YC + 0.035, -0.045), fonte_usinee, bev=0.003))
fasteners(ch, 'vis-tendeur-chaine', [((XD - 0.006, YC + 0.035, -0.045 + s * 0.012), (-1, 0, 0)) for s in (1, -1)], r=0.005, length=0.02, travel=0.04)
fasteners(ch, 'vis-pignon-aac', [((XD - 0.004, CAM_Y + s * 0.012, CAM_Z), (-1, 0, 0)) for s in (1, -1)], r=0.005, length=0.02, travel=0.04)

dist = Part('distribution', (-0.35, 0.1, 0))
dprof = [(-0.09, -0.06), (0.09, -0.06), (0.12, 0.0), (0.128, 0.08), (0.125, 0.15), (0.08, 0.18), (-0.05, 0.17), (-0.085, 0.12), (-0.095, 0.04)]
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
# MR 175 B-86 : corps rond en alu plaqué sur le bout de la culasse (joints montés à sec), roulement
# dans un nez, moyeu à 4 trous où se fixe la poulie, écrou central serré à 4,5 m.daN (poulie montée
# sans clavette, 2 gouttes de Loctite frein filet fort) ; tubulure de sortie verticale (thermostat,
# durite supérieure) et tubulures d'entrée (durite inférieure du radiateur, retour de chauffage).
WX, WY, WZ = XF + 0.03, YD + 0.0375, 0.02   # centré sur la face de la culasse (72 mm de haut)
wp.add(lathe([(0.0, 0.0), (0.036, 0.0), (0.036, 0.007), (0.045, 0.012), (0.045, 0.030), (0.034, 0.036), (0.024, 0.038),
              (0.024, 0.056), (0.0, 0.056)], (XF, WY, WZ), (1, 0, 0), alu, 40, 'corps-pompe'))
for k in range(6):   # nervures de la volute
    a_ = 2 * math.pi * k / 6 + 0.3
    wp.add(box((0.026, 0.004, 0.012), (XF + 0.022, WY + 0.047 * math.cos(a_), WZ + 0.047 * math.sin(a_)), alu, bev=0.001))
wp.add(lathe([(0.008, 0.0), (0.030, 0.0), (0.030, 0.004), (0.012, 0.004), (0.012, 0.010), (0.008, 0.010)], (XF + 0.056, WY, WZ), (1, 0, 0), acier, 32, 'moyeu'))
for k in range(4):   # 4 trous du moyeu
    a_ = math.pi / 4 + k * math.pi / 2
    wp.add(cyl(0.0035, 0.0045, (XF + 0.058, WY + 0.021 * math.cos(a_), WZ + 0.021 * math.sin(a_)), (1, 0, 0), acier_noir, 10))
wp.add(lathe([(0.012, -0.009), (0.06, -0.009), (0.06, -0.006), (0.054, 0.0), (0.06, 0.006), (0.06, 0.009), (0.012, 0.009)], (XF + 0.07, WY, WZ), (1, 0, 0), acier_noir, 40, 'poulie'))
# pattes de fixation autour de la bride
WP_EARS = [(0.027, 0.044), (-0.026, 0.044), (0.027, -0.034), (-0.026, -0.034), (0.0, 0.052)]
for dy, dz in WP_EARS:
    wp.add(cyl(0.0075, 0.009, (XF + 0.0045, WY + dy, WZ + dz), (1, 0, 0), alu, 16))
# tubulure de sortie verticale : siège du thermostat (equipements.py) et coude vers la durite supérieure
WY0 = YD + 0.03   # repère des tubulures (raccords des durites et thermostat, equipements.py)
TH = (XF + 0.03, WZ - 0.04)
wp.add(cyl(0.020, 0.036, (TH[0], WY0 + 0.035, TH[1]), (0, 1, 0), alu, 24, name='colonne-sortie'))
wp.add(cyl(0.024, 0.006, (TH[0], WY0 + 0.050, TH[1]), (0, 1, 0), alu, 28, name='siege-thermostat'))
wp.add(box((0.014, 0.006, 0.070), (TH[0], WY0 + 0.050, TH[1]), alu, bev=0.003))   # pattes des 2 vis du couvercle de thermostat
wp.add(tube([(TH[0], WY0 + 0.055, TH[1]), (TH[0], WY0 + 0.074, TH[1]), (TH[0] + 0.012, WY0 + 0.078, TH[1]), (XF + 0.057, WY0 + 0.078, TH[1])], 0.018, alu, seg=20, res=6))   # s'arrête avant le plan de la courroie
wp.add(torus(0.0185, 0.0018, (XF + 0.053, WY0 + 0.078, TH[1]), (1, 0, 0), alu, 24, 6))   # bourrelet de durite
# tubulures d'entrée : durite inférieure (radiateur) et retour de chauffage
wp.add(tube([(XF + 0.030, WY0 - 0.018, WZ + 0.030), (XF + 0.035, WY0 - 0.030, WZ + 0.060), (XF + 0.035, WY0 - 0.030, WZ + 0.078)], 0.017, alu, seg=18, res=4))   # vers +z : la durite contourne la poulie
wp.add(tube([(XF + 0.012, WY0 - 0.030, WZ + 0.030), (XF + 0.014, WY0 - 0.038, WZ + 0.050)], 0.010, alu, seg=14, res=3))
fasteners(wp, 'vis-pompe-eau', [((XF + 0.010, WY + dy, WZ + dz), (1, 0, 0)) for dy, dz in WP_EARS], r=0.006, length=0.02, travel=0.06)
fastener(wp, 'vis-poulie-pompe', (XF + 0.083, WY, WZ), (1, 0, 0), kind='nut', r=0.009, length=0.012, travel=0.04)

# =====================================================================================
# COLLECTEUR ADMISSION-ÉCHAPPEMENT (planche 9), côté gauche
# =====================================================================================
# sortie de descente déportée vers l'extérieur : le démarreur loge juste dessous
COL_Z = -0.19
YDC = YC + 0.196   # bride de descente : hauteur fixée par le tuyau d'échappement (soubassement.py) et l'écran du démarreur
col = Part('echappement', (0, 0.0, -0.35))
fonte_ech = M('fonte-echappement', 0x4b4845, 0.5, 0.65)
for i in range(4):   # pipes d'échappement vers la descente
    x = X(i)
    col.add(tube([(x, YD + 0.035, ZH_COL - 0.010), (x, YD + 0.03, -0.14), (EX + (x - EX) * 0.35, YDC - 0.02, -0.17), (EX + 0.02, YDC - 0.08, COL_Z)], 0.016, fonte_ech, seg=12, res=6))
col.add(cyl(0.024, 0.06, (EX + 0.02, YDC - 0.10, COL_Z), (0, 1, 0), fonte_ech, 24))
col.add(cyl(0.035, 0.008, (EX + 0.02, YDC - 0.13, COL_Z), (0, 1, 0), fonte_ech, 24))   # bride de descente
col.add(tube([(EX - 0.08, YD + 0.06, ZH_COL - 0.010), (EX - 0.05, YD + 0.085, -0.16), (EX, YD + 0.09, -0.175), (EX + 0.05, YD + 0.085, -0.16), (EX + 0.08, YD + 0.06, ZH_COL - 0.010)], 0.017, alu, seg=12, res=8))
col.add(cyl(0.03, 0.03, (EX, YD + 0.095, -0.175), (0, 1, 0), alu, 28))   # pipe d'admission sous le carburateur
col.add(box((0.16, 0.004, 0.07), (EX + 0.02, YD - 0.035, -0.205), M('tole-alu', 0xc7cccf, 0.8, 0.35), bev=0.001))   # tôle pare-chaleur
col.add(box((XF - XR - 0.04, 0.07, 0.004), (EX, YD + 0.045, ZH_COL - 0.0125), joint))   # joint de collecteur
ec = [((x, YD + y, ZH_COL - 0.021), (0, 0, -1)) for x, y in ((EX + 0.16, 0.05), (EX + 0.08, 0.025), (EX, 0.05), (EX - 0.08, 0.025), (EX - 0.16, 0.05), (EX, 0.015))]
fasteners(col, 'ecrous-collecteur', ec, kind='nut', r=0.007, length=0.03, travel=0.05)

# =====================================================================================
# CARBURATEUR ZENITH 28 IF (V 050 78 sur moteur 688 D7 12) — vue éclatée 3 bis et coupe (RTA p.28)
# Simple corps inversé, papillon Ø 28, diffuseur 20, volet de départ à froid, enrichisseur de pointe.
# Trois ensembles qui s'écartent à l'éclaté : corps-cuve (8) avec papillon et vis A / B,
# flotteur (5) et sa barrette (4), couvercle assemblé (2) avec cornet, volet, pointeau (3) et
# raccord d'arrivée à filtre (1). Gicleur principal (9) sous bouchon en bas de cuve, gicleur de
# ralenti (6) sous le couvercle, vis de richesse (10) à capuchon, vis butée de papillon (11),
# joints de cuve (7) et de bride (12). Cotes d'encombrement estimées d'après les dessins.
# =====================================================================================
zamak = M('zamak', 0xbcb6a3, 0.6, 0.4)
zamak_c = M('zamak-couvercle', 0xc6c1ae, 0.6, 0.38)
laiton_c = M('laiton', 0xb59a52, 0.9, 0.35)
CY = YD + 0.11                 # dessus de la pipe d'admission (plan de bride)
CZ = -0.175                    # axe du corps, côté gauche (côté collecteur)
BOWL_X = EX + 0.044            # cuve à niveau constant vers l'avant, accolée au fût
YJ = CY + 0.0565               # plan de joint corps / couvercle
YT = CY + 0.0645               # dessus du couvercle
HT = CY + 0.098                # haut du cornet d'air
STUDS = [(EX + 0.028, CZ + 0.025), (EX - 0.028, CZ - 0.025)]


def hull2d(pts):
    pts = sorted(set(pts))

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ring_pts(cx, cz, r, n=20):
    # (u, v) du plan local d'une extrusion d'axe +y : u = x, v = -z
    return [(cx - EX + r * math.cos(2 * math.pi * k / n), -(cz - CZ) + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rect_pts(cx, cz, wx, wz, r=0.006, n=5):
    pts = []
    for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        pts += ring_pts(cx + sx * (wx / 2 - r), cz + sz * (wz / 2 - r), r, 4 * n)
    return pts


# contour commun corps / joint / couvercle : fût + cuve
TOP_OUTLINE = hull2d(ring_pts(EX, CZ, 0.0265) + rect_pts(BOWL_X, CZ, 0.050, 0.056))
FLANGE_OUTLINE = hull2d(ring_pts(EX, CZ, 0.027) + ring_pts(*STUDS[0], 0.011) + ring_pts(*STUDS[1], 0.011))

# ---------------------------------------------------------------- corps-cuve (8)
carb = Part('carburateur', (0, 0.35, -0.35))
carb.add(extrude(FLANGE_OUTLINE, 0.0015, (EX, CY + 0.00075, CZ), (0, 1, 0), joint, 'joint-bride'))       # (12)
flange = extrude(FLANGE_OUTLINE, 0.008, (EX, CY + 0.0055, CZ), (0, 1, 0), zamak, 'bride', bev=0.001)
for sx, sz in STUDS + [(EX, CZ)]:
    c = cyl(0.014 if (sx, sz) == (EX, CZ) else 0.0045, 0.03, (sx, CY + 0.0055, sz), (0, 1, 0), None, 24)
    boolean(flange, c)
    apply_all(flange)
    delete(c)
carb.add(flange)
# fût : alésage Ø 28 traversant, papillon visible par le haut une fois le couvercle déposé
carb.add(lathe([(0.014, 0.0), (0.0235, 0.0), (0.0235, YJ - CY - 0.0095), (0.014, YJ - CY - 0.0095)], (EX, CY + 0.0095, CZ), (0, 1, 0), zamak, 40, 'fut'))
# cuve ouverte en haut (flotteur dedans)
bowl = box((0.050, YJ - CY - 0.011, 0.056), (BOWL_X, (YJ + CY + 0.011) / 2, CZ), zamak, bev=0.005, name='cuve')
cav = box((0.038, 0.05, 0.046), (BOWL_X + 0.002, YJ + 0.004, CZ), None)
boolean(bowl, cav)
apply_all(bowl)
delete(cav)
carb.add(bowl)
# diffuseur Ø 20 (buse) dans le fût, tube émulseur et puits de gicleur côté cuve
carb.add(lathe([(0.010, 0.0), (0.014, -0.004), (0.014, 0.020), (0.0115, 0.016), (0.010, 0.010)], (EX, CY + 0.030, CZ), (0, 1, 0), zamak, 32, 'diffuseur'))
carb.add(cyl(0.004, 0.034, (BOWL_X - 0.019, CY + 0.034, CZ), (0, 1, 0), laiton_c, 12, name='tube-emulseur'))   # (coupe, 9)
carb.add(tube([(BOWL_X - 0.019, CY + 0.046, CZ), (EX + 0.009, CY + 0.046, CZ)], 0.0018, laiton_c, 'bec-principal', seg=6))
# axe et papillon des gaz (1), fermé (incliné de 10°)
carb.add(cyl(0.0028, 0.078, (EX, CY + 0.018, CZ - 0.004), (0, 0, 1), acier, 12, name='axe-papillon'))
for sz in (1, -1):
    carb.add(cyl(0.0065, 0.010, (EX, CY + 0.018, CZ + sz * 0.026), (0, 0, 1), zamak, 16, name='bossage-axe'))
carb.add(cyl(0.0137, 0.0012, (EX, CY + 0.018, CZ), (math.sin(math.radians(10)), math.cos(math.radians(10)), 0), laiton_c, 32, name='papillon'))
for dx in (-0.005, 0.005):
    carb.add(cyl(0.0014, 0.003, (EX + dx, CY + 0.0188, CZ), (0, 1, 0), acier, 8, name='vis-papillon'))
# levier d'accélérateur (secteur) côté extérieur, ressort de rappel, butée de la vis A
lev = hull2d([(0.009 * math.cos(a), 0.009 * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]] +
             [(-0.032 + 0.006 * math.cos(a), 0.014 + 0.006 * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]] +
             [(-0.010, -0.012), (-0.020, -0.010)])
carb.add(extrude(lev, 0.003, (EX, CY + 0.018, CZ - 0.040), (0, 0, 1), acier, 'levier-accelerateur'))
carb.add(cyl(0.0035, 0.008, (EX - 0.032, CY + 0.032, CZ - 0.043), (0, 0, 1), acier, 10, name='rotule-cable'))
spring = [(EX - 0.010 + 0.026 * i / 40, CY + 0.007 + 0.003 * math.cos(2 * math.pi * 6 * i / 40), CZ - 0.046 + 0.003 * math.sin(2 * math.pi * 6 * i / 40)) for i in range(41)]
carb.add(tube(spring, 0.0007, M('ressort', 0x6d7d8a, 0.8, 0.35), 'ressort-rappel', seg=4, res=2))
carb.add(box((0.004, 0.010, 0.022), (EX + 0.018, CY + 0.007, CZ - 0.036), acier, name='patte-ressort'))   # accroche sur la bride
carb.add(box((0.008, 0.006, 0.010), (EX - 0.016, CY + 0.012, CZ - 0.040), zamak, bev=0.001, name='butee-vis-a'))
# câble d'accélérateur : gaine arrêtée sur une patte, vers la pédale par le tablier
carb.add(box((0.004, 0.022, 0.016), (EX - 0.052, CY + 0.026, CZ - 0.046), acier_noir, bev=0.001, name='patte-gaine'))
carb.add(tube([(EX - 0.032, CY + 0.032, CZ - 0.046), (EX - 0.052, CY + 0.032, CZ - 0.046)], 0.0009, acier, 'cable-nu', seg=6))
carb.add(tube([(EX - 0.054, CY + 0.032, CZ - 0.046), (EX - 0.09, CY + 0.05, CZ - 0.07), (0.80, 0.80, -0.32), (0.72, 0.82, -0.40)], 0.0025, noir, 'gaine-accelerateur', seg=6, res=10))
# vis de richesse (10) : bossage et capuchon d'inviolabilité ; prise de dépression d'avance
carb.add(cyl(0.0065, 0.012, (EX - 0.027, CY + 0.014, CZ + 0.012), (1, 0, 0), zamak, 16, name='bossage-richesse'))
carb.add(cyl(0.0028, 0.014, (EX - 0.004, CY + 0.026, CZ + 0.030), (0, 0, 1), laiton_c, 10, name='prise-depression'))
carb.add(tube([(EX - 0.004, CY + 0.026, CZ + 0.036), (EX - 0.01, CY + 0.06, CZ + 0.07), (0.87, YH + 0.075, -0.02), (0.85, YH + 0.06, 0.07), (0.835, CAM_Y + 0.17, 0.096)], 0.0028, caoutchouc, 'tuyau-depression', seg=6, res=10))
# bouchon de gicleur principal (9) en bas de cuve ; gicleur de ralenti (6) sous le couvercle
fastener(carb, 'gicleur-principal-carbu', (BOWL_X + 0.025, CY + 0.019, CZ + 0.006), (1, 0, 0), kind='plug', r=0.0055, length=0.012, travel=0.04)
fastener(carb, 'gicleur-ralenti-carbu', (EX + 0.021, YJ - 0.0005, CZ + 0.022), (0, 1, 0), kind='screw', r=0.0028, length=0.016, travel=0.035)
# vis A (butée de papillon, volume) puis B (richesse), comme sur la photo de réglage p.28
fasteners(carb, 'vis-ralenti', [((EX - 0.016, CY + 0.031, CZ - 0.040), (0, 1, 0)), ((EX - 0.034, CY + 0.014, CZ + 0.012), (-1, 0, 0.2))], kind='screw', r=0.0038, length=0.018, travel=0.014)
fasteners(carb, 'ecrous-carbu', [((sx, CY + 0.0105, sz), (0, 1, 0)) for sx, sz in STUDS], kind='nut', r=0.006, length=0.02, travel=0.04)

# ---------------------------------------------------------------- flotteur (5) et barrette (4)
fl = Part('carbu-flotteur', (0, 0.52, -0.35))
fl.add(box((0.026, 0.020, 0.036), (BOWL_X + 0.008, CY + 0.030, CZ), M('flotteur', 0x2d2a26, 0.0, 0.5), bev=0.006, name='flotteur'))
fl.add(box((0.020, 0.0015, 0.010), (BOWL_X - 0.006, CY + 0.041, CZ), laiton_c, name='bras-flotteur'))
fl.add(tube([(BOWL_X - 0.010, CY + 0.041, CZ), (BOWL_X - 0.010, CY + 0.046, CZ)], 0.0012, laiton_c, 'languette', seg=6))
fl.add(box((0.006, 0.012, 0.024), (BOWL_X - 0.015, CY + 0.051, CZ), acier, bev=0.001, name='barrette'))   # (4)
fl.add(cyl(0.0012, 0.030, (BOWL_X - 0.015, CY + 0.051, CZ), (0, 0, 1), acier, 8, name='axe-flotteur'))

# ---------------------------------------------------------------- couvercle assemblé (2)
cv = Part('carbu-couvercle', (0, 0.68, -0.35))
cv.add(extrude(TOP_OUTLINE, 0.0012, (EX, YJ + 0.0006, CZ), (0, 1, 0), joint, 'joint-cuve'))          # (7)
plate = extrude(TOP_OUTLINE, YT - YJ - 0.0012, (EX, (YT + YJ + 0.0012) / 2, CZ), (0, 1, 0), zamak_c, 'couvercle', bev=0.0015)
c = cyl(0.0195, 0.03, (EX, YT, CZ), (0, 1, 0), None, 32)
boolean(plate, c)
apply_all(plate)
delete(c)
cv.add(plate)
cv.add(lathe([(0.0195, 0.0), (0.023, 0.0), (0.023, HT - YT - 0.003), (0.0245, HT - YT - 0.002), (0.0245, HT - YT), (0.0195, HT - YT)], (EX, YT, CZ), (0, 1, 0), zamak_c, 40, 'cornet'))
# volet de départ (2 de la coupe), monté excentré sur son axe : représenté ouvert (moteur chaud)
cv.add(cyl(0.0022, 0.056, (EX - 0.004, CY + 0.083, CZ), (0, 0, 1), acier, 10, name='axe-volet'))
cv.add(cyl(0.0185, 0.0009, (EX - 0.002, CY + 0.083, CZ), (math.cos(math.radians(20)), math.sin(math.radians(20)), 0), laiton_c, 28, name='volet-depart'))
# levier de volet, serre-câble, patte de gaine et câble de starter (tirette au tableau de bord)
vl = hull2d([(0.007 * math.cos(a), 0.007 * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]] +
            [(0.020 + 0.005 * math.cos(a), -0.012 + 0.005 * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]])
cv.add(extrude(vl, 0.0025, (EX - 0.004, CY + 0.083, CZ - 0.030), (0, 0, 1), acier, 'levier-volet'))
cv.add(cyl(0.0035, 0.007, (EX + 0.016, CY + 0.071, CZ - 0.033), (0, 0, 1), laiton_c, 10, name='serre-cable'))
cv.add(box((0.020, 0.004, 0.014), (EX + 0.034, CY + 0.071, CZ - 0.032), acier, bev=0.001, name='patte-gaine-starter'))
cv.add(tube([(EX + 0.044, CY + 0.071, CZ - 0.032), (EX + 0.07, CY + 0.08, CZ - 0.06), (1.00, 0.82, -0.25), (0.86, 0.84, -0.33), (0.72, 0.83, -0.37)], 0.0022, noir, 'cable-starter', seg=6, res=10))
# tringle d'ouverture positive : levier de volet → levier de papillon
cv.add(tube([(EX + 0.008, CY + 0.076, CZ - 0.033), (EX + 0.006, CY + 0.050, CZ - 0.040), (EX + 0.004, CY + 0.024, CZ - 0.044)], 0.0011, acier, 'tringle-ouverture-positive', seg=6))
# enrichisseur de pointe : tube calibré débouchant dans le cornet
cv.add(tube([(EX + 0.017, YT, CZ), (EX + 0.017, YT + 0.016, CZ), (EX + 0.010, YT + 0.022, CZ)], 0.0016, laiton_c, 'enrichisseur', seg=6))
# raccord d'arrivée d'essence avec filtre (1), au-dessus de la cuve, tourné vers la pompe (droite)
cv.add(cyl(0.0065, 0.010, (BOWL_X + 0.006, YT + 0.005, CZ + 0.012), (0, 1, 0), zamak_c, 16, name='bossage-arrivee'))
cv.add(extrude(hexagon(0.0065), 0.006, (BOWL_X + 0.006, YT + 0.006, CZ + 0.022), (0, 0, 1), laiton_c, 'raccord-arrivee'))
cv.add(cyl(0.0032, 0.024, (BOWL_X + 0.006, YT + 0.006, CZ + 0.036), (0, 0, 1), laiton_c, 12, name='embout-arrivee'))
# pointeau (3) vissé sous le couvercle, au-dessus de la languette du flotteur
cv.add(extrude(hexagon(0.0045), 0.008, (BOWL_X - 0.008, YJ - 0.004, CZ + 0.008), (0, 1, 0), laiton_c, 'pointeau'))
cv.add(tube([(BOWL_X - 0.008, YJ - 0.008, CZ + 0.008), (BOWL_X - 0.010, YJ - 0.0105, CZ)], 0.0010, acier, 'aiguille-pointeau', seg=6))
cv.add(box((0.004, 0.008, 0.030), (BOWL_X - 0.015, YJ - 0.004, CZ), zamak_c, name='chape-flotteur'))
# 5 vis de couvercle sur bossages
VC = [(EX - 0.017, CZ - 0.021), (EX - 0.017, CZ + 0.021), (EX + 0.024, CZ - 0.026), (BOWL_X + 0.020, CZ - 0.022), (BOWL_X + 0.020, CZ + 0.022)]
for vx, vz in VC:
    cv.add(cyl(0.0055, 0.006, (vx, YT + 0.003, vz), (0, 1, 0), zamak_c, 16, name='bossage-vis'))
fasteners(cv, 'vis-couvercle-carbu', [((vx, YT + 0.006, vz), (0, 1, 0)) for vx, vz in VC], kind='screw', r=0.0035, length=0.018, travel=0.03)

# ---------------------------------------------------------------- filtre à air rond, sur le cornet
af = Part('filtre-air', (0, 0.7, -0.15))
AY = HT - 0.008
af.add(lathe([(0.0235, -0.012), (0.027, -0.012), (0.027, 0.0), (0.13, 0.0), (0.142, 0.006), (0.145, 0.02), (0.142, 0.034), (0.13, 0.04), (0.0235, 0.04)], (EX, AY, CZ), (0, 1, 0), noir, 48))
af.add(torus(0.0275, 0.0018, (EX, AY - 0.006, CZ), (0, 1, 0), acier, 32, 6, 'collier-cornet'))
af.add(lathe([(0.0, 0.058), (0.10, 0.055), (0.135, 0.046), (0.146, 0.036), (0.146, 0.03), (0.0, 0.03)], (EX, AY, CZ), (0, 1, 0), noir, 48))   # couvercle
for k in range(16):
    a = 2 * math.pi * k / 16
    af.add(box((0.05, 0.004, 0.006), (EX + 0.085 * math.cos(a), AY + 0.059, CZ + 0.085 * math.sin(a)), noir, bev=0.0015))
af.add(lathe([(0.11, 0.0), (0.13, 0.0), (0.13, 0.036), (0.11, 0.036)], (EX, AY + 0.002, CZ), (0, 1, 0), M('papier', 0xd9cf9e, 0.0, 0.9), 48))   # élément filtrant
af.add(tube([(EX + 0.13, AY + 0.02, -0.21), (EX + 0.22, AY + 0.015, -0.30), (1.30, AY - 0.02, -0.40)], 0.035, noir, seg=14, res=8))   # prise d'air
fastener(af, 'ecrou-filtre-air', (EX, AY + 0.062, CZ), (0, 1, 0), kind='nut', r=0.013, length=0.03, travel=0.06, washer=False)

# =====================================================================================
# ALLUMAGE : allumeur, bougies, fils
# =====================================================================================
dl = Part('allumeur', (0, 0.5, 0.25))
DX, DZ = EX, CAM_Z + 0.032
DY0 = CAM_Y + 0.095
dl.add(cyl(0.022, 0.07, (DX, DY0 + 0.035, DZ), (0, 1, 0), alu, 24))
dl.add(cyl(0.036, 0.025, (DX, DY0 + 0.08, DZ), (0, 1, 0), alu, 32))
dl.add(lathe([(0.0, 0.05), (0.02, 0.05), (0.03, 0.04), (0.038, 0.02), (0.04, 0.0), (0.0, 0.0)], (DX, DY0 + 0.092, DZ), (0, 1, 0), bakelite, 32))   # tête
for k in range(4):
    a = 2 * math.pi * k / 4 + math.pi / 4
    dl.add(cyl(0.007, 0.02, (DX + 0.02 * math.cos(a), DY0 + 0.145, DZ + 0.02 * math.sin(a)), (0, 1, 0), bakelite, 14))
dl.add(cyl(0.007, 0.02, (DX, DY0 + 0.15, DZ), (0, 1, 0), bakelite, 14))
dl.add(cyl(0.02, 0.03, (DX, DY0 + 0.075, DZ + 0.048), (0, 0, 1), alu, 24))   # capsule à dépression (vers l'extérieur)
dl.add(box((0.05, 0.006, 0.03), (DX, DY0 + 0.004, DZ + 0.02), acier_noir, bev=0.002))   # bride
fastener(dl, 'fix-allumeur', (DX, DY0 + 0.007, DZ + 0.03), (0, 1, 0), r=0.006, length=0.02, travel=0.04)

bg = Part('bougies', (0, 0.25, -0.4))
plug_specs = []
for i in range(4):
    p = (X(i), YD + 0.04, ZH_CAM + 0.004)
    plug_specs.append((p, (0, 0.45, 1)))
fasteners(bg, 'bougies', plug_specs, kind='spark', r=0.0105, length=0.07, travel=0.10)
# fils d'allumage : tête d'allumeur → bougies, courts, tout du côté droit
ign = Part('allumeur', (0, 0.5, 0.25))
order_cap = [0, 2, 3, 1]
for k, i in enumerate(order_cap):
    a = 2 * math.pi * k / 4 + math.pi / 4
    start = (DX + 0.02 * math.cos(a), DY0 + 0.155, DZ + 0.02 * math.sin(a))
    if i == 0:   # n° 1 sous l'alternateur : le fil part vers le bas puis revient vers l'allumeur
        end = (X(i), YD + 0.067, 0.146)
        path = [start, (start[0], DY0 + 0.18, start[2]), ((start[0] + 0.99) / 2, YD + 0.14, 0.15), (0.98, YD + 0.09, 0.17), (0.985, YD + 0.035, 0.16), (X(i) - 0.005, YD + 0.040, 0.152), end]
    else:
        end = (X(i), YD + 0.081, 0.175)   # capuchon dans l'axe de la bougie
        path = [start, (start[0], DY0 + 0.18, start[2]), ((start[0] + end[0]) / 2, YD + 0.14, 0.125), (end[0], YD + 0.105, 0.19), end]
    ign.add(tube(path, 0.0045, fil_rouge, seg=8, res=6))

# =====================================================================================
# POMPE À ESSENCE (mécanique, côté droit) et FILTRE À HUILE
# =====================================================================================
pe = Part('pompe-essence', (0, 0, 0.4))
pe.add(box((0.05, 0.04, 0.018), (EX + 0.06, CAM_Y - 0.02, 0.105), alu, bev=0.004))
pe.add(cyl(0.035, 0.03, (EX + 0.06, CAM_Y - 0.02, 0.130), (0, 0, 1), alu, 32))
pe.add(cyl(0.038, 0.006, (EX + 0.06, CAM_Y - 0.02, 0.130), (0, 0, 1), acier, 32))
pe.add(cyl(0.025, 0.012, (EX + 0.06, CAM_Y - 0.02, 0.151), (0, 0, 1), acier, 28))
for s in (1, -1):
    pe.add(cyl(0.004, 0.02, (EX + 0.06 + s * 0.02, CAM_Y + 0.01, 0.135), (0, 1, 0), alu, 10))
pe.add(tube([(EX + 0.06, CAM_Y + 0.02, 0.135), (EX + 0.08, YD - 0.02, 0.115), (EX + 0.08, YD + 0.10, 0.105), (EX + 0.08, YH + 0.09, 0.04), (EX + 0.08, YH + 0.10, -0.03), (EX + 0.06, YH + 0.08, -0.10), (EX + 0.05, CY + 0.075, -0.12), (EX + 0.05, CY + 0.0705, CZ + 0.05)], 0.0035, caoutchouc, seg=6))
pe.add(tube([(EX + 0.02, CAM_Y + 0.02, 0.135), (EX + 0.015, CAM_Y + 0.03, 0.20), (EX - 0.005, 0.552, 0.24), (EX - 0.015, 0.555, 0.25)], 0.0035, caoutchouc, seg=6))   # arrivée du filtre à essence (soubassement.py)
fasteners(pe, 'fix-pompe-essence', [((EX + 0.06 + s * 0.02, CAM_Y - 0.02, 0.114), (0, 0, 1)) for s in (1, -1)], kind='nut', r=0.006, length=0.02, travel=0.04)

fh = Part('filtre-huile', (0, -0.05, 0.45))
filt = lathe([(0.0, 0.0), (0.04, 0.0), (0.046, 0.006), (0.046, 0.09), (0.042, 0.098), (0.0, 0.1)], (0, 0, 0), (0, 1, 0), bleu, 40)
filt = join([filt, lathe([(0.03, -0.004), (0.036, -0.004), (0.036, 0.001), (0.03, 0.001)], (0, 0, 0), (0, 1, 0), caoutchouc, 32)], 'fx.filtre-huile-cartouche.0')
place(filt, (EX - 0.075, YC + 0.052, 0.135), axis=(0, 0, 1))
filt['fx'] = 'filtre-huile-cartouche'
filt['kind'] = 'filter'
filt['travel'] = 0.12
filt['dir'] = [0, 0, 1]
fh.fasteners.append(filt)

jg = Part('jauge', (0, 0.45, 0.1))
# tube de jauge derrière la bougie n° 4, au-dessus du filtre à huile
jg.add(tube([(EX - 0.15, YC + 0.09, 0.104), (EX - 0.15, YD - 0.02, 0.125), (EX - 0.15, YH + 0.06, 0.15), (EX - 0.15, YH + 0.11, 0.155)], 0.0045, acier_noir, seg=6))
jg.add(torus(0.014, 0.004, (EX - 0.15, YH + 0.128, 0.155), (0, 0, 1), M('jaune', 0xd2ae35, 0.1, 0.5), 20, 8))

export(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'moteur.glb'))
