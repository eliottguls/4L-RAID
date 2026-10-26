// Lecture locale de la Revue Technique (PDF) : le fichier reste dans le navigateur
// (IndexedDB) et n'est jamais envoyé ni publié avec le site.

const DB_NAME = 'manuel-4l';
const STORE = 'files';
const KEY = 'rta';

let pdfjs = null;
let doc = null;
let current = 1;
let rendering = false;

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function dbGet() {
  try {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const r = db.transaction(STORE).objectStore(STORE).get(KEY);
      r.onsuccess = () => resolve(r.result || null);
      r.onerror = () => reject(r.error);
    });
  } catch { return null; }
}

async function dbPut(blob) {
  try {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(blob, KEY);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
    return true;
  } catch { return false; }
}

async function dbDelete() {
  try {
    const db = await openDb();
    db.transaction(STORE, 'readwrite').objectStore(STORE).delete(KEY);
  } catch { /* rien à faire */ }
}

async function loadPdfjs() {
  if (pdfjs) return pdfjs;
  pdfjs = await import('../vendor/pdfjs/pdf.min.mjs');
  pdfjs.GlobalWorkerOptions.workerSrc = new URL('../vendor/pdfjs/pdf.worker.min.mjs', import.meta.url).href;
  return pdfjs;
}

async function openBlob(blob) {
  const lib = await loadPdfjs();
  // Une URL locale permet à pdf.js de ne lire que les pages demandées (91 Mo sinon).
  doc = await lib.getDocument({ url: URL.createObjectURL(blob), disableAutoFetch: true }).promise;
  return doc.numPages;
}

export async function restoreRta(onFound) {
  const blob = await dbGet();
  if (!blob) return { loaded: false };
  onFound?.();
  try {
    const pages = await openBlob(blob);
    return { loaded: true, pages, name: blob.name || 'Revue technique', persisted: true };
  } catch { return { loaded: false }; }
}

export async function loadRtaFile(file) {
  const pages = await openBlob(file);
  const persisted = await dbPut(file);
  return { loaded: true, pages, name: file.name, persisted };
}

export async function forgetRta() {
  doc = null;
  await dbDelete();
}

export function hasRta() { return !!doc; }

const dialog = () => document.getElementById('rta-dialog');

async function render() {
  if (!doc || rendering) return;
  rendering = true;
  const label = document.getElementById('rta-page');
  label.textContent = `Page ${current} / ${doc.numPages} · chargement…`;
  try {
    const canvas = document.getElementById('rta-canvas');
    const wrap = canvas.parentElement;
    const page = await doc.getPage(current);
    const base = page.getViewport({ scale: 1 });
    const scale = Math.min(2.5, Math.max(0.5, (wrap.clientWidth - 16) / base.width));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const vp = page.getViewport({ scale: scale * dpr });
    canvas.width = vp.width;
    canvas.height = vp.height;
    canvas.style.width = `${vp.width / dpr}px`;
    canvas.style.height = `${vp.height / dpr}px`;
    await page.render({ canvasContext: canvas.getContext('2d'), viewport: vp }).promise;
    label.textContent = `Page ${current} / ${doc.numPages}`;
  } catch {
    label.textContent = `Page ${current} illisible`;
  } finally {
    rendering = false;
  }
}

export async function showPage(n, title = 'Revue technique') {
  if (!doc) return false;
  current = Math.max(1, Math.min(doc.numPages, n));
  document.getElementById('rta-title').textContent = title;
  const d = dialog();
  if (!d.open) d.showModal();
  await render();
  return true;
}

export function initRtaDialog() {
  const d = dialog();
  document.getElementById('rta-close').addEventListener('click', () => d.close());
  document.getElementById('rta-prev').addEventListener('click', () => { if (current > 1) { current--; render(); } });
  document.getElementById('rta-next').addEventListener('click', () => { if (doc && current < doc.numPages) { current++; render(); } });
  d.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') document.getElementById('rta-prev').click();
    if (e.key === 'ArrowRight') document.getElementById('rta-next').click();
  });
  d.addEventListener('click', (e) => { if (e.target === d) d.close(); });
}
