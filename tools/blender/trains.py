# Trains avant et arrière, direction et freins de la Renault 4 GTL (berline R 1128), modélisés
# pièce par pièce d'après la RTA (boîte-pont, embrayage et transmissions : voir transmission.py).
# Lancer : python3 tools/blender/trains.py   →   models/trains.glb
#
# Cotes et nomenclatures de la RTA (pages du PDF) :
# - voies 1 280 / 1 248 mm, empattement droit 2 449 / gauche 2 401 mm, pneus 145 SR 13 (p.79, 82) ;
# - train avant (planche 18, p.54 ; p.55 à 60) : porte-fusée forgé sur rotules graissées à vie,
#   triangles sur coussinets élastiques, tirant de chasse, barres de torsion longitudinales
#   Ø 16,54 mm × 1 106 mm ancrées sous les sièges avant (2 empreintes à gauche, 3 à droite), came de
#   réglage et levier, amortisseur télescopique, barre stabilisatrice Ø 12 mm fixée aux triangles
#   inférieurs, moyeu sur deux roulements à billes 30 × 62 × 16 avec entretoise et plaque de fermeture ;
# - freins avant DBA (p.83) : disque Ø 228 × 10, chape, étrier coulissant, piston Ø 45, joint et
#   pare-poussière, deux clavettes avec épingles, plaquettes et ressorts d'appui, vis de purge ;
# - direction (planche 17, p.51 à 54) : boîtier à crémaillère sur cales de calage, pignon sur roulement
#   à aiguilles 20 × 26 × 14 et à billes 12 × 32 × 10, poussoir en Delrin et ressort sous couvercle,
#   palier antibruit, embouts vissés avec contre-écrou (cote de point milieu 71,5 mm), biellettes
#   horizontales parallèles à l'axe du bras supérieur, rotules de direction ;
# - train arrière (planche 19, p.63 à 66) : bras tirés sur tube d'articulation et deux paliers à 3 vis,
#   barres de torsion transversales Ø 18,5 mm × 868 mm, levier d'ancrage et came, amortisseurs presque
#   horizontaux (fixation inférieure à l'arrière), pas de barre stabilisatrice sur la berline,
#   roulements coniques 20 × 47 × 15,2 et 22 × 47 × 20,75, joint 25 × 52 ;
# - freins arrière à rattrapage automatique (planche 21 bis, p.69) : flasque, mâchoires et garnitures,
#   cylindre de roue Ø 20,6 (pistons, coupelles, ressort, capuchons, vis de purge), ressorts de rappel,
#   barre et levier de frein à main, dispositif à crans de rattrapage d'usure, cavaliers de maintien ;
#   tambour Ø 180 mm (p.67).
# Les formes non cotées (bras, carters, épaisseurs) sont reprises des vues éclatées.
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (M, Part, ball_bearing, box, circlip, cyl, export, extrude, fastener, fasteners, lathe,  # noqa: E402
                 reset, roller_bearing, rounded_rect, sphere, splined, toothed, torus, tube)

reset()
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'trains.glb')

AXLE_F = 1.306
AXLE_R = {1: -1.143, -1: -1.095}     # empattement droit / gauche (barres arrière décalées)
PIVOT_R = {1: -0.70, -1: -0.65}      # tubes d'articulation des bras arrière
WR = 0.285

alu = M('alu-coule', 0xb9bcba, 0.55, 0.5)
acier = M('acier', 0x9ca3a8, 0.85, 0.3)
acier_noir = M('acier-noirci', 0x3c3f42, 0.7, 0.45)
forge = M('acier-forge', 0x4a5056, 0.6, 0.55)
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
laiton = M('laiton', 0xc8a24a, 0.9, 0.3)
ressort = M('ressort', 0x6d7d8a, 0.8, 0.35)
graisse = M('graisse', 0x8a6d2b, 0.1, 0.3)
delrin = M('delrin', 0xe8e2d0, 0.0, 0.4)
zinc = M('zinc', 0xc9c4ae, 0.85, 0.3)
pastille = M('peinture-repere', 0xd8c13a, 0.1, 0.5)
machoire_m = M('machoire', 0x6b7076, 0.6, 0.5)


# ---------------------------------------------------------------- aides
def sector(cx, cy, r0, r1, a0, a1, n=12):
    """Secteur d'anneau dans le plan (x, y) du site, centré sur (cx, cy) : à extruder le long de z."""
    pts = [(cx + r1 * math.cos(a0 + (a1 - a0) * i / n), cy + r1 * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    pts += [(cx + r0 * math.cos(a1 - (a1 - a0) * i / n), cy + r0 * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    return pts


def zslab(pts, z0, z1, mat, name='piece', bev=0.0):
    """Profil (x, y) extrudé entre z0 et z1 (repère du site)."""
    return extrude(pts, abs(z1 - z0), (0, 0, (z0 + z1) / 2), (0, 0, 1), mat, name, bev=bev, up=(0, 1, 0))


def spring(p0, p1, r, wire, turns, mat=ressort, name='ressort'):
    """Ressort hélicoïdal entre deux points."""
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in d))
    a = [c / ln for c in d]
    ref = (0, 0, 1) if abs(a[2]) < 0.9 else (1, 0, 0)
    u = (a[1] * ref[2] - a[2] * ref[1], a[2] * ref[0] - a[0] * ref[2], a[0] * ref[1] - a[1] * ref[0])
    lu = math.sqrt(sum(c * c for c in u))
    u = [c / lu for c in u]
    v = (a[1] * u[2] - a[2] * u[1], a[2] * u[0] - a[0] * u[2], a[0] * u[1] - a[1] * u[0])
    pts = []
    n = int(turns * 10)
    for i in range(n + 1):
        t = i / n
        ang = 2 * math.pi * turns * t
        pts.append(tuple(p0[k] + d[k] * t + r * (u[k] * math.cos(ang) + v[k] * math.sin(ang)) for k in range(3)))
    return tube(pts, wire, mat, name, seg=6, res=2)


def polar(c, r, a, z):
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a), z)


def bush(part, pos, axis, r_in, r_out, length, sleeve=True):
    """Coussinet élastique : douille extérieure, caoutchouc, entretoise intérieure."""
    part.add(cyl(r_out * 0.92, length * 0.9, pos, axis, caoutchouc, 20, name='silentbloc'))
    if sleeve:
        part.add(cyl(r_out, length * 0.8, pos, axis, acier_noir, 24, name='douille'))
        part.add(cyl(r_out * 0.95, length * 0.82, pos, axis, caoutchouc, 24, name='lèvre'))
    part.add(cyl(r_in, length * 1.05, pos, axis, acier, 14, name='entretoise'))


purge = []    # vis de purge : avant (étriers) puis arrière (cylindres de roue), un seul jeu

