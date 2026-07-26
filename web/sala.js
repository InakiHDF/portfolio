// LA HABITACION
// =============
//
// Carga habitacion.glb y trata de dar la MISMA imagen que el render de
// Blender. Los tres puntos donde eso se juega:
//
//   1. La camara sale del propio GLB (CAM_ISO_SW). No se copia a mano una
//      posicion: se usa la que quedo aprobada en Blender.
//   2. Tone mapping AgX con la misma exposicion. Blender la cuenta en pasos
//      de diafragma y three en multiplicador, asi que hay una conversion.
//   3. Filtrado NEAREST y sin mipmaps en todas las texturas. Toda la estetica
//      del proyecto depende de que el texel se vea como bloque.
//
// Lo que TODAVIA no coincide, y hay que saberlo: la luz. El formato glTF no
// sabe representar luces de area, y once de las veinte de la escena lo son.
// Por eso ahora viajan solo nueve. La solucion definitiva es hornear la luz
// en texturas; hasta entonces esto es una aproximacion.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

// ---------------------------------------------------------------------------
// AJUSTES  (los mismos numeros que usan los scripts de render de Blender)
// ---------------------------------------------------------------------------

const CFG = {
  glb: "./modelos/habitacion.glb",
  camara: "CAM_ISO_SW",

  // Blender: view_settings.exposure = 0.9, en pasos de diafragma.
  // three: toneMappingExposure, multiplicador lineal. 2^0.9 = 1.866
  exposicion: Math.pow(2, 0.9),

  // Blender: mundo (0.36, 0.35, 0.34) con fuerza 0.15
  ambienteColor: 0x5c5a57,
  ambienteFuerza: 0.15,

  // Proporcion del render de Blender: 1712 x 945
  aspectoRef: 1712 / 945,

  bloom: { fuerza: 0.42, radio: 0.55, umbral: 0.72 },

  vinilos: { carpeta: "./vinilos/", indice: "./vinilos/pool.json", cantidad: 6 },

  vuelo: 0.055,          // suavidad del viaje de camara
  balanceo: 0.16,        // cuanto acompana el mouse
};

const $ = (id) => document.getElementById(id);
const fallar = (m) => {
  const e = $("error");
  e.style.display = "block";
  e.textContent += (e.textContent ? "\n" : "") + m;
  console.error(m);
};
addEventListener("error", (e) => fallar("Error: " + e.message));

// ---------------------------------------------------------------------------
// MOTOR
// ---------------------------------------------------------------------------

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = CFG.exposicion;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
scene.add(new THREE.AmbientLight(CFG.ambienteColor, CFG.ambienteFuerza));

// Camara provisoria: la definitiva sale del GLB
let camera = new THREE.PerspectiveCamera(63.6, CFG.aspectoRef, 0.05, 200);

let composer, bloomPass;
function armarComposer() {
  composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  bloomPass = new UnrealBloomPass(
    new THREE.Vector2(innerWidth, innerHeight),
    CFG.bloom.fuerza, CFG.bloom.radio, CFG.bloom.umbral);
  composer.addPass(bloomPass);
  composer.addPass(new OutputPass());   // aplica tone mapping al final
}

// ---------------------------------------------------------------------------
// ENCUADRE
// ---------------------------------------------------------------------------
//
// La camara de Blender esta calculada para 1712x945. En una ventana con otra
// proporcion hay que decidir que se conserva. Se conserva SIEMPRE el encuadre
// vertical cuando la ventana es mas ancha, y el horizontal cuando es mas
// angosta: asi nunca se pierde nada de lo que se ve en el render.

let fovVerticalRef = 63.6;

function ajustarTamano() {
  const w = Math.max(1, innerWidth), h = Math.max(1, innerHeight);
  const aspecto = w / h;
  camera.aspect = aspecto;
  if (aspecto >= CFG.aspectoRef) {
    camera.fov = fovVerticalRef;                       // ventana ancha
  } else {
    const tanH = Math.tan(THREE.MathUtils.degToRad(fovVerticalRef) / 2) * CFG.aspectoRef;
    camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(tanH / aspecto));
  }
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  if (composer) composer.setSize(w, h);
  if (bloomPass) bloomPass.resolution.set(w, h);
}
addEventListener("resize", ajustarTamano);

// ---------------------------------------------------------------------------
// ESTADO
// ---------------------------------------------------------------------------

