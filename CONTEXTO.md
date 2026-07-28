# Contexto del proyecto — leer antes de tocar nada

Handoff para quien siga. Escrito el 26 de julio de 2026.

## −1. La lista de trabajo está en `PEDIDOS.md` — empezar por ahí

El 28/07/2026 Iñaki dejó nueve pedidos de una sola vez, desordenados a
propósito: «vos lo hacés en el mejor orden, y si necesitás, por tandas». Están
todos en **`PEDIDOS.md`**, con el estado de cada uno. Ese archivo manda sobre
cualquier "pendiente" que diga este documento.

Cómo quiere que se trabaje, y lo dijo explícito:

- **Él hace los chequeos visuales, no el agente.** El agente verifica que
  compile y que no haya errores; no se pone a recorrer la página.
- **Por tandas**, y sólo se encadena lo que de verdad depende de un resultado
  anterior. Entre tanda y tanda, esperar su confirmación visual.
- **Dedicación absoluta en cada tarea**, como si fuera la única. Si son muchas y
  no da, se hacen de a una — pero ninguna a medias.
- Textual, sobre el ritmo de las animaciones: «es preferible que la cosa sea
  lenta, con animaciones limpias, que cada cosa llegue a su lugar y nada se
  teletransporte, antes que algo apurado porque sí. **NO HAY APURO. EN NADA.**»

### Tanda 1, hecha y a la espera de su revisión

Pantallas de monitor de un solo gris · luz del celular más tenue y cálida ·
cámaras con curva y 5,9 veces más lentas · UI externa limpiada y sin el copy
cliché · cursor sin lupa y botón de volver más grande · reproductor de video
rehecho · la página no carga hasta estar entera · pie derecho en `cama_celular` ·
**música borrada entera**.

### Tanda 2, abierta

Los tres rediseños grandes: web, video y escritura. Van después porque cada
interfaz se dibuja para la cámara que la mira, y él todavía no aprobó los
encuadres nuevos. El detalle de cada uno está en `PEDIDOS.md`.

### Dos cosas para no volver a tropezar

- **La caché del servidor de desarrollo.** `python3 -m http.server` dejaba al
  navegador con la copia vieja de todo lo que no llevara `?v=`. Se perdieron dos
  vueltas de verificación creyendo que el código no había cambiado. Ahora se usa
  `tools/servidor.py`, que manda `no-store`, y los módulos llevan `?v=NN` en
  tres lugares que se mueven juntos (ver `web/LEEME.md`).
- **`CFG.camara` ya existía** y valía `"CAM_ISO_SW"`. Agregarle una clave nueva
  con ese mismo nombre rompió la carga entera con un mensaje que no tenía nada
  que ver («El modelo no contiene la cámara principal»). Las duraciones de viaje
  viven en `CFG.viajes`.

## 0.0 Actualización vigente — contenido real conectado (28/07/2026)

Esta sección manda sobre cualquier apartado anterior que diga “placeholder”,
“pendiente” o “URL de ejemplo”.

**Se acabaron los placeholders.** Las cuatro zonas muestran contenido real y
los 17 enlaces de la página abren destinos verificados.

- El contenido ya no vive en `sala.js`: está en **`web/contenido.js`**, que lo
  **genera `tools/fetch_contenido.py`**. No editar el módulo a mano. El script
  baja el archivo de Substack, captura los tres sitios con Chrome headless y
  reescribe todo; si una fuente se cae, aborta sin dejar nada a medias.
- Substack real: `inakigongorarosi.substack.com`, 5 artículos con portada.
- Sitios: helicopters.ar, Cru y Opus, con capturas propias en el monitor.
- Video: `Videos/Cru. Launch Film.mov` transcodificado a
  `web/videos/cru-launch.mp4` (35 s, 5,2 MB; el original tenía audio PCM y
  pesaba 52 MB).
- Música dejó de estar pendiente: la pared de vinilos se vuelve el tablero de
  AOTY (`InakiHDF`). Cinco fichas de discos favoritos —tipográficas: **no se
  rehostean tapas ajenas**— más la tarjeta del perfil con un enlace por fila.
- **AOTY está detrás de Cloudflare**, tanto el sitio como el CDN de tapas. No
  se puede scrapear ni bajar imágenes de ahí: sus datos van fijos arriba de
  `fetch_contenido.py` y se actualizan a mano. `curl` recibe 403; un navegador
  entra bien. No confundir eso con un enlace roto.
- El Python de este Mac **no trae certificados raíz**: `urllib` falla en
  cualquier https. Por eso el script descarga con `curl`.

### La transición del video, que era el bug

Antes la vista fullscreen se abría 620 ms después del click, con la cámara
todavía en diagonal a la tela: la imagen saltaba de un escorzo a un rectángulo
recto. Ahora son dos tiempos separados y el reproductor es de verdad:

1. La cámara vuela al **frontal exacto** del proyector mientras el video real
   ya corre sobre la tela como `VideoTexture`. No se abre nada hasta llegar.
