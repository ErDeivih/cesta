"""Los ficheros de texto: sin marca al principio y sin doble codificado.

Por que existe
--------------
El 23 de septiembre de 2026 aparecio `docs/CIERRE-ENCARGO-UX.md` con las comillas angulares
convertidas en dos caracteres cada una -- se leia `\u00c2\u00ab\u00c2\u00bfesto esta caro?\u00c2\u00bb`
donde tenia que leerse `«¿esto esta caro?»` -- y `docs/OPERACION.md` con
`s\u00c3\u00b3lo` donde tenia que decir `sólo`. (Los ejemplos van con escapes a proposito:
este fichero tiene que pasar su propia regla, y escrito con los caracteres de verdad no la
pasaria.) Los dos venian de renglones escritos con PowerShell: el texto se leyo como
Latin-1 y se volvio a escribir como UTF-8, asi que cada byte acabo siendo **dos**
caracteres. Y los dos empezaban por una marca invisible (U+FEFF) que no llevaba ningun otro
fichero del repositorio.

Nada de eso rompe la aplicacion, y por eso vivio ahi sin que nadie lo viera. Rompe **lo que
se lee**, que en este proyecto es la mitad del trabajo: quien abre el documento ve
`\u00c2\u00ab` y deja de fiarse de lo que pone dentro. Es el mismo tipo de fallo que el contraste medido sobre
nada (`plataforma/prueba_navegador.py`): un instrumento o un documento que miente sin
avisar.

Que se comprueba
----------------
Dos reglas, sobre los ficheros de texto del repositorio:

1. **Ninguno empieza por U+FEFF.** En un `.py` puede romper herramientas que leen bytes
   (un `python fichero.py` con marca funciona, pero un shebang no); en un documento es la
   huella de que ha pasado por PowerShell, que es exactamente el camino por el que llego el
   doble codificado. `plataforma/web/estilo.css` tenia una y se le quito en el mismo commit.
2. **Ninguno lleva doble codificado**: un caracter de la familia `Â`/`Ã` (U+00C2, U+00C3)
   pegado a otro de la banda 0x80-0xBF. Esa pareja no aparece escribiendo castellano de
   verdad ni con acentos ni con comillas angulares: es siempre un byte leido dos veces.

Lo que **no** se comprueba, a proposito: los saltos de linea. Hay ficheros antiguos en CRLF
(`core/matching.py`, `docs/CIFRAS.md`, `docs/DIAGNOSTICO-MATCHING.md`), estan asi en el
repositorio desde antes de esto, y normalizarlos seria un diff enorme que no arregla nada
de lo que se ve en la pantalla.
"""
from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Lo que se lee como texto. Las imagenes, los parquet y los zip no entran: no son texto.
SUFIJOS = {".py", ".md", ".ts", ".tsx", ".css", ".sql", ".yml", ".yaml", ".json",
           ".toml", ".txt", ".bat", ".html", ".js"}
# Y lo que no se mira aunque tenga uno de esos sufijos: lo instala o lo genera otro.
CARPETAS = {"node_modules", ".git", ".venv", "venv", "data", "dist", "build",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

# La firma del doble codificado: `Â` o `Ã` seguidos de un caracter de la banda 0x80-0xBF.
# `re` sobre `str` trabaja con puntos de codigo, no con bytes, asi que se escribe con
# escapes y no con los caracteres de verdad: este fichero tambien tiene que pasar la regla.
DOBLE = re.compile("[\u00c2\u00c3][\u0080-\u00bf]")


def ficheros() -> list[pathlib.Path]:
    """Los ficheros de texto del repositorio, sin los que genera otro programa."""
    fuera = []
    for ruta in sorted(RAIZ.rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in SUFIJOS:
            continue
        if CARPETAS.intersection(ruta.parts):
            continue
        fuera.append(ruta)
    return fuera


def doble_codificado(texto: str) -> list[str]:
    """Las parejas de doble codificado que hay en un texto."""
    return DOBLE.findall(texto)


def test_el_detector_ve_el_doble_codificado() -> None:
    """La prueba de que la medida mira.

    Sin esto, un cero puede querer decir "todo bien" o "no he leido nada", y las dos cosas
    se escriben igual en el informe. Es la leccion de la trampa del contraste, aplicada a
    un fichero en vez de a una pantalla.
    """
    malo = "la frase de \u00c2\u00ab\u00c2\u00bfesto esta caro?\u00c2\u00bb no estaba"
    assert doble_codificado(malo)
    assert doble_codificado("la frase de «¿esto esta caro?» si estaba") == []
    # Y con acentos de verdad, que es lo que un fichero sano lleva:
    assert doble_codificado("un enlace que caduca, y sólo existe en ese fichero") == []


def test_ningun_fichero_lleva_doble_codificado() -> None:
    culpables = []
    for ruta in ficheros():
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        if parejas := doble_codificado(texto):
            linea = next((n for n, renglon in enumerate(texto.splitlines(), 1)
                          if doble_codificado(renglon)), 0)
            culpables.append(f"{ruta.relative_to(RAIZ)}:{linea} ({len(parejas)} parejas)")
    assert not culpables, (
        "hay texto doble codificado (se leyo como Latin-1 y se escribio como UTF-8): "
        + "; ".join(culpables[:5]))


def test_ningun_fichero_empieza_por_marca() -> None:
    culpables = [str(r.relative_to(RAIZ)) for r in ficheros()
                 if r.read_bytes()[:3] == b"\xef\xbb\xbf"]
    assert not culpables, ("hay ficheros que empiezan por U+FEFF (la marca que deja "
                           "PowerShell al escribir): " + ", ".join(culpables[:5]))
