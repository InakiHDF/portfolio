/**
 * EL AVATAR — una pose distinta en cada carga
 * ===========================================
 *
 * Este módulo NO posa ni ubica al avatar. Cada pose la hace Iñaki a mano en
 * `blender/AVATAR_POSE.blend`, que tiene el cuarto entero de referencia, y
 * `tools/avatar.sh` deja un GLB por pose en `modelos/avatar/`. Cada GLB trae
 * la pose Y el lugar adentro, así que acá se agrega tal cual viene, sin una
 * sola transformación.
 *
 * En cada carga se sortea una pose y se baja SOLO ese archivo: tener veinte
 * poses no cuesta nada de descarga.
 *
 * Lo que sí pasa acá, porque no puede estar horneado:
 *
 *   - El pasaje retro de los materiales: fuera el PBR moderno, filtrado
 *     Nearest, la textura pixelada a la vista.
 *   - Las mallas con `_LUZ` en el nombre se vuelven superficie que emite y se
 *     les cuelga una luz. Es la convención para la pantalla del teléfono o
 *     cualquier cosa que ilumine en una pose futura.
 *   - Una práctica tenue sobre el avatar, ubicada a partir de su propia
 *     cadera: así funciona esté donde esté en el cuarto.
 *   - El movimiento: respiración, dedos, deriva de la cabeza. Va sumado
 *     ENCIMA de la pose, así que sirve para cualquier pose. Y si una pose
 *     necesita algo propio, va en `MOVIMIENTO_POR_POSE` y sólo corre en ella.
 */

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const CARPETA = "./modelos/avatar/";
const INDICE = CARPETA + "poses.json";

/**
 * La pantalla del celular: superficie que emite + la luz que tira.
 *
 * Era una linterna. Tres cosas la volvían eso y las tres están acá: color
 * `#a8c4f0` —azul frío contra un cuarto horneado en cálido—, intensidad 1,45
 * con 1,3 m de alcance, y la superficie repintada cada cuadro con `setScalar`,
 * que le borraba el color y la dejaba en gris casi blanco. Ahora el color de la
 * superficie es un dato y el movimiento sólo lo modula.
 *
 * `superficie` va sin tonemap: es el valor que sale a pantalla tal cual. Queda
 * deliberadamente por debajo del umbral de bloom (0,88) para que no haga halo.
 */
const LUZ_EMISOR = {
  color: 0xbcae92,        // la luz que tira: cálida, del lado de la del cuarto
  intensidad: .52,
  alcance: .78,           // un celular alumbra una cara, no medio cuarto
  superficie: 0xa79d88,
};

/**
 * Movimiento propio de una pose, encima del que tienen todas.
 *
 * La clave es el nombre de la pose —el archivo sin `avatar_` ni `.glb`—. Los
 * períodos no son múltiplos de los generales ni entre sí: nunca cicla igual.
 */
const MOVIMIENTO_POR_POSE = {
  /**
   * El pie que quedó levantado sube y baja. El apoyado no se toca.
   *
   * El primer intento no se veía, y medirlo explicó por qué: 0,055 rad de
   * amplitud movían la punta del pie **0,87 cm en total**, y 0,44 rad/s es un
   * ciclo cada 14,3 segundos. Invisible por los dos lados. Con 0,16 rad la
   * punta recorre unos 5 cm —la punta está a 16 cm del tobillo— y el ciclo
   * baja a 2,5 s, que es el ritmo de un pie que se balancea sin pensarlo.
   */
  cama_celular: (t, gira) => {
    const balanceo = Math.sin(t * 2.53);
    gira("RightFoot", balanceo * .16, 0, 0);
    gira("RightToeBase", balanceo * .06, 0, 0);
  },
};

/**
 * Cómo se ilumina el avatar: con la luz REAL del cuarto en el punto donde está.
 *
 * La habitación está horneada en un lightmap, así que cada rincón tiene su
 * brillo y su color, pero nada de eso alcanza a un objeto agregado después.
 * Dos intentos previos fallaron y conviene no repetirlos:
 *
 *   - Un PointLight delante de la cara: en three.js una luz alumbra todo lo
 *     que tiene cerca. Reventaba de blanco las hojas del libro a diez
 *     centímetros y quemaba la mesa y los papeles del escritorio.
 *   - Autoiluminación uniforme inventada: no se derramaba, pero el avatar no
 *     se parecía en nada a lo que tenía al lado. Desentonaba.
 *
 * Ahora `tools/avatar.sh` mide con Blender la iluminación del cuarto en el
 * pecho del avatar, pose por pose, y la resume en 9 coeficientes de armónicos
 * esféricos (`blender/scripts/sonda_luz.py`). El shader evalúa esos
 * coeficientes contra la normal de cada píxel: el avatar recibe el color y la
 * dirección de la luz que de verdad hay ahí. Es el mismo horneado que tienen
 * las paredes, pero para él, y al vivir en su material no puede derramarse.
 *
 * `ESCALA` es el único número a ojo: pasa de la radiancia que mide Blender al
 * nivel que pide la página, que tiene su propia exposición y tono AgX.
 */
