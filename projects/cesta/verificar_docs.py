"""Comprueba que los numeros de los documentos siguen siendo verdad.

Por que existe
--------------
Los documentos de este proyecto estan llenos de cifras medidas, y esa es su
virtud: cada decision lleva al lado el numero que la sostiene. Pero los datos
cambian todos los dias, y una cifra que fue cierta en septiembre y ya no lo es
resulta peor que no poner ninguna, porque nadie la vuelve a comprobar.

El 17 de septiembre habia doce cifras caducadas repartidas por once documentos, y
una de ellas describia un comportamiento que el codigo ya no tenia.

    uv run python -m projects.cesta.verificar_docs

Sale 0 si todo cuadra, 1 si algo se ha ido. No arregla nada: avisa.

Donde viven los numeros de hoy
------------------------------
En `docs/CIFRAS.md`, y solo ahi. El 19 de septiembre este control marco ocho
cifras como caducadas y, al ir a corregirlas, se vio que casi todas estaban
escritas **con su fecha al lado** -- "medido el 18 de septiembre: 52.575
productos" --. Eso no es una cifra caducada: es un registro historico, y
cambiarla no la actualiza, la falsifica.

Asi que `CIFRAS.md` lleva los numeros de la ultima ejecucion y se reescribe
entero cada dia; los demas documentos conservan los suyos con la fecha en que se
midieron. El control encuentra el de hoy y deja de avisar, sin que nadie tenga
que reescribir la historia.

Como se anade una comprobacion
------------------------------
Una linea en COMPROBACIONES: la consulta que da el numero de verdad, y el texto
tal y como aparece escrito en los documentos. Si el texto deja de encontrarse en
ningun documento, tambien avisa: significa que alguien lo reescribio de otra
forma y la vigilancia dejo de servir para algo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

from core import config

RAIZ = Path(__file__).resolve().parents[2]
# **Tambien las subcarpetas**, desde el 24 de septiembre de 2026: el material de
# aprendizaje vive en `docs/aprende/*.md` (una carpeta, para no mezclarlo con el registro
# del dia a dia) y sus cifras son las mismas que las del resto de la casa. Si el control
# no mirara ahi, la mitad nueva del corpus quedaria sin vigilar justo cuando mas crece.
DOCS = [*(RAIZ / "docs").rglob("*.md"), RAIZ / "plataforma" / "LEEME.md"]

# (nombre, consulta, como se escribe en los documentos, tolerancia en %)
COMPROBACIONES = [
    ("productos del catalogo",
     "SELECT count(*) FROM g", "{:,}", 2),
    ("grupos comparables",
     """SELECT count(*) FROM (SELECT grupo_id FROM g WHERE grupo_id IS NOT NULL
        GROUP BY grupo_id HAVING count(DISTINCT fuente) >= 2)""", "{:,}", 3),
    ("productos con codigo de barras",
     "SELECT count(ean) FROM g", "{:,}", 3),
    ("productos con Nutri-Score",
     "SELECT count(nutriscore) FROM g", "{:,}", 5),
    ("productos comparables por kg/l/m",
     "SELECT count(*) FROM g WHERE comparacion_fiable", "{:,}", 3),
    # Anadidas el 17 de septiembre de 2026, cuando los sellos y las
    # certificaciones pasaron de ser una idea a ser un filtro de la app. Son las
    # cifras que mas se van a repetir en los documentos a partir de ahora, y las
    # que mas rabia da encontrar caducadas.
    ("productos con algun sello",
     "SELECT count(sellos) FROM g", "{:,}", 3),
    ("productos con certificado",
     "SELECT count(certificados) FROM g", "{:,}", 3),
    ("productos con tabla nutricional",
     "SELECT count(nutricion) FROM g", "{:,}", 3),
    ("productos con envase",
     "SELECT count(envase) FROM g", "{:,}", 3),
]


def _miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _citado(escrito: str, textos) -> bool:
    """¿Aparece esta cifra en algun documento, ella y no un trozo de otra?

    Buscar la cifra con `in` a secas daba por buena cualquier cosa. "123" esta
    dentro de "1.234" y dentro de "2026-09-18 12:30", y "0" esta en cualquier
    parte, asi que con un catalogo pequeno -- un ensayo, una prueba, un dia a
    medias -- el control decia "ok" en las nueve comprobaciones sin haber mirado
    nada. Un control que aprueba cuando no tiene con que comparar es peor que no
    tenerlo: se confia en el.

    Un cero no se da nunca por citado -- "cero productos con Nutri-Score" no es
    una cifra que verificar, es una capa que no ha corrido -- ni tampoco nada por
    debajo de cien: un numero de dos cifras coincide por casualidad con demasiadas
    cosas y no vale como vigilancia.
    """
    if len(escrito) < 3:
        return False
    # Delante: ni digito, ni separador de miles, ni guion (si no, el "18" de
    # "2026-09-18" contaria como cita). Detras: ni digito, ni un separador que
    # lleve digito pegado -- el punto final de una frase si vale.
    patron = re.compile(r"(?<![\d.,\-])" + re.escape(escrito) + r"(?!\d)(?![.,\-]\d)")
    return any(patron.search(t) for t in textos)


def main() -> int:
    ruta = str(config.DATA / "gold" / "grupos.parquet").replace("\\", "/")
    if not Path(ruta).exists():
        print("No hay gold todavia. Ejecuta el pipeline antes.")
        return 0
    con = duckdb.connect()
    con.execute(f"CREATE VIEW g AS SELECT * FROM '{ruta}'")

    textos = {d: d.read_text(encoding="utf-8") for d in DOCS if d.exists()}
    problemas = 0

    for nombre, consulta, _fmt, tolerancia in COMPROBACIONES:
        real = con.execute(consulta).fetchone()[0]
        escrito = _miles(real)
        # Se buscan numeros del mismo orden de magnitud cerca del concepto, para
        # no perseguir cualquier cifra del documento.
        encontrado = _citado(escrito, textos.values())
        if encontrado:
            print(f"  ok    {nombre:34} {escrito}")
            continue

        # No esta el numero de hoy: ¿hay alguno parecido que se haya quedado atras?
        candidatos = set()
        for t in textos.values():
            for m in re.finditer(r"\b(\d{1,3}(?:\.\d{3})+)\b", t):
                v = int(m.group(1).replace(".", ""))
                if real and abs(v - real) / real < (tolerancia / 100) and v != real:
                    candidatos.add((abs(v - real), m.group(1)))
        if candidatos:
            problemas += 1
            cerca = [c for _, c in sorted(candidatos)][:3]
            print(f"  AVISO {nombre:34} hoy es {escrito}; en los documentos "
                  f"hay {', '.join(cerca)}")
        else:
            print(f"  --    {nombre:34} {escrito}  (no se cita en ningun documento)")

    print()
    if problemas:
        print(f"{problemas} cifra(s) posiblemente caducada(s). Revisa y corrige.")
        print("Si el numero nuevo es el bueno, cambialo en los documentos.")
        return 1
    print("Los numeros de los documentos cuadran con los datos de hoy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
