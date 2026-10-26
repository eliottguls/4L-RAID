// Modèle 3D procédural d'une Renault 4 GTL, construit à partir des cotes de la RTA.
// Repère : x vers l'avant, y vers le haut, z vers la droite du conducteur. Unités : mètres.
// Chaque pièce est un THREE.Group portant userData.partId (clé de PARTS dans data.js)
// et userData.explode (décalage de la vue éclatée).
import * as THREE from 'three';

const AXLE_F = 1.306;          // essieu avant (porte-à-faux 528 mm)
const AXLE_R_RIGHT = -1.143;   // empattement droit 2 449 mm
const AXLE_R_LEFT = -1.095;    // empattement gauche 2 401 mm
const TRACK_F = 0.64;
const TRACK_R = 0.624;
const WHEEL_R = 0.285;

const COLORS = {
  steel: 0x8f969c, darkSteel: 0x4a4f55, alu: 0xb9bec2, black: 0x1d1f21, rubber: 0x232425,
  chrome: 0xd6d9dc, glass: 0x9fc3d6, seat: 0x6d6258, dash: 0x2e2c2b, block: 0x7c858c,
  head: 0xb4b8ba, rocker: 0x9a3b2f, red: 0xc2332b, blue: 0x2f6fb0, copper: 0xb0703a,
  yellow: 0xd7b33a, orange: 0xe07a2b, green: 0x4d8a57, brake: 0x6f5a4c,
};

function mat(color, opts = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.62, metalness: 0.12, ...opts });
}

function box(w, h, d, color, opts) {
  return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(color, opts));
}

// Cylindre le long d'un axe ('x', 'y' ou 'z').
function cyl(r, len, color, axis = 'y', seg = 20, opts) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), mat(color, opts));
  if (axis === 'x') m.rotation.z = Math.PI / 2;
  if (axis === 'z') m.rotation.x = Math.PI / 2;
  return m;
}

// Tube droit entre deux points.
function rod(a, b, r, color, seg = 10) {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const len = va.distanceTo(vb);
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), mat(color));
  m.position.copy(va).add(vb).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vb.clone().sub(va).normalize());
  return m;
}

function extrudeProfile(points, depth, color, opts) {
  const s = new THREE.Shape();
  points.forEach(([x, y], i) => (i ? s.lineTo(x, y) : s.moveTo(x, y)));
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false });
  return new THREE.Mesh(g, mat(color, opts));
}

function at(obj, x, y, z) { obj.position.set(x, y, z); return obj; }

