# Pedidos de Iñaki — 28 de julio de 2026

Todo lo que pidió, tal como lo pidió, con el estado de cada cosa. Este archivo
es la lista de trabajo: se actualiza al cerrar cada tanda, no al empezarla.

Estados: **abierto** · **en tanda 1** · **hecho (falta revisión visual)** ·
**aprobado**.

---

## Tanda 1 — hecha, con la devolución de Iñaki ya aplicada

Son los pedidos que no dependen de que apruebe un encuadre nuevo. Todos tocan
comportamiento, no diseño de las interfaces dentro del mundo.

| # | Pedido | Estado |
|---|---|---|
| 1 | Pantallas de monitor de un solo gris | **aprobado** |
| 1b | Los monitores prendidos si el avatar ya está sentado ahí | hecho — falta revisión |
| 2 | La luz del celular, más tenue y menos blanca | **aprobado** |
| 4 | Cámaras: curva de suavizado y mucho más lentas | **aprobado** |
| 4b | El tirón al empezar y al terminar el viaje | hecho — falta revisión |
| 5 | UI externa: sacar el copy cliché y limpiar la barra | **aprobado** |
| 5b | Título y subtítulo que digan qué es esto | hecho — falta decisión |
| 6 | Cursor sin lupa y botón `ESC VOLVER` más grande | **aprobado** |
| 6b | `ESC` y `VOLVER` alineados verticalmente | hecho — falta revisión |
| 7 | El reproductor de video | aprobado el cierre, no la apertura |
| 7b | La transición de la interfaz al video no tenía animación | hecho — falta revisión |
| 8 | La página no carga hasta estar entera | **aprobado** |
| 9 | Pie derecho con movimiento en `cama_celular` | rehecho — falta revisión |
| 3c | Música: borrar todo el tablero de AOTY | **aprobado** |

### La devolución del 28/07, y qué salió de cada cosa

**1b — los monitores.** Si sale sorteada la pose `escritorio`, el avatar ya está
sentado frente a las pantallas: tienen que estar prendidas siempre, no sólo al
entrar a Web. Se revisa en cada montaje de pose, así que `usar()` desde consola
también lo respeta.

**4b — el tirón.** La causa era el paneo de Home. En reposo la cámara no se mueve
nunca: lo que se mueve es una ventana recortada dentro del cuadro fijo de
Blender, con `setViewOffset`. Eso se prendía y se apagaba **de golpe** —
`clearViewOffset()` en el mismo cuadro del click al entrar, y el paneo
reactivándose en el primer cuadro del regreso, con el mouse donde hubiera
quedado. Un salto de hasta 2,4 % del cuadro, justo antes de que arranque la
animación: exactamente el "se reacomoda y ahí empieza". Ahora el paneo tiene
intensidad y la maneja el propio viaje, con la misma curva. En intensidad 0 el
recorte vale 1 y la ventana es el cuadro entero, o sea idéntico a no tener
offset, pero sin discontinuidad.

**5b — el nombre.** Quedó **La habitación**, con el subtítulo *El portfolio de
Iñaki Góngora*, que es lo que él dejó más cerca de convencerlo. Falta que decida.

**6b — el `ESC`.** El recuadro estaba posicionado contra la línea de texto y mide
10 px contra los 12 del botón, así que caía más arriba. Ahora se centra contra la
altura del botón: medido, quedan a 0,25 px uno del otro.

**7b — la apertura del video.** Faltaba la animación en la tela: la ficha se
reemplazaba por el video de un cuadro al otro, en el instante en que se montaba
el reproductor. Ahora el fundido de la tela arranca junto con el viaje de cámara
y termina antes de que llegue, así que no agrega ni un segundo. Si por lo que
fuera no llegara a tiempo, el cuadro espera: no se monta sobre una tela a medio
encender.

**9 — el pie.** El mecanismo corría, pero medido no se veía nada y por dos
motivos a la vez: 0,055 rad movían la punta del pie **0,87 cm en total**, y 0,44
rad/s es un ciclo cada **14,3 segundos**. Corregido y vuelto a medir:

| | antes | ahora |
|---|---|---|
| Recorrido de la punta | 0,87 cm | 5,1 cm |
| Período | 14,3 s | 2,48 s |

El pie izquierdo, el que está apoyado, se midió también: 0 cm. No se toca.

## Tanda 2 — después de la revisión visual de la tanda 1

