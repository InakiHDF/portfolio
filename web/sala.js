import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
// La versión va colgada de cada módulo y se mueve junto con la de `index.html`.
// Sin eso el navegador sirve la copia vieja de su caché y parece que editar el
// archivo no hizo nada. `tools/servidor.py` manda `no-store` para lo mismo, pero
// una entrada ya guardada de antes sobrevive igual: el número la invalida.
import { crearAvatar } from "./avatar.js?v=53";
import { CONTENIDO } from "./contenido.js?v=53";

const CFG = {
  glb: "./modelos/habitacion-console-ui.glb?v=1",
  camara: "CAM_ISO_SW",
  camarasSeccion: {
    web: "CAM_SECTION_WEB",
    video: "CAM_SECTION_VIDEO",
    texto: "CAM_SECTION_TEXTO",
    musica: "CAM_SECTION_MUSICA",
  },
  // El frontal del proyector sale de la pantalla, no de una pose escrita a mano.
  // `frontalidad` es cuánto se acerca la cámara de la sección a ese frontal: la
  // del GLB miraba la tela demasiado de costado. En 1 quedaría perpendicular
  // exacta, que es plano; en 0, la del GLB tal cual.
  encuadreVideo: { fov: 38, llenado: .84, frontalidad: .72 },

  /**
   * WEB — dos encuadres, uno por monitor, calculados sobre su propio plano.
   *
   * `CAM_SECTION_WEB` quedaba a 2,61 m del monitor principal y, medido contra
   * la pose del escritorio, **le pasaba por dentro de la cabeza**: la holgura
   * mínima de los rayos a las esquinas de la pantalla daba −2,1 cm. Por eso
   * cuando el avatar salía sorteado ahí tapaba todo.
   *
   * El `azimut` corre la cámara hacia el costado del cuarto y es lo que libera
   * la pantalla sin esconder al avatar: con −21° la holgura pasa a +6,3 cm y la
   * cámara queda por detrás de la cabeza, o sea él sigue en cuadro. La
   * `elevacion` negativa la baja apenas por debajo del centro de la pantalla.
   *
   * El lateral se mira de frente y de cerca —0,57 m—, donde el avatar no llega
   * a molestar (holgura 11,2 cm) y sus filas se leen enteras.
   */
  encuadreWebSitio: { fov: 34, llenado: .72, azimut: -21, elevacion: -6 },
  encuadreWebIndice: { fov: 36, llenado: .72, azimut: 0, elevacion: 0 },
  // Cuánto se curva el viaje de un monitor al otro para no atravesar al avatar.
  arcoWeb: { avance: .70, subida: .40 },
  // 16:9 exacto, así la tela, el canvas de la ficha y el archivo mp4 comparten
  // proporción y el pase a pantalla completa es un puro cambio de escala.
  planoVideo: { ancho: 1.92, alto: 1.08 },
  aspectoRef: 1712 / 945,
  luzPuntual: 0.0001,
  exposicion: Math.pow(2, .20),
  lightmapIntensidad: 3,
  bloom: { fuerza: .25, radio: .4, umbral: .88 },
  vinilos: { carpeta: "./vinilos/", indice: "./vinilos/pool.json" },

  /**
   * Los viajes de cámara, en segundos.
   *
   * Antes cada viaje era un lerp exponencial hacia el destino. Eso pone la
   * velocidad MÁXIMA en el primer cuadro y de ahí sólo baja: exactamente el
   * arranque brusco que había que sacar. Su constante de tiempo era 0,27 s, o
   * sea un pico de unas 3,7 veces la distancia por segundo.
   *
   * Ahora todo viaje tiene duración y pasa por `easeCamara`, que arranca en
   * cero, acelera hasta el medio y frena antes de llegar. El pico de esa curva
   * es 1,5 × distancia / duración: con 2,4 s da 0,63 — 5,9 veces más lento que
   * antes. Y a diferencia del lerp, un viaje con duración llega.
   */
  viajes: { seccion: 2.4, alFrenteDelVideo: 2 },
  pasePagina: 1.5,          // segundos que tarda una hoja en darse vuelta
  zoomCasa: 1.05,
  paneoSuavidad: .05,
  proyector: { color: 0xb9d9ff, intensidad: 18, angulo: .31, penumbra: .72 },
};

/**
 * Cuánto abre la tapa, y cuánto gira una hoja. Es el MISMO número a propósito:
 * si la hoja girara PI y la tapa 0,98·PI, la hoja aterrizaría 3,6° pasada y
 * quedaría cruzada contra la carilla de abajo.
 */
const ANGULO_LIBRO = Math.PI * .98;

const PALETA = { fondo: "#171816", panel: "#292a27", azul: "#758c99", naranja: "#c7793c", crema: "#ded9cb", gris: "#8f8c83", papel: "#d7cfba", tinta: "#201f1b" };

/**
 * Los rectángulos de todos los botones, en píxeles de su propio canvas.
 * Una sola fuente: los usa el dibujo y los usa `hotspotDeCanvas` para poner el
 * área clicable exactamente encima. Mover un botón es tocar un número acá.
 */
/**
 * La tira de abajo de la ficha de video, en píxeles de su canvas de 1200×675.
 *
 * Con un solo video no hay tira y el poster usa el cuadro entero. Antes la tira
 * era **vertical**, de 190 px, y ahí adentro no entraba nada: el título no cabía
 * y quedaba sólo el número del video en 13 px. Horizontal cada ficha tiene 284
 * px de ancho y el título entra en tres líneas de 21 px.
 */
const TIRA_VIDEO = CONTENIDO.video.length > 1 ? 128 : 0;

const RECTS = {
  videoPlay: [886, 675 - TIRA_VIDEO - 163, 250, 74],
  videoFicha: (i) => [24 + i * 296, 675 - TIRA_VIDEO + 16, 284, 96],
  webVisitar: [72, 470, 300, 78],
  webElegir: [400, 470, 360, 78],
  webFila: (i) => [28, 78 + i * 106, 664, 92],
};

const REPRESENTANTE = { web: "MONITOR_MAIN_PANEL", video: "SCREEN_SURFACE", texto: "NOTEBOOK_EAST", musica: "VINYL_WALL_01" };
const ZONAS = new Set(Object.keys(REPRESENTANTE));
const INDICE = { web: 0, video: 0, texto: 0 };
const $ = (id) => document.getElementById(id);
const carga = $("carga"), cargaBar = $("carga-bar"), cargaNum = $("carga-num"), cargaPaso = $("carga-paso");
const volver = $("volver"), intro = $("intro"), cursorLabel = $("cursor-label");

/* ─── La carga ─────────────────────────────────────────────────────────────
 *
 * Antes la página se daba por cargada apenas llegaba el GLB, y el avatar y los
 * vinilos aparecían un segundo después, ya con el telón levantado. Ahora la
 * barra cubre las cuatro etapas y no se descubre nada hasta que están las
 * cuatro. Los pesos son a ojo sobre lo que tarda cada una, no bytes exactos:
 * lo único que importa es que la barra avance sin frenarse.
 */
const PASOS = [
  { clave: "sala", texto: "Cargando la habitación", peso: .62 },
  { clave: "avatar", texto: "Buscando a Iñaki", peso: .16 },
  { clave: "vinilos", texto: "Ordenando los vinilos", peso: .10 },
  { clave: "contenido", texto: "Cargando el contenido", peso: .12 },
];
const avanceDe = new Map(PASOS.map((p) => [p.clave, 0]));
let revelado = false;

function avance(clave, fraccion) {
  avanceDe.set(clave, THREE.MathUtils.clamp(fraccion, 0, 1));
  const total = PASOS.reduce((suma, p) => suma + p.peso * avanceDe.get(p.clave), 0);
  const n = Math.min(100, Math.round(total * 100));
  cargaBar.style.width = n + "%";
  cargaNum.textContent = String(n).padStart(2, "0");
  const enCurso = PASOS.find((p) => avanceDe.get(p.clave) < 1);
  if (enCurso && cargaPaso) cargaPaso.textContent = enCurso.texto;
}

/** Todo enlace externo sale en otra pestaña: nadie pierde el recorrido. */
function abrir(url) {
  if (url) window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Las imágenes de contenido —capturas, portadas, poster— se dibujan adentro de
 * canvas que después viajan como textura. Un canvas no espera: si la imagen no
 * llegó todavía se dibuja sin ella y se vuelve a dibujar cuando carga.
 */
const IMAGENES = new Map();

/**
 * La entrada de una imagen, con su promesa. La promesa se cumple igual si la
 * imagen falla: una portada rota no puede dejar la pantalla de carga trabada.
 */
function entradaImagen(ruta) {
  let entrada = IMAGENES.get(ruta);
  if (!entrada) {
    entrada = { img: new Image(), listo: false };
    entrada.promesa = new Promise((resolver) => {
      entrada.img.onload = () => { entrada.listo = true; redibujarTodo(); resolver(); };
      entrada.img.onerror = () => { console.warn("no cargó la imagen", ruta); resolver(); };
    });
    entrada.img.src = ruta;
    IMAGENES.set(ruta, entrada);
  }
  return entrada;
}

function imagen(ruta) {
  if (!ruta) return null;
  const entrada = entradaImagen(ruta);
  return entrada.listo ? entrada.img : null;
}

/** Llena el marco recortando el sobrante, como `object-fit: cover`. */
function dibujarCubriendo(ctx, img, x, y, w, h) {
  const escala = Math.max(w / img.width, h / img.height);
  const iw = img.width * escala, ih = img.height * escala;
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.drawImage(img, x + (w - iw) * .5, y + (h - ih) * .5, iw, ih);
  ctx.restore();
}

function fallar(mensaje) {
  const e = $("error");
  e.hidden = false;
  e.textContent = mensaje;
  revelado = true;
  carga.classList.add("listo");
  console.error(mensaje);
}
addEventListener("error", (e) => fallar("Error: " + e.message));

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = CFG.exposicion;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.insertBefore(renderer.domElement, document.querySelector(".grain"));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050403);
let camera = new THREE.PerspectiveCamera(63.6, CFG.aspectoRef, .05, 200);
let composer, bloomPass, fovVerticalRef = 63.6;
const reloj = new THREE.Clock();

function armarComposer() {
  composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  bloomPass = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), CFG.bloom.fuerza, CFG.bloom.radio, CFG.bloom.umbral);
  composer.addPass(bloomPass);
  composer.addPass(new OutputPass());
}

/**
 * El paneo del cuadro de reposo, y el tirón que había al empezar y al terminar
 * un viaje.
 *
 * En Home la cámara no se mueve nunca: lo que se mueve es una ventana recortada
 * dentro del cuadro fijo de Blender, según el mouse. Eso se hacía con un
 * `setViewOffset` que se prendía y se apagaba **de golpe**: al entrar a una
 * sección se llamaba a `clearViewOffset()` en el mismo cuadro del click, y al
 * volver el paneo se reactivaba en el primer cuadro del regreso, con
 * `mouseSuave` donde hubiera quedado. Ese salto —hasta un 2,4 % del cuadro— es
 * el stagger: la cámara "se reacomodaba" y recién ahí arrancaba la animación.
 *
 * Ahora el paneo tiene intensidad y la maneja el propio viaje: se apaga con la
 * misma curva con la que la cámara se va, y se vuelve a encender con la misma
 * con la que vuelve. En 0 el recorte vale 1 y la ventana es el cuadro entero,
 * o sea exactamente lo mismo que no tener offset, pero sin discontinuidad.
 */
function aplicarPaneoCasa(intensidad) {
  if (!casa) return;
  // `clearViewOffset` recalcula la proyección, así que sólo cuando hace falta.
  if (intensidad <= .0005) { if (camera.view?.enabled) camera.clearViewOffset(); return; }
  const fullW = renderer.domElement.width / renderer.getPixelRatio();
  const fullH = renderer.domElement.height / renderer.getPixelRatio();
  const recorte = THREE.MathUtils.lerp(1, CFG.zoomCasa, intensidad);
  const viewW = fullW / recorte, viewH = fullH / recorte;
  camera.setViewOffset(fullW, fullH,
    (fullW - viewW) * (mouseSuave.x + 1) * .5,
    (fullH - viewH) * (1 - mouseSuave.y) * .5,
    viewW, viewH);
}

function proyeccionDeDetalle() { camera.zoom = 1; camera.updateProjectionMatrix(); }