// `escala` sale de calibrar contra lo que ya se había aprobado a ojo: con el
// esquema anterior la pose de escritura se veía bien multiplicando la textura
// por ~0,48, y ahí la sonda mide 0,268 de banda 0. De ahí 6,5.
const LUZ = {
  escala: 6.5,
  minimo: .04,        // piso para que nunca quede en negro absoluto
};

/**
 * EL VELADO — cómo se aparta el avatar cuando tapa lo que se está mirando.
 *
 * En la pose de escritura está sentado justo entre la cámara y el cuaderno:
 * medido, los rayos a las esquinas del spread le pasan **8,2 cm por dentro de
 * la cabeza**. Ahí la cámara no se puede correr —la distancia a la que se lee el
 * libro es la que es—, así que el que se aparta es él.
 *
 * No es bajarle la opacidad. Un `opacity` sobre una malla que se solapa consigo
 * misma deja ver por dentro del cuerpo y se ordena mal, y además borra la
 * silueta, que es justo lo que no puede perderse: si desaparece, deja de estar.
 *
 * Es un **disuelto por trama ordenada**: cada píxel se descarta o no según una
 * matriz de Bayer contra el nivel de velado. La malla sigue siendo opaca —no hay
 * mezcla ni orden que resolver— y lo que se ve es una retícula que se abre.
 *
 * Al final **no queda absolutamente nada**: el umbral llega a cero para todos
 * los píxeles. Un intento anterior dejaba un piso de píxeles vivos para que la
 * silueta aguantara, y lo que quedaba era un fantasma sucio encima del libro.
 * El `sesgo` sólo cambia el ORDEN en que se va: cuanto más rasante mira una
 * superficie, más tarda en desaparecer, así que el contorno se apaga último.
 * Está a tono con el resto del avatar, que es de pocos triángulos y Nearest.
 */
const VELO = {
  sesgo: .6,       // cuánto se demora el contorno respecto de las caras planas
  duracion: .7,    // segundos de la transición, medida, no un lerp que nunca llega
};

// Si una pose viene sin sonda medida: gris parejo y tenue. Para una radiancia
// constante L sólo sobrevive la banda 0, y vale L·0,282095·4π.
const SIN_SONDA = [[.28, .28, .28], ...Array.from({ length: 8 }, () => [0, 0, 0])];

const pos = (o) => new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);

/** Saca el PBR moderno y deja la textura pixelada. */
function retro(material) {
  for (const clave of ["normalMap", "metalnessMap", "roughnessMap", "aoMap"])
    if (material[clave]) material[clave] = null;
  material.metalness = 0;
  material.roughness = 1;
  if (material.map) {
    material.map.magFilter = THREE.NearestFilter;
    material.map.minFilter = THREE.NearestFilter;
    material.map.generateMipmaps = false;
    material.map.anisotropy = 1;
    material.map.needsUpdate = true;
  }
  material.needsUpdate = true;
}

