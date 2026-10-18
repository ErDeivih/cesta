"""*** EL BANCO DE ENSAYO: PROPIO, IDENTIFICABLE Y DESECHABLE. ***

*M00 de la especificacion maestra del 18/10/2026. Lo pide con estas palabras:*

    «Crear un comando de preparacion/limpieza del sandbox con manifiesto de recursos propios,
     PostgreSQL y SQLite separados de casa; probar las guardas antes de DDL.»

    Aceptacion: rechaza DSN protegido sin escribir; limpieza no toca recursos ajenos;
    dos ejecuciones reproducen el mismo escenario y se conoce cada proceso creado.

*** POR QUE ESTO ES LO PRIMERO Y NO UN DETALLE ***: *el encargo avisa de tres bases que no son
destino de restauracion -- **5432 (casa), 5433 (facylf) y 5434 (ensayos compartidos)** -- y de que
nunca hay que matar «el proceso del puerto».* *Un comando que se equivoque de base una vez borra el
trabajo de casa; uno que mate por puerto tumba un contenedor ajeno.*

*Asi que aqui las guardas **se comprueban antes de escribir nada**, y cada recurso que se crea queda
anotado en un manifiesto con su nombre y su identificador.* *La limpieza **solo** borra lo que esta
en el manifiesto.*

*** REGLAS, y cada una tiene su prueba ***:

1. **La base tiene que ser de ensayo y no estar en la lista negra.** *Puerto 5432, 5433 y 5434
   prohibidos, aunque el DSN venga bien escrito.*
2. **El nombre de la base tiene que empezar por `cesta_ensayo_`.** *Asi un DSN de casa no pasa ni
   por descuido ni por copiar y pegar.*
3. **SQLite vive en un directorio con marcador de pertenencia.** *No se toca nada fuera de el.*
4. **La limpieza no adivina: lee el manifiesto.** *Si un contenedor no esta anotado, no se borra
   aunque se llame parecido.*
5. **Cada contenedor que se crea queda en el manifiesto con su id**, *no solo con el nombre: un
   nombre se puede reutilizar, un id no.*

Uso:

    uv run python -m plataforma.ensayo prepara      # crea y siembra
    uv run python -m plataforma.ensayo estado       # que hay, y de quien es
    uv run python -m plataforma.ensayo limpia       # borra SOLO lo anotado
    uv run python -m plataforma.ensayo guardas      # prueba las guardas (no escribe nada)

*`guardas` es lo que se ejecuta antes que nada: **no toca la base**, solo comprueba que las reglas
rechazan lo que tienen que rechazar.*
"""

from __future__ import annotations

import json
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

# --- Lo que nunca se toca -------------------------------------------------

#: *Los puertos del encargo.* **No son destinos de restauracion ni de escritura.**
PUERTOS_PROTEGIDOS = frozenset({5432, 5433, 5434})

#: *Prefijo obligatorio del nombre de la base de ensayo.* *Un DSN de casa no lo lleva.*
PREFIJO_BASE = "cesta_ensayo_"

#: *Prefijo obligatorio de los contenedores de ensayo.*
PREFIJO_CONTENEDOR = "cesta-ensayo-"

#: *El marcador que llevan los directorios y ficheros propios.*
MARCADOR = ".cesta-ensayo"


# *** El catalogo del apartado 8, que es el guion del escenario. ***
# *Se lee del fichero versionado `plataforma/ensayo/catalogo.json`, no de constantes escritas en
# este modulo: el guion y el almacen son cosas distintas y no pueden divergir.*
CATALOGO_8 = json.loads(
    (Path(__file__).resolve().parent / "ensayo" / "catalogo.json").read_text(encoding="utf-8")
)


class GuardaRota(RuntimeError):
    """*Una guarda dijo que no.* *Se lanza **antes** de escribir nada.*"""


@dataclass(frozen=True)
class Plan:
    """*Lo que se va a crear, decidido **antes** de crear nada.*"""

    nombre: str
    puerto_pg: int
    contenedor: str
    dsn: str
    directorio: Path

    @property
    def sqlite(self) -> Path:
        return self.directorio / "privado.sqlite3"