function ajustarTamano() {
  const navH = 58, viewportW = Math.max(1, innerWidth), viewportH = Math.max(1, innerHeight - navH);
  const aspectoViewport = viewportW / viewportH;
  let w, h;
  if (aspectoViewport > CFG.aspectoRef) { w = viewportW; h = w / CFG.aspectoRef; }
  else { h = viewportH; w = h * CFG.aspectoRef; }
  camera.clearViewOffset();
  camera.zoom = 1;
  camera.aspect = CFG.aspectoRef;
  // Redimensionar en pleno vuelo no puede saltar al FOV de destino: mientras
  // vuela manda el FOV que la cámara tiene en ese instante.
  camera.fov = vuelo ? camera.fov : (destino?.fov ?? fovVerticalRef);
  camera.updateProjectionMatrix();
  renderer.domElement.style.left = `${(viewportW - w) * .5}px`;
  renderer.domElement.style.top = `${navH + (viewportH - h) * .5}px`;
  renderer.domElement.style.width = `${w}px`;
  renderer.domElement.style.height = `${h}px`;
  renderer.setSize(w, h, false);
  composer?.setSize(w, h);
  bloomPass?.resolution.set(w, h);
  aplicarPaneoCasa(paneoNivel);
}
addEventListener("resize", ajustarTamano);

const clicables = [], interfacesClicables = [], porZona = new Map(), vinilos = [];
const camarasSeccion = new Map(), superficies = {};
let casa = null, destino = null, acercado = false, zonaActiva = null;
let luzProyector = null, proyectorObjetivo = 0;
let notebook = null, coverTop = null, notebookBand = null, coverBaseX = 0, coverObjetivoX = 0, bookObjetivo = 0, bookProgreso = 0;
let pageTurnPivot = null, hojaDer = null, hojaIzq = null, transicionItem = null;
let camaraVideoFrente = null, avatar = null;
// Web tiene dos vistas, una por monitor, y se viaja de una a la otra.
const camarasWeb = { sitio: null, indice: null };
let vistaWeb = "sitio";
const posActual = new THREE.Vector3(), vistaAuxiliar = new THREE.Vector3();
const mouse = new THREE.Vector2(), mouseSuave = new THREE.Vector2(), puntero = new THREE.Vector2();
const rayo = new THREE.Raycaster();

function pixelar(material) {
  for (const clave of ["map", "emissiveMap"]) {
    const t = material?.[clave];
    if (!t) continue;
    t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
    t.generateMipmaps = false; t.anisotropy = 1; t.needsUpdate = true;
  }
}

function activarLightmap(material) {
  if (!material?.aoMap) return false;
  material.lightMap = material.aoMap;
  material.lightMapIntensity = CFG.lightmapIntensidad;
  material.lightMap.magFilter = THREE.LinearFilter;
  material.lightMap.minFilter = THREE.LinearMipmapLinearFilter;
  material.lightMap.generateMipmaps = true;
  material.lightMap.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  material.aoMap = null;
  material.needsUpdate = true;
  return true;
}

/**
 * Las dos pantallas de monitor, del mismo gris.
 *
 * No era la textura: los dos paneles comparten material (`MAT_BLOCKOUT_SCREEN`)
 * y comparten albedo (`TEX_SCREEN`, plano y oscuro). Lo que difiere es el
 * lightmap horneado. Promediando el atlas sobre el UV2 de cada panel:
 *
 *     MONITOR_MAIN_PANEL → (6, 4, 2)      casi negro
 *     MONITOR_SIDE_PANEL → (59, 41, 23)   diez veces más claro, y cálido
 *
 * De ahí que uno se lea gris oscuro y el otro gris claro.
 *
 * Una pantalla apagada tampoco tiene por qué recibir el rebote del cuarto, así
 * que los dos paneles pasan a un lightmap plano de un solo valor, el que hoy
 * tiene el principal. El atlas no se toca y no hay rebake. Se comprobó que
 * `MAT_BLOCKOUT_SCREEN` no lo usa ningún otro objeto de la escena: sólo esos
 * dos paneles, así que alcanza con tocar el material una vez.
 */
const GRIS_PANTALLA = 5;   // sobre 255, medido en el panel principal

function aplanarPantallas(raiz) {
  const paneles = ["MONITOR_MAIN_PANEL", "MONITOR_SIDE_PANEL"]
    .map((nombre) => raiz.getObjectByName(nombre)).filter((m) => m?.material?.lightMap);
  if (!paneles.length) return;

  const plano = new THREE.DataTexture(
    new Uint8Array([GRIS_PANTALLA, GRIS_PANTALLA, GRIS_PANTALLA, 255]), 1, 1);
  // El mismo espacio de color que el atlas que reemplaza: si no, el mismo byte
  // se decodifica distinto y el valor medido deja de significar lo mismo.
  plano.colorSpace = paneles[0].material.lightMap.colorSpace;
  plano.needsUpdate = true;

  for (const malla of paneles) {
    malla.material.lightMap = plano;
    malla.material.needsUpdate = true;
  }
}

function crearLuzProyector(lente, pantalla) {
  if (!lente || !pantalla) return;
  const origen = new THREE.Vector3(), objetivo = new THREE.Vector3();
  lente.getWorldPosition(origen); pantalla.getWorldPosition(objetivo);
  const distancia = origen.distanceTo(objetivo);
  luzProyector = new THREE.SpotLight(CFG.proyector.color, 0, distancia * 1.18, CFG.proyector.angulo, CFG.proyector.penumbra, 2);
  luzProyector.position.copy(origen); luzProyector.target.position.copy(objetivo); luzProyector.castShadow = false;
  scene.add(luzProyector, luzProyector.target);
}

function lienzo(ancho, alto, modo = "signal") {
  const canvas = document.createElement("canvas"); canvas.width = ancho; canvas.height = alto;
  const ctx = canvas.getContext("2d");
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const material = new THREE.MeshBasicMaterial({ map: texture, toneMapped: false, side: THREE.DoubleSide, transparent: true, opacity: 0, depthWrite: true });
  return { canvas, ctx, texture, material, plano: null, modo, nivel: 0, objetivo: 0, demora: 0 };
}

function crearPlanoUI(nombre, padre, ancho, alto, superficie, posicion, rotacion, accion) {
  const plano = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto), superficie.material);
  plano.name = nombre; plano.position.copy(posicion); plano.rotation.set(rotacion.x, rotacion.y, rotacion.z);
  plano.visible = false; plano.renderOrder = 14; plano.castShadow = false; plano.receiveShadow = false;
  plano.userData.basePosition = posicion.clone();
  plano.userData.uiAction = accion; padre.add(plano); superficie.plano = plano;
  if (accion) interfacesClicables.push(plano);
  return plano;
}

function crearHotspot(nombre, plano, ancho, alto, x, y, accion) {
  const material = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
  const area = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto), material);
  area.name = nombre; area.position.set(x, y, .003); area.userData.uiAction = accion;
  plano.add(area); interfacesClicables.push(area); return area;
}

/**
 * Parte un texto en las líneas que de verdad ocupa, con la tipografía que esté
 * puesta en el contexto. Medir antes de dibujar es lo que permite que el libro
 * acomode el bloque en vez de clavar posiciones y cortar lo que sobra.
 */
function partirEnLineas(ctx, texto, ancho) {
  const lineas = [];
  let linea = "";
  for (const palabra of String(texto).split(/\s+/)) {
    if (!palabra) continue;
    const prueba = linea ? `${linea} ${palabra}` : palabra;
    if (linea && ctx.measureText(prueba).width > ancho) { lineas.push(linea); linea = palabra; }
    else linea = prueba;
  }
  if (linea) lineas.push(linea);
  return lineas;
}

/** Pinta las líneas y devuelve la `y` de la última: por ahí sigue el bloque. */
function pintarLineas(ctx, lineas, x, y, altoLinea) {
  lineas.forEach((linea, i) => ctx.fillText(linea, x, y + i * altoLinea));
  return y + Math.max(0, lineas.length - 1) * altoLinea;
}

function textoAjustado(ctx, texto, x, y, ancho, altoLinea, maxLineas = 4) {
  pintarLineas(ctx, partirEnLineas(ctx, texto, ancho).slice(0, maxLineas), x, y, altoLinea);
}

/** El marco de una imagen que todavía no llegó: nunca un hueco blanco. */
function marcoVacio(ctx, x, y, w, h, color) {
  const g = ctx.createLinearGradient(x, y, x + w, y + h);
  g.addColorStop(0, "#2b302e"); g.addColorStop(.7, color || "#3a3f3c"); g.addColorStop(1, "#191a18");
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
}

/**
 * La tela del proyector: el poster a sangre y encima lo mínimo para elegir.
 *
 * El diseño anterior era una hoja de papel claro con el poster metido en un
 * recuadro chico, una tira vertical de 190 px a la izquierda y tres botones al
 * pie. Nada de eso entraba: en la tira no cabía un título y quedaba el número
 * del video en 13 px, ilegible. Ahora el poster ocupa todo y sobre él van el
 * título y el botón; la tira, si hace falta, es horizontal y abajo.
 */
function dibujarVideo() {
  const s = superficies.video, item = CONTENIDO.video[INDICE.video]; if (!s) return;
  const { ctx, canvas, texture } = s, w = canvas.width, h = canvas.height;
  const altoFicha = h - TIRA_VIDEO;

  const poster = imagen(item.poster);
  if (poster) dibujarCubriendo(ctx, poster, 0, 0, w, altoFicha);
  else marcoVacio(ctx, 0, 0, w, altoFicha, item.color);

  // Un degradado para que el texto se lea sobre cualquier imagen que venga.
  const sombra = ctx.createLinearGradient(0, altoFicha * .38, 0, altoFicha);
  sombra.addColorStop(0, "rgba(9,9,8,0)");
  sombra.addColorStop(1, "rgba(9,9,8,.94)");
  ctx.fillStyle = sombra; ctx.fillRect(0, altoFicha * .38, w, altoFicha * .62);

  const pie = altoFicha - 44;
  ctx.fillStyle = PALETA.naranja; ctx.fillRect(64, pie - 76, 6, 76);
  ctx.fillStyle = "#f1ede2"; ctx.font = "700 64px Arial Narrow, Arial";
  ctx.fillText(item.titulo.toUpperCase(), 90, pie - 24);
  const duracion = duracionVideo();
  if (duracion) {
    ctx.fillStyle = "#a9a498"; ctx.font = "700 21px Courier New";
    ctx.fillText(duracion, 90, pie + 8);
  }

  const play = RECTS.videoPlay;
  ctx.fillStyle = PALETA.naranja; ctx.fillRect(...play);
  ctx.fillStyle = "#1c1a16"; ctx.font = "700 22px Courier New"; ctx.textAlign = "center";
  ctx.fillText("▶  REPRODUCIR", play[0] + play[2] * .5, play[1] + 47);
  ctx.textAlign = "left";

  if (TIRA_VIDEO) {
    ctx.fillStyle = "#171714"; ctx.fillRect(0, altoFicha, w, TIRA_VIDEO);
    CONTENIDO.video.forEach((film, i) => {
      const [x, y, cw, ch] = RECTS.videoFicha(i), activo = i === INDICE.video;
      ctx.fillStyle = activo ? "#312f28" : "#222220"; ctx.fillRect(x, y, cw, ch);
      ctx.fillStyle = activo ? PALETA.naranja : "#4a4a44"; ctx.fillRect(x, y, 5, ch);
      const mini = imagen(film.poster);
      if (mini) dibujarCubriendo(ctx, mini, x + 18, y + 12, 128, 72);
      else { ctx.fillStyle = "#3a3a35"; ctx.fillRect(x + 18, y + 12, 128, 72); }
      // Sólo el título. Ni tipo ni año: no hacen falta para elegir un video.
      ctx.fillStyle = activo ? "#efe9dc" : "#8e8a80"; ctx.font = "700 21px Arial Narrow, Arial";
      textoAjustado(ctx, film.titulo.toUpperCase(), x + 160, y + 38, cw - 176, 25, 3);
    });
  }
  texture.needsUpdate = true;
}

/**
 * El logo del sitio sobre una placa clara.
 *
 * Los tres favicons son muy distintos entre sí —un lettering amarillo sin
 * fondo, un cuadrado color crema, un círculo negro— y sobre el carbón de la
 * interfaz el negro directamente desaparece. La placa los iguala: todos se leen
 * y ninguno pierde su forma. El logo va contenido, nunca recortado: un logo
 * recortado deja de ser el logo.
 */
