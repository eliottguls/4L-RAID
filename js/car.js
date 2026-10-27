// Modèle 3D procédural d'une Renault 4 GTL, construit à partir des cotes et des photos de la RTA.
// Repère : x vers l'avant, y vers le haut, z vers la droite du conducteur. Unités : mètres.
// Chaque pièce est un THREE.Group portant userData.partId (clé de PARTS dans data.js)
// et userData.explode (décalage de la vue éclatée).
// Les vis, écrous et bouchons sont rangés par jeu (FASTENERS dans data.js) : chaque élément
// est enfant de sa pièce, et connaît son axe de dévissage.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const AXLE_F = 1.306;          // essieu avant (porte-à-faux 528 mm)
const AXLE_R_RIGHT = -1.143;   // empattement droit 2 449 mm
const AXLE_R_LEFT = -1.095;    // empattement gauche 2 401 mm
const TRACK_F = 0.64;
const TRACK_R = 0.624;
const WHEEL_R = 0.285;
const EX = 0.92;               // centre du bloc-moteur (moteur derrière l'essieu, boîte devant)

const C = {
  steel: 0x8f969c, darkSteel: 0x464b51, alu: 0xb7bcbf, castAlu: 0xa9aca8, black: 0x1b1c1d, rubber: 0x202122,
  chrome: 0xd9dcdf, glass: 0x9cc0d3, seat: 0x5e5148, seatFrame: 0x2b2b2b, dash: 0x2a2826, block: 0x6f7a80,
  head: 0xb3b7b8, rocker: 0x8c2f27, red: 0xb8302a, blue: 0x2c64a3, copper: 0xb0703a, yellow: 0xd2ae35,
  orange: 0xe07a2b, green: 0x4d8a57, lining: 0x6f5a4c, trim: 0x55585a, zinc: 0xc9c2a6, white: 0xe9e8e2,
  plate: 0xf1efe6, plateYellow: 0xe8c63a, cable: 0x2a2a2a, leadBlue: 0x3a5f8f,
};

function mat(color, opts = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.6, metalness: 0.15, ...opts });
}
function paintMat(color) {
  const m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.38, metalness: 0.05, clearcoat: 0.6, clearcoatRoughness: 0.25, side: THREE.DoubleSide });
  m.userData.paint = true;
  return m;
}
function mesh(geo, m) { return new THREE.Mesh(geo, m); }
function at(obj, x, y, z) { obj.position.set(x, y, z); return obj; }

