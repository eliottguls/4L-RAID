# Cotes de caisse partagées (caisse.py, interieur.py, electricite.py). Repère du site : x avant,
# y haut, z droite, en mètres.
#
# Référence : MR 175 (Renault, mécanique, éd. 1983), page A-2 « Caractéristiques — Berline »
# (PDF manuels/MR175-mecanique-p001-350.pdf p.4) : empattement 2,449 m à droite / 2,401 m à
# gauche, longueur 3,668 m, voie AV 1,279 m, largeur hors tout G = 1,485 m, hauteur à vide 1,550 m.
# Les vues de profil, de face et de trois-quarts arrière de cette page, recalées à l'échelle sur
# l'empattement et la hauteur, donnent le reste : ceinture de caisse à 0,99 m, bas des vitres à
# 1,01 m, haut des vitres à 1,40 m, gouttières à 1,445 m, flancs bombés (largeur maxi entre 0,5 et
# 0,75 m du sol, 1,34 m à la ceinture) et pavillon nettement rentré (1,13 m aux gouttières),
# capot à 1,01 m au pied de pare-brise et 0,85 m à l'avant.
import math

W0 = 0.7425          # demi-largeur hors tout (G = 1 485 mm, MR 175 A-2)
BELT = 0.990         # ligne de ceinture (épaulement sous les vitres)
R_SH = 0.022         # rayon de l'épaulement de ceinture
SILL_IN = 0.032      # retrait de la ceinture vers le vitrage
Y_BOT = 0.385        # bas de caisse (dessous des portes)
Y_ROOF = 1.445       # arête du pavillon (gouttières)
CROWN = 0.100        # bombé du pavillon (sommet 1 545 mm)
ROOF_HW = 0.565      # demi-largeur du pavillon aux gouttières (vue de face MR 175 A-2)

# Section transversale du flanc sous la ceinture : demi-largeur (à plan maxi) selon la hauteur.
SECTION = [(0.30, 0.700), (0.385, 0.722), (0.45, 0.736), (0.55, 0.7425), (0.70, 0.7425),
           (0.80, 0.737), (0.88, 0.722), (0.935, 0.700), (0.990, 0.664)]

# Nervure horizontale du flanc (vue de profil A-2) : à 0,81 m sur les portes et l'aile arrière,
# descend vers l'avant sur l'aile avant (0,75 m au projecteur).
CREASE_H = 0.0028
CREASE_W = 0.010


def smooth_interp(pts, x):
    """Catmull-Rom sur une liste [(x, y)] triée."""
    n = len(pts)
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for k in range(n - 1):
        if pts[k][0] <= x <= pts[k + 1][0]:
            break
    p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, n - 1)]
    t = (x - p1[0]) / (p2[0] - p1[0])
    m1 = (p2[1] - p0[1]) / (p2[0] - p0[0]) * (p2[0] - p1[0])
    m2 = (p3[1] - p1[1]) / (p3[0] - p1[0]) * (p2[0] - p1[0])
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p1[1] + (t3 - 2 * t2 + t) * m1 + (-2 * t3 + 3 * t2) * p2[1] + (t3 - t2) * m2


def W(x):
    """Demi-largeur en plan (rétrécie à l'avant et à l'arrière)."""
    w = W0
    if x > 1.45:
        w -= 0.036 * ((x - 1.45) / 0.31) ** 2
    if x < -1.50:
        w -= 0.028 * ((-1.50 - x) / 0.27) ** 2
    return w


def crease_y(x):
    return 0.812 - 0.065 * min(max((x - 0.70) / 0.95, 0.0), 1.0)


def crease(x, y):
    d = abs(y - crease_y(x)) / CREASE_W
    return CREASE_H * max(0.0, 1.0 - d) ** 2


def zside(x, y):
    """Flanc sous la ceinture : section bombée, bas de caisse roulé vers l'intérieur, nervure."""
    return W(x) / W0 * smooth_interp(SECTION, y) + crease(x, y)


Z_GLASS0 = smooth_interp(SECTION, BELT - R_SH) - SILL_IN


def z_glass(y):
    """Flanc du pavillon (vitres, montants) : rentré de la ceinture jusqu'aux gouttières, galbé."""
    t = min(max((y - BELT) / (Y_ROOF - BELT), 0.0), 1.0)
    return Z_GLASS0 + (ROOF_HW - Z_GLASS0) * (0.70 * t + 0.30 * t * t)


def x_ws(y):
    """Arête avant du vitrage (montant de pare-brise) : 0,64 m au pied, incliné de 32°."""
    return 0.640 - (y - 1.02) * 0.63


# face arrière (profil MR 175 A-2, relevé point par point) : x selon y
REAR = [(0.30, -1.772), (0.45, -1.752), (0.513, -1.732), (0.58, -1.702), (0.68, -1.670), (0.80, -1.650),
        (0.90, -1.605), (0.97, -1.566), (1.10, -1.492), (1.165, -1.458), (1.30, -1.395), (1.40, -1.350),
        (1.445, -1.328)]


def x_rear(y):
    return smooth_interp(REAR, y)


X_ROOF_F = x_ws(Y_ROOF)              # bord avant du pavillon (haut du pare-brise)
X_ROOF_R = x_rear(Y_ROOF) + SILL_IN  # bord arrière du pavillon (haut du hayon)


def roof_y(x, z):
    """Hauteur extérieure du pavillon : bombé transversal, raccords arrondis à l'avant et à l'arrière
    (même loi que build_roof dans caisse.py)."""
    e = max(min((X_ROOF_F - x) / 0.24, (x - X_ROOF_R) / 0.30, 1.0), 0.0)
    return Y_ROOF + CROWN * max(0.0, 1 - (z / ROOF_HW) ** 2) * (3 * e ** 2 - 2 * e ** 3)
