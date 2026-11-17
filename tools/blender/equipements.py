# Équipements du compartiment moteur et circuits de la Renault 4 GTL : refroidissement (radiateur,
# motoventilateur, vase d'expansion, durites), électricité (batterie, alternateur et courroie,
# démarreur, boîte à fusibles, bobine, lave-glace), freinage hydraulique (maître-cylindre tandem,
# canalisations, limiteur). Lancer : python3 tools/blender/equipements.py → models/equipements.glb
#
# RTA : radiateur juste derrière la calandre, thermocontact en bas de la boîte à eau droite (p.38,
# p.71) ; vase d'expansion taré 0,8 bar (p.37) ; batterie à l'avant droit, robinet sur la borne –
# (photo p. VI) ; courroie poulie d'AAC → pompe à eau → alternateur (p.38, p.73) ; démarreur côté
# GAUCHE sous le collecteur, nez dans le carter d'embrayage, écran thermique (p.73) ; fusibles sur le tablier (p.71) ;
# maître-cylindre tandem Ø 20,6 sur le tablier, limiteur à l'arrière (p.67 à 70).
# Les positions sont prises sur les photos du compartiment moteur ; dimensions estimées.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import M, M_img, Part, box, cyl, export, extrude, fastener, fasteners, grid, hexagon, lathe, quad, reset, solidify, toothed, torus, tube  # noqa: E402
from mathutils import Quaternion  # noqa: E402
import tempfile  # noqa: E402

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'equipements.glb')

AXLE_F = 1.306
AXLE_R = {1: -1.143, -1: -1.095}
WR = 0.285
EX = 0.92
XF = EX + 0.185
TABLIER_X = 0.700
PUL_X = XF + 0.07                    # plan des poulies (côté embrayage)
CAM = (0.488, 0.074, 0.050)          # poulie d'arbre à cames (y, z, r) — voir moteur.py
WP = (0.626, 0.020, 0.060)           # poulie de pompe à eau
ALT = (0.665, 0.225, 0.036)          # poulie d'alternateur

alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
tole = M('tole-noire', 0x2d3033, 0.5, 0.5)
noir = M('noir', 0x1b1c1d, 0.1, 0.6)
caoutchouc = M('caoutchouc', 0x1d1e1f, 0.0, 0.85)
cuivre = M('cuivre', 0xb87333, 0.9, 0.3)
laiton = M('laiton', 0xb59a52, 0.9, 0.35)
faisceau = M('faisceau', 0x5a4632, 0.6, 0.6)
zinc = M('zinc', 0xc9c4ae, 0.85, 0.3)
plastique = M('plastique-translucide', 0xeeeee6, 0.0, 0.35, alpha=0.85)
liquide = M('liquide-refroidissement', 0x3b6fb0, 0.0, 0.2, alpha=0.7)
lave = M('liquide-lave-glace', 0x5a8fd0, 0.0, 0.2, alpha=0.6)
batterie_m = M('bac-batterie', 0x2a2b2d, 0.0, 0.6)
rouge = M('rouge', 0xb8302a, 0.1, 0.5)
fil = M('fil', 0x2a2a2a, 0.2, 0.6)
fil_rouge = M('fil-rouge', 0x8a2a22, 0.1, 0.55)
frein_liq = M('reservoir-frein', 0xe8e6d8, 0.0, 0.35, alpha=0.8)
bleu = M('bobine', 0x2c3e55, 0.4, 0.4)
bronze = M('coussinet', 0xc9a36a, 0.8, 0.3)
acier_taille = M('acier-taille', 0xb7bcc0, 0.95, 0.22)
bakelite = M('bakelite', 0x2a1f1b, 0.1, 0.35)

# =====================================================================================
# REFROIDISSEMENT (planche 11, p.38) : radiateur à boîtes à eau latérales (25), thermocontact (26)
# et joint (27), plots (28, 29), barre de fixation (22), motoventilateur (19) avec ventilateur (21),
# buse (20) et support (23), vase d'expansion (4) avec bouchon (1), soupape (2) et joint (3),
# thermostat (17) dans le boîtier de pompe à eau, durites et colliers.
# =====================================================================================
def core_png():
    """Faisceau vu de face : tubes plats verticaux et ailettes ondulées horizontales."""
    from PIL import Image, ImageDraw
    w, h = 1024, 640
    im = Image.new('RGB', (w, h), (58, 45, 33))
    d = ImageDraw.Draw(im)
    for y in range(0, h, 4):        # ailettes (pas ≈ 1,8 mm)
        d.line((0, y, w, y), fill=(92, 74, 54), width=1)
    for k in range(40):             # tubes plats (pas ≈ 10 mm)
        x = int((k + 0.5) * w / 40)
        d.rectangle((x - 4, 0, x + 4, h), fill=(110, 86, 58))
        d.line((x - 4, 0, x - 4, h), fill=(70, 55, 40), width=1)
    path = os.path.join(tempfile.mkdtemp(prefix='faisceau-'), 'faisceau.png')
    im.save(path)
    return path


RX = 1.692
RY, RZ = 0.625, -0.04
CW, CH = 0.41, 0.27                 # faisceau : surface frontale 12,32 dm² (p.22) → 0,41 × 0,30 hors tout
ZL, ZR = RZ - CW / 2, RZ + CW / 2   # boîtes à eau gauche (entrée) et droite (sortie, thermocontact)
core_m = M_img('faisceau-radiateur', core_png(), 0.6, 0.6)
rad = Part('radiateur', (0.5, 0.15, 0))
rad.add(box((0.030, CH, CW), (RX, RY, RZ), faisceau, name='faisceau'))
for nx in (1, -1):
    rad.add(quad((RX + nx * 0.0152, RY, RZ), CW, CH, (nx, 0, 0), core_m, 'ailettes'))