const clicables = [];                 // mallas con propiedad `zona`
const vinilos = [];                   // los seis planos de la pared
let casa = null;                      // encuadre de origen
let destino = null;                   // a donde viaja la camara
const posActual = new THREE.Vector3();
const miraActual = new THREE.Vector3();
const mouse = new THREE.Vector2();
let acercado = false;

const titulo = $("titulo"), volver = $("volver"), pista = $("pista");

// ---------------------------------------------------------------------------
// CARGA
// ---------------------------------------------------------------------------

function pixelar(material) {
  for (const clave of ["map", "emissiveMap", "lightMap", "aoMap"]) {
    const t = material[clave];
    if (!t) continue;
    t.magFilter = THREE.NearestFilter;
    t.minFilter = THREE.NearestFilter;   // sin mipmaps: el bloque no se derrite
    t.generateMipmaps = false;
    t.anisotropy = 1;
    t.needsUpdate = true;
  }
}

function prepararHaz(malla) {
  // El haz del proyector se exporta como material comun. Aca se le devuelve
  // el comportamiento: aditivo, sin escribir profundidad y sin sombra.
  const m = malla.material;
  m.transparent = true;
  m.opacity = 0.16;
  m.blending = THREE.AdditiveBlending;
  m.depthWrite = false;
  m.side = THREE.DoubleSide;
  m.toneMapped = true;
  malla.castShadow = false;
  malla.receiveShadow = false;
}

new GLTFLoader().load(CFG.glb, (gltf) => {
  const raiz = gltf.scene;
  scene.add(raiz);
  raiz.updateMatrixWorld(true);          // hace falta antes de leer transformadas

  let camaraGlb = null;
  raiz.traverse((n) => {
    if (n.isCamera && n.name.startsWith(CFG.camara)) camaraGlb = n;
    if (n.isLight) {
      n.castShadow = true;
      if (n.shadow) {
        n.shadow.mapSize.set(1024, 1024);
        n.shadow.bias = -0.0015;
      }
    }
    if (!n.isMesh) return;

    n.castShadow = true;
    n.receiveShadow = true;
    const materiales = Array.isArray(n.material) ? n.material : [n.material];
    materiales.forEach(pixelar);

    if (n.name.startsWith("PROJECTOR_BEAM")) prepararHaz(n);
    if (n.userData && n.userData.zona) clicables.push(n);
    if (/^VINYL_WALL_\d+$/.test(n.name)) vinilos.push(n);
  });

  if (!camaraGlb) {
    fallar("El GLB no trae la camara " + CFG.camara + "; se usa una provisoria");
  } else {
    // La camara viene ANIDADA dentro del GLB. Si se la deja ahi, moverla en el
    // bucle escribiria coordenadas locales y quedaria en cualquier lado: el
    // exportador mete un nodo raiz con rotacion para pasar de Z-arriba a
    // Y-arriba. Por eso se la saca a espacio de mundo antes de tocarla.
    const mundo = camaraGlb.matrixWorld.clone();
    camaraGlb.removeFromParent();
    scene.add(camaraGlb);
    mundo.decompose(camaraGlb.position, camaraGlb.quaternion, camaraGlb.scale);
    camaraGlb.scale.set(1, 1, 1);
    camera = camaraGlb;
    camera.near = 0.05;
    camera.far = 200;
    fovVerticalRef = camera.fov;
  }

  // El encuadre de origen: el que quedo aprobado en Blender
  camera.updateMatrixWorld(true);
  const adelante = new THREE.Vector3(0, 0, -1)
    .applyQuaternion(camera.quaternion).normalize();
  casa = { pos: camera.position.clone(),
           mira: camera.position.clone().addScaledVector(adelante, 6) };
  destino = casa;
  posActual.copy(casa.pos);
  miraActual.copy(casa.mira);

  armarComposer();
  ajustarTamano();
  sortearVinilos();

  $("carga").classList.add("listo");
  pista.textContent = `${clicables.length} objetos clicables · ${vinilos.length} vinilos`;
  console.log("zonas:", [...new Set(clicables.map((o) => o.userData.zona))]);
}, undefined, (e) => fallar("No se pudo cargar el GLB: " + (e.message || e)));

// ---------------------------------------------------------------------------
// VINILOS AL AZAR
// ---------------------------------------------------------------------------

