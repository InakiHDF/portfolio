# La habitación en el navegador

## Abrir localmente

```bash
python3 tools/servidor.py 8000 web
```

Después abrir <http://localhost:8000>. No funciona desde `file://`.

Es `http.server` mandando `no-store`. Sin eso el navegador se queda con la copia
vieja de todo lo que no lleve `?v=` colgado —`index.html`, el GLB, las
texturas— y parece que editar un archivo no hizo nada. Los módulos igual llevan
`?v=NN`: está en `index.html` para `sala.js` y en los dos `import` de arriba de
`sala.js` para `avatar.js` y `contenido.js`. **Los tres números se mueven
juntos**; una entrada ya guardada en la caché sobrevive al `no-store`.

## Versión actual

- HTML/UI: `web/index.html`
- Runtime Three: `web/sala.js`
- Fuente Blender: `blender/HABITACION_v020_CONSOLE_UI.blend`
- GLB: `web/modelos/habitacion-console-ui.glb`
- Lightmap aprobado: `blender/textures/lightmap/room_lightmap_2048.png`

`v020` parte directamente de `HABITACION_v017_LIGHTMAP_HQ.blend`. Sólo cambia
las cámaras de sección; no mueve geometría, no cambia iluminación ni rebakea.

## Identidad

La UI anterior de cards, neón, glitch y estética arcade fue eliminada. La capa
actual usa una identidad de archivo/consola de comienzos de los 2000: carbón,
papel, naranja apagado, azul grisáceo, tipografía utilitaria y ángulos rectos.
La navegación es una barra sólida de 58 px fuera del render.

La barra tiene el nombre a la izquierda —que además es el control de
"habitación"— y las cuatro secciones a continuación. Antes había un recuadro con
el nombre **y** un enlace "Habitación" al lado: dos controles para lo mismo, que
era justamente lo que no se entendía. `AUDIO: OFF` y `CONTACTO` fueron
eliminados, y con ellos el zumbido generativo que colgaba del primero.

**Prohibido el copy de palabras clave** separadas por barras —el
`PORTFOLIO / MENDOZA / 2026` que estaba arriba del título— en cualquier parte de
la página. Es una orden de Iñaki, no una preferencia.

El título grande de abajo a la izquierda dice **La habitación**, con el subtítulo
*El portfolio de Iñaki Góngora*. Es lo que quedó más cerca de convencerlo; sigue
sin estar cerrado.

## Las pantallas de los monitores

Los dos paneles comparten material (`MAT_BLOCKOUT_SCREEN`) y albedo
(`TEX_SCREEN`, plano y oscuro), pero el bake les dejó dos iluminaciones muy
distintas. Promediando el atlas sobre el UV2 de cada uno:

| Panel | Media del lightmap |
|---|---|
| `MONITOR_MAIN_PANEL` | (6, 4, 2) |
| `MONITOR_SIDE_PANEL` | (59, 41, 23) |

Diez veces más claro y encima cálido: por eso uno se leía gris oscuro y el otro
gris claro. Una pantalla apagada no tiene por qué recibir el rebote del cuarto,
así que `aplanarPantallas()` les pone a los dos un lightmap plano de 1×1 con el
valor del panel principal. **El atlas no se toca y no hay rebake**; se comprobó
que ningún otro objeto usa ese material.

## Cámaras

- `CAM_SECTION_VIDEO`: posición segura original, lente 36 mm, objetivo en la
  pantalla completa.
- `CAM_SECTION_WEB`: **ya no se usa.** Ver la sección Web más abajo: los dos
  encuadres se calculan sobre cada monitor.
- `CAM_SECTION_TEXTO`: lente 42 mm, desde el lado de la silla; el spread queda
  vertical y en su eje normal de lectura.
- `CAM_SECTION_MUSICA`: el plano general del rincón, tal como sale del GLB.

Video y Texto salen del GLB; Música también. Los encuadres calculados salen de
la geometría de su superficie —centro, normal y tamaño— con `encuadreFrontal()`,
que además acepta `azimut` y `elevacion` para girar alrededor de esa superficie
sin dejar de mirarla al centro. Si el objeto se mueve, el encuadre lo sigue.