2. Recién ahí el reproductor arranca ocupando **exactamente** el rectángulo que
   la tela ocupa en pantalla y crece hasta el cuadro entero.

Es el mismo `<video>` el que pinta la tela y el que se agranda, así que el
cuadro nunca salta. Medido: la cámara llega a `(0.3002, 1.75, −0.7815)` con
quaternion identidad contra una pantalla centrada en `(0.300, 1.750, −2.665)`.

**Ese vuelo tiene duración fija**, no usa el lerp exponencial del resto de la
página: el lerp nunca llega del todo, y acá hay que *saber* que la cámara está
perpendicular antes de abrir. Es la razón de que exista `volarA()`.

### Dos cosas que cambiaron de fondo

- **Todos los suavizados pasaron a medirse en segundos** (`suave(k, dt)`). Antes
  cada lerp usaba un factor fijo por cuadro: en una pantalla de 144 Hz los
  viajes de cámara salían más del doble de rápidos que en una de 60, y en una
  pestaña en segundo plano no llegaban nunca. Los factores de `CFG` no
  cambiaron y a 60 fps el movimiento es idéntico.
- **Los hotspots ya no son números a ojo en metros.** Los rectángulos de los
  botones viven una sola vez en `RECTS`, en píxeles de su canvas, y los comparten
  el dibujo y `hotspotDeCanvas()`. Mover un botón es tocar un número.

### La cámara de música no sale del GLB — leer

Es la única excepción a la regla del apartado 6.1. `CAM_SECTION_MUSICA` es un
plano general del rincón: a esa distancia las fichas no se leen. La página
calcula un frontal a partir de la caja de los seis vinilos. **No es una pose
escrita a mano**: sale de la geometría (centro, normal y tamaño), igual que el
frontal del proyector. Si Iñaki prefiere encuadrarla en Blender, alcanza con
poner `CFG.musicaDesdeGlb = true`.

### Pendiente conocido

Sobre el final del pase de página, cuando la hoja ya quedó apoyada a la
izquierda, su dorso se lee girado 180°. Es anterior a esta tanda y dura una
fracción de segundo. Invertir `pageTurnBackSurface.texture.rotation` **no** lo
corrige —se probó y se revirtió—, así que el error está en otro punto de la
cadena. Queda anotado en el código.

## 0. Actualización — MVP web verificado (27 de julio de 2026)

La página ya fue abierta y probada en navegador, tanto en escritorio como en
móvil. El primer visor cargaba pero quedaba casi completamente blanco: las
luces puntuales del GLB llegaban en candelas (hasta 4.891) y se usaban sin
conversión. `web/sala.js` ahora aplica una escala artística de `0.00115` y una
exposición de `0.78`; no reemplaza el horneado pendiente, pero deja un MVP
visible y utilizable.

La web tiene ahora una interfaz completa inspirada en el lenguaje de
Basement: barra fija negra, acento naranja, escena 3D a pantalla completa,
grano y scanlines, cursor contextual, navegación por las cinco zonas del GLB,
viajes de cámara, paneles de contenido con placeholders, sonido generativo,
carga con progreso y layout móvil. Las 31 zonas clicables se verificaron en
el navegador y no hay errores nuevos en consola.

Los archivos que definen el MVP son `web/index.html` y `web/sala.js`. Los
textos y cantidades del panel son deliberadamente provisorios y viven en el
objeto `ARCHIVO` al principio de `sala.js`.

Corrección de cámara del 27/07: la vista de reposo conserva literalmente la
posición, quaternion, FOV y proporción 1712×945 de `CAM_ISO_SW`. El cuadro
estático fue aprobado por Iñaki como el máximo absoluto. El movimiento usa un
recorte interno de 5 % y desplaza esa ventana según el mouse; nunca mueve
ni rota la cámara y nunca revela nada fuera del cuadro de Blender. En otras
proporciones el canvas usa `cover` antes de aplicar ese mismo margen interno.

Lightmap HQ del 27/07: `HABITACION_v013.blend` sigue intacto. La copia de
trabajo actual es `blender/HABITACION_v017_LIGHTMAP_HQ.blend`; tiene escalas
aplicadas, UV2 `LIGHTMAP` global y un bake difuso directo+indirecto de 2048 px
/ 32 muestras. El atlas limpio está en
`blender/textures/lightmap/room_lightmap_2048.png`, el crudo se conserva como
`room_lightmap_2048_raw.png` y el GLB web es
`web/modelos/habitacion-lightmap-hq.glb`. `LIGHT_SCREEN`, `PROJECTOR_BEAM` y la
emisión de la pantalla fueron excluidos del bake. La web recrea el proyector
con un SpotLight corto entre `PROJECTOR_LENS` y `SCREEN_SURFACE`.