function dibujarLogo(ctx, item, x, y, lado) {
  ctx.fillStyle = "#efece2"; ctx.fillRect(x, y, lado, lado);
  ctx.strokeStyle = "rgba(30,28,24,.22)"; ctx.lineWidth = 2;
  ctx.strokeRect(x + 1, y + 1, lado - 2, lado - 2);

  const img = imagen(item.logo);
  const margen = lado * .16, hueco = lado - margen * 2;
  if (img) {
    const escala = Math.min(hueco / img.width, hueco / img.height);
    const iw = img.width * escala, ih = img.height * escala;
    ctx.drawImage(img, x + (lado - iw) * .5, y + (lado - ih) * .5, iw, ih);
    return;
  }
  // Sin favicon usable: la inicial del sitio. Nunca un hueco.
  ctx.fillStyle = item.color;
  ctx.font = `700 ${Math.round(lado * .52)}px Arial Narrow, Arial`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(item.titulo[0].toUpperCase(), x + lado * .5, y + lado * .54);
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
}

/**
 * WEB — el monitor grande es el sitio y el chico es el índice.
 *
 * El diseño anterior metía una captura de la página en el monitor grande y la
 * lista de sitios en el chico, escrita en 15 px y mirada desde 2,6 m: ilegible.
 * Ahora cada monitor tiene su propia cámara —ver `CFG.encuadreWebSitio` y
 * `encuadreWebIndice`— y su propio contenido, dibujado para la distancia desde
 * la que se lo mira. Nada de capturas: los logos.
 */
function dibujarWeb() {
  const main = superficies.webMain, side = superficies.webSide, item = CONTENIDO.web[INDICE.web];
  if (!main || !side) return;

  /* ── El sitio, en el monitor principal ── */
  let ctx = main.ctx;
  let w = main.canvas.width, h = main.canvas.height;
  ctx.fillStyle = "#1b1c19"; ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#2a2c27"; ctx.fillRect(0, 0, w, 56);
  ctx.fillStyle = PALETA.naranja; ctx.fillRect(0, 0, 7, 56);
  ctx.fillStyle = "#96928a"; ctx.font = "700 21px Courier New";
  ctx.fillText(item.url.replace(/^https?:\/\/(www\.)?/, ""), 30, 37);

  dibujarLogo(ctx, item, 72, 110, 250);

  ctx.fillStyle = "#f1ede2"; ctx.font = "700 66px Arial Narrow, Arial";
  ctx.fillText(item.titulo.toUpperCase(), 366, 178);
  ctx.fillStyle = PALETA.naranja; ctx.font = "700 21px Courier New";
  ctx.fillText(`${item.tipo.toUpperCase()} / ${item.fecha}`, 368, 216);
  ctx.fillStyle = "#a29d92"; ctx.font = "24px Verdana";
  textoAjustado(ctx, item.descripcion, 368, 274, 600, 34, 3);

  const visitar = RECTS.webVisitar, elegir = RECTS.webElegir;
  ctx.fillStyle = PALETA.naranja; ctx.fillRect(...visitar);
  ctx.fillStyle = "#1c1a16"; ctx.font = "700 24px Courier New"; ctx.textAlign = "center";
  ctx.fillText("VISITAR ↗", visitar[0] + visitar[2] * .5, visitar[1] + 50);
  ctx.fillStyle = "#33352f"; ctx.fillRect(...elegir);
  ctx.fillStyle = "#ded9cb";
  ctx.fillText(`ELEGIR OTRO  (${CONTENIDO.web.length})`, elegir[0] + elegir[2] * .5, elegir[1] + 50);
  ctx.textAlign = "left";
  main.texture.needsUpdate = true;

  /* ── El índice, en el monitor chico ── */
  ctx = side.ctx;
  w = side.canvas.width; h = side.canvas.height;
  ctx.fillStyle = "#1b1c19"; ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#2a2c27"; ctx.fillRect(0, 0, w, 58);
  ctx.fillStyle = PALETA.naranja; ctx.fillRect(0, 0, 7, 58);
  ctx.fillStyle = "#96928a"; ctx.font = "700 22px Courier New";
  ctx.fillText("ELEGIR SITIO", 30, 39);

  CONTENIDO.web.forEach((p, i) => {
    const [x, y, ancho, alto] = RECTS.webFila(i), activo = i === INDICE.web;
    ctx.fillStyle = activo ? "#33352f" : "#232420"; ctx.fillRect(x, y, ancho, alto);
    ctx.fillStyle = activo ? PALETA.naranja : "#45463f"; ctx.fillRect(x, y, 6, alto);
    dibujarLogo(ctx, p, x + 22, y + 10, alto - 20);
    ctx.fillStyle = activo ? "#f1ede2" : "#918c82";
    ctx.font = "700 34px Arial Narrow, Arial";
    ctx.fillText(p.titulo.toUpperCase(), x + alto + 30, y + alto * .5 + 12);
  });
  side.texture.needsUpdate = true;
}

/**
 * UNA CARILLA POR ARTÍCULO
 * =======================
 *
 * El libro está abierto, así que se ven dos artículos a la vez: el spread son
 * las carillas `i` e `i+1`, y pasar de página avanza de a dos, como un libro de
 * verdad. Antes un mismo artículo ocupaba las dos carillas y salía todo
 * repetido: el subtítulo aparecía dos veces, había dos botones de leer —uno de
 * los cuales no hacía nada— y una firma inventada al pie.
 *
 * En cada carilla va lo que pidió y nada más: portada, título, subtítulo y el
 * botón de leer. Los de pasar de página no van sobre el contenido: son el
 * **margen exterior** de cada carilla. Se hace click en el borde de la hoja que
 * se quiere dar vuelta, que es como se pasa una página.
 */
const PAGINA = {
  ancho: 560, alto: 820,
  margen: 46,        // el papel se usa entero: no hay franja muerta
  botones: 76,
  separacion: 12,
  flecha: 76,
};
PAGINA.util = PAGINA.ancho - PAGINA.margen * 2;                 // 468
PAGINA.yBotones = PAGINA.alto - PAGINA.margen - PAGINA.botones; // 698
PAGINA.anchoLeer = PAGINA.util - PAGINA.flecha - PAGINA.separacion;

/**
 * La fila de abajo de cada carilla: leer el artículo y pasar de página.
 *
 * La flecha va del lado de afuera de cada carilla, así que en la izquierda
 * queda a la izquierda y en la derecha a la derecha, como los bordes del libro.
 */
const RECTS_PAGINA = {
  leer: (lado) => [
    PAGINA.margen + (lado === "izq" ? PAGINA.flecha + PAGINA.separacion : 0),
    PAGINA.yBotones, PAGINA.anchoLeer, PAGINA.botones],
  pasar: (lado) => [
    lado === "izq" ? PAGINA.margen : PAGINA.margen + PAGINA.anchoLeer + PAGINA.separacion,
    PAGINA.yBotones, PAGINA.flecha, PAGINA.botones],
};

const CUERPO_TITULO = 48, INTERLINEA_TITULO = 54;
const CUERPO_SUB = 25, INTERLINEA_SUB = 33;
const PORTADA_MAX = 300, PORTADA_MIN = 150;

/**
 * UNA CARILLA
 * ===========
 *
 * El bloque de texto **fluye**: se miden las líneas que ocupan de verdad el
 * título y el subtítulo, y recién ahí se decide dónde va cada cosa. Lo que
 * sobra se lo queda la portada, que se achica o desaparece.
 *
 * Antes el filete y el subtítulo estaban clavados en una `y` fija y el
 * subtítulo cortado a dos líneas: los títulos cortos dejaban un hueco enorme y
 * los subtítulos largos se cortaban a la mitad. **El subtítulo nunca se corta y
 * la tipografía nunca se achica**: la que cede es la imagen.
 */
function dibujarCarilla(ctx, item, lado, hayAdonde) {
  const w = PAGINA.ancho, h = PAGINA.alto, x0 = PAGINA.margen, ancho = PAGINA.util;

  ctx.fillStyle = lado === "izq" ? PALETA.papel : "#ddd5c1";
  ctx.fillRect(0, 0, w, h);
  // La sombra del lomo, del lado que da al centro del libro.
  const haciaElLomo = lado === "izq" ? w : 0;
  const lomo = ctx.createLinearGradient(haciaElLomo, 0, lado === "izq" ? w - 40 : 40, 0);
  lomo.addColorStop(0, "rgba(40,36,30,.20)"); lomo.addColorStop(1, "rgba(40,36,30,0)");
  ctx.fillStyle = lomo;
  ctx.fillRect(lado === "izq" ? w - 40 : 0, 0, 40, h);

  if (!item) return;

  ctx.font = `700 ${CUERPO_TITULO}px Georgia`;
  const titulo = partirEnLineas(ctx, item.titulo, ancho);
  ctx.font = `italic ${CUERPO_SUB}px Georgia`;
  const subtitulo = partirEnLineas(ctx, item.subtitulo, ancho);

  const disponible = PAGINA.yBotones - 32 - PAGINA.margen;
  // El hueco del título y su filete es fijo; lo que se reparte es el resto.
  const bloqueFijo = 34 + titulo.length * INTERLINEA_TITULO + 26 + 4 + 26;

  // **La imagen manda.** Se queda con lo que sobre, pero nunca baja de su
  // mínimo: sacarla cuando el subtítulo es largo rompía la continuidad de la
  // sección, que es peor que perder unas palabras.
  const portada = THREE.MathUtils.clamp(
    disponible - bloqueFijo - subtitulo.length * INTERLINEA_SUB,
    PORTADA_MIN, PORTADA_MAX);

  // Y si con esa imagen el subtítulo no entra entero, se corta con puntos
  // suspensivos: se pierde texto, nunca la imagen ni el encuadre.
  const caben = Math.floor((disponible - bloqueFijo - portada) / INTERLINEA_SUB);
  if (caben >= 1 && subtitulo.length > caben) {
    subtitulo.length = caben;
    subtitulo[caben - 1] = subtitulo[caben - 1].replace(/[\s,;:.]+$/, "") + "…";
  }

  let y = PAGINA.margen;
  const img = imagen(item.portada);
  if (img) dibujarCubriendo(ctx, img, x0, y, ancho, portada);
  else marcoVacio(ctx, x0, y, ancho, portada, item.color);
  ctx.strokeStyle = "rgba(40,36,30,.30)"; ctx.lineWidth = 3;
  ctx.strokeRect(x0, y, ancho, portada);
  y += portada + 34;

  ctx.fillStyle = PALETA.tinta; ctx.font = `700 ${CUERPO_TITULO}px Georgia`;
  y = pintarLineas(ctx, titulo, x0, y + CUERPO_TITULO, INTERLINEA_TITULO) + 26;

  ctx.fillStyle = item.color; ctx.fillRect(x0, y, 96, 4);
  y += 4 + 26;

  ctx.fillStyle = "#545046"; ctx.font = `italic ${CUERPO_SUB}px Georgia`;
  pintarLineas(ctx, subtitulo, x0, y + CUERPO_SUB, INTERLINEA_SUB);

  // Los dos botones se centran contra el centro geométrico de su rectángulo,
  // no contra una línea de base a ojo: con `alphabetic` la flecha caía baja y
  // distinto que el texto del otro botón, porque no comparten cuerpo.
  ctx.textAlign = "center"; ctx.textBaseline = "middle";

  const leer = RECTS_PAGINA.leer(lado);
  ctx.fillStyle = item.color; ctx.fillRect(...leer);
  ctx.fillStyle = "#f8f4ea"; ctx.font = "700 23px Courier New";
  ctx.fillText("LEER ARTÍCULO ↗", leer[0] + leer[2] * .5, leer[1] + leer[3] * .5);

  if (hayAdonde) {
    const pasar = RECTS_PAGINA.pasar(lado);
    ctx.fillStyle = "#3a372f"; ctx.fillRect(...pasar);
    ctx.fillStyle = "#e6e0d2"; ctx.font = "700 34px Courier New";
    // El eje X del canvas cae sobre el eje horizontal del libro, así que las
    // flechas se dibujan derechas: no hay que rotar nada.
    ctx.fillText(lado === "izq" ? "\u2190" : "\u2192",
      pasar[0] + pasar[2] * .5, pasar[1] + pasar[3] * .5);
  }
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
}

/** Cuántos spreads hay. Con cinco artículos, tres: (0,1) (2,3) (4,·). */
const SPREADS = Math.max(1, Math.ceil(CONTENIDO.texto.length / 2));
const articulo = (i) => CONTENIDO.texto[i] || null;