for zc, nm in ((ZL - 0.018, 'boite-gauche'), (ZR + 0.018, 'boite-droite')):
    rad.add(box((0.046, CH + 0.03, 0.036), (RX, RY, zc), noir, 0.010, nm))                    # boîte plastique
    rad.add(box((0.050, CH + 0.034, 0.006), (RX, RY, zc + (0.018 if zc > RZ else -0.018) * -1), acier, 0.001, 'sertissage'))
for yy in (RY + CH / 2 + 0.006, RY - CH / 2 - 0.006):
    rad.add(box((0.034, 0.012, CW), (RX, yy, RZ), acier_noir, 0.002, 'joue'))
rad.add(cyl(0.017, 0.045, (RX - 0.035, RY + 0.10, ZL - 0.018), (1, 0, 0), noir, 18, name='entree'))   # du thermostat
rad.add(cyl(0.017, 0.045, (RX - 0.035, RY - 0.10, ZR + 0.018), (1, 0, 0), noir, 18, name='sortie'))   # vers la pompe
rad.add(cyl(0.004, 0.030, (RX - 0.03, RY + CH / 2 + 0.008, ZL - 0.018), (1, 0, 0), noir, 8, name='raccord-vase'))
rad.add(cyl(0.012, 0.010, (RX - 0.028, RY - 0.06, ZR + 0.018), (1, 0, 0), noir, 18, name='bossage-thermocontact'))
for zz in (RZ - 0.12, RZ + 0.12):    # plots caoutchouc (28, 29) dans la traverse avant
    rad.add(cyl(0.008, 0.022, (RX, RY - CH / 2 - 0.022, zz), (0, 1, 0), caoutchouc, 14, name='plot'))
    rad.add(cyl(0.012, 0.006, (RX, RY - CH / 2 - 0.035, zz), (0, 1, 0), caoutchouc, 16, name='plot-collerette'))
rad.add(box((0.022, 0.006, CW + 0.08), (RX, 0.795, RZ), acier_noir, 0.002, 'barre-fixation'))         # barre (22)
for zz in (0.17, -0.25):
    rad.add(box((0.022, 0.03, 0.012), (RX, 0.785, zz), acier_noir, 0.002, 'patte-barre'))
fasteners(rad, 'ecrous-radiateur', [((RX, 0.808, 0.17), (0, 1, 0)), ((RX, 0.808, -0.25), (0, 1, 0))], kind='nut', r=0.007, length=0.03, travel=0.05)
fastener(rad, 'bouchon-vidange-radiateur', (RX, RY - CH / 2 - 0.02, ZR + 0.018), (0, -1, 0), kind='plug', r=0.007, length=0.015, travel=0.04)

fan = Part('motoventilateur', (0.3, 0.4, 0))
FX = RX - 0.05
# buse (20) : virole et bras de fixation vissés sur les joues du radiateur
fan.add(lathe([(0.150, -0.022), (0.158, -0.022), (0.158, 0.018), (0.172, 0.022), (0.172, 0.026), (0.150, 0.026)], (FX, RY, RZ), (1, 0, 0), noir, 64, 'buse'))
for k in range(4):
    a = 2 * math.pi * k / 4 + math.pi / 4
    fan.add(box((0.008, 0.012, 0.15), (FX - 0.03, RY + 0.075 * math.cos(a), RZ + 0.075 * math.sin(a)), acier_noir, 0.002, 'bras-buse', axis=(0, math.cos(a + math.pi / 2), math.sin(a + math.pi / 2))))
# moteur (19) et ventilateur (21) : 4 pales vrillées sur un moyeu
fan.add(lathe([(0.0, -0.045), (0.036, -0.045), (0.042, -0.035), (0.042, 0.030), (0.036, 0.036), (0.0, 0.036)], (FX - 0.065, RY, RZ), (1, 0, 0), acier_noir, 32, 'moteur'))
for k in range(6):
    a = 2 * math.pi * k / 6
    fan.add(box((0.05, 0.004, 0.004), (FX - 0.07, RY + 0.043 * math.cos(a), RZ + 0.043 * math.sin(a)), acier_noir, name='nervure-moteur'))
fan.add(cyl(0.004, 0.02, (FX - 0.115, RY, RZ), (1, 0, 0), acier, 10, name='arbre'))
fan.add(lathe([(0.0, -0.012), (0.026, -0.012), (0.028, 0.0), (0.024, 0.012), (0.0, 0.016)], (FX - 0.012, RY, RZ), (1, 0, 0), noir, 24, 'moyeu-ventilateur'))
for k in range(4):
    a0 = 2 * math.pi * k / 4
    P = []
    for i in range(7):                      # du pied (r 26 mm) au bout (r 140 mm)
        r = 0.026 + 0.114 * i / 6
        chord = 0.040 + 0.035 * math.sin(math.pi * i / 6)
        pitch = math.radians(34 - 16 * i / 6)
        row = []
        for j in range(5):
            t = (j / 4 - 0.5) * chord
            a = a0 + t / r * math.cos(pitch)
            row.append((FX - 0.012 + t * math.sin(pitch), RY + r * math.cos(a), RZ + r * math.sin(a)))
        P.append(row)
    blade = grid(P, noir, 'pale', smooth_angle=70)
    solidify(blade, 0.003, 0.0)
    fan.add(blade)
fan.add(box((0.012, 0.006, 0.30), (FX - 0.03, RY - 0.16, RZ), acier_noir, 0.002, 'support'))          # support (23)
fan.add(tube([(FX - 0.10, RY - 0.03, RZ - 0.03), (FX - 0.13, RY - 0.12, RZ + 0.05), (1.56, 0.53, 0.25), (1.55, 0.62, 0.30)], 0.003, fil, seg=6))
# thermocontact (26) et joint (27) dans la boîte à eau droite (enclenchement 90,5 à 93,5 °C)
fan.add(tube([(RX - 0.06, RY - 0.06, ZR + 0.018), (1.60, 0.55, 0.22), (1.55, 0.62, 0.30)], 0.003, fil, seg=6))
fan.add(cyl(0.0125, 0.003, (RX - 0.034, RY - 0.06, ZR + 0.018), (1, 0, 0), M('joint-fibre', 0xb79e72, 0.0, 0.8), 18, name='joint-thermocontact'))
fastener(fan, 'thermocontact-radiateur', (RX - 0.036, RY - 0.06, ZR + 0.018), (-1, 0, 0), kind='plug', r=0.009, length=0.03, travel=0.05)