Corrección UV del 27/07: el primer export horneado dejó por error `LIGHTMAP`
como UV de render y rompió todas las texturas implícitas. Ahora UV0 vuelve a
ser el canal activo de cada mesh y el atlas usa exclusivamente UV2. El
exportador repara y valida esa separación antes de generar el GLB. El archivo
actual tiene 90 texturas base en `TEXCOORD_0` y 94 lightmaps en `TEXCOORD_1`.

El esquema actual es híbrido: el atlas conserva luces de área y rebote; las 9
luces puntuales/spot exportables se mantienen a escala `0.0001` para recuperar
reflejos que un bake difuso no contiene. El atlas se transporta como
`occlusionTexture`/`TEXCOORD_1` y `sala.js` lo reasigna a `lightMap`. El bake
crudo se limpia con `tools/denoise_lightmap.py` antes de reexportar. La web usa
AgX con la exposición +0.20 de ISO V12 y lightmap intensity 3.0. La geometría
del cono del proyector se oculta; su SpotLight web permanece activo. Las
texturas artísticas usan `Nearest`, pero el lightmap usa filtrado lineal y
mipmaps: nunca volver a pixelar el atlas de iluminación.

Cámaras de sección del 27/07: están incluidas en la copia actual
`blender/HABITACION_v017_LIGHTMAP_HQ.blend`. En la colección
`50_CAMERAS_SECTION` están `CAM_SECTION_WEB`, `CAM_SECTION_VIDEO`,
`CAM_SECTION_TEXTO`, `CAM_SECTION_MUSICA` y `CAM_SECTION_MI`. La web ya no
calcula acercamientos desde bounding boxes: cualquier objeto de una zona viaja
siempre a la cámara fija de esa zona, interpolando posición, quaternion y FOV
exportados. Los encuadres actuales son puntos de partida para ajuste manual.
No renombrar las cámaras. `SHEET_EAST_01` quedó separada antes del último bake;
las polaroids 01, 03 y 04 volvieron a su composición original y
`PHOTO_NORTH_02`, la central que se superponía, fue eliminada antes de hornear.

---

## 1. Qué es esto

El portfolio personal de Iñaki: **una habitación 3D explorable** que se ve
desde una cámara fija, con objetos clicables que llevan a cada sección
(desarrollos web, videos, escritos, música, sobre mí). No es un sitio
profesional ni comercial — es una galería de lo que hace.

La habitación se construye en **Blender** y se exporta a **GLB** para una
página con **three.js**. Blender es el archivo maestro; la web es el visor.

**Archivo actual: `blender/HABITACION_v013.blend`.** Las versiones anteriores
se conservan sin tocar.

Estado: 394 objetos, 4.008 caras, 91 materiales, 20 luces. Todo texturado.
Todo lo modelable está hecho. Falta hornear la luz y meter el avatar.

---

## 2. Las reglas de la estética — no negociables

Costaron varias vueltas de corrección. Si se rompen, se rompe todo el look.

### La referencia es `basement.studio`, NO PS2

Al principio se apuntó a estética PS2/PSX. **Se descartó.** Iñaki mandó
capturas de `basement.studio` y pidió exactamente eso. Consecuencia concreta:
nada de vertex snapping, nada de texturas afines, nada de cuantizar el
framebuffer a 16 bits, nada de dither sobre el cuadro entero.

Lo que define el look: base casi negra, materiales oscuros, solo luces
prácticas visibles en cuadro, tiras de led dentro de las estanterías,
iluminación horneada, casi monocromo con acentos saturados solo en lo que
emite, y grano.

### Regla del téxel: 2,5 cm en el mundo

Un solo número para toda la habitación. Medido desde la cámara fija da entre
3,4 y 7,1 píxeles de pantalla por téxel según la distancia: lo cercano se ve
más grueso, que es como se comporta un juego con texturas en espacio de
mundo. La baldosa es de 64 téxeles = 1,60 m.

### El téxel tiene que ser MÁS GRANDE que el píxel de pantalla

Éste fue el error más caro. Derivar la resolución para que el téxel coincida
con el píxel de pantalla **garantiza nitidez**, que es lo contrario del
objetivo. Iñaki lo rechazó de plano: *"es que la idea es que pierda el
título"*.

Para las imágenes de contenido se usan **~5 píxeles de pantalla por téxel**.
Un vinilo que ocupa 110 px en pantalla lleva una textura de **32×32 píxeles
reales**. Los pósters van entre 18 y 96 téxeles según su tamaño en cuadro.

### Calibración de albedo — el error que se repitió dos veces

Las texturas se generan en **sRGB** pero reemplazan colores planos que estaban
en **lineal**, y los colores salen de referencias **ya iluminadas**. Sin
corregirlo, la escena perdió **54 % de albedo** de golpe (la madera 84 %).

`calibrar()` en `tools/make_textures.py` ajusta cada textura para que su media
**en lineal** dé exactamente el valor del color plano que reemplaza.

