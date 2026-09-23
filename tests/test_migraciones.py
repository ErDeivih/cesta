"""Las migraciones se reaplican enteras en cada arranque, asi que no pueden pelearse.

`almacen.migra()` aplica **todos** los ficheros de `plataforma/sql` por orden de nombre
**en cada arranque** de la API (son idempotentes a proposito: `IF NOT EXISTS`, `ADD COLUMN
IF NOT EXISTS`, `DROP ... IF EXISTS`). Eso tiene una consecuencia que no es obvia y que
costo un fallo real:

    **un fichero viejo que se reaplica no puede contradecir a uno nuevo que lo corrige.**

El 23 de septiembre de 2026, `001_esquema.sql` creaba un indice unico sobre `es_de_casa` a
secas -- "una sola lista de casa en todo el sistema" --, y `003_mas_de_dos.sql` lo borraba
para que cada persona tuviera la suya. Como los dos se aplican en cada arranque, el segundo
arranque lo resucitaba:

    psycopg.errors.UniqueViolation: could not create unique index "lista_de_casa_unica"
    DETAIL: Key (es_de_casa)=(t) is duplicated.

O sea que **la API no arrancaba** en cuanto habia dos listas de casa, que es el estado
normal de esta aplicacion. Lo encontro `plataforma/prueba_e2e.py` (que arranca contra un
PostgreSQL de verdad) al intentar borrar dos personas con su lista cada una.

Esta prueba lee los `.sql` y vigila esa clase de pelea: que ningun fichero cree algo que
otro borre despues. No sustituye a `prueba_e2e.py` -- eso ejecuta el SQL de verdad --, pero
avisa en el acto, sin contenedor y sin base de datos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SQL = RAIZ / "plataforma" / "sql"


def _ficheros() -> list[Path]:
    if not SQL.exists():
        pytest.skip("esta copia no trae las migraciones")
    return sorted(SQL.glob("*.sql"))


def _objetos(texto: str, patron: str) -> set[str]:
    return {m.group(1).lower() for m in re.finditer(patron, texto, re.I)}


def test_ningun_fichero_crea_algo_que_otro_borra():
    """Al reaplicarse enteros, crear y borrar el mismo objeto se pelean para siempre.

    Si un fichero crea `X` y otro lo borra, el orden decide: gana el ultimo que se aplica
    en cada arranque. Y como el que crea esta antes (por numero), **el que borra pierde
    siempre**: lo que queria quitar vuelve en cada arranque.
    """
    creados: dict[str, str] = {}
    borrados: dict[str, str] = {}
    for fichero in _ficheros():
        texto = fichero.read_text(encoding="utf-8")
        # Solo las lineas que no son comentario: medio fichero son explicaciones.
        vivas = "\n".join(ln for ln in texto.splitlines()
                          if not ln.lstrip().startswith("--"))
        for objeto in _objetos(vivas, r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)"):
            creados.setdefault(objeto, fichero.name)
        for objeto in _objetos(vivas, r"DROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?(\w+)"):
            borrados.setdefault(objeto, fichero.name)

    peleados = {o: (creados[o], borrados[o]) for o in creados if o in borrados}
    assert not peleados, (
        "hay indices que un fichero crea y otro borra, y como las migraciones se aplican "
        "enteras en cada arranque, el que borra pierde siempre:\n"
        + "\n".join(f"  {o}: lo crea {c} y lo borra {b}" for o, (c, b) in peleados.items())
        + "\n(el caso que paso: `lista_de_casa_unica`, y la API no arrancaba con dos "
          "listas de casa)")


def test_lo_que_se_borra_esta_en_algun_sitio_o_es_historia():
    """Un `DROP` de algo que no crea nadie es codigo muerto que confunde.

    Se permite si el fichero lo dice: hay `DROP` legitimamente historicos (borrar algo
    que creo una version anterior que ya no esta). Pero entonces tiene que estar contado
    en el comentario de arriba, porque quien lo lea va a buscar que era.
    """
    creados: set[str] = set()
    for fichero in _ficheros():
        texto = fichero.read_text(encoding="utf-8")
        vivas = "\n".join(ln for ln in texto.splitlines()
                          if not ln.lstrip().startswith("--"))
        creados |= _objetos(vivas, r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)")

    for fichero in _ficheros():
        texto = fichero.read_text(encoding="utf-8")
        vivas = "\n".join(ln for ln in texto.splitlines()
                          if not ln.lstrip().startswith("--"))
        for objeto in _objetos(vivas, r"DROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?(\w+)"):
            if objeto in creados:
                continue
            assert objeto in texto, f"{fichero.name} borra {objeto} y no lo explica"


def test_la_lista_de_casa_es_una_por_persona_y_no_una_por_sistema():
    """El caso concreto, escrito para que no vuelva.

    Una sola lista de casa en todo el sistema tenia sentido con dos personas que viven
    juntas; con amigos, cada uno quiere la suya y el segundo se lleva el error.
    """
    todo = "\n".join(f.read_text(encoding="utf-8") for f in _ficheros())
    vivas = "\n".join(ln for ln in todo.splitlines()
                      if not ln.lstrip().startswith("--"))
    # Se puede **borrar** (`003` lo hace, para quitarlo de las bases que lo tengan); lo
    # que no se puede es **crearlo**, que es lo que lo resucitaba en cada arranque.
    assert not re.search(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?"
                         r"lista_de_casa_unica", vivas, re.I), \
        "vuelve el indice unico global de lista de casa: la API no arranca con dos"
    assert re.search(r"ON lista\(dueno_id\) WHERE es_de_casa", vivas), \
        "falta el indice que hace que cada persona tenga LA SUYA (y solo una)"