function pintarCarilla(superficie, item, lado) {
  if (!superficie) return;
  dibujarCarilla(superficie.ctx, item, lado, SPREADS > 1);
  superficie.texture.needsUpdate = true;
}

function dibujarTexto() {
  const i = INDICE.texto;
  pintarCarilla(superficies.textLeft, articulo(i), "izq");
  pintarCarilla(superficies.textRight, articulo(i + 1), "der");
}

/**
 * La cámara que mira algo de frente: perpendicular, centrada y a la distancia
 * justa para que entre entero con el margen pedido.
 *
 * Sale de la geometría —centro, normal y tamaño—, no de una pose copiada. Si
 * mañana la pantalla o la pared cambian de lugar, el encuadre las sigue.
 */
function encuadreFrontal(centro, normal, ancho, alto, { fov, llenado, azimut = 0, elevacion = 0 }) {
  const altoVisible = Math.max(alto / llenado, (ancho / llenado) / CFG.aspectoRef);
  const distancia = (altoVisible * .5) / Math.tan(THREE.MathUtils.degToRad(fov) * .5);

  // `azimut` gira la cámara alrededor del eje vertical de la superficie y
  // `elevacion` la sube o baja, siempre a la misma distancia y siempre mirando
  // al centro. Con los dos en cero es el frontal exacto de siempre.
  const arriba = new THREE.Vector3(0, 1, 0);
  const derecha = new THREE.Vector3().crossVectors(arriba, normal).normalize();
  const a = THREE.MathUtils.degToRad(azimut), e = THREE.MathUtils.degToRad(elevacion);
  const direccion = new THREE.Vector3()
    .addScaledVector(normal, Math.cos(a) * Math.cos(e))
    .addScaledVector(derecha, Math.sin(a) * Math.cos(e))
    .addScaledVector(arriba, Math.sin(e))
    .normalize();

  const pos = centro.clone().addScaledVector(direccion, distancia);
  const ref = new THREE.PerspectiveCamera(fov, CFG.aspectoRef, .05, 200);
  ref.position.copy(pos); ref.up.set(0, 1, 0); ref.lookAt(centro);
  return { pos, quat: ref.quaternion.clone(), fov, zoom: 1 };
}

const normalDe = (objeto) => new THREE.Vector3(0, 0, 1)
  .applyQuaternion(objeto.getWorldQuaternion(new THREE.Quaternion())).normalize();

/**
 * Corre un encuadre hacia otro más frontal, sin llegar del todo.
 *
 * La posición se interpola, pero la orientación **no**: se vuelve a apuntar al
 * centro del objeto. Interpolar los dos por separado deja encuadres intermedios
 * donde el objeto se va del centro, porque la rotación que mira al centro no es
 * la interpolación de las dos rotaciones que lo miran desde las puntas.
 */
function acercarAFrontal(desde, frontal, centro, k) {
  const pos = desde.pos.clone().lerp(frontal.pos, k);
  const fov = THREE.MathUtils.lerp(desde.fov, frontal.fov, k);
  const ref = new THREE.PerspectiveCamera(fov, CFG.aspectoRef, .05, 200);
  ref.position.copy(pos); ref.up.set(0, 1, 0); ref.lookAt(centro);
  return { pos, quat: ref.quaternion.clone(), fov, zoom: 1 };
}

function encuadreDePlano(plano, opciones) {
  plano.updateMatrixWorld(true);
  const { width, height } = plano.geometry.parameters;
  return encuadreFrontal(plano.getWorldPosition(new THREE.Vector3()), normalDe(plano), width, height, opciones);
}

/**
 * Un hotspot puesto con el mismo rectángulo que se usó para dibujar el botón.
 *
 * Antes las áreas clicables eran números a ojo en metros y había que
 * recalcularlos a mano cada vez que se movía un botón en el canvas. Acá el
 * rectángulo es uno solo, vive en `RECTS` y lo comparten el dibujo y el click.
 */
function hotspotDeCanvas(nombre, plano, superficie, rect, accion, holgura = 1) {
  const [x, y, w, h] = rect, { canvas } = superficie;
  const ancho = plano.geometry.parameters.width, alto = plano.geometry.parameters.height;
  return crearHotspot(nombre, plano,
    w / canvas.width * ancho * holgura, h / canvas.height * alto * holgura,
    ((x + w * .5) / canvas.width - .5) * ancho,
    (.5 - (y + h * .5) / canvas.height) * alto, accion);
}

/**
 * Un hotspot sobre una carilla del libro.
 *
 * Las carillas llevan el canvas girado 90° (`texture.rotation = -PI/2`) porque
 * el texto tiene que leerse en el eje del libro y no en el del plano. Con esa
 * rotación el eje X del canvas cae sobre el eje Y del plano y viceversa, y
 * además invertidos: por eso no sirve `hotspotDeCanvas`. La correspondencia sale
 * de la matriz que arma three.js para `uvTransform`, no de probar a ojo.
 */
function hotspotDePagina(nombre, plano, superficie, rect, accion) {
  const [x, y, w, h] = rect, { canvas } = superficie;
  const ancho = plano.geometry.parameters.width, alto = plano.geometry.parameters.height;
  return crearHotspot(nombre, plano,
    h / canvas.height * ancho,
    w / canvas.width * alto,
    (.5 - (y + h * .5) / canvas.height) * ancho,
    (.5 - (x + w * .5) / canvas.width) * alto,
    accion);
}

/**
 * EL PASE DE PÁGINA
 * =================
 *
 * La hoja que gira es **una sola**, rígida, con sus dos caras, y ninguna de las
 * dos está espejada: la de la derecha va con `Euler(-PI/2)` sobre el pivote y la
 * de la izquierda con `Euler(+PI/2)`, que al completar el giro de PI queda
 * exactamente con la misma orientación que la carilla izquierda fija. Las dos
 * son `FrontSide` y comparten el mismo giro de textura que las carillas.
 *
 * El desastre anterior venía de compensar un espejo con otro: la cara de atrás
 * era `BackSide`, con el canvas rotado 180° al dibujarlo Y la textura rotada al
 * revés. Tres correcciones encadenadas que no cerraban — de ahí que los textos
 * se leyeran al revés durante el giro y se acomodaran de golpe al final.
 *
 * El otro error era **cuándo** cambiaba cada cosa. Antes las carillas fijas se
 * redibujaban a mitad del recorrido, así que la página de abajo cambiaba antes
 * de que llegara la hoja que traía lo nuevo. Ahora nada cambia a mitad de
 * camino: lo que va a quedar ya viene pintado en la cara de la hoja, y las
 * carillas fijas sólo se tocan cuando la hoja las está tapando.
 *
 * Y no se apagan. Apagar la carilla de abajo mientras la hoja bajaba fue el
 * intento anterior, y era peor: a pocos grados del final la hoja todavía está
 * levantada y por el hueco se veía la tapa — ése era el parpadeo negro. Como
 * ahora la hoja calza exactamente sobre la carilla, alcanza el polygon offset.
 */
function prepararLibro(raiz) {
  notebook = raiz.getObjectByName("NOTEBOOK_EAST");
  coverTop = raiz.getObjectByName("NOTEBOOK_EAST_COVER_TOP");
  notebookBand = raiz.getObjectByName("NOTEBOOK_EAST_BAND");
  if (!notebook || !coverTop) return;
  coverBaseX = coverTop.rotation.x;
  coverObjetivoX = coverBaseX;

  const carilla = () => {
    const s = lienzo(PAGINA.ancho, PAGINA.alto, "paper");
    s.texture.center.set(.5, .5);
    s.texture.rotation = -Math.PI / 2;
    return s;
  };

  superficies.textLeft = carilla();
  superficies.textRight = carilla();
  const left = crearPlanoUI("UI_TEXT_LEFT", coverTop, .28, .198, superficies.textLeft,
    new THREE.Vector3(0, -.0035, .11), new THREE.Euler(Math.PI / 2, 0, 0), null);
  const right = crearPlanoUI("UI_TEXT_RIGHT", notebook, .28, .198, superficies.textRight,
    new THREE.Vector3(0, .0118, 0), new THREE.Euler(-Math.PI / 2, 0, 0), null);

  hotspotDePagina("TEXT_LEER_IZQ", left, superficies.textLeft, RECTS_PAGINA.leer("izq"), "text-leer-izq");
  hotspotDePagina("TEXT_LEER_DER", right, superficies.textRight, RECTS_PAGINA.leer("der"), "text-leer-der");
  if (SPREADS > 1) {
    hotspotDePagina("TEXT_ANTERIOR", left, superficies.textLeft, RECTS_PAGINA.pasar("izq"), "text-prev");
    hotspotDePagina("TEXT_SIGUIENTE", right, superficies.textRight, RECTS_PAGINA.pasar("der"), "text-next");
  }

  // La hoja que gira, sobre la misma bisagra que la tapa.
  // El pivote va en el origen exacto de la tapa y la hoja gira lo mismo que
  // ella: así la cara derecha calza sobre la carilla derecha en reposo y la
  // izquierda sobre la izquierda al llegar, sin un milímetro de diferencia.
  // Antes el pivote y los offsets eran otros y la hoja quedaba 5 mm corrida en
  // z al arrancar y 10,3 mm en y al llegar — de ahí el salto y el hundimiento.
  pageTurnPivot = new THREE.Group(); pageTurnPivot.name = "NOTEBOOK_PAGE_TURN";
  pageTurnPivot.position.set(0, .013, -.11); notebook.add(pageTurnPivot);

  hojaDer = carilla();
  hojaIzq = carilla();
  for (const s of [hojaDer, hojaIzq]) {
    s.material.transparent = false;
    s.material.opacity = 1;
    s.material.side = THREE.FrontSide;
    // La hoja queda coplanar con la carilla que tapa en los dos extremos del
    // giro. Para eso está el polygon offset: gana ella y no hay parpadeo.
    // Apagar la carilla de abajo, que fue el intento anterior, dejaba ver la
    // tapa por el hueco — ése era el parpadeo negro.
    s.material.polygonOffset = true;
    s.material.polygonOffsetFactor = -8;
    s.material.polygonOffsetUnits = -8;
  }
  // Las dos caras miran para lados opuestos, así que en cada extremo del giro
  // sólo una da a la cámara: no hace falta prenderlas ni apagarlas.
  const caraDer = crearPlanoUI("UI_HOJA_DER", pageTurnPivot, .28, .198, hojaDer,
    new THREE.Vector3(0, -.0012, .11), new THREE.Euler(-Math.PI / 2, 0, 0), null);
  const caraIzq = crearPlanoUI("UI_HOJA_IZQ", pageTurnPivot, .28, .198, hojaIzq,
    new THREE.Vector3(0, -.0035, .11), new THREE.Euler(Math.PI / 2, 0, 0), null);
  caraDer.visible = true; caraIzq.visible = true;
  caraDer.renderOrder = 16; caraIzq.renderOrder = 16;
  pageTurnPivot.visible = false;

  dibujarTexto();
}