Los tres rediseños grandes. Van juntos y van después **porque dependen de un
encuadre aprobado**: cada interfaz se dibuja para la cámara que la mira, y si el
encuadre cambia después, el layout se rehace entero. La tanda 1 además cambia
cómo se mueve la cámara, así que estos encuadres hay que juzgarlos con el
movimiento nuevo puesto.

| # | Pedido | Estado |
|---|---|---|
| 3b | Video: cámara, miniatura, tira legible y la apertura | **aprobado** |
| 3b-2 | La barra de controles no se ocultaba nunca | hecho — falta revisión |
| 3b-3 | Segunda ficha para poder ver la tira | hecho — provisoria |
| 3a | Web: cámara más cerca, avatar que no tape, rediseño con logos | hecho — falta revisión |
| 3a-2 | El viaje entre monitores atravesaba al avatar | hecho — falta revisión |
| 3d | Escritura: avatar velado, rediseño del libro, animación de pase | **aprobado en parte** |
| 3d-2 | Franja muerta, botón de pasar página, subtítulos cortados, pase | **aprobado** |
| 3d-3 | Flechas descentradas, imagen que desaparecía, velado fantasma | hecho — falta revisión |

### 3a-2 · El viaje entre los dos monitores — hecho

En línea recta el viaje del monitor grande al chico pasaba **12 cm por dentro del
torso**: el avatar sentado está justo en el medio de las dos cámaras. Por arriba
no se puede —la cabeza y el respaldo cierran el paso— y por atrás tampoco, así
que el recorrido se curva hacia las pantallas: la cámara cruza por delante de él,
sobre el escritorio, subiendo 21 cm. Medido sobre la curva entera contra el
avatar, el respaldo y los dos monitores, la holgura mínima queda en **+10,6 cm**.

Los viajes ahora aceptan un punto de apoyo (Bézier cuadrática) y un par de puntos
a mirar. En un recorrido curvo interpolar las dos rotaciones apunta a cualquier
lado en el medio; mirando un punto que se interpola, la cámara acompaña las
pantallas de una a la otra. En los dos extremos da exactamente las orientaciones
de salida y llegada, porque los encuadres se construyen mirando justo esos puntos.

### 3a · Web — hecho

**El avatar tapaba, y estaba medido.** `CAM_SECTION_WEB` estaba a 2,59 m del
monitor principal. Tirando los rayos de esa cámara a las cuatro esquinas de la
pantalla y midiéndolos contra el cuerpo del avatar sentado —dos esferas, torso y
cabeza, sacadas de las posiciones reales de los huesos en
`avatar_escritorio.glb`— la holgura mínima daba **−1,7 cm**: la línea de visión
pasaba por dentro de la cabeza.

La salida no fue esconderlo ni levantar la cámara, sino **correrla de costado**:

| | distancia | holgura al avatar | |
|---|---|---|---|
| `CAM_SECTION_WEB` | 2,59 m | **−1,7 cm** | tapaba |
| sitio, azimut −21° | 0,92 m | +6,3 cm | y él sigue en cuadro |
| índice, de frente | 0,57 m | +11,2 cm | |

**2,8 veces más cerca** y la pantalla libre. La cámara del sitio queda por detrás
de la cabeza, así que el avatar se sigue viendo. Verificado también que esa
posición no cae dentro de la silla ni del monitor grande.

**Un monitor por vista.** El grande muestra el sitio, el chico es el índice, y
cada uno tiene su propia cámara: «ELEGIR OTRO» viaja al índice y elegir una fila
vuelve al sitio. La fila ya activa también vuelve, así que del índice siempre se
sale. Eso es lo que resuelve la incomodidad de tener que leer los dos monitores a
la vez desde un solo encuadre lejano.

**Los logos, no las capturas.** El favicon de cada sitio, el mismo de la pestaña
del navegador, bajado a `web/contenido/logos/`. Los tres que salieron son muy
distintos —un lettering amarillo sin fondo, un cuadrado crema, un círculo
negro—, así que cada uno va sobre una placa clara que los iguala, siempre
contenido y nunca recortado. Sin favicon usable va la inicial del sitio.

**Los canvas ahora están en la proporción de su plano** (1030×600 y 720×415):
antes eran 960×600 y 600×370 sobre planos de 1,716 y 1,735 de relación, o sea
todo el dibujo salía estirado.

### 3d-3 · La tercera vuelta de Escritura — hecho

**Las flechas descentradas.** Estaban puestas contra una línea de base a ojo
(`+51 px`) en vez del centro del rectángulo. Con `alphabetic` la flecha cae baja,
y encima distinto que el texto del botón de al lado porque no comparten cuerpo.
Ahora los dos van con `textBaseline = "middle"` sobre el centro geométrico.

