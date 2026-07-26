# Habitación 3D — archivo base de Blender

```
blender/
├── HABITACION_v008.blend      ← archivo maestro actual. Abrí este.
├── HABITACION_v00N.blend      ← versiones anteriores, no se tocan
├── textures/
│   ├── surface/               ← las 20 texturas generadas por código
│   └── content/               ← imágenes elegidas por Iñaki, ya procesadas
├── renders/                   ← renders de validación de las cámaras
└── scripts/
    ├── lib_blockout.py        ← utilidades compartidas (cajas, materiales)
    ├── generate_blockout.py   ← genera el archivo base desde cero (v001)
    ├── fix_architecture.py    ← retranqueo oeste, baranda, puerta, cama
    ├── fix_west_gap_and_stairs.py ← tapa el hueco oeste, extiende la escalera
    ├── sector_west.py         ← todo lo que ve CAM_LEFT
    ├── sector_north.py        ← todo lo que se apoya en el límite norte
    ├── add_camera_iso.py      ← CAM_ISO_SW, la cámara fija del sitio
    ├── setup_lights.py        ← rig de luces en 40_LIGHTS
    ├── lighting_variants.py   ← renderiza niveles de luz para elegir
    ├── add_bevels.py          ← bisel por objeto, ancho según su tamaño
    ├── refine_organic.py      ← plantas, almohadas y manta (malla propia)
    ├── apply_surface_textures.py ← UVs cúbicas en mundo + materiales
    ├── apply_content_textures.py ← imágenes en cuadros, vinilos y pantallas
    ├── split_materials.py     ← parte materiales sobrecargados
    ├── inventory_textures.py  ← lista los huecos de contenido (docs/HUECOS.md)
    ├── render_iso.py          ← render EEVEE a resolución completa, 8 s
    ├── render_closeup.py      ← un objeto aislado con luz neutra
    ├── close_sector.py        ← marca un sector como aprobado (candado)
    ├── inspect_scene.py       ← vuelca transforms y dimensiones exactas
    ├── audit.py               ← informe del estado de la escena
    └── render_checks.py       ← renderiza las cámaras a baja resolución
```

### Estado de los sectores

| Sector | Contenido | Estado |
|---|---|---|
| `ARCH` | retranqueo oeste, baranda, puerta, cama | cerrado |
| `WEST` | setup, estante, cuadros, plantas, riel | cerrado |
| `ARCH2` | relleno del hueco oeste, escalones 10–14, pared norte | cerrado |
| `NORTH` | pantalla, audio, discos, reja, plantas | cerrado |
| `NORTH2` | paneles negros que faltaban en los dos escalones bajos | cerrado |
| `CENTER` | alfombra, mesa ratona, libros, revistas, joysticks | cerrado |
| `EAST` | mesa de trabajo, silla, planos, lámpara, bolso de la cama | a revisar |
| `EAST2` | cuaderno, taza, lapicera, regla, rollos, tacho, bollos | a revisar |

Con `EAST` cerrado queda terminada la Fase 3–4 del brief: las cuatro paredes y
el centro están blockeados. Lo que sigue es refinamiento geométrico (Fase 5) o
saltar directo a materiales y texturas (Fase 6).

**Cerrado** = todos sus objetos tienen `status: approved` y `clear_sector()` se
niega a borrarlos. Volver a correr el script de un sector cerrado no destruye
nada: aborta.

## Cómo funcionan los sectores

Cada objeto generado por un script lleva una propiedad `sector` (`ARCH`,
`WEST`, …). Al volver a correr el script de un sector se borran **solo** los
objetos con ese sector y se rehacen. Lo que crees o edites vos a mano no lleva
esa propiedad, así que nunca se toca.