### Cómo se mueve la cámara

Todo viaje tiene duración y curva; no queda un solo lerp exponencial. El lerp
ponía la velocidad máxima en el primer cuadro —de ahí el arranque brusco— y
además nunca llegaba del todo al destino, sólo se le acercaba.

| | pico de velocidad | |
|---|---|---|
| lerp exponencial viejo | 3,713 × distancia/s | en el primer cuadro |
| `easeCamara`, 2,4 s | 0,625 × distancia/s | en la mitad del viaje |

`easeCamara` no es la misma `ease` que usan los cambios de contenido: aquélla es
un cúbico con pico 3,0 y ésta queda en 1,5, el más bajo posible para una curva
que sale y entra en reposo. Las duraciones están en `CFG.viajes`.

### El paneo, y el tirón que había al empezar y terminar un viaje

En Home la cámara **no se mueve nunca**: lo que se mueve es una ventana recortada
dentro del cuadro fijo de Blender, según el mouse. Eso se hacía con un
`setViewOffset` que se prendía y se apagaba de golpe — `clearViewOffset()` en el
mismo cuadro del click al entrar a una sección, y el paneo reactivándose en el
primer cuadro del regreso con `mouseSuave` donde hubiera quedado. Un salto de
hasta 2,4 % del cuadro justo antes de que arrancara la animación: se leía como
que la cámara se reacomodaba y recién ahí empezaba el viaje.

Ahora el paneo es una intensidad que **viaja dentro del vuelo** (`paneo0` →
`paneo1`) y se apaga y enciende con la misma curva de la cámara. En intensidad 0
el recorte vale 1 y la ventana es el cuadro entero, o sea exactamente lo mismo
que no tener offset, pero sin discontinuidad. No se deduce del estado porque el
vuelo al frontal del proyector también ocurre con la sección abierta, y ahí el
paneo no tiene que moverse.

## Interfaces dentro del mundo

### Video

**La ficha.** El poster ocupa la tela entera, con un degradado abajo para que el
texto se lea sobre cualquier imagen, el título en 64 px y el botón de reproducir.
El diseño anterior era una hoja de papel claro con el poster metido en un
recuadro chico y una **tira vertical de 190 px** a la izquierda: ahí no entraba
un título, así que quedaba sólo el número del video en 13 px, ilegible. Ahora la
tira, cuando haga falta, es horizontal y va abajo — 284 px de ancho por ficha,
con el título en tres líneas de 21 px. Con un solo video no hay tira.

En la tira va **sólo el título**. Ni tipo ni año: no hacen falta para elegir.

**La miniatura la elige Iñaki.** Es el campo `poster` de `VIDEOS`, arriba de
`tools/fetch_contenido.py`: cualquier PNG o JPG dentro de `web/videos/`. El
script verifica que el archivo exista y aborta si no — una miniatura rota deja la
tela con un marco vacío y nadie se entera hasta abrir la página.

**La cámara.** `CAM_SECTION_VIDEO` miraba la tela demasiado de costado. La página
la corre hacia el frontal exacto sin llegar del todo: `CFG.encuadreVideo.
frontalidad`, hoy 0,72. Medido, la sección quedó a **13,4°** de la perpendicular
y a 0,61 m del frontal. La posición se interpola pero la orientación **no**: se
vuelve a apuntar al centro de la tela, porque interpolar las dos rotaciones por
separado deja encuadres intermedios donde la tela se va del centro.

#### El reproductor, y por qué ya no hay `VideoTexture`

La versión anterior ponía el video corriendo sobre la tela y después montaba el
reproductor encima, calzado al milímetro sobre el mismo rectángulo, para que no
se notara el relevo. **Se notaba igual, y no por las medidas.** La tela la dibuja
el `EffectComposer` —tono AgX, exposición, bloom, y el grano encima del canvas—
mientras que el `<video>` del DOM sale crudo: son dos imágenes distintas del
mismo cuadro. Por más que los rectángulos coincidieran, el relevo era un salto de
color y de textura. Calzarlos mejor no podía arreglarlo nunca.