// Boîte aux arêtes arrondies (extrusion biseautée).
function rbox(w, h, d, r, m) {
  r = Math.min(r, w / 2 - 1e-3, h / 2 - 1e-3, d / 2 - 1e-3);
  const s = new THREE.Shape();
  const x = -w / 2 + r, y = -h / 2 + r, iw = w - 2 * r, ih = h - 2 * r;
  s.moveTo(x, y); s.lineTo(x + iw, y); s.lineTo(x + iw, y + ih); s.lineTo(x, y + ih); s.lineTo(x, y);
  const g = new THREE.ExtrudeGeometry(s, { depth: d - 2 * r, bevelEnabled: true, bevelThickness: r, bevelSize: r, bevelSegments: 3, curveSegments: 4 });
  g.translate(0, 0, -(d - 2 * r) / 2);
  return mesh(g, m);
}
function box(w, h, d, m) { return mesh(new THREE.BoxGeometry(w, h, d), m); }
function cyl(r, len, m, axis = 'y', seg = 20, r2 = r) {
  const o = mesh(new THREE.CylinderGeometry(r2, r, len, seg), m);
  if (axis === 'x') o.rotation.z = -Math.PI / 2;
  if (axis === 'z') o.rotation.x = Math.PI / 2;
  return o;
}
// Tube droit entre deux points.
function rod(a, b, r, m, seg = 10) {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const o = mesh(new THREE.CylinderGeometry(r, r, va.distanceTo(vb), seg), m);
  o.position.copy(va).add(vb).multiplyScalar(0.5);
  o.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
  return o;
}
// Tube courbe passant par des points.
function tube(points, r, m, closed = false, seg = 48) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), closed);
  return mesh(new THREE.TubeGeometry(curve, seg, r, 8, closed), m);
}
function lathe(profile, m, seg = 32) {
  return mesh(new THREE.LatheGeometry(profile.map(([r, y]) => new THREE.Vector2(r, y)), seg), m);
}
// Surface en grille : fn(i, j) -> [x, y, z] ; keep(i, j) filtre les quadrilatères.
function gridGeo(ni, nj, fn, keep = () => true) {
  const pos = [];
  for (let i = 0; i < ni; i++) for (let j = 0; j < nj; j++) pos.push(...fn(i, j));
  const idx = [];
  for (let i = 0; i < ni - 1; i++) for (let j = 0; j < nj - 1; j++) {
    if (!keep(i, j)) continue;
    const a = i * nj + j, b = (i + 1) * nj + j, c = (i + 1) * nj + j + 1, d = i * nj + j + 1;
    idx.push(a, b, d, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}
// Polygone plan (vitres) à partir de points 3D, triangulé en éventail.
function poly(points, m) {
  const pos = points.flat();
  const idx = [];
  for (let i = 1; i < points.length - 1; i++) idx.push(0, i, i + 1);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return mesh(g, m);
}
function linspace(a, b, n) { return Array.from({ length: n }, (_, i) => a + ((b - a) * i) / (n - 1)); }

// Textures dessinées (calandre, faisceau de radiateur, ailettes).
function stripesTexture(bg, fg, n, vertical = false) {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, 128, 128);
  g.fillStyle = fg;
  const step = 128 / n;
  for (let i = 0; i < n; i++) vertical ? g.fillRect(i * step, 0, step * 0.45, 128) : g.fillRect(0, i * step, 128, step * 0.45);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function labelTexture(text, bg = '#f1efe6', fg = '#111') {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 56;
  const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, 256, 56);
  g.strokeStyle = '#222'; g.lineWidth = 4; g.strokeRect(2, 2, 252, 52);
  g.fillStyle = fg; g.font = 'bold 34px "Arial Narrow", Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, 128, 30);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// ===================== Silhouette de la caisse =====================
const X_REAR = -1.835, X_NOSE = 1.84;
function halfW(x) {
  let w = 0.752;
  if (x > 1.55) w -= 0.09 * ((x - 1.55) / 0.29) ** 2;
  if (x < -1.6) w -= 0.05 * ((-1.6 - x) / 0.235) ** 2;
  return w;
}
function beltY(x) {
  if (x >= 0.84) {
    let y = 0.93 - (x - 0.84) * 0.10;
    if (x > 1.70) y -= 0.05 * ((x - 1.70) / 0.14) ** 2;
    return y;
  }
  if (x >= 0.80) return 0.935;
  return 0.95 + (0.80 - x) * 0.008;
}
function arch(x, c, r) { const d = x - c; return Math.abs(d) < r ? 0.29 + Math.sqrt(r * r - d * d) : 0; }
function sillY(x) {
  let y = 0.30;
  if (x > 1.70) y = 0.30 + 0.08 * ((x - 1.70) / 0.14) ** 2;
  if (x < -1.72) y = 0.30 + 0.06 * ((-1.72 - x) / 0.115) ** 2;
  return Math.max(y, arch(x, AXLE_F, 0.37), arch(x, -1.12, 0.355));
}
function hoodHalfW(x) { return Math.min(halfW(x) - 0.10, 0.62); }
const bulge = (t) => 0.955 + 0.045 * Math.sin(Math.PI * t);
// Point du flanc : t de 0 (bas) à 1 (ligne de caisse), puis v (0..1) pour le retour vers l'intérieur.
function sidePoint(x, t, v, s, push = 1) {
  const w = halfW(x), top = beltY(x), bot = sillY(x);
  if (v <= 0) {
    const y = bot + t * (top - bot);
    return [x, y, s * w * bulge(t) * push];
  }
  const inner = x > 0.83 ? hoodHalfW(x) + 0.006 : w * bulge(1) - 0.035;
  const outer = w * bulge(1);
  const z = outer + (inner - outer) * v;
  return [x, top + 0.012 * Math.sin((v * Math.PI) / 2), s * z * push];
}
const T_ROWS = [0, 0.085, 0.16, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.93, 1];
const V_ROWS = [0.25, 0.55, 1];
const DOORS = [[-0.02, 0.74], [-0.76, -0.05]];
const inDoor = (x) => DOORS.some(([a, b]) => x > a && x < b);
function stations(a, b, step, extra = []) {
  const xs = new Set(extra.filter((x) => x >= a && x <= b));
  for (let x = a; x < b; x += step) xs.add(+x.toFixed(4));
  xs.add(b);
  return [...xs].sort((p, q) => p - q);
}
function sideRows() { return [...T_ROWS.map((t) => [t, 0]), ...V_ROWS.map((v) => [1, v])]; }
const ROWS = sideRows();
const DOOR_ROW = 1; // les portes commencent à t = 0,085 (bas de porte)

export function buildCar({ bodyColor = 0xe9e6dc } = {}) {
  const root = new THREE.Group();
  const parts = new Map();
  const fasteners = new Map();

  function part(id, explode = [0, 0, 0], children = []) {
    const g = new THREE.Group();
    g.userData.partId = id;
    g.userData.explode = new THREE.Vector3(...explode);
    children.forEach((c) => g.add(c));
    root.add(g);
    if (!parts.has(id)) parts.set(id, []);
    parts.get(id).push(g);
    return g;
  }

  // Vis, écrous, bouchons. dir : sens de dévissage (vers l'extérieur de la pièce).
  // kind : 'bolt' (tête hexagonale), 'nut' (écrou sur goujon), 'plug' (bouchon carré),
  // 'screw' (vis cruciforme), 'pin' (clavette qui coulisse), 'spark' (bougie), 'fuse' (fusible).
  function fasten(group, setId, specs, { r = 0.008, len = 0.04, kind = 'bolt', travel } = {}) {
    if (!fasteners.has(setId)) fasteners.set(setId, []);
    for (const spec of specs) {
      const o = new THREE.Group();
      const zinc = mat(kind === 'plug' ? C.darkSteel : C.zinc, { metalness: 0.75, roughness: 0.32 });
      if (kind === 'spark') {
        o.add(at(cyl(r * 0.9, len * 0.55, mat(C.white, { roughness: 0.3 }), 'y', 14), 0, len * 0.35, 0));
        o.add(at(cyl(r * 1.35, r * 1.1, zinc, 'y', 6), 0, r * 0.4, 0));
        o.add(at(cyl(r * 0.55, len * 0.5, zinc, 'y', 10), 0, -len * 0.25, 0));
        o.add(at(cyl(r * 0.5, r * 1.2, mat(C.black), 'y', 10), 0, len * 0.66, 0));
      } else if (kind === 'fuse') {
        o.add(at(cyl(r * 0.6, len, mat(0xf3e6c4, { transparent: true, opacity: 0.9 }), 'y', 10), 0, 0, 0));
        o.add(at(cyl(r * 0.65, r * 0.8, zinc, 'y', 10), 0, len / 2, 0));
        o.add(at(cyl(r * 0.65, r * 0.8, zinc, 'y', 10), 0, -len / 2, 0));
      } else if (kind === 'pin') {
        o.add(at(cyl(r, len, zinc, 'y', 10), 0, -len / 2, 0));
        o.add(at(mesh(new THREE.TorusGeometry(r * 1.6, r * 0.35, 6, 14), zinc), 0, r * 1.4, 0));
      } else {
        const headR = kind === 'plug' ? r * 1.15 : r;
        const seg = kind === 'plug' ? 4 : kind === 'screw' ? 16 : 6;
        const headH = kind === 'screw' ? r * 0.55 : r * 0.75;
        o.add(at(cyl(headR, headH, zinc, 'y', seg), 0, headH / 2, 0));
        if (kind !== 'screw') o.add(at(cyl(r * 1.35, r * 0.18, zinc, 'y', 16), 0, r * 0.09, 0));
        if (kind === 'screw') o.add(at(box(r * 1.4, r * 0.25, r * 0.25, mat(C.black)), 0, headH + 0.0005, 0));
        o.add(at(cyl(r * 0.58, len, zinc, 'y', 8), 0, -len / 2, 0));
        if (kind === 'nut') o.add(at(cyl(r * 0.5, r * 0.8, zinc, 'y', 8), 0, headH + r * 0.4, 0)); // bout de goujon
      }
      const dir = new THREE.Vector3(...(spec.d || [0, 1, 0])).normalize();
      o.position.set(...spec.p);
      o.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      o.userData.fastener = setId;
      o.traverse((c) => { if (c.isMesh) c.userData.fastener = setId; });
      group.add(o);
      fasteners.get(setId).push({ obj: o, dir, base: o.position.clone(), q0: o.quaternion.clone(), travel: travel ?? len + 0.05, spin: kind !== 'pin' && kind !== 'fuse' });
    }
  }

  const paint = paintMat(bodyColor);
  const P = () => paint.clone();
  const black = () => mat(C.black, { roughness: 0.8 });
  const trimM = () => mat(C.trim, { roughness: 0.85 });
  const chromeM = () => mat(C.chrome, { metalness: 0.9, roughness: 0.18 });
  const glassM = () => mat(C.glass, { transparent: true, opacity: 0.3, roughness: 0.05, metalness: 0.4, side: THREE.DoubleSide, depthWrite: false });

  // ================= CARROSSERIE =================
  const XS = stations(X_REAR, X_NOSE, 0.02, [-0.76, -0.05, -0.02, 0.74, 0.80, 0.83, 0.84]);
  const caisse = [];
  for (const s of [1, -1]) {
    const g = gridGeo(XS.length, ROWS.length, (i, j) => sidePoint(XS[i], ROWS[j][0], ROWS[j][1], s),
      (i, j) => !(inDoor((XS[i] + XS[i + 1]) / 2) && j >= DOOR_ROW));
    caisse.push(mesh(g, P()));
    // Passages de roue (doublures noires)
    for (const [cx, r] of [[AXLE_F, 0.37], [-1.12, 0.355]]) {
      const liner = mesh(new THREE.CylinderGeometry(r, r, 0.22, 24, 1, true, Math.PI / 2, Math.PI), mat(C.black, { side: THREE.DoubleSide, roughness: 0.95 }));
      liner.rotation.x = Math.PI / 2;
      liner.rotation.y = 0;
      liner.position.set(cx, 0.29, s * (0.70 - 0.11));
      caisse.push(liner);
    }
    // Bas de caisse
    caisse.push(rod([-0.76, 0.30, s * 0.72], [0.94, 0.30, s * 0.72], 0.025, P()));
  }
  // Auvent, tablier, face avant, jupe arrière
  caisse.push(at(rbox(0.12, 0.03, 1.44, 0.01, P()), 0.815, 0.94, 0));
  caisse.push(at(box(0.08, 0.012, 1.10, black()), 0.83, 0.958, 0)); // grille d'auvent
  caisse.push(at(box(0.02, 0.60, 1.40, P()), 0.82, 0.64, 0));
  caisse.push(at(box(0.012, 0.42, 1.30, P()), 1.836, 0.58, 0));
  caisse.push(at(box(0.012, 0.10, 1.38, P()), -1.832, 0.40, 0));
  part('caisse', [0, 0.25, 0], caisse);

  // Baguettes de protection latérales grises (signe distinctif de la GTL)
  function stripSegment(x0, x1, s) {
    const xs = stations(x0, x1, 0.02);
    const ys = [0.405, 0.43, 0.455, 0.48];
    const g = gridGeo(xs.length, ys.length, (i, j) => {
      const x = xs[i], y = ys[j], top = beltY(x), bot = 0.30;
      const t = (y - bot) / (top - bot);
      return [x, y, s * (halfW(x) * bulge(t) + 0.009 + (j === 0 || j === 3 ? 0 : 0.004))];
    });
    return mesh(g, trimM());
  }
  const bodyStrips = [];
  for (const s of [1, -1]) {
    bodyStrips.push(stripSegment(0.745, 0.93, s), stripSegment(-0.048, -0.022, s), stripSegment(-1.80, -1.48, s));
  }
  part('caisse', [0, 0.25, 0], bodyStrips);

  // Pavillon bombé, montants, gouttières
  const RX = stations(-1.735, 0.33, 0.03);
  const RU = linspace(-1, 1, 15);
  const roofGeo = gridGeo(RX.length, RU.length, (i, j) => {
    const x = RX[i], u = RU[j];
    const endDrop = 0.012 * (Math.max(0, (x - 0.25) / 0.08) ** 2 + Math.max(0, (-1.66 - x) / 0.075) ** 2);
    return [x, 1.49 + 0.045 * (1 - u * u) - endDrop, u * 0.668];
  });
  const roofParts = [mesh(roofGeo, P())];
  for (const s of [1, -1]) {
    const zb = 0.715, zt = 0.664;
    roofParts.push(rod([0.80, 0.945, s * 0.70], [0.33, 1.49, s * zt], 0.026, P()));             // montant A
    roofParts.push(at(rbox(0.06, 0.54, 0.035, 0.01, P()), -0.035, 1.225, s * (zb + zt) / 2));    // montant B
    roofParts[roofParts.length - 1].rotation.x = s * 0.09;
    roofParts.push(at(rbox(0.05, 0.54, 0.035, 0.01, P()), -0.79, 1.23, s * (zb + zt) / 2));      // montant C
    roofParts[roofParts.length - 1].rotation.x = s * 0.09;
    roofParts.push(rod([-1.825, 0.968, s * 0.69], [-1.735, 1.49, s * 0.655], 0.03, P()));      // montant D
    roofParts.push(rod([0.33, 1.488, s * 0.668], [-1.735, 1.488, s * 0.668], 0.011, P()));     // gouttière
  }
  part('caisse', [0, 0.25, 0], roofParts);

  // Vitrages fixes : pare-brise et custodes
  const sideZ = (y) => 0.715 + (0.664 - 0.715) * ((y - 0.95) / 0.54);
  const vit = [];
  const wsGeo = gridGeo(8, 8, (i, j) => {
    const a = i / 7, u = (j / 7) * 2 - 1;
    const x = 0.795 - a * (0.795 - 0.335), y = 0.95 + a * 0.535;
    return [x + 0.025 * (1 - u * u), y, u * (0.69 - a * 0.03)];
  });
  const ws = mesh(wsGeo, glassM());
  ws.userData.glass = true;
  vit.push(ws);
  vit.push(tube([[0.795, 0.95, -0.69], [0.82, 0.95, 0], [0.795, 0.95, 0.69]], 0.008, black()));
  vit.push(tube([[0.335, 1.485, -0.66], [0.36, 1.485, 0], [0.335, 1.485, 0.66]], 0.008, black()));
  for (const s of [1, -1]) {
    const q = poly([[-0.815, 0.966, s * 0.712], [-1.81, 0.975, s * 0.708], [-1.73, 1.475, s * sideZ(1.475)], [-0.815, 1.475, s * sideZ(1.475)]], glassM());
    q.userData.glass = true;
    vit.push(q);
  }
  part('vitrage', [0, 0.6, 0], vit);

  // Capot (articulé à l'avant sur la 4L), légèrement bombé
  const HX = stations(0.845, X_NOSE + 0.004, 0.025);
  const HU = linspace(-1, 1, 17);
  const hoodGeo = gridGeo(HX.length, HU.length, (i, j) => {
    const x = HX[i], u = HU[j];
    return [x, beltY(x) + 0.006 + 0.035 * (1 - u * u) * (1 - 0.4 * Math.max(0, (x - 1.7) / 0.14)), u * hoodHalfW(x)];
  });
  const hood = [mesh(hoodGeo, P())];
  hood.push(at(box(0.012, 0.05, 1.10, P()), X_NOSE + 0.006, 0.785, 0)); // bord tombé avant
  part('capot', [0.35, 0.65, 0], hood);

  // Portes : découpées dans la même surface que la caisse
  function door(x0, x1, s) {
    const xs = stations(x0, x1, 0.02);
    const rows = ROWS.slice(DOOR_ROW);
    const g = new THREE.Group();
    g.add(mesh(gridGeo(xs.length, rows.length, (i, j) => sidePoint(xs[i], rows[j][0], rows[j][1], s, 1.004)), P()));
    // joint de porte (contour sombre)
    const yb = 0.355, zb = (x, y) => s * (halfW(x) * bulge((y - 0.30) / (beltY(x) - 0.30)) + 0.004);
    g.add(rod([x0, yb, zb(x0, yb)], [x1, yb, zb(x1, yb)], 0.003, black(), 6));
    g.add(tube([[x0, yb, zb(x0, yb)], [x0, 0.65, zb(x0, 0.65)], [x0, beltY(x0), zb(x0, beltY(x0))]], 0.003, black(), false, 8));
    g.add(tube([[x1, yb, zb(x1, yb)], [x1, 0.65, zb(x1, 0.65)], [x1, beltY(x1), zb(x1, beltY(x1))]], 0.003, black(), false, 8));
    // panneau intérieur
    const zi = s * 0.70;
    g.add(poly([[x0 + 0.02, 0.37, zi], [x1 - 0.02, 0.37, zi], [x1 - 0.02, beltY(x1) - 0.02, zi], [x0 + 0.02, beltY(x0) - 0.02, zi]], mat(0x3b3532, { side: THREE.DoubleSide, roughness: 0.9 })));
    // baguette grise
    g.add(stripSegment(x0 + 0.004, x1 - 0.004, s));
    // poignée
    const hz = s * (halfW(x0) + 0.012);
    g.add(at(rbox(0.11, 0.022, 0.02, 0.008, chromeM()), x0 + 0.085, 0.86, hz));
    // vitres coulissantes et encadrement
    const front = x1 > 0.5;
    const yb2 = beltY(x1), yt = 1.475;
    const pts = front
      ? [[x0 + 0.01, beltY(x0)], [x1 - 0.015, yb2], [0.345, yt], [x0 + 0.01, yt]]
      : [[x0 + 0.01, beltY(x0)], [x1 - 0.01, yb2], [x1 - 0.01, yt], [x0 + 0.01, yt]];
    const p3 = pts.map(([x, y]) => [x, y, s * sideZ(y)]);
    const gl = poly(p3, glassM());
    gl.userData.glass = true;
    g.add(gl);
    const frame = P();
    for (let k = 0; k < p3.length; k++) {
      const a = p3[k], b = p3[(k + 1) % p3.length];
      if (k === 0) continue; // pas de cadre sur la ligne de caisse
      g.add(rod(a, b, 0.012, frame, 8));
    }
    // rail central des vitres coulissantes
    const xm = front ? 0.36 : (x0 + x1) / 2;
    g.add(rod([xm, beltY(xm) + 0.01, s * sideZ(0.97)], [xm, 1.46, s * sideZ(1.46)], 0.006, black(), 6));
    if (front && s < 0) { // rétroviseur conducteur
      g.add(rod([0.70, 0.97, s * 0.73], [0.70, 1.02, s * 0.80], 0.008, black()));
      g.add(at(rbox(0.03, 0.08, 0.12, 0.012, black()), 0.70, 1.04, s * 0.84));
    }
    return g;
  }
  part('portes', [0, 0, 0.6], [door(-0.02, 0.74, 1)]);
  part('portes', [0, 0, 0.6], [door(-0.76, -0.05, 1)]);
  part('portes', [0, 0, -0.6], [door(-0.02, 0.74, -1)]);
  part('portes', [0, 0, -0.6], [door(-0.76, -0.05, -1)]);

  // Hayon : panneau bombé + lunette
  const hatch = new THREE.Group();
  const HZ = linspace(-0.6, 0.6, 13);
  const HY = linspace(0.44, 0.97, 8);
  hatch.add(mesh(gridGeo(HY.length, HZ.length, (i, j) => [-1.842 - 0.025 * (1 - (HZ[j] / 0.6) ** 2) + (HY[i] - 0.44) * 0.03, HY[i], HZ[j]]), P()));
  const hg = poly([[-1.822, 0.99, -0.59], [-1.822, 0.99, 0.59], [-1.74, 1.465, 0.58], [-1.74, 1.465, -0.58]], glassM());
  hg.userData.glass = true;
  hatch.add(hg);
  hatch.add(rod([-1.822, 0.98, -0.6], [-1.822, 0.98, 0.6], 0.013, P()));
  hatch.add(rod([-1.74, 1.475, -0.6], [-1.74, 1.475, 0.6], 0.013, P()));
  hatch.add(at(rbox(0.03, 0.03, 0.20, 0.01, chromeM()), -1.87, 0.90, 0));
  const plateR = at(box(0.006, 0.11, 0.52, mat(C.white, { map: labelTexture('1234 RT 33', '#e8c63a') })), -1.875, 0.55, 0);
  plateR.rotation.y = -Math.PI / 2;
  plateR.rotation.y = Math.PI;
  hatch.add(plateR);
  part('hayon', [-0.55, 0.35, 0], [hatch]);

  // Pare-chocs gris enveloppants
  function bumper(sign) {
    const shape = new THREE.Shape();
    const w = 0.07, h = 0.10, r = 0.025;
    shape.moveTo(-w / 2 + r, -h / 2); shape.lineTo(w / 2 - r, -h / 2); shape.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
    shape.lineTo(w / 2, h / 2 - r); shape.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); shape.lineTo(-w / 2 + r, h / 2);
    shape.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); shape.lineTo(-w / 2, -h / 2 + r); shape.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
    const xb = sign > 0 ? 1.885 : -1.885;
    const path = new THREE.CatmullRomCurve3([
      new THREE.Vector3(xb - sign * 0.11, 0, -0.77), new THREE.Vector3(xb - sign * 0.01, 0, -0.66),
      new THREE.Vector3(xb + sign * 0.012, 0, 0), new THREE.Vector3(xb - sign * 0.01, 0, 0.66), new THREE.Vector3(xb - sign * 0.11, 0, 0.77)]);
    const g = new THREE.ExtrudeGeometry(shape, { steps: 40, extrudePath: path, bevelEnabled: false });
    const o = mesh(g, mat(0x5d6062, { roughness: 0.75 }));
    o.position.y = 0.40;
    return o;
  }
  const bumpF = new THREE.Group();
  bumpF.add(bumper(1));
  const plateF = at(box(0.006, 0.11, 0.52, mat(C.white, { map: labelTexture('1234 RT 33') })), 1.93, 0.40, 0);
  plateF.rotation.y = Math.PI / 2;
  plateF.rotation.y = 0;
  bumpF.add(plateF);
  part('pare-chocs', [0.45, 0, 0], [bumpF]);
  part('pare-chocs', [-0.45, 0, 0], [bumper(-1)]);

  // Calandre noire pleine largeur avec entourages de phares
  const grille = new THREE.Group();
  const gTex = stripesTexture('#121212', '#3a3c3e', 9);
  gTex.wrapS = gTex.wrapT = THREE.RepeatWrapping;
  gTex.repeat.set(1, 1);
  const gMesh = at(box(0.02, 0.29, 0.64, mat(0xffffff, { map: gTex, roughness: 0.7 })), 1.848, 0.60, 0);
  grille.add(gMesh);
  grille.add(at(rbox(0.03, 0.33, 1.26, 0.02, black()), 1.842, 0.60, 0));
  for (const s of [1, -1]) grille.add(at(rbox(0.035, 0.24, 0.24, 0.04, mat(0x6c6f71, { metalness: 0.4, roughness: 0.4 })), 1.85, 0.62, s * 0.50));
  const diamond = at(box(0.012, 0.075, 0.075, chromeM()), 1.862, 0.62, 0);
  diamond.rotation.x = Math.PI / 4;
  grille.add(diamond);
  part('calandre', [0.4, 0, 0], [grille]);

  // ================= PLATEFORME =================
  const platform = [];
  platform.push(at(rbox(2.55, 0.035, 1.40, 0.012, mat(C.darkSteel)), -0.45, 0.285, 0));
  for (const z of [-0.42, 0.42]) platform.push(at(rbox(1.05, 0.08, 0.07, 0.015, mat(C.darkSteel)), 1.30, 0.32, z));
  for (const z of [-0.55, 0.55]) platform.push(at(rbox(2.4, 0.06, 0.08, 0.015, mat(C.darkSteel)), -0.40, 0.27, z));
  platform.push(at(rbox(0.07, 0.08, 0.92, 0.015, mat(C.darkSteel)), 1.72, 0.34, 0));
  platform.push(at(rbox(0.08, 0.07, 1.30, 0.015, mat(C.darkSteel)), 0.18, 0.27, 0)); // traverse d'ancrage des barres
  part('plateforme', [0, -0.45, 0], platform);

  // ================= ROUES =================
  const tireProfile = [[0.165, -0.07], [0.20, -0.072], [0.255, -0.07], [0.278, -0.058], [0.286, -0.03], [0.287, 0], [0.286, 0.03], [0.278, 0.058], [0.255, 0.07], [0.20, 0.072], [0.165, 0.07]];
  function wheel(x, z, s, partId = 'roues', explode) {
    const g = part(partId, explode);
    const w = new THREE.Group();
    const tire = lathe(tireProfile, mat(C.rubber, { roughness: 0.92, side: THREE.DoubleSide }), 40);
    tire.rotation.x = Math.PI / 2;
    w.add(tire);
    const rim = lathe([[0.0, 0.03], [0.07, 0.03], [0.11, 0.02], [0.15, -0.01], [0.168, -0.02], [0.168, -0.065], [0.172, -0.07]], mat(C.steel, { metalness: 0.55, roughness: 0.35, side: THREE.DoubleSide }), 36);
    rim.rotation.x = -Math.PI / 2 * s;
    w.add(rim);
    for (let i = 0; i < 6; i++) { // voile ajouré
      const a = (i / 6) * Math.PI * 2 + 0.3;
      const slot = at(rbox(0.035, 0.02, 0.01, 0.008, mat(C.black)), Math.cos(a) * 0.125, Math.sin(a) * 0.125, s * 0.012);
      slot.rotation.z = a;
      w.add(slot);
    }
    const cap = lathe([[0, 0.02], [0.03, 0.017], [0.045, 0.008], [0.048, 0]], chromeM(), 24);
    cap.rotation.x = Math.PI / 2 * s;
    at(cap, 0, 0, s * 0.032);
    w.add(cap);
    w.position.set(x, WHEEL_R, z);
    g.add(w);
    const nuts = [];
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2 + Math.PI / 2;
      nuts.push({ p: [x + Math.cos(a) * 0.075, WHEEL_R + Math.sin(a) * 0.075, z + s * 0.03], d: [0, 0, s] });
    }
    fasten(g, partId === 'roues' ? 'ecrous-roue' : 'ecrous-roue-secours', nuts, { r: 0.0095, len: 0.03, kind: 'nut', travel: 0.07 });
    return g;
  }
  wheel(AXLE_F, TRACK_F, 1, 'roues', [0, 0, 0.5]);
  wheel(AXLE_F, -TRACK_F, -1, 'roues', [0, 0, -0.5]);
  wheel(AXLE_R_RIGHT, TRACK_R, 1, 'roues', [0, 0, 0.5]);
  wheel(AXLE_R_LEFT, -TRACK_R, -1, 'roues', [0, 0, -0.5]);
  // Roue de secours sous le plancher arrière, face extérieure vers le sol
  const spareG = part('roue-secours', [-0.6, -0.2, 0]);
  const spare = new THREE.Group();
  const st = lathe(tireProfile, mat(C.rubber, { roughness: 0.92, side: THREE.DoubleSide }), 32);
  spare.add(st);
  spare.add(lathe([[0, 0.03], [0.11, 0.02], [0.168, -0.02], [0.168, -0.065]], mat(C.steel, { metalness: 0.5, side: THREE.DoubleSide }), 28));
  spare.position.set(-1.45, 0.19, 0);
  spare.scale.setScalar(0.95);
  spareG.add(spare);
  spareG.add(rod([-1.80, 0.27, -0.25], [-1.12, 0.27, -0.25], 0.008, mat(C.darkSteel)));
  spareG.add(rod([-1.80, 0.27, 0.25], [-1.12, 0.27, 0.25], 0.008, mat(C.darkSteel)));
  fasten(spareG, 'vis-berceau-secours', [{ p: [-1.80, 0.30, 0], d: [0, 1, 0] }], { r: 0.011, len: 0.06 });

  // ================= INTÉRIEUR =================
  function seat(x, z, w) {
    const g = new THREE.Group();
    const frame = mat(C.seatFrame, { metalness: 0.5, roughness: 0.4 });
    const cloth = mat(C.seat, { roughness: 0.95 });
    g.add(at(rbox(0.46, 0.09, w, 0.035, cloth), x, 0.50, z));
    const back = at(rbox(0.08, 0.50, w * 0.96, 0.035, cloth), x - 0.25, 0.77, z);
    back.rotation.z = 0.2;
    g.add(back);
    for (const dz of [-w / 2 + 0.02, w / 2 - 0.02]) {
      g.add(rod([x + 0.22, 0.46, z + dz], [x - 0.22, 0.46, z + dz], 0.01, frame));
      g.add(rod([x + 0.18, 0.46, z + dz], [x + 0.18, 0.30, z + dz], 0.01, frame));
      g.add(rod([x - 0.18, 0.46, z + dz], [x - 0.18, 0.30, z + dz], 0.01, frame));
      g.add(rod([x - 0.22, 0.47, z + dz], [x - 0.33, 1.0, z + dz], 0.01, frame));
    }
    return g;
  }
  part('sieges-av', [0, 0.7, 0], [seat(0.08, -0.33, 0.46)]);
  part('sieges-av', [0, 0.7, 0], [seat(0.08, 0.33, 0.46)]);
  part('banquette', [-0.2, 0.8, 0], [seat(-0.92, 0, 1.18)]);

  const dash = new THREE.Group();
  const dashM = mat(C.dash, { roughness: 0.85 });
  dash.add(at(rbox(0.22, 0.10, 1.38, 0.035, dashM), 0.70, 0.89, 0));
  dash.add(at(rbox(0.12, 0.05, 1.30, 0.02, dashM), 0.66, 0.82, 0)); // vide-poches
  const pod = at(rbox(0.08, 0.11, 0.34, 0.03, dashM), 0.61, 0.93, -0.35);
  dash.add(pod);
  for (const [dz, r] of [[-0.08, 0.042], [0.06, 0.032]]) {
    const dial = at(cyl(r, 0.006, mat(0x111111, { emissive: 0x15140f }), 'x', 24), 0.568, 0.935, -0.35 + dz);
    dash.add(dial);
    dash.add(at(cyl(r * 0.85, 0.004, mat(0xe9e4d6, { emissive: 0x2a2614 }), 'x', 24), 0.565, 0.935, -0.35 + dz));
  }
  for (const dz of [-0.55, 0.55, 0.12]) dash.add(at(rbox(0.02, 0.05, 0.09, 0.01, black()), 0.59, 0.90, dz)); // aérateurs
  fasten(dash, 'vis-planche', [[0.60, 0.95, -0.62], [0.60, 0.95, 0.62], [0.60, 0.84, -0.2], [0.60, 0.84, 0.3]].map((p) => ({ p, d: [-1, 0, 0] })), { r: 0.005, len: 0.025, kind: 'screw' });
  part('planche-bord', [-0.45, 0.35, 0], [dash]);

  const steering = new THREE.Group();
  const colA = [0.80, 0.76, -0.35], colB = [0.47, 0.97, -0.35];
  steering.add(rod(colA, colB, 0.022, black()));
  steering.add(at(rbox(0.10, 0.08, 0.08, 0.02, black()), 0.53, 0.92, -0.35)); // carénage
  const wheelG = new THREE.Group();
  wheelG.add(mesh(new THREE.TorusGeometry(0.19, 0.016, 12, 40), mat(C.black, { roughness: 0.6 })));
  wheelG.add(rod([-0.185, -0.02, 0], [0.185, -0.02, 0], 0.012, black()));
  wheelG.add(at(rbox(0.09, 0.07, 0.035, 0.02, black()), 0, -0.02, 0));
  wheelG.position.set(0.455, 0.985, -0.35);
  wheelG.rotation.y = Math.PI / 2;
  wheelG.rotateX(-0.58);
  steering.add(wheelG);
  fasten(steering, 'ecrou-volant', [{ p: [0.452, 0.99, -0.35], d: [-0.85, 0.53, 0] }], { r: 0.011, len: 0.03, kind: 'nut' });
  part('volant', [-0.45, 0.45, 0], [steering]);

  // Levier « trombone » + tige au-dessus du moteur
  const gear = new THREE.Group();
  const chr = chromeM();
  gear.add(tube([[0.62, 0.87, 0.03], [0.55, 0.87, 0.03], [0.50, 0.85, 0.04]], 0.008, chr, false, 12));
  gear.add(at(mesh(new THREE.SphereGeometry(0.026, 16, 12), mat(C.black, { roughness: 0.4 })), 0.49, 0.85, 0.04));
  gear.add(tube([[0.62, 0.87, 0.03], [0.82, 0.87, 0.03], [1.05, 0.80, 0.04], [1.42, 0.68, 0.05]], 0.008, mat(C.steel, { metalness: 0.6 }), false, 30));
  gear.add(at(cyl(0.02, 0.05, mat(C.rubber), 'x', 12), 0.82, 0.87, 0.03)); // soufflet de tablier
  part('levier-vitesses', [0, 0.45, 0], [gear]);

  const pedals = new THREE.Group();
  [-0.47, -0.37, -0.25].forEach((z, i) => {
    pedals.add(tube([[0.76, 0.80, z], [0.70, 0.62, z], [0.62, 0.44, z]], 0.008, mat(C.darkSteel), false, 10));
    pedals.add(at(rbox(0.02, 0.07, i === 2 ? 0.05 : 0.075, 0.008, mat(C.rubber)), 0.615, 0.43, z));
  });
  fasten(pedals, 'garde-frein', [{ p: [0.77, 0.72, -0.37], d: [-1, 0, 0] }], { r: 0.007, len: 0.02, kind: 'nut', travel: 0.02 });
  part('pedalier', [-0.3, 0.2, -0.3], [pedals]);

  const handbrake = new THREE.Group();
  handbrake.add(rod([0.74, 0.74, -0.12], [0.58, 0.74, -0.12], 0.008, chromeM()));
  handbrake.add(at(rbox(0.025, 0.035, 0.10, 0.01, black()), 0.575, 0.74, -0.12));
  handbrake.add(tube([[0.74, 0.74, -0.12], [0.76, 0.50, -0.12], [0.70, 0.30, -0.10], [0.0, 0.265, -0.03], [-0.95, 0.265, 0]], 0.005, mat(C.cable), false, 40));
  handbrake.add(at(rbox(0.05, 0.02, 0.12, 0.006, mat(C.darkSteel)), -0.95, 0.265, 0)); // palonnier
  handbrake.add(tube([[-0.95, 0.265, -0.05], [-1.05, 0.27, -0.35], [AXLE_R_LEFT + 0.04, 0.28, -0.52]], 0.004, mat(C.cable), false, 20));
  handbrake.add(tube([[-0.95, 0.265, 0.05], [-1.05, 0.27, 0.35], [AXLE_R_RIGHT + 0.04, 0.28, 0.52]], 0.004, mat(C.cable), false, 20));
  fasten(handbrake, 'reglage-frein-main', [{ p: [-0.92, 0.265, 0], d: [1, 0, 0] }], { r: 0.007, len: 0.025, kind: 'nut', travel: 0.02 });
  part('frein-main', [0, -0.25, 0], [handbrake]);

  // ================= MOTEUR 688 (Cléon-Fonte) =================
  const castM = () => mat(C.block, { roughness: 0.75, metalness: 0.25 });
  const block = part('bloc', [0, 0.2, 0]);
  block.add(at(rbox(0.42, 0.26, 0.26, 0.02, castM()), EX, 0.48, 0));
  block.add(at(rbox(0.40, 0.08, 0.30, 0.02, castM()), EX, 0.36, 0)); // jupe
  for (let i = 0; i < 4; i++) { // fûts de cylindres côté gauche
    block.add(at(cyl(0.045, 0.20, castM(), 'y', 16), EX + 0.15 - i * 0.10, 0.52, -0.115));
  }
  for (const x of [EX + 0.12, EX - 0.12]) block.add(at(cyl(0.018, 0.008, mat(C.zinc, { metalness: 0.6 }), 'z', 14), x, 0.50, 0.132)); // bouchons de dessablage
  const bell = lathe([[0.0, 0], [0.18, 0], [0.175, 0.06], [0.14, 0.12], [0.0, 0.12]], mat(C.castAlu, { metalness: 0.35, roughness: 0.55 }), 32);
  bell.rotation.z = -Math.PI / 2;
  at(bell, 1.13, 0.44, 0);
  block.add(bell);
  for (const s of [1, -1]) { // supports moteur
    block.add(at(rbox(0.08, 0.05, 0.10, 0.015, mat(C.darkSteel)), EX - 0.05, 0.36, s * 0.20));
    block.add(at(cyl(0.03, 0.04, mat(C.rubber), 'z', 14), EX - 0.05, 0.36, s * 0.27));
  }
  fasten(block, 'bouchon-vidange-bloc', [{ p: [EX + 0.05, 0.40, -0.135], d: [0, 0, -1] }], { r: 0.008, len: 0.02, kind: 'plug' });
  fasten(block, 'fix-boite', [[1.13, 0.60, 0.12], [1.13, 0.60, -0.12], [1.13, 0.30, 0.15], [1.13, 0.30, -0.15]].map((p) => ({ p: [p[0] + 0.125, p[1], p[2]], d: [1, 0, 0] })), { r: 0.009, len: 0.05 });

  // Culasse, culbuteurs
  const head = part('culasse', [0, 0.55, 0]);
  head.add(at(rbox(0.42, 0.10, 0.25, 0.012, mat(C.head, { metalness: 0.4, roughness: 0.45 })), EX, 0.67, 0));
  const rockerShaft = rod([EX + 0.20, 0.745, 0.0], [EX - 0.20, 0.745, 0.0], 0.008, mat(C.steel, { metalness: 0.6 }));
  head.add(rockerShaft);
  const adjusters = [];
  for (let i = 0; i < 8; i++) {
    const x = EX + 0.175 - i * 0.05;
    const z = i % 2 ? 0.035 : -0.035;
    const arm = at(rbox(0.018, 0.014, 0.09, 0.005, mat(C.steel, { metalness: 0.6 })), x, 0.752, 0);
    head.add(arm);
    adjusters.push({ p: [x, 0.762, z], d: [0, 1, 0] });
  }
  fasten(head, 'vis-reglage-culbuteurs', adjusters, { r: 0.006, len: 0.02, kind: 'nut', travel: 0.012 });
  // Vis de culasse : rangée gauche 7 5 2 4 10, rangée droite 9 3 1 6 8 (de l'avant vers l'arrière)
  const headBoltX = [0.19, 0.095, 0, -0.095, -0.19].map((d) => EX + d);
  const headBolts = [...headBoltX.map((x) => ({ p: [x, 0.725, -0.112] })), ...headBoltX.map((x) => ({ p: [x, 0.725, 0.112] }))];
  fasten(head, 'vis-culasse', headBolts.map((b) => ({ ...b, d: [0, 1, 0] })), { r: 0.009, len: 0.10, travel: 0.16 });
  fasteners.get('vis-culasse').order = [7, 5, 2, 4, 10, 9, 3, 1, 6, 8];
  // thermocontact d'eau à l'arrière de la culasse
  head.add(at(cyl(0.01, 0.03, mat(C.zinc, { metalness: 0.6 }), 'x', 10), EX - 0.225, 0.67, 0.05));

  const rocker = part('cache-culbuteurs', [0, 0.85, 0]);
  rocker.add(at(rbox(0.40, 0.06, 0.20, 0.025, mat(C.rocker, { roughness: 0.35, metalness: 0.3 })), EX, 0.765, 0.0));
  for (let i = 0; i < 5; i++) rocker.add(at(rbox(0.012, 0.012, 0.16, 0.005, mat(C.rocker, { roughness: 0.35, metalness: 0.3 })), EX + 0.14 - i * 0.07, 0.798, 0));
  rocker.add(at(rbox(0.40, 0.008, 0.21, 0.003, mat(C.black)), EX, 0.735, 0)); // joint
  fasten(rocker, 'bouchon-remplissage-huile', [{ p: [EX - 0.10, 0.796, 0.05], d: [0, 1, 0] }], { r: 0.022, len: 0.015, kind: 'screw', travel: 0.06 });
  fasten(rocker, 'fix-cache-culbuteurs', [[EX + 0.16, 0.796, -0.06], [EX - 0.16, 0.796, -0.06], [EX + 0.16, 0.796, 0.06], [EX - 0.16, 0.796, 0.06]].map((p) => ({ p, d: [0, 1, 0] })), { r: 0.006, len: 0.03, kind: 'nut' });

  const sump = part('carter-huile', [0, -0.45, 0]);
  sump.add(at(rbox(0.40, 0.10, 0.24, 0.02, mat(C.darkSteel, { metalness: 0.4 })), EX, 0.275, 0));
  for (let i = 0; i < 3; i++) sump.add(at(box(0.36, 0.006, 0.005, mat(C.darkSteel)), EX, 0.25 + i * 0.02, 0.122));
  fasten(sump, 'bouchon-vidange', [{ p: [EX - 0.05, 0.225, 0.02], d: [0, -1, 0] }], { r: 0.011, len: 0.018, kind: 'plug', travel: 0.08 });

  // Filtre à huile côté droit (photo RTA, repère 1)
  const oilFilter = part('filtre-huile', [0, -0.05, 0.45]);
  const ofil = lathe([[0, -0.05], [0.04, -0.05], [0.046, -0.04], [0.046, 0.045], [0.04, 0.052], [0, 0.052]], mat(C.blue, { roughness: 0.4, metalness: 0.3 }), 24);
  ofil.rotation.x = -Math.PI / 2;
  at(ofil, EX - 0.11, 0.44, 0.195);
  oilFilter.add(ofil);
  fasteners.set('filtre-huile-cartouche', [{ obj: ofil, dir: new THREE.Vector3(0, 0, 1), base: ofil.position.clone(), q0: ofil.quaternion.clone(), travel: 0.10, spin: true }]);
  ofil.userData.fastener = 'filtre-huile-cartouche';

  const dip = part('jauge', [0, 0.45, 0.1]);
  dip.add(tube([[EX + 0.06, 0.40, 0.135], [EX + 0.08, 0.60, 0.17], [EX + 0.09, 0.80, 0.18]], 0.005, mat(C.darkSteel), false, 14));
  dip.add(at(mesh(new THREE.TorusGeometry(0.016, 0.005, 6, 14), mat(C.yellow)), EX + 0.09, 0.82, 0.18));

  const dist = part('distribution', [-0.35, 0.1, 0]);
  dist.add(at(rbox(0.03, 0.34, 0.24, 0.015, mat(C.darkSteel, { metalness: 0.4 })), EX - 0.226, 0.52, 0));
  for (let i = 0; i < 6; i++) dist.add(at(box(0.004, 0.3, 0.004, mat(C.darkSteel)), EX - 0.243, 0.52, -0.10 + i * 0.04));

  // Bougies côté gauche, fils depuis l'allumeur côté droit
  const plugs = part('bougies', [0, 0.25, -0.4]);
  const plugSpecs = [];
  for (let i = 0; i < 4; i++) plugSpecs.push({ p: [EX + 0.15 - i * 0.10, 0.70, -0.13], d: [0, 0.5, -1] });
  fasten(plugs, 'bougies', plugSpecs, { r: 0.010, len: 0.07, kind: 'spark', travel: 0.10 });

  const distG = part('allumeur', [0, 0.5, 0.25]);
  const capX = EX - 0.17, capY = 0.83, capZ = 0.12;
  distG.add(at(cyl(0.025, 0.12, mat(C.alu, { metalness: 0.4 }), 'y', 14), capX, 0.75, capZ));
  distG.add(at(cyl(0.042, 0.05, mat(C.black, { roughness: 0.4 }), 'y', 18, 0.035), capX, capY, capZ));
  distG.add(at(cyl(0.016, 0.03, mat(C.alu), 'z', 10), capX + 0.03, 0.76, capZ - 0.03)); // capsule à dépression
  distG.add(at(rbox(0.05, 0.008, 0.03, 0.003, mat(C.darkSteel)), capX, 0.71, capZ - 0.03));
  for (let i = 0; i < 4; i++) {
    const a = (i / 4) * Math.PI * 2;
    const from = [capX + Math.cos(a) * 0.022, capY + 0.03, capZ + Math.sin(a) * 0.022];
    const to = [EX + 0.15 - i * 0.10, 0.75, -0.16];
    distG.add(tube([from, [from[0], 0.88, from[2]], [(from[0] + to[0]) / 2, 0.86, 0.02], [to[0], 0.80, -0.12], to], 0.0045, mat(0x8a2a22), false, 24));
  }
  distG.add(tube([[capX, capY + 0.03, capZ], [capX + 0.05, 0.90, capZ + 0.15], [0.86, 0.80, 0.42]], 0.005, mat(0x8a2a22), false, 16)); // fil de bobine
  fasten(distG, 'fix-allumeur', [{ p: [capX + 0.02, 0.715, capZ - 0.03], d: [0, 1, 0] }], { r: 0.006, len: 0.02 });

  const coil = part('bobine', [0, 0.3, 0.3]);
  coil.add(at(cyl(0.03, 0.12, mat(C.black, { roughness: 0.4 }), 'y', 16), 0.86, 0.74, 0.42));
  coil.add(at(cyl(0.012, 0.02, mat(C.black), 'y', 10), 0.86, 0.81, 0.42));

  // Échappement : collecteur 4-en-1 côté gauche, ligne sous la caisse
  // Collecteur (remplacé par celui du modèle détaillé quand il est chargé) et ligne d'échappement
  const exM = () => mat(0x4b4845, { metalness: 0.5, roughness: 0.6 });
  const manifold = part('echappement', [0, -0.35, 0]);
  manifold.userData.replaceKey = 'collecteur';
  for (let i = 0; i < 4; i++) {
    const x = EX + 0.15 - i * 0.10;
    manifold.add(tube([[x, 0.64, -0.13], [x, 0.62, -0.18], [EX + 0.01, 0.56, -0.20], [EX + 0.02, 0.466, -0.16]], 0.016, exM(), false, 14));
  }
  manifold.add(at(rbox(0.30, 0.004, 0.18, 0.002, mat(C.alu, { metalness: 0.6 })), EX, 0.60, -0.23)); // tôle pare-chaleur
  fasten(manifold, 'ecrous-collecteur', [EX + 0.15, EX + 0.05, EX - 0.05, EX - 0.15].map((x) => ({ p: [x + 0.05, 0.66, -0.14], d: [0, 0, -1] })), { r: 0.007, len: 0.03, kind: 'nut' });
  const exh = part('echappement', [0, -0.35, 0]);
  exh.add(tube([[EX + 0.02, 0.466, -0.16], [EX + 0.01, 0.38, -0.18], [0.66, 0.27, -0.16], [-0.20, 0.235, -0.05], [-0.90, 0.23, 0.10], [-1.13, 0.235, 0.20]], 0.02, exM(), false, 60));
  const muffler = lathe([[0, -0.20], [0.07, -0.2], [0.085, -0.17], [0.085, 0.17], [0.07, 0.2], [0, 0.2]], exM(), 18);
  muffler.rotation.z = Math.PI / 2;
  muffler.scale.set(1, 1, 1.35);
  at(muffler, -1.35, 0.235, 0.22);
  exh.add(muffler);
  exh.add(tube([[-1.55, 0.235, 0.24], [-1.80, 0.24, 0.30], [-1.92, 0.25, 0.32]], 0.018, exM(), false, 14));

  // Carburateur sur le collecteur, filtre à air rond par-dessus (photo RTA, repère 13)
  const carb = part('carburateur', [0, 0.35, -0.35]);
  carb.add(at(rbox(0.09, 0.08, 0.09, 0.012, mat(C.castAlu, { metalness: 0.5, roughness: 0.4 })), EX, 0.70, -0.22));
  carb.add(at(rbox(0.06, 0.05, 0.05, 0.01, mat(C.castAlu, { metalness: 0.5 })), EX + 0.065, 0.69, -0.22)); // cuve
  carb.add(at(cyl(0.012, 0.03, mat(C.alu), 'z', 10), EX - 0.05, 0.71, -0.24)); // biellette d'accélérateur
  carb.add(tube([[EX - 0.06, 0.71, -0.26], [0.83, 0.75, -0.40]], 0.003, mat(C.cable), false, 6)); // câble d'accélérateur
  fasten(carb, 'ecrous-carbu', [{ p: [EX + 0.04, 0.665, -0.18], d: [0, 1, 0] }, { p: [EX - 0.04, 0.665, -0.26], d: [0, 1, 0] }], { r: 0.006, len: 0.03, kind: 'nut' });
  fasten(carb, 'vis-ralenti', [{ p: [EX + 0.03, 0.68, -0.27], d: [0, 0, -1] }, { p: [EX - 0.03, 0.68, -0.27], d: [0, 0, -1] }], { r: 0.005, len: 0.02, kind: 'screw', travel: 0.01 });

  const airFilter = part('filtre-air', [0, 0.7, -0.15]);
  const af = lathe([[0, 0.05], [0.10, 0.045], [0.135, 0.03], [0.14, 0.0], [0.135, -0.03], [0.12, -0.035], [0, -0.035]], mat(C.black, { roughness: 0.5, metalness: 0.3 }), 36);
  at(af, EX, 0.80, -0.20);
  airFilter.add(af);
  for (let i = 0; i < 12; i++) { // nervures
    const a = (i / 12) * Math.PI * 2;
    const rib = at(box(0.05, 0.004, 0.006, mat(0x2b2b2b)), EX + Math.cos(a) * 0.08, 0.845, -0.20 + Math.sin(a) * 0.08);
    rib.rotation.y = -a;
    airFilter.add(rib);
  }
  airFilter.add(tube([[EX + 0.12, 0.79, -0.24], [EX + 0.26, 0.78, -0.34], [1.30, 0.76, -0.40]], 0.035, mat(C.black, { roughness: 0.6 }), false, 16)); // prise d'air
  fasten(airFilter, 'ecrou-filtre-air', [{ p: [EX, 0.85, -0.20], d: [0, 1, 0] }], { r: 0.013, len: 0.04, kind: 'nut' });

  const fuelPump = part('pompe-essence', [0, 0, 0.4]);
  fuelPump.add(at(cyl(0.035, 0.045, mat(C.alu, { metalness: 0.4 }), 'z', 18), EX + 0.02, 0.44, 0.175));
  fuelPump.add(tube([[EX + 0.02, 0.47, 0.19], [EX - 0.02, 0.62, 0.12], [EX - 0.02, 0.70, -0.10], [EX + 0.03, 0.72, -0.18]], 0.004, mat(C.cable), false, 20));
  fasten(fuelPump, 'fix-pompe-essence', [{ p: [EX + 0.055, 0.44, 0.158], d: [0, 0, 1] }, { p: [EX - 0.015, 0.44, 0.158], d: [0, 0, 1] }], { r: 0.006, len: 0.03, kind: 'nut' });

  const tank = part('reservoir', [0, -0.35, -0.2]);
  tank.add(at(rbox(0.42, 0.14, 0.55, 0.04, mat(C.darkSteel, { metalness: 0.4 })), -1.05, 0.20, -0.25));
  tank.add(tube([[-0.95, 0.27, -0.50], [-1.05, 0.55, -0.68], [-1.10, 0.70, -0.735]], 0.02, mat(C.rubber), false, 12)); // goulotte
  tank.add(at(cyl(0.035, 0.012, mat(C.darkSteel), 'z', 20), -1.10, 0.70, -0.745)); // bouchon (côté gauche)
  tank.add(tube([[-0.84, 0.25, -0.20], [0.20, 0.25, 0.18], [0.80, 0.30, 0.25], [EX + 0.02, 0.44, 0.21]], 0.004, mat(C.cable), false, 40));

  // ================= REFROIDISSEMENT =================
  const radiator = part('radiateur', [0.5, 0.15, 0]);
  const coreTex = stripesTexture('#6d4a2c', '#2a221b', 16, true);
  radiator.add(at(box(0.04, 0.30, 0.46, mat(0xffffff, { map: coreTex, roughness: 0.7, metalness: 0.3 })), 1.70, 0.58, -0.04));
  radiator.add(at(rbox(0.06, 0.04, 0.48, 0.01, mat(C.darkSteel)), 1.70, 0.75, -0.04));
  radiator.add(at(rbox(0.06, 0.04, 0.48, 0.01, mat(C.darkSteel)), 1.70, 0.41, -0.04));
  radiator.add(at(cyl(0.022, 0.03, mat(C.black), 'y', 16), 1.70, 0.785, -0.22)); // bouchon (repère 10)
  fasten(radiator, 'ecrous-radiateur', [{ p: [1.70, 0.775, 0.17], d: [0, 1, 0] }, { p: [1.70, 0.775, -0.20], d: [0, 1, 0] }], { r: 0.007, len: 0.03, kind: 'nut' });
  fasten(radiator, 'bouchon-vidange-radiateur', [{ p: [1.70, 0.39, 0.15], d: [0, -1, 0] }], { r: 0.007, len: 0.015, kind: 'plug' });

  const fan = part('motoventilateur', [0.3, 0.4, 0]);
  fan.add(at(mesh(new THREE.TorusGeometry(0.155, 0.012, 8, 32), mat(C.black)), 1.655, 0.58, -0.04));
  fan.children[0].rotation.y = Math.PI / 2;
  for (let i = 0; i < 4; i++) {
    const blade = at(rbox(0.006, 0.13, 0.05, 0.003, mat(C.black)), 1.655, 0.58, -0.04);
    blade.rotation.x = (i / 4) * Math.PI;
    blade.translateY(0.065);
    fan.add(blade);
  }
  fan.add(at(cyl(0.045, 0.08, mat(C.darkSteel), 'x', 16), 1.61, 0.58, -0.04));
  fan.add(at(cyl(0.012, 0.02, mat(C.zinc), 'z', 10), 1.70, 0.43, 0.20)); // thermocontact

  const expTank = part('vase-expansion', [0, 0.45, 0.25]);
  expTank.add(at(cyl(0.065, 0.15, mat(0xf2f2ea, { transparent: true, opacity: 0.85, roughness: 0.3 }), 'y', 20), 1.00, 0.80, 0.56));
  expTank.add(at(cyl(0.03, 0.03, mat(C.black), 'y', 16), 1.00, 0.89, 0.56));
  expTank.add(at(cyl(0.064, 0.05, mat(0x3b6fb0, { transparent: true, opacity: 0.6 }), 'y', 20), 1.00, 0.76, 0.56)); // liquide

  const waterPump = part('pompe-eau', [0.25, 0.4, 0]);
  waterPump.add(at(rbox(0.07, 0.12, 0.14, 0.015, mat(C.castAlu, { metalness: 0.4 })), EX + 0.24, 0.67, 0.0));
  const wpPulley = lathe([[0.0, -0.01], [0.06, -0.01], [0.055, 0], [0.06, 0.01], [0, 0.01]], mat(C.darkSteel, { metalness: 0.5 }), 28);
  wpPulley.rotation.z = Math.PI / 2;
  at(wpPulley, EX + 0.285, 0.67, 0.0);
  waterPump.add(wpPulley);
  fasten(waterPump, 'vis-pompe-eau', [[0.05, 0.06], [-0.05, 0.06], [0.05, -0.06], [-0.05, -0.06]].map(([dy, dz]) => ({ p: [EX + 0.275, 0.67 + dy, dz], d: [1, 0, 0] })), { r: 0.006, len: 0.04 });
  fasten(waterPump, 'vis-poulie-pompe', [0, 1, 2].map((i) => { const a = (i / 3) * Math.PI * 2; return { p: [EX + 0.296, 0.67 + Math.cos(a) * 0.025, Math.sin(a) * 0.025], d: [1, 0, 0] }; }), { r: 0.005, len: 0.02 });

  const hoses = part('durites', [0.15, 0.3, 0]);
  const hoseM = () => mat(C.rubber, { roughness: 0.7 });
  hoses.add(tube([[EX + 0.27, 0.72, -0.04], [1.35, 0.76, -0.12], [1.66, 0.74, -0.14]], 0.022, hoseM(), false, 24));
  hoses.add(tube([[EX + 0.25, 0.61, 0.05], [1.30, 0.50, 0.20], [1.66, 0.44, 0.17]], 0.022, hoseM(), false, 24));
  hoses.add(tube([[EX - 0.20, 0.70, -0.08], [0.86, 0.75, -0.30], [0.84, 0.70, -0.45]], 0.014, hoseM(), false, 16)); // chauffage
  hoses.add(tube([[1.00, 0.87, 0.56], [1.20, 0.82, 0.40], [1.68, 0.78, 0.0]], 0.006, hoseM(), false, 16)); // vase → radiateur
  fasten(hoses, 'vis-purge-refroidissement', [{ p: [EX + 0.22, 0.74, -0.02], d: [0, 1, 0] }, { p: [0.86, 0.77, -0.30], d: [0, 1, 0] }], { r: 0.005, len: 0.015, kind: 'screw', travel: 0.012 });

  // ================= TRANSMISSION =================
  const gbM = () => mat(C.castAlu, { metalness: 0.35, roughness: 0.55 });
  const gearbox = part('boite', [0.75, 0.15, 0]);
  gearbox.add(at(rbox(0.30, 0.22, 0.25, 0.03, gbM()), 1.38, 0.43, 0));
  gearbox.add(at(cyl(0.12, 0.30, gbM(), 'z', 24), AXLE_F, 0.34, 0));
  for (const s of [1, -1]) gearbox.add(at(cyl(0.05, 0.03, mat(C.darkSteel), 'z', 18), AXLE_F, 0.32, s * 0.165)); // écrous de réglage
  gearbox.add(at(rbox(0.03, 0.18, 0.22, 0.02, gbM()), 1.545, 0.44, 0)); // couvercle avant
  gearbox.add(at(box(0.012, 0.04, 0.05, mat(C.alu)), 1.565, 0.48, 0.05)); // plaque d'identification
  fasten(gearbox, 'bouchons-boite', [{ p: [AXLE_F + 0.05, 0.22, 0], d: [0, -1, 0] }, { p: [1.42, 0.40, 0.126], d: [0, 0, 1] }], { r: 0.010, len: 0.02, kind: 'plug', travel: 0.06 });
  fasten(gearbox, 'vis-couvercle-boite', [[0.06, 0.08], [-0.06, 0.08], [0.06, -0.08], [-0.06, -0.08]].map(([dy, dz]) => ({ p: [1.56, 0.44 + dy, dz], d: [1, 0, 0] })), { r: 0.006, len: 0.03 });

  const clutch = part('embrayage', [0.25, 0.6, 0.5]);
  const disc = lathe([[0.03, -0.004], [0.09, -0.004], [0.09, 0.004], [0.03, 0.004]], mat(C.lining, { side: THREE.DoubleSide }), 32);
  disc.rotation.z = Math.PI / 2;
  at(disc, 1.155, 0.44, 0);
  clutch.add(disc);
  const cover = lathe([[0.03, 0.0], [0.10, 0.0], [0.10, 0.02], [0.07, 0.03], [0.03, 0.03]], mat(C.steel, { metalness: 0.5, side: THREE.DoubleSide }), 32);
  cover.rotation.z = -Math.PI / 2;
  at(cover, 1.165, 0.44, 0);
  clutch.add(cover);
  clutch.add(at(cyl(0.035, 0.02, mat(C.steel, { metalness: 0.6 }), 'x', 18), 1.21, 0.44, 0)); // butée
  clutch.add(tube([[1.26, 0.52, 0.12], [1.10, 0.62, 0.30], [0.84, 0.66, -0.45]], 0.004, mat(C.cable), false, 20)); // câble
  fasten(clutch, 'vis-mecanisme', [0, 1, 2, 3, 4, 5].map((i) => { const a = (i / 6) * Math.PI * 2; return { p: [1.17, 0.44 + Math.cos(a) * 0.085, Math.sin(a) * 0.085], d: [-1, 0, 0] }; }), { r: 0.006, len: 0.02 });
  fasten(clutch, 'reglage-embrayage', [{ p: [1.27, 0.52, 0.12], d: [1, 0.3, 0.3] }, { p: [1.285, 0.525, 0.125], d: [1, 0.3, 0.3] }], { r: 0.007, len: 0.015, kind: 'nut', travel: 0.02 });

  const shafts = part('transmissions', [0, -0.35, 0]);
  for (const s of [1, -1]) {
    shafts.add(rod([AXLE_F, 0.32, s * 0.19], [AXLE_F, WHEEL_R, s * 0.50], 0.016, mat(C.steel, { metalness: 0.6 })));
    for (const [zz, yy] of [[0.21, 0.318], [0.48, 0.29]]) {
      const boot = lathe([[0.018, -0.045], [0.035, -0.03], [0.026, -0.015], [0.036, 0], [0.026, 0.015], [0.035, 0.03], [0.018, 0.045]], mat(C.rubber, { roughness: 0.8 }), 16);
      boot.rotation.x = Math.PI / 2;
      at(boot, AXLE_F, yy, s * zz);
      shafts.add(boot);
    }
    shafts.add(at(cyl(0.03, 0.05, mat(C.steel, { metalness: 0.6 }), 'z', 16), AXLE_F, WHEEL_R, s * 0.525));
  }

  // ================= TRAINS =================
  const arms = part('triangles-av', [0, -0.25, 0]);
  const armM = () => mat(C.darkSteel, { metalness: 0.4 });
  for (const s of [1, -1]) {
    arms.add(rod([AXLE_F - 0.14, 0.20, s * 0.30], [AXLE_F, 0.20, s * 0.53], 0.016, armM()));
    arms.add(rod([AXLE_F + 0.12, 0.20, s * 0.30], [AXLE_F, 0.20, s * 0.53], 0.016, armM()));
    arms.add(rod([AXLE_F - 0.12, 0.20, s * 0.30], [AXLE_F + 0.12, 0.20, s * 0.30], 0.016, armM()));
    arms.add(rod([AXLE_F - 0.10, 0.48, s * 0.36], [AXLE_F, 0.45, s * 0.52], 0.013, armM()));
    arms.add(rod([AXLE_F + 0.10, 0.48, s * 0.36], [AXLE_F, 0.45, s * 0.52], 0.013, armM()));
    for (const p of [[AXLE_F, 0.20, s * 0.53], [AXLE_F, 0.45, s * 0.52]]) arms.add(at(mesh(new THREE.SphereGeometry(0.022, 12, 10), armM()), ...p));
    fasten(arms, 'ecrous-rotules', [{ p: [AXLE_F, 0.175, s * 0.53], d: [0, -1, 0] }, { p: [AXLE_F, 0.475, s * 0.52], d: [0, 1, 0] }], { r: 0.009, len: 0.03, kind: 'nut' });
  }

  const knuckles = part('porte-fusee', [0, -0.15, 0]);
  for (const s of [1, -1]) {
    knuckles.add(tube([[AXLE_F, 0.20, s * 0.53], [AXLE_F - 0.01, WHEEL_R, s * 0.535], [AXLE_F, 0.45, s * 0.52]], 0.024, mat(C.steel, { metalness: 0.5 }), false, 12));
    knuckles.add(rod([AXLE_F - 0.01, 0.33, s * 0.52], [AXLE_F - 0.10, 0.45, s * 0.52], 0.012, mat(C.steel)));
    fasten(knuckles, 'ecrou-fusee-av', [{ p: [AXLE_F, WHEEL_R, s * 0.585], d: [0, 0, s] }], { r: 0.014, len: 0.03, kind: 'nut', travel: 0.06 });
  }

  const tbarsF = part('barres-torsion-av', [0, -0.3, 0]);
  for (const s of [1, -1]) {
    tbarsF.add(rod([AXLE_F - 0.12, 0.21, s * 0.30], [0.20, 0.25, s * 0.32], 0.0085, mat(C.green, { metalness: 0.3 })));
    tbarsF.add(at(rbox(0.06, 0.06, 0.10, 0.012, mat(C.darkSteel)), 0.18, 0.25, s * 0.32)); // palier d'ancrage
    fasten(tbarsF, 'vis-palier-torsion', [[0.165, 0.30, s * 0.29], [0.165, 0.30, s * 0.35], [0.20, 0.30, s * 0.32]].map((p) => ({ p, d: [0, 1, 0] })), { r: 0.008, len: 0.035 });
  }

  const shocksF = part('amortisseurs-av', [0, 0.25, 0]);
  for (const s of [1, -1]) {
    shocksF.add(rod([AXLE_F + 0.04, 0.22, s * 0.47], [AXLE_F + 0.11, 0.45, s * 0.46], 0.022, mat(C.yellow, { roughness: 0.4 })));
    shocksF.add(rod([AXLE_F + 0.11, 0.45, s * 0.46], [AXLE_F + 0.17, 0.62, s * 0.45], 0.008, chromeM()));
    fasten(shocksF, 'fix-amortisseurs-av', [{ p: [AXLE_F + 0.04, 0.22, s * 0.50], d: [0, 0, s] }, { p: [AXLE_F + 0.17, 0.64, s * 0.45], d: [0, 1, 0] }], { r: 0.008, len: 0.03, kind: 'nut' });
  }

  const rack = part('direction', [0, 0.25, 0]);
  rack.add(at(cyl(0.025, 0.62, mat(C.darkSteel), 'z', 14), 1.05, 0.52, 0));
  for (const s of [1, -1]) {
    const boot = lathe([[0.02, -0.04], [0.032, -0.025], [0.022, -0.01], [0.032, 0.005], [0.022, 0.02], [0.016, 0.04]], mat(C.rubber), 14);
    boot.rotation.x = s * Math.PI / 2;
    at(boot, 1.05, 0.52, s * 0.34);
    rack.add(boot);
    rack.add(rod([1.05, 0.52, s * 0.37], [AXLE_F - 0.10, 0.45, s * 0.52], 0.009, mat(C.steel)));
  }
  rack.add(rod([0.80, 0.76, -0.35], [1.04, 0.55, -0.22], 0.015, mat(C.darkSteel)));
  rack.add(at(cyl(0.03, 0.02, mat(C.rubber), 'y', 14), 0.92, 0.66, -0.29)); // joint souple
  fasten(rack, 'fix-direction', [[1.05, 0.55, 0.22], [1.05, 0.55, -0.22]].map((p) => ({ p, d: [0, 1, 0] })), { r: 0.008, len: 0.04 });

  const rearArms = part('bras-ar', [0, -0.25, 0]);
  rearArms.add(at(rbox(0.46, 0.07, 0.07, 0.02, mat(C.darkSteel)), (-0.70 + AXLE_R_RIGHT) / 2, 0.285, 0.50));
  rearArms.add(at(rbox(0.46, 0.07, 0.07, 0.02, mat(C.darkSteel)), (-0.65 + AXLE_R_LEFT) / 2, 0.285, -0.50));
  rearArms.add(at(cyl(0.04, 0.12, mat(C.darkSteel), 'z', 16), -0.70, 0.28, 0.48));
  rearArms.add(at(cyl(0.04, 0.12, mat(C.darkSteel), 'z', 16), -0.65, 0.28, -0.48));

  const tbarsR = part('barres-torsion-ar', [0, -0.35, 0]);
  tbarsR.add(rod([-0.70, 0.26, -0.60], [-0.70, 0.26, 0.48], 0.01, mat(C.green, { metalness: 0.3 })));
  tbarsR.add(rod([-0.65, 0.26, -0.48], [-0.65, 0.26, 0.60], 0.01, mat(C.green, { metalness: 0.3 })));

  const shocksR = part('amortisseurs-ar', [0, 0.2, 0]);
  for (const [x0, s] of [[AXLE_R_RIGHT, 1], [AXLE_R_LEFT, -1]]) {
    shocksR.add(rod([x0 + 0.02, 0.25, s * 0.45], [x0 + 0.30, 0.31, s * 0.45], 0.021, mat(C.yellow, { roughness: 0.4 })));
    shocksR.add(rod([x0 + 0.30, 0.31, s * 0.45], [x0 + 0.55, 0.36, s * 0.45], 0.008, chromeM()));
    fasten(shocksR, 'fix-amortisseurs-ar', [{ p: [x0 + 0.02, 0.25, s * 0.48], d: [0, 0, s] }, { p: [x0 + 0.56, 0.36, s * 0.48], d: [0, 0, s] }], { r: 0.008, len: 0.03, kind: 'nut' });
  }

  // ================= FREINS =================
  for (const s of [1, -1]) {
    const discG = part('disques-av', [0, 0, s * 0.35]);
    const d = lathe([[0.04, -0.03], [0.07, -0.03], [0.07, -0.005], [0.114, -0.005], [0.114, 0.005], [0.06, 0.005], [0.06, -0.025], [0.04, -0.025]], mat(C.steel, { metalness: 0.65, roughness: 0.35, side: THREE.DoubleSide }), 40);
    d.rotation.x = -s * Math.PI / 2;
    at(d, AXLE_F, WHEEL_R, s * 0.548);
    discG.add(d);
    const cal = part('etriers-av', [0, 0.15, s * 0.55]);
    const calM = mat(0x7a7f84, { metalness: 0.5, roughness: 0.45 });
    cal.add(at(rbox(0.09, 0.055, 0.06, 0.015, calM), AXLE_F - 0.075, WHEEL_R + 0.075, s * 0.548));
    cal.add(at(rbox(0.07, 0.008, 0.012, 0.003, mat(C.lining)), AXLE_F - 0.075, WHEEL_R + 0.1, s * 0.538)); // plaquette intérieure
    cal.add(at(rbox(0.07, 0.008, 0.012, 0.003, mat(C.lining)), AXLE_F - 0.075, WHEEL_R + 0.1, s * 0.558)); // plaquette extérieure
    cal.add(tube([[AXLE_F - 0.10, WHEEL_R + 0.09, s * 0.53], [AXLE_F - 0.15, 0.45, s * 0.48], [AXLE_F - 0.20, 0.50, s * 0.40]], 0.004, mat(C.cable), false, 12)); // flexible
    fasten(cal, 'clavettes-dba', [{ p: [AXLE_F - 0.075, WHEEL_R + 0.105, s * 0.548], d: [1, 0, 0] }, { p: [AXLE_F - 0.075, WHEEL_R + 0.045, s * 0.548], d: [1, 0, 0] }], { r: 0.0035, len: 0.08, kind: 'pin', travel: 0.10 });
    fasten(cal, 'vis-purge-freins', [{ p: [AXLE_F - 0.10, WHEEL_R + 0.105, s * 0.52], d: [0, 1, 0] }], { r: 0.005, len: 0.015, travel: 0.008 });
  }
  for (const [x0, s] of [[AXLE_R_RIGHT, 1], [AXLE_R_LEFT, -1]]) {
    const drumG = part('tambours-ar', [0, 0, s * 0.4]);
    const drum = lathe([[0.0, -0.03], [0.10, -0.03], [0.10, 0.03], [0.095, 0.035], [0.04, 0.035], [0.0, 0.035]], mat(C.darkSteel, { metalness: 0.4, side: THREE.DoubleSide }), 32);
    drum.rotation.x = -s * Math.PI / 2;
    at(drum, x0, WHEEL_R, s * 0.54);
    drumG.add(drum);
    drumG.add(at(cyl(0.105, 0.006, mat(C.darkSteel), 'z', 32), x0, WHEEL_R, s * 0.50)); // flasque
    fasten(drumG, 'ecrou-fusee-ar', [{ p: [x0, WHEEL_R, s * 0.575], d: [0, 0, s] }], { r: 0.013, len: 0.02, kind: 'nut', travel: 0.06 });
    fasten(drumG, 'vis-purge-freins', [{ p: [x0 + 0.02, WHEEL_R + 0.08, s * 0.495], d: [0, 0, -s] }], { r: 0.005, len: 0.015, travel: 0.008 });
  }

  const master = part('maitre-cylindre', [0.2, 0.45, -0.2]);
  master.add(at(cyl(0.025, 0.14, mat(C.castAlu, { metalness: 0.4 }), 'x', 16), 0.90, 0.80, -0.42));
  master.add(at(rbox(0.09, 0.07, 0.07, 0.015, mat(0xeeeeee, { transparent: true, opacity: 0.85 })), 0.92, 0.86, -0.42));
  master.add(at(cyl(0.022, 0.015, mat(C.black), 'y', 16), 0.92, 0.903, -0.42));
  master.add(at(cyl(0.06, 0.04, mat(C.black), 'x', 24), 0.855, 0.80, -0.42)); // servo absent : bride de tablier
  master.add(tube([[0.97, 0.80, -0.42], [1.10, 0.70, -0.30], [1.15, 0.50, -0.42], [AXLE_F - 0.20, 0.50, -0.40]], 0.003, mat(C.copper, { metalness: 0.7 }), false, 30));
  master.add(tube([[0.97, 0.79, -0.42], [0.60, 0.29, -0.20], [-0.80, 0.29, 0.18]], 0.003, mat(C.copper, { metalness: 0.7 }), false, 40));
  fasten(master, 'vis-maitre-cylindre', [{ p: [0.84, 0.84, -0.42], d: [-1, 0, 0] }, { p: [0.84, 0.76, -0.42], d: [-1, 0, 0] }], { r: 0.007, len: 0.03, kind: 'nut' });

  const limiter = part('limiteur', [0, -0.3, 0.2]);
  limiter.add(at(rbox(0.07, 0.05, 0.05, 0.01, mat(C.castAlu)), -0.80, 0.30, 0.18));
  limiter.add(rod([-0.80, 0.30, 0.18], [AXLE_R_RIGHT + 0.1, 0.285, 0.45], 0.004, mat(C.steel)));

  // ================= ÉLECTRICITÉ =================
  // Batterie à l'avant droit (photo RTA, repère 5), robinet sur la borne négative (repère 7)
  const battery = part('batterie', [0.2, 0.55, 0.3]);
  battery.add(at(rbox(0.18, 0.17, 0.13, 0.01, mat(0xe8e2cf, { roughness: 0.7 })), 1.50, 0.69, 0.48));
  battery.add(at(rbox(0.18, 0.02, 0.13, 0.008, mat(C.black)), 1.50, 0.785, 0.48));
  for (let i = 0; i < 6; i++) battery.add(at(cyl(0.008, 0.01, mat(C.black), 'y', 10), 1.43 + i * 0.028, 0.80, 0.48));
  battery.add(at(cyl(0.012, 0.025, mat(C.red), 'y', 10), 1.43, 0.805, 0.53));
  battery.add(at(cyl(0.012, 0.025, mat(C.darkSteel), 'y', 10), 1.57, 0.805, 0.53));
  battery.add(tube([[1.43, 0.82, 0.53], [1.35, 0.86, 0.45], [1.15, 0.50, 0.25], [1.10, 0.38, 0.22]], 0.008, mat(C.red), false, 20));
  battery.add(tube([[1.57, 0.82, 0.53], [1.62, 0.80, 0.55], [1.62, 0.60, 0.60]], 0.008, mat(C.cable), false, 12));
  battery.add(at(rbox(0.02, 0.015, 0.14, 0.005, mat(C.darkSteel)), 1.50, 0.79, 0.48)); // bride
  fasten(battery, 'bornes-batterie', [{ p: [1.43, 0.825, 0.53], d: [0, 1, 0] }, { p: [1.57, 0.825, 0.53], d: [0, 1, 0] }], { r: 0.007, len: 0.02, kind: 'nut' });

  // Alternateur au centre côté droit (repère 12), courroie (repère 11)
  const alt = part('alternateur', [0.2, 0.1, 0.45]);
  const altBody = lathe([[0, -0.06], [0.06, -0.06], [0.068, -0.04], [0.068, 0.04], [0.06, 0.06], [0, 0.06]], mat(C.alu, { metalness: 0.45, roughness: 0.4 }), 24);
  altBody.rotation.z = -Math.PI / 2;
  at(altBody, EX + 0.14, 0.58, 0.22);
  alt.add(altBody);
  for (let i = 0; i < 10; i++) alt.add(at(box(0.10, 0.004, 0.004, mat(C.darkSteel)), EX + 0.14, 0.58 + Math.cos(i * 0.63) * 0.069, 0.22 + Math.sin(i * 0.63) * 0.069));
  const altPulley = lathe([[0, -0.008], [0.035, -0.008], [0.03, 0], [0.035, 0.008], [0, 0.008]], mat(C.darkSteel, { metalness: 0.5 }), 20);
  altPulley.rotation.z = Math.PI / 2;
  at(altPulley, EX + 0.285, 0.58, 0.22);
  alt.add(altPulley);
  alt.add(at(cyl(0.03, 0.012, mat(C.black), 'x', 20), EX + 0.21, 0.58, 0.22)); // ventilateur
  // Courroie : poulie d'arbre à cames → pompe à eau → alternateur
  alt.add(tube([[EX + 0.288, 0.52, -0.08], [EX + 0.288, 0.73, -0.02], [EX + 0.288, 0.62, 0.25], [EX + 0.288, 0.545, 0.24], [EX + 0.288, 0.47, -0.05]], 0.005, mat(C.black, { roughness: 0.8 }), true, 60));
  alt.add(at(cyl(0.05, 0.016, mat(C.darkSteel, { metalness: 0.5 }), 'x', 24), EX + 0.288, 0.50, -0.07)); // poulie d'AAC
  alt.add(rod([EX + 0.10, 0.62, 0.27], [EX + 0.05, 0.70, 0.20], 0.006, mat(C.darkSteel))); // tendeur
  fasten(alt, 'pivot-alternateur', [{ p: [EX + 0.215, 0.52, 0.22], d: [1, 0, 0] }], { r: 0.008, len: 0.15, travel: 0.20 });
  fasten(alt, 'tendeur-courroie', [{ p: [EX + 0.10, 0.625, 0.275], d: [0, 0.4, 1] }, { p: [EX + 0.05, 0.705, 0.205], d: [0, 1, 0] }], { r: 0.007, len: 0.03, travel: 0.03 });

  const starter = part('demarreur', [0, -0.2, 0.45]);
  starter.add(at(cyl(0.045, 0.16, mat(C.darkSteel, { metalness: 0.4 }), 'x', 18), 1.08, 0.35, 0.19));
  starter.add(at(cyl(0.022, 0.08, mat(C.darkSteel, { metalness: 0.4 }), 'x', 14), 1.10, 0.405, 0.19)); // solénoïde
  fasten(starter, 'vis-demarreur', [{ p: [1.18, 0.40, 0.22], d: [1, 0, 0] }, { p: [1.18, 0.30, 0.22], d: [1, 0, 0] }, { p: [1.00, 0.35, 0.235], d: [-1, 0, 0] }], { r: 0.008, len: 0.05 });

  // Boîte à fusibles sur le tablier (repère 15)
  const fuseBox = part('fusibles', [0.25, 0.3, 0]);
  fuseBox.add(at(rbox(0.035, 0.07, 0.16, 0.008, mat(C.black)), 0.85, 0.80, -0.22));
  fuseBox.add(at(box(0.004, 0.06, 0.15, mat(0xd9d4c3, { transparent: true, opacity: 0.5 })), 0.869, 0.80, -0.22));
  fasten(fuseBox, 'fusibles-cartouches', [0, 1, 2, 3].map((i) => ({ p: [0.865, 0.80, -0.27 + i * 0.033], d: [1, 0, 0] })), { r: 0.006, len: 0.03, kind: 'fuse', travel: 0.06 });

  // Projecteurs ronds
  const lights = part('phares', [0.4, 0.15, 0]);
  for (const s of [1, -1]) {
    const lens = lathe([[0, 0.02], [0.05, 0.015], [0.08, 0.005], [0.082, 0]], mat(0xfff6d1, { emissive: 0x5a4a12, roughness: 0.1, transparent: true, opacity: 0.9 }), 28);
    lens.rotation.z = -Math.PI / 2;
    at(lens, 1.865, 0.62, s * 0.50);
    lights.add(lens);
    lights.add(at(mesh(new THREE.TorusGeometry(0.083, 0.008, 8, 28), chromeM()), 1.866, 0.62, s * 0.50));
    lights.children[lights.children.length - 1].rotation.y = Math.PI / 2;
    lights.add(at(cyl(0.07, 0.10, mat(C.black), 'x', 20), 1.80, 0.62, s * 0.50)); // cuvelage
    lights.add(at(cyl(0.035, 0.03, mat(C.black), 'x', 14), 1.74, 0.62, s * 0.50)); // capuchon arrière
  }

  const tails = part('feux', [0, 0.15, 0]);
  for (const s of [1, -1]) {
    tails.add(at(rbox(0.03, 0.22, 0.075, 0.012, mat(C.red, { emissive: 0x2a0000, roughness: 0.3 })), -1.84, 0.68, s * 0.665));
    tails.add(at(rbox(0.032, 0.06, 0.075, 0.012, mat(C.orange, { emissive: 0x2a1300, roughness: 0.3 })), -1.84, 0.54, s * 0.665));
    tails.add(at(rbox(0.04, 0.04, 0.10, 0.012, mat(C.orange, { emissive: 0x2a1300, roughness: 0.3 })), 1.85, 0.44, s * 0.58)); // clignotant avant
    tails.add(at(rbox(0.05, 0.02, 0.012, 0.005, mat(C.orange, { emissive: 0x2a1300 })), 1.20, 0.70, s * 0.765)); // répétiteur
    fasten(tails, 'vis-feux-ar', [{ p: [-1.858, 0.74, s * 0.665], d: [-1, 0, 0] }, { p: [-1.858, 0.53, s * 0.665], d: [-1, 0, 0] }], { r: 0.004, len: 0.02, kind: 'screw' });
    fasten(tails, 'vis-feux-av', [{ p: [1.872, 0.44, s * 0.58], d: [1, 0, 0] }], { r: 0.004, len: 0.02, kind: 'screw' });
  }

  const wipers = part('essuie-glace', [0.2, 0.4, 0]);
  wipers.add(tube([[0.86, 0.965, -0.48], [0.74, 1.08, -0.30], [0.62, 1.20, -0.10]], 0.006, black(), false, 10));
  wipers.add(tube([[0.86, 0.965, 0.08], [0.74, 1.08, 0.26], [0.62, 1.20, 0.46]], 0.006, black(), false, 10));
  wipers.add(at(rbox(0.09, 0.06, 0.12, 0.015, mat(C.darkSteel)), 0.76, 0.90, 0.25));
  wipers.add(rod([0.76, 0.92, 0.25], [0.86, 0.95, -0.48], 0.004, mat(C.steel)));

  const washer = part('lave-glace', [0, 0.4, 0.3]);
  washer.add(at(rbox(0.12, 0.14, 0.10, 0.02, mat(0xe9edf0, { transparent: true, opacity: 0.85 })), 1.25, 0.76, 0.60));
  washer.add(at(cyl(0.02, 0.02, mat(C.blue), 'y', 14), 1.25, 0.84, 0.60));

  // Ombres + matériaux d'origine mémorisés pour la mise en évidence.
  root.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = !o.userData.glass;
      o.receiveShadow = true;
      o.userData.baseOpacity = o.material.opacity ?? 1;
      o.userData.baseTransparent = o.material.transparent;
      o.userData.baseEmissive = o.material.emissive.getHex();
    }
  });
  for (const groups of parts.values()) for (const g of groups) g.userData.basePos = g.position.clone();

  return { root, parts, fasteners };
}