function prepararInterfaces(raiz) {
  const screen = raiz.getObjectByName("SCREEN_SURFACE"), main = raiz.getObjectByName("MONITOR_MAIN_PANEL"), side = raiz.getObjectByName("MONITOR_SIDE_PANEL");
  // Los canvas van en la proporción exacta de su plano, si no el dibujo sale
  // estirado: 0,695/0,405 = 1,716 y 0,465/0,268 = 1,735.
  superficies.video = lienzo(1200, 675, "projector");
  superficies.webMain = lienzo(1030, 600, "monitor");
  superficies.webSide = lienzo(720, 415, "monitor");
  const video = crearPlanoUI("UI_VIDEO", screen, CFG.planoVideo.ancho, CFG.planoVideo.alto, superficies.video, new THREE.Vector3(0, 0, .0165), new THREE.Euler(0, 0, 0), null);
  const webMain = crearPlanoUI("UI_WEB_MAIN", main, .695, .405, superficies.webMain, new THREE.Vector3(.028, 0, 0), new THREE.Euler(0, Math.PI / 2, 0), null);
  const webSide = crearPlanoUI("UI_WEB_SIDE", side, .465, .268, superficies.webSide, new THREE.Vector3(.028, 0, 0), new THREE.Euler(0, Math.PI / 2, 0), null);

  hotspotDeCanvas("VIDEO_PLAY", video, superficies.video, RECTS.videoPlay, "video-play", 1.08);
  if (TIRA_VIDEO) {
    CONTENIDO.video.forEach((_, i) =>
      hotspotDeCanvas(`VIDEO_FICHA_${i}`, video, superficies.video, RECTS.videoFicha(i), `video-select-${i}`, 1.02));
  }
  // Cada botón vive en la vista donde tiene sentido: los del monitor grande
  // sólo cuando se está mirando el sitio, las filas sólo cuando se está
  // eligiendo. Si no, se pueden clickear por accidente desde la otra cámara,
  // donde se ven de unos pocos píxeles.
  hotspotDeCanvas("WEB_VISITAR", webMain, superficies.webMain, RECTS.webVisitar, "web-visitar", 1.08).userData.uiVista = "sitio";
  hotspotDeCanvas("WEB_ELEGIR", webMain, superficies.webMain, RECTS.webElegir, "web-elegir", 1.08).userData.uiVista = "sitio";
  CONTENIDO.web.forEach((_, i) => {
    hotspotDeCanvas(`WEB_FILA_${i}`, webSide, superficies.webSide, RECTS.webFila(i), `web-select-${i}`, 1.02)
      .userData.uiVista = "indice";
  });

  // El frontal del proyector: exactamente perpendicular a la tela y encuadrado
  // sobre ella. Es adonde viaja la cámara ANTES de abrir el reproductor.
  camaraVideoFrente = encuadreDePlano(video, CFG.encuadreVideo);

  // Y la cámara de la sección se corre hacia ese frontal. La del GLB miraba la
  // tela demasiado de costado. No se lleva hasta el frontal exacto —eso sería
  // un plano muerto—, se la acerca: `frontalidad` es cuánto.
  const desdeGlb = camarasSeccion.get("video");
  if (desdeGlb) {
    video.updateMatrixWorld(true);
    camarasSeccion.set("video", acercarAFrontal(
      desdeGlb, camaraVideoFrente, video.getWorldPosition(new THREE.Vector3()), CFG.encuadreVideo.frontalidad));
  }

  // Las dos cámaras de Web salen de sus propios planos. La del GLB queda sin
  // uso: estaba a 2,61 m y le pasaba por dentro de la cabeza del avatar.
  camarasWeb.sitio = encuadreDePlano(webMain, CFG.encuadreWebSitio);
  camarasWeb.indice = encuadreDePlano(webSide, CFG.encuadreWebIndice);
  camarasSeccion.set("web", camarasWeb.sitio);

  /**
   * El arco entre los dos monitores.
   *
   * En línea recta el viaje pasa **12 cm por dentro del torso** del avatar
   * cuando salió sorteada la pose del escritorio: él está justo en el medio de
   * las dos cámaras. Por arriba no se puede —la cabeza y el respaldo de la
   * silla cierran el paso— y por atrás tampoco, así que el recorrido se curva
   * hacia las pantallas: la cámara cruza por delante de él, sobre el
   * escritorio, subiendo apenas. Medido sobre la curva entera contra el
   * avatar, el respaldo y los dos monitores, la holgura mínima queda en 10,6 cm.
   *
   * El punto de apoyo sale de la geometría: el medio de las dos cámaras,
   * corrido contra la normal del monitor principal y levantado.
   */
  webMain.updateMatrixWorld(true); webSide.updateMatrixWorld(true);
  camarasWeb.centroSitio = webMain.getWorldPosition(new THREE.Vector3());
  camarasWeb.centroIndice = webSide.getWorldPosition(new THREE.Vector3());
  camarasWeb.apoyo = camarasWeb.sitio.pos.clone().lerp(camarasWeb.indice.pos, .5)
    .addScaledVector(normalDe(webMain), -CFG.arcoWeb.avance)
    .addScaledVector(new THREE.Vector3(0, 1, 0), CFG.arcoWeb.subida);

  prepararLibro(raiz); dibujarVideo(); dibujarWeb();
}

new GLTFLoader().load(CFG.glb, (gltf) => {
  const raiz = gltf.scene; scene.add(raiz); raiz.updateMatrixWorld(true);
  let camaraGlb = null, lente = null, pantalla = null, lightmaps = 0;
  raiz.traverse((n) => {
    if (n.isCamera && n.name.startsWith(CFG.camara)) camaraGlb = n;
    if (n.isCamera) {
      const zona = Object.keys(CFG.camarasSeccion).find((key) => CFG.camarasSeccion[key] === n.name);
      if (zona) { const pos = new THREE.Vector3(), quat = new THREE.Quaternion(), scale = new THREE.Vector3(); n.matrixWorld.decompose(pos, quat, scale); camarasSeccion.set(zona, { pos, quat, fov: n.fov, zoom: n.zoom }); }
    }
    if (n.name === "PROJECTOR_LENS") lente = n;
    if (n.name === "SCREEN_SURFACE") pantalla = n;
    if (n.isLight) { n.intensity *= CFG.luzPuntual; n.castShadow = true; }
    if (!n.isMesh) return;
    n.castShadow = true; n.receiveShadow = true;
    (Array.isArray(n.material) ? n.material : [n.material]).forEach((m) => { if (activarLightmap(m)) lightmaps++; pixelar(m); });
    if (n.name.startsWith("PROJECTOR_BEAM")) { n.visible = false; n.castShadow = false; n.receiveShadow = false; }
    if (ZONAS.has(n.userData?.zona)) { clicables.push(n); if (!porZona.has(n.userData.zona)) porZona.set(n.userData.zona, []); porZona.get(n.userData.zona).push(n); }
    if (/^VINYL_WALL_\d+$/.test(n.name)) vinilos.push(n);
  });
  aplanarPantallas(raiz);
  prepararInterfaces(raiz); crearLuzProyector(lente, pantalla);
  if (!camaraGlb) return fallar("El modelo no contiene la cámara principal.");
  const mundo = camaraGlb.matrixWorld.clone(); camaraGlb.removeFromParent(); scene.add(camaraGlb);
  mundo.decompose(camaraGlb.position, camaraGlb.quaternion, camaraGlb.scale); camaraGlb.scale.set(1, 1, 1);
  camera = camaraGlb; camera.near = .05; camera.far = 200; fovVerticalRef = camera.fov; camera.updateMatrixWorld(true);
  casa = { pos: camera.position.clone(), quat: camera.quaternion.clone(), fov: camera.fov, zoom: camera.zoom };
  destino = casa; posActual.copy(casa.pos);
  // Cada vez que se monta una pose se revisa si los monitores van encendidos.
  // Va acá y no en `cuandoListo` porque `usar()` cambia la pose desde consola.
  avatar = crearAvatar(scene, (estadoAvatar) => {
    monitoresSiempreEncendidos = estadoAvatar.pose === "escritorio";
    dibujarWeb();
    if (!zonaActiva) apagarModulos();
  });
  armarComposer(); ajustarTamano();
  avance("sala", 1);
  console.log(`sala: ${lightmaps} lightmaps · ${camarasSeccion.size} cámaras · ${interfacesClicables.length} hotspots`);

  // El telón se levanta cuando están las cuatro etapas, no cuando llegó el GLB.
  Promise.all([
    avatar.cuandoListo.then(() => avance("avatar", 1)),
    sortearVinilos().then(() => avance("vinilos", 1)),
    precargarContenido().then(() => avance("contenido", 1)),
  ]).then(() => revelar());
}, (e) => {
  if (e.total) avance("sala", e.loaded / e.total * .99);
}, (e) => fallar("No se pudo cargar la habitación: " + (e.message || e)));

/**
 * Levanta el telón. Con red o disco lentos alguna etapa podría no volver nunca;
 * un reloj de seguridad lo destraba, porque una pantalla de carga colgada es
 * peor que descubrir la habitación con un vinilo de menos.
 */
function revelar(porTiempo = false) {
  if (revelado) return;
  revelado = true;
  if (porTiempo) console.warn("carga: se levantó el telón por tiempo, algo no terminó");
  PASOS.forEach((p) => avance(p.clave, 1));
  carga.classList.add("listo");
}
setTimeout(() => revelar(true), 15000);

async function sortearVinilos() {
  if (!vinilos.length) return;
  try {
    const lista = await (await fetch(CFG.vinilos.indice)).json();
    const copia = lista.slice().sort(() => Math.random() - .5), loader = new THREE.TextureLoader();
    const ordenados = vinilos.sort((a, b) => a.name.localeCompare(b.name));
    let puestos = 0;
    // Se espera a que las texturas estén puestas, no a haberlas pedido: si no,
    // los vinilos aparecen con la página ya descubierta.
    await Promise.all(ordenados.map((malla, i) => new Promise((resolver) => {
      loader.load(CFG.vinilos.carpeta + copia[i % copia.length], (t) => {
        t.colorSpace = THREE.SRGBColorSpace; t.flipY = false;
        malla.material.map = t; pixelar(malla.material); malla.material.needsUpdate = true;
        avance("vinilos", ++puestos / ordenados.length); resolver();
      }, undefined, () => { avance("vinilos", ++puestos / ordenados.length); resolver(); });
    })));
  } catch (e) { console.warn("Pool de vinilos", e); }
}

function objetoDeZona(zona, preferido) { const o = porZona.get(zona) || []; return o.find((x) => x.name === preferido) || o[0]; }
// El nombre de la barra es el control de "habitación": marcado cuando no hay
// ninguna sección abierta. Antes había un recuadro con el nombre y además un
// enlace "Habitación" al lado, dos controles para lo mismo.
function activarNav(zona) {
  document.querySelectorAll(".nav-link").forEach((b) => b.classList.toggle("on", b.dataset.zone === zona));
  document.querySelectorAll(".brand").forEach((b) => b.classList.toggle("on", !zona));
}

function apuntarSuperficie(clave, objetivo, demora = 0) {
  const s = superficies[clave]; if (!s) return; s.objetivo = objetivo; s.demora = objetivo ? reloj.elapsedTime + demora : 0;
}

/**
 * Si la pose sorteada es la del escritorio, el avatar ya está sentado ahí: los
 * monitores tienen que estar prendidos siempre, no sólo al entrar a Web. Una
 * persona sentada frente a dos pantallas apagadas no tiene ningún sentido.
 */
let monitoresSiempreEncendidos = false;

function apagarModulos() {
  Object.keys(superficies).forEach((k) => apuntarSuperficie(k, 0));
  proyectorObjetivo = 0; bookObjetivo = 0; coverObjetivoX = coverBaseX;
  avatar?.velar(false);
  if (monitoresSiempreEncendidos) { apuntarSuperficie("webMain", 1, 0); apuntarSuperficie("webSide", 1, .12); }
}

function activarModulo(zona) {
  apagarModulos(); transicionItem = null;
  if (zona === "video") { dibujarVideo(); apuntarSuperficie("video", 1, .18); proyectorObjetivo = 1; }
  else if (zona === "web") { dibujarWeb(); apuntarSuperficie("webMain", 1, .12); apuntarSuperficie("webSide", 1, .34); }
  else if (zona === "texto") { dibujarTexto(); bookObjetivo = 1; coverObjetivoX = coverBaseX - ANGULO_LIBRO; apuntarSuperficie("textLeft", 1, .35); apuntarSuperficie("textRight", 1, .25); }
  // El avatar se vela sólo acá: en la pose de escritura está sentado justo
  // entre la cámara y el cuaderno y le tapa 8,2 cm del spread.
  // La demora hace que el avatar siga entero hasta bien entrado el viaje de
  // cámara: si empieza a velarse en el instante del click, ya está medio ido
  // cuando el recorrido recién arranca.
  avatar?.velar(zona === "texto", zona === "texto" ? CFG.viajes.seccion * .62 : 0);
  // Música todavía no tiene interfaz: la zona sólo acerca la cámara.
}

/** Viaja entre los dos monitores de Web. Cada uno tiene su propia cámara. */
function verWeb(vista) {
  if (zonaActiva !== "web" || vistaWeb === vista || !camarasWeb[vista]) return;
  const aIndice = vista === "indice";
  vistaWeb = vista;
  volarA(camarasWeb[vista], CFG.viajes.seccion, {
    paneo: 0,
    control: camarasWeb.apoyo,
    mirar: aIndice
      ? [camarasWeb.centroSitio, camarasWeb.centroIndice]
      : [camarasWeb.centroIndice, camarasWeb.centroSitio],
  });
}