Ahora **nadie se releva**. La tela muestra siempre su ficha dibujada, y el
reproductor aparece por encima con un disolvido: la diferencia entre las dos
imágenes pasa a ser el efecto en vez del error. Cuatro tiempos:

1. **Acercando** (2 s). La cámara viaja al frontal exacto del proyector.
2. **Fundiendo** (0,42 s). El reproductor aparece **quieto**, exactamente sobre
   el rectángulo de la tela, disolviéndose sobre ella.
3. **Creciendo** (0,95 s). Ya visible y sin cambiar de imagen, crece hasta el
   cuadro entero. Con la cámara perpendicular es un puro cambio de escala.
4. **Pleno.** Todo quieto y en su lugar: recién ahora empieza el video.

Al cerrar, el camino exacto al revés: encoge hasta la tela y ahí se disuelve.
Como la tela nunca cambió de imagen, al desaparecer el cuadro ya está debajo lo
que tiene que quedar.

Los controles son propios, no los nativos: play/pausa, barra de posición con
arrastre, tiempo, audio y pantalla completa. **Se van solos a los 2 s** sin
actividad y vuelven al mover el mouse; en pausa se quedan puestos, porque ahí el
que mira está decidiendo algo. Teclas: espacio o `k` play/pausa, flechas ±5 s,
`m` audio, `Esc` cierra. Un click mientras se abre cancela y vuelve.

Sólo despiertan la barra los eventos que son **una decisión de quien mira**:
mover el mouse, una tecla, play y pausa. Nunca `timeupdate`, que llega unas
cuatro veces por segundo mientras el video corre: cuando despertaba también con
eso, el temporizador de ocio se reiniciaba siempre y la barra no se escondía
jamás.

**Hoy hay una segunda ficha de relleno** —«Video de prueba, para ver la tira»—
apuntando al mismo mp4, sólo para poder ver la tira de selección, que con un
único video no existe. Está marcada como provisoria arriba de
`tools/fetch_contenido.py`: se borra esa entrada y se vuelve a correr el script.

### Web

**Un monitor por vista, cada uno con su cámara.** El monitor grande muestra el
sitio; el chico es el índice para elegir. Se viaja de uno al otro: «ELEGIR OTRO»
lleva al índice y elegir una fila vuelve al sitio. La fila ya activa también
vuelve, así que del índice siempre se sale.

Si la pose sorteada del avatar es `escritorio`, **los dos monitores quedan
prendidos siempre**, no sólo al entrar a la sección: ya está sentado ahí, y una
persona frente a dos pantallas apagadas no tiene sentido.

#### El avatar tapaba las pantallas, y estaba medido

`CAM_SECTION_WEB` estaba a 2,59 m del monitor principal. Tirando los rayos de esa
cámara a las cuatro esquinas de la pantalla y midiendo contra el cuerpo del
avatar en la pose del escritorio —dos esferas, torso y cabeza, sacadas de las
posiciones reales de los huesos en `avatar_escritorio.glb`— la holgura mínima
daba **−1,7 cm**: la línea de visión pasaba por dentro de la cabeza. Por eso
cuando salía sorteado ahí tapaba todo.

La salida no fue esconderlo ni subir la cámara, sino **correrla de costado**. El
`azimut` de `CFG.encuadreWebSitio` la gira alrededor del eje vertical de la
pantalla manteniendo distancia y centro:

| | distancia | holgura al avatar | |
|---|---|---|---|
| `CAM_SECTION_WEB` | 2,59 m | **−1,7 cm** | tapaba |
| sitio, azimut −21° | 0,92 m | +6,3 cm | y él sigue en cuadro |
| índice, de frente | 0,57 m | +11,2 cm | |

La cámara del sitio queda **por detrás de la cabeza**, así que el avatar sigue
viéndose; la del índice queda delante, mirando el monitor chico de cerca, donde
él ni aparece. Se comprobó además que esa posición no cae dentro de la silla ni
del monitor grande.

#### Los logos, no las capturas

En los dos monitores va el favicon de cada sitio, el mismo que sale en la
pestaña del navegador. Los baja `tools/fetch_contenido.py` a
`web/contenido/logos/`: prefiere el más grande que declare el HTML —el
`apple-touch-icon` suele ser de 180 px— y deja el `/favicon.ico` de último
recurso. Los SVG se saltean porque PIL no los abre.