// Couleur de carrosserie modifiable à chaud.
export function setBodyColor(parts, hex) {
  for (const groups of parts.values()) for (const g of groups) {
    g.traverse((o) => { if (o.isMesh && o.material.userData.paint) o.material.color.set(hex); });
  }
}

// Modèles détaillés faits dans Blender (tools/blender). Ils remplacent les pièces procédurales
// de même id une fois chargés ; si le chargement échoue, le modèle procédural reste affiché.
// Chaque nœud glTF porte extras.partId (pièce) ou extras.fx (fixation : jeu, sens, course).
export const MODELS = [
  {
    url: 'models/moteur.glb',
    replaces: ['bloc', 'culasse', 'cache-culbuteurs', 'carter-huile', 'filtre-huile', 'jauge', 'distribution', 'bougies',
      'allumeur', 'carburateur', 'filtre-air', 'pompe-essence', 'pompe-eau', 'collecteur'],
  },
  {
    url: 'models/transmission.glb',
    replaces: ['embrayage', 'boite', 'transmissions'],
  },
  {
    url: 'models/trains.glb',
    replaces: ['triangles-av', 'porte-fusee', 'barres-torsion-av', 'amortisseurs-av', 'direction',
      'bras-ar', 'barres-torsion-ar', 'amortisseurs-ar', 'disques-av', 'etriers-av', 'tambours-ar'],
  },
  {
    url: 'models/caisse.glb',
    replaces: ['caisse', 'portes', 'hayon', 'capot', 'vitrage', 'pare-chocs', 'calandre', 'phares', 'feux', 'essuie-glace'],
  },
  {
    url: 'models/chassis.glb',
    replaces: ['plateforme', 'roues', 'roue-secours', 'reservoir', 'echappement'],
  },
  {
    url: 'models/interieur.glb',
    replaces: ['sieges-av', 'banquette', 'planche-bord', 'volant', 'levier-vitesses', 'pedalier', 'frein-main'],
  },
  {
    url: 'models/equipements.glb',
    replaces: ['radiateur', 'motoventilateur', 'vase-expansion', 'durites', 'batterie', 'alternateur', 'demarreur',
      'fusibles', 'bobine', 'lave-glace', 'maitre-cylindre', 'limiteur'],
  },
];