function irA(malla) {
  if (!malla || !casa || !ZONAS.has(malla.userData.zona)) return;
  cerrarVideo(true);
  proyeccionDeDetalle(); zonaActiva = malla.userData.zona;
  vistaWeb = "sitio";   // Web siempre entra por el monitor grande
  volarA(zonaActiva === "web" ? camarasWeb.sitio : camarasSeccion.get(zonaActiva),
    CFG.viajes.seccion, { paneo: 0 });
  acercado = true; volver.classList.add("on"); intro.style.opacity = "0"; cursorLabel.classList.remove("on");
  renderer.domElement.style.cursor = "default"; activarNav(zonaActiva); activarModulo(zonaActiva);
}
function irAZona(zona) { irA(objetoDeZona(zona, REPRESENTANTE[zona])); }
function irACasa() {
  if (!casa) return;
  cerrarVideo(true);
  volarA(casa, CFG.viajes.seccion, { paneo: 1 });
  acercado = false; zonaActiva = null; volver.classList.remove("on"); intro.style.opacity = "1";
  cursorLabel.classList.remove("on"); renderer.domElement.style.cursor = "crosshair"; apagarModulos(); activarNav(null);
}

function actualizarContenido() {
  if (zonaActiva === "video") dibujarVideo();
  else if (zonaActiva === "web") dibujarWeb();
  else if (zonaActiva === "texto") dibujarTexto();
}

/**
 * Arranca el pase de página.
 *
 * Lo que va en cada superficie sale de qué se ve en cada momento, y todo se
 * pinta ACÁ, antes de que la hoja se mueva. Yendo hacia adelante:
 *
 *   cara derecha de la hoja  ← la carilla derecha de ahora, la que se levanta
 *   cara izquierda de la hoja ← la carilla izquierda nueva, que es lo que va a
 *                               quedar cuando la hoja se apoye
 *   carilla derecha fija     ← la carilla derecha NUEVA. Cambia ya, pero está
 *                               tapada por la hoja: se descubre al levantarse.
 *   carilla izquierda fija   ← sin tocar. Se la queda tapando la hoja al final.
 *
 * Yendo hacia atrás es el espejo exacto. Nada cambia a mitad de camino.
 */
function pasarPagina(direccion) {
  const spread = INDICE.texto / 2;
  const nuevoSpread = (spread + direccion + SPREADS) % SPREADS;
  const i = INDICE.texto, j = nuevoSpread * 2;

  if (direccion > 0) {
    pintarCarilla(hojaDer, articulo(i + 1), "der", true);
    pintarCarilla(hojaIzq, articulo(j), "izq", true);
    pintarCarilla(superficies.textRight, articulo(j + 1), "der", true);
  } else {
    pintarCarilla(hojaIzq, articulo(i), "izq", true);
    pintarCarilla(hojaDer, articulo(j + 1), "der", true);
    pintarCarilla(superficies.textLeft, articulo(j), "izq", true);
  }

  pageTurnPivot.rotation.x = direccion > 0 ? 0 : -ANGULO_LIBRO;
  pageTurnPivot.visible = true;
  return j;
}

function cambiarItem(direccion, indiceObjetivo = null) {
  if (!CONTENIDO[zonaActiva] || transicionItem) return;

  if (zonaActiva === "texto") {
    if (SPREADS < 2 || !pageTurnPivot) return;
    const hacia = pasarPagina(direccion);
    transicionItem = { zona: "texto", direccion, desde: INDICE.texto, hacia, tiempo: 0, duracion: CFG.pasePagina };
    return;
  }

  const lista = CONTENIDO[zonaActiva], desde = INDICE[zonaActiva];
  const hacia = indiceObjetivo ?? (desde + direccion + lista.length) % lista.length;
  transicionItem = { zona: zonaActiva, direccion, desde, hacia, tiempo: 0, cambiado: false, duracion: .58 };
}

function ejecutarAccion(golpe) {
  if (transicionItem) return true;
  const action = golpe.object.userData.uiAction;
  if (action === "video-play") abrirVideo();
  else if (action?.startsWith("video-select-")) {
    const indice = Number(action.slice(action.lastIndexOf("-") + 1));
    if (indice !== INDICE.video) cambiarItem(indice > INDICE.video ? 1 : -1, indice);
  }
  else if (action === "web-visitar") abrir(CONTENIDO.web[INDICE.web].url);
  else if (action === "web-elegir") verWeb("indice");
  else if (action?.startsWith("web-select-")) {
    const indice = Number(action.slice(action.lastIndexOf("-") + 1));
    if (indice !== INDICE.web) cambiarItem(indice > INDICE.web ? 1 : -1, indice);
    else dibujarWeb();
    verWeb("sitio");
  } else if (action === "text-prev") cambiarItem(-1);
  else if (action === "text-next") cambiarItem(1);
  else if (action === "text-leer-izq") abrir(articulo(INDICE.texto)?.url);
  else if (action === "text-leer-der") abrir(articulo(INDICE.texto + 1)?.url);
  return true;
}

/* ══════════════════════════════════════════════════════════════════════════
 * LOS VIAJES DE CÁMARA
 *
 * Todo movimiento de cámara pasa por acá y todo movimiento tiene duración y
 * curva. No queda un solo lerp exponencial: ése ponía la velocidad máxima en el
 * primer cuadro —el arranque brusco— y encima nunca llegaba del todo al
 * destino, sólo se le acercaba. Para abrir el reproductor hace falta saber que
 * la cámara está EXACTAMENTE de frente a la tela, porque si no el rectángulo
 * del video no coincide con el de la tela y el pase a pantalla completa salta.
 *
 * `destino` sigue siendo dónde tiene que estar la cámara; el vuelo es cómo
 * llega. Pedir un destino nuevo mientras vuela arranca un vuelo nuevo desde
 * donde esté, sin cortes.
 * ══════════════════════════════════════════════════════════════════════════ */

let vuelo = null;

/**
 * `paneo` es cuánto del recorte de Home está aplicado: 1 en reposo, 0 dentro de
 * una sección. Viaja como parte del vuelo —de dónde sale y a dónde va— en vez
 * de deducirse del estado, porque el vuelo al frontal del proyector también
 * ocurre con la sección abierta y ahí el paneo no tiene que moverse.
 */
let paneoNivel = 1;

/**
 * Un viaje de cámara.
 *
 *   alLlegar  qué hacer al terminar
 *   paneo     cuánto recorte de Home tiene que haber al llegar
 *   control   punto de apoyo para curvar el recorrido. Sin él la cámara va en
 *             línea recta, que es lo normal; con él describe una Bézier
 *             cuadrática, que es lo que hace falta cuando en el medio hay algo.
 *   mirar     [desde, hasta] — dos puntos del mundo. Si están, la orientación
 *             sale de mirar el punto interpolado en vez de interpolar las dos
 *             rotaciones. En un recorrido curvo el slerp apunta a cualquier
 *             lado en el medio; mirando a un punto, la cámara acompaña.
 */
function volarA(referencia, duracion, opciones = {}) {
  if (!referencia) return;
  const { alLlegar = null, paneo = paneoNivel, control = null, mirar = null } = opciones;
  destino = referencia;
  vuelo = {
    p0: posActual.clone(), q0: camera.quaternion.clone(), f0: camera.fov,
    ref: referencia, t: 0, dur: duracion, alLlegar,
    paneo0: paneoNivel, paneo1: paneo, control, mirar,
  };
}

/**
 * La curva de los viajes de cámara. No es la misma `ease` que usan los cambios
 * de contenido, y la diferencia es el punto del pedido: `ease` es un cúbico
 * cuya velocidad máxima llega a 3,0 × distancia / duración, mientras que ésta
 * queda en 1,5 — el pico más bajo que se puede tener saliendo del reposo y
 * frenando antes de llegar. Con 2,4 s da 0,63 contra los 3,71 del lerp viejo.
 */
const easeCamara = (p) => p * p * (3 - 2 * p);

function avanzarVuelo(dt) {
  const v = vuelo; v.t += dt;
  const p = Math.min(1, v.t / v.dur), e = easeCamara(p);

  if (v.control) {
    const u = 1 - e;
    posActual.set(0, 0, 0)
      .addScaledVector(v.p0, u * u)
      .addScaledVector(v.control, 2 * u * e)
      .addScaledVector(v.ref.pos, e * e);
  } else {
    posActual.copy(v.p0).lerp(v.ref.pos, e);
  }
  camera.position.copy(posActual);

  if (v.mirar) {
    // En los dos extremos esto da exactamente las orientaciones de salida y de
    // llegada, porque los encuadres se construyen mirando justo esos puntos.
    camera.up.set(0, 1, 0);
    camera.lookAt(vistaAuxiliar.copy(v.mirar[0]).lerp(v.mirar[1], e));
  } else {
    camera.quaternion.copy(v.q0).slerp(v.ref.quat, e);
  }
  paneoNivel = THREE.MathUtils.lerp(v.paneo0, v.paneo1, e);
  const fov = THREE.MathUtils.lerp(v.f0, v.ref.fov, e);
  if (Math.abs(fov - camera.fov) > .0001) { camera.fov = fov; camera.updateProjectionMatrix(); }
  if (p < 1) return;
  const alLlegar = v.alLlegar;
  vuelo = null;
  alLlegar?.();
}

/* ══════════════════════════════════════════════════════════════════════════
 * EL REPRODUCTOR
 *
 * ── Por qué ya no hay `VideoTexture` ──────────────────────────────────────
 *
 * La versión anterior ponía el video corriendo sobre la tela y después montaba
 * el reproductor encima, calzado al milímetro sobre el mismo rectángulo. La idea
 * era que no se notara el relevo. Se notaba igual, y no por las medidas: la tela
 * la dibuja el `EffectComposer` —tono AgX, exposición, bloom, y el grano encima
 * del canvas—, mientras que el `<video>` del DOM sale crudo. Son dos imágenes
 * distintas del mismo cuadro, así que el relevo era un salto de color y de
 * textura por más que los rectángulos coincidieran. Calzarlos mejor no podía
 * arreglarlo nunca.
 *
 * Ahora nadie se releva. La tela **siempre** muestra su ficha dibujada, y el
 * reproductor aparece por encima con un disolvido: la diferencia entre las dos
 * imágenes pasa a ser el efecto, en vez del error.
 *
 * ── Los cuatro tiempos ────────────────────────────────────────────────────
 *
 *   1. ACERCANDO  — la cámara viaja al frontal exacto del proyector.
 *   2. FUNDIENDO  — el reproductor aparece quieto, exactamente sobre el
 *      rectángulo de la tela, disolviéndose sobre ella.
 *   3. CRECIENDO  — ya visible y sin cambiar de imagen, crece hasta el cuadro
 *      entero. Con la cámara perpendicular es un puro cambio de escala.
 *   4. PLENO      — todo quieto y en su lugar: recién ahora empieza el video.
 *
 * Al cerrar, el camino exacto al revés.
 * ══════════════════════════════════════════════════════════════════════════ */

const FUNDIDO = 420;     // ms del disolvido entre la ficha de la tela y el cuadro
const CRECIDA = 950;     // ms que tarda el cuadro en llenar la pantalla
const OCIO = 2000;       // ms sin actividad y la barra de controles se va sola
const videoStage = $("video-stage"), videoShell = $("video-shell"), videoEl = $("video-el");
let videoFase = "off";   // off · acercando · fundiendo · creciendo · pleno · encogiendo · saliendo
let temporizador = null, ocioso = null;

function duracionVideo() {
  const s = videoEl?.duration;
  if (!s || !isFinite(s)) return "";
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

/** Dónde cae, en píxeles de la ventana, el rectángulo de la tela. */
function rectanguloDeTela() {
  const plano = superficies.video?.plano;
  const lienzoDom = renderer.domElement.getBoundingClientRect();
  if (!plano) return lienzoDom;
  const { width, height } = plano.geometry.parameters;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
    const v = plano.localToWorld(new THREE.Vector3(sx * width * .5, sy * height * .5, 0)).project(camera);
    const px = lienzoDom.left + (v.x * .5 + .5) * lienzoDom.width;
    const py = lienzoDom.top + (-v.y * .5 + .5) * lienzoDom.height;
    x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py);
  }
  return { left: x0, top: y0, width: x1 - x0, height: y1 - y0 };
}

/** El cuadro final: 16:9 centrado en lo que queda bajo la barra. */
function rectanguloPleno() {
  const navH = 58, disponibleW = innerWidth, disponibleH = innerHeight - navH;
  const proporcion = CFG.planoVideo.ancho / CFG.planoVideo.alto;
  let w = disponibleW * .94, h = w / proporcion;
  if (h > disponibleH * .88) { h = disponibleH * .88; w = h * proporcion; }
  return { left: (disponibleW - w) * .5, top: navH + (disponibleH - h) * .5, width: w, height: h };
}