**Este error se cometió dos veces**: primero en las texturas de superficie y
después, idéntico, en el arte de contenido (`make_content_art.py`). Cualquier
generador de textura nuevo tiene que calibrar.

### Sin rotaciones al eje... salvo cuando sí

Iñaki sacó las rotaciones que le puse a los objetos del centro. Pero **sí**
pidió que los papeles del escritorio este estén desalineados. Regla práctica:
muebles y objetos apoyados, alineados al eje; papeles sueltos, rotados.

---

## 3. Cómo está organizado el repo

```
blender/
  HABITACION_v013.blend    ← el archivo maestro actual
  HABITACION_v0NN.blend    ← versiones anteriores, no se tocan
  model-2.glb              ← avatar de Avaturn, sin integrar todavía
  avaturn_ps2_facil.py     ← script de Iñaki para bajarle textura al avatar
  scripts/                 ← 20 scripts de Blender (ver sección 5)
  textures/
    surface/               ← 23 texturas generadas por código
    content/               ← 153 imágenes procesadas + pool de 83 vinilos
  renders/                 ← SALIDA, está en .gitignore, se regenera
tools/                     ← 5 herramientas de imagen en Python puro
web/                       ← la página (ver sección 6)
Sprites/                   ← fuentes que aporta Iñaki: vinilos, pósters, libros
docs/HUECOS.md             ← inventario de los 75 huecos de contenido
docs/huecos.json           ← el mismo inventario, para que lo lean los scripts
refs/                      ← capturas de sitios de referencia
Front/Back/Left/Right/Top.png  ← las referencias de la habitación
_archivo/sala_vieja/       ← primer intento de modelar en la web. Descartado.
```

`_archivo/sala_vieja/` ya está en el historial de git: se puede borrar del
disco sin perderlo.

### Cuidado con git

Existe un **repositorio de git accidental en `/Users/gongorainaki`**, o sea la
carpeta personal entera, sin ningún commit. Antes de que el proyecto tuviera
el suyo, cualquier comando de git corrido acá arriba apuntaba a ése: un
`git add -A` se pone a recorrer toda la carpeta de usuario y no termina más.

El proyecto ahora tiene su propio repo en `Repos/Web/Portfolio`, que al estar
anidado tiene prioridad. Verificar siempre con `git rev-parse --show-toplevel`
antes de commitear.

---

## 4. El sistema de sectores y el candado — LEER

Cada objeto que crea un script lleva una propiedad `sector`. Al volver a
correr el script de un sector, `clear_sector()` borra **solo** los objetos de
ese sector y los rehace. Lo que Iñaki crea o edita a mano no lleva la
propiedad, así que nunca se toca.

**El candado**: los objetos con `status: "approved"` **nunca** se borran. Un
sector se cierra con `close_sector.py` cuando Iñaki lo revisó. Correr el
script de un sector cerrado aborta con un error en vez de destruir su trabajo.

| Sector | Objetos | Estado |
|---|---|---|
| `ARCH` | 11 | cerrado |
| `WEST` | 96 | cerrado |
| `ARCH2` | 8 | cerrado |
| `NORTH` | 70 | cerrado |
| `NORTH2` | 2 | cerrado |
| `CENTER` | 15 | cerrado |
| `CAMS` | 1 | cerrado |
| `EAST` | 33 | **abierto** |
| `EAST2` | 22 | **abierto** |
| `NORTH3` | 27 | **abierto** |
| `PROPS2` | 53 | **abierto** |
| `LIGHTS` | 19 | **abierto** |
| `LIGHTS2` | 1 | **abierto** |
| `BEAM` | 1 | **abierto** |

Los abiertos ya fueron aprobados verbalmente por Iñaki pero no se cerraron con
el script. **Conviene cerrarlos antes de seguir**, porque hoy están expuestos.

---

## 5. Los scripts de Blender

