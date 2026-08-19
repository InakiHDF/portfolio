#!/usr/bin/env python3
"""
LOS LOGOS DE LOS SITIOS
=======================

Un favicon no es un logo: es un cuadradito pensado para 16 px en una pestaña.
Los tres logos de la sección Web se arman acá, a partir de los archivos que
manda cada sitio, y `fetch_contenido.py` los respeta (ver `LOGOS_A_MANO`).

    python3 tools/procesar_logos.py

Los tres salen en PNG con transparencia y RECORTADOS al contenido: el dibujo
del monitor los escala por área (`AREA_LOGO` en `sala.js`) y cualquier margen
transparente que sobreviva acá contaría como parte del logo y lo dejaría más
chico que los otros.

Van claros porque el monitor es oscuro. Ojo con esto si alguna vez vuelve una
placa clara detrás: un crema sobre un crema no se ve.
"""

import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ                      # donde caen los archivos originales
DESTINO = RAIZ / "web" / "contenido" / "logos"
CREMA = (244, 235, 223)             # F4EBDF
MAX_LADO = 900                      # el monitor lo dibuja a ~350 px de ancho


def terminar(im, nombre):
    """Recorta al contenido, achica si hace falta y guarda."""
    caja = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(caja)
    if max(im.size) > MAX_LADO:
        e = MAX_LADO / max(im.size)
        im = im.resize((round(im.size[0] * e), round(im.size[1] * e)), Image.LANCZOS)
    DESTINO.mkdir(parents=True, exist_ok=True)
    im.save(DESTINO / nombre, "PNG", optimize=True)
    w, h = im.size
    print(f"  {nombre}: {w}×{h}  proporción {w / h:.2f}")


def helicopters(src):
    """Ya viene bien: amarillo sobre transparente. Sólo cambia de contenedor."""
    terminar(Image.open(src).convert("RGBA"), "helicopters.png")


def cru(src):
    """El trazo viene negro y va crema.

    La forma y el suavizado de los bordes están enteros en el canal alfa, así
    que se conserva tal cual y sólo se reemplaza el RGB. Teñir píxel por píxel
    según el color de origen no haría falta: es un solo negro plano.
    """
    im = Image.open(src).convert("RGBA")
    tenido = Image.new("RGBA", im.size, CREMA + (0,))
    tenido.putalpha(im.getchannel("A"))
    terminar(tenido, "cru.png")


def opus(src):
    """Viene opaco y cuadrado: hay que sacarle el fondo y dejar la O y el punto.

    El fondo no es un negro plano —tiene una textura que llega a luminancia 30—
    y la marca recién empieza en 45: entre medio hay un valle limpio donde
    cortar. Cada píxel del borde es el color de la marca mezclado contra ese
    fondo casi negro, o sea que su luminancia ES cuánto le corresponde de alfa.

    Son DOS colores planos, la O en crema y el punto en dorado, y el dorado es
    bastante más oscuro. Medidos los dos contra la misma referencia, el punto
    quedaba a media transparencia y se veía gris; cada uno se mide contra el
    suyo. El tinte sobrevive a la mezcla contra negro, así que sirve para
    separarlos también en los píxeles del borde, no sólo en los del centro.
    """
    CLARO, DORADO = (245, 241, 234), (201, 169, 97)
    L_CLARO, L_DORADO, L_FONDO = 236, 167, 30

    src_im = Image.open(src).convert("RGB")
    w, h = src_im.size
    px = src_im.load()
    out = Image.new("RGBA", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            luz = (r * 299 + g * 587 + b * 114) // 1000
            if luz <= L_FONDO:
                op[x, y] = (0, 0, 0, 0)
                continue
            es_dorado = (r - b) > 0.2 * max(r, 1)
            color, ref = (DORADO, L_DORADO) if es_dorado else (CLARO, L_CLARO)
            a = round((luz - L_FONDO) * 255 / (ref - L_FONDO))
            op[x, y] = color + (max(0, min(255, a)),)

    # La marca ocupa 271×228 de los 512 del original: al doble queda a la
    # altura de los otros dos, que vienen de archivos mucho más grandes.
    terminar(out.resize((w * 2, h * 2), Image.LANCZOS), "opus.png")


RECETAS = [
    (helicopters, "logoHelicopters.webp"),
    (cru, "00_CRU_LOGO_BLACK.png"),
    (opus, "logo-opus-fondo.png"),
]


def main():
    print("logos:")
    faltan = []
    for receta, archivo in RECETAS:
        src = FUENTES / archivo
        if not src.exists():
            faltan.append(archivo)
            continue
        receta(src)
    if faltan:
        print("\nno estaban, se dejaron como estaban: " + ", ".join(faltan))
        print(f"(se buscan en {FUENTES})")
    return 1 if len(faltan) == len(RECETAS) else 0


if __name__ == "__main__":
    sys.exit(main())
