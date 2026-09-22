"""Lo que la API importa tiene que estar dentro de su imagen.

El 21 de septiembre de 2026 `cesta-api` se quedo en un bucle de reinicios y el
sintoma que llegaba a la consola no decia nada del motivo:

    Error response from daemon: Container c0a28ba4... is restarting,
    wait until the container is running

La causa estaba a tres saltos de distancia. `plataforma/api/catalogo.py` hacia
`from core import comparacion` para leer **una constante**, y `core/comparacion.py`
abria con `import polars as pl`. Polars no esta en la imagen de la API, porque la
API no manipula dataframes: consulta SQL. Asi que el contenedor moria al
importarse, antes de servir una sola peticion, con un ModuleNotFoundError que
solo aparecia en `docker compose logs api`.

Por que no lo vio ninguna prueba
--------------------------------
Porque las pruebas corren en el entorno de desarrollo, donde polars **si** esta.
El programa importaba bien en todas partes menos en el unico sitio donde tenia
que funcionar. Ninguna prueba que ejecute codigo puede ver esa diferencia: la
diferencia no esta en el codigo, esta en la lista de paquetes de la imagen.

Asi que esto no ejecuta nada. Lee el grafo de importaciones con `ast` desde
`plataforma/api/main.py`, se queda con los modulos de terceros y comprueba que
todos aparecen en el `pip install` del Dockerfile. Es estatico, tarda
milisegundos y no necesita Docker.

Lo que esta prueba protege de verdad es la frontera: **el pipeline vive de
dataframes y la API vive de SQL**. El dia que alguien vuelva a cruzarla sin
querer -- que es lo facil, porque una constante compartida parece inofensiva --
se entera aqui y no en un contenedor que se reinicia en silencio.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
DOCKERFILE = RAIZ / "plataforma" / "Dockerfile"
ENTRADA = RAIZ / "plataforma" / "api" / "main.py"

# Los paquetes se instalan por su nombre de distribucion y se importan por otro.
# No hay forma de deducirlo sin consultar el paquete instalado, asi que la
# correspondencia se escribe, que ademas obliga a mirarla al anadir uno.
MODULOS_DE = {
    "fastapi": {"fastapi"},
    "uvicorn": {"uvicorn"},
    "duckdb": {"duckdb"},
    "psycopg": {"psycopg", "psycopg_pool"},
    "argon2-cffi": {"argon2"},
    "pydantic": {"pydantic"},
    "polars": {"polars"},
    "starlette": {"starlette"},
}

# Paquetes de primera parte: se siguen en vez de contarlos como dependencia.
NUESTROS = ("plataforma", "core", "projects")


def _distribuciones_del_dockerfile() -> set[str]:
    """Los nombres que el Dockerfile pasa a `pip install`, sin la version."""
    texto = DOCKERFILE.read_text(encoding="utf-8")
    # El RUN se parte en varias lineas con `\`; se juntan antes de mirar.
    plano = texto.replace("\\\n", " ")
    fuera: set[str] = set()
    for linea in plano.splitlines():
        if "pip install" not in linea:
            continue
        for trozo in linea.split("pip install", 1)[1].split():
            trozo = trozo.strip('"\'')
            if trozo.startswith("-"):          # --no-cache-dir y companía
                continue
            # "psycopg[binary,pool]>=3.2"  ->  "psycopg"
            nombre = trozo.split("[")[0]
            for corte in (">=", "==", "<=", "~=", ">", "<"):
                nombre = nombre.split(corte)[0]
            if nombre:
                fuera.add(nombre.lower())
    return fuera


def _fichero_de(modulo: str) -> Path | None:
    """De `plataforma.api.catalogo` al fichero que lo contiene, si es nuestro."""
    ruta = RAIZ / Path(*modulo.split("."))
    if (ruta / "__init__.py").exists():
        return ruta / "__init__.py"
    if ruta.with_suffix(".py").exists():
        return ruta.with_suffix(".py")
    return None


def _es_solo_para_tipos(nodo: ast.stmt) -> bool:
    """`if TYPE_CHECKING:` — un bloque que en ejecucion no existe."""
    if not isinstance(nodo, ast.If):
        return False
    prueba = nodo.test
    if isinstance(prueba, ast.Name):
        return prueba.id == "TYPE_CHECKING"
    if isinstance(prueba, ast.Attribute):
        return prueba.attr == "TYPE_CHECKING"
    return False


def _sentencias_de_arranque(cuerpo: list[ast.stmt]):
    """Solo lo que se ejecuta al importar el modulo.

    Esta es toda la precision de la prueba. Un `import` dentro de una funcion no
    tira el contenedor al arrancar: falla el dia que se llama a esa funcion, y en
    la API hay funciones que no se llaman nunca desde la API. Y un bloque
    `if TYPE_CHECKING:` no se ejecuta jamas.

    Contar esos dos como dependencias haria fallar la prueba con el codigo bien,
    que es la forma mas rapida de que alguien la desactive.
    """
    for nodo in cuerpo:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue                      # se ejecuta al llamar, no al importar
        if _es_solo_para_tipos(nodo):
            continue
        yield nodo
        # Un `import` de primer nivel puede estar dentro de un `if`, un `try` o
        # un `with`: se sigue ejecutando al importar el modulo.
        for campo in ("body", "orelse", "finalbody"):
            dentro = getattr(nodo, campo, None)
            if isinstance(dentro, list):
                yield from _sentencias_de_arranque(dentro)
        for manejador in getattr(nodo, "handlers", []) or []:
            yield from _sentencias_de_arranque(manejador.body)


def _importados(fichero: Path, paquete: str) -> set[str]:
    """Los modulos que este fichero importa **al importarse el**, ya resueltos."""
    arbol = ast.parse(fichero.read_text(encoding="utf-8"), filename=str(fichero))
    fuera: set[str] = set()
    for nodo in _sentencias_de_arranque(arbol.body):
        if isinstance(nodo, ast.Import):
            fuera.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                # `from . import x` dentro de plataforma.api -> plataforma.api.x
                partes = paquete.split(".")
                base = ".".join(partes[:len(partes) - nodo.level + 1])
                raiz = f"{base}.{nodo.module}" if nodo.module else base
            else:
                raiz = nodo.module or ""
            if not raiz:
                continue
            fuera.add(raiz)
            # `from core import comparacion`: lo que importa es core.comparacion,
            # no `core`. Sin esto el grafo se para en el paquete y no ve el
            # `import polars` que hay dentro del modulo.
            for a in nodo.names:
                fuera.add(f"{raiz}.{a.name}")
    return fuera


def grafo(entrada: Path) -> tuple[set[str], set[str]]:
    """Recorre las importaciones desde `entrada`. Devuelve (nuestros, terceros)."""
    modulo_inicial = ".".join(
        entrada.relative_to(RAIZ).with_suffix("").parts)
    pendientes = [(modulo_inicial, entrada)]
    vistos: set[str] = set()
    terceros: set[str] = set()
    while pendientes:
        modulo, fichero = pendientes.pop()
        if modulo in vistos:
            continue
        vistos.add(modulo)
        paquete = modulo.rsplit(".", 1)[0]
        for importado in _importados(fichero, paquete):
            cabeza = importado.split(".")[0]
            if cabeza in sys.stdlib_module_names or cabeza == "__future__":
                continue
            if cabeza in NUESTROS:
                hijo = _fichero_de(importado)
                if hijo is not None:
                    pendientes.append((importado, hijo))
                # Si no hay fichero es `from core import comparacion` apuntando a
                # un nombre dentro del modulo, no a un modulo. No es de terceros.
                continue
            terceros.add(cabeza)
    return vistos, terceros


@pytest.fixture(scope="module")
def instalados() -> set[str]:
    if not DOCKERFILE.exists():
        pytest.skip("no hay Dockerfile en esta copia del proyecto")
    modulos: set[str] = set()
    for dist in _distribuciones_del_dockerfile():
        modulos |= MODULOS_DE.get(dist, {dist.replace("-", "_")})
    return modulos


def test_el_dockerfile_declara_algo():
    """Si el parseo se rompe, el resto de pruebas pasarian sin mirar nada."""
    if not DOCKERFILE.exists():
        pytest.skip("no hay Dockerfile en esta copia del proyecto")
    dists = _distribuciones_del_dockerfile()
    assert "fastapi" in dists and "duckdb" in dists, dists


def test_todo_lo_que_importa_la_api_esta_en_su_imagen(instalados):
    """La prueba que habria ahorrado el bucle de reinicios del 21 de septiembre."""
    _, terceros = grafo(ENTRADA)
    faltan = sorted(terceros - instalados)
    assert not faltan, (
        f"la API importa {faltan} y el Dockerfile no lo instala. El contenedor "
        f"arrancaria y moriria con ModuleNotFoundError antes de servir nada. "
        f"O se anade al pip install, o se deja de importar desde plataforma/api.")


def test_la_api_no_arrastra_polars():
    """Polars es del pipeline, no de la API. Esta es la frontera, por su nombre.

    Se comprueba aparte del test anterior a proposito: anadir polars al
    Dockerfile haria pasar aquel y dejaria pasar el error de diseno. La API
    consulta SQL; el dia que necesite un dataframe, lo que hay que revisar es
    por que.
    """
    _, terceros = grafo(ENTRADA)
    assert "polars" not in terceros, (
        "plataforma/api vuelve a importar polars. La API consulta SQL sobre los "
        "parquet con DuckDB y no manipula dataframes: si hace falta una "
        "constante de un modulo que si usa polars, el import va dentro de la "
        "funcion que lo necesita (ver core/comparacion.py).")


def test_el_grafo_llega_a_core():
    """Guarda de la guarda: si el recorrido se quedara corto, no vigilaria nada."""
    vistos, _ = grafo(ENTRADA)
    assert "plataforma.api.catalogo" in vistos
    assert any(m.startswith("core.") for m in vistos), sorted(vistos)