vase = Part('vase-expansion', (0, 0.45, 0.25))
VX, VY, VZ = 1.05, 0.765, 0.465
vase.add(lathe([(0.0, -0.075), (0.055, -0.075), (0.062, -0.06), (0.062, 0.05), (0.05, 0.065), (0.022, 0.07), (0.022, 0.085), (0.0, 0.085)], (VX, VY, VZ), (0, 1, 0), plastique, 32, 'vase'))
vase.add(lathe([(0.0, -0.072), (0.058, -0.072), (0.058, 0.01), (0.0, 0.01)], (VX, VY, VZ), (0, 1, 0), liquide, 32, 'niveau'))
for dy, w in ((-0.035, 0.03), (0.02, 0.03)):
    vase.add(box((0.004, 0.003, w), (VX - 0.062, VY + dy, VZ), noir, name='repere'))   # mini / maxi
vase.add(torus(0.021, 0.0025, (VX, VY + 0.086, VZ), (0, 1, 0), caoutchouc, 20, 6, 'joint-soupape'))        # joint (3)
vase.add(lathe([(0.0, 0.0), (0.016, 0.0), (0.016, 0.012), (0.010, 0.016), (0.0, 0.016)], (VX, VY + 0.072, VZ), (0, 1, 0), laiton, 18, 'soupape'))   # soupape (2)
vase.add(cyl(0.006, 0.02, (VX + 0.045, VY - 0.07, VZ), (1, 0, 0), plastique, 10, name='raccord-sortie'))
vase.add(box((0.02, 0.12, 0.08), (VX, VY - 0.02, VZ + 0.075), acier_noir, 0.004, 'support'))
vase.add(torus(0.064, 0.003, (VX, VY - 0.02, VZ), (0, 1, 0), acier_noir, 32, 6, 'collier-support'))
fastener(vase, 'bouchon-vase', (VX, VY + 0.092, VZ), (0, 1, 0), kind='plug', r=0.024, length=0.022, travel=0.07)   # bouchon (1), taré 0,8 bar

# thermostat (17) dans le boîtier de pompe à eau (voir moteur.py) : début d'ouverture 86 °C
th = Part('thermostat', (0, 0.18, 0))
TX, TY, TZ = 1.135, 0.671, -0.02
th.add(cyl(0.021, 0.0015, (TX, TY + 0.012, TZ), (0, 1, 0), M('joint', 0x8b6b45, 0.0, 0.8), 24, name='joint-thermostat'))
th.add(lathe([(0.008, 0.0), (0.020, 0.0), (0.020, 0.002), (0.008, 0.002)], (TX, TY + 0.010, TZ), (0, 1, 0), laiton, 24, 'bride'))
th.add(lathe([(0.0, -0.002), (0.013, -0.002), (0.013, 0.002), (0.0, 0.002)], (TX, TY + 0.006, TZ), (0, 1, 0), laiton, 24, 'clapet'))
th.add(lathe([(0.0, -0.022), (0.007, -0.022), (0.008, -0.004), (0.0, -0.004)], (TX, TY + 0.006, TZ), (0, 1, 0), cuivre, 18, 'capsule-cire'))
for s in (1, -1):
    th.add(tube([(TX + s * 0.016, TY + 0.010, TZ), (TX + s * 0.012, TY - 0.012, TZ), (TX, TY - 0.016, TZ)], 0.0015, laiton, 'etrier', seg=6))
pts = [(TX + 0.011 * math.cos(2 * math.pi * 3.5 * i / 30), TY + 0.004 - 0.014 * i / 30, TZ + 0.011 * math.sin(2 * math.pi * 3.5 * i / 30)) for i in range(31)]
th.add(tube(pts, 0.0011, M('ressort', 0x6d7d8a, 0.8, 0.35), 'ressort', seg=4, res=2))
fasteners(th, 'vis-boitier-thermostat', [((TX + s * 0.024, TY + 0.03, TZ), (0, 1, 0)) for s in (1, -1)], kind='bolt', r=0.004, length=0.025, travel=0.04)

dur = Part('durites', (0.15, 0.3, 0))
up = [(1.175, 0.690, -0.02), (1.30, 0.75, -0.10), (1.50, 0.76, -0.20), (RX - 0.065, RY + 0.10, ZL - 0.018)]
lo = [(RX - 0.065, RY - 0.10, ZR + 0.018), (1.50, 0.53, 0.20), (1.25, 0.58, 0.14), (1.16, 0.58, 0.07)]
dur.add(tube(up, 0.019, caoutchouc, 'durite-superieure', seg=14, res=10))     # thermostat → radiateur
dur.add(tube(lo, 0.019, caoutchouc, 'durite-inferieure', seg=14, res=10))     # radiateur → pompe
dur.add(tube([(0.76, 0.64, -0.06), (0.73, 0.72, -0.20), (TABLIER_X + 0.005, 0.79, -0.30)], 0.010, caoutchouc, 'durite-chauffage-aller', seg=10))
dur.add(tube([(1.12, 0.58, 0.07), (0.95, 0.64, 0.25), (0.76, 0.74, 0.30), (TABLIER_X + 0.005, 0.79, 0.28)], 0.010, caoutchouc, 'durite-chauffage-retour', seg=10, res=10))
dur.add(tube([(VX + 0.06, VY - 0.07, VZ), (1.20, 0.72, 0.35), (1.55, 0.82, 0.10), (RX - 0.03, RY + CH / 2 + 0.008, ZL - 0.018)], 0.005, caoutchouc, 'tuyau-vase', seg=8, res=10))
cl = []
for p, ax in ((up[0], (1, 0.4, 0)), (up[-1], (1, 0, 0)), (lo[0], (1, 0, 0)), (lo[-1], (1, 0, 0)),
              ((0.76, 0.645, -0.065), (0.3, 1, -0.6)), ((TABLIER_X + 0.012, 0.79, -0.30), (1, 0, 0)), ((TABLIER_X + 0.012, 0.79, 0.28), (1, 0, 0)), ((1.115, 0.582, 0.075), (1, 0, 0))):
    r = 0.019 if p in (up[0], up[-1], lo[0], lo[-1]) else 0.010
    dur.add(torus(r + 0.002, 0.0022, p, ax, zinc, 24, 6, 'collier'))
    cl.append(((p[0], p[1] + r + 0.004, p[2]), (0, 1, 0)))