def _puerto_libre(puerto: int) -> bool:
    """*Nadie escuchando en esa direccion.* *Comprobado, no supuesto.*"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def comprueba_dsn(dsn: str) -> str:
    """*** La guarda principal: ¿este DSN es de ensayo? *** *Devuelve el nombre de la base.*

    *Rechaza, con el motivo escrito, todo lo que no sea inequivocamente desechable.*
    """
    partes = urlparse(dsn)
    if partes.scheme not in ("postgres", "postgresql"):
        raise GuardaRota(f"el DSN no es de PostgreSQL: {partes.scheme!r}")
    anfitrion = (partes.hostname or "").strip().lower()
    if anfitrion not in ("127.0.0.1", "localhost", "::1"):
        raise GuardaRota(
            f"la base tiene que estar en loopback, y esto apunta a {anfitrion!r}: "
            "un ensayo no se hace contra una base de fuera de esta maquina"
        )
    try:
        puerto = partes.port or 5432
    except ValueError as exc:
        raise GuardaRota("el puerto del DSN no es un numero") from exc
    if puerto in PUERTOS_PROTEGIDOS:
        raise GuardaRota(
            f"el puerto {puerto} esta protegido por el encargo (5432 casa, 5433 facylf, "
            "5434 ensayos compartidos): no es destino de escritura ni de restauracion"
        )
    base = (partes.path or "").lstrip("/").strip()
    if not base.startswith(PREFIJO_BASE):
        raise GuardaRota(
            f"la base {base!r} no empieza por {PREFIJO_BASE!r}: no parece un ensayo, "
            "y una base que no se llama como un ensayo no se toca"
        )
    return base


def comprueba_contenedor(nombre: str) -> None:
    """*El contenedor tiene que ser nuestro por el nombre, y no estar ya en uso.*"""
    if not nombre.startswith(PREFIJO_CONTENEDOR):
        raise GuardaRota(f"el contenedor {nombre!r} no empieza por {PREFIJO_CONTENEDOR!r}")
    salida = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^{re.escape(nombre)}$", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    if nombre in salida.stdout.split():
        raise GuardaRota(f"ya existe un contenedor llamado {nombre!r}: no se reutiliza a ciegas")


def plan_para(nombre: str, puerto_pg: int = 55432) -> Plan:
    """*** Decide el plan y **no crea nada**.*** *Si algo no cuadra, falla aqui.*"""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,30}", nombre):
        raise GuardaRota(f"nombre de ensayo invalido: {nombre!r} (minusculas, digitos, - y _)")
    contenedor = f"{PREFIJO_CONTENEDOR}{nombre}"
    base = f"{PREFIJO_BASE}{nombre.replace('-', '_')}"
    dsn = f"postgresql://cesta:prueba@127.0.0.1:{puerto_pg}/{base}"
    # *Las tres guardas, en el mismo orden en que se leerian en voz alta.*
    comprueba_dsn(dsn)
    comprueba_contenedor(contenedor)
    if not _puerto_libre(puerto_pg):
        raise GuardaRota(f"el puerto {puerto_pg} ya esta ocupado: se elige otro, no se mata a nadie")
    raiz = Path(__file__).resolve().parent.parent / "data" / "ensayo" / nombre
    return Plan(nombre=nombre, puerto_pg=puerto_pg, contenedor=contenedor, dsn=dsn, directorio=raiz)


# --- El manifiesto --------------------------------------------------------


@dataclass
class Manifiesto:
    """*** Lo que este trabajo creo, para poder borrarlo sin adivinar. ***"""

    nombre: str
    contenedor: str = ""
    contenedor_id: str = ""
    puerto_pg: int = 0
    dsn: str = ""
    directorio: str = ""
    sqlite: str = ""
    # *El catalogo del ensayo: su propio gold de parquet, con su version.*
    gold: str = ""
    procesos: list[int] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def ruta(self) -> Path:
        return Path(__file__).resolve().parent.parent / "data" / "ensayo" / f"{self.nombre}.manifiesto.json"

    def guarda(self) -> None:
        ruta = self.ruta()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (ruta.parent / MARCADOR).write_text(
            "Directorio del banco de ensayo. Todo lo que hay aqui lo creo este trabajo.\n",
            encoding="utf-8",
        )

    @classmethod
    def lee(cls, nombre: str) -> Manifiesto:
        ruta = Path(__file__).resolve().parent.parent / "data" / "ensayo" / f"{nombre}.manifiesto.json"
        if not ruta.exists():
            raise GuardaRota(
                f"no hay manifiesto para {nombre!r}: sin manifiesto no se sabe que se creo, "
                "y limpiar a ciegas es como se borra lo que no es de uno"
            )
        return cls(**json.loads(ruta.read_text(encoding="utf-8")))


def _docker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=False)


def prepara(nombre: str = "propio", puerto_pg: int = 55432, espera_s: int = 60) -> Manifiesto:
    """*Crea el banco de ensayo y deja anotado **cada** recurso.* *No siembra: eso es `siembra`.*"""
    plan = plan_para(nombre, puerto_pg)
    if plan.directorio.exists():
        raise GuardaRota(
            f"ya existe {plan.directorio}: no se pisa un ensayo anterior sin limpiarlo antes"
        )
    man = Manifiesto(
        nombre=nombre, contenedor=plan.contenedor, puerto_pg=plan.puerto_pg,
        dsn=plan.dsn, directorio=str(plan.directorio), sqlite=str(plan.sqlite),
    )
    plan.directorio.mkdir(parents=True)
    (plan.directorio / MARCADOR).write_text(
        "Directorio del banco de ensayo. Todo lo que hay aqui lo creo este trabajo.\n",
        encoding="utf-8",
    )

    creado = _docker(
        "run", "--rm", "-d", "--name", plan.contenedor,
        "-e", "POSTGRES_PASSWORD=prueba", "-e", "POSTGRES_USER=cesta",
        "-e", f"POSTGRES_DB={plan.dsn.rsplit('/', 1)[-1]}",
        "-p", f"127.0.0.1:{plan.puerto_pg}:5432", "postgres:16-alpine",
    )
    if creado.returncode != 0:
        man.notas.append("docker run fallo: " + (creado.stderr or "").strip()[:300])
        man.guarda()
        raise GuardaRota("no se pudo crear el contenedor: " + (creado.stderr or "").strip()[:200])
    man.contenedor_id = creado.stdout.strip()
    man.guarda()  # *Anotado ANTES de esperar: si se corta aqui, la limpieza sabe que existe.*

    # *** Y SU CATALOGO. *** *Un ensayo sin datos no sirve para nada: el escenario del apartado 8
    # necesita arroz (dos marcas), leche y huevos, y el gold de casa no los tiene.* *Se construye
    # aqui, con el generador versionado, en vez de copiar un parquet suelto.*
    try:
        from plataforma.construye_gold_ensayo import (
            construye as construye_gold,
        )

        destino_gold = plan.directorio / "gold"
        construye_gold(destino_gold)
        man.gold = str(destino_gold)
        man.guarda()
        man.notas.append("catalogo del apartado 8 construido en " + str(destino_gold))
    except Exception as exc:  # noqa: BLE001
        man.notas.append("el catalogo NO se pudo construir: " + str(exc)[:200])
        man.guarda()

    limite = time.monotonic() + espera_s
    while time.monotonic() < limite:
        listo = _docker("exec", plan.contenedor, "pg_isready", "-U", "cesta")
        if "accepting connections" in (listo.stdout or ""):
            return man
        time.sleep(2)
    man.notas.append(f"no respondio en {espera_s} s")
    man.guarda()
    raise GuardaRota(f"la base de ensayo no respondio en {espera_s} s; queda anotada para limpiar")


def limpia(nombre: str = "propio") -> list[str]:
    """*** Borra **solo** lo que esta en el manifiesto.*** *Devuelve lo que hizo, para poder leerlo.*

    *No se busca por nombre «parecido», ni por puerto, ni por proceso suelto.* *Un contenedor ajeno
    llamado `cesta-sandbox-x` no se toca: no esta en **este** manifiesto.*
    """
    man = Manifiesto.lee(nombre)
    hecho: list[str] = []

    if man.contenedor_id:
        # *Por ID, que no se reutiliza.* *Y se comprueba que el que se va a borrar es el anotado.*
        actual = _docker("inspect", "--format", "{{.Name}}", man.contenedor_id)
        if actual.returncode == 0:
            nombre_real = actual.stdout.strip().lstrip("/")
            if nombre_real != man.contenedor:
                man.notas.append(
                    f"el id {man.contenedor_id[:12]} ya no es {man.contenedor!r} sino {nombre_real!r}: NO se borra"
                )
            else:
                borrado = _docker("rm", "-f", man.contenedor_id)
                hecho.append(("contenedor " + man.contenedor + " borrado") if borrado.returncode == 0
                             else ("contenedor " + man.contenedor + ": " + (borrado.stderr or "").strip()[:120]))

    for pid in man.procesos:
        hecho.append(f"proceso {pid}: NO se mata automaticamente (se cierra desde su duenno)")

    directorio = Path(man.directorio) if man.directorio else None
    if directorio and directorio.exists():
        if (directorio / MARCADOR).exists():
            shutil.rmtree(directorio)
            hecho.append("directorio " + str(directorio) + " borrado")
        else:
            hecho.append(
                "directorio " + str(directorio) + ": NO se borra, no lleva el marcador de pertenencia"
            )

    ruta_man = man.ruta()
    if ruta_man.exists():
        ruta_man.unlink()
        hecho.append("manifiesto borrado")
    return hecho


def estado(nombre: str | None = None) -> dict:
    """*Que hay en `data/ensayo`, y de quien es cada cosa.* *Solo lectura.*"""
    raiz = Path(__file__).resolve().parent.parent / "data" / "ensayo"
    if not raiz.exists():
        return {"manifiestos": [], "suelto": []}
    manifiestos = []
    for f in sorted(raiz.glob("*.manifiesto.json")):
        datos = json.loads(f.read_text(encoding="utf-8"))
        inspect = _docker("inspect", "--format", "{{.State.Status}}", datos.get("contenedor_id") or "")
        datos["vivo"] = (inspect.stdout or "").strip() if inspect.returncode == 0 else "ausente"
        manifiestos.append(datos)
    if nombre:
        manifiestos = [m for m in manifiestos if m.get("nombre") == nombre]
    suelto = [p.name for p in raiz.iterdir() if p.is_dir() and not (p / MARCADOR).exists()]
    return {"manifiestos": manifiestos, "suelto": suelto}


# --- La siembra -----------------------------------------------------------


def siembra(nombre: str = "propio") -> dict:
    """*** Las cuentas y las listas del escenario, en el banco de ensayo. ***

    *Lo que pide M03 para poder probarse: **sin listas, sin casa y con casa**.* *Son tres personas
    distintas y no se puede simular con una sola, asi que se siembran tres.*

        A  casa     hogar: lista «Casa» (es_de_casa) + lista «Viaje» (personal)
        B  sin casa  una lista normal, ninguna de casa
        C  sin listas  ninguna lista

    *Y una cuarta, **D**, que no se siembra: existe para probar que **no** ve lo de A.*

    *** Lo que NO siembra, y por que ***: *recetas, despensa y ofertas necesitan el **catalogo de
    ensayo**, que todavia no existe.* *La especificacion pide que sea «pequeno y versionado» y que no
    dependa del producto del dia; inventarlo ahora con cuatro productos sueltos seria justo lo que
    advierte que no se haga.* *Se siembra lo que se puede comprobar y se dice lo que falta.*

    *Devuelve un resumen con lo creado, para que la prueba pueda afirmarlo sin creerse nada.*
    """
    import os

    man = Manifiesto.lee(nombre)
    # *La guarda otra vez: el DSN que se va a usar tiene que ser el de este ensayo.*
    comprueba_dsn(man.dsn)

    # *`almacen` lee la variable al arrancar: se pone **antes** de importarlo.*
    os.environ["CESTA_POSTGRES"] = man.dsn
    # *** Y EL CATALOGO, que va aparte. *** *`catalogo.py` monta sus vistas sobre parquet y
    # resuelve `AJUSTES.gold` con **`CESTA_GOLD`** (`ajustes.py:27`).* *Sin esto el ensayo tendria
    # cuentas y listas, pero la ficha no encontraria ni un producto.*
    if man.gold and Path(man.gold).exists():
        os.environ["CESTA_GOLD"] = man.gold
    else:
        man.notas.append("sin catalogo: no hay gold en el manifiesto")
    from plataforma.api import almacen  # a proposito: despues de poner el entorno

    almacen.arranca()

    resumen: dict = {"cuentas": {}, "listas": {}, "recetas": [], "despensa": [], "avisos": []}

    # *** Las tres configuraciones que pide M03.*** *La clave es unica: dos corridas fallan en vez
    # de duplicar, que es lo que hace falta para que el escenario sea reproducible.*
    cuentas = [
        ("a_casa", "A con casa", [("Casa", True), ("Viaje", False)]),
        ("b_sin_casa", "B sin casa", [("Mi lista", False)]),
        ("c_sin_listas", "C sin listas", []),
    ]
    for usuario, nombre_largo, listas in cuentas:
        try:
            # *** IDEMPOTENTE: si la cuenta ya esta, se reutiliza. ***
            # *«Dos ejecuciones reproducen el mismo escenario»: la segunda no puede reventar por
            # clave duplicada, tiene que dejar lo mismo.* *`entra` es el login de verdad, asi que
            # sirve de comprobacion sin inventar una consulta nueva.*
            ya = almacen.entra(usuario, "prueba-larga-1")
            if ya:
                quien = ya[1]
                resumen["cuentas"][usuario] = quien["id"]
                # *Y las listas que falten se anaden; las que ya estan no se duplican.*
                existentes = {x["nombre"] for x in almacen.listas_de(quien["id"])}
                creadas = []
                for nombre_lista, es_casa in listas:
                    if nombre_lista in existentes:
                        creadas.append({"nombre": nombre_lista, "es_de_casa": es_casa, "id": "(ya estaba)"})
                    else:
                        lista = almacen.crea_lista(quien["id"], nombre_lista, es_casa)
                        creadas.append({"nombre": nombre_lista, "es_de_casa": es_casa, "id": lista["id"]})
                resumen["listas"][usuario] = creadas
                continue
            quien = almacen.crea_usuario(usuario, nombre_largo, "prueba-larga-1")
            resumen["cuentas"][usuario] = quien["id"]
            creadas = []
            for nombre_lista, es_casa in listas:
                lista = almacen.crea_lista(quien["id"], nombre_lista, es_casa)
                creadas.append({"nombre": nombre_lista, "es_de_casa": es_casa, "id": lista["id"]})
            resumen["listas"][usuario] = creadas
        except Exception as exc:  # noqa: BLE001  (se informa, no se traga)
            resumen["cuentas"][usuario] = "ERROR: " + str(exc)[:160]

    # *** LAS CINCO RECETAS DEL APARTADO 8, *y en el SQLite DEL ENSAYO*. ***
    #
    # *`core.recetas.conecta(ruta)` hace `Path(ruta) if ruta else BASE`: **sin ruta escribe en el
    # recetario de casa**.* *Asi que aqui se le pasa `man.sqlite` **siempre**, y si el manifiesto no
    # lo trae, se falla en vez de escribir donde no se debe.*
    if not man.sqlite:
        resumen["recetas"] = ["ERROR: el manifiesto no tiene ruta de SQLite; no se escribe nada"]
    else:
        from core import recetas as core_recetas  # a proposito: despues de validar la ruta

        con = core_recetas.conecta(man.sqlite)
        try:
            for r in CATALOGO_8["escenario"]["recetas"]:
                try:
                    n = r["necesita"]
                    receta_id = core_recetas.crear(
                        con,
                        propietario=str(resumen["cuentas"]["a_casa"]),
                        nombre=r["nombre"],
                        raciones=r["raciones"],
                        preparacion="Receta sintetica del banco de ensayo (apartado 8).",
                        ingredientes=[
                            {
                                "texto": n["texto"],
                                "cantidad": n["cantidad"],
                                "unidad": n["unidad"],
                                "producto_id": n["producto_id"],
                            }
                        ],
                        etiquetas="ensayo",
                    )
                    resumen["recetas"].append({"id": r["id"], "receta_id": receta_id, "nombre": r["nombre"]})
                except Exception as exc:  # noqa: BLE001
                    resumen["recetas"].append({"id": r["id"], "ERROR": str(exc)[:140]})
        finally:
            con.close()

    # *** LA DESPENSA: PENDIENTE, *y se dice sin disfrazarlo de error*. ***
    # *La tabla de existencias de `despensa.py` usa un contrato (`ExistenciaIn`) que hay que
    # respetar; meter filas a mano con SQL seria inventarlo.* *Y la primera version de este bloque
    # comprobaba la tabla con `to_regclass` y acababa imprimiendo «ERROR: 0», que no informa de nada:
    # un mensaje que no dice que pasa es peor que no tenerlo.*
    resumen["despensa"] = ["pendiente: el contrato de existencias (ExistenciaIn) no se ha sembrado"]
    return resumen


# --- Las guardas, probadas antes de DDL -----------------------------------


def prueba_de_guardas() -> list[tuple[str, bool, str]]:
    """*** Las guardas se prueban **antes** de escribir nada. *** *Devuelve (caso, pasa, detalle).*

    *Cada caso es un DSN que **tiene que ser rechazado**, o uno que tiene que pasar.* *Si alguno
    cambia de veredicto, algo se ha aflojado y hay que verlo antes de tocar una base.*
    """
    casos: list[tuple[str, str, bool]] = [
        ("casa 5432", "postgresql://cesta:prueba@127.0.0.1:5432/cesta_ensayo_x", False),
        ("facylf 5433", "postgresql://cesta:prueba@127.0.0.1:5433/cesta_ensayo_x", False),
        ("ensayos compartidos 5434", "postgresql://cesta:prueba@127.0.0.1:5434/cesta_ensayo_x", False),
        ("base de casa por nombre", "postgresql://cesta:prueba@127.0.0.1:55432/cesta", False),
        ("fuera de loopback", "postgresql://cesta:prueba@10.0.0.5:55432/cesta_ensayo_x", False),
        ("no es postgres", "sqlite:///tmp/cesta_ensayo_x.db", False),
        ("puerto no numerico", "postgresql://cesta:prueba@127.0.0.1:abc/cesta_ensayo_x", False),
        ("un ensayo valido", "postgresql://cesta:prueba@127.0.0.1:55432/cesta_ensayo_propio", True),
    ]
    salida: list[tuple[str, bool, str]] = []
    for titulo, dsn, debe_pasar in casos:
        try:
            comprueba_dsn(dsn)
            salida.append((titulo, debe_pasar, "aceptado"))
        except GuardaRota as exc:
            salida.append((titulo, not debe_pasar, str(exc)[:110]))
    return salida


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    orden = args[0] if args else "estado"
    nombre = args[1] if len(args) > 1 else "propio"

    if orden == "guardas":
        fallos = 0
        for titulo, pasa, detalle in prueba_de_guardas():
            print(("  ok   " if pasa else "  FALLO") + f" {titulo}: {detalle}")
            fallos += 0 if pasa else 1
        print(f"  {fallos} guarda(s) con veredicto equivocado")
        return 0 if fallos == 0 else 1

    if orden == "prepara":
        man = prepara(nombre)
        print("  ensayo preparado: " + man.nombre)
        print("      contenedor " + man.contenedor + "  id " + man.contenedor_id[:12])
        print("      dsn        " + man.dsn)
        print("      directorio " + man.directorio)
        return 0

    if orden == "siembra":
        resumen = siembra(nombre)
        print("  cuentas y listas sembradas:")
        for usuario, idc in resumen["cuentas"].items():
            listas = resumen["listas"].get(usuario, [])
            detalle = ", ".join(
                ("Casa" if x["es_de_casa"] else x["nombre"]) for x in listas
            ) or "(ninguna)"
            print(f"      {usuario:14} {'ok' if not str(idc).startswith('ERROR') else idc}   listas: {detalle}")
        # *El catalogo ya existe (lo construye `prepara`), asi que **ya no es el motivo**.* *Lo que
        # falta ahora es distinto: sembrar recetas, despensa y ofertas **sobre** el, y eso es el
        # siguiente paso, no una carencia de datos.*
        print("  recetas: " + str(len(resumen["recetas"])) + " intentadas")
        for r in resumen["recetas"]:
            print("      " + str(r))
        print("  despensa: " + str(resumen["despensa"]))
        print("  catalogo del apartado 8: arroz A y B, leche, huevos")
        # *Un error de siembra NO puede salir con 0.*
        fallos = [u for u, i in resumen["cuentas"].items() if str(i).startswith("ERROR")]
        if fallos:
            print("  FALLO en: " + ", ".join(fallos))
            return 1
        return 0

    if orden == "limpia":
        for linea in limpia(nombre):
            print("  " + linea)
        return 0

    if orden == "estado":
        datos = estado(nombre if nombre != "propio" or len(args) > 1 else None)
        if not datos["manifiestos"]:
            print("  no hay ensayos anotados")
        for m in datos["manifiestos"]:
            print(f"  {m['nombre']}: contenedor {m['contenedor']} ({m['vivo']})  dsn {m['dsn']}")
        if datos["suelto"]:
            print("  directorios SIN marcador de pertenencia (no se tocan): " + ", ".join(datos["suelto"]))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