# =====================================================================================
# TRAIN AVANT (planche 18) : triangles, rotules, tirant de chasse, porte-fusée, moyeu, roulements
# =====================================================================================
tri = Part('triangles-av', (0, -0.25, 0))
rsu = Part('rotules-suspension', (0, -0.18, 0.12))
tch = Part('tirants-chasse', (0.25, -0.15, 0))
pf = Part('porte-fusee', (0, -0.15, 0.25))
mya = Part('moyeux-av', (0, 0, 0.42))
rla = Part('roulements-av', (0, 0, 0.30))
tbf = Part('barres-torsion-av', (-0.35, -0.3, 0))
amf = Part('amortisseurs-av', (0, 0.3, 0))
stab = Part('barres-stabilisatrices', (0, -0.3, 0))
fx = {k: [] for k in ('rot', 'vrot', 'axes', 'tir', 'pal', 'amo', 'plaque')}
PIV_LO = (AXLE_F - 0.13, 0.205)       # axe du bras inférieur (douille d'ancrage de la barre)
for s in (1, -1):
    z = lambda v: s * v  # noqa: E731
    # ---------------- bras inférieur (8) : tôle emboutie à bords tombés, douille d'ancrage (11)
    outline = [(AXLE_F - 0.19, 0.285), (AXLE_F - 0.07, 0.285), (AXLE_F + 0.06, 0.44), (AXLE_F + 0.045, 0.515),
               (AXLE_F - 0.045, 0.52), (AXLE_F - 0.10, 0.42), (AXLE_F - 0.19, 0.33)]
    tri.add(extrude([(x, -s * zz) for x, zz in outline], 0.005, (0, 0.212, 0), (0, 1, 0), acier_noir, 'bras-inferieur', bev=0.002))
    for (xa, za), (xb, zb) in ((outline[1], outline[2]), (outline[5], outline[6]), (outline[2], outline[3]), (outline[4], outline[5])):
        tri.add(tube([(xa, 0.199, z(za)), (xb, 0.199, z(zb))], 0.012, acier_noir, 'bord-tombe', seg=6))   # bords tombés
    for k in range(3):
        tri.add(cyl(0.013, 0.004, (AXLE_F - 0.02 + 0.03 * k, 0.2155, z(0.40 + 0.02 * k)), (0, 1, 0), tole, 16, name='trou-allegement'))
    tri.add(cyl(0.030, 0.13, (PIV_LO[0], PIV_LO[1], z(0.30)), (1, 0, 0), acier_noir, 28, name='douille-ancrage'))
    bush(tri, (PIV_LO[0], PIV_LO[1], z(0.30)), (1, 0, 0), 0.012, 0.031, 0.13, sleeve=False)
    tri.add(cyl(0.012, 0.24, (PIV_LO[0] + 0.03, PIV_LO[1], z(0.30)), (1, 0, 0), acier, 14, name='axe-bras-inferieur'))
    for x in (AXLE_F + 0.02, AXLE_F + 0.065):   # chape d'amortisseur
        tri.add(box((0.006, 0.045, 0.05), (x, 0.235, z(0.47)), acier_noir, 0.002, 'chape-amortisseur'))
    tri.add(box((0.05, 0.02, 0.03), (AXLE_F + 0.075, 0.215, z(0.45)), acier_noir, 0.004, 'patte-tirant'))
    tri.add(box((0.03, 0.015, 0.03), (AXLE_F - 0.07, 0.222, z(0.49)), acier_noir, 0.004, 'patte-stabilisatrice'))
    fx['axes'].append(((PIV_LO[0] + 0.155, PIV_LO[1], z(0.30)), (1, 0, 0)))
    # ---------------- bras supérieur (23) en fourche, coussinets élastiques (22), axe
    for x in (AXLE_F - 0.10, AXLE_F + 0.10):
        tri.add(tube([(x, 0.48, z(0.36)), (AXLE_F + (x - AXLE_F) * 0.45, 0.47, z(0.44)), (AXLE_F + (x - AXLE_F) * 0.15, 0.458, z(0.50))], 0.013, acier_noir, 'bras-superieur', seg=10))
        bush(tri, (x, 0.48, z(0.36)), (1, 0, 0), 0.008, 0.019, 0.045)
    tri.add(extrude(rounded_rect(0.09, 0.07, 0.025), 0.006, (AXLE_F, 0.46, z(0.505)), (0, 1, 0), acier_noir, 'platine-rotule', bev=0.002))
    tri.add(cyl(0.010, 0.27, (AXLE_F, 0.48, z(0.36)), (1, 0, 0), acier, 14, name='axe-bras-superieur'))
    fx['axes'].append(((AXLE_F + 0.135, 0.48, z(0.36)), (1, 0, 0)))
    # ---------------- rotules (9 et 19) : boîtier à 3 vis, rotule, queue conique, soufflet
    for yb, up in ((0.198, 1), (0.468, -1)):
        zc = 0.525 if up > 0 else 0.515
        tri_pl = [(0.028 * math.cos(a), 0.028 * math.sin(a)) for a in (math.radians(90 + 120 * k) for k in range(3))]
        rsu.add(extrude(rounded_rect(0.07, 0.06, 0.02), 0.004, (AXLE_F, yb, z(zc)), (0, 1, 0), acier, 'bride-rotule', bev=0.0012))
        rsu.add(lathe([(0.0, -0.016), (0.022, -0.014), (0.024, 0.0), (0.018, 0.012), (0.0, 0.014)], (AXLE_F, yb - up * 0.012, z(zc)), (0, -up, 0), acier, 24, 'boitier-rotule'))
        rsu.add(sphere(0.013, (AXLE_F, yb + up * 0.004, z(zc)), chrome, 14, 8, 'rotule'))
        rsu.add(lathe([(0.012, 0.0), (0.019, 0.004), (0.016, 0.012), (0.009, 0.020), (0.007, 0.022)], (AXLE_F, yb + up * 0.004, z(zc)), (0, up, 0), caoutchouc, 20, 'soufflet-rotule'))
        rsu.add(cyl(0.008, 0.045, (AXLE_F, yb + up * 0.03, z(zc)), (0, 1, 0), acier, 14, r2=0.006, name='queue-rotule'))
        for (u, v) in tri_pl:
            fx['rot'].append(((AXLE_F + u, yb - up * 0.003, z(zc) + v), (0, -up, 0)))
        fx['vrot'].append(((AXLE_F, yb + up * 0.052, z(zc)), (0, up, 0)))
    # ---------------- tirant de chasse : tige filetée, écrous A et B, coussinets
    t0, t1 = (AXLE_F + 0.075, 0.215, z(0.45)), (AXLE_F + 0.36, 0.40, z(0.40))
    tch.add(tube([t0, t1], 0.0085, acier_noir, 'tirant', seg=10))
    for p in (t0, t1):
        tch.add(cyl(0.016, 0.022, p, tuple(t1[i] - t0[i] for i in range(3)), caoutchouc, 18, name='coussinet-tirant'))
    tch.add(box((0.05, 0.05, 0.06), (t1[0] + 0.02, t1[1] + 0.01, t1[2]), acier_noir, 0.006, 'support-tirant'))
    dt = tuple(t1[i] - t0[i] for i in range(3))
    ln = math.sqrt(sum(c * c for c in dt))
    dt = tuple(c / ln for c in dt)
    fx['tir'] += [(tuple(t1[i] - dt[i] * 0.035 for i in range(3)), tuple(-c for c in dt)), (tuple(t1[i] + dt[i] * 0.03 for i in range(3)), dt)]
    # ---------------- porte-fusée (6) en acier forgé
    pf.add(tube([(AXLE_F, 0.232, z(0.525)), (AXLE_F - 0.012, 0.30, z(0.522)), (AXLE_F - 0.008, 0.39, z(0.516)), (AXLE_F, 0.432, z(0.515))], 0.024, forge, 'corps', seg=14))
    for yb in (0.232, 0.432):   # oeils des queues de rotules
        pf.add(cyl(0.020, 0.03, (AXLE_F, yb, z(0.522 if yb < 0.3 else 0.515)), (0, 1, 0), forge, 20, name='oeil-rotule'))
    pf.add(lathe([(0.031, -0.026), (0.046, -0.026), (0.050, -0.018), (0.050, 0.020), (0.046, 0.025), (0.031, 0.025)], (AXLE_F, WR, z(0.548)), (0, 0, s), forge, 40, 'logement-roulements'))
    pf.add(tube([(AXLE_F + 0.03, 0.40, z(0.515)), (AXLE_F + 0.08, 0.47, z(0.505)), (AXLE_F + 0.12, 0.545, z(0.50)), (AXLE_F + 0.13, 0.56, z(0.50))], 0.011, forge, 'levier-direction', seg=10))
    pf.add(cyl(0.016, 0.024, (AXLE_F + 0.13, 0.555, z(0.50)), (0, 1, 0), forge, 18, name='oeil-direction'))
    TH = math.radians(135)    # position de l'étrier : en haut, vers l'arrière
    pf.add(zslab(sector(AXLE_F, WR, 0.045, 0.085, TH - 0.62, TH + 0.62, 10), z(0.517) - 0.005, z(0.517) + 0.005, forge, 'pattes-chape'))
    pf.add(zslab(sector(AXLE_F, WR, 0.108, 0.120, TH + 0.75, TH + 2 * math.pi - 0.75, 30), z(0.537) - 0.0008, z(0.537) + 0.0008, tole, 'protecteur-disque'))
    pf.add(zslab(sector(AXLE_F, WR, 0.050, 0.110, TH + 0.75, TH + 0.80, 2), z(0.531), z(0.537), tole, 'protecteur-bord'))
    pf.add(cyl(0.040, 0.003, (AXLE_F, WR, z(0.5205)), (0, 0, 1), acier_noir, 32, name='plaque-fermeture'))
    for k in range(3):
        a = math.radians(30 + 120 * k)
        fx['plaque'].append(((AXLE_F + 0.034 * math.cos(a), WR + 0.034 * math.sin(a), z(0.519)), (0, 0, -s)))
    # ---------------- roulements (2 × 30 × 62 × 16), entretoise, joint, graisse
    for zc in (0.534, 0.562):
        rla.add(ball_bearing(0.015, 0.031, 0.016, (AXLE_F, WR, z(zc)), (0, 0, 1), acier, chrome))
    rla.add(lathe([(0.017, -0.006), (0.021, -0.006), (0.021, 0.006), (0.017, 0.006)], (AXLE_F, WR, z(0.548)), (0, 0, 1), acier, 28, 'entretoise'))
    rla.add(lathe([(0.021, -0.006), (0.029, -0.006), (0.029, 0.006), (0.021, 0.006)], (AXLE_F, WR, z(0.548)), (0, 0, 1), graisse, 24, 'graisse'))
    rla.add(lathe([(0.016, -0.002), (0.031, -0.002), (0.031, 0.002), (0.016, 0.002)], (AXLE_F, WR, z(0.5715)), (0, 0, 1), caoutchouc, 28, 'joint-etancheite'))
    # ---------------- moyeu (1) : fût dans les roulements, bride, 3 goujons (entraxe 130), cannelures
    mya.add(lathe([(0.0105, -0.03), (0.015, -0.03), (0.015, 0.022), (0.022, 0.022), (0.024, 0.024), (0.075, 0.024), (0.075, 0.030),
                   (0.032, 0.030), (0.030, 0.042), (0.0105, 0.042)], (AXLE_F, WR, z(0.548)), (0, 0, s), acier, 48, 'moyeu'))
    mya.add(splined(0.0105, 0.07, (AXLE_F, WR, z(0.553)), (0, 0, 1), acier_noir, 22, 'cannelures-moyeu'))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        p = (AXLE_F + 0.065 * math.cos(a), WR + 0.065 * math.sin(a))
        mya.add(cyl(0.006, 0.045, (p[0], p[1], z(0.594)), (0, 0, 1), zinc, 12, name='goujon'))
        mya.add(cyl(0.0085, 0.004, (p[0], p[1], z(0.5705)), (0, 0, 1), zinc, 14, name='tete-goujon'))
    mya.add(cyl(0.014, 0.003, (AXLE_F, WR, z(0.592)), (0, 0, 1), acier, 6, name='rondelle-fusee'))
    # ---------------- barre de torsion (13) : Ø 16,54 × 1 106 mm, cannelures (20 et 21 crans),
    # empreintes pyramidales (2 à gauche, 3 à droite), palier arrière (15), levier et came (16)
    x0b, x1b = PIV_LO[0] - 0.06, PIV_LO[0] - 0.06 - 1.106
    yb0, yb1 = PIV_LO[1], 0.235
    tbf.add(tube([(x0b, yb0, z(0.30)), (x1b, yb1, z(0.305))], 0.00827, vert, 'barre', seg=10))
    tbf.add(splined(0.0098, 0.05, (x0b + 0.045, yb0, z(0.30)), (1, 0, 0), vert, 20, 'cannelures-avant'))
    tbf.add(splined(0.0098, 0.04, (x1b + 0.01, yb1, z(0.305)), (1, 0, 0), vert, 21, 'cannelures-arriere'))
    for k in range(3 if s > 0 else 2):
        tbf.add(cyl(0.004, 0.004, (x0b - 0.03 - 0.012 * k, yb0 + 0.0095, z(0.30)), (0, 1, 0), pastille, 4, r2=0.0005, name='empreinte'))
    tbf.add(box((0.012, 0.004, 0.004), (x0b - 0.08, yb0 + 0.0085, z(0.30)), pastille, name='trait-couleur'))
    tbf.add(extrude([(-0.030, 0.0), (0.030, 0.0), (0.024, -0.075), (-0.012, -0.075)], 0.012, (x1b + 0.012, yb1, z(0.305)), (1, 0, 0), acier_noir, 'levier-reglage', bev=0.003, up=(0, 1, 0)))
    tbf.add(cyl(0.013, 0.012, (x1b + 0.012, yb1, z(0.305)), (1, 0, 0), acier_noir, 20, name='moyeu-levier'))
    tbf.add(cyl(0.017, 0.016, (x1b + 0.035, yb1 - 0.065, z(0.33)), (1, 0, 0), acier, 20, name='came-reglage'))
    tbf.add(box((0.045, 0.075, 0.10), (x1b - 0.01, yb1 + 0.005, z(0.31)), acier_noir, 0.008, 'palier-ancrage'))
    tbf.add(cyl(0.022, 0.003, (x1b + 0.03, 0.372, z(0.33)), (0, 1, 0), caoutchouc, 20, name='obturateur'))
    tbf.add(box((0.06, 0.012, 0.07), (x1b + 0.02, yb1 - 0.085, z(0.31)), tole, 0.003, 'carter-protection'))
    fx['pal'] += [((x1b - 0.01, yb1 + 0.045, z(0.28)), (0, 1, 0)), ((x1b - 0.01, yb1 + 0.045, z(0.34)), (0, 1, 0)), ((x1b + 0.035, yb1 + 0.04, z(0.33)), (0, 1, 0))]
    # ---------------- amortisseur (36) : corps, cache-poussière, tige, butée, empilage supérieur 37-44
    a0, a1 = (AXLE_F + 0.042, 0.235, z(0.47)), (AXLE_F + 0.16, 0.62, z(0.45))
    d = tuple(a1[i] - a0[i] for i in range(3))
    at = lambda f: tuple(a0[i] + d[i] * f for i in range(3))  # noqa: E731
    amf.add(cyl(0.021, 0.025, a0, (1, 0, 0), jaune, 20, name='oeil-inferieur'))
    bush(amf, a0, (1, 0, 0), 0.006, 0.016, 0.04, sleeve=False)
    amf.add(tube([at(0.06), at(0.58)], 0.021, jaune, 'corps', seg=18))
    amf.add(tube([at(0.56), at(0.84)], 0.0235, noir, 'cache-poussiere', seg=18))
    amf.add(tube([at(0.82), at(1.0)], 0.007, chrome, 'tige', seg=10))
    amf.add(cyl(0.018, 0.022, at(0.86), d, caoutchouc, 18, name='butee-choc'))
    for f, r, mat, nm in ((0.905, 0.019, acier, 'coupelle'), (0.925, 0.016, caoutchouc, 'silentbloc-inf'), (0.965, 0.016, caoutchouc, 'silentbloc-sup'), (0.985, 0.019, acier, 'coupelle')):
        amf.add(cyl(r, 0.008 if mat is acier else 0.012, at(f), d, mat, 20, name=nm))
    fx['amo'] += [((AXLE_F + 0.075, 0.235, z(0.47)), (1, 0, 0)), (tuple(a1[i] + d[i] * 0.03 for i in range(3)), (0, 1, 0))]
    # ---------------- barre stabilisatrice : biellettes sur les triangles inférieurs
    stab.add(tube([(AXLE_F - 0.07, 0.226, z(0.49)), (AXLE_F - 0.07, 0.26, z(0.49))], 0.006, acier, 'biellette-stab', seg=8))
    stab.add(cyl(0.012, 0.015, (AXLE_F - 0.07, 0.26, z(0.49)), (0, 0, 1), caoutchouc, 16, name='coussinet-stab'))