fasteners(dur, 'colliers-durites', cl, kind='screw', r=0.003, length=0.012, travel=0.025)
fasteners(dur, 'vis-purge-refroidissement', [((1.20, 0.712, -0.045), (0, 1, 0)), ((0.73, 0.735, -0.20), (0, 1, 0))], kind='screw', r=0.005, length=0.015, travel=0.012)

# =====================================================================================
# ÉLECTRICITÉ
# =====================================================================================
bat = Part('batterie', (0.2, 0.55, 0.3))
BX, BY, BZ = 1.62, 0.69, 0.37
bat.add(box((0.175, 0.165, 0.13), (BX, BY, BZ), batterie_m, 0.006, 'bac'))
bat.add(box((0.178, 0.012, 0.133), (BX, BY + 0.088, BZ), noir, 0.004, 'couvercle'))
for k in range(6):
    bat.add(cyl(0.009, 0.008, (BX - 0.07 + k * 0.028, BY + 0.097, BZ), (0, 1, 0), noir, 14, name='bouchon'))
bat.add(box((0.20, 0.012, 0.15), (BX, BY - 0.088, BZ), acier_noir, 0.003, 'bac-support'))
bat.add(box((0.012, 0.012, 0.15), (BX, BY + 0.097, BZ), acier_noir, 0.002, 'bride'))
for s in (1, -1):
    bat.add(tube([(BX, BY + 0.097, BZ + s * 0.075), (BX, BY - 0.09, BZ + s * 0.075)], 0.004, acier, seg=6))   # tiges de bride
bat.add(cyl(0.011, 0.02, (BX - 0.07, BY + 0.104, BZ + 0.045), (0, 1, 0), M('plomb', 0x8d8f91, 0.6, 0.5), 14, name='borne+'))
bat.add(cyl(0.010, 0.02, (BX + 0.07, BY + 0.104, BZ + 0.045), (0, 1, 0), M('plomb', 0x8d8f91, 0.6, 0.5), 14, name='borne-'))
bat.add(box((0.035, 0.025, 0.03), (BX + 0.07, BY + 0.125, BZ + 0.045), rouge, 0.006, 'robinet'))   # coupe-batterie (repère 7)
bat.add(tube([(BX + 0.07, BY + 0.135, BZ + 0.045), (BX + 0.12, BY + 0.10, BZ + 0.07), (BX + 0.12, BY - 0.05, BZ + 0.15)], 0.007, fil, seg=10))
fasteners(bat, 'bornes-batterie', [((BX - 0.07, BY + 0.118, BZ + 0.045), (0, 1, 0)), ((BX + 0.07, BY + 0.118, BZ + 0.045), (0, 1, 0))], kind='nut', r=0.007, length=0.02, travel=0.05)

alt = Part('alternateur', (0.2, 0.1, 0.45))
AY_, AZ_ = ALT[0], ALT[1]
alt.add(lathe([(0.0, -0.06), (0.058, -0.06), (0.066, -0.045), (0.066, 0.045), (0.058, 0.06), (0.0, 0.06)], (PUL_X - 0.11, AY_, AZ_), (1, 0, 0), alu, 36, 'carcasse'))
for k in range(12):
    a = 2 * math.pi * k / 12
    alt.add(box((0.09, 0.006, 0.006), (PUL_X - 0.11, AY_ + 0.066 * math.cos(a), AZ_ + 0.066 * math.sin(a)), alu, name='nervure'))
alt.add(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (0.0, 0.012)], (PUL_X - 0.05, AY_, AZ_), (1, 0, 0), acier_noir, 28, 'ventilateur'))
alt.add(lathe([(0.008, -0.009), (ALT[2], -0.009), (ALT[2], -0.006), (ALT[2] - 0.006, 0.0), (ALT[2], 0.006), (ALT[2], 0.009), (0.008, 0.009)], (PUL_X, AY_, AZ_), (1, 0, 0), acier_noir, 32, 'poulie'))
alt.add(box((0.04, 0.03, 0.05), (PUL_X - 0.17, AY_ + 0.02, AZ_ + 0.03), noir, 0.006, 'regulateur'))
alt.add(box((0.05, 0.03, 0.04), (PUL_X - 0.11, AY_ - 0.075, AZ_ - 0.03), acier_noir, 0.006, 'patte-pivot'))
alt.add(tube([(PUL_X - 0.10, AY_ + 0.06, AZ_ - 0.03), (PUL_X - 0.10, AY_ + 0.09, AZ_ - 0.12), (PUL_X - 0.10, 0.68, 0.06)], 0.006, acier_noir, seg=8))   # tendeur à coulisse
alt.add(tube([(PUL_X - 0.17, AY_ + 0.03, AZ_ + 0.05), (0.95, 0.62, 0.30), (0.80, 0.80, 0.30)], 0.004, fil, seg=6))


