"""Extrae paletas de las imagenes de referencia, por region.

No inventa colores: los saca de las mismas fotos que definen el proyecto.
Para cada region recorta, cuantiza y devuelve los colores dominantes con su
peso, mas una hoja de contacto para verificar que la region es la correcta.
"""
import os
import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# nombre -> (archivo, caja de recorte)
REGIONES = {
    "PISO":        ("Front.png", (600, 780, 1100, 930)),
    "PARED":       ("Front.png", (250, 150, 900, 430)),
    "MADERA":      ("Right.png", (700, 400, 1150, 520)),
    "TELA_CAMA":   ("Front.png", (560, 590, 1120, 720)),
    "ALFOMBRA":    ("Top.png", (600, 300, 1050, 560)),
    "METAL":       ("Back.png", (1150, 330, 1350, 470)),
    "HORMIGON":    ("Back.png", (150, 430, 420, 640)),
    "ESTANTE":     ("Back.png", (1200, 470, 1560, 640)),
}


def dominantes(img, n=6):
    q = img.convert("RGB").quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:n * 3]).reshape(-1, 3)
    cuenta = np.bincount(np.asarray(q).ravel(), minlength=n)
    orden = np.argsort(-cuenta)
    total = cuenta.sum()
    return [(tuple(int(v) for v in pal[i]), cuenta[i] / total) for i in orden]


def main():
    cel = 220
    hoja = Image.new("RGB", (cel * len(REGIONES), cel + 60), (18, 18, 20))
    print("REGION        peso  color            hex")
    for k, (nombre, (archivo, caja)) in enumerate(REGIONES.items()):
        im = Image.open(os.path.join(REPO, archivo)).crop(caja)
        hoja.paste(im.resize((cel, cel)), (k * cel, 0))
        cols = dominantes(im)
        for i, (c, w) in enumerate(cols[:4]):
            hoja.paste(Image.new("RGB", (cel // 4, 60), c),
                       (k * cel + i * (cel // 4), cel))
        print("%-12s" % nombre, " ".join("%.2f #%02x%02x%02x" % (w, *c) for c, w in cols[:4]))
    dest = os.path.join(REPO, "blender", "renders", "PALETA_REFERENCIA.png")
    hoja.save(dest)
    print("\nhoja:", dest)


main()
