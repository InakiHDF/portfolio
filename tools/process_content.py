"""
PROCESADO DE IMAGENES DE CONTENIDO
==================================

Toma las imagenes que elige el usuario (tapas de disco, afiches, fotos) y las
deja en condiciones de convivir con el resto de la habitacion.

No es "pixelar" en el sentido de agrandar pixeles: es REDUCIR la imagen a la
cantidad de pixeles que realmente va a ocupar en pantalla, y reducir tambien
la cantidad de colores. Lo que se ve como pixel es el pixel real de la
textura, no un filtro encima.

Cadena, en orden:

  1. Recorte al alto por ancho exacto del hueco. Nunca se deforma.
  2. Curva de tono: mas contraste, menos saturacion, y un corrimiento
     calido, porque en la habitacion todo esta bajo luz de tungsteno y un
     blanco puro grita.
  3. Reduccion de tamano con filtro de area.
  4. Cuantizacion a pocos colores con dither ordenado de Bayer. El dither
     ordenado lee como decision de epoca; el de difusion de error lee como
     jpeg mal guardado.
  5. Borde: el canto del papel o de la funda, apenas mas oscuro.

Uso:
  python3 tools/process_content.py hoja      # arma la hoja de comparacion
  python3 tools/process_content.py vinilos   # procesa los 84 vinilos
"""

import os
import sys
import glob

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_VINYL = os.path.join(REPO, "Sprites", "Vinilos")
SRC_POSTER = os.path.join(REPO, "Sprites", "Posters")
OUT = os.path.join(REPO, "blender", "textures", "content")

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=np.float32) / 64.0 - 0.5


# ---------------------------------------------------------------------------

def crop_to_aspect(img, aspect):
    """Recorta centrado hasta la proporcion pedida. No deforma nunca."""
    w, h = img.size
    if w / h > aspect:
        new_w = int(round(h * aspect))
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    new_h = int(round(w / aspect))
    top = int((h - new_h) * 0.42)          # un poco arriba del centro
    return img.crop((0, top, w, top + new_h))


def tone(a, contrast, saturation, warm, lift):
    """Curva de tono. `a` en 0..1."""
    a = (a - 0.5) * contrast + 0.5
    gris = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    a = gris[..., None] + (a - gris[..., None]) * saturation
    a = a * np.array(warm, dtype=np.float32)
    a = a * (1.0 - lift) + lift
    return np.clip(a, 0.0, 1.0)