async function sortearVinilos() {
  if (!vinilos.length) return;
  let lista;
  try {
    lista = await (await fetch(CFG.vinilos.indice)).json();
  } catch (e) {
    return fallar("No se pudo leer el indice de vinilos: " + e.message);
  }
  // Barajado parcial: se sacan N distintos sin repetir
  const copia = lista.slice();
  for (let i = copia.length - 1; i > 0; i--) {
    const j = (Math.random() * (i + 1)) | 0;
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  const cargador = new THREE.TextureLoader();
  vinilos.sort((a, b) => a.name.localeCompare(b.name));
  vinilos.forEach((malla, i) => {
    const archivo = copia[i % copia.length];
    cargador.load(CFG.vinilos.carpeta + archivo, (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.flipY = false;                    // el GLB usa UVs de glTF
      malla.material.map = t;
      pixelar(malla.material);
      malla.material.needsUpdate = true;
      malla.userData.vinilo = archivo;
    });
  });
  console.log("vinilos sorteados de un pool de", lista.length);
}

// ---------------------------------------------------------------------------
// VIAJES DE CAMARA
// ---------------------------------------------------------------------------
//
// No hay estaciones escritas a mano: el encuadre se calcula del objeto que se
// toco. Se lo mira desde la misma direccion en que lo mira la camara de
// origen, a la distancia justa para que ocupe la fraccion pedida del cuadro.

const _caja = new THREE.Box3();
const _esfera = new THREE.Sphere();

function encuadrar(malla, ocupacion = 0.55) {
  _caja.setFromObject(malla);
  _caja.getBoundingSphere(_esfera);
  const radio = Math.max(_esfera.radius, 0.12);
  const mitad = THREE.MathUtils.degToRad(camera.fov) / 2;
  const dist = radio / (Math.tan(mitad) * ocupacion);
  const dir = casa.pos.clone().sub(_esfera.center).normalize();
  return { pos: _esfera.center.clone().addScaledVector(dir, dist),
           mira: _esfera.center.clone() };
}

function irA(malla) {
  destino = encuadrar(malla);
  acercado = true;
  titulo.textContent = malla.userData.zona_titulo || malla.userData.zona;
  titulo.classList.add("on");
  volver.classList.add("on");
}

function irACasa() {
  destino = casa;
  acercado = false;
  titulo.classList.remove("on");
  volver.classList.remove("on");
}

const rayo = new THREE.Raycaster();
const puntero = new THREE.Vector2();

renderer.domElement.addEventListener("pointerdown", (e) => {
  if (!casa) return;
  puntero.x = (e.clientX / innerWidth) * 2 - 1;
  puntero.y = -(e.clientY / innerHeight) * 2 + 1;
  rayo.setFromCamera(puntero, camera);
  const golpe = rayo.intersectObjects(clicables, false)[0];
  if (golpe && !acercado) irA(golpe.object);
  else if (acercado) irACasa();
});

addEventListener("pointermove", (e) => {
  mouse.x = (e.clientX / innerWidth) * 2 - 1;
  mouse.y = (e.clientY / innerHeight) * 2 - 1;
});
volver.addEventListener("click", (e) => { e.stopPropagation(); irACasa(); });
addEventListener("keydown", (e) => { if (e.key === "Escape") irACasa(); });

// ---------------------------------------------------------------------------
// BUCLE
// ---------------------------------------------------------------------------

const _pos = new THREE.Vector3();

function bucle() {
  requestAnimationFrame(bucle);
  if (!casa || !composer) return;

  const k = acercado ? CFG.vuelo * 1.4 : CFG.vuelo;
  posActual.lerp(destino.pos, k);
  miraActual.lerp(destino.mira, k);

  const balanceo = acercado ? CFG.balanceo * 0.35 : CFG.balanceo;
  _pos.copy(posActual);
  _pos.x += mouse.x * balanceo;
  _pos.y += -mouse.y * balanceo * 0.45;
  camera.position.copy(_pos);
  camera.lookAt(miraActual);

  composer.render();
}
bucle();

// Ayuda para ajustar desde la consola del navegador
window.__sala = {
  camara: () => ({
    pos: camera.position.toArray().map((n) => +n.toFixed(3)),
    mira: miraActual.toArray().map((n) => +n.toFixed(3)),
    fov: +camera.fov.toFixed(2),
  }),
  exposicion: (v) => { renderer.toneMappingExposure = v; },
  bloom: (f, r, u) => {
    if (f != null) bloomPass.strength = f;
    if (r != null) bloomPass.radius = r;
    if (u != null) bloomPass.threshold = u;
  },
  zonas: () => [...new Set(clicables.map((o) => o.userData.zona))],
};