La contra: si editás a mano un objeto que generé yo y después vuelvo a correr
ese sector, tu edición se pierde. Por eso, una vez que revisás y corregís un
sector, ese sector queda cerrado y no se regenera.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background blender/HABITACION_v002.blend --python blender/scripts/sector_west.py -- $(pwd)/blender/HABITACION_v002.blend
```

## Qué hay adentro

- Unidades métricas, escala 1.0, resolución 1920×1080.
- Las 10 colecciones del brief, colgando de `SCENE_ROOT`.
- Arquitectura en `10_ARCHITECTURE_LOCKED`: suelo, techo, 4 paredes, zócalos,
  plataforma de entrada con 3 escalones, puerta y una escalera de 10 escalones
  con baranda.
- 4 cámaras en el centro de la habitación, a 1.60 m, 20 mm, separadas 90°.
  Cada una tiene su imagen de referencia cargada como fondo.
- Un solo mueble, `BED_01_ROOT`, como plantilla del patrón ROOT/PROXY.
- 9 materiales de blockout con color plano, visibles en modo Solid.

Medidas interiores actuales: **9.00 × 8.00 × 2.90 m**.

## Convención de ejes

| | dirección | pared | cámara |
|---|---|---|---|
| Sur | −Y | `WALL_SOUTH` (la cama) | `CAM_FRONT` |
| Norte | +Y | `WALL_NORTH` (la escalera) | `CAM_BACK` |
| Este | +X | `WALL_EAST` | `CAM_RIGHT` |
| Oeste | −X | `WALL_WEST` (la puerta) | `CAM_LEFT` |

Los nombres son de plano, no del observador: `CAM_RIGHT` mira hacia la pared
este, no hacia "tu derecha".

## Primeros pasos en Blender

1. Abrí `HABITACION_v001.blend` con doble clic.
2. Para mirar por una cámara: en el Outliner (panel de la derecha) hacé clic
   derecho sobre `CAM_FRONT` → `Set Active Camera`, y después apretá `0` del
   teclado numérico. Si no tenés numpad, arriba a la derecha del visor hay un
   ícono de cámara.
3. La imagen de referencia aparece detrás de la geometría, al 40 % de opacidad.
   Para apagarla: seleccioná la cámara, panel de propiedades (derecha) →
   ícono de cámara verde → `Background Images` → destildá.
4. Para mover un mueble: clic en el objeto `_ROOT` en el Outliner, `G` para
   mover, `R` para rotar, `S` para escalar. Los hijos lo siguen.
5. `Ctrl+S` guarda. Antes de un cambio grande, `File → Save As` y subí el
   número de versión (`v002`, `v003`…).

## Cómo ajustar el tamaño de la habitación

Editá el diccionario `ROOM` al principio de `generate_blockout.py` y volvé a
ejecutarlo. **Ojo: eso borra y rehace el archivo entero.** Hacelo solo antes de
empezar a trabajar a mano, o cambiá `OUT_NAME` para escribir en otra versión.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python blender/scripts/generate_blockout.py
```

## Auditar la escena

Informa colecciones, cámaras, jerarquías, nombres genéricos, escalas sin
aplicar, objetos sin material y mallas densas.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background blender/HABITACION_v001.blend --python blender/scripts/audit.py
```

## Renders de validación

Genera `renders/CHECK_CAM_*.png` con el motor Workbench (colores planos, sin
necesidad de luces). Guardá el .blend antes de correrlo.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background blender/HABITACION_v001.blend --python blender/scripts/render_checks.py
```

Cuando haya iluminación de verdad (Fase 7), correlo con Cycles:

```bash
CHECK_ENGINE=CYCLES /Applications/Blender.app/Contents/MacOS/Blender --background blender/HABITACION_v001.blend --python blender/scripts/render_checks.py
```


## Sistema de texturas

Dos reglas gobiernan todo. Se pueden repetir de memoria y explican cada
decisión concreta:

**1. Téxel de 2.5 cm en el mundo.** Un solo número para toda la habitación.
Medido desde `CAM_ISO_SW` da entre 3.4 y 7.1 píxeles de pantalla por téxel
según la distancia: lo cercano se ve más grueso, que es como se comporta un
juego con texturas en espacio de mundo. La baldosa es de 64 téxeles = 1.60 m.

**2. El téxel tiene que ser más grande que el píxel de pantalla.** Derivar la
resolución para que coincidan da nitidez, que es lo contrario del objetivo.
Para las imágenes de contenido se usan ~5 píxeles de pantalla por téxel: un
vinilo que ocupa 103 px en pantalla lleva una textura de 20×20.

### Calibración de albedo

Las texturas se generan en sRGB pero reemplazan colores planos que estaban en
lineal, y los colores salen de referencias **ya iluminadas**. Sin corregir
eso, la escena perdió 54 % de albedo. `calibrar()` ajusta cada textura para
que su media en lineal dé exactamente el valor del color plano que reemplaza.

### Herramientas

| comando | qué hace |
|---|---|
| `python3 tools/make_textures.py` | genera las 20 texturas + hoja de contacto + test de costuras |
| `python3 tools/process_content.py hoja` | hoja de comparación de niveles retro |
| `python3 tools/process_content.py vinilos` | procesa los 84 vinilos del pool |
| `python3 tools/sample_palette.py` | extrae paletas de las imágenes de referencia |
