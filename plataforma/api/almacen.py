"""PostgreSQL: cuentas, listas y favoritos. Lo unico que se escribe.

Se usa psycopg en modo sincrono con un pool. FastAPI corre las rutas en un pool
de hilos cuando no son `async`, asi que esto es correcto y es mucho mas simple
de leer que la version asincrona. Con dos usuarios, el rendimiento no es el
problema que hay que resolver.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .ajustes import AJUSTES

_hasher = PasswordHasher()

# Tres a la vez: bastantes para invitar a quien quieras, pocos para que se
# te escape uno reenviado.
MAX_INVITACIONES_VIVAS = 3

# Cuantas cuentas se pueden crear en una hora, con el registro abierto.
#
# No es defensa contra nadie decidido: es que una pagina de registro abierta sin
# ningun freno se llena sola, y el dia que pase no quieres enterarte por el
# tamano del volumen de PostgreSQL. Diez caben de sobra aunque se apunte un
# grupo entero de amigos a la vez.
ALTAS_POR_HORA = 10

# La zona de casa, para contar dias. Es la misma que `core/config.py`
# (`SCRAP_TZ`, por defecto Europe/Madrid), y esta escrita aqui por una razon de
# capas: este modulo es el unico que sabe de PostgreSQL y no importa nada del
# proyecto de recoleccion -- `core.config` crea carpetas al importarse y el
# contenedor de la API monta gold en solo lectura. Que los dos numeros no se
# separen lo vigila `tests/test_avisos_cadena.py`.
ZONA_HORARIA = os.environ.get("SCRAP_TZ", "Europe/Madrid")
_pool: ConnectionPool | None = None


class UsuarioRepetido(RuntimeError):
    """Ya hay una cuenta con ese nombre de usuario."""


class DemasiadasAltas(RuntimeError):
    """Se ha llegado al tope de cuentas nuevas por hora."""


def arranca(espera: float = 30) -> None:
    """Arranca el almacen: el pool de conexiones y, si toca, las migraciones.

    `espera` es cuanto se aguanta a que la base conteste, y existe por la cadena
    diaria: `projects/cesta/avisos.py` pasa por aqui desde el PC, donde la base de
    casa **no publica su puerto** (`docker-compose.yml`: "solo lo alcanza la API"),
    y a las 06:00 no se puede estar treinta segundos esperando a un puerto que no
    va a contestar. La API sigue con los treinta de siempre.

    **Se prueba la base con una conexion suelta antes de crear el pool**, y esto se
    aprendio midiendo: el pool abre un hilo que reintenta conectar, asi que cuando la
    base no esta, el fallo tarda lo que tarde el `wait` **mas** otros cinco segundos
    de ese hilo muriendo, y el proceso termina con un aviso de hilo que no para. Sin
    pool no hay hilo: si la base no esta, esto falla en el acto y no deja nada detras.
    """
    global _pool
    if _pool is None:
        # El tope de la conexion suelta y el de las del pool son el mismo, y ninguno
        # baja de tres segundos: una conexion no puede quedarse colgada para siempre
        # contra un puerto que no contesta (un cortafuegos que descarta los paquetes,
        # en vez de rechazarlos).
        tope = max(int(espera), 3)
        psycopg.connect(AJUSTES.postgres, connect_timeout=tope).close()
        _pool = ConnectionPool(AJUSTES.postgres, min_size=1, max_size=8,
                               kwargs={"row_factory": dict_row,
                                       "connect_timeout": tope})
        _pool.wait(timeout=espera)
        migra()


def para() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def arrancado() -> bool:
    """Si el pool esta en marcha.

    Existe por el paso de la cadena (`projects/cesta/avisos.py`): si el almacen ya
    estaba arrancado -- porque quien llama es la API, o una prueba de punta a punta
    que ya lo arranco --, ese paso **no puede cerrarlo** al terminar. Seria apagarle
    el almacen a quien se lo presto.
    """
    return _pool is not None


@contextmanager
def cursor() -> Iterator[psycopg.Cursor]:
    if _pool is None:
        raise RuntimeError("el almacen no esta arrancado")
    with _pool.connection() as con, con.cursor() as cur:
        yield cur


# El esquema usa `gen_random_uuid()`, que es del nucleo de PostgreSQL desde la
# 13, y `CREATE OR REPLACE VIEW` con columnas nuevas, que pide la 14.
POSTGRES_MINIMO = 14

# Los tres que ya venian escritos en el CHECK de la tabla.
ALERTA_TIPOS = ("baja_de", "minimo_90d", "cualquier_bajada")


def migra() -> None:
    """Aplica los .sql de plataforma/sql por orden de nombre. Son idempotentes."""
    with cursor() as cur:
        version = cur.execute("SHOW server_version_num").fetchone()
        # psycopg puede devolver la fila como dict o como tupla segun la fabrica
        # de filas que este puesta; se acepta cualquiera de las dos.
        crudo = next(iter(version.values())) if isinstance(version, dict) else version[0]
        numero = int(crudo)
    if numero < POSTGRES_MINIMO * 10000:
        raise RuntimeError(
            f"Esta base de datos es PostgreSQL {numero // 10000}. Cesta necesita "
            f"la {POSTGRES_MINIMO} o mas nueva: el esquema usa gen_random_uuid(), "
            f"que es del nucleo desde la 13, y vistas que se reemplazan en "
            f"caliente. Cambia la imagen en docker-compose.yml.")
    carpeta = Path(__file__).resolve().parent.parent / "sql"
    for fichero in sorted(carpeta.glob("*.sql")):
        with cursor() as cur:
            cur.execute(fichero.read_text(encoding="utf-8"))


# --------------------------------------------------------------- personas ---

def crea_usuario(usuario: str, nombre: str, clave: str) -> dict:
    """Da de alta a una persona. El nombre repetido sale por su propia puerta.

    `UsuarioRepetido` en vez de dejar subir el error de PostgreSQL: quien llama
    tiene que poder decirle a la persona "ese nombre ya esta cogido" sin leer el
    texto de una restriccion de la base de datos, que es un detalle del esquema
    y cambia sin avisar.
    """
    try:
        with cursor() as cur:
            cur.execute("""
                INSERT INTO usuario (usuario, nombre, clave_hash) VALUES (%s, %s, %s)
                RETURNING id, usuario, nombre
            """, (usuario.strip().lower(), nombre.strip(), _hasher.hash(clave)))
            return cur.fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise UsuarioRepetido(usuario.strip().lower()) from exc


def altas_en_la_ultima_hora() -> int:
    with cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM usuario "
                    "WHERE creado_en > now() - interval '1 hour'")
        return int(cur.fetchone()["n"])


def personas() -> list[dict]:
    """Quien tiene cuenta y desde cuando.

    Con el registro abierto esto **no es un adorno**: es lo unico que convierte
    "cualquiera puede apuntarse" en algo que se puede vigilar. Una puerta
    abierta sin una ventana por la que mirar quien ha entrado no es una
    decision, es un descuido.
    """
    with cursor() as cur:
        cur.execute("""
            SELECT u.id, u.usuario, u.nombre, u.creado_en,
                   (SELECT max(s.creada_en) FROM sesion s
                     WHERE s.usuario_id = u.id) AS ultima_sesion
              FROM usuario u ORDER BY u.creado_en
        """)
        return [{"id": str(f["id"]), "usuario": f["usuario"], "nombre": f["nombre"],
                 "creado_en": f["creado_en"].isoformat(),
                 "ultima_sesion": (f["ultima_sesion"].isoformat()
                                   if f["ultima_sesion"] else None)}
                for f in cur.fetchall()]


def entra(usuario: str, clave: str, dispositivo: str | None = None) -> tuple[str, dict] | None:
    """Devuelve (token en claro, usuario) o None. El token solo existe aqui."""
    with cursor() as cur:
        cur.execute("SELECT id, usuario, nombre, clave_hash FROM usuario WHERE usuario = %s",
                    (usuario.strip().lower(),))
        fila = cur.fetchone()
    if not fila:
        # Se gasta el mismo tiempo que si existiera, para no delatar por
        # cuanto tarda que ese usuario no esta dado de alta.
        _hasher.hash(clave)
        return None
    try:
        _hasher.verify(fila["clave_hash"], clave)
    except VerifyMismatchError:
        return None

    token = secrets.token_urlsafe(32)
    with cursor() as cur:
        cur.execute("""
            INSERT INTO sesion (token, usuario_id, dispositivo, expira_en)
            VALUES (%s, %s, %s, %s)
        """, (_huella(token), fila["id"], dispositivo,
              datetime.now(timezone.utc) + timedelta(days=AJUSTES.dias_sesion)))
    return token, {"id": str(fila["id"]), "usuario": fila["usuario"], "nombre": fila["nombre"]}


def quien(token: str | None) -> dict | None:
    if not token:
        return None
    with cursor() as cur:
        cur.execute("""
            SELECT u.id, u.usuario, u.nombre FROM sesion s
              JOIN usuario u ON u.id = s.usuario_id
             WHERE s.token = %s AND s.expira_en > now()
        """, (_huella(token),))
        fila = cur.fetchone()
    return {"id": str(fila["id"]), "usuario": fila["usuario"], "nombre": fila["nombre"]} if fila else None


def sale(token: str) -> None:
    with cursor() as cur:
        cur.execute("DELETE FROM sesion WHERE token = %s", (_huella(token),))


def _huella(token: str) -> str:
    """En la base se guarda el hash, nunca el token. Si alguien lee la tabla, no
    puede entrar con lo que ha leido."""
    return hashlib.sha256(token.encode()).hexdigest()


# ----------------------------------------------------------------- listas ---

def listas_de(usuario_id: str) -> list[dict]:
    with cursor() as cur:
        cur.execute("""
            SELECT l.id, l.nombre, l.es_de_casa, l.creada_en,
                   l.dueno_id = %(u)s AS soy_dueno,
                   a.papel,
                   (SELECT count(*) FROM lista_linea li
                     WHERE li.lista_id = l.id AND li.borrado_en IS NULL) AS lineas,
                   (SELECT count(*) FROM lista_linea li
                     WHERE li.lista_id = l.id AND li.borrado_en IS NULL
                       AND li.tachado_en IS NOT NULL) AS tachadas,
                   (SELECT count(*) FROM lista_acceso x WHERE x.lista_id = l.id) AS personas
              FROM lista l
              JOIN lista_acceso a ON a.lista_id = l.id AND a.usuario_id = %(u)s
             WHERE l.archivada_en IS NULL
             ORDER BY l.es_de_casa DESC, l.creada_en DESC
        """, {"u": usuario_id})
        return [dict(f, id=str(f["id"])) for f in cur.fetchall()]


def crea_lista(usuario_id: str, nombre: str, es_de_casa: bool = False) -> dict:
    with cursor() as cur:
        cur.execute("""
            INSERT INTO lista (nombre, dueno_id, es_de_casa) VALUES (%s, %s, %s)
            RETURNING id, nombre, es_de_casa
        """, (nombre.strip(), usuario_id, es_de_casa))
        lista = cur.fetchone()
        cur.execute("""
            INSERT INTO lista_acceso (lista_id, usuario_id, papel, aceptado_en)
            VALUES (%s, %s, 'dueno', now())
        """, (lista["id"], usuario_id))
    return dict(lista, id=str(lista["id"]))


def papel_en(lista_id: str, usuario_id: str) -> str | None:
    with cursor() as cur:
        cur.execute("SELECT papel FROM lista_acceso WHERE lista_id = %s AND usuario_id = %s",
                    (lista_id, usuario_id))
        fila = cur.fetchone()
    return fila["papel"] if fila else None


def comparte(lista_id: str, con_usuario: str, quien_invita: str,
             papel: str = "escribe") -> dict | None:
    with cursor() as cur:
        cur.execute("SELECT id, nombre FROM usuario WHERE usuario = %s",
                    (con_usuario.strip().lower(),))
        otro = cur.fetchone()
        if not otro:
            return None
        cur.execute("""
            INSERT INTO lista_acceso (lista_id, usuario_id, papel, invitado_por, aceptado_en)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (lista_id, usuario_id) DO UPDATE SET papel = EXCLUDED.papel
        """, (lista_id, otro["id"], papel, quien_invita))
    return {"usuario": con_usuario, "nombre": otro["nombre"], "papel": papel}


def lineas_de(lista_id: str) -> list[dict]:
    """Las lineas vivas de una lista, con el nombre de quien las anadio.

    **`LEFT JOIN` en el autor, y no `JOIN`.** Con un `JOIN` a secas, la linea que alguien
    anadio a una lista ajena y luego se dio de baja **desaparecia de la pantalla**: la fila
    seguia en la base (con `anadido_por` a NULL, que es lo que promete `borrar_usuario` en
    `plataforma/sql/003_mas_de_dos.sql`: *"las lineas en listas ajenas pierden el autor pero
    no desaparecen"*), pero la consulta no la devolvia, asi que la otra persona veia su
    compra menguada sin saber por que. Medido en un navegador el 24 de septiembre de 2026:
    4 lineas en la lista, se da de baja quien anadio una, y la pantalla ensena 3.
    """
    with cursor() as cur:
        cur.execute("""
            SELECT li.id, li.grupo_id, li.producto_id, li.nombre_visto, li.cantidad,
                   li.nota, li.tachado_en, li.anadido_en, li.en_carrito,
                   li.cadena_elegida,
                   qa.nombre AS anadido_por, qt.nombre AS tachado_por
              FROM lista_linea li
              LEFT JOIN usuario qa ON qa.id = li.anadido_por
              LEFT JOIN usuario qt ON qt.id = li.tachado_por
             WHERE li.lista_id = %s AND li.borrado_en IS NULL
             ORDER BY li.en_carrito, li.anadido_en
        """, (lista_id,))
        return [dict(f, id=str(f["id"])) for f in cur.fetchall()]


def anade_linea(lista_id: str, usuario_id: str, linea_id: str, nombre: str,
                grupo_id: int | None = None, producto_id: str | None = None,
                cantidad: int = 1, nota: str | None = None,
                cadena_elegida: str | None = None) -> dict:
    """El id lo trae el movil. Si llega dos veces, no se duplica: se actualiza.

    La tienda elegida se actualiza con `COALESCE`: subir otra vez una linea que se
    anadio sin tienda **no puede borrar** la tienda que se eligio despues en otro
    movil. Y al reves si funciona: ponerla es ponerla.
    """
    with cursor() as cur:
        cur.execute("""
            INSERT INTO lista_linea
                (id, lista_id, grupo_id, producto_id, nombre_visto, cantidad, nota,
                 anadido_por, cadena_elegida)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
               SET cantidad = EXCLUDED.cantidad, nota = EXCLUDED.nota,
                   cadena_elegida = COALESCE(EXCLUDED.cadena_elegida,
                                             lista_linea.cadena_elegida),
                   borrado_en = NULL, tocado_en = now()
            RETURNING id, grupo_id, producto_id, nombre_visto, cantidad, nota,
                      cadena_elegida
        """, (linea_id, lista_id, grupo_id, producto_id, nombre, cantidad, nota,
              usuario_id, cadena_elegida))
        return dict(cur.fetchone(), id=linea_id)


SIN_CAMBIAR = object()
"""Centinela para distinguir «no me lo toques» de «ponlo a NULL».

Sin esto no se puede quitar la tienda de una linea: `None` significaria las dos
cosas a la vez (no lo cambies / borralo), y la pantalla no tendria forma de
deshacer una asignacion sin borrar la linea entera.
"""


def cambia_linea(lista_id: str, linea_id: str, usuario_id: str, *,
                 tachado: bool | None = None, cantidad: int | None = None,
                 nota: str | None = None, borrado: bool | None = None,
                 en_carrito: bool | None = None,
                 cadena_elegida=SIN_CAMBIAR,
                 momento: datetime | None = None) -> dict | None:
    """Idempotente a proposito: tachar algo ya tachado no hace nada y no es un
    error. Si los dos tachais a la vez, gana quien lo hizo antes y el otro ve lo
    que queria ver.

    `momento` es la hora del MOVIL, no la de llegada: tachar sin cobertura a las
    18:04 y subirlo a las 18:20 cuenta como las 18:04, que si no el orden de los
    hechos se lo inventa el servidor.
    """
    cuando = momento or datetime.now(timezone.utc)
    trozos, args = [], []
    if tachado is True:
        trozos.append("en_carrito = true")
        # COALESCE: si ya estaba tachado, se respeta el primero.
        trozos.append("tachado_en = LEAST(COALESCE(tachado_en, %s), %s)")
        args += [cuando, cuando]
        trozos.append("tachado_por = COALESCE(tachado_por, %s)")
        args.append(usuario_id)
    elif tachado is False:
        trozos += ["tachado_en = NULL", "tachado_por = NULL", "en_carrito = false"]
    if cantidad is not None:
        trozos.append("cantidad = %s")      # gana el ultimo, a proposito
        args.append(cantidad)
    if nota is not None:
        trozos.append("nota = %s")
        args.append(nota)
    if en_carrito is not None:
        # Meter en el carro es tachar: son la misma accion vista de dos formas,
        # y el movil manda la que entiende. Mantenerlas coherentes evita que una
        # linea acabe "en el carro" pero sin tachar.
        trozos.append("en_carrito = %s")
        args.append(en_carrito)
        if en_carrito:
            trozos.append("tachado_en = LEAST(COALESCE(tachado_en, %s), %s)")
            args += [cuando, cuando]
            trozos.append("tachado_por = COALESCE(tachado_por, %s)")
            args.append(usuario_id)
        else:
            trozos += ["tachado_en = NULL", "tachado_por = NULL"]
    if borrado is True:
        trozos.append("borrado_en = COALESCE(borrado_en, %s)")
        args.append(cuando)
    elif borrado is False:
        trozos.append("borrado_en = NULL")
    # La tienda donde se compra esta linea. Se guarda para que el total y las
    # sublistas sean **una decision de la persona** y no una propuesta que se
    # recalcula cada vez que se abre la pantalla (ver `008_linea_en_tienda.sql`).
    if cadena_elegida is not SIN_CAMBIAR:
        trozos.append("cadena_elegida = %s")
        args.append(cadena_elegida)
    if not trozos:
        return None
    trozos.append("tocado_en = now()")
    with cursor() as cur:
        cur.execute(f"""
            UPDATE lista_linea SET {', '.join(trozos)}
             WHERE id = %s AND lista_id = %s
            RETURNING id, cantidad, nota, tachado_en, borrado_en, en_carrito,
                      cadena_elegida
        """, (*args, linea_id, lista_id))
        fila = cur.fetchone()
    return dict(fila, id=str(fila["id"])) if fila else None


def pon_tienda(lista_id: str, cadena: str | None, usuario_id: str,
               lineas: list[str] | None = None) -> int:
    """Pone (o quita) la tienda de varias lineas de una vez.

    Existe por dos botones de la pantalla que son la misma operacion con distinto
    alcance: «esta sublista se compra en X» y «quitar toda la sublista». Sin esto,
    una lista de treinta lineas pide treinta peticiones para cambiar de opinion, y
    en el pasillo eso no se hace.

    `cadena=None` deja las lineas **sin decidir** (siguen en la lista y vuelven a
    «sin asignar»); no las borra. Borrar la sublista es `borra_lineas_de_tienda`.
    """
    if not lineas:
        return 0
    with cursor() as cur:
        cur.execute("""
            UPDATE lista_linea SET cadena_elegida = %s, tocado_en = now()
             WHERE lista_id = %s AND id = ANY(%s) AND borrado_en IS NULL
        """, (cadena, lista_id, list(lineas)))
        return cur.rowcount


def borra_lineas_de_tienda(lista_id: str, cadena: str, usuario_id: str,
                           momento: datetime | None = None) -> int:
    """Borra (de mentira) toda la sublista de una tienda, del tiron.

    Marcadas, no borradas de verdad: la fila se queda y `limpiar_lineas_borradas`
    se la lleva a los 30 dias. Deshacer veinte lineas borradas sin querer en el
    pasillo no puede depender de una copia de seguridad.
    """
    cuando = momento or datetime.now(timezone.utc)
    with cursor() as cur:
        cur.execute("""
            UPDATE lista_linea SET borrado_en = COALESCE(borrado_en, %s), tocado_en = now()
             WHERE lista_id = %s AND cadena_elegida = %s AND borrado_en IS NULL
        """, (cuando, lista_id, cadena))
        return cur.rowcount


def archiva_lista(lista_id: str, usuario_id: str) -> bool:
    """La lista desaparece de la pantalla. Solo quien la creo.

    Archivar y no borrar: una lista compartida que se borra de verdad le quita la
    compra a otra persona de un toque. Con la marca, el dia que haga falta
    recuperarla esta entera en la base.
    """
    with cursor() as cur:
        cur.execute("""
            UPDATE lista SET archivada_en = now()
             WHERE id = %s AND dueno_id = %s AND archivada_en IS NULL
        """, (lista_id, usuario_id))
        return cur.rowcount > 0


def renombra_lista(lista_id: str, nombre: str, usuario_id: str) -> dict | None:
    """Ponerle nombre a una lista. Cualquiera que escriba en ella, no solo el dueno.

    Con varias listas, «Lista» y «Lista (2)» dejan de distinguirse justo cuando mas
    hacen falta: quien compra para dos casas necesita llamarlas por su nombre, y
    quien las usa a diario es quien escribe en ellas.
    """
    limpio = nombre.strip()[:80]
    if not limpio:
        return None
    with cursor() as cur:
        cur.execute("""
            UPDATE lista SET nombre = %s
             WHERE id = %s
               AND EXISTS (SELECT 1 FROM lista_acceso a
                            WHERE a.lista_id = lista.id AND a.usuario_id = %s
                              AND a.papel <> 'mira')
            RETURNING id, nombre
        """, (limpio, lista_id, usuario_id))
        fila = cur.fetchone()
    return dict(fila, id=str(fila["id"])) if fila else None


# -------------------------------------------------------------- favoritos ---

def favoritos_de(usuario_id: str) -> list[dict]:
    with cursor() as cur:
        cur.execute("""SELECT grupo_id, producto_id, anadido_en FROM favorito
                        WHERE usuario_id = %s ORDER BY anadido_en DESC""", (usuario_id,))
        return cur.fetchall()


def anade_favorito(usuario_id: str, grupo_id: int | None, producto_id: str | None) -> None:
    with cursor() as cur:
        if grupo_id is not None:
            cur.execute("""INSERT INTO favorito (usuario_id, grupo_id) VALUES (%s, %s)
                           ON CONFLICT DO NOTHING""", (usuario_id, grupo_id))
        else:
            cur.execute("""INSERT INTO favorito (usuario_id, producto_id) VALUES (%s, %s)
                           ON CONFLICT DO NOTHING""", (usuario_id, producto_id))


def quita_favorito(usuario_id: str, grupo_id: int | None, producto_id: str | None) -> None:
    with cursor() as cur:
        if grupo_id is not None:
            cur.execute("DELETE FROM favorito WHERE usuario_id = %s AND grupo_id = %s",
                        (usuario_id, grupo_id))
        else:
            cur.execute("DELETE FROM favorito WHERE usuario_id = %s AND producto_id = %s",
                        (usuario_id, producto_id))


def mis_grupos(usuario_id: str) -> list[int]:
    """Los grupos de **esta persona**: sus listas y sus favoritos.

    Es "lo mio" para la pantalla de bajadas, que contesta a la pregunta *"¿ha bajado
    algo de lo mio?"* -- la cuarta de las cuatro con las que se abre la aplicacion, y
    la unica que hasta hoy no tenia por donde contestarse.

    Van las dos cosas y por eso es una consulta: lo que alguien tiene apuntado en una
    lista es lo que va a comprar, y lo que ha marcado como favorito es lo que mira.
    Ni una linea borrada cuenta (ya no esta en la lista) ni un grupo nulo: una linea
    sin grupo es un producto suelto, y sin grupo no hay nada que comparar.

    Se devuelven **identificadores de grupo**, no productos: el historico de precios
    se guarda por producto de cada cadena, y quien lo cruza con esto es
    `movimientos.bajadas`.
    """
    with cursor() as cur:
        cur.execute("""
            SELECT DISTINCT grupo_id FROM (
                SELECT li.grupo_id FROM lista_linea li
                  JOIN lista l ON l.id = li.lista_id
                  JOIN lista_acceso la ON la.lista_id = l.id
                 WHERE la.usuario_id = %s AND li.borrado_en IS NULL
                UNION
                SELECT f.grupo_id FROM favorito f WHERE f.usuario_id = %s
            ) x WHERE grupo_id IS NOT NULL""", (usuario_id, usuario_id))
        return [int(f["grupo_id"]) for f in cur.fetchall()]


# ------------------------------------------------------------- habituales ---
#
# Lo que esta persona ha puesto mas veces en sus listas. Es lo que sostiene el
# mosaico de `/api/habituales` (ver `api/habituales.py` para los tres origenes).
#
# Las tres decisiones que hay detras de esta consulta -- contar tambien las lineas
# borradas, contar solo lo que anadio esta persona y pesar por recencia -- estan
# escritas en el docstring de `historial_de`, que es donde se leen antes de
# tocarla. Del SQL, lo unico que hay que saber aqui: `y` es el filtro del autor y
# `orden` el criterio que cambia entre el historial propio y el de todos.

# La vida media del decaimiento, en dias. El porque, en `historial_de`.
VIDA_MEDIA_DIAS = 30

# El propio: ordenado por lo reciente que se ha anadido, y a igualdad por veces.
# `grupo_id` al final para que la cuadricula no baile entre dos peticiones: sin un
# ultimo criterio estable, PostgreSQL puede devolver el empate en cualquier orden.
_ORDEN_PROPIO = "peso DESC, veces DESC, grupo_id"
# El de todos: primero lo que ha anadido MAS GENTE DISTINTA, que es la unica
# lectura honesta de "lo mas comprado por todos". Con dos personas, ordenar solo
# por veces haria que lo que compra una sola de ellas pareciera de todos.
_ORDEN_DE_TODOS = "personas DESC, peso DESC, veces DESC, grupo_id"

SQL_HISTORIAL = """
    SELECT grupo_id,
           count(*) AS veces,
           max(anadido_en)::date::text AS ultima_vez,
           count(DISTINCT anadido_por) AS personas,
           sum(power(0.5::float8,
                     EXTRACT(EPOCH FROM (now() - anadido_en))::float8
                     / 86400.0 / {vida})) AS peso
      FROM lista_linea
     WHERE grupo_id IS NOT NULL {y}
     GROUP BY grupo_id
     ORDER BY {orden}
     LIMIT %(n)s
"""


def consulta_historial(suyo: bool = True) -> str:
    """El SQL del ranking, montado y listo para ejecutar.

    Se saca a una funcion para que las tres reglas del historial se puedan leer
    desde fuera -- y vigilar desde una prueba -- sin PostgreSQL delante: el filtro
    del autor y el orden no son los mismos en el historial propio que en el de
    todos, y son justo las dos cosas que no se pueden equivocar.
    """
    return SQL_HISTORIAL.format(
        vida=VIDA_MEDIA_DIAS,
        y="AND anadido_por = %(u)s" if suyo else "",
        orden=_ORDEN_PROPIO if suyo else _ORDEN_DE_TODOS)


def _ranking(usuario_id: str | None, limite: int) -> list[dict]:
    """El ranking, propio o de todos. Uno solo para que no se separen las reglas."""
    suyo = usuario_id is not None
    parametros: dict = {"n": int(limite)}
    if suyo:
        parametros["u"] = usuario_id
    with cursor() as cur:
        cur.execute(consulta_historial(suyo), parametros)
        return [{"grupo_id": f["grupo_id"], "veces": f["veces"],
                 "ultima_vez": f["ultima_vez"], "personas": f["personas"]}
                for f in cur.fetchall()]


def historial_de(usuario_id: str, limite: int = 72) -> list[dict]:
    """Los grupos que esta persona ha anadido, lo reciente pesando mas.

    Tres decisiones, y las tres estan en el SQL para que la regla y la consulta no
    se puedan separar:

    **Se cuentan todas las lineas, incluidas las borradas.** `lista_linea` no borra
    de verdad: pone `borrado_en` y `limpiar_lineas_borradas` las quita a los 30
    dias. *Una lista se vacia al terminar la compra; el habito no.* Contando solo
    las lineas vivas, el historial de quien usa la lista como se usa una lista
    -- vaciandola despues de comprar -- estaria siempre vacio, y el mosaico
    ensenaria lo de todos a alguien que lleva meses comprando.

    **Se cuenta por `anadido_por`, no por "las listas en las que estoy".** En una
    lista compartida se apunta lo que trae el otro, y eso no es tu historial: es el
    suyo. Ademas, quien tiene permiso de solo mirar una lista no puede sacar de
    aqui lo que hay dentro de ella.

    **Lo reciente pesa mas, con un decaimiento y no con un corte.** El encargo deja
    elegir entre contar solo los ultimos 90 dias o pesar por recencia, y pide
    escribirlo. Se eligio pesar, con una vida media de 30 dias:

        - con un corte a 90 dias, un producto desaparece del mosaico de un dia para
          otro al cruzar el dia 90, y `veces` tendria que pasar a significar "veces
          en 90 dias". Dos numeros distintos con el mismo nombre es justo el error
          que este proyecto ya pago una vez con "imposible" (core/comparacion.py);
        - noventa dias, ademas, es un numero que no se puede defender frente a 60 o
          a 180. Una vida media es una sola linea y se explica sola;
        - con 30 dias de vida media, lo que se anadio este mes pesa el doble que lo
          del mes pasado y a los 90 dias pesa un octavo -- casi el mismo trabajo
          que aquel corte, sin el borde. Nueve veces hace tres meses, que es el
          caso que el encargo pone como "eso no es un habito", pesa poco mas que
          una vez de ayer.

    `veces` es el recuento entero, sin decaimiento: es lo que se le ensena a la
    persona, y tiene que ser lo que de verdad hizo. El decaimiento decide **el
    orden**, nada mas.
    """
    return _ranking(usuario_id, limite)


def mas_comprados(limite: int = 72) -> list[dict]:
    """Lo mismo sobre las lineas de todo el mundo, sin decir de quien es cada una.

    Es el segundo origen del mosaico: quien acaba de crearse la cuenta no tiene
    historial, y con esto la pantalla no se ve vacia el primer dia. Lo que sale de
    aqui es un recuento agregado -- "esto lo ha anadido alguien N veces" --, nunca
    quien lo anadio.
    """
    return _ranking(None, limite)


# ----------------------------------------------------------------- alertas ---
#
# La tabla estaba en el esquema desde el primer dia y no la usaba nadie. Ver
# `api/alertas.py` para lo que decide si una salta; aqui solo se guardan.

def alertas_de(usuario_id: str) -> list[dict]:
    with cursor() as cur:
        cur.execute("""SELECT id, grupo_id, tipo, umbral_cent, creada_en, vista_en,
                              salto_en, salto_texto
                         FROM alerta WHERE usuario_id = %s
                        ORDER BY creada_en DESC""", (usuario_id,))
        return cur.fetchall()


def alertas_por_saltar() -> list[dict]:
    """Las alertas de todo el mundo que no han saltado y nadie ha visto.

    Son para el vigilante (`api/vigilante.py`), y por eso **no** llevan `usuario_id`:
    evaluar una alerta no necesita saber de quien es, y lo que no viaja no se puede
    filtrar por descuido. `vista_en IS NULL` deja fuera las ya contadas -- una alerta
    se dispara una vez -- y `salto_en IS NULL` las que ya saltaron.
    """
    with cursor() as cur:
        cur.execute("""SELECT id, grupo_id, tipo, umbral_cent FROM alerta
                        WHERE vista_en IS NULL AND salto_en IS NULL""")
        return cur.fetchall()


def avisos_del_dia() -> dict:
    """Cuantos avisos han saltado hoy y cuantos siguen esperando. Solo cuenta.

    Es lo que pide el §6 del encargo -- *"que el resumen diario diga cuantas
    saltaron"* --, y lo lee `projects/cesta/avisos.py` despues de su pasada.

    **El dia se cuenta en la zona de casa, no en la del servidor.** `salto_en` es un
    `timestamptz` y el contenedor de PostgreSQL corre en UTC: a las 06:00 los dos
    dias coinciden, pero a las 00:30 no, y un "hoy" que unas veces es hoy y otras
    ayer no se puede leer. La zona es la misma que usa el resto del proyecto
    (`core.config.ZONA_HORARIA`), que es de donde sale el `Europe/Madrid`.

    Los tres numeros dicen tres cosas distintas, y por eso van los tres:
    `saltaron_hoy` es lo que se le ensena a nadie (es el resumen), `sin_saltar` son
    las que esperan su dia, y `por_mirar` es **la cola del vigilante** -- sin saltar
    y sin que nadie las haya visto --, que es el numero con el que se comprueba que
    la pasada ha hecho su trabajo.
    """
    zona = ZONA_HORARIA
    with cursor() as cur:
        cur.execute("""
            SELECT count(*) FILTER (
                       WHERE (salto_en AT TIME ZONE %(z)s)::date
                             = (now() AT TIME ZONE %(z)s)::date) AS saltaron_hoy,
                   count(*) FILTER (WHERE salto_en IS NULL)             AS sin_saltar,
                   count(*) FILTER (WHERE salto_en IS NULL
                                      AND vista_en IS NULL)             AS por_mirar
              FROM alerta""", {"z": zona})
        return dict(cur.fetchone())


def marca_alerta_saltada(alerta_id: str, texto: str) -> bool:
    """Apunta que esta alerta salto, y con que frase. False si ya estaba apuntada.

    El `AND salto_en IS NULL` es lo que hace que dos pasadas seguidas del vigilante no
    cuenten lo mismo dos veces, y que lo que se cuenta sea **lo que se apunto** y no lo
    que se intento apuntar.

    **El texto se guarda y no se recalcula**: la frase se mide contra el gold de ese
    dia, y gold se reescribe cada manana. Sin guardarla, el aviso que alguien vio ayer
    contaria hoy otra cosa, o ninguna.
    """
    with cursor() as cur:
        cur.execute("""UPDATE alerta SET salto_en = now(), salto_texto = %s
                        WHERE id = %s AND salto_en IS NULL""", (texto, alerta_id))
        return cur.rowcount > 0


def crea_alerta(usuario_id: str, grupo_id: int, tipo: str,
                umbral_cent: int | None = None) -> dict:
    """Una alerta por grupo y tipo. Repetirla la actualiza en vez de duplicarla.

    Sin eso, pulsar dos veces la campana deja dos avisos identicos y el dia que
    salten llegan por duplicado. Y al volver a crearla se limpian `vista_en` y
    `salto_en`: pedir otra vez la misma alerta es volver a empezar, y si no se
    limpiara, una alerta que ya salto no volveria a saltar nunca.
    """
    if tipo not in ALERTA_TIPOS:
        raise ValueError(f"tipo de alerta desconocido: {tipo}")
    if tipo == "baja_de" and not umbral_cent:
        raise ValueError("una alerta 'baja_de' necesita un umbral")
    with cursor() as cur:
        cur.execute("""
            INSERT INTO alerta (usuario_id, grupo_id, tipo, umbral_cent)
                 VALUES (%s, %s, %s, %s)
            ON CONFLICT (usuario_id, grupo_id, tipo) DO UPDATE
                    SET umbral_cent = EXCLUDED.umbral_cent, vista_en = NULL,
                        salto_en = NULL, salto_texto = NULL
              RETURNING id, grupo_id, tipo, umbral_cent, creada_en, vista_en,
                        salto_en, salto_texto
        """, (usuario_id, grupo_id, tipo, umbral_cent))
        return cur.fetchone()


def borra_alerta(usuario_id: str, alerta_id: str) -> bool:
    with cursor() as cur:
        cur.execute("DELETE FROM alerta WHERE id = %s AND usuario_id = %s",
                    (alerta_id, usuario_id))
        return cur.rowcount > 0


def marca_alertas_vistas(usuario_id: str, ids: list[str]) -> int:
    """Una alerta se cuenta una vez. Un aviso que se repite deja de leerse."""
    if not ids:
        return 0
    with cursor() as cur:
        cur.execute("""UPDATE alerta SET vista_en = now()
                        WHERE usuario_id = %s AND id = ANY(%s)""",
                    (usuario_id, list(ids)))
        return cur.rowcount


def preferencias_de(usuario_id: str) -> dict:
    with cursor() as cur:
        cur.execute("SELECT clave, valor FROM preferencia WHERE usuario_id = %s", (usuario_id,))
        return {f["clave"]: f["valor"] for f in cur.fetchall()}


def guarda_preferencia(usuario_id: str, clave: str, valor: Any) -> None:
    import json
    with cursor() as cur:
        cur.execute("""INSERT INTO preferencia (usuario_id, clave, valor) VALUES (%s, %s, %s)
                       ON CONFLICT (usuario_id, clave) DO UPDATE SET valor = EXCLUDED.valor""",
                    (usuario_id, clave, json.dumps(valor)))


# ----------------------------------------------------------- invitaciones ---

def crea_invitacion(lista_id: str, usuario_id: str, papel: str = "escribe",
                    usos: int = 1, dias: int = 7) -> dict:
    """Un codigo para un enlace. Caduca, y se puede revocar.

    Un enlace que dura para siempre acaba reenviado en un grupo que no era.
    """
    codigo = secrets.token_urlsafe(9)
    with cursor() as cur:
        # Un enlace reenviado sin querer mete en la lista a gente que no sabes
        # que esta. Tres vivos a la vez es de sobra para invitar a quien quieras
        # y poco para que se te escape.
        cur.execute("SELECT coalesce(v.vivas, 0) AS vivas FROM (SELECT 1) t "
                    "LEFT JOIN invitaciones_vivas v ON v.lista_id = %s",
                    (lista_id,))
        fila = cur.fetchone()
        if fila and fila["vivas"] >= MAX_INVITACIONES_VIVAS:
            raise ValueError("ya hay tres enlaces sin usar para esta lista; "
                             "anula alguno antes de crear otro")
        cur.execute("""
            INSERT INTO invitacion (codigo, lista_id, creada_por, papel, usos_max, expira_en)
            VALUES (%s, %s, %s, %s, %s, now() + (%s || ' days')::interval)
            RETURNING codigo, papel, usos_max, expira_en
        """, (codigo, lista_id, usuario_id, papel, usos, dias))
        return cur.fetchone()


def acepta_invitacion(codigo: str, usuario_id: str) -> dict | None:
    """Entra en la lista. Si ya estabas dentro, no pasa nada y no gasta un uso."""
    with cursor() as cur:
        cur.execute("""
            SELECT i.lista_id, i.papel, i.usos, i.usos_max, i.creada_por, l.nombre
              FROM invitacion i JOIN lista l ON l.id = i.lista_id
             WHERE i.codigo = %s AND i.revocada_en IS NULL AND i.expira_en > now()
               AND i.usos < i.usos_max
        """, (codigo,))
        inv = cur.fetchone()
        if not inv:
            return None
        cur.execute("SELECT papel FROM lista_acceso WHERE lista_id = %s AND usuario_id = %s",
                    (inv["lista_id"], usuario_id))
        if cur.fetchone():
            return {"lista_id": str(inv["lista_id"]), "nombre": inv["nombre"],
                    "papel": inv["papel"], "ya_estabas": True}
        # Con quince personas, quien invito a quien importa: para saber a
        # quien echar si alguien se pasa, y para entender como crecio la cosa.
        cur.execute("""
            INSERT INTO lista_acceso
                (lista_id, usuario_id, papel, invitado_por, aceptado_en)
            VALUES (%s, %s, %s, %s, now())
        """, (inv["lista_id"], usuario_id, inv["papel"], inv["creada_por"]))
        cur.execute("UPDATE invitacion SET usos = usos + 1 WHERE codigo = %s", (codigo,))
    return {"lista_id": str(inv["lista_id"]), "nombre": inv["nombre"],
            "papel": inv["papel"], "ya_estabas": False}


def revoca_invitaciones(lista_id: str) -> int:
    with cursor() as cur:
        cur.execute("""UPDATE invitacion SET revocada_en = now()
                        WHERE lista_id = %s AND revocada_en IS NULL""", (lista_id,))
        return cur.rowcount


def quienes_en(lista_id: str) -> list[dict]:
    with cursor() as cur:
        cur.execute("""
            SELECT u.usuario, u.nombre, a.papel, a.aceptado_en
              FROM lista_acceso a JOIN usuario u ON u.id = a.usuario_id
             WHERE a.lista_id = %s ORDER BY a.papel = 'dueno' DESC, u.nombre
        """, (lista_id,))
        return cur.fetchall()


# --------------------------------------------------------------- novedades ---

def novedades(lista_id: str, usuario_id: str) -> list[dict]:
    """Lo que ha tocado la otra persona desde que tu miraste.

    Sin esto, una lista compartida es un sitio donde las cosas aparecen y
    desaparecen solas, y eso desconcierta mas de lo que ayuda.
    """
    with cursor() as cur:
        cur.execute("""
            SELECT li.nombre_visto, li.en_carrito, li.anadido_en, li.tachado_en,
                   qa.nombre AS anadido_por, qt.nombre AS tachado_por
              FROM lista_linea li
              JOIN usuario qa ON qa.id = li.anadido_por
              LEFT JOIN usuario qt ON qt.id = li.tachado_por
             WHERE li.lista_id = %(l)s AND li.borrado_en IS NULL
               AND li.tocado_en > COALESCE(
                   (SELECT vista_en FROM visita WHERE lista_id = %(l)s AND usuario_id = %(u)s),
                   now() - interval '7 days')
               AND (li.anadido_por <> %(u)s OR li.tachado_por <> %(u)s)
             ORDER BY li.tocado_en DESC LIMIT 12
        """, {"l": lista_id, "u": usuario_id})
        return cur.fetchall()


def marca_visita(lista_id: str, usuario_id: str) -> None:
    with cursor() as cur:
        cur.execute("""
            INSERT INTO visita (lista_id, usuario_id) VALUES (%s, %s)
            ON CONFLICT (lista_id, usuario_id) DO UPDATE SET vista_en = now()
        """, (lista_id, usuario_id))


def borra_usuario(usuario_id: str) -> dict:
    """Se lleva las listas propias, los favoritos y las sesiones.

    Lo que NO se lleva son las lineas que esa persona anadio a listas de otros:
    borrarlas vaciaria la lista de la compra de alguien que no ha pedido nada.
    Se quedan sin autor, que es lo honesto.
    """
    with cursor() as cur:
        cur.execute("SELECT * FROM borrar_usuario(%s)", (usuario_id,))
        fila = cur.fetchone()
    return {"listas_borradas": fila["listas_borradas"],
            "lineas_conservadas": fila["lineas_conservadas"]} if fila else {}
