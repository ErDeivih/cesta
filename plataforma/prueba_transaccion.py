"""La transaccion del cierre: o se guarda la compra entera, o no pasa nada.

**Por que existe.** `cierra_compra` promete, en su docstring: *"se hace en una transaccion
(`cursor()`): o se archivan las lineas y se guarda la compra, o no pasa nada"*. **Esa promesa no
estaba probada**: `test_aislamiento.py` mira `commit()`, `test_publicacion.py` prueba el rollback de
la publicacion, y **nadie habia forzado nunca un fallo a mitad del cierre de una compra**. La
atomicidad estaba escrita en un `with` y sin demostrar.

**Como.** En un PostgreSQL desechable, y con la siembra del propio ensayo:

  1. arranca el contenedor del **5434** (andamiaje de `prueba_copia`, reutilizado);
  2. corre `prueba_e2e`, que deja usuario, listas y compras de verdad -- **no se registra a nadie ni
     se adivina ningun esquema ni ninguna firma**;
  3. se re-invoca a si mismo con `--dentro` y la variable de entorno puesta, porque `almacen` lee
     `CESTA_POSTGRES` al importarse;
  4. dentro: coge una lista y un usuario del ensayo, mete **dos lineas en el carro**, parchea
     `almacen.cursor` para que falle en la enesima escritura, y llama al cierre;
  5. y comprueba **las tres cosas**: no hay `compra`, las lineas siguen `en_carrito`, y ninguna
     tiene `borrado_en`. O sea: **como si no se hubiera pulsado el boton.**

**Lo que NO hace**: no toca la base de casa. El contenedor es de este guion y se retira al final.
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from plataforma.prueba_copia import (  # noqa: E402
    ENSAYO,
    PUERTO_ENSAYO,
    arranca,
    consulta,
    corre,
    revisa,
    texto,
)

ANCHO = "127.0.0.1:5434"
CADENA = "postgresql://cesta:prueba@127.0.0.1:5434/cesta"


def dentro() -> int:
    """El trabajo real: se ejecuta con `CESTA_POSTGRES` ya apuntando al contenedor."""
    from plataforma.api import almacen

    # **El almacen tiene ciclo de vida**: sin esto, la primera escritura levanta
    # `RuntimeError: el almacen no esta arrancado`. Lo le? en `main.py` (su `ciclo`), y no lo tuve
    # en cuenta al escribir el guion. Medido el 13 de octubre de 2026.
    almacen.arranca()
    fallos = 0
    # **Los nombres, medidos y no supuestos**: la tabla de usuarios es `usuario` -- no `persona` -- y
    # el esquema lo crea la aplicacion al arrancar, por eso el ensayo tiene que haber corrido antes.
    # Y se comprueba la FORMA: `consulta` concatena stdout y stderr, asi que un error de SQL llega aqui
    # como si fuera un valor. Medido el 13 de octubre de 2026.
    import re

    usuario = consulta(ENSAYO, "SELECT id FROM usuario LIMIT 1")
    lista = consulta(ENSAYO, "SELECT id FROM lista LIMIT 1")
    forma = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    for nombre, valor in (("usuario", usuario), ("lista", lista)):
        if not forma.match(valor or ""):
            print(f"   FALLO: {nombre} no es un uuid; la base contesto: {valor[:120]!r}")
            return 1
    print(f"   usuario {usuario[:8]}... lista {lista[:8]}...")

    # **Dos lineas al carro, por las funciones que usa la app.** Sin SQL a mano.
    puestas = []
    for nombre in ("Prueba transaccion A", "Prueba transaccion B"):
        linea = almacen.anade_linea(lista, usuario, str(uuid.uuid4()), nombre,
                                    grupo_id=None, producto_id=f"dia:{abs(hash(nombre)) % 9999}",
                                    cantidad=1)
        almacen.cambia_linea(lista, linea["id"], usuario, en_carrito=True)
        puestas.append(linea["id"])
    # **Contado por identificador, no por lista**: el ensayo deja sus propias lineas, y contarlas
    # mezcladas fue un error de la ronda anterior.
    ids = ",".join(f"'{i}'" for i in puestas)
    compras_antes = consulta(ENSAYO, f"SELECT count(*) FROM compra WHERE lista_id = '{lista}'")
    en_carro = consulta(ENSAYO, f"SELECT count(*) FROM lista_linea WHERE id IN ({ids}) "
                                "AND en_carrito AND borrado_en IS NULL")
    print(f"   mis lineas, en el carro antes de cerrar: {en_carro}")

    # **El fallo, en la enesima escritura.** El proxy no depende del cuerpo de `cierra_compra`.
    real = almacen.cursor
    llamadas = {"n": 0}

    class CursorQueFalla:
        """Envuelve **el generador**, que es quien hace commit o rollback.

        La version anterior envolvia el *cursor* que devolvia `__enter__`, y llamaba a su `__exit__`:
        pero `cursor()` es un `@contextmanager`, asi que **quien cierra la transaccion es el
        generador**, no el cursor. Por eso el `__exit__` de la transaccion no corria nunca y el error
        que salia era `the cursor is closed`. Medido el 13 de octubre de 2026.
        """

        def __init__(self, gen, falla_en):
            self._gen, self._falla_en, self._cur, self._dentro = gen, falla_en, None, False

        def __enter__(self):
            self._cur = self._gen.__enter__()
            self._dentro = True
            llamadas["n"] = 0
            return self

        def __exit__(self, *a):
            self._dentro = False
            # **Al generador**, no al cursor: aqui es donde se decide commit o rollback.
            return self._gen.__exit__(*a)

        def execute(self, *a, **k):
            if self._dentro:
                llamadas["n"] += 1
                if llamadas["n"] == self._falla_en:
                    raise RuntimeError("fallo forzado a mitad del cierre")
            return self._cur.execute(*a, **k)

        def __getattr__(self, nombre):
            return getattr(self._cur, nombre)

    almacen.cursor = lambda: CursorQueFalla(real(), 4)
    try:
        almacen.cierra_compra(lista, usuario, precios={p: {"cadena": "dia", "precio_cent": 100}
                                                       for p in puestas})
        print("   FALLO: el cierre no fallo; el escenario no prueba nada")
        fallos += 1
    except Exception as exc:  # noqa: BLE001
        print(f"   el cierre fallo como debia: {type(exc).__name__}: {exc}")
    finally:
        almacen.cursor = real

    print()
    # **El delta, no el total.** `lista` es la primera de la tabla, y el ensayo ya cerro compras de la
    # suya: contar el total mezclaria las dos. Lo que importa es cuantas aparecen POR ESTE cierre.
    compras_despues = consulta(ENSAYO, f"SELECT count(*) FROM compra WHERE lista_id = '{lista}'")
    delta = int(compras_despues) - int(compras_antes)
    revisa("compras nuevas de este cierre", delta, 0)
    siguen = consulta(ENSAYO, f"SELECT count(*) FROM lista_linea WHERE id IN ({ids}) "
                              "AND en_carrito AND borrado_en IS NULL")
    revisa("mis lineas que siguen en el carro", siguen, en_carro)
    borradas = consulta(ENSAYO, f"SELECT count(*) FROM lista_linea WHERE id IN ({ids}) "
                                "AND borrado_en IS NOT NULL")
    revisa("mis lineas archivadas", borradas, "0")
    almacen.para()
    return fallos


def main() -> int:
    if "--dentro" in sys.argv:
        return dentro()

    print("== la transaccion del cierre: o entera, o nada")
    print("\n-- 1. el PostgreSQL desechable, en el 5434")
    if not arranca(ENSAYO, PUERTO_ENSAYO):
        print("   no se pudo arrancar el contenedor: se para")
        return 1
    print("   contenedor listo")

    print("\n-- 2. el ensayo, que deja datos de verdad")
    e = corre(["uv", "run", "python", "-m", "plataforma.prueba_e2e"], cwd=str(RAIZ))
    if e.returncode != 0:
        print("   FALLO: el ensayo no pasa; sin datos buenos no se prueba el cierre")
        print(texto(e)[-600:])
        corre(["docker", "rm", "-f", ENSAYO], timeout=120)
        return 1
    print("   el ensayo pasa y deja sus datos")

    print("\n-- 3. el fallo a mitad del cierre")
    entorno = dict(os.environ, CESTA_POSTGRES=CADENA, PYTHONPATH=str(RAIZ))
    r = subprocess.run([sys.executable, "-m", "plataforma.prueba_transaccion", "--dentro"],
                       capture_output=True, cwd=RAIZ, env=entorno, timeout=900)
    print(texto(r).strip())

    print("\n-- 4. recoger")
    corre(["docker", "rm", "-f", ENSAYO], timeout=120)
    print("   contenedor retirado")

    # **El veredicto lee los fallos, no los supone.** La version anterior daba `TODO BIEN` con dos
    # fallos en pantalla: miraba solo el codigo de salida. Un falso verde en una prueba es peor que no
    # tenerla. Medido el 13 de octubre de 2026.
    salida = texto(r)
    hay_fallo = "FALLO" in salida or r.returncode != 0
    print("\n== " + ("HAY FALLOS" if hay_fallo else "TODO BIEN"))
    return 1 if hay_fallo else 0


if __name__ == "__main__":
    raise SystemExit(main())
