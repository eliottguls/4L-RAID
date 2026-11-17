# Équipement électrique et chauffage de la Renault 4 GTL : faisceaux avant (A) et arrière (B),
# avertisseur, centrale clignotante, plafonnier, ampoules, contacteurs, masses, appareil de
# chauffage-ventilation. Lancer : python3 tools/blender/electricite.py → models/electricite.glb
#
# RTA : légende du schéma électrique depuis les modèles 1979 (p.76) : avertisseur sonore droit (10),
# masses gauche et droite (13, 14), mano-contact de pression d'huile (21), thermo-contacts sur radiateur
# (22) et sur culasse (23), maître-cylindre et contacteur stop (27, 52), moto-ventilateur de chauffage
# (28), platine de servitude (44), plafonnier (62), rhéostat de jauge (65), lunette arrière dégivrante
# (66), feux arrière (68, 69), éclaireur de plaque (70), contacteur de feux de recul (72), centrale
# clignotante (74), bloc raccord câblage avant / arrière (81) ; répertoire des câblages A avant,
# B arrière, K lancement, M essuie-glace (p.76) ; tableau des lampes (p.71) : projecteurs P 45 t 41
# 45/40 W, position AV R 19 5 W, AR P 25-2 21/5 W, clignotants P 25-1 21 W, plafonnier navette 10 × 39 ;
# appareil de chauffage-ventilation (« climatiseur ») derrière la planche de bord (p.75), moto-
# ventilateur à deux vitesses depuis 1981 (p.85). Cheminement des fils et formes estimés.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, Part, box, cyl, export, extrude, fastener, fasteners, lathe, reset, rounded_rect, sphere, torus, tube  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'electricite.glb')

TABLIER_X = 0.700
GX = 1.766                     # face de la calandre (caisse.py)
HL = (GX + 0.022, 0.671)       # projecteurs Ø 168
EX = 0.92                      # milieu du bloc moteur (moteur.py)

gaine = M('gaine-faisceau', 0x1f2021, 0.0, 0.75)
nylon = M('connecteur', 0xe6e1d2, 0.0, 0.45)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
cuivre = M('cuivre', 0xb87333, 0.9, 0.3)
laiton = M('laiton', 0xb59a52, 0.9, 0.35)
tresse = M('tresse-masse', 0xa9a196, 0.9, 0.5)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
verre = M('verre-ampoule', 0xf2f0e8, 0.2, 0.05, alpha=0.45)
filament = M('filament', 0xffd27a, 0.6, 0.3)
culot = M('culot', 0xc9c4ae, 0.9, 0.3)
plastique_gris = M('plastique-gris', 0x6a6d6f, 0.0, 0.7)
plastique_cl = M('plastique-clair', 0xbdb8ad, 0.0, 0.6)
diffuseur = M('diffuseur', 0xf4f1e4, 0.1, 0.2, alpha=0.7)
fils = [M('fil-' + n, c, 0.1, 0.55) for n, c in (('rouge', 0x8a2a22), ('jaune', 0xc9a227), ('bleu', 0x2c5ea8), ('vert', 0x3f7a45),
                                                  ('blanc', 0xd8d4c8), ('marron', 0x5b3b25), ('violet', 0x5b3f78), ('gris', 0x8b8d8f))]


