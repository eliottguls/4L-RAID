import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { buildCar, setBodyColor, loadModels } from './car.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { VEHICLE, SYSTEMS, PARTS, PROCEDURES, MAINTENANCE, FASTENERS } from './data.js';
import { restoreRta, loadRtaFile, forgetRta, hasRta, showPage, initRtaDialog } from './rta.js';

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const systemOf = (id) => SYSTEMS.find((s) => s.id === PARTS[id]?.system);
const procById = (id) => PROCEDURES.find((p) => p.id === id);
const BODY_PARTS = ['caisse', 'capot', 'portes', 'hayon', 'vitrage', 'pare-chocs', 'calandre'];
const DIFFICULTY = ['', 'Facile', 'Moyen', 'Atelier'];
const INNER_PARTS = new Set(['chemises-pistons', 'bielles', 'vilebrequin', 'arbre-cames', 'culbuterie', 'soupapes', 'joint-culasse', 'chaine-distribution', 'pompe-huile', 'volant-moteur', 'embrayage']);

// Procédures liées à chaque pièce
const procsForPart = {};
for (const p of PROCEDURES) {
  const ids = new Set([...p.parts, ...p.steps.flatMap((s) => [...(s.remove || []), ...(s.focus || [])])]);
  p.involved = ids;
  for (const id of p.parts) (procsForPart[id] ||= []).push(p.id);
}

// ===================== Scène 3D =====================
const viewer = $('#viewer');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewer.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1c1814);
scene.fog = new THREE.Fog(0x1c1814, 9, 22);

const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 60);
const HOME = { pos: new THREE.Vector3(4.6, 2.5, 4.4), target: new THREE.Vector3(0, 0.6, 0) };
camera.position.copy(HOME.pos);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(HOME.target);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 0.4;
controls.maxDistance = 14;
controls.maxPolarAngle = Math.PI * 0.495;

renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xfff4e0, 0x2a2018, 0.45));
const sun = new THREE.DirectionalLight(0xfff1dc, 1.8);
sun.position.set(4, 7, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 1, far: 20 });
scene.add(sun);
const fill = new THREE.DirectionalLight(0xc8d8ff, 0.5);
fill.position.set(-5, 3, -4);
scene.add(fill);

