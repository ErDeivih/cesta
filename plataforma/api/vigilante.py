"""El vigilante: mira las alertas **sin que nadie abra la pantalla**.

Esto existe por una frase del encargo de Claude, y es un fallo entero en una linea:
*"`alertas.evalua()` solo corre cuando alguien abre `GET /api/alertas`, o sea que la
alerta salta si entras a mirar."* Un aviso que solo salta cuando vas a verlo no es un
aviso: es una pantalla. La funcion que tienen todos los de la competencia es que **te
busque a ti**, y para eso la condicion hay que comprobarla cuando cambian los datos, no
cuando alguien tiene tiempo.

Que hace, y que NO hace
-----------------------
Cada pasada (`una_pasada`):

  1. lee de PostgreSQL las alertas **pendientes de saltar**: las que nadie ha visto
     (`vista_en IS NULL`) y que no han saltado todavia (`salto_en IS NULL`)
  2. las mira contra gold (`alertas.evalua`, que es el modulo que sabe de precios)
  3. apunta la hora en las que saltan (`salto_en`)

**No toca `vista_en`**, y esa es la diferencia que hace que esto sirva: `vista_en` es
"esta persona lo ha visto". Apuntarlo aqui seria decir que alguien ha visto un aviso que
no ha visto, y la pantalla lo daria por contado. `salto_en` es lo contrario: cuando la
condicion se cumplio de verdad, la mire quien la mire.

Y una alerta **salta una vez**: el `UPDATE` lleva `AND salto_en IS NULL`, asi que dos
pasadas seguidas no cuentan lo mismo dos veces. Un aviso que se repite todos los dias
deja de leerse, que es la leccion de `CIFRAS.md`.

Cuando corre
------------
Cuando **cambia gold**. El vigilante mira la fecha de escritura de
`data/gold/grupos.parquet` (lo mismo que usa `catalogo` para saber si tiene que rehacer
su copia) y solo hace una pasada si es distinta de la ultima que vio, mas una al
arrancar. Es la regla honesta: los precios cambian una vez al dia, y comprobar cien
veces lo mismo no adelanta nada.

Un fallo **no puede tumbar la API**: la pasada va envuelta, se cuenta y se sigue. Si
PostgreSQL o gold no estan, se reintenta en la vuelta siguiente.
"""
from __future__ import annotations

import threading
import time

from . import alertas, almacen, catalogo

# Cada cuanto se mira si gold ha cambiado. Los precios se escriben una vez al dia, asi
# que esto es de sobra; lo que no puede pasar es que la alerta espere a que alguien
# entre a mirar.
INTERVALO = 900

_parar: threading.Event | None = None
_hilo: threading.Thread | None = None


def una_pasada() -> dict:
    """Mira las alertas pendientes y apunta las que saltan. Sin tocar `vista_en`."""
    pendientes = almacen.alertas_por_saltar()
    if not pendientes:
        return {"miradas": 0, "saltan": 0, "apuntadas": 0}
    saltan = alertas.evalua(pendientes)
    apuntadas = 0
    for s in saltan:
        # La frase se guarda con el aviso: se mide contra el gold de hoy, y manana gold
        # es otro. Sin guardarla, lo que alguien vio ayer diria hoy otra cosa.
        # `marca_alerta_saltada` devuelve False si otra pasada se adelanto: el UPDATE
        # lleva `AND salto_en IS NULL`, y asi lo que se cuenta es lo que se apunto.
        if almacen.marca_alerta_saltada(s["alerta_id"], s["por_que"]):
            apuntadas += 1
    return {"miradas": len(pendientes), "saltan": len(saltan), "apuntadas": apuntadas}


def _sello() -> float:
    """Cuando se escribio gold por ultima vez. Es la senal de "hay datos nuevos"."""
    return catalogo.sello_de_gold()


def en_marcha(parar: threading.Event, intervalo: float = INTERVALO, *,
              pasada=una_pasada, sello=_sello) -> None:
    """El bucle. Se puede llamar a mano en una prueba, con su propia pasada."""
    ultimo = None
    primera = True
    while not parar.is_set():
        ahora = sello()
        if primera or ahora != ultimo:
            primera = False
            ultimo = ahora
            try:
                r = pasada()
            except Exception as exc:  # noqa: BLE001
                # Un fallo aqui no puede tumbar la API ni parar el vigilante: si la
                # base de datos o gold no estan, se reintenta en la vuelta siguiente.
                print(f"  vigilante: fallo la pasada ({type(exc).__name__}: {exc})",
                      flush=True)
            else:
                if r.get("apuntadas"):
                    print(f"  vigilante: {r['apuntadas']} alerta(s) saltaron "
                          f"de {r['miradas']} miradas", flush=True)
        parar.wait(intervalo)


def arranca(intervalo: float = INTERVALO) -> None:
    """Enciende el vigilante. Idempotente: llamarlo dos veces no pone dos hilos."""
    global _parar, _hilo
    if _hilo is not None and _hilo.is_alive():
        return
    _parar = threading.Event()
    _hilo = threading.Thread(target=en_marcha, args=(_parar, intervalo),
                             name="vigilante", daemon=True)
    _hilo.start()


def para() -> None:
    """Lo apaga. La API lo llama al cerrarse."""
    global _parar, _hilo
    if _parar is not None:
        _parar.set()
    if _hilo is not None:
        _hilo.join(timeout=5)
    _parar = None
    _hilo = None


def espera(segundos: float) -> None:
    """Deja que el vigilante haga su primera pasada. Para las pruebas."""
    time.sleep(segundos)