def quantize(a, colors, dither):
    """Paleta adaptada a la propia imagen, con dither ordenado."""
    h, w, _ = a.shape
    pil = Image.fromarray((a * 255).astype(np.uint8))
    pal_img = pil.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                           dither=Image.Dither.NONE)
    pal = np.array(pal_img.getpalette()[:colors * 3],
                   dtype=np.float32).reshape(-1, 3) / 255.0

    if dither:
        tile = np.tile(BAYER8, (h // 8 + 1, w // 8 + 1))[:h, :w]
        # El paso tiene que ser la distancia al color VECINO de la paleta, no
        # la dispersion total: con la dispersion el dither tapa la imagen.
        dd = ((pal[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        np.fill_diagonal(dd, 1e9)
        paso = float(np.median(np.sqrt(dd.min(axis=1)))) * 0.55
        a = np.clip(a + tile[..., None] * paso, 0.0, 1.0)

    d = ((a.reshape(-1, 1, 3) - pal.reshape(1, -1, 3)) ** 2).sum(axis=2)
    return pal[d.argmin(axis=1)].reshape(h, w, 3)


def edge(a, fuerza=0.35):
    """Oscurece el canto: el borde del papel nunca es del color del centro."""
    h, w, _ = a.shape
    m = np.ones((h, w), dtype=np.float32)
    m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = 1.0 - fuerza
    if h > 3 and w > 3:
        m[1, 1:-1] = m[-2, 1:-1] = np.minimum(m[1, 1:-1], 1.0 - fuerza * 0.45)
        m[1:-1, 1] = m[1:-1, -2] = np.minimum(m[1:-1, 1], 1.0 - fuerza * 0.45)
    return a * m[..., None]


# La regla no es "que el texel coincida con el pixel de pantalla": eso da
# nitidez. Es al reves. Cada texel tiene que ocupar VARIOS pixeles de
# pantalla para que el bloque se vea. El divisor de cada nivel es cuantos
# pixeles de pantalla mide un texel.
PRESETS = {
    # nombre: (lado, colores, dither, contraste, saturacion, calido, lift)
    "R40": (40, 12, True, 1.30, 0.82, (1.05, 1.00, 0.93), 0.030),
    "R28": (28, 8, True, 1.45, 0.74, (1.07, 1.00, 0.91), 0.040),
    "R20": (20, 6, True, 1.60, 0.66, (1.09, 1.00, 0.89), 0.050),
    "R14": (14, 4, False, 1.85, 0.56, (1.11, 1.00, 0.86), 0.060),
    # Un escalon menos que R20, para los vinilos: se entiende algo mas
    # de que es cada tapa sin salirse del resto de la habitacion.
    "VINILO": (32, 10, True, 1.34, 0.80, (1.05, 1.00, 0.92), 0.034),
}

# pixeles de pantalla por texel, para cada nivel
TEXEL_PX = {"R40": 2.6, "R28": 3.7, "R20": 5.2, "R14": 7.4, "VINILO": 3.4}


def process(path, aspect, preset, out_size=None):
    lado, colores, dith, con, sat, warm, lift = PRESETS[preset]
    img = Image.open(path).convert("RGB")
    img = crop_to_aspect(img, aspect)
    w = lado
    h = max(1, int(round(lado / aspect)))
    img = img.resize((w, h), Image.BOX)

    a = np.asarray(img, dtype=np.float32) / 255.0
    a = tone(a, con, sat, warm, lift)
    a = quantize(a, colores, dith)
    a = edge(a)

    out = Image.fromarray((a * 255).astype(np.uint8))
    if out_size:
        out = out.resize(out_size, Image.NEAREST)
    return out


# ---------------------------------------------------------------------------

def hoja(escala=3, sufijo="", real=False):
    """Hoja de comparacion.

    escala: cuanto se amplia (con nearest) para ver la estructura de pixel.
    real:   si es True, cada muestra se dibuja al tamano que de verdad va a
            tener en pantalla. Es la unica forma honesta de juzgar."""
    muestras = [
        ("Poster_west_01.jpg", SRC_POSTER, 66.0 / 114.0),
        ("Poster_west_05.jpg", SRC_POSTER, 54.0 / 72.0),
        ("003 - Kendrick Lamar - To Pimp a Butterfly.jpg", SRC_VINYL, 1.0),
        ("006 - Radiohead - In Rainbows.jpg", SRC_VINYL, 1.0),
        ("014 - Madvillain - Madvillainy.jpg", SRC_VINYL, 1.0),
    ]
    cel = 300 if not real else 130
    pad = 10
    cols = 1 + len(PRESETS)
    hoja_img = Image.new("RGB", (cols * cel + (cols + 1) * pad,
                                 len(muestras) * cel + (len(muestras) + 1) * pad),
                         (26, 26, 28))
    for r, (nombre, carpeta, aspect) in enumerate(muestras):
        path = os.path.join(carpeta, nombre)
        alto = int(cel / aspect) if aspect < 1 else cel
        ancho = cel if aspect >= 1 else int(cel * aspect)
        ancho, alto = (cel, int(cel / aspect)) if aspect >= 1 else (int(cel * aspect), cel)
        ancho, alto = min(ancho, cel), min(alto, cel)

        orig = crop_to_aspect(Image.open(path).convert("RGB"), aspect)
        orig = orig.resize((ancho, alto), Image.LANCZOS)
        y = pad + r * (cel + pad) + (cel - alto) // 2
        hoja_img.paste(orig, (pad + (cel - ancho) // 2, y))

        for c, preset in enumerate(PRESETS):
            im = process(path, aspect, preset, out_size=(ancho, alto))
            hoja_img.paste(im, (pad + (c + 1) * (cel + pad) + (cel - ancho) // 2, y))

    dest = os.path.join(REPO, "blender", "renders", "HOJA_CONTENIDO%s.png" % sufijo)
    hoja_img.save(dest)
    print("hoja:", dest)
    print("columnas: original |", " | ".join(PRESETS))


def lote(carpeta, aspect, preset, prefijo):
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for path in sorted(glob.glob(os.path.join(carpeta, "*.jpg")) +
                       glob.glob(os.path.join(carpeta, "*.png"))):
        base = os.path.splitext(os.path.basename(path))[0]
        process(path, aspect, preset).save(
            os.path.join(OUT, "%s_%s.png" % (prefijo, base.replace(" ", "_"))))
        n += 1
    print("procesadas %d imagenes -> %s" % (n, OUT))


# Tapas que Inaki no quiere ver, aunque el archivo siga en la carpeta.
# Se excluyen aca en vez de borrar el original: es reversible y queda escrito.
EXCLUIDOS = ("White Pony",)


def lote_vinilos():
    """Todo el pool, al mismo nivel y al mismo tamano."""
    os.makedirs(OUT, exist_ok=True)
    for viejo in glob.glob(os.path.join(OUT, "POOL_*.png")):
        os.remove(viejo)
    n, fuera = 0, 0
    for path in sorted(glob.glob(os.path.join(SRC_VINYL, "*.jpg"))):
        base = os.path.splitext(os.path.basename(path))[0]
        if any(e.lower() in base.lower() for e in EXCLUIDOS):
            fuera += 1
            continue
        process(path, 1.0, "VINILO").save(
            os.path.join(OUT, "POOL_%s.png" % base.replace(" ", "_")))
        n += 1
    print("pool de vinilos: %d imagenes a 32x32, 10 colores (%d excluidas)"
          % (n, fuera))


# Cada poster con su fuente y su nivel. `px_por_texel` mas bajo = mas
# definicion. Las obras que Inaki quiere que se lean van mas finas.
POSTERS = {
    # nombre:            (archivo, px_por_texel, colores, contraste, saturacion)
    "POSTER_WEST_01": ("Posters/Poster_west_01.jpg", 5.2, 8, 1.55, 0.70),
    "POSTER_WEST_02": ("Dancers apaisado.png",       2.4, 20, 1.16, 0.88),
    "POSTER_WEST_03": ("Posters/Poster_west_03.jpg", 5.2, 8, 1.55, 0.70),
    "POSTER_WEST_04": ("Lilies.jpg",                 2.6, 18, 1.18, 0.90),
    "POSTER_WEST_05": ("Posters/Poster_west_05.jpg", 3.0, 14, 1.30, 0.78),
}


def lote_posters():
    """Cada poster a la resolucion que le toca por su tamano en pantalla."""
    import json
    huecos = json.load(open(os.path.join(REPO, "docs", "huecos.json")))
    raiz = os.path.join(REPO, "Sprites")
    for nombre, (arch, ppt, colores, con, sat) in POSTERS.items():
        src = os.path.join(raiz, arch)
        if nombre not in huecos or not os.path.exists(src):
            print("  falta:", nombre, arch)
            continue
        d = huecos[nombre]
        lado = max(12, int(round(d["px_pantalla"] / ppt / 2.0)) * 2)
        PRESETS["AUTO"] = (lado, colores, True, con, sat, (1.05, 1.00, 0.93), 0.030)
        im = process(src, d["proporcion"], "AUTO")
        im.save(os.path.join(OUT, nombre + ".png"))
        print("  %-16s %3d px pantalla / %.1f -> %dx%d texels, %d colores"
              % (nombre, d["px_pantalla"], ppt, im.size[0], im.size[1], colores))


# Que tapa va en cada libro visible. Solo los del centro: el resto de los
# libros de la escena muestran el lomo, no la tapa.
LIBROS = {
    "BOOK_TABLE_01":       "04.png",
    "BOOK_TABLE_02":       "08.png",
    "MAGAZINE_TABLE_01":   "09.png",
    "BOOK_FLOOR_STACK_01": "07.png",
    "BOOK_FLOOR_STACK_02": "02.png",
    "BOOK_FLOOR_STACK_03": "05.png",
}


def lote_libros():
    """Tapas sobre los libros del centro.

    Detalle importante: la tapa es vertical (2:3) y el libro acostado en la
    mesa es apaisado. Recortar la tapa a apaisado la destruye. Se la gira 90
    grados, que ademas es lo natural: un libro apoyado queda como cae."""
    import json
    huecos = json.load(open(os.path.join(REPO, "docs", "huecos.json")))
    origen = os.path.join(REPO, "Sprites", "Libros_norm")
    for nombre, archivo in LIBROS.items():
        src = os.path.join(origen, archivo)
        if nombre not in huecos or not os.path.exists(src):
            print("  falta:", nombre, archivo)
            continue
        d = huecos[nombre]
        lado = max(14, int(round(d["px_pantalla"] / 3.0 / 2.0)) * 2)
        PRESETS["AUTO"] = (lado, 14, True, 1.24, 0.86, (1.04, 1.00, 0.94), 0.028)

        img = Image.open(src).convert("RGB")
        if (img.width / img.height < 1.0) != (d["proporcion"] < 1.0):
            img = img.transpose(Image.ROTATE_90)
        tmp = os.path.join(OUT, "_tmp.png")
        img.save(tmp)
        im = process(tmp, d["proporcion"], "AUTO")
        os.remove(tmp)
        im.save(os.path.join(OUT, nombre + ".png"))
        print("  %-22s %3d px -> %dx%d texels  <- %s"
              % (nombre, d["px_pantalla"], im.size[0], im.size[1], archivo))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "hoja"
    if cmd == "hoja":
        hoja(sufijo="_ampliada")
        hoja(sufijo="_real", real=True)
    elif cmd == "vinilos":
        lote_vinilos()
    elif cmd == "posters":
        lote_posters()
    elif cmd == "libros":
        lote_libros()
    else:
        print(__doc__)