function ubicar(caja) {
  videoShell.style.left = `${caja.left}px`;
  videoShell.style.top = `${caja.top}px`;
  videoShell.style.width = `${caja.width}px`;
  videoShell.style.height = `${caja.height}px`;
}

const transicionDeCaja = (ms, curva) => ["left", "top", "width", "height"]
  .map((p) => `${p} ${ms}ms cubic-bezier(${curva})`).join(", ");

function abrirVideo() {
  if (zonaActiva !== "video" || videoFase !== "off" || !camaraVideoFrente) return;
  const item = CONTENIDO.video[INDICE.video];
  if (videoEl.dataset.archivo !== item.archivo) {
    videoEl.src = item.archivo; videoEl.poster = item.poster; videoEl.dataset.archivo = item.archivo;
  }
  videoFase = "acercando";
  videoEl.pause();
  videoEl.currentTime = 0;
  volarA(camaraVideoFrente, CFG.viajes.alFrenteDelVideo, { alLlegar: fundirVideo });
  sincronizarControles();
}

/** La llama el vuelo al terminar: la cámara ya está perpendicular a la tela. */
function fundirVideo() {
  if (videoFase !== "acercando") return;
  videoFase = "fundiendo";
  videoShell.style.transition = "none";
  videoShell.style.opacity = "0";
  ubicar(rectanguloDeTela());
  videoStage.classList.add("montado");
  videoStage.setAttribute("aria-hidden", "false");
  // Dos cuadros: uno para que el navegador acepte el estado inicial y recién el
  // siguiente para que la transición tenga de dónde salir.
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (videoFase !== "fundiendo") return;
    videoShell.style.transition = `opacity ${FUNDIDO}ms ease`;
    videoShell.style.opacity = "1";
  }));
  clearTimeout(temporizador);
  temporizador = setTimeout(crecerVideo, FUNDIDO + 40);
}

/** Ya visible y quieto sobre la tela: ahora sí crece, sin cambiar de imagen. */
function crecerVideo() {
  if (videoFase !== "fundiendo") return;
  videoFase = "creciendo";
  videoShell.style.transition = transicionDeCaja(CRECIDA, ".22,.68,.16,1");
  ubicar(rectanguloPleno());
  videoStage.classList.add("on");
  clearTimeout(temporizador);
  temporizador = setTimeout(() => {
    if (videoFase !== "creciendo") return;
    videoFase = "pleno"; videoStage.classList.add("pleno");
    // Todo quieto y en su lugar. Recién ahora arranca.
    videoEl.play().catch(() => { /* si el navegador lo bloquea, queda el botón */ });
    sincronizarControles();
  }, CRECIDA + 40);
}

/** Deja el reproductor desmontado y la tela como estaba. No anima nada. */
function desmontarVideo() {
  clearTimeout(temporizador); clearTimeout(ocioso);
  videoEl.pause();
  videoStage.classList.remove("on", "montado", "pleno", "quieto");
  videoStage.setAttribute("aria-hidden", "true");
  videoShell.style.transition = "none";
  videoShell.style.opacity = "0";
  videoFase = "off";
}

function cerrarVideo(inmediato = false) {
  if (videoFase === "off") return;
  clearTimeout(temporizador); clearTimeout(ocioso);
  videoStage.classList.remove("quieto");

  // Sin rampas: se usa al salir de la sección, donde el corte queda tapado por
  // el viaje de cámara que arranca justo después.
  if (inmediato) { desmontarVideo(); return; }

  // Cancelar durante el acercamiento: no hay nada montado todavía, sólo hay que
  // devolver la cámara a la sección.
  if (videoFase === "acercando") {
    vuelo = null; videoFase = "off";
    if (zonaActiva === "video") volarA(camarasSeccion.get("video"), CFG.viajes.seccion);
    return;
  }

  // El camino exacto al revés: encoge hasta la tela, y una vez encima de ella se
  // disuelve. La tela nunca cambió de imagen, así que al desaparecer el cuadro
  // ya está lo que tiene que quedar.
  videoFase = "encogiendo";
  videoStage.classList.remove("on", "pleno");
  videoShell.style.transition = transicionDeCaja(CRECIDA, ".3,.1,.2,1");
  ubicar(rectanguloDeTela());
  temporizador = setTimeout(() => {
    if (videoFase !== "encogiendo") return;
    videoFase = "saliendo";
    videoShell.style.transition = `opacity ${FUNDIDO}ms ease`;
    videoShell.style.opacity = "0";
    temporizador = setTimeout(() => {
      if (videoFase !== "saliendo") return;
      desmontarVideo();
      if (zonaActiva === "video") volarA(camarasSeccion.get("video"), CFG.viajes.seccion);
    }, FUNDIDO + 40);
  }, CRECIDA + 40);
}

/**
 * La barra de controles se va sola y vuelve al mover el mouse. Sólo se esconde
 * con el video corriendo: en pausa el que mira está decidiendo algo y necesita
 * los botones puestos.
 */
function despertarControles() {
  clearTimeout(ocioso);
  videoStage.classList.remove("quieto");
  if (videoFase !== "pleno" || videoEl.paused) return;
  ocioso = setTimeout(() => {
    if (videoFase === "pleno" && !videoEl.paused) videoStage.classList.add("quieto");
  }, OCIO);
}
videoStage.addEventListener("pointermove", despertarControles);
videoStage.addEventListener("pointerdown", (e) => {
  despertarControles();
  // Mientras se abre, el telón ya tapa el canvas y el botón de cerrar todavía
  // no está: sin esto un click ahí no hace nada y parece colgado.
  if (videoFase === "fundiendo" || videoFase === "creciendo") { e.preventDefault(); cerrarVideo(false); }
});

function coordenadasCanvas(e) {
  const rect = renderer.domElement.getBoundingClientRect(); puntero.x = ((e.clientX - rect.left) / rect.width) * 2 - 1; puntero.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
}

function hotspotsActivos() {
  return interfacesClicables.filter((o) =>
    o.parent?.visible && o.parent.material?.opacity > .12
    && (!o.userData.uiVista || o.userData.uiVista === vistaWeb));
}

renderer.domElement.addEventListener("pointerdown", (e) => {
  if (!casa) return;
  // Mientras la cámara viaja al frontal, el click cancela el video y no saca
  // de la sección: el reproductor todavía no tapa nada.
  if (videoFase !== "off") return cerrarVideo(false);
  coordenadasCanvas(e); rayo.setFromCamera(puntero, camera);
  if (acercado) {
    const ui = rayo.intersectObjects(hotspotsActivos(), false)[0];
    if (ui) { ejecutarAccion(ui); return; }
    irACasa(); return;
  }
  const golpe = rayo.intersectObjects(clicables, false)[0]; if (golpe) irA(golpe.object);
});

renderer.domElement.addEventListener("pointermove", (e) => {
  mouse.x = THREE.MathUtils.clamp(e.clientX / innerWidth * 2 - 1, -1, 1); mouse.y = THREE.MathUtils.clamp(-((e.clientY - 58) / Math.max(1, innerHeight - 58)) * 2 + 1, -1, 1);
  cursorLabel.style.left = e.clientX + "px"; cursorLabel.style.top = e.clientY + "px";
  if (!casa) return cursorLabel.classList.remove("on");
  coordenadasCanvas(e); rayo.setFromCamera(puntero, camera);
  if (acercado) {
    // Fuera de un botón el cursor queda normal. La lupa con menos anunciaba un
    // "alejar" que no es lo que pasa, y ensuciaba toda la sección.
    const ui = rayo.intersectObjects(hotspotsActivos(), false)[0];
    cursorLabel.classList.remove("on"); renderer.domElement.style.cursor = ui ? "pointer" : "default"; return;
  }
  const golpe = rayo.intersectObjects(clicables, false)[0];
  renderer.domElement.style.cursor = golpe ? "pointer" : "crosshair";
  if (golpe) { cursorLabel.textContent = `ABRIR ${golpe.object.userData.zona_titulo || golpe.object.userData.zona}`; cursorLabel.classList.add("on"); }
  else cursorLabel.classList.remove("on");
});
renderer.domElement.addEventListener("pointerleave", () => { cursorLabel.classList.remove("on"); renderer.domElement.style.cursor = "crosshair"; });

document.querySelectorAll("[data-zone]").forEach((b) => b.addEventListener("click", () => irAZona(b.dataset.zone)));
document.querySelectorAll("[data-home]").forEach((b) => b.addEventListener("click", (e) => { e.preventDefault(); irACasa(); }));
volver.addEventListener("click", irACasa);
addEventListener("keydown", (e) => {
  if (e.key === "Escape" && videoFase !== "off") return cerrarVideo(false);
  if (videoFase !== "off") return;                       // el reproductor manda sus propias teclas
  if (e.key === "Escape") irACasa();
  else if (acercado && e.key === "ArrowLeft") cambiarItem(-1);
  else if (acercado && e.key === "ArrowRight") cambiarItem(1);
  else if (acercado && e.key === "Enter" && zonaActiva === "video") abrirVideo();
});

/* ─── Controles del reproductor ────────────────────────────────────────── */

const vcPlay = $("vc-play"), vcBarra = $("vc-barra"), vcProgreso = $("vc-progreso");
const vcTiempo = $("vc-tiempo"), vcMute = $("vc-mute"), vcPleno = $("vc-pleno"), vcTitulo = $("vc-titulo");