Todos se corren igual:

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
F=$PWD/blender/HABITACION_v013.blend
$B --background $F --python blender/scripts/NOMBRE.py -- $F
```

| Script | Qué hace |
|---|---|
| `lib_blockout.py` | Utilidades compartidas: cajas, materiales, paleta, `clear_sector` con candado |
| `generate_blockout.py` | Genera el archivo base desde cero (solo histórico) |
| `sector_west/north/east/center.py` | Cada pared y el centro |
| `fix_*.py` | Correcciones puntuales de arquitectura |
| `refine_organic.py` | Plantas, almohadas y manta con malla propia |
| `refine_props.py` | Mochila, lámpara de lava, reloj, reja, polaroids, vinilos |
| `add_bevels.py` | Bisel por objeto, ancho calculado según su tamaño |
| `apply_surface_textures.py` | UVs cúbicas en espacio de mundo + materiales |
| `apply_content_textures.py` | Imágenes en cuadros, vinilos, libros y pantallas |
| `setup_lights.py` | Crea las 20 luces ancladas a objetos de la escena |
| `tune_lighting.py` | Ajusta ambiente y potencias sin mover nada |
| `tune_depth_and_glow.py` | Oclusión, luz rasante, brillo de pantalla |
| `add_projector_beam.py` | Haz del proyector y niebla de escena |
| `tag_zones.py` | Marca los objetos clicables |
| `export_glb.py` | Exporta a `web/modelos/habitacion.glb` |
| `inventory_textures.py` | Genera `docs/HUECOS.md` y `docs/huecos.json` |
| `audit.py`, `inspect_scene.py` | Diagnóstico |
| `render_iso.py` | Render EEVEE a resolución completa, ~15 s |
| `render_closeup.py` | Un objeto aislado con luz neutra, para juzgar forma |
| `close_sector.py` | Marca un sector como aprobado |

Y en `tools/` (Python puro, sin Blender):

| Herramienta | Qué hace |
|---|---|
| `make_textures.py` | Las 23 texturas de superficie + test de costuras |
| `make_content_art.py` | Lomos, polaroids, consolas, hojas escritas |
| `process_content.py` | Procesa las imágenes de Iñaki (vinilos, pósters, libros) |
| `normalize_books.py` | Recorta y normaliza las tapas de libros |
| `sample_palette.py` | Extrae paletas de las imágenes de referencia |

---

## 6. La web

```
web/  index.html · sala.js · lib/ (three.js r169) · modelos/ · vinilos/
```

Se levanta con `cd web && python3 -m http.server 8000`. Con doble clic no
funciona: el navegador bloquea los módulos desde `file://`.

**Tres decisiones de diseño que hay que respetar:**

1. **La cámara sale del GLB.** No hay ninguna posición copiada al javascript.
   La página busca `CAM_ISO_SW` adentro del archivo.
2. **Las zonas clicables salen del GLB.** `tag_zones.py` le pone a 31 objetos
   una propiedad `zona`, que viaja como `userData`. Para cambiar las zonas se
   edita ese script y se reexporta; la web no se toca.
3. **Los encuadres se calculan.** Al hacer clic, la página mide el objeto y
   calcula desde dónde mirarlo. No hay tabla de posiciones que mantener.

**IMPORTANTE: nadie abrió todavía esta página en un navegador.** Está
verificada la sintaxis, la validez del GLB y que todo se sirve por HTTP, pero
no se vio renderizar. Es lo primero que hay que hacer.

---

## 7. Lo que falta

### 7.1 Hornear la luz — el paso grande

**El problema**: el formato glTF no sabe representar luces de área, y **once
de las veinte** de la escena lo son (tiras de led, pantalla, monitores,
relleno, rasante). Solo viajan nueve. Por eso hoy la web no puede coincidir
con el render.

**La solución acordada con Iñaki**: hornear toda la luz en texturas. Después
el navegador no tiene ninguna luz encendida — la luz está pintada en la
textura y la imagen es idéntica al render **por construcción**.

Pasos: desplegar un segundo juego de UVs sin solapamiento en cada malla (todas
tienen ya UVs de textura, falta el de lightmap), hornear con Cycles a un
atlas, exportar, y en three.js usar `MeshBasicMaterial` × lightmap.

Lo que no se puede hornear: lo que se mueva. El avatar, la tapa del cuaderno
al abrirse, las agujas del reloj.

### 7.2 El avatar

`blender/model-2.glb`, de Avaturn. Medido:

| | habitación | avatar |
|---|---|---|
| Caras | 4.008 | **29.203** |
| Texturas | 23, de 64 px | 13, de **1024 px** |
| Rig | — | 52 huesos, **0 animaciones** |

Tiene siete veces más geometría que toda la habitación y texturas dieciséis
veces más finas que la regla del proyecto. Hay que **decimarlo a ~4.000 caras**
y bajar las texturas a **128 px con filtrado Closest** — ése es el número que
sale de la regla del téxel. Iñaki probó con 80 y le quedó raro: no era el
número, era que sin filtrado Closest la textura se derrite.

Está riggeado, así que las actividades van como **clips de animación**. El
archivo trae cero: hay que posarlo y crear una acción por actividad (acostado
mirando el teléfono, sentado leyendo, en la computadora, escribiendo).

Decisión tomada: el cuarto se hornea una vez; el avatar lleva **su propio
horneado por pose** más una sombra blanda en el piso. No va a proyectar sombra
real sobre el cuarto.

### 7.3 Lo que ya está resuelto y solo falta conectar

- **Vinilos al azar**: el pool de 83 está procesado en `web/vinilos/` y la
  página ya sortea 6 en cada carga.
- **Atmósfera**: Iñaki eligió "haz + halo". El haz del proyector es geometría
  y ya viaja en el GLB; el halo es el bloom que ya está en la página. La
  niebla de escena de Blender **no se exporta** — es un efecto de motor.

---

## 8. Bugs y trampas — el patrón que se repitió tres veces

**Un script que reemplaza algo NO puede sacar su posición de lo que va a
borrar.** Pasó tres veces con síntomas distintos:

1. `fix_north_details.py` deducía la posición de los cubos de las pilas que él
   mismo había reemplazado. Al reejecutarlo **desaparecieron los 21 libros**.
   Arreglado: ahora se apoya en los divisores de la estantería, que son
   permanentes.
2. `refine_props.py` hacía lo mismo con el reloj, la reja, la lava y el
   cuaderno. Arreglado con un sistema de **anclas**: las posiciones se
   calculan y se guardan en propiedades de la escena **antes** de borrar nada
   (`ancla_reloj`, `ancla_reja`, `ancla_lava`, `ancla_cuaderno`, `ancla_mochila`).
3. `enrich_table_east.py` leía su propio resultado de la corrida anterior como
   si fueran ediciones manuales de Iñaki, y salteaba todo.

**Regla: todo script tiene que ser idempotente y hay que probarlo corriéndolo
dos veces seguidas.**

Otras trampas concretas:

- **Cambiar el color de un material no sirve si tiene textura**: la textura
  pisa el Base Color. Pasó con la puerta verde. Hay que cambiar el color en el
  generador de la textura.
- **Una luz adentro de una malla cerrada no ilumina nada**: la malla le atrapa
  la luz. Pasó con la lámpara de lava, que se veía encendida sin iluminar.
  Se resuelve con `visible_shadow = False` en la geometría de la práctica.
- **El texel de una textura tileable tiene que dividir el lado de la baldosa.**
  Si no, hay costura al repetir. `make_textures.py` tiene un test que lo
  comprueba solo.
- **La cara visible de un objeto no es siempre la más grande**: en un libro
  parado es el lomo. Y un libro acostado muestra la tapa. `cara_visible()` en
  `apply_content_textures.py` decide primero el eje según la forma y recién
  después el signo con la cámara.
- **La cámara del GLB viene anidada**: el exportador mete un nodo raíz con
  rotación para pasar de Z-arriba a Y-arriba. Hay que sacarla a espacio de
  mundo antes de moverla.

**Deuda menor**: hay 10 objetos con la escala sin aplicar (plataforma de
entrada, alfombra, mesa del centro, monitor). Son ediciones manuales de Iñaki.
Conviene aplicarlas con `Ctrl+A → Scale` antes de hornear, porque las UVs de
lightmap salen deformadas si no.

---

## 9. Cómo trabajar con Iñaki

Tiene criterio visual muy formado y sabe lo que quiere. Vale la pena leer esto
antes de proponerle nada.

- **Mostrar evidencia, no describir.** Renderizar y mandarle la imagen. Cuando
  hay una decisión abierta, mandarle 3 o 4 variantes y que elija él. Es el
  director creativo; el rol del agente es ejecutar con precisión, no
  reinterpretar.
- **Nada de humo.** Tono directo, sin vender las propias ideas, sin adjetivos
  de más. Si algo salió mal, decirlo con el número.
- **Medir antes de opinar.** Varias veces la causa real no era la que parecía:
  la escena no estaba oscura por falta de luz sino por albedo mal calibrado;
  la lava no alumbraba porque la luz estaba atrapada, no por potencia.
- **No tomar atajos.** Lo pidió explícitamente. Prefiere que se haga bien y
  por partes antes que rápido y a medias.
- **Trabajar por tandas y esperar revisión.** Él revisa, ajusta a mano en
  Blender y devuelve el archivo. Hay que respetar sus ediciones: por eso
  existen los sectores, el candado y las anclas.
- **Prohibido**: el copy de aforismos, las antítesis del tipo "no es X, es Y",
  y decidir por él en cuestiones de diseño.

Iñaki no domina Blender. Cuando hay que pedirle que haga algo a mano, van
pasos numerados, con el atajo y qué debería ver después de cada paso.

---

## 11. Actualización vigente — interfaz dentro del mundo (27/07/2026)

Esta sección reemplaza el estado antiguo de los apartados 6, 7 y 10 cuando se
contradigan.

- La luz HQ ya fue horneada y aprobada. La fuente estable es
  `HABITACION_v017_LIGHTMAP_HQ.blend` y el atlas es
  `textures/lightmap/room_lightmap_2048.png`.
- La web actual carga `web/modelos/habitacion-world-ui.glb`.
- `HABITACION_v018_WORLD_UI.blend` es una copia de v017 que sólo acerca
  `CAM_SECTION_TEXTO` al cuaderno: 0,70 m, lente 36 mm. No hubo rebake.
- La UI Basement fue retirada: nueva navegación flotante, acento menta, sin
  panel lateral y sin “Sobre mí”.
- Films funciona en la pantalla del proyector; Web en ambos monitores; Essays
  abre el cuaderno y usa páginas dinámicas. Son texturas Canvas de Three y no
  alteran el lightmap. Music queda conscientemente pendiente.