def belt_loop(pulleys, n=24):
    """Courroie : enveloppe convexe des poulies (plan y-z), échantillonnée."""
    pts = []
    for y, z, r in pulleys:
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append((y + (r + 0.004) * math.cos(a), z + (r + 0.004) * math.sin(a)))
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


hull = belt_loop([CAM, WP, ALT])
alt.add(tube([(PUL_X, y, z) for y, z in hull], 0.0045, caoutchouc, seg=6, res=2, closed=True))
fastener(alt, 'pivot-alternateur', (PUL_X - 0.04, AY_ - 0.075, AZ_ - 0.03), (1, 0, 0), kind='bolt', r=0.008, length=0.15, travel=0.20)
fasteners(alt, 'tendeur-courroie', [((PUL_X - 0.10, AY_ + 0.065, AZ_ - 0.03), (0, 0.6, 0.8)), ((PUL_X - 0.10, 0.68, 0.06), (0, 1, 0))], kind='bolt', r=0.007, length=0.03, travel=0.04)

# Démarreur Paris-Rhône D 8 E 121 (planche 26, p.74) : côté GAUCHE, sous le collecteur, nez engagé
# dans le carter d'embrayage. RTA p.73 : dépose après le filtre à air, la bride du tuyau
# d'échappement et l'écran de protection du démarreur ; boulon haut (clé Elé 565) et boulon
# inférieur à écrou (clé à rotule 3/8" + douille de 13, clé contre-coudée pour tenir l'écrou).
# Repères de la vue éclatée : fourchette (1), solénoïde (2), pignon lanceur (3), plateau
# porte-balais (4), inducteur (5), induit (6). Longueurs et diamètres estimés (Ø carcasse 78 mm).
SA_Y, SA_Z = 0.412, -0.141           # axe du démarreur (voir moteur.py)
RING_X = XF + 0.030                  # couronne du volant (96 dents)


def sector(profile, x0, a0, a1, mat, name, seg=24, ax=(1, 0, 0)):
    """Révolution autour de l'axe du démarreur, de a0 à a1 (degrés) : 0° = vers le bas,
    90° = vers l'extérieur (gauche), 180° = vers le haut, 270° = vers le moteur."""
    o = lathe(profile, (x0, SA_Y, SA_Z), ax, mat, seg, name, angle=math.radians(a1 - a0))
    o.rotation_quaternion = o.rotation_quaternion @ Quaternion((0, 0, 1), math.radians(a0))
    return o


def on_axis(r, a, x):
    """Point à `r` de l'axe du démarreur, angle `a` (même convention que sector)."""
    t = math.radians(a)
    return (x, SA_Y - r * math.cos(t), SA_Z - r * math.sin(t))


def radial(a):
    t = math.radians(a)
    return (0, -math.cos(t), -math.sin(t))


dem = Part('demarreur', (0, -0.12, -0.45))
X_FL = XF                            # bride d'appui contre la face arrière du carter d'embrayage
X_F0 = X_FL - 0.044                  # carter intermédiaire (fourchette)
X_Y1 = X_F0 - 0.112                  # arrière de la carcasse
# nez en alu : cône ouvert côté couronne (fenêtre d'engrènement), bague bronze en bout
dem.add(sector([(0.0, 0.0), (0.036, 0.0), (0.036, 0.022), (0.030, 0.045), (0.018, 0.062), (0.011, 0.068), (0.0, 0.068)], X_FL, 325, 575, alu, 'nez', 40))
dem.add(lathe([(0.0045, 0.0), (0.011, 0.0), (0.011, 0.008), (0.0045, 0.008)], (X_FL + 0.064, SA_Y, SA_Z), (1, 0, 0), bronze, 16, 'bague-nez'))
# bride à deux oreilles (boulon haut, boulon bas)
dem.add(lathe([(0.0, 0.0), (0.041, 0.0), (0.041, 0.008), (0.0, 0.008)], (X_FL - 0.002, SA_Y, SA_Z), (1, 0, 0), alu, 40, 'bride'))
EARS = (162, 342)
for a in EARS:
    dem.add(cyl(0.011, 0.008, on_axis(0.048, a, X_FL + 0.002), (1, 0, 0), alu, 18, name='oreille-bride'))
    dem.add(box((0.008, 0.016, 0.012), on_axis(0.040, a, X_FL + 0.002), alu, name='oreille-bride', axis=None))
# pignon lanceur (3) au repos derrière la couronne, roue libre, ressort et arbre d'induit
dem.add(toothed(9, 0.01215, 0.012, (RING_X - 0.016, SA_Y, SA_Z), (1, 0, 0), acier_taille, hole=0.005, name='pignon-lanceur'))
dem.add(lathe([(0.0065, 0.0), (0.020, 0.0), (0.020, 0.020), (0.013, 0.024), (0.0065, 0.024)], (RING_X - 0.048, SA_Y, SA_Z), (1, 0, 0), acier, 24, 'roue-libre'))
dem.add(cyl(0.006, X_FL + 0.068 - (X_Y1 - 0.02), ((X_FL + 0.068 + X_Y1 - 0.02) / 2, SA_Y, SA_Z), (1, 0, 0), acier, 14, name='arbre-induit'))
# carter intermédiaire et fourchette (1) ; axe de fourchette visible sur le dessus
dem.add(lathe([(0.0, 0.0), (0.040, 0.0), (0.040, 0.044), (0.0, 0.044)], (X_F0, SA_Y, SA_Z), (1, 0, 0), alu, 36, 'carter-fourchette'))
dem.add(cyl(0.0045, 0.014, on_axis(0.040, 205, X_F0 + 0.022), radial(205), acier, 10, name='axe-fourchette'))
# carcasse acier noir (inducteur 5), vis de masses polaires, bande de protection des balais
dem.add(lathe([(0.0, 0.0), (0.039, 0.0), (0.039, X_F0 - X_Y1), (0.0, X_F0 - X_Y1)], (X_Y1, SA_Y, SA_Z), (1, 0, 0), acier_noir, 40, 'carcasse'))
for a in (60, 240):
    dem.add(cyl(0.0065, 0.004, on_axis(0.039, a, X_Y1 + 0.055), radial(a), acier, 12, name='vis-masse-polaire'))