const ground = new THREE.Mesh(new THREE.CircleGeometry(9, 64), new THREE.MeshStandardMaterial({ color: 0x2a241e, roughness: 0.95 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);
const grid = new THREE.PolarGridHelper(8, 16, 12, 64, 0x3d342b, 0x332b24);
grid.position.y = 0.002;
scene.add(grid);

const model = buildCar();
const { root: car, parts, fasteners } = model;
scene.add(car);
$('#loading').remove();

let allGroups = [];
let allMeshes = [];
function reindex() {
  allGroups = [...parts.values()].flat();
  allMeshes = [];
  for (const g of allGroups) g.traverse((o) => { if (o.isMesh) { o.userData.group = g; allMeshes.push(o); } });
}
reindex();
// Modèles détaillés (Blender) : chargés après le premier affichage, ils remplacent les pièces simplifiées.
loadModels(model).then(() => {
  for (const sprites of seqSprites.values()) for (const { sp } of sprites) scene.remove(sp);
  seqSprites.clear();
  reindex();
  if (state.proc || state.selected) route(); else applyVisualState();
}).catch((e) => console.warn('Modèle détaillé non chargé :', e));

// Sur mobile, le panneau du bas cache une partie de la vue : on décale le centre
// de projection pour que la pièce reste visible au-dessus du panneau.
function resize() {
  const { clientWidth: w, clientHeight: h } = viewer;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  const sheet = window.matchMedia('(max-width: 820px)').matches && !detail.hidden ? detail.offsetHeight : 0;
  if (sheet > 0 && sheet < h) camera.setViewOffset(w, h + sheet, 0, sheet, w, h);
  else camera.clearViewOffset();
  camera.updateProjectionMatrix();
}
const detail = $('#detail');
const ro = new ResizeObserver(resize);
ro.observe(viewer);
ro.observe(detail);
resize();

// ===================== État =====================
const state = {
  xray: false,
  explode: 0,
  hidden: new Set(),
  selected: null,   // id de pièce
  proc: null,       // procédure active
  step: -1,         // -1 = vue d'ensemble
  hovered: null,
};

let previewFx = null; // jeu de vis montré depuis une fiche pièce
let pendingFx = null;
// Calcule les cibles (position, opacité, surbrillance) de chaque pièce.
function applyVisualState() {
  const proc = state.proc;
  const removed = new Set();
  const focus = new Set();
  const unscrewed = new Set();
  const boltFocus = new Set();
  let sequence = null;
  if (proc) {
    proc.steps.forEach((s, i) => {
      if (i > state.step) return;
      (s.remove || []).forEach((id) => removed.add(id));
      (s.refit || []).forEach((id) => removed.delete(id));
      (s.unscrew || []).forEach((id) => unscrewed.add(id));
      (s.screw || []).forEach((id) => unscrewed.delete(id));
    });
    const cur = proc.steps[state.step];
    if (cur) {
      [...(cur.focus || []), ...(cur.remove || []), ...(cur.refit || [])].forEach((id) => focus.add(id));
      [...(cur.unscrew || []), ...(cur.screw || []), ...(cur.bolts || [])].forEach((id) => boltFocus.add(id));
      sequence = cur.sequence || null;
    } else proc.parts.forEach((id) => focus.add(id));
  } else if (state.selected) {
    focus.add(state.selected);
    if (previewFx) { unscrewed.add(previewFx); boltFocus.add(previewFx); sequence = fasteners.get(previewFx)?.order ? previewFx : null; }
  }

  for (const g of allGroups) {
    const id = g.userData.partId;
    const sys = PARTS[id]?.system;
    g.visible = !state.hidden.has(sys);
    const off = g.userData.explode.clone().multiplyScalar(state.explode);
    if (removed.has(id)) off.add(g.userData.explode.clone().multiplyScalar(1.8)).add(new THREE.Vector3(0, 0.08, 0));
    g.userData.targetOffset = off;

    let opacity = 1;
    const isBody = BODY_PARTS.includes(id);
    if (proc) {
      if (focus.has(id)) opacity = 1;
      else if (proc.involved.has(id)) opacity = 0.75;
      else opacity = isBody ? 0.05 : 0.12;
    } else if (state.selected) {
      if (id === state.selected) opacity = 1;
      else if (isBody && !BODY_PARTS.includes(state.selected)) opacity = 0.06;
      // pièce interne (vilebrequin, pistons…) : les pièces autour s'effacent davantage pour la laisser voir
      else opacity = INNER_PARTS.has(state.selected) ? 0.1 : 0.3;
    } else if (state.xray && (isBody || sys === 'interieur')) {
      opacity = isBody ? 0.08 : 0.35;
    }
    const highlight = focus.has(id);
    g.traverse((o) => {
      if (!o.isMesh) return;
      const bolt = o.userData.fastener && boltFocus.has(o.userData.fastener);
      o.userData.targetOpacity = Math.min(bolt ? 1 : opacity, o.userData.baseOpacity);
      o.userData.highlight = bolt ? 'bolt' : highlight;
    });
  }
  for (const [id, list] of fasteners) for (const f of list) f.target = unscrewed.has(id) ? 1 : 0;
  state.sequence = sequence;
  if (sequence) sequenceSprites(sequence);
  state.boltFocus = boltFocus;
}

// Numéros d'ordre de serrage affichés au-dessus des vis.
const seqSprites = new Map();
function sequenceSprites(setId) {
  if (seqSprites.has(setId)) return seqSprites.get(setId);
  const list = fasteners.get(setId) || [];
  const order = list.order || list.map((_, i) => i + 1);
  const sprites = list.map((f, i) => {
    const c = document.createElement('canvas');
    c.width = c.height = 64;
    const g = c.getContext('2d');
    g.fillStyle = '#f28c28'; g.beginPath(); g.arc(32, 32, 28, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#1b1209'; g.font = 'bold 34px Barlow, Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(String(order[i]), 32, 34);
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false }));
    sp.scale.setScalar(0.035);
    sp.renderOrder = 10;
    sp.visible = false;
    scene.add(sp);
    return { sp, f };
  });
  seqSprites.set(setId, sprites);
  return sprites;
}

// ===================== Caméra =====================
let camTween = null;
function tweenCamera(pos, target, duration = 0.9) {
  if (reduceMotion) { camera.position.copy(pos); controls.target.copy(target); return; }
  camTween = { fromPos: camera.position.clone(), fromTarget: controls.target.clone(), pos, target, t: 0, duration };
}

// Appelé avant openDetail : on attend que le panneau (et le décalage de vue) soit en place.
function focusOn(ids) { queueMicrotask(() => focusNow(ids)); }