**La imagen desaparecía.** Si el subtítulo era largo, la portada se caía a cero.
Se invirtió la prioridad: **la imagen manda**, nunca baja de 150 px y nunca se
saca; si con ella puesta el subtítulo no entra, se corta con puntos suspensivos.
Verificado con los cinco artículos: cuatro entran completos con 300 px de imagen
y sólo el de F1 aprieta a 150 px y recorta el subtítulo de seis a cuatro líneas.

**El velado.** Dos cosas. No llegaba a cero —quedaba un piso de píxeles vivos
para que la silueta aguantara, y era un fantasma sucio encima del libro—, y
empezaba en el instante del click, así que el avatar ya estaba medio ido cuando
el viaje de cámara recién arrancaba. Ahora el umbral llega a **cero para todos
los píxeles** (y la comparación es `>=`, porque con `>` sobrevivía la grilla
donde la matriz de Bayer vale exactamente cero), y **arranca al 62 % del viaje**,
terminando justo antes de llegar.

### 3d-2 · La segunda vuelta de Escritura — hecho

Cuatro cosas, y las cuatro tenían causa medible.

**La franja muerta.** El borde exterior de 56 px hacía de botón de pasar página
y no se leía como tal: se veía una línea suelta y un hueco. Se fue: el papel se
usa entero y **pasar de página es un botón de verdad** al lado del de leer, con
la flecha del lado de afuera de cada carilla. Las flechas del teclado siguen.

**Los subtítulos cortados y el hueco entre título y subtítulo.** El filete y el
subtítulo estaban clavados en una `y` fija y el subtítulo cortado a dos líneas.
Ahora el bloque **fluye**: se miden las líneas reales de cada texto y se decide
dónde va cada cosa. El subtítulo nunca se corta y la tipografía nunca se achica —
la que cede es la imagen, que se queda con lo que sobra entre 96 y 300 px. Con el
contenido de hoy el único que la achica es el de F1, que baja a 116 px.

**El salto y el hundimiento.** La hoja que gira no calzaba con la carilla que
reemplaza. Medido:

| | desfase de la hoja |
|---|---|
| en reposo, contra la carilla derecha | 5,0 mm en z · 3,1 mm en y |
| al llegar, contra la izquierda | 4,6 mm en z · 10,3 mm en y |

El pivote pasó al origen exacto de la tapa y la hoja gira **el mismo ángulo que
ella**. Desfase nuevo: **cero en los tres ejes, en los dos extremos**.

**El parpadeo negro.** Lo había metido yo en la vuelta anterior: apagaba la
carilla de abajo mientras la hoja bajaba, y a pocos grados del final la hoja
todavía está levantada, así que por el hueco se veía la tapa. Ya no se apaga
nada; como la hoja calza exacto, alcanza con el polygon offset.

### 3d · Escritura — hecho

**Una carilla por artículo.** El spread son las carillas `i` e `i+1` y pasar de
página avanza de a dos, como un libro: con cinco artículos, tres spreads. Se fue
toda la redundancia — el subtítulo repetido, los dos botones de leer (uno de los
cuales no hacía nada) y la firma inventada al pie. En cada carilla va portada,
título, subtítulo y leer. Los de pasar de página son **el margen exterior de la
carilla**: se hace click en el borde de la hoja que se quiere dar vuelta.

**El pase estaba mal por dos lados a la vez.**

*El espejo.* La cara de atrás era `BackSide`, con el canvas rotado 180° al
dibujarlo Y la textura rotada al revés: tres correcciones encadenadas que no
cerraban, y de ahí los textos espejados que se acomodaban de golpe. Ahora es una
hoja rígida con dos caras, las dos `FrontSide`, sin una sola compensación.
Verificado componiendo las matrices: las cuatro superficies terminan con el mismo
eje `derecha`, que es exactamente lo que se invertiría si quedara un espejo.

*El momento.* Antes las carillas fijas se redibujaban a mitad del recorrido, así
que la de abajo cambiaba antes de que llegara la hoja con lo nuevo. Ahora nada
cambia a mitad de camino: todo se pinta al arrancar y sólo se toca lo que está
tapado por la hoja.

El giro pasó de 1,05 a 1,5 s, con una curva quíntica que sale y entra en reposo
con derivada y aceleración cero — la cúbica de antes tiene un filo perceptible
justo al apoyarse.