stab.add(tube([(AXLE_F - 0.07, 0.262, 0.49), (AXLE_F - 0.12, 0.27, 0.42), (AXLE_F - 0.15, 0.285, 0.30), (AXLE_F - 0.15, 0.285, 0.0),
               (AXLE_F - 0.15, 0.285, -0.30), (AXLE_F - 0.12, 0.27, -0.42), (AXLE_F - 0.07, 0.262, -0.49)], 0.006, acier_noir, 'barre-stab', seg=10, res=10))
stab_fx = []
for s in (1, -1):
    stab.add(cyl(0.013, 0.035, (AXLE_F - 0.15, 0.285, s * 0.30), (0, 0, 1), caoutchouc, 18, name='palier-stab'))
    stab.add(extrude([(-0.022, -0.016), (0.022, -0.016), (0.022, 0.0), (0.012, 0.016), (-0.012, 0.016), (-0.022, 0.0)], 0.03, (AXLE_F - 0.15, 0.29, s * 0.30), (0, 0, 1), acier_noir, 'bride-stab', bev=0.002, up=(0, 1, 0)))
    stab_fx += [((AXLE_F - 0.172, 0.31, s * 0.30), (0, 1, 0)), ((AXLE_F - 0.128, 0.31, s * 0.30), (0, 1, 0))]

