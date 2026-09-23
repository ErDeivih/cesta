"""Verificacion de punta a punta de la API, contra un PostgreSQL **de verdad**.

Por que existe
--------------
Las pruebas de `tests/` sustituyen PostgreSQL a proposito -- una prueba que dependa de la
base del dia mide el calendario, no el codigo --, y eso deja un hueco: **el SQL y las
migraciones no los ejecuta nadie** hasta que arranca el contenedor. El 23 de septiembre de
2026 ese hueco dejo pasar un fallo: `/api/bajadas?solo_mios=true` **sin sesion** contestaba
`"solo_mios": true` aunque no hubiera filtrado nada (los grupos que llegaban al SQL si se
comprobaban en las pruebas; el campo de la respuesta, no). La pantalla habria ensenado
sesenta bajadas del catalogo entero bajo el titulo "Lo tuyo que ha bajado".

Esto lo ejecuta todo de verdad: las seis migraciones de `plataforma/sql`, las consultas
nuevas y el flujo entero, contra una base **desechable** y con el gold de verdad.

Como se corre
-------------
    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    uv run python -m plataforma.prueba_e2e
    docker rm -f cesta-prueba-db

**No toca la base de produccion**: el contenedor de Cesta no publica su 5432 (ver
`plataforma/docker-compose.yml`), asi que no hay forma de alcanzarla por descuido. El 5434
es de esta prueba y esta escrito aqui a proposito, con nombre y puerto, para que nadie lo
confunda con el de casa.

Que comprueba
-------------
    las migraciones          se aplican una a una sobre una base vacia
    /api/listas/{id}         el pasillo en cada linea, con el orden del recorrido
    /api/habituales          la cuadricula, con `origen` en cada tarjeta y rellenando
    /api/alertas             la alerta con la tarjeta del grupo (nombre, precio)
    el vigilante             una pasada de verdad: mira, salta y apunta `salto_en`
    /api/buscar?q=lece…      la correccion de faltas
    /api/bajadas?solo_mios   el filtro "lo mio", y que el campo diga la verdad
"""
from __future__ import annotations

import os
import sys
import uuid

PUERTO = 5434
CLAVE = "prueba"
# Se pone **antes** de importar la plataforma: `Ajustes.del_entorno()` se lee al importar.
os.environ.setdefault(
    "CESTA_POSTGRES", f"postgresql://cesta:{CLAVE}@127.0.0.1:{PUERTO}/cesta")