**El avatar velado.** En la pose de escritura los rayos a las esquinas del spread
le pasan **8,2 cm por dentro de la cabeza**, y ahí la cámara no se puede correr.
No es bajarle la opacidad: es un disuelto por trama de Bayer 8×8, con la malla
opaca —sin mezcla ni orden que resolver— y un término de borde que deja
sobrevivir más píxeles en el contorno, así que la silueta aguanta mientras el
cuerpo se abre. 14 % de píxeles de frente, 72 % en el contorno, 0,85 s.

### 3b · Video — hecho

**La ficha.** El poster ocupa la tela entera, con degradado abajo, el título en
64 px y el botón. La tira vertical de 190 px se fue: ahí no entraba un título y
por eso quedaba el número en 13 px. Si algún día hay más de un video la tira es
**horizontal y abajo**, con 284 px por ficha y el título en tres líneas de 21 px.
Sólo el título, sin tipo ni año.

**La miniatura.** Es el campo `poster` de `VIDEOS`, arriba de
`tools/fetch_contenido.py`. Cualquier PNG o JPG en `web/videos/`. El script ahora
verifica que exista y aborta si no.

**La cámara.** Medido: pasó de mirar la tela de costado a **13,4°** de la
perpendicular, a 0,61 m del frontal exacto. La perilla es
`CFG.encuadreVideo.frontalidad`, hoy 0,72 — subirla la acerca más al frontal,
bajarla la devuelve al ángulo del GLB.

**La apertura, que era el problema de fondo.** No era un tema de medidas. La tela
la dibuja el `EffectComposer` —AgX, exposición, bloom, y el grano encima del
canvas— y el `<video>` del DOM sale crudo: son **dos imágenes distintas del mismo
cuadro**. El relevo entre una y otra era un salto de color y textura por más que
los rectángulos calzaran al milímetro. Calzarlos mejor no lo podía arreglar
nunca, y por eso seguía snapeando después del intento anterior.

Se sacó la `VideoTexture` entera. Ahora nadie se releva: la tela muestra siempre
su ficha, el reproductor aparece **quieto** encima disolviéndose sobre ella
(0,42 s), y recién ahí crece (0,95 s). La diferencia entre las dos imágenes pasa
a ser el efecto en vez del error. Al cerrar, exactamente al revés.

**La barra de controles.** No se ocultaba por una causa concreta: `sincronizarControles()`
despertaba la barra, y esa función corre con **cada `timeupdate`** — unas cuatro
veces por segundo mientras el video anda. El temporizador de ocio se reiniciaba
antes de poder vencer, siempre. Ahora sólo despiertan la barra los eventos que
son una decisión de quien mira: mover el mouse, una tecla, play y pausa. Y el
ocio bajó de 2,8 s a **2 s**.

**La segunda ficha es provisoria.** Con un solo video no hay tira ni forma de
pasar de uno a otro, así que se agregó «Video de prueba, para ver la tira»
apuntando al mismo mp4 con una miniatura sacada del segundo 24 para que se
distinga. Está marcada para borrar arriba de `tools/fetch_contenido.py`.

---

## El detalle de cada pedido

### 1 · La textura de las pantallas del monitor

> «No es de un solo color, actualmente es de un gris oscuro y uno más claro, no
> tiene sentido, debería ser toda del color gris oscuro. Tené cuidado con esto y
> cómo lo manejás ya que las luces están horneadas.»

**Medido antes de tocar nada.** No era la textura: los dos paneles comparten
material (`MAT_BLOCKOUT_SCREEN`) y comparten albedo (`TEX_SCREEN`, 64 px, plano
y oscuro). Lo que difiere es **el lightmap horneado**, promediado sobre el área
UV2 de cada panel:

| Panel | Media del lightmap | Lectura |
|---|---|---|
| `MONITOR_MAIN_PANEL` | (6, 4, 2) | casi negro |
| `MONITOR_SIDE_PANEL` | (59, 41, 23) | diez veces más claro y cálido |

Por eso uno se ve gris oscuro y el otro gris claro.

**Cómo se corrigió sin tocar el horneado:** el material de los dos paneles deja
de leer el atlas y pasa a un lightmap plano de un solo valor, calcado del que
hoy tiene el panel principal. El atlas del cuarto no se toca, no hay rebake, y
`MAT_BLOCKOUT_SCREEN` no lo usa ningún otro objeto — se comprobó: sólo esos dos.

### 2 · La luz del celular