export function buildCar({ bodyColor = 0xe9e6dc } = {}) {
  const root = new THREE.Group();
  const parts = new Map();

  // Crée un groupe de pièce et l'enregistre.
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

  const paint = (o = {}) => ({ roughness: 0.45, metalness: 0.15, ...o });

  // ================= CARROSSERIE =================
  // Flanc avec passages de roue.
  function sidePanelGeometry() {
    const s = new THREE.Shape();
    s.moveTo(1.80, 0.33);
    s.lineTo(1.83, 0.78);
    s.lineTo(1.72, 0.855);
    s.lineTo(0.80, 0.95);
    s.lineTo(-1.80, 0.97);
    s.lineTo(-1.835, 0.42);
    s.lineTo(-1.76, 0.33);
    s.lineTo(-1.12 - 0.37, 0.33);
    s.absarc(-1.12, 0.30, 0.37, Math.PI, 0, true);
    s.lineTo(AXLE_F - 0.37, 0.33);
    s.absarc(AXLE_F, 0.30, 0.37, Math.PI, 0, true);
    s.lineTo(1.80, 0.33);
    return new THREE.ExtrudeGeometry(s, { depth: 0.025, bevelEnabled: false });
  }
  const sideGeo = sidePanelGeometry();
  const sideL = new THREE.Mesh(sideGeo, mat(bodyColor, paint()));
  sideL.position.z = -0.755;
  const sideR = new THREE.Mesh(sideGeo, mat(bodyColor, paint()));
  sideR.position.z = 0.73;

  const firewall = at(box(0.03, 0.62, 1.46, bodyColor, paint()), 0.82, 0.64, 0);
  const cowl = at(box(0.14, 0.03, 1.46, bodyColor, paint()), 0.80, 0.945, 0);
  const rearPanel = at(box(0.03, 0.16, 1.46, bodyColor, paint()), -1.82, 0.39, 0);
  const roof = at(box(2.0, 0.03, 1.40, bodyColor, paint()), -0.70, 1.505, 0);
  const pillars = [];
  for (const z of [-0.69, 0.69]) {
    pillars.push(rod([0.80, 0.95, z], [0.30, 1.49, z], 0.025, bodyColor));
    pillars.push(at(box(0.07, 0.55, 0.03, bodyColor, paint()), -0.03, 1.22, z));
    pillars.push(at(box(0.09, 0.55, 0.03, bodyColor, paint()), -0.80, 1.23, z));
    pillars.push(rod([-1.81, 0.98, z], [-1.70, 1.49, z], 0.03, bodyColor));
  }
  part('caisse', [0, 0.25, 0], [sideL, sideR, firewall, cowl, rearPanel, roof, ...pillars]);

  // Vitrages (verrière + pare-brise)
  const glassMat = { transparent: true, opacity: 0.28, roughness: 0.05, metalness: 0.3, depthWrite: false };
  const greenhouse = extrudeProfile([[0.80, 0.955], [0.30, 1.49], [-1.70, 1.49], [-1.81, 0.975]], 1.37, COLORS.glass, glassMat);
  greenhouse.position.z = -0.685;
  greenhouse.userData.glass = true;
  part('vitrage', [0, 0.55, 0], [greenhouse]);

  // Capot (articulé à l'avant sur la 4L)
  const hood = extrudeProfile([[0.84, 0.958], [1.72, 0.868], [1.845, 0.80], [1.845, 0.775], [1.71, 0.842], [0.84, 0.932]], 1.47, bodyColor, paint());
  hood.position.z = -0.735;
  part('capot', [0.35, 0.65, 0], [hood]);

  // Portes
  function door(x0, x1, z, sign) {
    const g = new THREE.Group();
    const panel = extrudeProfile([[x0, 0.35], [x1, 0.35], [x1, 0.955], [x0, 0.955]], 0.02, bodyColor, paint());
    panel.position.z = z;
    g.add(panel);
    // Encadrement de vitre : la porte avant suit l'inclinaison du montant de pare-brise.
    const fz = z + 0.01 - sign * 0.04;
    const front = x1 > 0.5;
    const topEnd = front ? 0.31 : x1;
    g.add(rod([x0, 1.44, fz], [topEnd, 1.44, fz], 0.012, bodyColor));
    if (front) g.add(rod([topEnd, 1.44, fz], [x1, 0.96, fz], 0.012, bodyColor));
    const frameBack = at(box(0.025, 0.48, 0.02, bodyColor, paint()), Math.min(x0, x1) + 0.015, 1.20, fz);
    const handle = at(box(0.10, 0.02, 0.02, COLORS.chrome, { metalness: 0.8, roughness: 0.25 }), Math.min(x0, x1) + 0.09, 0.86, z + sign * 0.02 + 0.01);
    g.add(frameBack, handle);
    return g;
  }
  part('portes', [0, 0, 0.55], [door(-0.02, 0.74, 0.755, 1)]);
  part('portes', [0, 0, 0.55], [door(-0.78, -0.05, 0.755, 1)]);
  part('portes', [0, 0, -0.55], [door(-0.02, 0.74, -0.775, -1)]);
  part('portes', [0, 0, -0.55], [door(-0.78, -0.05, -0.775, -1)]);

  // Hayon
  const hatchPanel = at(box(0.03, 0.52, 1.30, bodyColor, paint()), -1.835, 0.71, 0);
  hatchPanel.rotation.z = 0.06;
  const hatchFrame = rod([-1.81, 1.47, -0.64], [-1.81, 1.47, 0.64], 0.02, bodyColor);
  const hatchHandle = at(box(0.03, 0.03, 0.18, COLORS.chrome, { metalness: 0.8, roughness: 0.25 }), -1.86, 0.92, 0);
  part('hayon', [-0.55, 0.35, 0], [hatchPanel, hatchFrame, hatchHandle]);

  // Pare-chocs
  const bumperF = at(box(0.08, 0.09, 1.50, COLORS.darkSteel, { metalness: 0.4 }), 1.87, 0.40, 0);
  const bumperR = at(box(0.08, 0.09, 1.50, COLORS.darkSteel, { metalness: 0.4 }), -1.87, 0.40, 0);
  part('pare-chocs', [0.45, 0, 0], [bumperF]);
  part('pare-chocs', [-0.45, 0, 0], [bumperR]);

  // Calandre
  const grille = new THREE.Group();
  grille.add(at(box(0.03, 0.30, 0.78, COLORS.black), 1.835, 0.60, 0));
  for (let i = 0; i < 5; i++) grille.add(at(box(0.035, 0.018, 0.74, COLORS.darkSteel, { metalness: 0.5 }), 1.84, 0.49 + i * 0.055, 0));
  grille.add(at(box(0.035, 0.08, 0.10, COLORS.chrome, { metalness: 0.8, roughness: 0.2 }), 1.845, 0.62, 0)); // losange
  part('calandre', [0.4, 0, 0], [grille]);

  // ================= PLATEFORME =================
  const floor = at(box(2.55, 0.04, 1.40, COLORS.darkSteel), -0.45, 0.28, 0);
  const rails = [];
  for (const z of [-0.42, 0.42]) rails.push(at(box(1.05, 0.08, 0.06, COLORS.darkSteel), 1.30, 0.32, z));
  const cross = at(box(0.06, 0.08, 0.90, COLORS.darkSteel), 1.70, 0.34, 0);
  part('plateforme', [0, -0.45, 0], [floor, ...rails, cross]);

  // ================= ROUES =================
  function wheel(x, z) {
    const g = new THREE.Group();
    const tire = new THREE.Mesh(new THREE.TorusGeometry(WHEEL_R - 0.055, 0.058, 12, 28), mat(COLORS.rubber, { roughness: 0.9 }));
    tire.scale.set(1, 1, 1.25);
    const rim = cyl(0.19, 0.11, COLORS.steel, 'z', 24, { metalness: 0.5, roughness: 0.4 });
    const hub = cyl(0.06, 0.13, COLORS.chrome, 'z', 16, { metalness: 0.8, roughness: 0.2 });
    g.add(tire, rim, hub);
    // 3 écrous
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2;
      const nut = cyl(0.012, 0.14, COLORS.chrome, 'z', 6);
      nut.position.set(Math.cos(a) * 0.09, Math.sin(a) * 0.09, 0);
      g.add(nut);
    }
    g.position.set(x, WHEEL_R, z);
    return g;
  }
  part('roues', [0, 0, 0.5], [wheel(AXLE_F, TRACK_F)]);
  part('roues', [0, 0, -0.5], [wheel(AXLE_F, -TRACK_F)]);
  part('roues', [0, 0, 0.5], [wheel(AXLE_R_RIGHT, TRACK_R)]);
  part('roues', [0, 0, -0.5], [wheel(AXLE_R_LEFT, -TRACK_R)]);
  const spare = wheel(-1.45, 0);
  spare.rotation.x = Math.PI / 2;
  spare.position.y = 0.20;
  spare.scale.setScalar(0.95);
  part('roue-secours', [-0.6, -0.2, 0], [spare]);

  // ================= INTÉRIEUR =================
  function seat(x, z, w) {
    const g = new THREE.Group();
    g.add(at(box(0.48, 0.10, w, COLORS.seat, { roughness: 0.9 }), x, 0.50, z));
    const back = at(box(0.09, 0.52, w, COLORS.seat, { roughness: 0.9 }), x - 0.25, 0.78, z);
    back.rotation.z = 0.18;
    g.add(back);
    g.add(at(box(0.30, 0.18, w * 0.8, COLORS.darkSteel), x, 0.38, z));
    return g;
  }
  part('sieges-av', [0, 0.7, 0], [seat(0.08, -0.33, 0.46)]);
  part('sieges-av', [0, 0.7, 0], [seat(0.08, 0.33, 0.46)]);
  part('banquette', [-0.2, 0.8, 0], [seat(-0.92, 0, 1.18)]);

  const dash = new THREE.Group();
  dash.add(at(box(0.16, 0.12, 1.38, COLORS.dash, { roughness: 0.8 }), 0.70, 0.86, 0));
  dash.add(at(box(0.04, 0.10, 0.36, COLORS.black), 0.61, 0.90, -0.35)); // bloc compteur
  dash.add(at(box(0.01, 0.06, 0.12, 0xdcd6c6, { emissive: 0x332a10 }), 0.595, 0.905, -0.35));
  part('planche-bord', [-0.45, 0.35, 0], [dash]);

  const steering = new THREE.Group();
  const colA = [0.80, 0.76, -0.35], colB = [0.47, 0.97, -0.35];
  steering.add(rod(colA, colB, 0.022, COLORS.black));
  const wheelRing = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.016, 10, 32), mat(COLORS.black, { roughness: 0.7 }));
  wheelRing.position.set(0.455, 0.98, -0.35);
  wheelRing.rotation.y = Math.PI / 2;
  wheelRing.rotation.x = -0.58;
  steering.add(wheelRing);
  const spoke = rod([0.455, 0.98, -0.53], [0.455, 0.98, -0.17], 0.012, COLORS.black);
  spoke.rotation.x += 0;
  steering.add(spoke);
  part('volant', [-0.45, 0.45, 0], [steering]);

  // Levier « trombone » + tige au-dessus du moteur
  const gear = new THREE.Group();
  gear.add(rod([0.70, 0.86, 0.02], [0.50, 0.86, 0.02], 0.010, COLORS.chrome));
  gear.add(at(new THREE.Mesh(new THREE.SphereGeometry(0.028, 14, 10), mat(COLORS.black)), 0.49, 0.86, 0.02));
  gear.add(rod([0.70, 0.86, 0.02], [1.42, 0.68, 0.05], 0.009, COLORS.steel));
  part('levier-vitesses', [0, 0.45, 0], [gear]);

  const pedals = new THREE.Group();
  [-0.47, -0.37, -0.25].forEach((z, i) => {
    pedals.add(rod([0.74, 0.78, z], [0.62, 0.42, z], 0.008, COLORS.darkSteel));
    pedals.add(at(box(0.02, 0.07, i === 2 ? 0.05 : 0.07, COLORS.rubber), 0.62, 0.42, z));
  });
  part('pedalier', [-0.3, 0.2, -0.3], [pedals]);

  const handbrake = new THREE.Group();
  handbrake.add(rod([0.74, 0.74, -0.12], [0.58, 0.74, -0.12], 0.008, COLORS.chrome));
  handbrake.add(at(box(0.02, 0.03, 0.09, COLORS.black), 0.575, 0.74, -0.12));
  handbrake.add(rod([0.74, 0.74, -0.12], [0.70, 0.30, -0.12], 0.005, COLORS.darkSteel));
  handbrake.add(rod([0.70, 0.30, -0.12], [-0.95, 0.27, 0], 0.005, COLORS.darkSteel));
  handbrake.add(rod([-0.95, 0.27, -0.45], [-0.95, 0.27, 0.45], 0.005, COLORS.darkSteel));
  part('frein-main', [0, -0.25, 0], [handbrake]);

  // ================= MOTEUR (longitudinal, derrière l'essieu, boîte devant) =================
  const EX = 0.92; // centre du bloc
  const block = new THREE.Group();
  block.add(at(box(0.42, 0.30, 0.28, COLORS.block), EX, 0.48, 0));
  block.add(at(box(0.40, 0.08, 0.06, COLORS.block), EX, 0.42, -0.16)); // bossage arbre à cames
  // Volant moteur + carter d'embrayage
  const bell = cyl(0.17, 0.10, COLORS.alu, 'x', 24, { metalness: 0.35 });
  bell.position.set(1.18, 0.44, 0);
  block.add(bell);
  part('bloc', [0, 0.2, 0], [block]);

  const headG = at(box(0.42, 0.10, 0.26, COLORS.head, { metalness: 0.35, roughness: 0.4 }), EX, 0.68, 0);
  part('culasse', [0, 0.55, 0], [headG]);

  const rocker = at(box(0.40, 0.07, 0.20, COLORS.rocker, { roughness: 0.35 }), EX, 0.765, 0.01);
  const oilCap = at(cyl(0.025, 0.03, COLORS.black, 'y'), EX - 0.10, 0.81, 0.02);
  part('cache-culbuteurs', [0, 0.85, 0], [rocker, oilCap]);

  const sump = at(box(0.40, 0.10, 0.24, COLORS.darkSteel), EX, 0.28, 0);
  const drainPlug = at(cyl(0.014, 0.02, COLORS.chrome, 'y', 8), EX - 0.05, 0.225, 0);
  part('carter-huile', [0, -0.45, 0], [sump, drainPlug]);

  const oilFilter = at(cyl(0.045, 0.10, COLORS.blue, 'z', 18, { roughness: 0.4 }), EX - 0.06, 0.46, -0.20);
  part('filtre-huile', [0, -0.05, -0.45], [oilFilter]);

  const dip = new THREE.Group();
  dip.add(rod([EX + 0.08, 0.40, -0.15], [EX + 0.10, 0.80, -0.19], 0.006, COLORS.yellow));
  dip.add(at(new THREE.Mesh(new THREE.TorusGeometry(0.018, 0.005, 6, 14), mat(COLORS.yellow)), EX + 0.10, 0.82, -0.19));
  part('jauge', [0, 0.45, -0.1], [dip]);

  const chainCover = at(box(0.03, 0.34, 0.24, COLORS.darkSteel), EX - 0.225, 0.52, 0);
  part('distribution', [-0.35, 0.1, 0], [chainCover]);

  const plugs = new THREE.Group();
  for (let i = 0; i < 4; i++) {
    const x = EX + 0.15 - i * 0.10;
    plugs.add(at(cyl(0.010, 0.07, 0xe8e3d6, 'z', 8), x, 0.69, 0.15));
    plugs.add(at(cyl(0.012, 0.03, COLORS.red, 'z', 8), x, 0.69, 0.195));
  }
  part('bougies', [0, 0.25, 0.4], [plugs]);

  const dist = new THREE.Group();
  dist.add(at(cyl(0.035, 0.10, COLORS.black, 'y', 14), EX - 0.18, 0.80, 0.11));
  dist.add(at(cyl(0.045, 0.03, COLORS.red, 'y', 14), EX - 0.18, 0.86, 0.11));
  part('allumeur', [0, 0.5, 0.25], [dist]);

  const coil = at(cyl(0.03, 0.12, COLORS.black, 'y', 14), 0.86, 0.72, 0.42);
  part('bobine', [0, 0.3, 0.3], [coil]);

  const manifold = new THREE.Group();
  manifold.add(at(box(0.36, 0.05, 0.05, COLORS.darkSteel, { metalness: 0.5 }), EX, 0.62, -0.16));
  const silencer = at(box(0.40, 0.11, 0.20, COLORS.darkSteel, { metalness: 0.5 }), -1.35, 0.24, 0.20);
  manifold.add(silencer);
  manifold.add(rod([EX, 0.60, -0.18], [0.70, 0.27, -0.18], 0.022, COLORS.darkSteel));
  manifold.add(rod([0.70, 0.27, -0.18], [-0.40, 0.245, -0.05], 0.022, COLORS.darkSteel));
  manifold.add(rod([-0.40, 0.245, -0.05], [-1.15, 0.24, 0.15], 0.022, COLORS.darkSteel));
  manifold.add(rod([-1.55, 0.24, 0.20], [-1.95, 0.24, 0.30], 0.02, COLORS.darkSteel));
  part('echappement', [0, -0.35, 0], [manifold]);

  const carb = at(box(0.08, 0.09, 0.08, COLORS.alu, { metalness: 0.5, roughness: 0.35 }), EX, 0.70, -0.23);
  part('carburateur', [0, 0.35, -0.35], [carb]);

  const airFilter = new THREE.Group();
  airFilter.add(at(cyl(0.13, 0.07, COLORS.black, 'y', 24), EX, 0.80, -0.20));
  airFilter.add(rod([EX + 0.10, 0.80, -0.20], [EX + 0.32, 0.80, -0.30], 0.035, COLORS.black));
  part('filtre-air', [0, 0.7, -0.15], [airFilter]);

  const fuelPump = at(cyl(0.035, 0.05, COLORS.alu, 'z', 14), EX - 0.10, 0.46, -0.22);
  part('pompe-essence', [0, 0, -0.4], [fuelPump]);

  // Refroidissement
  const radiator = new THREE.Group();
  radiator.add(at(box(0.05, 0.34, 0.48, COLORS.darkSteel), 1.70, 0.58, 0.08));
  for (let i = 0; i < 8; i++) radiator.add(at(box(0.052, 0.012, 0.46, COLORS.copper), 1.70, 0.44 + i * 0.04, 0.08));
  part('radiateur', [0.5, 0.15, 0], [radiator]);

  const fan = new THREE.Group();
  fan.add(at(cyl(0.15, 0.03, COLORS.black, 'x', 24), 1.64, 0.58, 0.08));
  fan.add(at(cyl(0.05, 0.08, COLORS.darkSteel, 'x', 14), 1.60, 0.58, 0.08));
  part('motoventilateur', [0.3, 0.4, 0], [fan]);

  const expTank = at(cyl(0.06, 0.16, 0xf2f2ea, 'y', 16, { transparent: true, opacity: 0.85, roughness: 0.3 }), 1.05, 0.80, 0.55);
  part('vase-expansion', [0, 0.45, 0.25], [expTank]);

  const waterPump = new THREE.Group();
  waterPump.add(at(box(0.08, 0.10, 0.12, COLORS.alu, { metalness: 0.4 }), EX + 0.23, 0.68, 0.0));
  waterPump.add(at(cyl(0.06, 0.015, COLORS.darkSteel, 'x', 20), EX + 0.28, 0.66, 0.0));
  part('pompe-eau', [0.25, 0.4, 0], [waterPump]);

  const hoses = new THREE.Group();
  hoses.add(rod([EX + 0.28, 0.70, -0.04], [1.68, 0.70, -0.10], 0.022, COLORS.black));
  hoses.add(rod([EX + 0.10, 0.40, 0.12], [1.68, 0.45, 0.25], 0.022, COLORS.black));
  hoses.add(rod([EX - 0.20, 0.70, -0.08], [0.84, 0.70, -0.40], 0.015, COLORS.black)); // chauffage
  part('durites', [0.15, 0.3, 0], [hoses]);

  // Transmission
  const gearbox = new THREE.Group();
  gearbox.add(at(box(0.30, 0.22, 0.26, COLORS.alu, { metalness: 0.35 }), 1.36, 0.42, 0));
  gearbox.add(at(cyl(0.12, 0.30, COLORS.alu, 'z', 20, { metalness: 0.35 }), AXLE_F, 0.34, 0));
  part('boite', [0.75, 0.15, 0], [gearbox]);

  const clutch = new THREE.Group();
  clutch.add(at(cyl(0.09, 0.012, COLORS.brake, 'x', 24), 1.15, 0.44, 0));
  clutch.add(at(cyl(0.10, 0.03, COLORS.steel, 'x', 24, { metalness: 0.5 }), 1.19, 0.44, 0));
  part('embrayage', [0.25, 0.6, 0.5], [clutch]);

  const shafts = new THREE.Group();
  for (const s of [1, -1]) {
    shafts.add(rod([AXLE_F, 0.32, s * 0.15], [AXLE_F, WHEEL_R, s * 0.56], 0.018, COLORS.steel));
    shafts.add(at(cyl(0.035, 0.08, COLORS.rubber, 'z', 12), AXLE_F, 0.315, s * 0.20));
    shafts.add(at(cyl(0.035, 0.08, COLORS.rubber, 'z', 12), AXLE_F, 0.29, s * 0.51));
  }
  part('transmissions', [0, -0.35, 0], [shafts]);

  // Trains
  const frontArms = new THREE.Group();
  for (const s of [1, -1]) {
    frontArms.add(rod([AXLE_F - 0.12, 0.20, s * 0.30], [AXLE_F, 0.20, s * 0.55], 0.015, COLORS.darkSteel));
    frontArms.add(rod([AXLE_F + 0.12, 0.20, s * 0.30], [AXLE_F, 0.20, s * 0.55], 0.015, COLORS.darkSteel));
    frontArms.add(rod([AXLE_F - 0.10, 0.48, s * 0.36], [AXLE_F, 0.44, s * 0.53], 0.013, COLORS.darkSteel));
    frontArms.add(rod([AXLE_F + 0.10, 0.48, s * 0.36], [AXLE_F, 0.44, s * 0.53], 0.013, COLORS.darkSteel));
  }
  part('triangles-av', [0, -0.25, 0], [frontArms]);

  const knuckles = new THREE.Group();
  for (const s of [1, -1]) knuckles.add(rod([AXLE_F, 0.20, s * 0.55], [AXLE_F, 0.44, s * 0.53], 0.025, COLORS.steel));
  part('porte-fusee', [0, -0.15, 0], [knuckles]);

  const tbarsF = new THREE.Group();
  for (const s of [1, -1]) tbarsF.add(rod([AXLE_F - 0.12, 0.21, s * 0.30], [0.20, 0.25, s * 0.32], 0.009, COLORS.green));
  part('barres-torsion-av', [0, -0.3, 0], [tbarsF]);

  const shocksF = new THREE.Group();
  for (const s of [1, -1]) shocksF.add(rod([AXLE_F + 0.05, 0.22, s * 0.47], [AXLE_F + 0.18, 0.62, s * 0.45], 0.02, COLORS.yellow));
  part('amortisseurs-av', [0, 0.25, 0], [shocksF]);

  const rack = new THREE.Group();
  rack.add(at(cyl(0.025, 0.70, COLORS.darkSteel, 'z', 12), 1.05, 0.52, 0));
  for (const s of [1, -1]) rack.add(rod([1.05, 0.52, s * 0.35], [AXLE_F - 0.10, 0.45, s * 0.53], 0.010, COLORS.steel));
  rack.add(rod([0.80, 0.76, -0.35], [1.05, 0.54, -0.25], 0.016, COLORS.darkSteel));
  part('direction', [0, 0.25, 0], [rack]);

  const rearArms = new THREE.Group();
  rearArms.add(rod([-0.70, 0.28, 0.45], [AXLE_R_RIGHT, WHEEL_R, 0.52], 0.03, COLORS.darkSteel));
  rearArms.add(rod([-0.65, 0.28, -0.45], [AXLE_R_LEFT, WHEEL_R, -0.52], 0.03, COLORS.darkSteel));
  part('bras-ar', [0, -0.25, 0], [rearArms]);

  const tbarsR = new THREE.Group();
  tbarsR.add(rod([-0.70, 0.26, -0.60], [-0.70, 0.26, 0.48], 0.01, COLORS.green));
  tbarsR.add(rod([-0.65, 0.26, -0.48], [-0.65, 0.26, 0.60], 0.01, COLORS.green));
  part('barres-torsion-ar', [0, -0.35, 0], [tbarsR]);

  const shocksR = new THREE.Group();
  shocksR.add(rod([AXLE_R_RIGHT + 0.02, 0.24, 0.46], [-0.55, 0.36, 0.46], 0.018, COLORS.yellow));
  shocksR.add(rod([AXLE_R_LEFT + 0.02, 0.24, -0.46], [-0.50, 0.36, -0.46], 0.018, COLORS.yellow));
  part('amortisseurs-ar', [0, 0.2, 0], [shocksR]);

  // Freins
  for (const s of [1, -1]) {
    const disc = at(cyl(0.114, 0.012, COLORS.steel, 'z', 28, { metalness: 0.6, roughness: 0.35 }), AXLE_F, WHEEL_R, s * 0.545);
    part('disques-av', [0, 0, s * 0.35], [disc]);
    const caliper = at(box(0.07, 0.06, 0.05, COLORS.red), AXLE_F - 0.08, WHEEL_R + 0.07, s * 0.545);
    part('etriers-av', [0, 0.15, s * 0.55], [caliper]);
  }
  const drumR = at(cyl(0.10, 0.06, COLORS.darkSteel, 'z', 24, { metalness: 0.4 }), AXLE_R_RIGHT, WHEEL_R, 0.54);
  const drumL = at(cyl(0.10, 0.06, COLORS.darkSteel, 'z', 24, { metalness: 0.4 }), AXLE_R_LEFT, WHEEL_R, -0.54);
  part('tambours-ar', [0, 0, 0.4], [drumR]);
  part('tambours-ar', [0, 0, -0.4], [drumL]);

  const master = new THREE.Group();
  master.add(at(cyl(0.025, 0.14, COLORS.alu, 'x', 14), 0.90, 0.80, -0.42));
  master.add(at(box(0.08, 0.07, 0.07, 0xeeeeee, { transparent: true, opacity: 0.85 }), 0.92, 0.86, -0.42));
  part('maitre-cylindre', [0.2, 0.45, -0.2], [master]);

  const limiter = at(box(0.06, 0.05, 0.05, COLORS.alu), -0.80, 0.30, 0.18);
  part('limiteur', [0, -0.3, 0.2], [limiter]);

  // Électricité
  const battery = new THREE.Group();
  battery.add(at(box(0.18, 0.17, 0.13, COLORS.black), 1.50, 0.70, 0.48));
  battery.add(at(cyl(0.012, 0.02, COLORS.red, 'y', 8), 1.45, 0.795, 0.45));
  battery.add(at(cyl(0.012, 0.02, COLORS.darkSteel, 'y', 8), 1.55, 0.795, 0.45));
  part('batterie', [0.2, 0.55, 0.3], [battery]);

  const alternator = new THREE.Group();
  alternator.add(at(cyl(0.065, 0.13, COLORS.alu, 'x', 18, { metalness: 0.45 }), EX + 0.12, 0.56, 0.22));
  alternator.add(at(cyl(0.035, 0.012, COLORS.darkSteel, 'x', 14), EX + 0.20, 0.56, 0.22));
  const belt = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.006, 6, 30), mat(COLORS.black));
  belt.position.set(EX + 0.24, 0.60, 0.11);
  belt.rotation.y = Math.PI / 2;
  belt.scale.set(1, 1, 2.2);
  alternator.add(belt);
  part('alternateur', [0.2, 0.1, 0.45], [alternator]);

  const starter = at(cyl(0.045, 0.16, COLORS.darkSteel, 'x', 16), 1.10, 0.36, 0.20);
  part('demarreur', [0, -0.2, 0.45], [starter]);

  const fuses = at(box(0.03, 0.08, 0.14, COLORS.black), 0.85, 0.80, -0.20);
  part('fusibles', [0.25, 0.3, 0], [fuses]);

  const lights = new THREE.Group();
  for (const s of [1, -1]) {
    lights.add(at(cyl(0.085, 0.05, COLORS.chrome, 'x', 24, { metalness: 0.8, roughness: 0.2 }), 1.82, 0.64, s * 0.52));
    lights.add(at(cyl(0.075, 0.02, 0xfff3c2, 'x', 24, { emissive: 0x4a3f10, roughness: 0.2 }), 1.85, 0.64, s * 0.52));
  }
  part('phares', [0.4, 0.15, 0], [lights]);

  const tails = new THREE.Group();
  for (const s of [1, -1]) {
    tails.add(at(box(0.03, 0.18, 0.07, COLORS.red, { emissive: 0x330000 }), -1.84, 0.70, s * 0.70));
    tails.add(at(box(0.03, 0.05, 0.07, COLORS.orange, { emissive: 0x331800 }), -1.84, 0.58, s * 0.70));
    tails.add(at(box(0.05, 0.04, 0.03, COLORS.orange, { emissive: 0x331800 }), 1.80, 0.50, s * 0.66));
  }
  part('feux', [0, 0.15, 0], [tails]);

  const wipers = new THREE.Group();
  wipers.add(rod([0.86, 0.97, -0.50], [0.62, 1.20, -0.10], 0.007, COLORS.black));
  wipers.add(rod([0.86, 0.97, 0.05], [0.62, 1.20, 0.45], 0.007, COLORS.black));
  wipers.add(at(box(0.08, 0.06, 0.10, COLORS.darkSteel), 0.76, 0.90, 0.25));
  part('essuie-glace', [0.2, 0.4, 0], [wipers]);

  const washer = at(box(0.10, 0.14, 0.10, 0xe9edf0, { transparent: true, opacity: 0.85 }), 1.25, 0.76, 0.60);
  part('lave-glace', [0, 0.4, 0.3], [washer]);

  const tank = at(box(0.42, 0.14, 0.55, COLORS.darkSteel), -1.05, 0.20, -0.25);
  part('reservoir', [0, -0.35, -0.2], [tank]);

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

  return { root, parts };
}

// Couleur de carrosserie modifiable à chaud.
export function setBodyColor(parts, hex) {
  for (const id of ['caisse', 'capot', 'portes', 'hayon']) {
    for (const g of parts.get(id) || []) {
      g.traverse((o) => {
        if (o.isMesh && o.material.metalness < 0.5 && o.material.color.getHex() !== COLORS.chrome) o.material.color.set(hex);
      });
    }
  }
}
