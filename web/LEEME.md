# La habitación en el navegador

```
web/
├── index.html          ← abrí esto
├── sala.js             ← toda la lógica
├── lib/                ← three.js r169 + addons (no se toca)
├── modelos/
│   └── habitacion.glb  ← exportado desde Blender, 2.6 MB
└── vinilos/
    ├── POOL_*.png      ← 83 tapas, 108 KB en total
    └── pool.json       ← índice que lee la página
```

## Cómo abrirlo

**No sirve hacer doble clic en `index.html`.** El navegador bloquea la carga
de módulos y del GLB desde `file://`. Hay que levantar un servidor local:

```bash
cd web && python3 -m http.server 8000
```

Y después abrir <http://localhost:8000>.

## Qué hace hoy

- Carga el GLB y usa **la cámara `CAM_ISO_SW` que viene adentro**. No hay
  ninguna posición copiada a mano: es la que quedó aprobada en Blender.
- Tone mapping **AgX** con la misma exposición que el render.
- Filtrado **NEAREST sin mipmaps** en todas las texturas.
- Sortea **6 vinilos** de un pool de 83 en cada carga.
- **31 objetos clicables** en 5 zonas. Al hacer clic la cámara viaja y encuadra
  el objeto; se vuelve con el botón, con Escape o con otro clic.
- Bloom para el halo de las lámparas y el haz del proyector.

## Lo que todavía NO coincide con el render

**La luz.** El formato glTF no sabe representar luces de área, y once de las
veinte de la escena lo son: las tiras de led, la pantalla, los monitores, el
relleno y la rasante. Solo viajaron nueve (6 puntuales y 3 focos).

Se arregla horneando la luz en texturas. Cuando eso esté, el navegador no va a
tener ninguna luz encendida: la luz va a estar pintada en la textura y la
imagen va a ser idéntica al render por construcción.

## Ajustar desde la consola del navegador

```js
__sala.camara()          // posición, mira y campo visual actuales
__sala.exposicion(1.6)   // probar otra exposición
__sala.bloom(0.5, .6, .7) // fuerza, radio, umbral
__sala.zonas()           // las zonas que encontró en el GLB
```

## Cómo se conecta con Blender

Las zonas clicables **no están escritas en el javascript**. Se marcan en
Blender con `blender/scripts/tag_zones.py`, que le pone a cada objeto una
propiedad `zona` y `zona_titulo`. El exportador las mete en el GLB como
`userData`, y la página las lee de ahí.

Consecuencia práctica: para agregar o sacar una zona clicable se edita el
diccionario `ZONAS` de ese script y se vuelve a exportar. No se toca la web.

```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
F=$PWD/blender/HABITACION_v013.blend
$B --background $F --python blender/scripts/tag_zones.py -- $F
$B --background $F --python blender/scripts/export_glb.py -- $PWD/web/modelos/habitacion.glb
```