fasteners(rsu, 'vis-rotules-suspension', fx['rot'], r=0.0055, length=0.02, travel=0.03)
fasteners(rsu, 'ecrous-rotules', fx['vrot'], kind='nut', r=0.009, length=0.03, travel=0.05)
fasteners(tri, 'ecrous-axes-bras-av', fx['axes'], kind='nut', r=0.010, length=0.03, travel=0.05)
fasteners(tch, 'ecrous-tirant-chasse', fx['tir'], kind='nut', r=0.009, length=0.02, travel=0.04, washer=False)
fasteners(tbf, 'vis-palier-torsion', fx['pal'], r=0.008, length=0.035, travel=0.05)
fasteners(amf, 'fix-amortisseurs-av', fx['amo'], kind='nut', r=0.008, length=0.03, travel=0.04)
fasteners(pf, 'vis-plaque-fermeture', fx['plaque'], kind='screw', r=0.0045, length=0.012, travel=0.025)
fasteners(stab, 'vis-paliers-stab', stab_fx, r=0.0055, length=0.025, travel=0.04)
fasteners(mya, 'ecrou-fusee-av', [((AXLE_F, WR, s * 0.596), (0, 0, s)) for s in (1, -1)], kind='nut', r=0.015, length=0.03, travel=0.06)

# =====================================================================================
# FREINS AVANT DBA (p.83) : disque, chape, étrier coulissant, piston, plaquettes, clavettes
# =====================================================================================
dsk = Part('disques-av', (0, 0, 0.35))
etr = Part('etriers-av', (0, 0.15, 0.55))
plq = Part('plaquettes-av', (0, 0.22, 0.42))
cla = []
chape_fx = []
for s in (1, -1):
    z = lambda v: s * v  # noqa: E731
    C = (AXLE_F, WR)
    # disque Ø 228 × 10 et son bol, serré entre bride de moyeu et roue
    dsk.add(lathe([(0.068, -0.005), (0.114, -0.005), (0.114, 0.005), (0.074, 0.005), (0.074, 0.030), (0.070, 0.037),
                   (0.034, 0.037), (0.034, 0.030), (0.068, 0.030)], (AXLE_F, WR, z(0.548)), (0, 0, s), disque_m, 72, 'disque'))
    for zz in (0.5428, 0.5532):   # pistes de friction (sillons d'usure)
        dsk.add(torus(0.095, 0.0006, (AXLE_F, WR, z(zz)), (0, 0, 1), M('disque-piste', 0xa7adb3, 0.95, 0.25), 64, 4, 'sillon'))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        dsk.add(torus(0.0075, 0.0015, (AXLE_F + 0.065 * math.cos(a), WR + 0.065 * math.sin(a), z(0.5855)), (0, 0, 1), disque_m, 14, 5, 'trou-goujon'))
    # chape (23) boulonnée au porte-fusée, à cheval sur le disque
    for sg in (1, -1):
        a = TH + sg * 0.47
        etr.add(zslab(sector(*C, 0.074, 0.128, a - 0.05, a + 0.05, 3), z(0.514), z(0.578), acier_noir, 'chape'))
    etr.add(zslab(sector(*C, 0.060, 0.080, TH - 0.53, TH + 0.53, 10), z(0.512), z(0.522), acier_noir, 'chape-base'))
    for sg in (1, -1):
        chape_fx.append((polar(C, 0.068, TH + sg * 0.42, z(0.508)), (0, 0, -s)))
    # étrier (34) : côté cylindre, pont au-dessus du disque, doigts extérieurs
    etr.add(zslab(sector(*C, 0.074, 0.124, TH - 0.40, TH + 0.40, 10), z(0.507), z(0.5275), fonte_frein, 'etrier-cylindre', 0.003))
    etr.add(zslab(sector(*C, 0.116, 0.131, TH - 0.31, TH + 0.31, 8), z(0.507), z(0.574), fonte_frein, 'etrier-pont', 0.003))
    etr.add(zslab(sector(*C, 0.086, 0.124, TH - 0.33, TH + 0.33, 8), z(0.5675), z(0.5745), fonte_frein, 'etrier-doigts', 0.002))
    etr.add(zslab(sector(*C, 0.098, 0.112, TH - 0.06, TH + 0.06, 2), z(0.5675) - 0.001, z(0.5745) + 0.001, acier_noir, 'fente-etrier'))
    pc = polar(C, 0.095, TH, 0)
    etr.add(cyl(0.0225, 0.010, (pc[0], pc[1], z(0.527)), (0, 0, 1), chrome, 32, name='piston'))   # piston Ø 45 (25)
    etr.add(torus(0.024, 0.0025, (pc[0], pc[1], z(0.529)), (0, 0, 1), caoutchouc, 32, 8, 'pare-poussiere'))   # (27)
    etr.add(torus(0.0228, 0.0012, (pc[0], pc[1], z(0.518)), (0, 0, 1), caoutchouc, 32, 6, 'joint-piston'))   # (26)
    etr.add(cyl(0.010, 0.010, (pc[0], pc[1], z(0.503)), (0, 0, 1), fonte_frein, 20, name='bossage-raccord'))
    etr.add(tube([polar(C, 0.13, TH - 0.31, z(0.541)), polar(C, 0.134, TH, z(0.541)), polar(C, 0.13, TH + 0.31, z(0.541))], 0.0012, ressort, 'ressort-epingle'))   # (21)
    # flexible : de l'étrier à la patte sur la caisse, raccords sertis
    f0 = (pc[0], pc[1], z(0.498))
    etr.add(tube([f0, (pc[0] - 0.02, pc[1] + 0.03, z(0.47)), (AXLE_F - 0.17, 0.47, z(0.43)), (AXLE_F - 0.20, 0.50, z(0.40))], 0.0045, caoutchouc, 'flexible', seg=8, res=10))
    etr.add(extrude([(-0.007 * math.cos(a), 0.007 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]], 0.010, f0, (0, 0, 1), laiton, 'raccord-flexible'))
    etr.add(box((0.03, 0.004, 0.03), (AXLE_F - 0.20, 0.50, z(0.40)), acier_noir, 0.002, 'patte-flexible'))
    etr.add(cyl(0.0045, 0.01, (pc[0], pc[1], z(0.5025)), (0, 0, 1), cuivre, 14, name='joint-cuivre'))
    # clavettes (28) et épingles, entre étrier et chape
    for sg in (1, -1):
        cla.append((polar(C, 0.101, TH + sg * 0.415, z(0.586)), (0, 0, s)))
    purge.append((polar(C, 0.122, TH + 0.18, z(0.512)), (math.cos(TH + 0.18), math.sin(TH + 0.18), 0)))
    # plaquettes (20) : garniture + support acier, ressorts d'appui (22)
    for zf, zb, nm in ((0.5325, 0.529, 'int'), (0.5635, 0.567, 'ext')):
        plq.add(zslab(sector(*C, 0.078, 0.113, TH - 0.36, TH + 0.36, 10), z(zf) - 0.005, z(zf) + 0.005, garniture, 'garniture-' + nm, 0.0012))
        plq.add(zslab(sector(*C, 0.076, 0.116, TH - 0.40, TH + 0.40, 10), z(zb) - 0.00175, z(zb) + 0.00175, acier, 'support-' + nm))
        plq.add(zslab(sector(*C, 0.0945, 0.0955, TH - 0.36, TH + 0.36, 8), z(zf) - 0.0052, z(zf) + 0.0052, acier_noir, 'rainure-' + nm))
        plq.add(tube([polar(C, 0.074, TH - 0.30, z(zb)), polar(C, 0.071, TH, z(zb)), polar(C, 0.074, TH + 0.30, z(zb))], 0.0009, ressort, 'ressort-appui'))
