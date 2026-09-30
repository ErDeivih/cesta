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

Y ademas de las cifras: las citas
---------------------------------
Los documentos no solo citan numeros; citan codigo, asi: `almacen.py:287`. Esa
cita es la prueba de lo que se afirma, y envejece sola: el fichero se renombra,
o la linea 1200 aparece en un fichero de 900 lineas. Nadie lo nota leyendo,
porque el texto sigue sonando igual de bien.

Desde el 30 de septiembre de 2026 este control tambien saca todas las citas con
numero de linea de `docs/`, `README.md`, `.stitch/` y `plataforma/LEEME.md`, y
comprueba dos cosas que si se pueden medir: que el fichero citado este donde
dice, y que la linea citada llegue. No comprueba que la linea siga tratando de
lo mismo -- eso hay que mirarlo --, pero dice donde mirar, que es lo que faltaba.
"""
from __future__ import annotations

import json
import re
import sys
from contextlib import suppress
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


# --- Las citas de codigo: `almacen.py:287` -----------------------------------
# Ver el porque en la cabecera. Aqui solo las reglas de la busqueda.
def _docs_con_citas() -> list[Path]:
    """Los documentos que citan ficheros y lineas.

    Se miran tambien `README.md` y los disenos de `.stitch/`, que no llevan
    cifras pero si citas de codigo.
    """
    fuera = [*(RAIZ / "docs").rglob("*.md"), RAIZ / "README.md",
             RAIZ / "plataforma" / "LEEME.md"]
    stitch = RAIZ / ".stitch"
    if stitch.is_dir():
        fuera += list(stitch.glob("*.md"))
    return [p for p in fuera if p.exists()]

# Un nombre de fichero acabado en extension conocida, dos puntos y un numero
# (o dos, si es un tramo: `app.js:1413-1418`).
REFERENCIA = re.compile(
    r"([A-Za-z0-9_./\-]+\.(?:py|js|ts|tsx|jsx|sql|ya?ml|md|json|sh|css|html))"
    r":(\d+)(?:-(\d+))?"
)

# Carpetas que no forman parte del proyecto que se cita: dentro de ellas hay
# ficheros con los mismos nombres que los de verdad y la busqueda por nombre
# suelto encontraria el de mentira.
NO_SE_MIRAN = frozenset({
    "node_modules", ".git", "data", "dist", ".venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build",
})

def _cuantas_lineas(p: Path) -> int:
    try:
        return len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def _citas(texto: str):
    """Las citas con linea que hay en un texto: (fichero, desde, hasta)."""
    return [
        (m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else 0)
        for m in REFERENCIA.finditer(texto)
    ]


def _cita_viva(citado: str, desde: int, hasta: int, buscar) -> tuple[str, str]:
    """¿Se puede mirar esta cita? Devuelve el estado y con que se compara.

    Estados: `ok` (el fichero esta donde dice y la linea llega), `movida` (el
    fichero existe pero en otro sitio: el lector no lo abre con esa ruta),
    `fuera` (el fichero es mas corto que la linea citada) y `no esta` (no hay
    ningun fichero con ese nombre).

    `buscar(nombre)` devuelve [(ruta, total_de_lineas, es_la_ruta_citada), ...],
    para poder probar esto sin tocar el disco.
    """
    pedida = max(desde, hasta)
    candidatos = buscar(citado)
    if not candidatos:
        return "no esta", ""
    for ruta, total, directa in candidatos:
        if pedida <= total:
            return ("ok" if directa else "movida"), str(ruta)
    ruta, total, _ = candidatos[0]
    return "fuera", f"{ruta} tiene {total}"


def _indice_por_nombre() -> dict[str, list[Path]]:
    """Nombre suelto -> ficheros con ese nombre, para las citas sin ruta."""
    indice: dict[str, list[Path]] = {}
    for p in RAIZ.rglob("*"):
        if not p.is_file():
            continue
        if any(parte in NO_SE_MIRAN for parte in p.parts):
            continue
        indice.setdefault(p.name, []).append(p)
    return indice


def _candidatos(citado: str, indice: dict[str, list[Path]]):
    """Donde puede estar el fichero citado, y si la cita decia donde.

    Una cita vale si el fichero que se encuentra **acaba** en lo que la cita
    dice: los documentos escriben `almacen.py:287` a secas, y tambien
    `src/tipos.ts:173` desde la carpeta de la aplicacion, y las dos formas
    senalan un fichero que el lector encuentra. Se da por movida solo cuando el
    fichero existe con ese nombre y **ninguna** ruta acaba en lo que la cita
    afirma -- entonces la cita manda a un sitio donde no esta.

    Las dos primeras versiones de esto avisaron de 523 citas buenas: primero por
    resolver por nombre suelto, luego por no aceptar rutas parciales. Un aviso
    falso por cada cita buena es la forma mas rapida de que nadie los mire.
    """
    directo = RAIZ / citado
    if directo.is_file():
        return [(directo, _cuantas_lineas(directo), True)]
    dicho = citado.replace("\\", "/")
    candidatos = []
    for p in indice.get(Path(citado).name, []):
        rel = p.relative_to(RAIZ).as_posix()
        candidatos.append((p, _cuantas_lineas(p), rel.endswith(dicho)))
    return candidatos


def comprobar_citas() -> tuple[int, list[str]]:
    """Todas las citas con linea de los documentos, una a una."""
    indice = _indice_por_nombre()

    def buscar(citado: str):
        return _candidatos(citado, indice)

    total = 0
    rotas: list[str] = []
    for doc in sorted(set(_docs_con_citas())):
        nombre_doc = doc.relative_to(RAIZ).as_posix()
        for n, linea in enumerate(
            doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for citado, desde, hasta in _citas(linea):
                total += 1
                estado, detalle = _cita_viva(citado, desde, hasta, buscar)
                if estado != "ok":
                    rotas.append(f"{nombre_doc}:{n}  {estado}: {citado}:{desde}  {detalle}")
    return total, rotas


# --- Los comandos que los documentos mandan ejecutar -------------------------
# Un documento que dice `uv run python -m projects.cesta.pipeline` esta prometiendo
# que ese modulo existe. Si el modulo se renombra, el documento sigue diciendo lo
# mismo y suena igual de bien: nadie ejecuta los comandos escritos por ahi para
# comprobarlo. Esto los saca y mira si llevan a algun sitio.
COMANDOS = {
    "modulo": re.compile(r"python -m ([A-Za-z_][\w.]*)"),
    "fichero": re.compile(r"python ([A-Za-z_][\w./\\-]*\.py)"),
    "npm": re.compile(r"npm run ([\w:-]+)"),
    "uvicorn": re.compile(r"uvicorn ([\w.]+):([\w_]+)"),
}

NO_SE_MIRAN_ESTO = frozenset({"data", "node_modules", "dist", "docs", "assets"})


def _carpetas_propias() -> set[str]:
    return {
        p.name for p in RAIZ.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in NO_SE_MIRAN_ESTO
    }


def _existe_modulo(nombre: str, propias: set[str]) -> bool | None:
    """¿Existe ese modulo? `None` si no es de casa y no hay nada que mirar.

    `pytest`, `uvicorn`, `http.server` y compania no son nuestros: mirarlos daria
    avisos por todas partes y ninguno seria un fallo del repositorio.
    """
    piezas = nombre.split(".")
    if piezas[0] not in propias:
        return None
    base = RAIZ.joinpath(*piezas)
    return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()


def _existe_fichero(citado: str, indice: dict[str, list[Path]]) -> bool | None:
    """Igual, para `python ruta/al/fichero.py`."""
    if "$" in citado or citado.startswith(("/", "\\")):
        return None  # una ruta de dentro de un contenedor, o una variable
    dicho = citado.replace("\\", "/")
    if (RAIZ / dicho).is_file():
        return True
    return any(
        p.relative_to(RAIZ).as_posix().endswith(dicho)
        for p in indice.get(Path(dicho).name, [])
    )


def _comandos(linea: str) -> list[tuple[str, str]]:
    """Los comandos que hay en una linea: (clase, dato que hay que buscar).

    El dato es lo que se busca, **sin adorno**: el modulo, la ruta, el nombre del
    script, `modulo:app`. La primera version devolvia el comando ya escrito
    (`"uvicorn plataforma.api.main:app"`) y luego lo volvia a partir por `:` para
    sacar el modulo; le pasaba `"uvicorn plataforma.api.main"` a la comprobacion,
    que contestaba "esto no es de casa" y **saltaba el comando sin medirlo**. El
    texto se compone al escribir el aviso, no al buscar: asi no hay dos formas de
    decir lo mismo.
    """
    if "<" in linea or "NN" in linea or "..." in linea:
        return []  # una plantilla, no un comando
    fuera = []
    for clase, patron in COMANDOS.items():
        for m in patron.finditer(linea):
            if clase != "uvicorn":
                fuera.append((clase, m.group(1)))
            else:
                fuera.append(("uvicorn", f"{m.group(1)}:{m.group(2)}"))
    return fuera


def _como_se_escribe(clase: str, dato: str) -> str:
    """El comando tal y como se lee en el documento, para el aviso."""
    return f"npm run {dato}" if clase == "npm" else (
        f"uvicorn {dato}" if clase == "uvicorn" else dato
    )


def _comando_existe(clase: str, dato: str, propias: set[str],
                    indice: dict[str, list[Path]], npm: set[str]) -> bool | None:
    """¿Ese comando lleva a algun sitio? `None` si no es de casa."""
    if clase == "modulo":
        return _existe_modulo(dato, propias)
    if clase == "fichero":
        return _existe_fichero(dato, indice)
    if clase == "npm":
        return dato in npm
    # uvicorn: el dato es `modulo:app`
    return _existe_modulo(dato.split(":")[0], propias)


def _scripts_de_npm() -> set[str]:
    scripts: set[str] = set()
    for p in (RAIZ / "package.json",
              RAIZ / "plataforma" / "web" / "app" / "package.json"):
        if p.exists():
            with suppress(OSError, json.JSONDecodeError):
                scripts |= set(json.loads(p.read_text(encoding="utf-8")).get("scripts", {}))
    return scripts


def comprobar_comandos() -> tuple[int, list[str]]:
    """Los comandos citados en los documentos, uno a uno."""
    propias = _carpetas_propias()
    indice = _indice_por_nombre()
    npm = _scripts_de_npm()

    total = 0
    rotos: list[str] = []
    for doc in sorted(set(_docs_con_citas())):
        nombre_doc = doc.relative_to(RAIZ).as_posix()
        for n, linea in enumerate(
            doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for clase, dato in _comandos(linea):
                visto = _comando_existe(clase, dato, propias, indice, npm)
                if visto is None:
                    continue
                total += 1
                if not visto:
                    texto = _como_se_escribe(clase, dato)
                    rotos.append(f"{nombre_doc}:{n}  ({clase})  {texto}")
    return total, rotos


def _numeros() -> int:
    """Las cifras de los documentos contra el gold de hoy. Devuelve los avisos."""
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
    else:
        print("Los numeros de los documentos cuadran con los datos de hoy.")
    return problemas


def main() -> int:
    problemas = _numeros()

    # Las citas de codigo no dependen del gold, asi que se comprueban siempre
    # -- tambien cuando no hay datos, que es cuando mas documentos se escriben
    # y menos se revisan.
    print()
    total, rotas = comprobar_citas()
    print(f"Las citas de codigo de los documentos: {total} con numero de linea")
    if rotas:
        problemas += len(rotas)
        print(f"  AVISO {len(rotas)} cita(s) que ya no se pueden mirar:")
        for r in rotas[:20]:
            print(f"    {r}")
        if len(rotas) > 20:
            print(f"    ... y {len(rotas) - 20} mas")
        print("  Corrige el fichero, la linea o la ruta; si el fichero ya no esta,")
        print("  quita el numero de linea y deja el nombre.")
    else:
        print("  ok    todas apuntan a un fichero que esta y a una linea que llega")

    # Y los comandos, que tampoco dependen del gold.
    print()
    total_cmd, rotos = comprobar_comandos()
    print(f"Los comandos que los documentos mandan ejecutar: {total_cmd} de casa")
    if rotos:
        problemas += len(rotos)
        print(f"  AVISO {len(rotos)} comando(s) que no llevan a ningun sitio:")
        for r in rotos[:20]:
            print(f"    {r}")
        if len(rotos) > 20:
            print(f"    ... y {len(rotos) - 20} mas")
        print("  Corrige el comando o el nombre del modulo; si el modulo ya no esta,")
        print("  cuenta en el documento que se fue y por que.")
    else:
        print("  ok    todos apuntan a un modulo, un fichero o un script que existe")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
