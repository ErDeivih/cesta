"""**La comprobacion de la seccion 17 de `docs/ui/COMO-SE-MIDE.md`.**

*Consolidar un documento no lo mantiene vivo: **lo fotografia.** Y una foto es
cierta el dia que se hace, y no despues. El documento no se queda obsoleto por
descuido: **se queda obsoleto porque el trabajo sigue.**

Este script busca, en los documentos **vigentes**, las frases y los numeros que
el trabajo posterior dejo atras. Nacio de un caso real: el `RESUMEN VIGENTE` del
dictamen decia «paso de 19 ok a **177 ok**» cuando la puerta ya daba **194**, y
dos secciones del dictamen seguian diciendo que «la seccion de los toques no
llega al final» cuando ya llegaba. **Las tres frases estaban en la primera
pagina del entregable.**

**Y la leccion que lo justifica**: el script que las dejo atras buscaba un bloque
exacto y lo sustituyo, y **habia dos sitios con el mismo numero**. Es el mismo
error que las 22 lineas de la ronda 29: **arreglar un sitio y no su vecino.**
Por eso esto no es un corrector de estilo: es la unica forma de que la regla
**se corra**.

Uso: `uv run python -m plataforma.comprueba_documentos`

Sale con 0 si los documentos vigentes estan limpios, y con 1 si no. El historico
**no se mira**: ahi las frases viejas son el registro, y valen.
"""

from __future__ import annotations

import contextlib
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Los documentos que AFIRMAN un estado. El historico no esta aqui a proposito.
VIGENTES = (
    "docs/DICTAMEN.md",
    "docs/ui/ESTADO-FASE-5.md",
    "docs/ui/VERSION-SERVIDA.md",
    "docs/ui/COMO-SE-MIDE.md",
)

# **Las frases que el trabajo posterior deja atras.** Y hay que ser ESTRECHO:
# *un comprobador que avisa de todo **no se corre**, y entonces no comprueba
# nada.* Por eso aqui NO estan «NO HECHO» ni «no se puede verificar»: los dos
# aparecen **legitimamente** *(-- *diciendo que algo sigue sin hacerse, *o
# citando la regla --)*. Lo que se busca es *** el numero de la puerta cuando ya
# no es el suyo***.
VIEJAS = re.compile(
    r"\b19 ok\b|\b87 ok\b|\b177 ok\b|\b190 ok\b|\b194 ok\b"
    r"|no llega al final"
    # **Y el censo de `pytest`**, *que cambio al anadir las pruebas de documentos:*
    # *2081 -> 2083. *Sin esto, **la comprobacion solo miraba lo que se me
    # ocurrio mirar**, *que es el defecto que vino a arreglar.*
    r"|\b2081 passed\b|\b206 ok\b"
)

# **Y los numeros de hoy**, para no acusar a la linea que dice el bueno: *la frase
# «paso de 19 ok a 194 ok» es **la correcta**, y sin esto se acusaba a si misma.*
#
# **Y va una lista, *no uno*.** *Porque esto ya paso: al subir la puerta de 194 a
# 206 se puso `206` y **se dejo `194` aqui**, *y la frase que dice los dos numeros
# **volvio a acusarse a si misma**.* *Es el mismo defecto que este fichero vino a
# arreglar, **un escalon mas abajo** -- y por eso ahora son varios, y crecen con la
# puerta.* *Si el numero de hoy no esta aqui, **la comprobacion se queja de la
# frase que dice la verdad**, y entonces se deja de correr.*
BUENO = re.compile(r"\b194 ok\b|\b206 ok\b|\b212 ok\b")

# En el dictamen, el historico empieza aqui y NO se mira: sus frases viejas son
# el registro de como se llego, y eso es lo que se quiere conservar.
CORTE_HISTORICO = "# PARTE 4"

# **Y en `COMO-SE-MIDE.md`, la seccion 17 es LA REGLA**, *y una regla tiene que
# citar los patrones que busca: «NO HECHO», «177 ok»... Asi que se mira hasta
# donde empieza, y no ella. *Sin esto el script **se acusa a si mismo**, que es
# lo que paso la primera vez que se corrio.*
CORTE_REGLA = ("docs/ui/COMO-SE-MIDE.md", "## 17.")


def _tramo(lines: list[str], fichero: str) -> tuple[int, int]:
    """El tramo vigente: sin el historico del dictamen ni la regla de la seccion 17."""
    corte = None
    if fichero.endswith("DICTAMEN.md"):
        corte = CORTE_HISTORICO
    elif fichero == CORTE_REGLA[0]:
        corte = CORTE_REGLA[1]
    if corte:
        for i, linea in enumerate(lines):
            if linea.startswith(corte):
                return 0, i
    return 0, len(lines)


def revisa(raiz: Path = RAIZ) -> list[tuple[str, int, str]]:
    """Devuelve (fichero, linea, texto) de cada frase vieja en un vigente."""
    malas: list[tuple[str, int, str]] = []
    for fichero in VIGENTES:
        ruta = raiz / fichero
        if not ruta.exists():
            malas.append((fichero, 0, "NO EXISTE"))
            continue
        lines = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        ini, fin = _tramo(lines, fichero)
        for i in range(ini, fin):
            if VIEJAS.search(lines[i]) and not BUENO.search(lines[i]):
                malas.append((fichero, i + 1, lines[i].strip()[:100]))
    return malas


def main() -> int:
    # **La consola de Windows es `cp1252`**, *y estas lineas llevan `✓` y tildes:
    # sin esto el script **peta al imprimir el diagnostico**, *que es justo cuando
    # mas falta hace que se lea.*
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    malas = revisa()
    for fichero in VIGENTES:
        cuantas = sum(1 for f, _, _ in malas if f == fichero)
        print(f"  {fichero}: {'LIMPIO' if not cuantas else str(cuantas) + ' SOSPECHOSAS'}")
        for f, n, texto in malas:
            if f == fichero:
                print(f"    l{n}: {texto}")
    if malas:
        print(
            "\n  **Y esto es lo que la seccion 17 dice que hay que hacer**:"
            "\n  *consolidar no es arreglar, es fotografiar. *Y el trabajo siguio:"
            "\n  *estas frases son de una foto anterior.\n"
        )
        return 1
    print("\n  == TODO BIEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