dem.add(lathe([(0.0392, 0.0), (0.0408, 0.0), (0.0408, 0.020), (0.0392, 0.020)], (X_Y1 + 0.004, SA_Y, SA_Z), (1, 0, 0), acier, 40, 'bande-balais'))
dem.add(cyl(0.0035, 0.008, on_axis(0.044, 300, X_Y1 + 0.014), (1, 0, 0), acier, 10, name='vis-bande'))
# plateau porte-balais (4) : palier arrière en alu, bossage de bague, tirants et leurs écrous
dem.add(lathe([(0.0, 0.0), (0.037, 0.0), (0.037, 0.008), (0.030, 0.014), (0.014, 0.016), (0.014, 0.026), (0.010, 0.028), (0.0, 0.028)], (X_Y1, SA_Y, SA_Z), (-1, 0, 0), alu, 36, 'plateau-porte-balais'))
for a in (110, 290):
    p0 = on_axis(0.031, a, X_Y1 - 0.016)
    dem.add(extrude(hexagon(0.0045), 0.004, p0, (1, 0, 0), acier, 'ecrou-tirant'))
    dem.add(cyl(0.0022, X_FL - X_Y1, ((X_FL + X_Y1) / 2 - 0.006, p0[1], p0[2]), (1, 0, 0), acier, 8, name='tirant'))
# patte arrière vissée sur le flanc du carter-cylindres
P_X = X_Y1 - 0.022
dem.add(box((0.006, 0.016, 0.040), (P_X, SA_Y + 0.020, SA_Z + 0.018), acier_noir, 0.001, 'patte-arriere'))
dem.add(box((0.006, 0.030, 0.012), (P_X, SA_Y + 0.040, -0.113), acier_noir, 0.001, 'patte-arriere'))
# solénoïde (2) sur le dessus : corps, capot bakélite, gros plots (batterie, inducteur), cosse +
SOL = on_axis(0.062, 180, 0)
SX0, SX1 = X_FL - 0.020, X_FL - 0.094
dem.add(lathe([(0.0, 0.0), (0.022, 0.0), (0.022, SX0 - SX1 - 0.012), (0.0, SX0 - SX1 - 0.012)], (SX0, SOL[1], SOL[2]), (-1, 0, 0), acier_noir, 32, 'solenoide'))
dem.add(lathe([(0.0, 0.0), (0.0215, 0.0), (0.0215, 0.008), (0.018, 0.012), (0.0, 0.012)], (SX1 + 0.012, SOL[1], SOL[2]), (-1, 0, 0), bakelite, 32, 'capot-solenoide'))
dem.add(box((0.040, 0.014, 0.030), on_axis(0.044, 180, SX0 - 0.03), acier_noir, 0.002, 'semelle-solenoide'))
BAT_T = (SX1 - 0.004, SOL[1] + 0.009, SOL[2] - 0.006)      # plot batterie (haut)
MOT_T = (SX1 - 0.004, SOL[1] - 0.010, SOL[2] + 0.004)      # plot vers l'inducteur
for p in (BAT_T, MOT_T):
    dem.add(cyl(0.0035, 0.016, p, (1, 0, 0), laiton, 10, name='plot'))
dem.add(box((0.003, 0.010, 0.006), (SX1 + 0.002, SOL[1] - 0.004, SOL[2] - 0.016), laiton, name='cosse-commande'))
# barrette cuivre : plot du solénoïde → borne d'inducteur sur la carcasse
FT = on_axis(0.041, 180, X_Y1 + 0.03)
dem.add(tube([(MOT_T[0] - 0.006, MOT_T[1], MOT_T[2]), (MOT_T[0] - 0.012, MOT_T[1] - 0.004, MOT_T[2]), (FT[0] + 0.01, FT[1] + 0.004, FT[2]), FT], 0.0025, cuivre, 'barrette-inducteur', seg=6))
dem.add(cyl(0.006, 0.006, FT, (0, 1, 0), bakelite, 12, name='borne-inducteur'))
fasteners(dem, 'ecrous-bornes-demarreur', [((BAT_T[0] - 0.006, BAT_T[1], BAT_T[2]), (-1, 0, 0)), ((MOT_T[0] - 0.006, MOT_T[1], MOT_T[2]), (-1, 0, 0))], kind='nut', r=0.0055, length=0.012, travel=0.03, washer=False)
# fixations : boulon haut (clé Elé 565), boulon bas et son écrou côté carter d'embrayage, patte arrière
fx_dem = [(on_axis(0.048, EARS[0], X_FL - 0.002), (-1, 0, 0)), (on_axis(0.048, EARS[1], X_FL - 0.002), (-1, 0, 0)),
          ((P_X, SA_Y + 0.040, -0.120), (0, 0, -1))]
fasteners(dem, 'vis-demarreur', fx_dem, kind='bolt', r=0.0075, length=0.05, travel=0.08)
fastener(dem, 'ecrou-demarreur', on_axis(0.048, EARS[1], XF + 0.014), (1, 0, 0), kind='nut', r=0.0075, length=0.012, travel=0.05)

# écran de protection du démarreur : tôle cintrée entre la descente d'échappement et le démarreur
ecr = Part('ecran-demarreur', (0, 0.06, -0.32))
E0, E1 = X_Y1 + 0.006, X_FL - 0.012
tole_alu = M('tole-aluminiee', 0xb7bab6, 0.75, 0.4)
ecr.add(sector([(0.050, 0.0), (0.0512, 0.0), (0.0512, E1 - E0), (0.050, E1 - E0), (0.050, 0.0)], E0, 52, 150, tole_alu, 'tole-ecran', 24))
for a in (52, 150):   # bords tombés
    ecr.add(box((E1 - E0, 0.0012, 0.008), on_axis(0.046, a, (E0 + E1) / 2), tole_alu, name='bord-ecran', axis=None))