function focusNow(ids) {
  const box = new THREE.Box3();
  let any = false;
  for (const id of ids) {
    for (const g of parts.get(id) || []) {
      if (!g.visible) continue;
      const b = new THREE.Box3().setFromObject(g);
      const delta = g.userData.basePos.clone().add(g.userData.targetOffset || new THREE.Vector3()).sub(g.position);
      b.translate(delta);
      box.union(b);
      any = true;
    }
  }
  if (!any) return;
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3()).length();
  // En portrait (mobile), le champ horizontal est étroit, et le panneau du bas
  // réduit le champ vertical (setViewOffset) : on recule d'autant.
  const narrow = Math.max(1, 1 / Math.max(camera.aspect, 0.35)) ** 0.6;
  const sheet = camera.view?.enabled ? camera.view.fullHeight / camera.view.height : 1;
  const dist = THREE.MathUtils.clamp((size * 1.7 + 0.8) * narrow * sheet, 1.0, 10);
  const dir = camera.position.clone().sub(controls.target).normalize();
  if (dir.y < 0.15) dir.y = 0.35;
  dir.normalize();
  tweenCamera(center.clone().add(dir.multiplyScalar(dist)), center);
}

function resetView() {
  tweenCamera(HOME.pos.clone(), HOME.target.clone());
}

// ===================== Interaction 3D =====================
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const tooltip = $('#tooltip');

function pick(ev) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  raycaster.setFromCamera(pointer, camera);
  const candidates = allMeshes.filter((m) => m.userData.group.visible && m.material.opacity > 0.3);
  const hit = raycaster.intersectObjects(candidates, false)[0];
  hoveredFastener = hit?.object.userData.fastener || null;
  return hit ? hit.object.userData.group.userData.partId : null;
}
let hoveredFastener = null;

let down = null;
renderer.domElement.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY }; closeSidebarMobile(); });
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;
  const id = pick(e);
  const fx = hoveredFastener;
  if (id) {
    pendingFx = !state.proc && fx && FASTENERS[fx]?.part === id ? fx : null;
    if (location.hash === `#/piece/${id}`) showPart(id, false); else navigate(`#/piece/${id}`);
  }
  else if (state.selected && !state.proc) navigate('#/');
});
renderer.domElement.addEventListener('pointermove', (e) => {
  if (e.pointerType !== 'mouse') return;
  const id = pick(e);
  state.hovered = id;
  renderer.domElement.style.cursor = id ? 'pointer' : 'grab';
  if (id) {
    tooltip.hidden = false;
    const fx = hoveredFastener && FASTENERS[hoveredFastener];
    tooltip.textContent = fx ? `${fx.name} · ${PARTS[id]?.name || id}` : PARTS[id]?.name || id;
    const r = viewer.getBoundingClientRect();
    tooltip.style.transform = `translate(${e.clientX - r.left + 14}px, ${e.clientY - r.top + 12}px)`;
  } else tooltip.hidden = true;
});
renderer.domElement.addEventListener('pointerleave', () => { tooltip.hidden = true; state.hovered = null; });