fasteners(etr, 'clavettes-dba', cla, kind='pin', r=0.0035, length=0.08, travel=0.10)
fasteners(etr, 'vis-chape-etrier', chape_fx, r=0.0075, length=0.03, travel=0.05)

# =====================================================================================
# DIRECTION À CRÉMAILLÈRE (planche 17, p.51 à 54)
# =====================================================================================
dr = Part('direction', (0, 0.25, 0))
bdr = Part('biellettes-direction', (0, 0.12, 0))
RX, RY = 1.43, 0.575
ZB = 0.22                      # demi-longueur du boîtier
ZP = -0.12                     # pignon côté conducteur
dr.add(cyl(0.022, 2 * ZB, (RX, RY, 0), (0, 0, 1), alu, 28, name='boitier'))
for zz in (-ZB + 0.012, ZB - 0.012, 0.10):
    dr.add(torus(0.0225, 0.0025, (RX, RY, zz), (0, 0, 1), alu, 28, 6, 'nervure'))
dr.add(cyl(0.030, 0.03, (RX, RY, ZB - 0.015), (0, 0, 1), alu, 28, name='logement-palier-antibruit'))
dr.add(circlip(0.016, (RX, RY, ZB + 0.001), (0, 0, 1), acier))
dr.add(cyl(0.034, 0.075, (RX, RY, ZP), (0, 0, 1), alu, 28, name='carter-pignon'))
PAX = (-0.55, 0.80, -0.20)     # axe du pignon, vers la colonne
pl_ = math.sqrt(sum(c * c for c in PAX))
PAX = tuple(c / pl_ for c in PAX)
pp = lambda f: (RX + PAX[0] * f, RY + PAX[1] * f, ZP + PAX[2] * f)  # noqa: E731
dr.add(cyl(0.024, 0.05, pp(0.03), PAX, alu, 24, name='fut-pignon'))
dr.add(cyl(0.010, 0.05, pp(0.07), PAX, acier, 14, name='arbre-pignon'))
dr.add(splined(0.009, 0.02, pp(0.085), PAX, acier_noir, 18))
dr.add(cyl(0.020, 0.004, pp(0.056), PAX, acier_noir, 24, name='bouchon-fermeture'))
# poussoir (Delrin), ressort, rondelle élastique et cales sous couvercle à 2 vis (p.52)
POU = (0.62, -0.78, 0.0)
pou_l = math.sqrt(sum(c * c for c in POU))
POU = tuple(c / pou_l for c in POU)
po = lambda f: (RX + POU[0] * f, RY + POU[1] * f, ZP + 0.005 + POU[2] * f)  # noqa: E731
dr.add(cyl(0.019, 0.035, po(0.035), POU, alu, 24, name='logement-poussoir'))
dr.add(extrude(rounded_rect(0.05, 0.028, 0.008), 0.004, po(0.054), POU, alu, 'couvercle-poussoir', bev=0.001, up=(0, 0, 1)))
dr.add(cyl(0.012, 0.016, po(0.022), POU, delrin, 20, name='poussoir'))
dr.add(spring(po(0.031), po(0.050), 0.007, 0.0009, 4))
dr.add(cyl(0.013, 0.002, po(0.051), POU, ressort, 20, name='cales-reglage'))
# crémaillère (visible en transparence) : tige, denture face au pignon, pignon taillé
dr.add(cyl(0.0105, 0.60, (RX, RY, 0), (0, 0, 1), chrome, 20, name='cremaillere'))
for k in range(16):
    dr.add(box((0.012, 0.003, 0.0022), (RX - 0.004, RY + 0.009, ZP - 0.032 + k * 0.004), acier_noir, name='denture'))
dr.add(toothed(9, 0.0085, 0.022, (RX, RY + 0.018, ZP), PAX, acier_noir, helix=math.radians(20), name='pignon'))
dr.add(ball_bearing(0.006, 0.016, 0.010, pp(0.035), PAX, acier, chrome))                   # 12 × 32 × 10
dr.add(lathe([(0.010, -0.007), (0.013, -0.007), (0.013, 0.007), (0.010, 0.007)], (RX, RY - 0.006, ZP), PAX, acier, 20, 'roulement-aiguilles'))   # 20 × 26 × 14
# brides de fixation et cales de calage (n° 1 à 7, 8,9 à 14,9 mm, p.62)
fixd = []
for zz in (0.17, -0.17):
    dr.add(extrude([(-0.03, -0.028), (0.03, -0.028), (0.03, 0.004), (0.02, 0.026), (-0.02, 0.026), (-0.03, 0.004)], 0.035, (RX, RY - 0.005, zz), (0, 0, 1), acier_noir, 'bride', bev=0.002, up=(0, 1, 0)))
    dr.add(box((0.07, 0.0119, 0.04), (RX, RY - 0.040, zz), M('cale-direction', 0x8b8f6a, 0.6, 0.4), 0.0015, 'cale-calage'))
    fixd += [((RX - 0.02, RY - 0.025, zz), (0, 1, 0)), ((RX + 0.02, RY - 0.025, zz), (0, 1, 0))]