export function crearAvatar(scene, alListo) {
  const estado = {
    raiz: null, pose: null, disponibles: [],
    huesos: new Map(), base: new Map(), emisores: [], materiales: [], listo: false,
  };
  const cargador = new GLTFLoader();

  // La página no levanta el telón hasta que el avatar esté puesto: antes se
  // veía la habitación y un segundo después aparecía él. La promesa se cumple
  // también si no hay poses o si el GLB falla — un tropiezo acá no puede dejar
  // la pantalla de carga trabada para siempre.
  let terminar;
  estado.cuandoListo = new Promise((resolver) => { terminar = resolver; });

  function limpiar() {
    if (estado.raiz) scene.remove(estado.raiz);
    estado.raiz = null; estado.listo = false;
    estado.huesos.clear(); estado.base.clear();
    estado.emisores.length = 0; estado.materiales.length = 0;
    // Una pose nueva entra siempre entera. Si no, hereda el velado de la
    // anterior y aparece invisible sin que nadie se lo haya pedido.
    estado.velo = 0; estado.veloObjetivo = 0; estado.veloDemora = 0;
  }

  /**
   * Ilumina al avatar con la sonda de luz de su pose, adentro de su material.
   *
   * `shGetIrradianceAt` ya viene en los shaders de three.js (lo usa LightProbe)
   * y espera exactamente el mismo orden de coeficientes que produce
   * `sonda_luz.py`. Se aprovecha el canal de emisión para que el resultado sea
   * `textura × irradiancia`, o sea el color propio del avatar bajo la luz del
   * lugar, sin agregar una sola luz a la escena.
   */
  function iluminar(sh) {
    const coeficientes = (sh && sh.length === 9 ? sh : SIN_SONDA)
      .map((c) => new THREE.Vector3(c[0], c[1], c[2]));

    for (const m of estado.materiales) {
      // De dónde sale el color propio de la superficie. El cuerpo y la ropa
      // tienen textura; los props modelados a mano —el teléfono, el libro— son
      // color plano. Saltearlos por no tener textura es lo que dejaba el libro
      // en negro absoluto: sin luces de escena, sin emisión no hay nada.
      if (m.map) {
        m.emissive = new THREE.Color(0xffffff);
        m.emissiveMap = m.map;
      } else {
        m.emissive = new THREE.Color().copy(m.color);
        m.emissiveMap = null;
      }
      m.emissiveIntensity = 1;

      const uniformes = {
        uSonda: { value: coeficientes },
        uEscala: { value: LUZ.escala },
        uMinimo: { value: LUZ.minimo },
        uVelado: { value: 0 },
        uSesgo: { value: VELO.sesgo },
      };
      m.userData.luz = uniformes;

      m.onBeforeCompile = (shader) => {
        Object.assign(shader.uniforms, uniformes);

        // La normal en mundo. Después de <skinnormal_vertex> el `objectNormal`
        // ya viene deformado por los huesos, así que sirve para cualquier pose.
        // La posición en mundo sale de `transformed`, que a esa altura ya pasó
        // por el skinning: hace falta para saber hacia dónde está la cámara.
        shader.vertexShader = shader.vertexShader
          .replace("#include <common>", "#include <common>\nvarying vec3 vNormalMundo;\nvarying vec3 vPosMundo;")
          .replace("#include <defaultnormal_vertex>",
            "#include <defaultnormal_vertex>\nvNormalMundo = normalize(mat3(modelMatrix) * objectNormal);")
          .replace("#include <project_vertex>",
            "#include <project_vertex>\nvPosMundo = (modelMatrix * vec4(transformed, 1.0)).xyz;");

        shader.fragmentShader = shader.fragmentShader
          .replace("#include <common>", `
            #include <common>
            varying vec3 vNormalMundo;
            varying vec3 vPosMundo;
            uniform vec3 uSonda[9];
            uniform float uEscala;
            uniform float uMinimo;
            uniform float uVelado;
            uniform float uSesgo;
            // Bayer 8×8 por recursión de la de 2×2. Devuelve un umbral ordenado
            // en 0..1 según la posición del píxel en pantalla.
            float bayer2(vec2 a) { a = floor(a); return fract(a.x / 2.0 + a.y * a.y * 0.75); }
            float bayer4(vec2 a) { return bayer2(0.5 * a) * 0.25 + bayer2(a); }
            float bayer8(vec2 a) { return bayer4(0.5 * a) * 0.25 + bayer2(a); }
          `)
          .replace("#include <clipping_planes_fragment>", `
            #include <clipping_planes_fragment>
            if (uVelado > 0.001) {
              // Velado del todo: no queda un solo píxel. Va como rama propia y
              // no colgado del caso borde de la matriz, que dejaba viva la
              // grilla de píxeles donde Bayer vale exactamente cero.
              if (uVelado > 0.995) discard;
              vec3 haciaCamara = normalize(cameraPosition - vPosMundo);
              float borde = 1.0 - abs(dot(normalize(vNormalMundo), haciaCamara));
              float quedan = clamp((1.0 - uVelado) * (1.0 + uSesgo * borde), 0.0, 1.0);
              if (bayer8(gl_FragCoord.xy) > quedan) discard;
            }
          `)
          .replace("#include <emissivemap_fragment>", `
            #include <emissivemap_fragment>
            vec3 irradiancia = shGetIrradianceAt(normalize(vNormalMundo), uSonda);
            totalEmissiveRadiance *= max(vec3(uMinimo), irradiancia * RECIPROCAL_PI * uEscala);
          `);
      };
      m.needsUpdate = true;
    }
  }

  function montar(gltf, entrada) {
    limpiar();
    const raiz = gltf.scene;
    raiz.name = "AVATAR";
    // Sin position, sin quaternion, sin scale: viene puesto de Blender.

    raiz.traverse((n) => {
      if (n.isBone) estado.huesos.set(n.name, n);
      if (!n.isMesh && !n.isSkinnedMesh) return;
      n.castShadow = true;
      n.receiveShadow = true;
      n.frustumCulled = false;   // la caja del bind pose no cubre una pose acostada
      (Array.isArray(n.material) ? n.material : [n.material]).forEach((m) => {
        retro(m);
        estado.materiales.push(m);
      });
    });

    for (const [nombre, hueso] of estado.huesos) estado.base.set(nombre, hueso.quaternion.clone());

    // Convención `_LUZ`: superficie que emite + luz colgada de ella. El color
    // sale de la constante y no del GLB: así se calibra en un solo lugar.
    raiz.traverse((n) => {
      if (!n.isMesh || !/_LUZ/i.test(n.name)) return;
      n.material = new THREE.MeshBasicMaterial({ color: LUZ_EMISOR.superficie, toneMapped: false });
      const luz = new THREE.PointLight(LUZ_EMISOR.color, 0, LUZ_EMISOR.alcance, 2);
      luz.position.set(0, 0, 0.02);   // por delante de la superficie
      luz.castShadow = false;
      n.add(luz);
      estado.emisores.push({ malla: n, luz, base: new THREE.Color(LUZ_EMISOR.superficie) });
    });

    scene.add(raiz);
    raiz.updateMatrixWorld(true);
    iluminar(entrada.sh);
    aplicarVelado();

    estado.raiz = raiz;
    estado.pose = entrada.archivo.replace(/^avatar_|\.glb$/g, "");
    estado.listo = true;
    console.log(`avatar: pose "${estado.pose}" · ${estado.huesos.size} huesos · `
      + `${estado.emisores.length} emisor(es) · sonda ${entrada.sh ? "medida" : "SIN MEDIR"}`);
    alListo?.(estado);
    terminar(estado);
  }

  // `version` viene de `tools/avatar.sh` y cuelga de la URL del GLB. Sin eso el
  // navegador sirve el modelo viejo de su caché y parece que exportar no hizo
  // nada. El índice se pide sin caché justamente para enterarse de la versión.
  const cargar = (entrada) => cargador.load(`${CARPETA}${entrada.archivo}?v=${estado.version}`,
    (g) => montar(g, entrada),
    undefined, (e) => { console.warn("avatar: no se pudo cargar", entrada.archivo, e); terminar(estado); });

  fetch(INDICE, { cache: "no-store" })
    .then((r) => r.json())
    .then((indice) => {
      // Tolera los formatos viejos: lista pelada, o lista de nombres sueltos.
      const crudo = Array.isArray(indice) ? indice : indice.poses;
      if (!Array.isArray(crudo) || !crudo.length) throw new Error("índice vacío");
      estado.version = Array.isArray(indice) ? 0 : indice.v;
      estado.disponibles = crudo.map((p) => (typeof p === "string" ? { archivo: p, sh: null } : p));
      cargar(estado.disponibles[Math.floor(Math.random() * estado.disponibles.length)]);
    })
    .catch((e) => { console.warn("avatar: no hay poses todavía —", e.message); terminar(estado); });

  /** Fuerza una pose por nombre. Para revisar una en particular. */
  estado.usar = (nombre) => {
    const entrada = estado.disponibles.find(
      (p) => p.archivo === nombre || p.archivo === `avatar_${nombre}.glb`);
    if (!entrada) {
      return console.warn("avatar: no existe la pose", nombre, "—",
        estado.disponibles.map((p) => p.archivo));
    }
    cargar(entrada);
  };

  /**
   * Pide que el avatar se vele o se vuelva a ver. Se puede llamar antes de que
   * la pose esté montada: el nivel se guarda y se aplica cuando exista.
   */
  estado.velo = 0;
  estado.veloObjetivo = 0;
  estado.veloDemora = 0;
  /**
   * `demora` en segundos antes de empezar. Al entrar a una sección la cámara
   * tarda en llegar, y el avatar tiene que seguir entero hasta estar
   * considerablemente más cerca: si empieza en el mismo instante del click, ya
   * está medio ido cuando el viaje recién arranca. Al volver, sin demora.
   */
  estado.velar = (si, demora = 0) => {
    estado.veloObjetivo = si ? 1 : 0;
    estado.veloDemora = demora;
  };

  const suavizar = (x) => x * x * x * (x * (x * 6 - 15) + 10);

  /**
   * El único lugar que escribe el nivel en los materiales.
   *
   * Se llama en cada cuadro Y al montar una pose. Antes sólo corría mientras la
   * rampa se movía, así que si el nivel ya estaba en su destino los materiales
   * nuevos de una pose recién montada se quedaban sin enterarse: el estado
   * decía una cosa y el shader mostraba otra.
   */
  function aplicarVelado() {
    const aplicado = suavizar(estado.velo);
    for (const m of estado.materiales) {
      if (m.userData.luz) m.userData.luz.uVelado.value = aplicado;
    }
  }

  function avanzarVelado(dt) {
    if (estado.velo === estado.veloObjetivo) return;
    if (estado.veloDemora > 0) { estado.veloDemora -= dt; return; }
    const paso = dt / VELO.duracion;
    // La rampa es lineal y la curva se aplica al escribirla: así la transición
    // dura exactamente lo que dice `VELO.duracion` y entra y sale sin filo.
    estado.velo = estado.veloObjetivo > estado.velo
      ? Math.min(estado.veloObjetivo, estado.velo + paso)
      : Math.max(estado.veloObjetivo, estado.velo - paso);
    aplicarVelado();
  }

  const q = new THREE.Quaternion(), e = new THREE.Euler();
  const gira = (nombre, x, y, z) => {
    const hueso = estado.huesos.get(nombre), base = estado.base.get(nombre);
    if (!hueso) return;
    hueso.quaternion.copy(base).multiply(q.setFromEuler(e.set(x, y, z)));
  };

  // Movimiento. Nada de esto es un clip: son sinusoides de períodos que no son
  // múltiplos entre sí, así no cicla nunca igual y no hay que hornear nada.
  // Todo se aplica ENCIMA de la pose que venga del GLB.
  estado.actualizar = (t, dt = 1 / 60) => {
    if (!estado.listo) return;
    avanzarVelado(dt);

    // Respiración: unas 14 por minuto, con la inhalación más corta.
    const ciclo = (t * 0.235) % 1;
    const aire = Math.sin(Math.pow(ciclo, .75) * Math.PI * 2) * .5 + .5;
    const r = (aire - .5) * .024;
    gira("Spine", r * .5, 0, 0);
    gira("Spine1", r, 0, 0);
    gira("Spine2", r * .8, 0, 0);
    gira("LeftShoulder", 0, 0, -r * .9);
    gira("RightShoulder", 0, 0, r * .9);

    // Cabeza: deriva lentísima, tres frecuencias distintas.
    gira("Neck", Math.sin(t * .21) * .013 + aire * .004, Math.sin(t * .13) * .022, Math.sin(t * .17) * .010);

    // Dedos. El pulgar izquierdo scrollea cada tanto; el resto se reacomoda
    // con otro período.
    const scroll = Math.max(0, Math.sin(t * .55) - .82) / .18;
    gira("LeftHandThumb2", 0, 0, -scroll * .42);
    gira("LeftHandThumb3", 0, 0, -scroll * .28);
    ["Index", "Middle", "Ring", "Pinky"].forEach((dedo, i) => {
      const micro = Math.abs(Math.sin(t * (.31 + i * .043) + i * 1.7)) * .03;
      gira(`LeftHand${dedo}2`, 0, 0, -micro);
      gira(`RightHand${dedo}2`, 0, 0, micro * .7);
    });

    // Los emisores: variación fina más algún salto, como cuando cambia lo que
    // está mirando. El nivel MODULA el color propio de la pantalla; ponerlo con
    // `setScalar` era lo que la dejaba en gris casi blanco.
    if (estado.emisores.length) {
      const salto = Math.max(0, Math.sin(t * .37) - .93) / .07;
      const nivel = .84 + Math.sin(t * 2.3) * .04 + Math.sin(t * 5.7) * .02 - salto * .42;
      for (const { malla, luz, base } of estado.emisores) {
        luz.intensity = LUZ_EMISOR.intensidad * nivel;
        malla.material.color.copy(base).multiplyScalar(.64 + nivel * .36);
      }
    }

    MOVIMIENTO_POR_POSE[estado.pose]?.(t, gira);
  };

  return estado;
}