// ===================== Boucle de rendu =====================
const ORANGE = new THREE.Color(0xf28c28);
const CYAN = new THREE.Color(0x2fd3ff);
const SPIN = new THREE.Quaternion();
const Y_AXIS = new THREE.Vector3(0, 1, 0);
const tmpV = new THREE.Vector3();
const clock = new THREE.Clock();
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  const k = reduceMotion ? 1 : 1 - Math.exp(-dt * 7);
  const pulse = 0.28 + 0.14 * Math.sin(clock.elapsedTime * 4);
  for (const g of allGroups) {
    const target = g.userData.basePos.clone().add(g.userData.targetOffset || new THREE.Vector3());
    g.position.lerp(target, k);
  }
  for (const m of allMeshes) {
    const mat = m.material;
    const t = m.userData.targetOpacity ?? m.userData.baseOpacity;
    mat.opacity += (t - mat.opacity) * k;
    const transparent = mat.opacity < 0.995 || m.userData.baseTransparent;
    if (mat.transparent !== transparent) { mat.transparent = transparent; mat.needsUpdate = true; }
    mat.depthWrite = !m.userData.glass && mat.opacity > 0.6;
    const hovered = m.userData.group.userData.partId === state.hovered;
    if (m.userData.highlight === 'bolt') mat.emissive.copy(CYAN).multiplyScalar(pulse * 2);
    else if (m.userData.highlight) mat.emissive.copy(ORANGE).multiplyScalar(pulse);
    else if (hovered) mat.emissive.copy(ORANGE).multiplyScalar(0.18);
    else mat.emissive.setHex(m.userData.baseEmissive);
  }
  const kb = reduceMotion ? 1 : 1 - Math.exp(-dt * 3);
  for (const list of fasteners.values()) for (const f of list) {
    const p = (f.p ?? 0) + ((f.target ?? 0) - (f.p ?? 0)) * kb;
    if (Math.abs(p - (f.p ?? 0)) < 1e-5 && f.p !== undefined) continue;
    f.p = p;
    f.obj.position.copy(f.base).addScaledVector(f.dir, f.travel * p);
    f.obj.quaternion.copy(f.q0);
    if (f.spin) f.obj.quaternion.multiply(SPIN.setFromAxisAngle(Y_AXIS, p * Math.PI * 6));
  }
  for (const [id, sprites] of seqSprites) for (const { sp, f } of sprites) {
    sp.visible = state.sequence === id && f.obj.parent.visible;
    if (sp.visible) sp.position.copy(f.obj.getWorldPosition(tmpV)).add(Y_AXIS.clone().multiplyScalar(0.035));
  }
  if (camTween) {
    camTween.t = Math.min(1, camTween.t + dt / camTween.duration);
    const e = 1 - Math.pow(1 - camTween.t, 3);
    camera.position.lerpVectors(camTween.fromPos, camTween.pos, e);
    controls.target.lerpVectors(camTween.fromTarget, camTween.target, e);
    if (camTween.t >= 1) camTween = null;
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
applyVisualState();
frame();

// ===================== Recherche =====================
const STOP = new Set('comment faire je j on le la les de des du un une a au aux et ou pour sur mon ma mes ce cet cette quoi quel quelle quels est en d l qu que il faut peut dois veux how to the sa son ses avec par se tu vous nous ca cela plat'.split(' '));
const SYN = {
  delco: 'allumeur', platinees: 'rupteur', platine: 'rupteur', vis: 'rupteur', cardans: 'transmission', cardan: 'transmission',
  carbu: 'carburateur', pneu: 'roue', pneus: 'roue', crevaison: 'roue', ampoule: 'lampe', ampoules: 'lampe', phare: 'projecteur',
  eau: 'refroidissement', surchauffe: 'refroidissement', chauffe: 'refroidissement', liquide: 'liquide', frein: 'freins',
  plaquette: 'plaquettes', disque: 'plaquettes', machoires: 'tambour', segments: 'tambour', amorto: 'amortisseur', amortos: 'amortisseur',
  boite: 'boite', vitesses: 'boite', patine: 'embrayage', soupapes: 'culbuteurs', soupape: 'culbuteurs', cale: 'ralenti',
  moteur: 'moteur', ventilo: 'motoventilateur', ventilateur: 'motoventilateur', clignotants: 'clignotant', fusibles: 'fusible',
};
const norm = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’'«»"()/,.;:!?-]/g, ' ');
const words = (s) => norm(s).split(/\s+/).filter(Boolean);
const stem = (w) => (w.length > 4 ? w.replace(/(es|s|x)$/, '') : w);

function tokenize(q) {
  const out = [];
  for (const w of words(q)) {
    if (STOP.has(w) || w.length < 2) continue;
    out.push(stem(w));
    if (SYN[w]) out.push(stem(SYN[w]));
  }
  return [...new Set(out)];
}

function fieldScore(tokens, text, weight) {
  const ws = words(text).map(stem);
  let s = 0;
  for (const t of tokens) {
    if (ws.some((w) => w === t)) s += weight;
    else if (t.length >= 3 && ws.some((w) => w.startsWith(t) || (w.length >= 4 && t.startsWith(w)))) s += weight * 0.6;
  }
  return s;
}

const LOW = new Set(['moteur', 'voiture', '4l', 'chang', 'remplac', 'change', 'remplace', 'remplacer', 'changer', 'regler', 'deposer', 'depose', 'monter']);
function search(q) {
  const tokens = tokenize(q);
  const strong = tokens.filter((t) => !LOW.has(t));
  const toks = strong.length ? strong : tokens;
  if (!toks.length) return { procs: [], parts: [] };
  const procs = PROCEDURES.map((p) => ({
    p,
    score: fieldScore(toks, p.title, 4) + fieldScore(toks, p.keywords.join(' '), 3)
      + fieldScore(toks, p.parts.map((id) => PARTS[id]?.name || '').join(' '), 2)
      + fieldScore(toks, p.steps.map((s) => s.t).join(' '), 0.3),
  })).filter((r) => r.score >= 1.5).sort((a, b) => b.score - a.score);
  const partsRes = Object.entries(PARTS).map(([id, p]) => ({
    id, p, score: fieldScore(toks, p.name, 4) + fieldScore(toks, p.desc, 0.6),
  })).filter((r) => r.score >= 2).sort((a, b) => b.score - a.score);
  return { procs: procs.slice(0, 8), parts: partsRes.slice(0, 6) };
}

// ===================== Panneaux =====================
const sidebar = $('#sidebar');

function procItem(p) {
  const sys = SYSTEMS.find((s) => s.id === p.system);
  return `<li><a class="proc-item" href="#/proc/${p.id}">
    <span class="dot" style="--c:${sys.color}"></span>
    <span class="proc-title">${esc(p.title)}</span>
    <span class="proc-meta">${DIFFICULTY[p.difficulty]} · ${esc(p.duration)}</span>
  </a></li>`;
}

function partItem(id) {
  const p = PARTS[id];
  const sys = systemOf(id);
  return `<li><a class="part-item" href="#/piece/${id}"><span class="dot" style="--c:${sys.color}"></span>${esc(p.name)}</a></li>`;
}

const SUGGESTIONS = ['vidange', 'plaquettes', 'joint de culasse', 'purge freins', 'courroie', 'bougies', 'embrayage', 'roue'];

function renderSearch(q = '') {
  const panel = $('#panel-search');
  if (!q.trim()) {
    panel.innerHTML = `
      <div class="intro">
        <h2>Que veux-tu faire sur la 4L ?</h2>
        <p>Tape une question comme « comment changer la pompe à eau », ou clique sur une pièce du modèle.</p>
        <div class="chips">${SUGGESTIONS.map((s) => `<button class="chip" data-q="${esc(s)}">${esc(s)}</button>`).join('')}</div>
      </div>
      <div class="vehicle-card">
        <h3>${esc(VEHICLE.name)} · ${VEHICLE.year}</h3>
        <ul>${VEHICLE.notes.map((n) => `<li>${esc(n)}</li>`).join('')}</ul>
      </div>
      ${SYSTEMS.filter((s) => PROCEDURES.some((p) => p.system === s.id)).map((s) => `
        <h3 class="group-title">${esc(s.name)}</h3>
        <ul class="list">${PROCEDURES.filter((p) => p.system === s.id).map(procItem).join('')}</ul>`).join('')}`;
    return;
  }
  const { procs, parts: ps } = search(q);
  if (!procs.length && !ps.length) {
    panel.innerHTML = `<div class="empty">
      <h3>Rien trouvé pour « ${esc(q)} »</h3>
      <p>Essaie avec le nom d’une pièce (alternateur, étrier, carburateur…) ou parcours l’onglet Pièces.</p>
      <button class="btn" data-tab-go="parts">Parcourir les pièces</button>
    </div>`;
    return;
  }
  panel.innerHTML = `
    ${procs.length ? `<h3 class="group-title">Interventions</h3><ul class="list">${procs.map((r) => procItem(r.p)).join('')}</ul>` : ''}
    ${ps.length ? `<h3 class="group-title">Pièces</h3><ul class="list">${ps.map((r) => partItem(r.id)).join('')}</ul>` : ''}`;
}

function renderParts() {
  $('#panel-parts').innerHTML = SYSTEMS.map((s) => {
    const ids = Object.keys(PARTS).filter((id) => PARTS[id].system === s.id);
    return `<h3 class="group-title"><span class="dot" style="--c:${s.color}"></span>${esc(s.name)}</h3>
      <ul class="list">${ids.map(partItem).join('')}</ul>`;
  }).join('');
}

function renderMaintenance() {
  $('#panel-maintenance').innerHTML = `
    <p class="muted">Intervalles de la RTA. En raid, rapproche-les : la poussière et la chaleur usent vite.</p>
    ${MAINTENANCE.map((m) => `
      <section class="maint">
        <h3>${esc(m.when)}</h3>
        <ul>${m.items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>
        <div class="chips">${m.procs.map((id) => `<a class="chip" href="#/proc/${id}">${esc(procById(id).title)}</a>`).join('')}</div>
      </section>`).join('')}
    <section class="maint">
      <h3>Capacités</h3>
      <table class="specs">
        <tr><th>Huile moteur</th><td>3 L + 0,25 L filtre · 15W40</td></tr>
        <tr><th>Boîte de vitesses</th><td>1,8 L · 80W GL4</td></tr>
        <tr><th>Refroidissement</th><td>5,9 L</td></tr>
        <tr><th>Freins</th><td>0,4 L · DOT 4 (SAE J 1703)</td></tr>
        <tr><th>Carburant</th><td>34 L</td></tr>
        <tr><th>Pneus AV / AR</th><td>1,4 / 1,5 bar (chargé : 1,6 / 1,8)</td></tr>
      </table>
    </section>`;
}

let rtaInfo = { loaded: false };
function renderRtaPanel() {
  const p = $('#panel-rta');
  if (rtaInfo.restoring) { p.innerHTML = '<p class="status" role="status">Ouverture de ta revue technique…</p>'; return; }
  p.innerHTML = rtaInfo.loaded
    ? `<div class="rta-ok">
        <h3>Revue technique chargée</h3>
        <p>${esc(rtaInfo.name)} · ${rtaInfo.pages} pages${rtaInfo.persisted ? ' · gardée sur cet appareil' : ''}.</p>
        <p class="muted">Les boutons « RTA p. … » des fiches ouvrent directement la bonne page, avec les schémas d’origine.</p>
        <div class="row"><button class="btn" id="rta-open-1">Ouvrir la RTA</button><button class="btn ghost" id="rta-forget">Retirer de cet appareil</button></div>
      </div>`
    : `<div class="rta-load">
        <h3>Ajoute ta revue technique</h3>
        <p>Choisis ton PDF « Revue Technique 4L GTL » pour voir les pages et schémas d’origine à côté de chaque intervention.</p>
        <p class="muted">Le fichier reste dans ton navigateur : il n’est jamais envoyé ni publié sur le site.</p>
        <label class="btn file">Choisir le PDF<input type="file" accept="application/pdf" id="rta-file" hidden></label>
        <p class="status" id="rta-status" role="status"></p>
      </div>`;
  $('#rta-file')?.addEventListener('change', async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    $('#rta-status').textContent = 'Lecture du PDF…';
    try {
      rtaInfo = await loadRtaFile(f);
      renderRtaPanel();
      if (state.proc) showProcedure(state.proc.id, state.step, false); else if (state.selected) showPart(state.selected, false);
    } catch {
      $('#rta-status').textContent = 'Ce fichier n’a pas pu être lu. Vérifie que c’est bien un PDF et réessaie.';
    }
  });
  $('#rta-open-1')?.addEventListener('click', () => showPage(1));
  $('#rta-forget')?.addEventListener('click', async () => { await forgetRta(); rtaInfo = { loaded: false }; renderRtaPanel(); });
}

const BOLT_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3h8l4 4-4 4H8L4 7z"/><path d="M10 11v10M14 11v10M10 15h4M10 18h4"/></svg>';
function fastenerLabel(id) {
  const f = FASTENERS[id];
  if (!f) return '';
  const n = f.count ? `${f.count} × ` : '';
  return `${n}${f.name}${f.torque ? ` · ${f.torque}` : ''}`;
}
function fastenerChips(step) {
  const ids = [...(step.unscrew || []), ...(step.screw || []), ...(step.bolts || [])];
  if (!ids.length) return '';
  return `<span class="bolt-chips">${[...new Set(ids)].map((id) => {
    const verb = step.unscrew?.includes(id) ? 'Dévisser' : step.screw?.includes(id) ? 'Serrer' : 'Repérer';
    return `<span class="bolt-chip">${BOLT_ICON}<span><b>${verb}</b> ${esc(fastenerLabel(id))}</span></span>`;
  }).join('')}</span>`;
}
function partFasteners(partId) {
  const ids = Object.keys(FASTENERS).filter((id) => FASTENERS[id].part === partId);
  if (!ids.length) return '';
  return `<h3 class="group-title">Vis et fixations</h3><ul class="fx-list">${ids.map((id) => {
    const f = FASTENERS[id];
    return `<li><button class="fx-item${previewFx === id ? ' on' : ''}" data-fx="${id}">${BOLT_ICON}<span><b>${esc((f.count ? `${f.count} × ` : '') + f.name)}</b>${f.torque ? `<span class="mono">${esc(f.torque)}</span>` : ''}${f.note ? `<span class="muted">${esc(f.note)}</span>` : ''}</span></button></li>`;
  }).join('')}</ul>`;
}

function pageButtons(pages, title) {
  if (!pages?.length) return '';
  return `<div class="pages"><span class="muted">Revue technique :</span>${pages.map((n) =>
    `<button class="page-btn" data-page="${n}" data-title="${esc(title)}" title="${hasRta() ? 'Ouvrir la page' : 'Charge ta RTA pour ouvrir la page'}">p. ${n}</button>`).join('')}</div>`;
}

function openDetail(html) {
  detail.innerHTML = html;
  detail.hidden = false;
  document.body.classList.add('has-detail');
  detail.scrollTop = 0;
  resize();
}

function closeDetail() {
  detail.hidden = true;
  document.body.classList.remove('has-detail');
  resize();
}

function showPart(id, moveCamera = true) {
  const p = PARTS[id];
  if (!p) return;
  previewFx = pendingFx || (state.selected === id ? previewFx : null);
  pendingFx = null;
  state.proc = null; state.step = -1; state.selected = id;
  applyVisualState();
  if (moveCamera) focusOn([id]);
  const sys = systemOf(id);
  const procs = procsForPart[id] || [];
  openDetail(`
    <div class="detail-head">
      <span class="tag" style="--c:${sys.color}">${esc(sys.name)}</span>
      <button class="icon-btn" data-close aria-label="Fermer" title="Fermer (Échap)">✕</button>
    </div>
    <h2>${esc(p.name)}</h2>
    <p>${esc(p.desc)}</p>
    ${p.specs.length ? `<table class="specs">${p.specs.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('')}</table>` : ''}
    ${procs.length ? `<h3 class="group-title">Interventions</h3><ul class="list">${procs.map((pid) => procItem(procById(pid))).join('')}</ul>` : ''}
    ${partFasteners(id)}
    ${pageButtons(p.pages, p.name)}`);
}

function showProcedure(id, step = -1, moveCamera = true) {
  const p = procById(id);
  if (!p) return;
  const changedProc = state.proc !== p;
  state.proc = p; state.selected = null;
  state.step = Math.max(-1, Math.min(p.steps.length - 1, step));
  applyVisualState();
  if (moveCamera) {
    const cur = p.steps[state.step];
    const ids = cur ? [...(cur.focus || []), ...(cur.remove || [])] : p.parts;
    focusOn(ids.length ? ids : p.parts);
  }
  const sys = SYSTEMS.find((s) => s.id === p.system);
  const list = (title, items) => items?.length ? `<details ${changedProc ? '' : 'open'}><summary>${title} <span class="muted">(${items.length})</span></summary><ul>${items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul></details>` : '';
  openDetail(`
    <div class="detail-head">
      <span class="tag" style="--c:${sys.color}">${esc(sys.name)}</span>
      <button class="icon-btn" data-close aria-label="Fermer" title="Fermer (Échap)">✕</button>
    </div>
    <h2>${esc(p.title)}</h2>
    <div class="meta">
      <span class="badge d${p.difficulty}">${DIFFICULTY[p.difficulty]}</span>
      <span class="badge">${esc(p.duration)}</span>
      ${p.interval ? `<span class="badge soft">${esc(p.interval)}</span>` : ''}
    </div>
    ${p.warning ? `<p class="warning">${esc(p.warning)}</p>` : ''}
    ${list('Outils', p.tools)}
    ${list('Pièces et ingrédients', p.supplies)}
    ${p.torques.length ? `<table class="specs">${p.torques.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('')}</table>` : ''}
    <ol class="steps">${p.steps.map((s, i) => `
      <li class="${i === state.step ? 'active' : ''} ${i < state.step ? 'done' : ''}">
        <button data-step="${i}"><span class="num">${i + 1}</span><span>${esc(s.t)}${fastenerChips(s)}</span></button>
      </li>`).join('')}</ol>
    ${pageButtons(p.pages, p.title)}
    <div class="step-bar">
      <button class="btn ghost" data-step="${state.step - 1}" ${state.step < 0 ? 'disabled' : ''}>Précédente</button>
      <span class="step-count">${state.step < 0 ? 'Vue d’ensemble' : `Étape ${state.step + 1} / ${p.steps.length}`}</span>
      ${state.step < p.steps.length - 1
        ? `<button class="btn" data-step="${state.step + 1}">${state.step < 0 ? 'Commencer' : 'Suivante'}</button>`
        : `<button class="btn" data-step="-1">Tout remonter</button>`}
    </div>`);
  const active = detail.querySelector('.steps li.active');
  if (active && (!changedProc || !window.matchMedia('(max-width: 820px)').matches)) active.scrollIntoView({ block: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' });
}

// ===================== Navigation (hash) =====================
function navigate(hash) {
  if (location.hash === hash) route(); else location.hash = hash;
}

function route() {
  const [, kind, id, step] = location.hash.split('/');
  if (kind === 'proc' && procById(id)) {
    const s = step !== undefined ? parseInt(step, 10) : -1;
    const same = state.proc?.id === id;
    showProcedure(id, Number.isNaN(s) ? -1 : s, true);
    if (!same) closeSidebarMobile();
  } else if (kind === 'piece' && PARTS[id]) {
    showPart(id);
    closeSidebarMobile();
  } else {
    state.proc = null; state.selected = null; state.step = -1;
    applyVisualState();
    closeDetail();
  }
}
window.addEventListener('hashchange', route);

// ===================== Événements UI =====================
document.addEventListener('click', async (e) => {
  const t = e.target.closest('button, a');
  if (!t) return;
  if (t.matches('[data-close]')) { navigate('#/'); return; }
  if (t.dataset.step !== undefined && state.proc) {
    const n = parseInt(t.dataset.step, 10);
    history.replaceState(null, '', `#/proc/${state.proc.id}/${n}`);
    showProcedure(state.proc.id, n);
    return;
  }
  if (t.dataset.fx) {
    const id = t.dataset.fx;
    const on = previewFx === id ? null : id;
    previewFx = on;
    detail.querySelectorAll('[data-fx]').forEach((b) => b.classList.toggle('on', b.dataset.fx === on));
    applyVisualState();
    return;
  }
  if (t.dataset.q) { $('#search').value = t.dataset.q; renderSearch(t.dataset.q); return; }
  if (t.dataset.tabGo) { selectTab(t.dataset.tabGo); return; }
  if (t.dataset.page) {
    const ok = await showPage(parseInt(t.dataset.page, 10), t.dataset.title);
    if (!ok) { selectTab('rta'); openSidebarMobile(); }
  }
});

function selectTab(name) {
  sidebar.querySelectorAll('[role=tab]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
  sidebar.querySelectorAll('.tab-panel').forEach((p) => { p.hidden = p.dataset.panel !== name; });
}
sidebar.querySelectorAll('[role=tab]').forEach((b) => b.addEventListener('click', () => selectTab(b.dataset.tab)));

const searchInput = $('#search');
searchInput.addEventListener('input', () => { selectTab('search'); renderSearch(searchInput.value); });
searchInput.addEventListener('focus', openSidebarMobile);
$('#search-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const { procs, parts: ps } = search(searchInput.value);
  if (procs[0]) navigate(`#/proc/${procs[0].p.id}`);
  else if (ps[0]) navigate(`#/piece/${ps[0].id}`);
  searchInput.blur();
});

function openSidebarMobile() { document.body.classList.add('sidebar-open'); }
function closeSidebarMobile() { document.body.classList.remove('sidebar-open'); }
$('#menu-btn').addEventListener('click', () => document.body.classList.toggle('sidebar-open'));
$('#home-link').addEventListener('click', (e) => { e.preventDefault(); navigate('#/'); resetView(); });

const xrayBtn = $('#xray-btn');
function setXray(on) {
  state.xray = on;
  xrayBtn.setAttribute('aria-pressed', String(on));
  applyVisualState();
}
xrayBtn.addEventListener('click', () => setXray(!state.xray));

const explodeInput = $('#explode');
explodeInput.addEventListener('input', () => { state.explode = parseFloat(explodeInput.value); applyVisualState(); });
$('#reset-btn').addEventListener('click', resetView);
$('#body-color').addEventListener('input', (e) => setBodyColor(parts, e.target.value));

// Puces des systèmes
$('#systems').innerHTML = SYSTEMS.map((s) => `<button class="sys-chip" aria-pressed="true" data-sys="${s.id}" title="Afficher ou masquer : ${esc(s.name)}"><span class="dot" style="--c:${s.color}"></span>${esc(s.name)}</button>`).join('');
$('#systems').addEventListener('click', (e) => {
  const b = e.target.closest('[data-sys]');
  if (!b) return;
  const id = b.dataset.sys;
  if (state.hidden.has(id)) state.hidden.delete(id); else state.hidden.add(id);
  b.setAttribute('aria-pressed', String(!state.hidden.has(id)));
  applyVisualState();
});

document.addEventListener('keydown', (e) => {
  const typing = e.target.matches('input, textarea') || $('#rta-dialog').open;
  if (e.key === '/' && !typing) { e.preventDefault(); searchInput.focus(); return; }
  if (e.key === 'Escape' && !$('#rta-dialog').open) {
    if (document.activeElement === searchInput) searchInput.blur();
    else if (!detail.hidden) navigate('#/');
    closeSidebarMobile();
  }
  if (typing) return;
  if (e.key === 'x' || e.key === 'X') setXray(!state.xray);
  if (e.key === 'r' || e.key === 'R') resetView();
  if (e.key === 'e' || e.key === 'E') {
    state.explode = state.explode > 0.5 ? 0 : 1;
    explodeInput.value = state.explode;
    applyVisualState();
  }
  if (state.proc && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
    const n = state.step + (e.key === 'ArrowRight' ? 1 : -1);
    if (n >= -1 && n < state.proc.steps.length) {
      history.replaceState(null, '', `#/proc/${state.proc.id}/${n}`);
      showProcedure(state.proc.id, n);
    }
  }
});

// ===================== Démarrage =====================
initRtaDialog();
renderSearch();
renderParts();
renderMaintenance();
renderRtaPanel();
route();
restoreRta(() => { rtaInfo = { restoring: true }; renderRtaPanel(); })
  .then((info) => { rtaInfo = info; renderRtaPanel(); });

if ('serviceWorker' in navigator && location.protocol === 'https:') {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