Los tres son muy distintos entre sí: un lettering amarillo sin fondo, un
cuadrado crema, un círculo negro. Sobre el carbón de la interfaz el negro
desaparecía, así que cada logo va sobre **una placa clara** que los iguala, y
siempre contenido, nunca recortado — un logo recortado deja de ser el logo. Si
un sitio no tiene favicon usable, va la inicial: nunca un hueco.

Las capturas se siguen generando pero ya no se dibujan en ningún lado; de ellas
sale el color de acento de cada sitio.

### Textos

**Una carilla por artículo.** El spread son las carillas `i` e `i+1` y pasar de
página avanza de a dos, como un libro: con cinco artículos, tres spreads.

**El papel se usa entero.** Antes había una franja muerta de 56 px en el borde
exterior que hacía de botón de pasar página y no se leía como tal: se veía una
línea suelta y un hueco grande. Ahora el margen es parejo y **pasar de página es
un botón de verdad**, al lado del de leer, con la flecha del lado de afuera de
cada carilla. Las flechas del teclado siguen funcionando igual.

**El bloque de texto fluye.** Se miden las líneas que de verdad ocupan el título
y el subtítulo con la tipografía puesta, y recién ahí se decide dónde va cada
cosa. Antes el filete y el subtítulo estaban clavados en una `y` fija y el
subtítulo cortado a dos líneas: los títulos cortos dejaban un hueco enorme y los
largos se cortaban por la mitad.

**La imagen manda y la tipografía nunca se achica.** La portada se queda con lo
que sobra, entre 150 y 300 px, y **nunca desaparece**: sacarla cuando el
subtítulo es largo rompía la continuidad de la sección, que es peor que perder
unas palabras. Si con la imagen puesta el subtítulo no entra entero, se corta con
puntos suspensivos.

Con el contenido de hoy, cuatro de los cinco artículos entran completos con la
imagen en 300 px. El único que aprieta es el de F1 —cuatro líneas de título y
seis de subtítulo—: se queda con 150 px de imagen y el subtítulo baja a cuatro
líneas con «…».

Los dos botones se centran contra el centro geométrico de su rectángulo, no
contra una línea de base: con `alphabetic` la flecha caía baja, y distinto que el
texto del otro botón porque no comparten cuerpo.

#### El pase de página

**La hoja calza al milímetro.** El pivote está en el origen exacto de la tapa y
la hoja gira **el mismo ángulo que ella** (`ANGULO_LIBRO`, 0,98·PI). Medido, el
desfase entre la hoja y la carilla que reemplaza es **cero en los tres ejes**, en
los dos extremos del giro. Antes el pivote y los offsets eran otros:

| | desfase de la hoja contra la carilla |
|---|---|
| en reposo, contra la derecha | 5,0 mm en z · 3,1 mm en y |
| al llegar, contra la izquierda | 4,6 mm en z · 10,3 mm en y |

Eso era el salto lateral al arrancar, el hundimiento al llegar, y el
desacomodarse al final yendo para el otro lado. Y si la hoja girara PI mientras
la tapa abre 0,98·PI, aterrizaría 3,6° pasada y quedaría cruzada contra la
carilla de abajo — por eso es el mismo número.

**Nada se apaga.** Apagar la carilla de abajo mientras la hoja bajaba fue un
intento anterior y era peor: a pocos grados del final la hoja todavía está
levantada y por el hueco se veía la tapa. **Ése era el parpadeo negro.** Como
ahora la hoja calza exactamente, alcanza con el polygon offset.

**Sin espejos.** La hoja es una sola, rígida, con dos caras, las dos
`FrontSide` y con el mismo giro de textura que las carillas: la derecha va con
`Euler(-PI/2)` sobre el pivote y la izquierda con `Euler(+PI/2)`, que al
completar el giro queda con la orientación exacta de la carilla izquierda.
Verificado componiendo las matrices: las cuatro superficies terminan con el mismo
eje `derecha`, que es justo lo que se invertiría si quedara un espejo. El intento
anterior compensaba `BackSide` con el canvas rotado 180° y la textura rotada al
revés — tres correcciones encadenadas que no cerraban, y de ahí los textos
espejados.

