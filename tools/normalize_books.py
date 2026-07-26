"""
NORMALIZAR LAS TAPAS DE LIBROS
==============================

Las diez imagenes vienen de fuentes distintas: algunas traen borde blanco,
otras estan recortadas fuera de proporcion, y las hay de 172 px de ancho.

  1. Se recorta el borde uniforme (marco blanco o negro) si lo hay.
  2. Se lleva todo a 2:3, la proporcion de una tapa de libro.
  3. Se sube todo a 1000x1500 para partir siempre del mismo lugar.

Escribe Sprites/Libros_norm/.
"""

import os
import glob

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "Sprites", "Libros")
DST = os.path.join(REPO, "Sprites", "Libros_norm")
ASPECTO = 2.0 / 3.0


def sin_borde(img, tol=24):
    """Saca el marco uniforme. Mira si cada fila/columna del borde es casi
    de un solo color y ademas parecida a la esquina."""
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    h, w, _ = a.shape
    esquina = a[0, 0].astype(np.float32)

    def uniforme(linea):
        return (np.abs(linea - linea.mean(axis=0)).mean() < tol and
                np.abs(linea.mean(axis=0) - esquina).mean() < tol * 2.2)

    top, bot, izq, der = 0, h - 1, 0, w - 1
    while top < h // 3 and uniforme(a[top]):
        top += 1
    while bot > 2 * h // 3 and uniforme(a[bot]):
        bot -= 1
    while izq < w // 3 and uniforme(a[:, izq]):
        izq += 1
    while der > 2 * w // 3 and uniforme(a[:, der]):
        der -= 1
    if der - izq < w * 0.4 or bot - top < h * 0.4:
        return img, 0
    recortado = (top + (h - 1 - bot) + izq + (w - 1 - der))
    return img.crop((izq, top, der + 1, bot + 1)), recortado


def a_proporcion(img, aspecto):
    w, h = img.size
    if w / h > aspecto:
        nw = int(round(h * aspecto))
        return img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = int(round(w / aspecto))
    top = int((h - nh) * 0.30)
    return img.crop((0, top, w, top + nh))


def main():
    os.makedirs(DST, exist_ok=True)
    fuentes = sorted(f for f in glob.glob(os.path.join(SRC, "*"))
                     if not os.path.basename(f).startswith("."))
    for i, f in enumerate(fuentes, 1):
        im = Image.open(f).convert("RGB")
        antes = im.size
        # Dos pasadas: al sacar un borde suele aparecer otro debajo.
        im, r1 = sin_borde(im)
        im, r2 = sin_borde(im)
        recorte = r1 + r2
        im = a_proporcion(im, ASPECTO)
        im = im.resize((1000, 1500), Image.LANCZOS)
        titulo = os.path.splitext(os.path.basename(f))[0]
        im.save(os.path.join(DST, "%02d.png" % i))
        print("  %02d  %-46s %4dx%-4d -> 1000x1500  borde recortado: %d px"
              % (i, titulo[:44], antes[0], antes[1], recorte))
    print("\n%d tapas normalizadas en %s" % (len(fuentes), DST))


if __name__ == "__main__":
    main()