ecr.add(sector([(0.0402, 0.0), (0.0415, 0.0), (0.0415, 0.012), (0.0402, 0.012)], (E0 + E1) / 2 - 0.006, 0, 360, acier, 'collier-ecran', 32))
ecr.add(box((0.012, 0.008, 0.010), on_axis(0.046, 101, (E0 + E1) / 2), acier, 0.001, 'patte-collier', axis=None))
fastener(ecr, 'vis-ecran-demarreur', on_axis(0.052, 101, (E0 + E1) / 2), radial(101), kind='bolt', r=0.005, length=0.012, travel=0.03)

# câble de batterie (+) : borne + (avant droit) → plot du solénoïde, par l'avant de la boîte
bat.add(tube([(BX - 0.07, BY + 0.12, BZ + 0.045), (BX - 0.13, BY + 0.10, BZ - 0.01), (1.47, 0.70, 0.20), (1.46, 0.62, 0.0),
              (1.40, 0.60, -0.18), (1.25, 0.56, -0.25), (1.10, 0.52, -0.21), (BAT_T[0] - 0.015, BAT_T[1] + 0.012, BAT_T[2] - 0.01),
              (BAT_T[0] - 0.008, BAT_T[1], BAT_T[2])], 0.007, fil_rouge, 'cable-batterie', seg=10, res=12))
bat.add(box((0.004, 0.018, 0.016), (BAT_T[0] - 0.007, BAT_T[1], BAT_T[2]), cuivre, 0.001, 'cosse-cable'))

fus = Part('fusibles', (0.25, 0.3, 0))
fus.add(box((0.035, 0.07, 0.17), (TABLIER_X + 0.02, 0.84, -0.20), noir, 0.006, 'platine'))
fus.add(box((0.004, 0.06, 0.16), (TABLIER_X + 0.039, 0.84, -0.20), M('couvercle-fusibles', 0xd9d4c3, 0.0, 0.3, alpha=0.45), 0.002, 'couvercle'))
fasteners(fus, 'fusibles-cartouches', [((TABLIER_X + 0.033, 0.84, -0.255 + i * 0.036), (1, 0, 0)) for i in range(4)], kind='fuse', r=0.006, length=0.03, travel=0.06)
for k in range(5):
    fus.add(tube([(TABLIER_X + 0.02, 0.80, -0.27 + k * 0.035), (TABLIER_X + 0.01, 0.76, -0.25 + k * 0.03), (TABLIER_X + 0.002, 0.74, -0.2)], 0.003, fil, seg=6))

bob = Part('bobine', (0, 0.3, 0.3))
bob.add(lathe([(0.0, -0.07), (0.03, -0.07), (0.03, 0.06), (0.02, 0.075), (0.0, 0.078)], (TABLIER_X + 0.05, 0.80, 0.20), (0, 1, 0), bleu, 28, 'bobine'))
bob.add(box((0.02, 0.10, 0.07), (TABLIER_X + 0.012, 0.80, 0.20), acier_noir, 0.004, 'collier'))
bob.add(cyl(0.006, 0.025, (TABLIER_X + 0.05, 0.89, 0.20), (0, 1, 0), noir, 12, name='sortie-ht'))
bob.add(tube([(TABLIER_X + 0.05, 0.90, 0.20), (0.80, 0.86, 0.15), (0.84, 0.80, 0.11)], 0.004, noir, seg=6))   # fil HT vers l'allumeur

# =====================================================================================
# PLAQUES D'IDENTIFICATION (RTA p.5 / PDF p.19 et photo) : plaque constructeur rivée sur le
# tablier côté droit, plaque ovale sur le tablier côté gauche, référence peinture sur le côté
# d'auvent droit (la plaque moteur est sur le bloc, moteur.py ; la plaque de boîte sur le
# couvercle avant de boîte, transmission.py). Champs de numéros laissés vides.
# =====================================================================================
def id_png(name, size, bg, lines, oval=False):
    from PIL import Image, ImageDraw, ImageFont
    w, h = size
    im = Image.new('RGB', (w, h), (40, 40, 40) if oval else bg)
    d = ImageDraw.Draw(im)
    if oval:
        d.ellipse((2, 2, w - 3, h - 3), fill=bg, outline=(90, 90, 90), width=4)
    else:
        d.rectangle((2, 2, w - 3, h - 3), outline=(90, 90, 90), width=4)
        for cx, cy in ((14, 14), (w - 14, 14), (14, h - 14), (w - 14, h - 14)):
            d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(150, 150, 150))
    fp = next((f for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if os.path.exists(f)), '')
    y = 0
    for txt, sz in lines:
        y += sz * 0.6
        font = ImageFont.truetype(fp, sz) if fp else None
        d.text((w / 2, y + h * 0.08), txt, fill=(25, 25, 25), font=font, anchor='mm')
        y += sz * 0.75
    path = os.path.join(tempfile.mkdtemp(prefix='id-'), name + '.png')
    im.save(path)
    return path


