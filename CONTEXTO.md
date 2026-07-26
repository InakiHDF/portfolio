# Contexto del proyecto — leer antes de tocar nada

Handoff para quien siga. Escrito el 26 de julio de 2026.

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

## 10. Lo primero que haría quien siga

1. **Abrir la página en el navegador** y ver qué sale. Nadie lo hizo todavía.
2. **Cerrar los sectores abiertos** con `close_sector.py`, que hoy están
   expuestos a que un script los borre.
3. Recién ahí, el horneado.
