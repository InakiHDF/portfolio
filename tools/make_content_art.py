"""
ARTE GENERADO PARA LOS HUECOS QUE NO LLEVAN REFERENCIA
======================================================

Tres familias, cada una con su propia resolucion porque cada una tiene un
tamano distinto en pantalla:

  Lomos de libros   3 a 5 texels de ancho. No entra una palabra ni forzando,
                    asi que las "palabras" son bloques negros. Escribir texto
                    de verdad a esta escala desentona: se lee como error.
  Polaroids         12 x 16 texels. Blanco y negro, marco blanco con el pie
                    mas ancho abajo, que es lo que hace que se lea polaroid.
  Cuadros escalera  16 a 23 texels. Alcanza para una composicion: horizonte,
                    figura, arco, rombos.

Todas comparten paleta con la habitacion. Nada de colores chillones.

Uso:
  python3 tools/make_content_art.py
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_textures import calibrar, a_lineal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "blender", "textures", "content")

NEGRO = (22, 20, 19)
CREMA = (206, 196, 178)
BLANCO = (232, 229, 222)


def guardar(a, nombre, albedo=None):
    """Guarda calibrando el albedo.

    Sin esto los lomos salieron mucho mas oscuros que los colores planos que
    reemplazaban: el PNG es sRGB y el color plano estaba en lineal. Es el
    mismo error que ya habia corregido en las texturas de superficie, y se me
    escapo aca."""
    os.makedirs(OUT, exist_ok=True)
    a = np.clip(a, 0, 255) / 255.0
    if albedo is not None:
        a = calibrar(a, albedo)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(OUT, nombre + ".png"))


# ---------------------------------------------------------------------------
# LOMOS DE LIBROS
# ---------------------------------------------------------------------------

LOMOS = [
    (62, 74, 58), (96, 52, 40), (44, 56, 78), (122, 104, 62),
    (72, 62, 84), (38, 68, 66), (140, 122, 96), (88, 44, 46),
    (54, 78, 52), (104, 86, 58), (46, 50, 62), (118, 70, 44),
]


def lomo(w, h, seed):
    rng = np.random.default_rng(seed)
    base = np.array(LOMOS[seed % len(LOMOS)], dtype=np.float32)
    a = np.tile(base, (h, w, 1))

    # Veta vertical suave: ningun lomo es de un color exacto
    a *= (0.92 + 0.16 * rng.random((h, w, 1)))

    # Bandas horizontales cerca de los extremos
    claro = np.clip(base * 1.45, 0, 255)
    oscuro = base * 0.6
    if h >= 12:
        a[2:4] = claro
        a[h - 5:h - 3] = claro
        if h >= 20:
            a[h - 9:h - 8] = oscuro

    # "Titulo": bloques negros que sugieren palabras, nunca texto de verdad
    y = max(5, h // 3)
    for _ in range(rng.integers(2, 4)):
        largo = int(rng.integers(2, max(3, h // 6)))
        x0 = 1 if w <= 3 else int(rng.integers(1, max(2, w - 1)))
        ancho = max(1, w - 2)
        a[y:y + largo, x0:x0 + ancho] = NEGRO
        y += largo + int(rng.integers(2, 4))
        if y > h - 8:
            break
    return a


# ---------------------------------------------------------------------------
# POLAROIDS
# ---------------------------------------------------------------------------

def polaroid(w, h, seed):
    rng = np.random.default_rng(100 + seed)
    a = np.tile(np.array(BLANCO, dtype=np.float32), (h, w, 1))
    m, pie = 1, 3                            # marco y pie inferior
    ih, iw = h - m - pie, w - 2 * m
    yy, xx = np.mgrid[0:ih, 0:iw]
    u = xx / max(1, iw - 1)
    v = yy / max(1, ih - 1)

    tipo = seed % 8
    if tipo == 0:                            # figura de pie a contraluz
        g = np.where(v > 0.72, 0.25, 0.86)
        cuerpo = (np.abs(u - 0.5) < 0.12) & (v > 0.28)
        cabeza = ((u - 0.5) ** 2 + (v - 0.22) ** 2) < 0.012
        g = np.where(cuerpo | cabeza, 0.12, g)
    elif tipo == 1:                          # ventana con luz
        g = np.full((ih, iw), 0.18)
        vent = (np.abs(u - 0.5) < 0.30) & (np.abs(v - 0.42) < 0.28)
        g = np.where(vent, 0.90, g)
        g = np.where(vent & ((np.abs(u - 0.5) < 0.03) | (np.abs(v - 0.42) < 0.03)),
                     0.20, g)
    elif tipo == 2:                          # horizonte y luna
        g = np.where(v > 0.60, 0.22, 0.78)
        luna = ((u - 0.68) ** 2 + (v - 0.28) ** 2) < 0.020
        g = np.where(luna, 0.97, g)
    elif tipo == 3:                          # retrato desenfocado
        d = ((u - 0.5) ** 2 * 1.6 + (v - 0.45) ** 2)
        g = np.clip(0.95 - d * 3.2, 0.10, 0.95)
    elif tipo == 4:                          # escalera y sombra
        g = np.where((v * 6).astype(int) % 2 == 0, 0.72, 0.30)
        g = np.where(u > 0.62, g * 0.42, g)
    elif tipo == 5:                          # dos figuras
        g = np.where(v > 0.78, 0.20, 0.88)
        for cx in (0.34, 0.62):
            g = np.where((np.abs(u - cx) < 0.09) & (v > 0.34), 0.14, g)
            g = np.where(((u - cx) ** 2 + (v - 0.27) ** 2) < 0.008, 0.14, g)
    elif tipo == 6:                          # mar y horizonte alto
        g = np.where(v > 0.34, 0.40, 0.86)
        g = np.where(v > 0.72, 0.24, g)
    else:                                    # planta a contraluz
        g = np.full((ih, iw), 0.90)
        tallo = np.abs(u - 0.5) < 0.05
        g = np.where(tallo & (v > 0.35), 0.16, g)
        for k, (hx, hy) in enumerate(((0.30, 0.42), (0.70, 0.36), (0.36, 0.66))):
            g = np.where(((u - hx) ** 2 * 2.2 + (v - hy) ** 2 * 3.0) < 0.030, 0.18, g)
        g = np.where(v > 0.84, 0.28, g)

    g = g + (rng.random((ih, iw)) - 0.5) * 0.10
    g = np.clip((g - 0.5) * 1.30 + 0.46, 0, 1)        # mas contraste
    g = np.round(g * 4) / 4.0                        # 5 grises, no mas
    a[m:m + ih, m:m + iw] = (g[..., None] * 255).astype(np.float32)
    return a


# ---------------------------------------------------------------------------
# CUADROS DE LA ESCALERA
# ---------------------------------------------------------------------------

PAL_ARTE = [
    np.array([(28, 26, 25), (196, 184, 164), (168, 78, 40), (72, 84, 92)]),
    np.array([(24, 28, 32), (176, 172, 160), (94, 116, 84), (196, 148, 62)]),
    np.array([(32, 24, 22), (204, 192, 172), (120, 60, 58), (86, 92, 108)]),
]


def cuadro(w, h, seed):
    pal = PAL_ARTE[seed % len(PAL_ARTE)]
    rng = np.random.default_rng(200 + seed)
    yy, xx = np.mgrid[0:h, 0:w]
    u = xx / max(1, w - 1)
    v = yy / max(1, h - 1)
    m = np.ones((h, w), dtype=np.int32)       # indice 1 = fondo claro

    tipo = seed % 7
    if tipo == 0:                             # sierra de montanas
        m[:] = 1
        for k, alt in enumerate((0.55, 0.68)):
            pico = alt + 0.16 * np.sin(u * 6.2 + k * 2.1)
            m[v > pico] = 2 if k == 0 else 0
        m[((u - 0.74) ** 2 + (v - 0.22) ** 2) < 0.010] = 3
    elif tipo == 1:                           # rectangulos concentricos
        b = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
        m = (b // max(1, h // 8)) % 2 * 2
        m[b < 1] = 0
    elif tipo == 2:                           # corte diagonal
        m = np.where(u + v > 1.0, 0, 1)
        m[np.abs(u + v - 1.0) < 0.10] = 2
    elif tipo == 3:                           # arco
        m[:] = 0
        arco = (((u - 0.5) ** 2 * 3.0 + (v - 0.75) ** 2 * 0.7) < 0.22) & (v > 0.18)
        m[arco] = 1
        m[arco & (v > 0.80)] = 3
    elif tipo == 4:                           # grilla de puntos
        m[:] = 1
        paso = max(3, h // 6)
        m[(yy % paso == paso // 2) & (xx % paso == paso // 2)] = 0
        m[v > 0.86] = 2
    elif tipo == 5:                           # figura sentada
        m[:] = 1
        m[v > 0.70] = 3
        cuerpo = (np.abs(u - 0.44) < 0.16) & (v > 0.40) & (v < 0.78)
        cabeza = ((u - 0.44) ** 2 * 1.4 + (v - 0.32) ** 2) < 0.014
        m[cuerpo | cabeza] = 0
    else:                                     # rombos
        cw, ch = max(4, w // 3), max(4, h // 4)
        dx = ((xx + (yy // ch % 2) * cw // 2) % cw) - cw / 2.0
        dy = (yy % ch) - ch / 2.0
        d = np.abs(dx) / (cw / 2.0) + np.abs(dy) / (ch / 2.0)
        m[:] = 1
        m[d < 0.9] = 2
        m[d < 0.45] = 0

    # Marco: una orilla oscura de un texel
    m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = 0
    a = pal[m].astype(np.float32)
    a *= (0.94 + 0.12 * rng.random((h, w, 1)))
    return a


# ---------------------------------------------------------------------------

def main():
    # (nombre, ancho, alto) en texels. Salen de medir el objeto y dividir
    # por el tamano de texel elegido para cada familia.
    print("LOMOS DE LIBROS (texel 1.2 cm)")
    ESPESOR = (0.034, 0.052, 0.040, 0.030, 0.058, 0.036, 0.046)
    ALTURA = (0.38, 0.34, 0.42, 0.30, 0.36, 0.40, 0.32)
    for i in range(21):
        k = (i % 7 + i // 7) % 7
        w = max(3, int(round(ESPESOR[k] / 0.012)))
        h = max(10, int(round(ALTURA[k] / 0.012)))
        # Albedo alternado para que la fila no quede pareja, en el rango
        # de los materiales planos que reemplazan (0.22 a 0.79).
        obj = (0.30, 0.42, 0.26, 0.36, 0.48, 0.32, 0.38)[i % 7]
        guardar(lomo(w, h, i), "BOOK_NORTH_%02d" % (i + 1), albedo=obj)
    print("  21 lomos, de %dx%d a %dx%d texels" % (3, 25, 5, 35))

    # Las once polaroids (cuatro en la pared norte, siete en la escalera)
    # comparten tamano, para que se lean como una misma coleccion. La
    # resolucion sale del tamano real en pantalla, leido del inventario.
    import json
    huecos = json.load(open(os.path.join(REPO, "docs", "huecos.json")))
    print("POLAROIDS")
    grupos = ([("PHOTO_NORTH_%02d" % i, i - 1) for i in range(1, 5)] +
              [("FRAME_STAIR_%02d" % i, i + 3) for i in range(1, 8)])
    anchos = []
    for nombre, semilla in grupos:
        d = huecos.get(nombre)
        if d is None:
            print("  sin medida:", nombre)
            continue
        w = max(10, int(round(d["px_pantalla"] / 4.0)))
        h = max(12, int(round(w / d["proporcion"])))
        anchos.append(w)
        # Sin calibrar: al escalar la imagen entera para llegar a una media,
        # cada polaroid termina con un blanco distinto y la foto se lava.
        guardar(polaroid(w, h, semilla), nombre)
    print("  %d polaroids, de %d a %d texels de ancho, 8 motivos distintos"
          % (len(anchos), min(anchos), max(anchos)))


# ---------------------------------------------------------------------------
# CONSOLAS, HOJAS ESCRITAS Y CUERO
# ---------------------------------------------------------------------------

def consola(w, h, modelo):
    """Frente de una consola. A 37 x 9 texels no entra un logo, pero si
    entran las senas que la identifican: la ranura, la luz, la franja."""
    if modelo == "wii":
        cuerpo, detalle, luz = (232, 232, 230), (150, 150, 148), (90, 190, 255)
        a = np.tile(np.array(cuerpo, dtype=np.float32), (h, w, 1))
        a[2:h - 2, int(w * 0.16):int(w * 0.16) + 2] = detalle     # ranura del disco
        a[h - 4:h - 2, int(w * 0.16):int(w * 0.60)] = luz          # led azul
        a[1:h - 1, int(w * 0.78):int(w * 0.90)] = detalle          # tapa de puertos
    elif modelo == "switch":
        cuerpo, izq, der = (34, 34, 38), (196, 52, 40), (32, 118, 190)
        a = np.tile(np.array(cuerpo, dtype=np.float32), (h, w, 1))
        a[:, :int(w * 0.17)] = izq                                 # joy-con rojo
        a[:, int(w * 0.83):] = der                                 # joy-con azul
        a[2:h - 2, int(w * 0.24):int(w * 0.76)] = (18, 18, 20)      # pantalla
    else:                                                          # ps
        cuerpo, franja, luz = (28, 28, 32), (216, 214, 210), (60, 140, 240)
        a = np.tile(np.array(cuerpo, dtype=np.float32), (h, w, 1))
        a[:, int(w * 0.30):int(w * 0.36)] = franja                  # canto blanco
        a[:, int(w * 0.64):int(w * 0.70)] = franja
        a[h - 3:h - 1, int(w * 0.40):int(w * 0.60)] = luz           # led
        a[1:3, int(w * 0.42):int(w * 0.58)] = (70, 70, 76)          # ranura
    ruido = np.random.default_rng(hash(modelo) % 9999).random((h, w, 1))
    return a * (0.94 + 0.10 * ruido)


def hoja_escrita(w, h, seed):
    """Hoja escrita a mano: parrafos de renglones de largo desparejo.

    Nada de croquis ni diagonales. Los renglones son bloques oscuros: a esta
    escala una letra de verdad se lee como suciedad, pero un renglon con el
    largo justo se lee como texto sin que se pueda leer nada."""
    rng = np.random.default_rng(300 + seed)
    papel = np.array((228, 224, 214), dtype=np.float32)
    tinta = np.array((52, 48, 44), dtype=np.float32)
    a = np.tile(papel, (h, w, 1))
    a *= (0.96 + 0.07 * rng.random((h, w, 1)))

    margen = max(2, w // 10)
    util = w - 2 * margen
    y = margen
    # Titulo: un renglon corto y grueso, arriba
    if h > 20:
        a[y:y + 2, margen:margen + int(util * rng.uniform(0.35, 0.60))] = tinta
        y += 5

    # Parrafos: el ultimo renglon de cada uno siempre queda corto, que es lo
    # que hace que un bloque de renglones se lea como texto y no como rayas.
    while y < h - margen - 2:
        renglones = int(rng.integers(3, 7))
        for i in range(renglones):
            if y >= h - margen - 2:
                break
            largo = (int(util * rng.uniform(0.30, 0.62)) if i == renglones - 1
                     else int(util * rng.uniform(0.86, 1.00)))
            sangria = int(util * 0.08) if i == 0 else 0
            a[y, margen + sangria:margen + sangria + largo] = tinta
            y += 2
        y += 2

    return a


def cuero(w=32, h=32, seed=9):
    """Cuero de la tapa: grano irregular, oscuro y calido."""
    from make_textures import fractal, rampa, aplicar
    v = fractal(w, h, seed, octavas=4, celdas=5) * 0.8 + 0.1
    pal = rampa([(48, 30, 20), (62, 40, 26), (78, 52, 34), (92, 64, 42)], 4)
    return aplicar(np.clip(v, 0, 1), pal) * 255.0


def consolas_y_hojas():
    import json
    huecos = json.load(open(os.path.join(REPO, "docs", "huecos.json")))

    print("CONSOLAS")
    for nombre, modelo in (("RETRO_CONSOLE_01", "wii"),
                           ("RETRO_CONSOLE_02", "switch"),
                           ("RETRO_CONSOLE_03", "ps")):
        guardar(consola(37, 9, modelo), nombre)
    print("  3 frentes de 37x9 texels: Wii, Switch y PlayStation")

    print("HOJAS DEL ESCRITORIO ESTE")
    n = 0
    for i in range(1, 8):
        nombre = "SHEET_EAST_%02d" % i
        d = huecos.get(nombre)
        if d is None:
            continue
        w = max(20, int(round(d["px_pantalla"] / 5.0)))
        h = max(24, int(round(w / d["proporcion"])))
        guardar(hoja_escrita(w, h, i), nombre, albedo=0.72)
        n += 1
    print("  %d hojas escritas, hasta %d texels de ancho" % (n, w))

    print("CUERO DEL CUADERNO")
    guardar(cuero(), "TEX_NOTEBOOK_LEATHER", albedo=0.075)
    import shutil
    shutil.copy(os.path.join(OUT, "TEX_NOTEBOOK_LEATHER.png"),
                os.path.join(REPO, "blender", "textures", "surface",
                             "TEX_NOTEBOOK_LEATHER.png"))
    os.remove(os.path.join(OUT, "TEX_NOTEBOOK_LEATHER.png"))
    print("  cuero de 32x32 en textures/surface")


def lomos_oeste():
    """Los seis libros del estante sobre el escritorio, mismo criterio."""
    ANCHO, ALTO = 0.05, (0.22, 0.25, 0.28, 0.22, 0.25, 0.28)
    for i in range(6):
        w = max(3, int(round(ANCHO / 0.012)))
        h = max(10, int(round(ALTO[i] / 0.012)))
        obj = (0.34, 0.26, 0.44, 0.30, 0.40, 0.28)[i]
        guardar(lomo(w, h, 40 + i), "SHELF_BOOK_%02d" % (i + 1), albedo=obj)
    print("LOMOS DEL ESTANTE OESTE")
    print("  6 lomos de %dx%d a %dx%d texels" % (4, 18, 4, 23))


if __name__ == "__main__":
    main()
    lomos_oeste()
    consolas_y_hojas()