> «Es desproporcionada, y demasiado blanca. Bajala un poco, parece una linterna,
> y que no sea tan blanca porque desentona con la iluminación cálida.»

Tres cosas la volvían una linterna, y las tres estaban en `web/avatar.js`:
intensidad 1,45 con alcance 1,3 m, color `#a8c4f0`, y —la peor— la superficie
de la pantalla se repintaba cada cuadro con `setScalar`, que borra el color y
deja gris casi blanco. Ahora la superficie conserva su color y sólo se modula su
brillo.

### 3 · Ángulos de cámara y rediseño de las interfaces

Es el pedido grande. Se parte en cuatro; sólo música entra en la tanda 1.

#### 3a · Web — **tanda 2**

- De base está muy lejos.
- Usar los dos monitores es ingenioso pero incómodo.
- Si el avatar está en el escritorio, tapa absolutamente todo. La cámara tiene
  que aguantar eso **sin hacer desaparecer al avatar**.
- El monitor chico como navegación no está mal, pero así es ilegible: lejos, y
  con el nombre escrito chiquito.
- Rediseño completo. Se puede seguir usando la segunda pantalla, pero mejor
  aprovechada, con otro ángulo, más de cerca y más grande.
- **Nada de previews de las páginas: los logos.** Los favicon de cada sitio.

#### 3b · Video — **tanda 2**

- El ángulo tiene que ser más de frente. No 100 % de frente, pero está
  demasiado angulado.
- La miniatura del costado se elige mal. Tiene que poder indicar él qué PNG
  funciona de miniatura.
- En la tira lateral hoy sale sólo un `01` ridículamente chico. Debería decir el
  título, y nada más que eso (**sin año ni tipo**).
- El problema de fondo es que no hay lugar para eso como está: el tamaño de ese
  texto es ridículo. Hay que resolverlo de raíz, no agrandar la fuente.

#### 3c · Música — **tanda 1, hecho**

> «Fue un error conceptual enorme. Borrá todo lo que hay, incluida la nueva
> cámara. Dejá obvio que sea clickeable música, que se haga un zoom.»

El agente anterior leyó "AOTY" y decidió que cada vinilo de la pared fuera un
enlace a una página de álbum de albumoftheyear.org. Iñaki lo llama alucinación.
Borrado: las seis fichas, la tarjeta de perfil, los enlaces, los hotspots y la
cámara calculada sobre la pared. La zona sigue siendo clicable y vuelve a usar
`CAM_SECTION_MUSICA` del GLB, que es el plano general del rincón.

Queda pendiente decidir qué va a ser música. Nadie lo decide por él.

#### 3d · Escritura — **tanda 2**

- Igual que en web: si el avatar está ahí, no se ve nada. Acá es más difícil
  porque la cámara debería estar muchísimo más cerca, y la distancia está bien.
- Solución que pidió: **el avatar se vuelve traslúcido, sólo en esta sección**,
  con un fundido suave y un efecto pensado y medido — no bajarle un `opacity`
  y listo.
- La interfaz del libro está mal de raíz: dos botones de leer y el de abajo no
  hace nada, el subtítulo aparece dos veces, y `gongora — substack` es texto
  inventado que no sale de ningún lado.
- Rediseño: **una carilla por artículo**, con título, subtítulo, imagen y botón
  de leer. Nada más. Como el libro está abierto, se ven dos artículos a la vez.
  Los botones de avanzar y retroceder tienen que ir en algún lado.
- La animación de pase de página está rota por todos lados: los textos aparecen
  espejados durante la transición y se acomodan de golpe, y la página de atrás
  cambia antes de que llegue la hoja que trae la información nueva.

#### La pregunta que dejó abierta

> «No sé si estás limitado por el hecho de que sean canvas en un espacio 3D. Si
> es el caso, decime y vemos si no cambiamos el enfoque completamente.»

**No es una limitación de la técnica.** Un `CanvasTexture` es un mapa de bits
normal: el monitor principal hoy dibuja 960×600 px sobre un plano de 70 cm, y a
la distancia a la que lo mira la cámara sobra resolución. Lo que falló fue el
diseño de esos canvas, no el soporte. Los dos límites reales del enfoque son
otros y ninguno explica lo que él está viendo: no hay selección de texto ni
accesibilidad nativa (es un dibujo, no un DOM), y todo lo que se dibuja hay que
posicionarlo a mano en píxeles. Se sigue con canvas.

### 4 · Las transiciones de cámara