- El proyector está apagado en Home y se enciende al entrar a Films.
- El cuaderno anima `NOTEBOOK_EAST_COVER_TOP`, oculta la banda y muestra dos
  páginas más una guarda editorial en la cara interior. Al volver se restaura.
- Los placeholders viven en `CONTENIDO`, al comienzo de `web/sala.js`.
- Verificación real en navegador completada: carga, cuatro cámaras, pantalla,
  monitores, apertura/cierre, cambio por flechas y retorno a Home. Cero errores
  de consola.
- Próximo trabajo recomendado: revisión visual de Iñaki; después retocar sólo
  las cámaras que él marque y conectar contenido/URLs reales.

### Refinamiento retro posterior (descartado; sólo histórico)

Esta actualización reemplaza la identidad menta mencionada arriba:

- La UI de cards/pills fue descartada. `index.html` usa una identidad inspirada
  en interfaces de videojuegos 2000/PS2: ángulos rectos, cortes diagonales,
  azul/rosa cromático, tipografía mono/condensada y scanlines.
- Fuente de esa iteración: `HABITACION_v019_RETRO_UI.blend`; GLB de esa iteración:
  `web/modelos/habitacion-retro-ui.glb`.
- Video 36 mm y Web 34 mm: ahora las superficies ocupan el encuadre y se leen.
- Texto 40 mm casi cenital, centrado en un libro abierto de dos anchos.
- La tapa gira desde un pivot runtime en el lomo izquierdo. La página izquierda
  acompaña la tapa y una hoja adicional anima el paso de página.
- Proyector y monitores tienen rampas de encendido/apagado. Los cambios de
  video/proyecto colapsan la señal antes de reemplazar contenido.
- Hover específico por acción; click fuera de la superficie activa vuelve al
  cuarto.
- Validación visual completa realizada sin errores de consola.

---

## 10. Lo primero que haría quien siga

1. **Abrir la página en el navegador** y ver qué sale. Nadie lo hizo todavía.
2. **Cerrar los sectores abiertos** con `close_sector.py`, que hoy están
   expuestos a que un script los borre.
3. Recién ahí, el horneado.

---

## 12. Actualización vigente — UI física sobria / v020 (27/07/2026)

Esta sección reemplaza por completo el “Refinamiento retro posterior” de la
sección 11 y también el apartado 10 cuando se contradigan.

- Se descartó la asociación PS2 = neón/glitch/arcade. La identidad actual es
  una interfaz de archivo/consola de comienzos de los 2000: carbón, papel,
  naranja apagado, azul grisáceo, bordes rectos y tipografía utilitaria.
- La barra superior es sólida, mide 58 px y queda fuera del render; nunca tapa
  información de la habitación.
- Fuente de cámaras: `blender/HABITACION_v020_CONSOLE_UI.blend`. GLB servido:
  `web/modelos/habitacion-console-ui.glb`. Ambos parten del lightmap HQ
  aprobado y no cambian geometría ni iluminación.
- `CAM_SECTION_WEB` fue elevada para liberar el contenido de la silla. Video
  conserva el plano útil de la pantalla. Texto mira el cuaderno desde el lado
  de la silla y lo presenta vertical, en su eje natural de lectura.
- Web ya no usa planos flotantes: las dos CanvasTexture quedan insetadas dentro
  de los biseles. El monitor principal imita una ventana web de época y el
  secundario funciona como índice/selector.
- Video es una proyección sobre tela con lógica de tira/contact sheet. No tiene
  boot de monitor. La luz y la imagen aparecen/desaparecen por una rampa suave.
  “Ver video” mueve primero la cámara hacia la tela y luego abre una vista de
  video a pantalla completa.
- El cuaderno recuperó su bisagra superior original. La tapa abre como estaba
  modelada; la página izquierda vive en su cara interior y la derecha en el
  cuerpo. El contenido está rotado para leerse desde la silla.
- El pase de página es una hoja opaca con contenido real en ambas caras,
  gira sobre la bisagra física, cambia el spread a mitad del recorrido y usa
  polygon offset para no recortarse contra la página inferior.
- Dentro de las secciones no hay tooltip en el mouse. Sólo hay cursor y botones
  visibles con hotspots ajustados a sus límites. Click fuera vuelve a Home.
  El tooltip contextual existe únicamente en Home.
- Verificación visual real realizada en navegador para Home, Video, transición
  a fullscreen, Web, Texto, botones del libro y pase de página. `node --check`
  y `git diff --check` pasan.

Próximo paso recomendado: revisión visual de Iñaki sobre esta tanda. Música y
URLs/contenido definitivos siguen conscientemente pendientes.

---

## 13. El avatar (27/07/2026)

Reemplaza el apartado 7.2. **Las poses las hace Iñaki a mano, no un script.**
El objetivo es que en cada carga de la página el avatar aparezca en otro lado
haciendo otra cosa, sorteado.

### El circuito