const reloj_mmss = (s) => !isFinite(s) ? "--:--"
  : `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

function sincronizarControles() {
  const item = CONTENIDO.video[INDICE.video];
  vcTitulo.textContent = `${item.titulo} — ${item.tipo}, ${item.fecha}`;
  vcPlay.textContent = videoEl.paused ? "▶" : "❚❚";
  vcPlay.setAttribute("aria-label", videoEl.paused ? "Reproducir" : "Pausar");
  vcMute.textContent = videoEl.muted || !videoEl.volume ? "SIN AUDIO" : "AUDIO";
  vcTiempo.textContent = `${reloj_mmss(videoEl.currentTime)} / ${reloj_mmss(videoEl.duration)}`;
  const p = videoEl.duration ? videoEl.currentTime / videoEl.duration : 0;
  vcProgreso.style.width = `${p * 100}%`;
  vcBarra.setAttribute("aria-valuenow", Math.round(p * 100));
}

const alternarPlay = () => (videoEl.paused ? videoEl.play().catch(() => {}) : videoEl.pause());

vcPlay.addEventListener("click", alternarPlay);
vcMute.addEventListener("click", () => { videoEl.muted = !videoEl.muted; sincronizarControles(); });
vcPleno.addEventListener("click", () => {
  if (document.fullscreenElement) document.exitFullscreen();
  else videoShell.requestFullscreen?.().catch(() => {});
});
$("video-back").addEventListener("click", () => cerrarVideo(false));
videoEl.addEventListener("click", alternarPlay);
["play", "pause", "timeupdate", "loadedmetadata", "volumechange", "ended"].forEach((evento) =>
  videoEl.addEventListener(evento, () => {
    sincronizarControles();
    // Sólo despiertan los eventos que son una decisión de quien mira. `timeupdate`
    // llega unas cuatro veces por segundo mientras corre el video: si también
    // despertara, el temporizador de ocio se reiniciaría siempre y la barra no
    // se escondería nunca. Era exactamente eso lo que estaba pasando.
    if (evento === "play" || evento === "pause") despertarControles();
    if (evento === "loadedmetadata" && zonaActiva === "video") dibujarVideo();
  }));

/** Buscar: click o arrastre sobre la barra. */
function buscarEn(e) {
  const r = vcBarra.getBoundingClientRect();
  if (videoEl.duration) videoEl.currentTime = THREE.MathUtils.clamp((e.clientX - r.left) / r.width, 0, 1) * videoEl.duration;
}
vcBarra.addEventListener("pointerdown", (e) => { vcBarra.setPointerCapture(e.pointerId); buscarEn(e); });
vcBarra.addEventListener("pointermove", (e) => { if (vcBarra.hasPointerCapture(e.pointerId)) buscarEn(e); });

addEventListener("keydown", (e) => {
  if (videoFase === "off") return;
  despertarControles();
  if (e.key === " " || e.key === "k") { e.preventDefault(); alternarPlay(); }
  else if (e.key === "ArrowLeft") videoEl.currentTime = Math.max(0, videoEl.currentTime - 5);
  else if (e.key === "ArrowRight") videoEl.currentTime = Math.min(videoEl.duration || 0, videoEl.currentTime + 5);
  else if (e.key === "m") { videoEl.muted = !videoEl.muted; sincronizarControles(); }
});

// Si la ventana cambia de tamaño con el reproductor abierto, el cuadro se
// recalcula: si no, queda anclado a un rectángulo que ya no existe.
addEventListener("resize", () => {
  if (videoFase === "pleno") { videoShell.style.transition = "none"; ubicar(rectanguloPleno()); }
});

/* ─── Precarga ─────────────────────────────────────────────────────────── */

function redibujarTodo() {
  // Nunca en medio de un pase: repintar las carillas fijas ahí borraría lo que
  // el pase dejó preparado en ellas.
  if (transicionItem?.zona === "texto") return;
  if (zonaActiva) actualizarContenido();
  else { dibujarVideo(); dibujarWeb(); dibujarTexto(); }
}

// Los contadores de la barra salen del contenido: si mañana hay otro artículo,
// el número cambia solo y nunca miente. Música todavía no tiene contenido, así
// que va sin número: un "--" se lee como un error.
{
  const cuantos = { web: CONTENIDO.web.length, video: CONTENIDO.video.length, texto: CONTENIDO.texto.length };
  document.querySelectorAll(".nav-link[data-zone]").forEach((b) => {
    const sup = b.querySelector("sup"), n = cuantos[b.dataset.zone];
    if (sup) sup.textContent = n ? String(n).padStart(2, "0") : "";
  });
}

/**
 * Todo lo que se dibuja adentro de un canvas se pide de una, al arrancar, y la
 * página espera a tenerlo. Del mp4 sólo la cabecera: con eso la ficha ya puede
 * escribir la duración real en vez de inventarla, y el cuerpo del archivo se
 * baja solo mientras tanto.
 */
function precargarContenido() {
  // Los logos, no las capturas: las capturas ya no se dibujan en ningún lado.
  // Siguen generándose porque de ellas sale el color de acento de cada sitio.
  const rutas = [
    ...CONTENIDO.web.map((p) => p.logo),
    ...CONTENIDO.video.map((v) => v.poster),
    ...CONTENIDO.texto.map((t) => t.portada),
  ].filter(Boolean);

  let listas = 0;
  const paso = () => avance("contenido", ++listas / (rutas.length + 1));
  const imagenes = rutas.map((r) => entradaImagen(r).promesa.then(paso));

  const primero = CONTENIDO.video[INDICE.video];
  const cabecera = new Promise((resolver) => {
    if (!primero) return resolver();
    videoEl.poster = primero.poster;
    videoEl.src = primero.archivo;
    videoEl.dataset.archivo = primero.archivo;
    if (videoEl.readyState >= 1) return resolver();
    videoEl.addEventListener("loadedmetadata", resolver, { once: true });
    videoEl.addEventListener("error", resolver, { once: true });
  }).then(paso);

  return Promise.all([...imagenes, cabecera]);
}

function ease(p) { return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }

/**
 * El mismo suavizado exponencial de siempre, pero medido en segundos.
 *
 * Antes cada lerp usaba un factor fijo por cuadro: en una pantalla de 144 Hz
 * los viajes de cámara salían más del doble de rápidos que en una de 60, y en
 * una pestaña en segundo plano no llegaban nunca. Los factores de `CFG` siguen
 * siendo los mismos y a 60 fps el movimiento es idéntico al anterior.
 */
const suave = (k, dt) => 1 - Math.pow(1 - k, dt * 60);

function actualizarSuperficies(t, dt) {
  for (const s of Object.values(superficies)) {
    if (!s?.plano) continue;
    const objetivo = s.objetivo && t >= s.demora ? 1 : 0;
    s.nivel = THREE.MathUtils.lerp(s.nivel, objetivo, suave(objetivo ? .09 : .12, dt));
    const visible = s.nivel > .006 || objetivo > 0;
    s.plano.visible = visible;
    if (!visible) continue;
    const alpha = THREE.MathUtils.smoothstep(s.nivel, 0, 1);
    s.material.opacity = THREE.MathUtils.clamp(alpha, 0, 1);
    s.plano.scale.set(1, 1, 1);
  }
}

function actualizarLibro(dt) {
  const k = suave(.075, dt);
  bookProgreso = THREE.MathUtils.lerp(bookProgreso, bookObjetivo, k);
  if (coverTop) coverTop.rotation.x = THREE.MathUtils.lerp(coverTop.rotation.x, coverObjetivoX, k);
  if (notebookBand) notebookBand.visible = bookProgreso < .035;
  const paginas = THREE.MathUtils.smoothstep(bookProgreso, .27, .72);
  for (const k of ["textLeft", "textRight"]) if (superficies[k]) superficies[k].material.opacity *= paginas;
}

/**
 * La curva del pase: sale y entra en reposo con derivada Y aceleración cero.
 *
 * Es más blanda en las puntas que la de la cámara y más rápida en el medio, que
 * es como se comporta una hoja: cuesta despegarla, vuela por el aire y se posa
 * sin golpe. `ease`, un cúbico, tiene un filo perceptible justo al apoyarse.
 */
const easeHoja = (p) => p * p * p * (p * (p * 6 - 15) + 10);

function actualizarTransicion(dt) {
  if (!transicionItem) return;
  const tr = transicionItem; tr.tiempo += dt; const p = Math.min(1, tr.tiempo / tr.duracion);

  if (tr.zona === "texto") {
    const avance = easeHoja(p);
    // El giro va siempre de 0 a −PI; hacia atrás se recorre al revés.
    const giro = tr.direccion > 0 ? -avance : -(1 - avance);
    pageTurnPivot.rotation.x = giro * ANGULO_LIBRO;

    // Las carillas fijas se ocultan sólo en el tramo donde la hoja está encima
    // de ellas y a punto de quedar coplanar. Muestran exactamente lo mismo que
    // la cara de la hoja que las tapa, así que el cambio no se ve.
    if (p >= 1) {
      INDICE.texto = tr.hacia;
      dibujarTexto();
      pageTurnPivot.visible = false;
      pageTurnPivot.rotation.x = 0;
      transicionItem = null;
    }
    return;
  }

  const claves = tr.zona === "video" ? ["video"] : ["webMain", "webSide"];
  const disolver = Math.abs(p - .5) * 2, piso = tr.zona === "video" ? .18 : .04;
  claves.forEach((k) => { if (superficies[k]) superficies[k].material.opacity *= piso + (1 - piso) * ease(disolver); });
  if (!tr.cambiado && p >= .5) { INDICE[tr.zona] = tr.hacia; actualizarContenido(); tr.cambiado = true; }
  if (p >= 1) transicionItem = null;
}

function bucle() {
  requestAnimationFrame(bucle); const dt = Math.min(.05, reloj.getDelta()), t = reloj.elapsedTime;
  if (!casa || !composer) return;
  // Sin vuelo la cámara está quieta en su destino: no queda ningún lerp que
  // siga acercándose para siempre sin llegar.
  if (vuelo) avanzarVuelo(dt);
  actualizarSuperficies(t, dt); actualizarLibro(dt); actualizarTransicion(dt); avatar?.actualizar(t, dt);

  if (luzProyector) { const nivel = superficies.video?.nivel ?? 0; luzProyector.intensity = CFG.proyector.intensidad * nivel * nivel * proyectorObjetivo; }
  // `mouseSuave` sigue al mouse siempre, también dentro de una sección: así el
  // paneo ya está donde tiene que estar cuando el regreso lo vuelve a encender.
  mouseSuave.lerp(mouse, suave(CFG.paneoSuavidad, dt));
  aplicarPaneoCasa(paneoNivel);
  composer.render();
}
bucle();

window.__sala = {
  zonas: () => [...porZona.keys()], camaras: () => Object.fromEntries([...camarasSeccion].map(([z, r]) => [z, { pos: r.pos.toArray(), quat: r.quat.toArray(), fov: r.fov }])),
  irA: irAZona, casa: irACasa, siguiente: () => cambiarItem(1), anterior: () => cambiarItem(-1),
  estado: () => ({ zonaActiva, indices: { ...INDICE }, proyector: luzProyector?.intensity ?? 0, libro: bookProgreso, transicion: transicionItem?.zona ?? null, video: videoFase }),
  contenido: () => CONTENIDO,
  enlaces: () => [
    ...CONTENIDO.web.map((p) => p.url), ...CONTENIDO.video.map((v) => v.url),
    ...CONTENIDO.texto.map((t) => t.url),
  ],
  reproducir: abrirVideo, cerrarVideo: () => cerrarVideo(false),
  // Para el pendiente del dorso de la hoja que gira (ver `prepararLibro`).
  hoja: () => ({ derecha: hojaDer, izquierda: hojaIzq, pivot: pageTurnPivot }),

  // Dónde cae cada área clicable en la ventana. Sirve para comprobar que un
  // botón dibujado y su hotspot terminaron en el mismo lugar.
  hotspots: () => {
    const lienzoDom = renderer.domElement.getBoundingClientRect();
    return hotspotsActivos().map((o) => {
      const v = o.getWorldPosition(new THREE.Vector3()).project(camera);
      return {
        nombre: o.name, accion: o.userData.uiAction,
        x: Math.round(lienzoDom.left + (v.x * .5 + .5) * lienzoDom.width),
        y: Math.round(lienzoDom.top + (-v.y * .5 + .5) * lienzoDom.height),
      };
    });
  },
  camara: () => ({ pos: camera.position.toArray(), quat: camera.quaternion.toArray(), fov: camera.fov }), exposicion: (v) => { renderer.toneMappingExposure = Number(v); },

  // Banco de pruebas del avatar. Sólo para mirar y medir: la pose y la
  // ubicación viven en `blender/AVATAR_POSE.blend`, no acá.
  av: {
    obj: () => avatar,
    hueso: (nombre) => {
      const h = avatar.huesos.get(nombre); if (!h) return null;
      const p = new THREE.Vector3().setFromMatrixPosition(h.matrixWorld);
      return { x: +p.x.toFixed(3), y: +p.y.toFixed(3), z: +p.z.toFixed(3) };
    },
    caja: () => {
      const b = new THREE.Box3();
      avatar.raiz.traverse((n) => { if (n.isSkinnedMesh) { n.updateMatrixWorld(true); b.expandByObject(n); } });
      return { min: b.min.toArray().map((v) => +v.toFixed(3)), max: b.max.toArray().map((v) => +v.toFixed(3)) };
    },
    // Cámara libre para inspeccionar la cama de cerca.
    ver: (px, py, pz, tx = -0.3, ty = 1.05, tz = 2.6, fov = 45) => {
      proyeccionDeDetalle(); acercado = true;
      const c = new THREE.PerspectiveCamera(fov, CFG.aspectoRef, .05, 200);
      c.position.set(px, py, pz); c.lookAt(tx, ty, tz);
      destino = { pos: c.position.clone(), quat: c.quaternion.clone(), fov, zoom: 1 };
      posActual.copy(c.position); camera.position.copy(c.position); camera.quaternion.copy(c.quaternion);
      camera.fov = fov; camera.updateProjectionMatrix();
    },
    /**
     * Qué está pasando con el velado. Si el avatar no se ve cuando debería,
     * esto dice en una línea si el problema es el estado o el shader: `nivel`
     * es lo que la página cree, `uniforme` lo que de verdad está leyendo el
     * material. Con la habitación abierta los dos tienen que dar 0.
     */
    velo: () => ({
      zona: zonaActiva,
      nivel: avatar?.velo,
      objetivo: avatar?.veloObjetivo,
      demora: +(avatar?.veloDemora ?? 0).toFixed(2),
      uniforme: avatar?.materiales.find((m) => m.userData.luz)?.userData.luz.uVelado.value,
      materiales: avatar?.materiales.length,
    }),

    // Calibrar en vivo, sin recargar, la única constante a ojo del avatar:
    //   escala = de la radiancia que midió Blender al nivel que pide la página
    //   minimo = piso para que nunca quede en negro absoluto
    // El color y la dirección de la luz no se tocan acá: los mide la sonda de
    // cada pose. Ninguno de los dos puede tocar la habitación.
    luz: (escala, minimo) => {
      for (const m of avatar.materiales) {
        const u = m.userData.luz;
        if (!u) continue;
        if (escala !== undefined) u.uEscala.value = escala;
        if (minimo !== undefined) u.uMinimo.value = minimo;
      }
      const u = avatar.materiales.find((m) => m.userData.luz)?.userData.luz;
      return { escala: u?.uEscala.value, minimo: u?.uMinimo.value };
    },
  },
};