**Nada cambia a mitad de camino.** Todo se pinta al arrancar: la cara derecha de
la hoja lleva la carilla que se levanta, la izquierda la que va a quedar, y la
carilla derecha fija ya lleva la nueva, tapada por la hoja hasta que se levanta.
Antes se redibujaban a mitad del recorrido y la página de abajo cambiaba antes de
que llegara la hoja con lo nuevo.

El giro dura 1,5 s con una curva quíntica que sale y entra en reposo con
derivada **y aceleración** cero.

#### El avatar velado

En la pose de escritura está sentado justo entre la cámara y el cuaderno: medido,
los rayos a las esquinas del spread le pasan **8,2 cm por dentro de la cabeza**.
Ahí la cámara no se puede correr, así que el que se aparta es él.

No es bajarle la opacidad. Un `opacity` sobre una malla que se solapa consigo
misma deja ver por dentro del cuerpo, se ordena mal y borra la silueta. Es un
**disuelto por trama ordenada**: cada píxel se descarta o no según una matriz de
Bayer 8×8, así que la malla sigue siendo opaca y no hay mezcla que ordenar.

**Al final no queda nada.** El umbral llega a cero para todos los píxeles. Un
intento anterior dejaba un piso de píxeles vivos para que la silueta aguantara, y
lo que quedaba era un fantasma sucio encima del libro. El `sesgo` sólo cambia el
ORDEN en que se va: el contorno se apaga último. Y la comparación es `>=`, no
`>`: con `>` sobrevivía la grilla de píxeles donde la matriz de Bayer vale
exactamente cero.

**Empieza tarde a propósito.** El velado arranca al 62 % del viaje de cámara y
termina justo antes de llegar. Antes empezaba en el instante del click y el
avatar ya estaba medio ido cuando el recorrido recién arrancaba.

Los números están en `VELO`, arriba de `web/avatar.js`: sesgo 0,6 y 0,7 s de
transición. Sólo se vela en esta sección.

### Música

**Vacía a propósito.** La zona es clicable y la cámara se acerca al rincón, y no
hay nada más.

Lo que había —cada vinilo de la pared convertido en un enlace a una página de
álbum de albumoftheyear.org— fue un error conceptual y está borrado entero:
fichas, tarjeta de perfil, hotspots y la cámara calculada sobre la pared. Queda
decidir qué va a ser esta sección, y eso lo decide Iñaki.

## Interacción

- En Home, los objetos etiquetados por Blender abren su sección.
- Dentro de una sección no aparece ningún tooltip. Sólo cambian los cursores y
  se usan botones visibles con hotspots ajustados a sus límites.
- Sobre un botón el cursor es `pointer`; fuera de un botón queda normal. **No
  hay lupa con menos**: anunciaba un "alejar" que no es lo que pasa y ensuciaba
  la sección entera.
- Un click fuera de la superficie activa equivale a volver al cuarto.
- Escape también vuelve, y el botón `ESC VOLVER` está arriba a la izquierda.
- Flechas izquierda/derecha cambian el contenido con su animación.
- El regreso no corta interfaces: apaga señal/proyector y cierra el libro.

Todos los enlaces abren destinos reales, en otra pestaña.

## El contenido

Ya no hay placeholders. Todo sale de `web/contenido.js`, que **es generado** —
no editarlo a mano:

```bash
python3 tools/fetch_contenido.py
```

Ese script baja el archivo de Substack (título, subtítulo, fecha, URL y
portada), captura los tres sitios con Chrome headless y escribe el módulo. Las
URLs de los sitios, el video y los favoritos de AOTY se configuran arriba del
propio script. Si una fuente se cae, aborta sin tocar `contenido.js`.

Correrlo cuando Iñaki publique un artículo nuevo o cambie un sitio.

| Zona | Contenido | Origen |
|---|---|---|
| Web | helicopters.ar, Cru, Opus | capturas propias en `web/contenido/capturas/` |
| Videos | Cru. Launch Film | `web/videos/cru-launch.mp4` (35 s, 5,2 MB) |
| Ensayos | los 5 artículos | `inakigongorarosi.substack.com` |
| Música | — | la sección está vacía a propósito |