```
blender/AVATAR_POSE.blend      ← Iñaki posa y ubica acá, una Action por pose
        │  tools/avatar.sh
        ▼
web/modelos/avatar/*.glb       ← un GLB por pose, con pose y lugar adentro
        │  + poses.json
        ▼
web/avatar.js                  ← sortea una, materiales retro, luz, movimiento
```

`AVATAR_POSE.blend` lo genera `blender/scripts/avatar_pose_file.py` a partir de
`HABITACION_v020_CONSOLE_UI.blend` + `model-2.glb`. Trae el avatar **sin tocar**
(29.123 caras, texturas de 1024 px) y la habitación entera como referencia, en
la colección `REFERENCIA` y bloqueada con `hide_select`. Las coordenadas son las
mismas que las del archivo maestro: donde quede ahí queda en la página.

**El .blend tiene siempre UNA pose: la que se está editando.** Las terminadas
viven como JSON en `blender/poses/<nombre>.json` — dónde está parado el avatar,
la rotación de cada hueso y la transformación y visibilidad de lo que lo
acompaña. `tools/pose.sh guardar <nombre>` las saca del .blend sin tocarlo;
`tools/pose.sh abrir <nombre>` las devuelve.

**Nada de Actions.** Se probó y salió mal: una Action con fotogramas clavados le
pisa la pose viva cada vez que Blender recalcula la animación, y cambiar de modo
con `Tab` la recalcula. Borró una pose entera de trabajo a mano. Un JSON no se
ejecuta ni recalcula. `tools/arreglar_blend.sh` le saca la Action a un archivo
que todavía la tenga, sin tocar la pose.

Regla de exportación: sale todo lo que **no** esté en `REFERENCIA`, salvo lo
marcado como no visible en la pose. Un objeto que sobra en una pose se oculta
antes de guardarla; no hace falta borrarlo.

Y una convención de nombres: cualquier malla con `_LUZ` en el nombre la página
la convierte en superficie que emite y le cuelga un `PointLight`. Así está
hecha la pantalla del teléfono (`TELEFONO_PANTALLA_LUZ`).

La página baja **un solo GLB por visita**, el sorteado: tener veinte poses no
la hace más lenta, sólo ocupa más disco. `poses.json` lleva una versión con la
hora de la corrida, colgada de la URL del GLB: sin eso el navegador sigue
sirviendo el modelo viejo de su caché y parece que exportar no hizo nada. Para
revisar una pose en particular desde la consola:
`__sala.av.obj().usar("cama_celular")`.

**Volver a correr `avatar_pose_file.py` reconstruye el .blend desde cero.** Los
JSON de `blender/poses/` sobreviven; la pose que estaba en el .blend sin
guardar, no.

### Lo que se aprendió, para no repetirlo

- **El estilo del avatar es low-poly retro deliberado**, tipo Fears to Fathom:
  manos como mitones, cara de pocos triángulos, textura pixelada a la vista. La
  lectura de "personaje suave y oscuro que se integra por la luz" es incorrecta.
- **Decimar con Blender destruye las siluetas.** Las zapatillas al 5 % quedaron
  hechas trizas. Se usa `gltf-transform simplify` (meshoptimizer) con
  `--lock-border`, que respeta costuras de UV y bordes abiertos: de 29.123 a
  12.621 triángulos sin romper nada.
- **Primero posar, después decimar.** Al revés se posa sobre una malla rota.
- **`export_rest_position_armature=False`** es obligatorio al exportar. En su
  valor por defecto (True) el exportador escribe la postura de reposo y el
  avatar llega a la página en T, con la pose perdida entera.
- **El importador de glTF revienta dentro de los .blend horneados**: el grupo
  `glTF Material Output` que dejó el bake tiene un solo socket y el importador
  lo toma por suyo. Hay que renombrarlo durante la importación y devolverlo
  después (el exportador lo busca por ese nombre).
- **Lo que apoya en la cama es la pelvis, no el abrigo.** Medir el punto más
  bajo de la ropa deja el cuerpo flotando 12 cm, porque la capucha queda
  tendida bajo los hombros.
- **Posar por rotaciones numéricas a ciegas no funciona.** Se intentó y salió un
  maniquí. Para los brazos, si hay que hacerlo por código, va IK de dos huesos
  (dónde va la mano + hacia dónde cae el codo), no rotaciones de hombro y codo.

### Lo que hace la página y no puede estar horneado

`web/avatar.js` agrega el avatar **sin una sola transformación** y se ocupa de:
materiales retro (fuera normal/metal, filtrado Nearest), las mallas `_LUZ` como
`PointLight` de alcance corto —la única luz que llega a ese rincón de la cama—,
una práctica tenue ubicada **a partir de la cadera del propio avatar**, para que
funcione esté donde esté en el cuarto, y el movimiento: respiración de ~14 por
minuto, deriva de cabeza y dedos, todo con sinusoides de períodos no múltiplos
para que no cicle nunca igual. Se suma **encima** de la pose que venga del GLB,
así que sigue funcionando con cualquier pose que él haga.