pid = Part('plaques-identification', (0.12, 0.1, 0))
alu_id = (214, 214, 206)
pc = M_img('plaque-constructeur', id_png('constructeur', (400, 300), alu_id, [('RÉGIE NATIONALE', 30), ('DES USINES RENAULT', 30), ('◇ 112800 (R 1128)', 34), ('N° ············', 30), ('PTAC ····· kg', 26), ('PTR ····· kg', 26), ('1 – ··· kg   2 – ··· kg', 26)]), 0.6, 0.4)
pid.add(quad((TABLIER_X + 0.004, 0.72, 0.36), 0.10, 0.075, (1, 0, 0), pc, 'plaque-constructeur'))
po = M_img('plaque-ovale', id_png('ovale', (360, 200), alu_id, [('R 1128', 52), ('· · · ·', 34), ('N° ··········', 30)], oval=True), 0.6, 0.4)
pid.add(quad((TABLIER_X + 0.004, 0.87, -0.06), 0.09, 0.05, (1, 0, 0), po, 'plaque-ovale'))
pp = M_img('reference-peinture', id_png('peinture', (300, 120), (236, 233, 222), [('PEINTURE', 34), ('réf. ·····', 34)]), 0.0, 0.6)
pid.add(quad((TABLIER_X + 0.004, 0.93, 0.47), 0.06, 0.024, (1, 0, 0), pp, 'reference-peinture'))
for zz, yy in ((0.36 - 0.044, 0.72 + 0.031), (0.36 + 0.044, 0.72 + 0.031), (0.36 - 0.044, 0.72 - 0.031), (0.36 + 0.044, 0.72 - 0.031), (-0.06 - 0.038, 0.87), (-0.06 + 0.038, 0.87)):
    pid.add(cyl(0.0028, 0.002, (TABLIER_X + 0.0045, yy, zz), (1, 0, 0), acier, 10, name='rivet'))

lg = Part('lave-glace', (0, 0.4, 0.3))
lg.add(box((0.12, 0.13, 0.085), (1.26, 0.77, 0.475), plastique, 0.02, 'reservoir'))
lg.add(box((0.115, 0.08, 0.08), (1.26, 0.745, 0.475), lave, 0.018, 'liquide'))
lg.add(cyl(0.02, 0.025, (1.24, 0.845, 0.475), (0, 1, 0), M('bleu', 0x2c64a3, 0.1, 0.4), 16, name='bouchon'))
lg.add(cyl(0.018, 0.035, (1.29, 0.71, 0.475), (0, 1, 0), noir, 14, name='pompe'))
lg.add(tube([(1.29, 0.69, 0.47), (1.10, 0.86, 0.40), (0.80, 0.98, 0.25), (0.665, 1.045, 0.10)], 0.0025, M('tuyau-lave', 0xdbd8cc, 0.0, 0.5), seg=6, res=10))

# =====================================================================================
# FREINAGE HYDRAULIQUE
# =====================================================================================
mc = Part('maitre-cylindre', (0.2, 0.45, -0.2))
MZ, MY = -0.42, 0.82
mc.add(box((0.012, 0.10, 0.10), (TABLIER_X + 0.008, MY, MZ), acier_noir, 0.006, 'bride'))
mc.add(lathe([(0.0, 0.0), (0.024, 0.0), (0.024, 0.15), (0.02, 0.16), (0.0, 0.16)], (TABLIER_X + 0.014, MY, MZ), (1, 0, 0), alu, 28, 'corps'))
mc.add(box((0.10, 0.06, 0.065), (TABLIER_X + 0.085, MY + 0.06, MZ), frein_liq, 0.012, 'reservoir'))
mc.add(box((0.09, 0.03, 0.06), (TABLIER_X + 0.085, MY + 0.045, MZ), M('liquide-frein', 0xc9b26a, 0.0, 0.2, alpha=0.6), 0.01, 'liquide'))
mc.add(cyl(0.022, 0.014, (TABLIER_X + 0.085, MY + 0.098, MZ), (0, 1, 0), noir, 20, name='bouchon'))
mc.add(cyl(0.008, 0.02, (TABLIER_X + 0.15, MY, MZ - 0.03), (0, 0, 1), laiton, 10, name='contacteur-stop'))
for dz in (0.02, -0.02):
    mc.add(cyl(0.006, 0.02, (TABLIER_X + 0.12, MY - 0.03, MZ + dz), (0, 1, 0), laiton, 10, name='raccord'))
# canalisations : circuit AV gauche, AV droit, et vers le limiteur arrière
for s in (1, -1):
    mc.add(tube([(TABLIER_X + 0.12, MY - 0.04, MZ + 0.02), (0.90, 0.70, s * 0.40 if s < 0 else -0.10), (1.10, 0.55, s * 0.38), (AXLE_F - 0.20, 0.50, s * 0.40)], 0.0028, cuivre, seg=6, res=12))
mc.add(tube([(TABLIER_X + 0.12, MY - 0.04, MZ - 0.02), (TABLIER_X + 0.05, 0.55, -0.52), (0.60, 0.36, -0.55), (0.0, 0.345, -0.55), (-0.60, 0.33, -0.20), (-0.80, 0.30, 0.15)], 0.0028, cuivre, seg=6, res=14))
fasteners(mc, 'vis-maitre-cylindre', [((TABLIER_X + 0.018, MY + 0.035, MZ + 0.035), (1, 0, 0)), ((TABLIER_X + 0.018, MY - 0.035, MZ - 0.035), (1, 0, 0))], kind='nut', r=0.007, length=0.03, travel=0.04)

lim = Part('limiteur', (0, -0.3, 0.2))
lim.add(box((0.07, 0.05, 0.05), (-0.80, 0.30, 0.18), alu, 0.008, 'corps'))
lim.add(box((0.03, 0.08, 0.06), (-0.80, 0.33, 0.215), acier_noir, 0.004, 'support'))
lim.add(tube([(-0.80, 0.29, 0.15), (-0.95, 0.27, 0.35), (AXLE_R[1] + 0.10, 0.28, 0.46)], 0.004, acier, seg=6))   # tige de commande vers le bras
for s in (1, -1):
    x0 = AXLE_R[s]
    lim.add(tube([(-0.78, 0.31, 0.18), (-0.85, 0.32, s * 0.30), (x0 + 0.05, 0.33, s * 0.45), (x0, WR + 0.075, s * 0.49)], 0.0028, cuivre, seg=6, res=12))

export(OUT)