export async function loadModels({ root, parts, fasteners }, models = MODELS) {
  const loader = new GLTFLoader();
  // téléchargements en parallèle, remplacement dans l'ordre ; un modèle absent laisse sa version simplifiée
  const loads = models.map(({ url }) => loader.loadAsync(url).catch((e) => { console.warn('Modèle non chargé :', url, e); return null; }));
  for (const [i, { url, replaces }] of models.entries()) {
    const gltf = await loads[i];
    if (!gltf) continue;
    // 1. retire les pièces procédurales remplacées (et leurs fixations)
    const drop = new Set(replaces);
    for (const [id, groups] of parts) {
      const keep = groups.filter((g) => g.userData.model || (!(drop.has(id) && !g.userData.replaceKey) && !drop.has(g.userData.replaceKey)));
      for (const g of groups) if (!keep.includes(g)) root.remove(g);
      if (keep.length) parts.set(id, keep); else parts.delete(id);
    }
    for (const [setId, list] of fasteners) {
      const kept = list.filter((f) => { let o = f.obj; while (o && o !== root) o = o.parent; return o === root; });
      if (kept.length !== list.length) { if (kept.length) { kept.order = list.order; fasteners.set(setId, kept); } else fasteners.delete(setId); }
    }
    // 2. ajoute les pièces du modèle
    const fresh = [];
    for (const node of [...gltf.scene.children]) {
      const id = node.userData.partId;
      if (!id) continue;
      const g = new THREE.Group();
      g.userData.partId = id;
      g.userData.model = url;
      g.userData.explode = new THREE.Vector3(...(node.userData.explode || [0, 0, 0]));
      for (const child of [...node.children]) {
        const fx = child.userData.fx;
        g.add(child);
        if (fx) {
          if (!fasteners.has(fx)) fasteners.set(fx, []);
          child.userData.fastener = fx;
          child.traverse((c) => { if (c.isMesh) c.userData.fastener = fx; });
          const idx = +child.name.split('.').pop() || 0;
          fasteners.get(fx).push({ obj: child, idx, dir: new THREE.Vector3(...child.userData.dir).normalize(), base: child.position.clone(), q0: child.quaternion.clone(), travel: child.userData.travel, spin: !['pin', 'fuse'].includes(child.userData.kind) });
        }
      }
      root.add(g);
      if (!parts.has(id)) parts.set(id, []);
      parts.get(id).push(g);
      fresh.push(g);
    }
    for (const list of fasteners.values()) list.sort((a, b) => (a.idx ?? 0) - (b.idx ?? 0));
    if (fasteners.has('vis-culasse')) fasteners.get('vis-culasse').order = [7, 5, 2, 4, 10, 9, 3, 1, 6, 8];
    // 3. un matériau par maillage (la mise en évidence modifie le matériau), ombres, état de base
    for (const g of fresh) {
      g.userData.basePos = g.position.clone();
      g.traverse((o) => {
        if (!o.isMesh) return;
        o.material = o.material.clone();
        // matériaux nommés dans les scripts Blender : peinture (couleur modifiable) et vitres
        if (o.material.name === 'peinture') o.material.userData.paint = true;
        if (o.material.name === 'vitre') { o.userData.glass = true; o.material.depthWrite = false; }
        o.castShadow = !o.userData.glass;
        o.receiveShadow = true;
        o.userData.baseOpacity = o.material.opacity ?? 1;
        o.userData.baseTransparent = o.material.transparent;
        o.userData.baseEmissive = o.material.emissive.getHex();
      });
    }
  }
}