> «Ridículamente bruscas y rápidas. Primero una curva de suavizado natural, y
> además bastante más lentas, para que se sienta premium. Empieza lento, se
> acelera un poco, y antes de llegar desacelera. Siempre que la velocidad máxima
> sea bastante menos que la actual: se debe sentir que la cámara pesa.»

Antes cada viaje era un lerp exponencial: la velocidad **máxima está en el
primer cuadro** y después sólo baja. Eso es exactamente lo contrario de lo que
pidió, y es la razón del arranque brusco. Medido: 3,713 veces la distancia por
segundo en el arranque.

Ahora todo viaje de cámara tiene duración y curva propia (`easeCamara`): arranca
en reposo, acelera y frena antes de llegar. Su pico es 1,5 × distancia /
duración, el más bajo posible para una curva que además sale y entra en reposo.

| | pico | |
|---|---|---|
| lerp exponencial viejo | 3,713 × distancia/s | en el primer cuadro |
| curva nueva, 2,4 s | 0,625 × distancia/s | en la mitad del viaje |

**5,9 veces más lento.** Además el lerp exponencial nunca llegaba del todo al
destino, sólo se le acercaba; un viaje con duración llega, y eso es lo que
permite abrir el reproductor sabiendo que la cámara está exactamente de frente.

### 5 · La UI de afuera

- **Orden**: nunca más copy de palabras clave tipo `PORTFOLIO / MENDOZA / 2026`.
  Anotado en la memoria del proyecto, no sólo acá.
- El título grande de abajo a la izquierda hay que cambiarlo: ni "Habitación" ni
  "Archivo personal". Escucha sugerencias.
- El recuadro con `IÑAKI / ARCHIVO PERSONAL` no se entiende qué función cumple.
  Repensado.
- `AUDIO: OFF` y `CONTACTO` afuera.

### 6 · Cursor y botón de volver

- Dentro de una sección, al pasar por una zona no clicable el cursor se pone en
  lupa con menos. No tiene que pasar.
- El botón `ESC VOLVER` es tan chico que ni se nota.

### 7 · El reproductor de video

- Al dar play arranca el video, se dispara la animación y se reinicia. Lo que
  tiene que pasar: **la animación, la pantalla completa, todo en su lugar, y
  recién ahí empieza**.
- La barra de controles no se va nunca. Tiene que irse sola a los pocos segundos
  sin actividad y volver al mover el mouse.
- Salir de un video también está roto.
- La filosofía, textual: **«es preferible que la cosa sea lenta, con animaciones
  limpias, que cada cosa llegue a su lugar y nada se teletransporte, antes que
  algo apurado porque sí. NO HAY APURO. EN NADA.»**

### 8 · El orden de carga

La página se muestra cargada y un segundo después aparecen el avatar y los
vinilos. Tienen que estar antes de que se levante el telón.

### 9 · El pie derecho

En la pose `cama_celular`, que el pie levantado —el derecho, no el que está
apoyado— suba y baje mínimamente.

---

## Lo que se tocó sin que lo pidiera, y por qué

- **`tools/servidor.py`**, y `.claude/launch.json` apuntando ahí. Es
  `python3 -m http.server` mandando `no-store`. Sin eso el navegador se queda con
  la copia vieja de todo lo que no lleve `?v=` colgado: se perdieron dos vueltas
  de verificación creyendo que el código no había cambiado. Los módulos además
  llevan `?v=NN`, en `index.html` y en los dos `import` de arriba de `sala.js`;
  los tres números se mueven juntos.

## Pendientes anotados que tampoco son pedidos suyos

- `web/contenido.js` y `tools/fetch_contenido.py` siguen bajando y guardando los
  datos de AOTY, que ya no usa nadie. Sacarlo cuando se decida qué va a ser la
  sección de música.
- El título grande de abajo a la izquierda dice el nombre a falta de una
  decisión. Es provisorio.

## Lo que no se pudo verificar desde acá

Las duraciones de cámara y la secuencia del reproductor no se pudieron medir en
vivo: con el panel del navegador oculto `requestAnimationFrame` se congela y el
bucle de render no avanza, así que la cámara no se mueve y los tiempos dan cero.
Lo que sí quedó verificado: carga limpia sin errores de consola, barra al 100 %,
9 hotspots y 9 enlaces, los dos paneles de monitor con lightmap plano de 1×1, el
emisor del celular en `#a79d88`, `node --check` y `git diff --check`. La curva de
cámara se verificó numéricamente aparte: pico 0,625 contra 3,713.