def main() -> int:
    from fastapi.testclient import TestClient

    from plataforma.api import almacen, catalogo, main, vigilante

    print("== arrancando el almacen (aplica plataforma/sql/*.sql)")
    almacen.arranca()
    print("   migraciones aplicadas")

    # Una persona limpia en cada pasada: la base es de prueba y se puede vaciar.
    with almacen.cursor() as cur:
        cur.execute("DELETE FROM usuario")

    filas = catalogo.conexion().execute("""
        SELECT grupo_id, min(nombre), count(DISTINCT fuente) AS cadenas
          FROM buscable
         WHERE grupo_id IS NOT NULL AND precio_unidad_cent > 0
         GROUP BY grupo_id HAVING count(DISTINCT fuente) >= 3
         ORDER BY cadenas DESC LIMIT 3""").fetchall()
    print(f"   grupos de verdad: {[(g, n[:30]) for g, n, _c in filas]}")

    yo = almacen.crea_usuario("prueba", "Prueba", "clave-de-prueba")
    lista = almacen.crea_lista(yo["id"], "Casa", True)
    for grupo_id, nombre, _c in filas:
        # El id lo trae el movil y es un uuid (`idDeLinea` en el front).
        almacen.anade_linea(str(lista["id"]), yo["id"], str(uuid.uuid4()), nombre,
                            grupo_id=grupo_id)
    almacen.crea_alerta(yo["id"], int(filas[0][0]), "minimo_90d")

    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    # `/api/bajadas` pide la sesion **opcional**: se sustituye tambien para poder
    # comprobar las dos ramas -- con sesion filtra, sin sesion tiene que decirlo.
    main.app.dependency_overrides[main.usuario_opcional] = lambda: yo
    cliente = TestClient(main.app)
    fallos = 0

    def pide(ruta, **params):
        nonlocal fallos
        r = cliente.get(ruta, params=params)
        print(f"\n== GET {ruta}  ->  {r.status_code}")
        if r.status_code != 200:
            fallos += 1
            print(f"   {r.text[:200]}")
            return {}
        return r.json()

    cuerpo = pide(f"/api/listas/{lista['id']}")
    for linea in cuerpo.get("lineas", []):
        print(f"   {linea['nombre_visto'][:32]:34s} grupo {linea['grupo_id']:6d}  "
              f"pasillo={linea.get('pasillo')!r} orden={linea.get('pasillo_orden')}")
    if not any(x.get("pasillo") for x in cuerpo.get("lineas", [])):
        fallos += 1
        print("   FALLO: ninguna linea trae pasillo")

    cuerpo = pide("/api/habituales", limite=8)
    print(f"   origenes={cuerpo.get('origenes')}")
    for h in cuerpo.get("habituales", []):
        print(f"   {h['origen']:9s} {h['nombre'][:32]:34s} {h['precio_unidad_cent']:8.2f}"
              f" /{h['unidad']}")
    if not cuerpo.get("origenes"):
        fallos += 1
        print("   FALLO: la cuadricula no dice de donde sale nada")

    cuerpo = pide("/api/alertas")
    for a in cuerpo.get("alertas", []):
        print(f"   alerta {a['tipo']:11s} grupo {a['grupo_id']:6d} "
              f"nombre={a.get('nombre')!r} precio={a.get('precio_unidad_cent')}")
    if not any(a.get("nombre") for a in cuerpo.get("alertas", [])):
        fallos += 1
        print("   FALLO: la alerta no trae el nombre del producto")

    print("\n== el vigilante: una pasada de verdad")
    r = vigilante.una_pasada()
    print(f"   {r}")
    if r["apuntadas"] != 1:
        fallos += 1
        print("   FALLO: la alerta no se apunto")
    cuerpo = pide("/api/alertas")
    for a in cuerpo.get("alertas", []):
        print(f"   salto_en={a['salto_en']}  texto={a['salto_texto']!r}")
    if not any(a.get("salto_texto") for a in cuerpo.get("alertas", [])):
        fallos += 1
        print("   FALLO: la frase no se guardo")

    cuerpo = pide("/api/buscar", q="lece entera", limite=2)
    print(f"   corregido={cuerpo.get('corregido')!r}  "
          f"primero={cuerpo['resultados'][0]['nombre'] if cuerpo.get('resultados') else None!r}")
    if cuerpo.get("corregido") != "leche entera":
        fallos += 1
        print("   FALLO: no ha corregido la falta")

    cuerpo = pide("/api/bajadas", solo_mios="true", dias=90)
    print(f"   solo_mios={cuerpo.get('solo_mios')}  resultados={len(cuerpo.get('resultados', []))}")
    if cuerpo.get("solo_mios") is not True:
        fallos += 1
        print("   FALLO: con sesion no ha filtrado por 'lo mio'")

    # **La cola de lo que se hizo sin cobertura** (§3.5). El movil manda los cambios de
    # golpe con su hora, y el servidor los aplica: esto es lo que hace que tachar sin red
    # no sea un error.
    print("\n== la cola sin cobertura: /sincronizar")
    linea = almacen.lineas_de(str(lista["id"]))[0]
    momento = "2026-09-23T18:04:00+00:00"
    r = cliente.post(f"/api/listas/{lista['id']}/sincronizar",
                     json=[{"id": linea["id"], "momento": momento, "tachado": True}])
    print(f"   POST /sincronizar -> {r.status_code}  {r.json() if r.status_code == 200 else r.text[:150]}")
    if r.status_code != 200 or r.json().get("aplicados") != 1:
        fallos += 1
        print("   FALLO: la cola no se ha aplicado")
    despues = next(x for x in almacen.lineas_de(str(lista["id"]))
                   if x["id"] == linea["id"])
    print(f"   tachado_en={despues['tachado_en']}  (la hora que mando el movil: {momento})")
    if not despues["tachado_en"]:
        fallos += 1
        print("   FALLO: el cambio de la cola no se aplico")
    if str(despues["tachado_en"]).replace("T", " ")[:16] != momento.replace("T", " ")[:16]:
        fallos += 1
        print("   FALLO: se ha guardado la hora de llegada en vez de la del movil")

    # **Sin sesion**: el filtro no puede saber que es "lo mio", y el campo tiene que
    # decir la verdad. Este es el fallo que encontro esta prueba.
    print("\n== y sin sesion, que el campo no mienta")
    del main.app.dependency_overrides[main.usuario_opcional]
    r = cliente.get("/api/bajadas", params={"solo_mios": "true", "dias": 90})
    cuerpo = r.json() if r.status_code == 200 else {}
    print(f"   solo_mios={cuerpo.get('solo_mios')}  resultados={len(cuerpo.get('resultados', []))}")
    if cuerpo.get("solo_mios") is not False:
        fallos += 1
        print("   FALLO: dice que ha filtrado por 'lo mio' y no ha filtrado")

    almacen.para()
    print(f"\n== {'TODO BIEN' if not fallos else f'{fallos} FALLO(S)'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