fasteners(dr, 'fix-direction', fixd, r=0.008, length=0.045, travel=0.05)
fasteners(dr, 'vis-couvercle-poussoir', [(tuple(po(0.057)[i] + (0, 0, 0.018)[i] for i in range(3)), POU), (tuple(po(0.057)[i] - (0, 0, 0.018)[i] for i in range(3)), POU)], r=0.004, length=0.015, travel=0.025)
# joint souple (flector, 18) avec cale caoutchouc, axe intermédiaire, cardan
fl = pp(0.105)
dr.add(cyl(0.034, 0.012, fl, PAX, caoutchouc, 28, name='flector'))
dr.add(cyl(0.014, 0.004, tuple(fl[i] + PAX[i] * 0.008 for i in range(3)), PAX, acier_noir, 16, name='rivet-flector'))
for sg in (1, -1):
    dr.add(box((0.05, 0.006, 0.012), tuple(fl[i] + PAX[i] * sg * 0.009 for i in range(3)), acier_noir, 0.002, 'bride-flector', axis=PAX))
c1 = tuple(fl[i] + PAX[i] * 0.02 for i in range(3))
dr.add(tube([c1, (1.12, 0.73, -0.23), (0.97, 0.76, -0.29)], 0.011, acier_noir, 'axe-intermediaire', seg=10))
dr.add(box((0.03, 0.03, 0.03), (0.95, 0.765, -0.30), acier_noir, 0.005, 'cardan-direction'))
fasteners(dr, 'ecrou-flector', [(tuple(fl[i] + PAX[i] * 0.02 + (0.022, 0, 0)[i] for i in range(3)), PAX), (tuple(fl[i] + PAX[i] * 0.02 - (0.022, 0, 0)[i] for i in range(3)), PAX)], kind='nut', r=0.006, length=0.02, travel=0.03)
# soufflets, embouts (28) vissés + contre-écrous (27), oeils, biellettes (1), rotules
emb = []
rot_d = []
for s in (1, -1):
    z = lambda v: s * v  # noqa: E731
    dr.add(lathe([(0.023, 0.0), (0.031, 0.008), (0.022, 0.016), (0.031, 0.024), (0.022, 0.032), (0.031, 0.040), (0.022, 0.048), (0.028, 0.056), (0.011, 0.068), (0.011, 0.074)], (RX, RY, z(ZB)), (0, 0, s), caoutchouc, 28, 'soufflet'))
    for zz in (ZB + 0.004, ZB + 0.072):
        dr.add(torus(0.023 if zz < ZB + 0.01 else 0.012, 0.0015, (RX, RY, z(zz)), (0, 0, 1), zinc, 24, 6, 'collier'))
    zl = ZB + 0.0715      # cote de point milieu : 71,5 mm entre contre-écrou et boîtier (p.51)
    bdr.add(cyl(0.008, 0.035, (RX, RY, z(zl + 0.022)), (0, 0, 1), acier, 16, name='embout'))
    bdr.add(lathe([(0.0, -0.016), (0.019, -0.016), (0.019, 0.016), (0.0, 0.016)], (RX, RY, z(zl + 0.05)), (1, 0, 0), acier, 24, 'oeil-cremaillere'))
    bdr.add(cyl(0.006, 0.05, (RX, RY, z(zl + 0.05)), (1, 0, 0), acier, 12, name='axe-biellette'))
    emb.append(((RX, RY, z(zl + 0.003)), (0, 0, s)))
    b0, b1 = (RX, RY - 0.002, z(zl + 0.066)), (AXLE_F + 0.13, 0.571, z(0.488))
    bdr.add(tube([b0, b1], 0.0085, acier, 'biellette', seg=10))
    for p in (b0,):
        bdr.add(cyl(0.012, 0.016, p, (0, 0, 1), caoutchouc, 16, name='silentbloc-biellette'))
    bdr.add(lathe([(0.0, -0.012), (0.017, -0.010), (0.018, 0.004), (0.010, 0.014), (0.0, 0.016)], (AXLE_F + 0.13, 0.575, z(0.50)), (0, 1, 0), acier, 20, 'rotule-direction'))
    bdr.add(lathe([(0.008, 0.0), (0.014, 0.004), (0.010, 0.012), (0.006, 0.014)], (AXLE_F + 0.13, 0.568, z(0.50)), (0, -1, 0), caoutchouc, 16, 'soufflet-rotule'))
    rot_d.append(((AXLE_F + 0.13, 0.535, z(0.50)), (0, -1, 0)))
fasteners(bdr, 'contre-ecrous-embouts', emb, kind='nut', r=0.010, length=0.012, travel=0.03, washer=False)
fasteners(bdr, 'ecrous-rotules-direction', rot_d, kind='nut', r=0.0085, length=0.025, travel=0.04)