Los contadores de la barra (`WEB 03`, `ENSAYOS 05`…) salen del contenido: si
mañana hay otro artículo, el número cambia solo. Música va sin número, porque no
tiene contenido y un `--` se lee como un error.

`fetch_contenido.py` **todavía baja y guarda los datos de AOTY**, que ya no usa
nadie. Sacarlo cuando se decida qué va a ser la sección de música.

El video se transcodifica del `.mov` original con:

```bash
ffmpeg -i "Videos/Cru. Launch Film.mov" -c:v libx264 -preset slow -crf 23 \
  -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart web/videos/cru-launch.mp4
```

El original traía audio PCM sin comprimir y pesaba 52 MB.

## Reexportar cámaras

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background blender/HABITACION_v020_CONSOLE_UI.blend \
  --python blender/scripts/export_lightmapped_glb.py -- \
  blender/textures/lightmap/room_lightmap_2048.png \
  web/modelos/habitacion-console-ui.glb
```

No hace falta rebakear al mover una cámara.

## Consola

```js
__sala.zonas()
__sala.camaras()
__sala.estado()          // incluye la fase del reproductor
__sala.irA("video")
__sala.siguiente()
__sala.anterior()
__sala.casa()
__sala.enlaces()         // las 9 URLs que puede abrir la página
__sala.hotspots()        // dónde cae cada área clicable en la ventana
__sala.reproducir()
```

`__sala.hotspots()` sirve para comprobar que un botón dibujado y su área
clicable terminaron en el mismo lugar: devuelve coordenadas de ventana.

## La carga

La página no se descubre hasta estar entera. Antes se daba por cargada apenas
llegaba el GLB y el avatar y los vinilos aparecían con el telón ya levantado.

La barra cubre cuatro etapas con pesos a ojo sobre lo que tarda cada una
—habitación 62 %, avatar 16 %, vinilos 10 %, contenido 12 %— y el telón se
levanta cuando terminaron las cuatro. Cada etapa cumple su promesa **también si
falla**: una portada rota o un GLB caído no pueden dejar la pantalla de carga
trabada. Y por las dudas hay un reloj de seguridad de 15 s que la destraba igual,
con un aviso en consola.

Del mp4 se espera sólo la cabecera, que es lo que la ficha necesita para escribir
la duración real. El cuerpo se sigue bajando solo, porque el `<video>` está en
`preload="auto"`: con `metadata` el archivo recién empezaba a bajar al apretar
play y el video arrancaba trabándose.

## Validación

Del 28/07/2026, después de la tanda 1 y de la devolución de Iñaki:

- Carga limpia, cero errores de consola, barra al 100 % y telón levantado.
- Los dos paneles de monitor comparten un lightmap plano de 1×1.
- 9 hotspots (eran 17: los 8 de música ya no existen) y 9 enlaces.
- Con la pose `escritorio` los monitores quedan prendidos en Home.
- `ESC` y `VOLVER`: centros verticales a 0,25 px uno del otro.
- El pie derecho en `cama_celular`: la punta recorre 5,1 cm con un período de
  2,48 s. El izquierdo, 0 cm.
- La curva de cámara, verificada aparte: pico 0,625 contra 3,713.
- `node --check` y `git diff --check` pasan.

Lo visual lo revisa Iñaki. Las duraciones de cámara y la secuencia del
reproductor no se pueden medir en vivo desde el agente: con el panel del
navegador oculto `requestAnimationFrame` se congela y el bucle de render no
avanza, así que la cámara no se mueve y los tiempos dan cero.

`node --check` pasa.

### Pendiente conocido

Sobre el final del pase de página, cuando la hoja ya quedó apoyada a la
izquierda, su dorso se lee girado 180°. Es anterior a esta tanda y dura una
fracción de segundo. Invertir `pageTurnBackSurface.texture.rotation` no lo
corrige —se probó—, así que el error está en otro punto de la cadena (canvas
girado en `dibujarPaginaVuelta` + `BackSide` + bisagra). Sin tocar.