def harness(part, pts, r=0.0065, clips=0):
    """Faisceau gainé ; `clips` agrafes réparties le long du tracé."""
    part.add(tube(pts, r, gaine, 'faisceau', seg=8, res=10))
    for k in range(clips):
        i = min(len(pts) - 1, 1 + k * (len(pts) - 1) // max(1, clips))
        part.add(box((0.012, 0.012, 0.022), pts[i], acier_noir, 0.002, 'agrafe'))


def branch(part, pts, n_wires=2, conn=None, conn_axis=(1, 0, 0)):
    """Dérivation : quelques fils de couleur (code RTA) vers un connecteur."""
    for k in range(n_wires):
        off = (k - (n_wires - 1) / 2) * 0.004
        part.add(tube([(p[0], p[1] + off, p[2] + off) for p in pts], 0.0016, fils[(len(part.objs) + k) % len(fils)], 'fil', seg=6, res=6))
    if conn:
        part.add(box(conn, pts[-1], nylon, 0.002, 'connecteur', axis=conn_axis))


# =====================================================================================
# FAISCEAU AVANT (A) et câble de lancement (K) : boîte à fusibles → projecteurs, feux, avertisseur,
# moto-ventilateur, thermo-contacts, alternateur et régulateur, démarreur, bobine, stop, recul
# =====================================================================================
fa = Part('faisceau-avant', (0.15, 0.25, 0))
F0 = (TABLIER_X + 0.03, 0.80, -0.20)                      # sortie de la platine de servitude
L_ = [F0, (0.76, 0.87, -0.32), (0.86, 0.86, -0.50), (1.20, 0.83, -0.53), (1.55, 0.81, -0.53), (1.70, 0.80, -0.46), (1.725, 0.80, -0.20)]
R_ = [(1.725, 0.80, -0.20), (1.725, 0.80, 0.20), (1.70, 0.80, 0.46), (1.55, 0.81, 0.53), (1.20, 0.83, 0.53), (0.86, 0.86, 0.50), (0.76, 0.87, 0.30), (0.74, 0.86, 0.05), F0]
harness(fa, L_, 0.0075, 4)
harness(fa, R_, 0.0075, 5)
for s in (1, -1):
    z = lambda v: s * v  # noqa: E731
    branch(fa, [(1.70, 0.80, z(0.44)), (1.68, 0.76, z(0.43)), (HL[0] - 0.13, HL[1], z(0.417))], 3, (0.03, 0.025, 0.025))         # projecteurs
    branch(fa, [(1.72, 0.80, z(0.48)), (1.745, 0.62, z(0.49)), (GX - 0.02, 0.505, z(0.485))], 2, (0.02, 0.02, 0.02))            # feux AV
    fa.add(box((0.025, 0.004, 0.015), (1.72, 0.76, z(0.555)), tresse, 0.001, 'masse-' + ('droite' if s > 0 else 'gauche')))
branch(fa, [(1.70, 0.80, 0.38), (1.73, 0.62, 0.32), (1.73, 0.50, 0.30)], 2, (0.018, 0.02, 0.012))                 # avertisseur droit
branch(fa, [(1.725, 0.80, 0.08), (1.66, 0.72, 0.06), (1.64, 0.66, 0.05)], 2, (0.02, 0.02, 0.02))                  # moto-ventilateur
branch(fa, [(1.725, 0.80, 0.22), (1.72, 0.60, 0.21), (1.70, 0.505, 0.20)], 1, (0.015, 0.015, 0.015))             # thermo-contact radiateur
branch(fa, [(1.05, 0.83, 0.53), (1.03, 0.76, 0.36), (1.005, 0.70, 0.26)], 3, (0.02, 0.015, 0.025), (0, 1, 0))    # régulateur / alternateur
branch(fa, [(1.12, 0.83, -0.53), (1.07, 0.66, -0.32), (1.03, 0.52, -0.20), (1.016, 0.472, -0.158)], 1, (0.012, 0.012, 0.008))   # démarreur (cosse du solénoïde, côté gauche)
branch(fa, [(0.76, 0.87, 0.28), (0.76, 0.84, 0.22), (0.75, 0.82, 0.20)], 2, (0.015, 0.015, 0.015))               # bobine
branch(fa, [(0.74, 0.86, 0.04), (0.74, 0.74, 0.04), (0.735, 0.66, 0.04)], 1, (0.012, 0.012, 0.012))              # thermo-contact culasse (23)
branch(fa, [(0.86, 0.86, -0.50), (0.84, 0.70, -0.32), (0.83, 0.52, -0.19), (EX - 0.10, 0.468, -0.143)], 1, (0.012, 0.012, 0.008))   # mano-contact (21), côté gauche
branch(fa, [(0.86, 0.86, -0.48), (0.86, 0.84, -0.45), (TABLIER_X + 0.15, 0.82, -0.43)], 2, (0.012, 0.012, 0.012))  # contacteur stop (52)
branch(fa, [(1.20, 0.83, -0.53), (1.36, 0.66, -0.20), (1.40, 0.56, -0.10)], 2, (0.015, 0.012, 0.012))             # feux de recul (72)
fa.add(cyl(0.022, 0.012, (TABLIER_X + 0.006, 0.86, -0.30), (1, 0, 0), caoutchouc, 20, name='passe-fil'))
harness(fa, [(TABLIER_X + 0.01, 0.86, -0.30), (0.66, 0.84, -0.28), (0.60, 0.83, -0.25)], 0.0085)                  # vers le tableau de bord
# mano-contact de pression d'huile (21) : sur le flanc GAUCHE du carter-cylindres (RTA p.23,
# « déposer le manocontact (côté gauche du carter-cylindres) ») ; il est modélisé avec le bloc (moteur.py)
# tresse de masse moteur → caisse
fa.add(tube([(1.10, 0.36, -0.20), (1.12, 0.38, -0.30), (1.15, 0.40, -0.38)], 0.004, tresse, 'tresse-masse', seg=6))
fastener(fa, 'tresse-masse', (1.15, 0.40, -0.385), (0, 0, -1), r=0.006, length=0.02, travel=0.03)

# =====================================================================================
# FAISCEAU ARRIÈRE (B) : bloc raccord (81) sous la planche, long du bas de caisse gauche, feux
# arrière, éclaireur de plaque, rhéostat de jauge, lunette arrière dégivrante, plafonnier
# =====================================================================================
fb = Part('faisceau-arriere', (0, 0.15, -0.25))
fb.add(box((0.04, 0.03, 0.025), (0.56, 0.78, -0.56), nylon, 0.003, 'bloc-raccord'))
B_ = [(0.56, 0.78, -0.56), (0.54, 0.60, -0.62), (0.45, 0.40, -0.625), (0.0, 0.392, -0.625), (-0.55, 0.392, -0.625),
      (-0.80, 0.50, -0.60), (-1.30, 0.52, -0.58), (-1.70, 0.62, -0.56), (-1.765, 0.70, -0.40), (-1.765, 0.70, 0.40), (-1.70, 0.62, 0.56)]
harness(fb, B_, 0.0055, 6)
for s in (1, -1):
    branch(fb, [(-1.70, 0.62, s * 0.56), (-1.76, 0.72, s * 0.62), (-1.77, 0.80, s * 0.635)], 3, (0.02, 0.025, 0.02))   # feux AR (68, 69)
branch(fb, [(-1.765, 0.70, 0.0), (-1.80, 0.62, 0.0)], 2, (0.02, 0.012, 0.03))                                        # éclaireur de plaque (70)
branch(fb, [(-0.80, 0.50, -0.60), (-0.90, 0.47, -0.30), (-0.92, 0.45, 0.06), (-0.92, 0.45, 0.10)], 2, (0.012, 0.012, 0.012))   # jauge (65)
branch(fb, [(-1.70, 0.62, -0.56), (-1.66, 0.95, -0.60), (-1.62, 1.12, -0.56)], 2, (0.012, 0.012, 0.02))             # lunette dégivrante (66)
harness(fb, [(0.54, 0.80, -0.60), (0.52, 1.10, -0.64), (0.40, 1.47, -0.58), (0.0, 1.49, -0.20), (-0.04, 1.49, -0.03)], 0.004)   # vers le plafonnier
fb.add(cyl(0.012, 0.008, (-0.90, 0.47, -0.30), (0, 1, 0), caoutchouc, 16, name='passe-fil'))

# =====================================================================================
# AVERTISSEUR (10), CENTRALE CLIGNOTANTE (74), PLAFONNIER (62)
# =====================================================================================
av = Part('avertisseur', (0.3, 0, 0.15))
AVP = (1.73, 0.47, 0.30)
av.add(lathe([(0.0, -0.012), (0.045, -0.012), (0.048, -0.004), (0.045, 0.006), (0.030, 0.012), (0.0, 0.012)], AVP, (1, 0, 0), noir, 36, 'avertisseur'))
av.add(lathe([(0.0, 0.0), (0.020, 0.0), (0.024, 0.004), (0.0, 0.006)], (AVP[0] + 0.012, AVP[1], AVP[2]), (1, 0, 0), acier, 24, 'pavillon'))
av.add(box((0.006, 0.07, 0.018), (AVP[0] - 0.015, AVP[1] + 0.04, AVP[2]), acier_noir, 0.002, 'patte'))
for dz in (-0.007, 0.007):
    av.add(box((0.006, 0.010, 0.004), (AVP[0] - 0.016, AVP[1] + 0.02, AVP[2] + dz), laiton, name='cosse'))
fastener(av, 'ecrou-avertisseur', (AVP[0] - 0.015, AVP[1] + 0.07, AVP[2]), (-1, 0, 0), kind='nut', r=0.006, length=0.015, travel=0.03)

cc = Part('centrale-clignotante', (-0.2, 0, -0.1))
CCP = (0.58, 0.76, -0.50)
cc.add(cyl(0.016, 0.045, CCP, (0, 1, 0), plastique_gris, 24, name='boitier'))
cc.add(cyl(0.017, 0.006, (CCP[0], CCP[1] - 0.024, CCP[2]), (0, 1, 0), noir, 24, name='embase'))
for k, a in enumerate((0, 2.1, 4.2)):
    cc.add(box((0.0012, 0.008, 0.005), (CCP[0] + 0.007 * math.cos(a), CCP[1] - 0.031, CCP[2] + 0.007 * math.sin(a)), laiton, name='broche'))
cc.add(box((0.004, 0.03, 0.03), (CCP[0] + 0.02, CCP[1], CCP[2]), acier_noir, 0.002, 'agrafe'))
branch(cc, [(0.56, 0.78, -0.56), (0.57, 0.72, -0.52), (CCP[0], CCP[1] - 0.04, CCP[2])], 3, (0.03, 0.012, 0.03))
fastener(cc, 'vis-centrale', (CCP[0] + 0.022, CCP[1], CCP[2]), (1, 0, 0), kind='screw', r=0.004, length=0.012, travel=0.02)

pf_ = Part('plafonnier', (0, -0.15, 0))
PP = (-0.05, 1.495, 0.0)
pf_.add(extrude(rounded_rect(0.16, 0.06, 0.02), 0.012, (PP[0], PP[1] - 0.006, PP[2]), (0, 1, 0), plastique_cl, 'boitier', bev=0.003))
pf_.add(extrude(rounded_rect(0.12, 0.045, 0.015), 0.006, (PP[0], PP[1] - 0.014, PP[2]), (0, 1, 0), diffuseur, 'diffuseur', bev=0.002))
pf_.add(box((0.012, 0.006, 0.02), (PP[0] + 0.065, PP[1] - 0.016, PP[2]), noir, 0.002, 'interrupteur'))
pf_.add(cyl(0.005, 0.039, (PP[0], PP[1] - 0.012, PP[2]), (1, 0, 0), verre, 12, name='navette'))   # navette 10 × 39
for sg in (1, -1):
    pf_.add(cyl(0.0052, 0.006, (PP[0] + sg * 0.0195, PP[1] - 0.012, PP[2]), (1, 0, 0), culot, 12, name='culot'))
fasteners(pf_, 'vis-plafonnier', [((PP[0] - 0.065, PP[1] - 0.013, PP[2]), (0, -1, 0)), ((PP[0] + 0.045, PP[1] - 0.013, PP[2]), (0, -1, 0))], kind='screw', r=0.0035, length=0.012, travel=0.02)

# =====================================================================================
# AMPOULES (tableau des lampes p.71) : projecteurs P 45 t 41, feux AV et AR, éclaireur de plaque
# =====================================================================================
am = Part('ampoules', (0.2, 0.1, 0))


def bulb(part, pos, axis, r, ln, base_r, two=False):
    a = axis
    p = pos
    part.add(cyl(base_r, ln * 0.45, p, a, culot, 16, name='culot'))
    tip = tuple(p[i] + a[i] * ln * 0.55 for i in range(3))
    part.add(sphere(r, tip, verre, 14, 8, 'globe'))
    part.add(tube([tuple(tip[i] - a[i] * r * 0.5 for i in range(3)), tuple(tip[i] + a[i] * r * 0.3 for i in range(3))], r * 0.08, filament, 'filament', seg=4))
    if two:
        part.add(tube([tuple(tip[i] - a[i] * r * 0.2 + (0, r * 0.35, 0)[i] for i in range(3)), tuple(tip[i] + a[i] * r * 0.5 + (0, r * 0.35, 0)[i] for i in range(3))], r * 0.07, filament, 'filament', seg=4))
        part.add(box((r * 0.5, r * 0.08, r * 0.9), tuple(tip[i] + (0, r * 0.15, 0)[i] for i in range(3)), culot, name='coupelle-code'))   # cuvette du code
    for k, (dy, dz) in enumerate(((0.0, base_r * 1.1), (0.0, -base_r * 1.1))):
        part.add(box((0.002, 0.002, 0.004), (p[0], p[1] + dy, p[2] + dz), culot, name='ergot'))


for s in (1, -1):
    bulb(am, (HL[0] - 0.085, HL[1], s * 0.417), (1, 0, 0), 0.0125, 0.05, 0.0115, two=True)          # P 45 t 41, 45/40 W
    bulb(am, (HL[0] - 0.060, HL[1] - 0.05, s * 0.417), (1, 0, 0), 0.0045, 0.012, 0.0035)             # veilleuse R 19 5 W
    bulb(am, (GX - 0.002, 0.505, s * 0.485), (1, 0, 0), 0.0125, 0.03, 0.0075)                        # clignotant P 25-1 21 W
    for yy in (0.76, 0.87):                                                                          # P 25-2 21/5 W et P 25-1
        bulb(am, (-1.755, yy, s * 0.632), (-1, 0, 0), 0.0125, 0.03, 0.0075)
bulb(am, (-1.795, 0.62, 0.0), (-1, 0, 0), 0.0045, 0.012, 0.0035)                                    # éclaireur de plaque

# =====================================================================================
# APPAREIL DE CHAUFFAGE-VENTILATION (« climatiseur », p.75) : boîtier contre le tablier sous l'auvent
# (prise d'air frais par la grille d'auvent), radiateur de chauffage, moto-ventilateur deux vitesses
# (p.85), robinet d'eau, durites vers le moteur ; dans l'habitacle, gaines de désembuage et de pieds
# derrière la planche, volets commandés par câbles depuis les boutons de chauffage
# =====================================================================================
ch = Part('chauffage', (0.25, 0.25, 0.0))
HC = (0.765, 0.875, 0.0)
ch.add(box((0.09, 0.105, 0.22), HC, plastique_gris, 0.012, 'boitier'))
ch.add(box((0.094, 0.006, 0.224), (HC[0], HC[1] + 0.01, HC[2]), noir, 0.002, 'joint-coquilles'))
ch.add(box((0.004, 0.10, 0.20), (TABLIER_X + 0.004, HC[1], HC[2]), caoutchouc, 0.002, 'joint-tablier'))
VO = (HC[0] + 0.005, HC[1] + 0.005, HC[2] + 0.06)
ch.add(lathe([(0.0, -0.028), (0.044, -0.028), (0.048, -0.02), (0.048, 0.02), (0.044, 0.028), (0.0, 0.028)], VO, (1, 0, 0), plastique_gris, 32, 'volute'))
ch.add(cyl(0.026, 0.05, (VO[0] + 0.05, VO[1], VO[2]), (1, 0, 0), acier_noir, 24, name='moteur-ventilateur'))
ch.add(cyl(0.012, 0.012, (VO[0] + 0.08, VO[1], VO[2]), (1, 0, 0), acier, 16, name='palier-moteur'))
for k in range(16):                                                            # turbine (visible en transparence)
    a = 2 * math.pi * k / 16
    ch.add(box((0.04, 0.004, 0.016), (VO[0], VO[1] + 0.036 * math.cos(a), VO[2] + 0.036 * math.sin(a)), noir, name='pale', axis=None))
ch.add(box((0.07, 0.085, 0.028), (HC[0], HC[1] - 0.004, HC[2] - 0.055), M('faisceau-chauffage', 0x6a4a2e, 0.7, 0.5), 0.002, 'radiateur-chauffage'))
for k in range(14):
    ch.add(box((0.072, 0.0015, 0.03), (HC[0], HC[1] - 0.042 + k * 0.006, HC[2] - 0.055), cuivre, name='ailette'))
for sg, zt in ((-1, -0.30), (1, 0.28)):                                        # tubulures et durites (raccordées aux durites de chauffage du moteur)
    p0 = (HC[0] - 0.01, HC[1] - 0.035, sg * 0.11)
    ch.add(cyl(0.008, 0.04, (p0[0], p0[1], p0[2] + sg * 0.01), (0, 0, 1), cuivre, 14, name='tubulure'))
    ch.add(tube([(p0[0], p0[1], p0[2] + sg * 0.025), (0.74, 0.81, sg * 0.20), (TABLIER_X + 0.008, 0.79, zt)], 0.010, caoutchouc, 'durite-chauffage', seg=12))
    ch.add(torus(0.0115, 0.0018, (p0[0], p0[1], p0[2] + sg * 0.028), (0, 0, 1), acier, 18, 5, 'collier'))
ch.add(cyl(0.012, 0.03, (HC[0] - 0.01, HC[1] - 0.035, -0.15), (0, 0, 1), laiton, 16, name='robinet-eau'))
ch.add(box((0.006, 0.03, 0.006), (HC[0] - 0.01, HC[1] - 0.012, -0.15), acier, name='levier-robinet'))
ch.add(box((0.05, 0.005, 0.16), (HC[0] - 0.005, HC[1] + 0.055, HC[2]), plastique_gris, 0.002, 'prise-air-auvent'))
for s in (1, -1):                                                              # gaines de désembuage derrière la planche
    ch.add(tube([(TABLIER_X - 0.005, 0.90, s * 0.04), (0.665, 0.95, s * 0.22), (0.625, 0.995, s * 0.45)], 0.016, noir, 'gaine-desembuage', seg=10))
ch.add(box((0.05, 0.03, 0.16), (0.665, 0.855, 0.0), plastique_gris, 0.008, 'bouche-pieds'))
for k, zz in enumerate((0.055, 0.095)):                                       # câbles des volets depuis les boutons de la planche
    ch.add(box((0.04, 0.004, 0.05), (HC[0] - 0.02, HC[1] - 0.05, HC[2] - 0.03 + k * 0.06), acier_noir, 0.002, 'volet'))
    ch.add(tube([(0.53, 0.825, zz), (0.62, 0.84, zz), (TABLIER_X, 0.835, zz - 0.02), (HC[0] - 0.02, HC[1] - 0.055, HC[2] - 0.03 + k * 0.06)], 0.0025, noir, 'cable-volet', seg=6))
branch(ch, [(0.76, 0.87, -0.10), (0.80, 0.90, -0.02), (VO[0] + 0.07, VO[1] + 0.02, VO[2])], 3, (0.02, 0.015, 0.015))   # 2 vitesses
fasteners(ch, 'vis-chauffage', [((TABLIER_X + 0.012, HC[1] + dy, HC[2] + dz), (1, 0, 0)) for dy in (0.045, -0.045) for dz in (0.10, -0.10)], kind='screw', r=0.0045, length=0.015, travel=0.03)

export(OUT)
