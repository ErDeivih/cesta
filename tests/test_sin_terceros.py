"""Ninguna de las dos interfaces llama a un tercero.

Esta aplicacion se sirve **desde casa**: el PC del salon, por Tailscale, para dos
personas. Todo lo que se cargue de fuera no es solo una dependencia: es que alguien
de fuera se entera de que se ha abierto, cuando y desde que IP.

La interfaz vieja cargaba la tipografia de `fonts.googleapis.com`. O sea que **cada
vez que se abria Cesta, Google se enteraba**, y la tipografia ademas no pintaba
hasta que contestara un servidor ajeno. Se quito el 23 de septiembre de 2026: las
dos interfaces usan la fuente del sistema, que pinta antes y no avisa a nadie.

Esto no se ve en pantalla y no da ningun error: si alguien vuelve a pegar el
`<link>`, todo sigue funcionando igual de bien y de rapido, y la fuga vuelve. Por
eso esta prueba.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "plataforma" / "web"
APP = WEB / "app"

# Lo que se sirve desde el propio origen no cuenta: `estilo.css`, `app.js` y los
# ficheros de `dist` son nuestros.
PROPIOS = ("estilo.css", "app.js", "index.html")

SOSPECHOSO = re.compile(
    r"""(?:src|href)\s*=\s*["'](https?:)?//(?!127\.0\.0\.1|localhost)[^"']+""",
    re.I)


@pytest.mark.skipif(not WEB.exists(), reason="esta copia no trae la interfaz")
def test_la_interfaz_vieja_no_carga_nada_de_fuera():
    """La que esta sirviendose en produccion hoy."""
    culpables = []
    for fichero in sorted(WEB.glob("*.html")) + sorted(WEB.glob("*.css")):
        for linea, texto in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            for encontrado in SOSPECHOSO.findall(texto):
                culpables.append(f"{fichero.name}:{linea}: {encontrado}")
            # `@import url(https://...)` en CSS no lleva `src=` ni `href=`.
            if fichero.suffix == ".css" and re.search(r"@import\s+(url\()?['\"]?https?://", texto):
                culpables.append(f"{fichero.name}:{linea}: @import de fuera")
    assert not culpables, (
        "la interfaz carga algo de un tercero. Esta aplicacion se sirve desde "
        "casa: cada carga es que alguien de fuera sabe que se ha abierto, cuando y "
        "desde donde.\n  " + "\n  ".join(culpables))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_nueva_tampoco():
    """Y la que va a sustituirla, que ya nace sin nada de fuera."""
    culpables = []
    for fichero in sorted(APP.rglob("*.html")) + sorted(APP.rglob("*.css")):
        if "node_modules" in fichero.parts or "dist" in fichero.parts:
            continue
        for linea, texto in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            for encontrado in SOSPECHOSO.findall(texto):
                culpables.append(f"{fichero.name}:{linea}: {encontrado}")
    assert not culpables, (
        "la interfaz nueva carga algo de un tercero:\n  " + "\n  ".join(culpables))
