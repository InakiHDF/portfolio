#!/usr/bin/env python3
"""
El servidor de desarrollo de la página.

Es `python3 -m http.server` con una sola diferencia: manda `no-store` en todo.

Sin eso el navegador se queda con la copia vieja de cualquier archivo que no
lleve `?v=` colgado, y eso son casi todos: `index.html`, `avatar.js`,
`contenido.js`, el GLB de la habitación, las texturas. Edita uno, recarga, y la
página sigue siendo la de antes — parece que el cambio no hizo nada. Ya pasó
con el avatar (por eso `tools/avatar.sh` inventó la versión en `poses.json`) y
vuelve a pasar con cada módulo nuevo.

Esto es sólo para trabajar en local. En producción el `?v=` sigue siendo la
forma correcta de invalidar.

    python3 tools/servidor.py [puerto] [carpeta]
"""

import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler


class SinCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    carpeta = sys.argv[2] if len(sys.argv) > 2 else "web"
    manejador = partial(SinCache, directory=carpeta)
    print(f"sirviendo {carpeta}/ en http://localhost:{puerto} — sin caché")
    HTTPServer(("", puerto), manejador).serve_forever()


if __name__ == "__main__":
    main()