# =====================================================================================
# TRAIN ARRIÈRE (planche 19) : bras tirés, paliers, barres de torsion, amortisseurs, moyeux
# =====================================================================================
bra = Part('bras-ar', (0, -0.25, 0))
tbr = Part('barres-torsion-ar', (0, -0.35, 0))
amr = Part('amortisseurs-ar', (0, 0.2, 0))
tam = Part('tambours-ar', (0, 0, 0.4))
rlr = Part('roulements-ar', (0, 0, 0.30))
mac = Part('machoires-ar', (0, 0.0, 0.22))
cyr = Part('cylindres-roue', (0, 0.12, 0.16))
fxr = {k: [] for k in ('pal', 'came', 'amo', 'fus', 'gou', 'cyl', 'cav')}
for s in (1, -1):
    z = lambda v: s * v  # noqa: E731
    x0, xp = AXLE_R[s], PIVOT_R[s]
    C = (x0, WR)
    # tube d'articulation (11), paliers intérieur (23) et extérieur (22) à 3 vis
    bra.add(cyl(0.032, 0.30, (xp, 0.275, z(0.41)), (0, 0, 1), acier_noir, 28, name='tube-articulation'))
    for zz in (0.285, 0.535):
        bra.add(cyl(0.040, 0.035, (xp, 0.275, z(zz)), (0, 0, 1), caoutchouc, 24, name='coussinet'))
        bra.add(extrude([(-0.055, 0.02), (0.055, 0.02), (0.045, 0.075), (-0.045, 0.075), (-0.05, 0.03)], 0.03, (xp, 0.275, z(zz)), (0, 0, 1), fonte_frein, 'palier', bev=0.004, up=(0, 1, 0)))
        bra.add(cyl(0.046, 0.03, (xp, 0.275, z(zz)), (0, 0, 1), fonte_frein, 28, name='collier-palier'))
        for dx in (-0.035, 0.0, 0.035):
            fxr['pal'].append(((xp + dx, 0.352, z(zz)), (0, 1, 0)))
    # bras (13) en caisson soudé, du tube à la platine de fusée
    L = abs(x0 - xp)
    bra.add(extrude([(-0.03, -0.03), (0.03, -0.032), (0.034, 0.028), (-0.028, 0.036)], L - 0.03, ((x0 + xp) / 2 + 0.015, 0.282, z(0.462)), (1, 0, 0), acier_noir, 'bras', bev=0.008, up=(0, 1, 0)))
    bra.add(box((L * 0.6, 0.004, 0.055), ((x0 + xp) / 2 + 0.03, 0.318, z(0.462)), acier_noir, 0.002, 'cordon-soudure'))
    bra.add(box((0.11, 0.11, 0.012), (x0 + 0.02, WR, z(0.497)), acier_noir, 0.006, 'platine-fusee'))
    bra.add(box((0.05, 0.08, 0.016), (x0 + 0.03, WR, z(0.484)), acier_noir, 0.004, 'gousset'))
    bra.add(box((0.03, 0.05, 0.04), (x0 + 0.06, 0.25, z(0.445)), acier_noir, 0.004, 'chape-amortisseur'))
    # fusée Ø 22 / 20 et flasque de frein (1)
    bra.add(lathe([(0.0, 0.0), (0.013, 0.0), (0.0125, 0.012), (0.011, 0.014), (0.011, 0.055), (0.010, 0.058), (0.010, 0.085), (0.0, 0.085)], (x0, WR, z(0.503)), (0, 0, s), acier, 28, 'fusee'))
    bra.add(lathe([(0.03, -0.002), (0.098, -0.002), (0.104, 0.004), (0.104, 0.012), (0.100, 0.012), (0.096, 0.004), (0.03, 0.004)], (x0, WR, z(0.505)), (0, 0, s), tole, 48, 'flasque'))
    for k in range(4):   # emboutis de renfort du flasque
        a = math.radians(45 + 90 * k)
        bra.add(box((0.03, 0.03, 0.003), (x0 + 0.06 * math.cos(a), WR + 0.06 * math.sin(a), z(0.509)), tole, 0.004, 'embouti'))
    bra.add(box((0.022, 0.018, 0.012), (x0, WR - 0.078, z(0.515)), acier_noir, 0.003, 'point-fixe'))   # appui bas des mâchoires
    # barre de torsion (14) Ø 18,5 × 868 mm, cannelures 24 et 25 crans, levier d'ancrage (15), came (16)
    zo, zi = z(0.50), z(-0.368)
    tbr.add(tube([(xp, 0.275, zo), (xp, 0.275, zi)], 0.00925, vert, 'barre', seg=10))
    tbr.add(splined(0.0108, 0.04, (xp, 0.275, zo - s * 0.015), (0, 0, 1), vert, 24, 'cannelures-bras'))
    tbr.add(splined(0.0108, 0.035, (xp, 0.275, zi + s * 0.012), (0, 0, 1), vert, 25, 'cannelures-levier'))
    for k in range(3 if s > 0 else 2):
        tbr.add(cyl(0.004, 0.004, (xp, 0.285, zo - s * (0.06 + 0.012 * k)), (0, 1, 0), pastille, 4, r2=0.0005, name='empreinte'))
    tbr.add(extrude([(-0.024, 0.016), (0.024, 0.016), (0.02, -0.075), (-0.014, -0.075)], 0.014, (xp, 0.275, zi + s * 0.008), (0, 0, 1), acier_noir, 'levier-ancrage', bev=0.003, up=(0, 1, 0)))
    tbr.add(cyl(0.017, 0.014, (xp, 0.275, zi + s * 0.008), (0, 0, 1), acier_noir, 20, name='moyeu-levier'))
    tbr.add(cyl(0.016, 0.02, (xp + 0.002, 0.190, zi + s * 0.008), (0, 0, 1), acier, 20, name='came-reglage'))
    tbr.add(box((0.08, 0.06, 0.04), (xp, 0.31, zi - s * 0.02), acier_noir, 0.008, 'support-came'))
    fxr['came'].append(((xp + 0.002, 0.190, zi - s * 0.006), (0, 0, -s)))
    # amortisseur (12) presque horizontal : fixation inférieure (arrière) sur le bras, supérieure (avant) sur la caisse
    a0, a1 = (x0 + 0.06, 0.25, z(0.445)), (x0 + 0.40, 0.335, z(0.445))
    d = tuple(a1[i] - a0[i] for i in range(3))
    at = lambda f: tuple(a0[i] + d[i] * f for i in range(3))  # noqa: E731
    amr.add(tube([at(0.06), at(0.55)], 0.020, jaune, 'corps', seg=16))
    amr.add(tube([at(0.45), at(0.80)], 0.0235, noir, 'cache-poussiere', seg=16))
    amr.add(tube([at(0.78), at(0.95)], 0.007, chrome, 'tige', seg=10))
    for p in (a0, a1):
        amr.add(cyl(0.018, 0.028, p, (0, 0, 1), jaune if p is a0 else acier_noir, 18, name='oeil'))
        bush(amr, p, (0, 0, 1), 0.006, 0.014, 0.032, sleeve=False)
    amr.add(box((0.05, 0.06, 0.05), (a1[0] + 0.01, a1[1] + 0.03, z(0.445)), acier_noir, 0.006, 'support-caisse'))
    fxr['amo'] += [((a0[0], a0[1], z(0.47)), (0, 0, s)), ((a1[0], a1[1], z(0.47)), (0, 0, s))]
    # tambour Ø 180 (17) : moyeu-tambour, ailettes, goujons, bouchon de moyeu
    tam.add(lathe([(0.024, -0.030), (0.034, -0.030), (0.034, 0.028), (0.0898, 0.028), (0.0898, -0.035), (0.099, -0.035), (0.099, 0.030),
                   (0.094, 0.038), (0.034, 0.038), (0.030, 0.050), (0.024, 0.050), (0.024, -0.030)], (x0, WR, z(0.54)), (0, 0, s), fonte_frein, 64, 'tambour'))
    for k in range(12):
        a = 2 * math.pi * k / 12
        tam.add(box((0.006, 0.006, 0.058), (x0 + 0.1005 * math.cos(a), WR + 0.1005 * math.sin(a), z(0.536)), fonte_frein, name='ailette', axis=None))
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        tam.add(cyl(0.006, 0.04, (x0 + 0.065 * math.cos(a), WR + 0.065 * math.sin(a), z(0.592)), (0, 0, 1), zinc, 10, name='goujon'))
    tam.add(lathe([(0.0, 0.016), (0.022, 0.014), (0.0245, 0.0), (0.0245, -0.006), (0.0225, -0.006)], (x0, WR, z(0.592)), (0, 0, s), acier, 24, 'bouchon-moyeu'))
    # roulements coniques : intérieur 22 × 47 × 20,75, extérieur 20 × 47 × 15,2, joint 25 × 52
    rlr.add(roller_bearing(0.011, 0.0235, 0.0208, (x0, WR, z(0.530)), (0, 0, -s), acier, chrome))
    rlr.add(roller_bearing(0.010, 0.0235, 0.0152, (x0, WR, z(0.566)), (0, 0, s), acier, chrome))
    rlr.add(lathe([(0.0125, -0.003), (0.026, -0.003), (0.026, 0.003), (0.0125, 0.003)], (x0, WR, z(0.515)), (0, 0, 1), caoutchouc, 28, 'joint-etancheite'))
    rlr.add(lathe([(0.0115, -0.006), (0.0235, -0.006), (0.0235, 0.006), (0.0115, 0.006)], (x0, WR, z(0.548)), (0, 0, 1), graisse, 24, 'graisse'))
    rlr.add(cyl(0.017, 0.003, (x0, WR, z(0.5755)), (0, 0, 1), acier, 6, name='rondelle-appui'))
    rlr.add(extrude([(0.016 * math.cos(math.radians(30 * k)) * (1 if k % 2 else 0.8), 0.016 * math.sin(math.radians(30 * k)) * (1 if k % 2 else 0.8)) for k in range(12)], 0.006, (x0, WR, z(0.584)), (0, 0, 1), acier, 'frein-ecrou'))
    fxr['fus'].append(((x0, WR, z(0.579)), (0, 0, s)))
    fxr['gou'].append(((x0, WR + 0.012, z(0.584)), (0, 1, 0)))
    # mâchoires (3, 14) et garnitures, ressorts de rappel, barre et levier de frein à main,
    # dispositif à crans de rattrapage (4, 6), cavaliers de maintien
    for side, a_c in ((1, 0.0), (-1, math.pi)):          # side +1 : mâchoire avant (vers +x)
        a0_, a1_ = a_c - math.radians(68), a_c + math.radians(68)
        mac.add(zslab(sector(*C, 0.0845, 0.0857, a0_, a1_, 18), z(0.512), z(0.542), machoire_m, 'table'))
        mac.add(zslab(sector(*C, 0.062, 0.0845, a0_, a1_, 18), z(0.5255), z(0.5285), machoire_m, 'ame'))
        ga0, ga1 = a_c - math.radians(55 if side > 0 else 62), a_c + math.radians(55 if side > 0 else 62)   # garniture la plus courte vers l'arrière... avant ici
        mac.add(zslab(sector(*C, 0.0857, 0.0896, ga0, ga1, 16), z(0.5135), z(0.5405), garniture, 'garniture', 0.0008))
        for k in range(4):   # rivets
            a = ga0 + (ga1 - ga0) * (k + 0.5) / 4
            mac.add(cyl(0.0022, 0.0012, polar(C, 0.0895, a, z(0.527)), (math.cos(a), math.sin(a), 0), laiton, 8, name='rivet'))
        cav = polar(C, 0.072, a_c, z(0.527))
        fxr['cav'].append(((cav[0], cav[1], z(0.535)), (0, 0, s)))
        mac.add(spring((cav[0], cav[1], z(0.531)), (cav[0], cav[1], z(0.545)), 0.0045, 0.0007, 4))
    up_ = lambda dx, dy, zz: (x0 + dx, WR + dy, z(zz))  # noqa: E731
    mac.add(spring(up_(-0.040, 0.062, 0.531), up_(0.040, 0.062, 0.531), 0.0035, 0.0009, 12, ressort, 'ressort-rappel-sup'))
    mac.add(spring(up_(-0.035, -0.068, 0.531), up_(0.035, -0.068, 0.531), 0.0035, 0.0009, 10, ressort, 'ressort-rappel-inf'))
    mac.add(zslab([(x0 - 0.062, WR + 0.040), (x0 + 0.058, WR + 0.040), (x0 + 0.058, WR + 0.050), (x0 - 0.062, WR + 0.050)], z(0.519), z(0.523), acier, 'barre-frein-main'))
    mac.add(zslab([(x0 - 0.064, WR + 0.050), (x0 - 0.056, WR + 0.052), (x0 - 0.046, WR - 0.060), (x0 - 0.054, WR - 0.062)], z(0.5225), z(0.5255), acier_noir, 'levier-frein-main'))
    mac.add(zslab(sector(x0 + 0.052, WR + 0.045, 0.006, 0.018, math.radians(60), math.radians(200), 8), z(0.5195), z(0.5225), acier, 'secteur-cranté'))
    for k in range(7):
        a = math.radians(60 + 20 * k)
        mac.add(box((0.0025, 0.0025, 0.003), (x0 + 0.052 + 0.0185 * math.cos(a), WR + 0.045 + 0.0185 * math.sin(a), z(0.521)), acier, name='cran'))
    mac.add(spring(up_(0.052, 0.045, 0.524), up_(0.062, 0.010, 0.524), 0.0022, 0.0006, 6, ressort, 'ressort-rattrapage'))
    mac.add(tube([up_(-0.05, -0.058, 0.519), up_(-0.03, -0.085, 0.505), up_(0.02, -0.10, 0.49)], 0.0025, M('cable', 0x2a2a2a, 0.3, 0.6), 'cable-frein-main', seg=6))
    # cylindre de roue (20) Ø 20,6 : corps, pistons, coupelles, ressort, capuchons, vis de purge
    cyc = (x0, WR + 0.074, z(0.524))
    cyr.add(cyl(0.0125, 0.052, cyc, (1, 0, 0), fonte_frein, 20, name='corps'))
    cyr.add(box((0.03, 0.022, 0.012), (x0, WR + 0.074, z(0.512)), fonte_frein, 0.003, 'embase'))
    for sg in (1, -1):
        cyr.add(lathe([(0.0, 0.0), (0.0128, 0.0), (0.0135, 0.004), (0.010, 0.010), (0.006, 0.012), (0.0, 0.012)], (x0 + sg * 0.026, WR + 0.074, z(0.524)), (sg, 0, 0), caoutchouc, 18, 'capuchon'))
        cyr.add(cyl(0.0103, 0.012, (x0 + sg * 0.018, WR + 0.074, z(0.524)), (1, 0, 0), alu, 18, name='piston'))
        cyr.add(cyl(0.0104, 0.003, (x0 + sg * 0.010, WR + 0.074, z(0.524)), (1, 0, 0), caoutchouc, 18, name='coupelle'))
        cyr.add(box((0.006, 0.010, 0.010), (x0 + sg * 0.034, WR + 0.074, z(0.524)), acier, 0.001, 'poussoir-machoire'))
    cyr.add(spring((x0 - 0.008, WR + 0.074, z(0.524)), (x0 + 0.008, WR + 0.074, z(0.524)), 0.006, 0.0006, 4))
    cyr.add(tube([(x0 + 0.004, WR + 0.074, z(0.505)), (x0 + 0.004, WR + 0.074, z(0.49)), (x0 + 0.05, WR + 0.075, z(0.488))], 0.0028, cuivre, 'canalisation', seg=6))
    fxr['cyl'] += [((x0 - 0.010, WR + 0.074, z(0.499)), (0, 0, -s)), ((x0 + 0.010, WR + 0.074, z(0.499)), (0, 0, -s))]
    purge.append(((x0 - 0.012, WR + 0.082, z(0.498)), (0, 0, -s)))
    # flexible arrière entre caisse et bras
    cyr.add(tube([(x0 + 0.20, 0.335, z(0.44)), (x0 + 0.14, 0.32, z(0.465)), (x0 + 0.06, 0.33, z(0.47))], 0.0045, caoutchouc, 'flexible-ar', seg=8))
fasteners(bra, 'vis-paliers-bras-ar', fxr['pal'], r=0.007, length=0.035, travel=0.05)
fasteners(tbr, 'ecrous-cames-ar', fxr['came'], kind='nut', r=0.009, length=0.02, travel=0.04)
fasteners(amr, 'fix-amortisseurs-ar', fxr['amo'], kind='nut', r=0.008, length=0.03, travel=0.04)
fasteners(rlr, 'ecrou-fusee-ar', fxr['fus'], kind='nut', r=0.013, length=0.02, travel=0.06)
fasteners(rlr, 'goupilles-fusee-ar', fxr['gou'], kind='pin', r=0.0015, length=0.035, travel=0.05)
fasteners(cyr, 'vis-cylindre-roue', fxr['cyl'], r=0.0045, length=0.016, travel=0.03)
fasteners(mac, 'cavaliers-machoires', fxr['cav'], kind='pin', r=0.0018, length=0.03, travel=0.04)

# vis de purge : avant (étriers) puis arrière (cylindres de roue), un seul jeu comme sur le site
for i, (p, d) in enumerate(purge):
    fastener(etr if i < 2 else cyr, 'vis-purge-freins', p, d, r=0.005, length=0.015, travel=0.008, idx=i)

export(OUT)
