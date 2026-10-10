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
    avisos.py (la cadena)    la misma pasada desde el paso de la cadena, y lo que
                             contaria el resumen (`3 saltaron hoy`)
    /api/buscar?q=lece…      la correccion de faltas
    /api/bajadas?solo_mios   el filtro "lo mio", y que el campo diga la verdad
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import time
import uuid

PUERTO = 5434
CLAVE = "prueba"
# Se pone **antes** de importar la plataforma: `Ajustes.del_entorno()` se lee al importar.
os.environ.setdefault(
    "CESTA_POSTGRES", f"postgresql://cesta:{CLAVE}@127.0.0.1:{PUERTO}/cesta")


def main() -> int:
    from fastapi.testclient import TestClient

    from plataforma.api import alertas, almacen, catalogo, main, vigilante
    from plataforma.api.ajustes import AJUSTES
    # El gold de verdad, por donde lo busca todo el mundo (`CESTA_GOLD`, que en el contenedor es
    # `/datos/gold`): aqui no se escribe nada, solo se leen los grupos de hoy y la tabla de ayer.
    gold = AJUSTES.gold

    print("== arrancando el almacen (aplica plataforma/sql/*.sql)")
    almacen.arranca()
    print("   migraciones aplicadas")
    fallos = 0

    # Una persona limpia en cada pasada: la base es de prueba y se puede vaciar.
    with almacen.cursor() as cur:
        cur.execute("DELETE FROM usuario")

    # **Dos personas, cada una con su lista de casa, y borrarlas.** No es un adorno: el
    # 23 de septiembre de 2026 esto fallaba por dos motivos distintos, y los dos solo se
    # ven con dos listas de casa de verdad --
    #
    #   - `001_esquema.sql` creaba un indice unico sobre `es_de_casa` a secas (una sola
    #     lista de casa en TODO el sistema), `003` lo borraba, y como `migra()` aplica
    #     todos los ficheros en cada arranque, el segundo arranque lo resucitaba: la API
    #     no arrancaba con dos listas de casa.
    #   - `lista_linea.tachado_coherente` pedia "quien" si y solo si "cuando", asi que
    #     borrar a alguien que habia tachado algo fallaba (`007`).
    print("\n== dos personas con su lista de casa, y borrarlas")
    for nombre in ("dos-a", "dos-b"):
        otra = almacen.crea_usuario(nombre, nombre.title(), "clave-de-prueba-123")
        almacen.crea_lista(otra["id"], "Casa", True)
    with almacen.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM lista WHERE es_de_casa")
        listas_de_casa = cur.fetchone()["n"]
    print(f"   listas de casa: {listas_de_casa}")
    if listas_de_casa < 2:
        fallos += 1
        print("   FALLO: no se han podido crear dos listas de casa")
    for nombre in ("dos-a", "dos-b"):
        with almacen.cursor() as cur:
            cur.execute("DELETE FROM usuario WHERE usuario = %s", (nombre,))
    print("   las dos se borran sin error")

    # Los grupos de prueba: con tres cadenas o mas, y **ordenados por lo cerca que estan de su
    # minimo de 90 dias**, que es lo que hace que la alerta `minimo_90d` salte.
    #
    # Elegirlos solo por numero de cadenas parecia inofensivo y no lo era: el 24 de septiembre
    # de 2026 esta prueba se puso roja de pronto -- «la alerta no se apunto» -- y el fallo no
    # era de la aplicacion: `ORDER BY cadenas DESC` **sin desempate** deja que DuckDB devuelva
    # cualquiera de los grupos empatados a cadenas, y habia caido en uno cuyo precio no estaba
    # en su minimo. `grupo_id` cierra el orden, y el minimo de 90 dias se lee como lo lee la
    # aplicacion (`arg_max(min_90d_cent, fecha)`, la ultima fecha de cada producto).
    filas = catalogo.conexion().execute("""
        WITH der AS (
            SELECT fuente, id_fuente, arg_max(min_90d_cent, fecha) AS minimo
              FROM derivado GROUP BY fuente, id_fuente),
        candidatos AS (
            SELECT b.grupo_id, min(b.precio_unidad_cent) AS precio,
                   count(DISTINCT b.fuente) AS cadenas,
                   min(der.minimo) AS minimo
              FROM buscable b
              JOIN der ON der.fuente = b.fuente AND der.id_fuente = b.id_fuente
             WHERE b.grupo_id IS NOT NULL AND b.precio_unidad_cent > 0
               -- **Las mismas condiciones que exige la alerta**, y no es un adorno: el 26
               -- de septiembre de 2026 esta prueba se puso roja con «la alerta no se apunto»
               -- y el fallo no era de la aplicacion. Sin este filtro, el grupo mas cercano a
               -- su minimo de 90 dias resulto ser uno medido en unidades (`ud`, compresas),
               -- y `alertas._mejor_de_cada_grupo` descarta esos grupos a proposito
               -- (`comparacion_fiable`: dos precios por unidad de un grupo medido en
               -- unidades no se comparan entre cadenas). El vigilante hacia lo correcto:
               -- callarse. Es el mismo tipo de fallo que el desempate del 24 de septiembre,
               -- un banco de pruebas que no cumple las condiciones que la aplicacion pide.
               AND coalesce(b.comparacion_fiable, false)
             GROUP BY b.grupo_id HAVING count(DISTINCT b.fuente) >= 3)
        SELECT c.grupo_id,
               (SELECT min(nombre) FROM buscable WHERE grupo_id = c.grupo_id) AS nombre,
               c.cadenas
          FROM candidatos c
         WHERE c.minimo IS NOT NULL
         ORDER BY (c.precio - c.minimo) ASC, c.grupo_id
         LIMIT 3""").fetchall()
    print(f"   grupos de verdad: {[(g, n[:30]) for g, n, _c in filas]}")

    yo = almacen.crea_usuario("prueba", "Prueba", "clave-de-prueba")
    lista = almacen.crea_lista(yo["id"], "Casa", True)
    for grupo_id, nombre, _c in filas:
        # El id lo trae el movil y es un uuid (`idDeLinea` en el front).
        almacen.anade_linea(str(lista["id"]), yo["id"], str(uuid.uuid4()), nombre,
                            grupo_id=grupo_id)
    # **Y una linea a la que le han renumerado el grupo.** El emparejador numera los grupos en el
    # orden en que aparecen los productos, asi que el grupo de esta linea es hoy otro producto: la
    # linea se queda diciendo un nombre que no es el suyo. Medido el 28 de septiembre de 2026:
    # **43 de 54 lineas** de la lista de la cuenta de pruebas estaban asi, y la estimacion decia
    # 298,71 EUR cuando lo que se podia contar eran 10,56 -- el resto era el precio de un
    # pintalabios puesto en lineas de leche. Aqui se siembra el caso a mano para que se pueda
    # medir sin depender de que pase.
    movida_id = str(uuid.uuid4())
    almacen.anade_linea(str(lista["id"]), yo["id"], movida_id,
                        "PINTALABIOS DE PRUEBA QUE NO ES DE ESTE GRUPO", grupo_id=int(filas[0][0]))
    almacen.crea_alerta(yo["id"], int(filas[0][0]), "minimo_90d")

    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    # `/api/bajadas` pide la sesion **opcional**: se sustituye tambien para poder
    # comprobar las dos ramas -- con sesion filtra, sin sesion tiene que decirlo.
    main.app.dependency_overrides[main.usuario_opcional] = lambda: yo
    cliente = TestClient(main.app)

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
    # La linea sembrada tiene que venir marcada y **sin pasillo**: el pasillo tambien es del
    # grupo, y el suyo seria el de otro producto.
    sembrada = next((x for x in cuerpo.get("lineas", []) if str(x["id"]) == movida_id), None)
    print(f"   la linea movida: marcada={sembrada and sembrada.get('producto_movido')} "
          f"pasillo={sembrada and sembrada.get('pasillo')!r}")
    if not sembrada or not sembrada.get("producto_movido"):
        fallos += 1
        print("   FALLO: la linea cuyo grupo es otro producto no viene marcada")
    elif sembrada.get("pasillo") is not None:
        fallos += 1
        print("   FALLO: la linea movida sigue trayendo el pasillo de otro producto")
    # Y no puede estar en el total: la estimacion la cuenta como «sin precio».
    sin_precio = cuerpo.get("estimacion", {}).get("sin_precio", 0)
    print(f"   sin precio: {sin_precio}")
    if sin_precio < 1:
        fallos += 1
        print("   FALLO: la linea movida esta entrando en la estimacion")
    # Ni en el reparto: se estaria decidiendo la tienda de un producto por el precio de otro.
    reparto = pide(f"/api/listas/{lista['id']}/reparto")
    dentro = [x for grupo in reparto.get("sublistas", []) for x in grupo.get("lineas", [])]
    dentro += reparto.get("sin_asignar", [])
    if any(str(x.get("linea_id")) == movida_id for x in dentro):
        fallos += 1
        print("   FALLO: la linea movida aparece en el reparto")
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

    # **Y el paso de la cadena diaria** (§6): la misma pasada, pero pedida desde donde
    # la pide `run.py` a las 06:00, y contada como la cuenta el resumen. Lo que se
    # comprueba aqui no es el SQL -- eso ya esta arriba --, sino que el numero que
    # llega al resumen es el de verdad: cuando la base SI se alcanza.
    print("\n== el paso de la cadena: projects/cesta/avisos.py")
    from projects.cesta import avisos
    with tempfile.TemporaryDirectory() as sitio:
        de_verdad, avisos.FICHERO = avisos.FICHERO, pathlib.Path(sitio) / "avisos.json"
        try:
            nota = avisos.una_pasada()
        finally:
            avisos.FICHERO = de_verdad
        print(f"   {nota}")
        print(f"   resumen: {avisos.frase(nota)}")
        if "error" in nota:
            fallos += 1
            print(f"   FALLO: el paso no ha podido mirar con la base delante: {nota}")
        if nota.get("saltaron_hoy", 0) < 1:
            fallos += 1
            print("   FALLO: la alerta salto y el resumen diria que no ha saltado nada")
        if nota.get("por_mirar", 1) != 0:
            fallos += 1
            print(f"   FALLO: la cola del vigilante no se ha vaciado: {nota.get('por_mirar')}")
        if "saltaron hoy" not in avisos.frase(nota):
            fallos += 1
            print("   FALLO: la linea del resumen no cuenta lo que ha visto el paso")
        if not almacen.arrancado():
            fallos += 1
            print("   FALLO: el paso le ha cerrado el almacen a quien ya lo tenia abierto")

    # §6: *"dejar el resultado guardado, para que abrir la aplicacion sea instantaneo"*.
    # Eso es una afirmacion sobre el tiempo, asi que se mide -- y **midiendolo se
    # descubrio que el instrumento mentia**, que es la segunda vez en este proyecto:
    #
    #   - por `TestClient` (httpx en el mismo proceso), `GET /api/salud`, que no hace
    #     nada, tarda **409 ms**. Los 469 ms que se midieron primero eran el andamio de
    #     la prueba, no la aplicacion. Con ese numero se habria "arreglado" algo que no
    #     estaba roto, y el arreglo habria sido creerse un dato falso.
    #   - La aplicacion se mide **llamando a la ruta**, que es lo que de verdad cuesta.
    #     Y se mide el andamio tambien, para que quede dicho y nadie lo confunda otra
    #     vez. Es la misma leccion que la trampa del contraste: la medida tiene que
    #     demostrar que mira.
    print("\n== abrir los avisos, cronometrado")
    t0 = time.monotonic()
    for _ in range(5):
        cliente.get("/api/salud")
    andamio = (time.monotonic() - t0) / 5 * 1000
    print(f"   el andamio de la prueba (GET /api/salud por TestClient): {andamio:.0f} ms")
    print("   ^ eso NO es la aplicacion: es httpx en el mismo proceso.")

    alertas.olvida()          # en frio: lo primero que pasa despues de cambiar gold
    t0 = time.monotonic()
    cuerpo = main.ver_alertas(usuario=yo)
    frio = (time.monotonic() - t0) * 1000
    if not cuerpo.get("alertas"):
        fallos += 1
        print("   FALLO: la ruta de los avisos no devuelve las alertas de la persona")
    momentos = []
    for _ in range(5):
        t0 = time.monotonic()
        main.ver_alertas(usuario=yo)
        momentos.append((time.monotonic() - t0) * 1000)
    media = sum(momentos) / len(momentos)
    print(f"   la aplicacion, en frio (gold recien cambiado, nadie ha preguntado): "
          f"{frio:.0f} ms")
    print(f"   la aplicacion, en caliente: {media:.0f} ms de media "
          f"({min(momentos):.0f}-{max(momentos):.0f} ms de 5, en este PC)")
    print("   (el frio lo paga el vigilante a las 06:00 en este mismo proceso, y su "
          "respuesta es la que encuentra quien abre la pantalla)")
    if media > 150:
        fallos += 1
        print("   FALLO: abrir los avisos tarda mas que un parpadeo: el resultado "
              "guardado no esta sirviendo de nada")

    # **Darse de baja** (`DELETE /api/yo`). La interfaz nueva gano el boton el 24 de
    # septiembre de 2026 (`Ajustes.tsx`), y aqui se comprueba lo que de verdad promete el
    # borrado, que es lo que no se ve en la pantalla: sus listas se van, **y la linea que
    # dejo en la lista de otra persona se queda**, sin autor. Eso es la migracion 005
    # (`anadido_por` con `SET NULL`): sin ella la baja respondia 500.
    # **Y el producto que salto, guardado con la frase.** El nombre del grupo se lee del gold de
    # hoy; la frase es del dia que salto. Sin guardar el nombre, la tarjeta enseña las dos epocas
    # juntas: medido el 28 de septiembre de 2026 en la pantalla de avisos, «TWIX Barritas de
    # chocolate ... esta al precio mas bajo de los ultimos 90 dias: 0.96 EUR/l en mercadona», que
    # es la frase de la leche entera (el grupo 10226 era la leche el dia que salto). Aqui se
    # siembra el caso a mano: se marca la alerta como saltada **con el nombre de otro producto** y
    # se comprueba que la API devuelve ese nombre y no el del grupo de hoy.
    print("\n== el producto que salto, guardado con la frase")
    mio = almacen.alertas_de(yo["id"])[0]
    # Se **vuelve a crear** la alerta: el `ON CONFLICT` la deja otra vez por saltar (y limpia
    # `salto_texto` y `salto_nombre`), que es justo lo que hace falta para poder sembrar el caso.
    # Sin eso, la pasada del vigilante de arriba ya la habia marcado y el `UPDATE` no la toca
    # (`AND salto_en IS NULL`), que es lo correcto.
    puesta = almacen.crea_alerta(yo["id"], int(mio["grupo_id"]), str(mio["tipo"]))
    nombre_de_entonces = "El producto que era ese dia"
    marcada = almacen.marca_alerta_saltada(str(puesta["id"]), "una frase de aquel dia",
                                           nombre_de_entonces)
    print(f"   la alerta se vuelve a marcar: {marcada}")
    if not marcada:
        fallos += 1
        print("   FALLO: no se ha podido marcar la alerta como saltada")
    cuerpo = pide("/api/alertas")
    guardadas = [a for a in cuerpo.get("alertas", []) if str(a["id"]) == str(puesta["id"])]
    apuntado = guardadas[0]["salto_nombre"] if guardadas else None
    de_hoy = guardadas[0].get("nombre") if guardadas else None
    print(f"   guardado: {apuntado!r}   el grupo hoy se llama: {de_hoy!r}")
    if apuntado != nombre_de_entonces:
        fallos += 1
        print("   FALLO: el nombre que salto no se ha guardado (la pantalla enseñaria el de hoy)")
    if apuntado and apuntado == de_hoy:
        fallos += 1
        print("   FALLO: el nombre guardado es el de hoy, no el del dia que salto")

    print("\n== la numeracion de los grupos, y la tabla que la hace estable")

    print("\n== la numeracion de los grupos, y la tabla que la hace estable")
    # **El fichero que hace que un grupo conserve su numero entre pasadas.** El emparejador numera
    # los grupos por el orden en que aparecen los productos, y ese numero lo guardan las listas,
    # los favoritos y los avisos: sin esta tabla, cada pasada deja esas referencias apuntando a
    # otro producto (medido el 28 de septiembre de 2026: 43 de 54 lineas de una lista). Aqui se
    # comprueba que esta y que **cuadra con los grupos de hoy**, que es lo que la hace util.
    tabla_ayer = gold / "grupos_anterior.parquet"
    if not tabla_ayer.exists():
        fallos += 1
        print(f"   FALLO: no esta {tabla_ayer.name}: la pasada de mañana renumeraria los grupos")
    else:
        import polars as pl
        ayer = pl.read_parquet(tabla_ayer)
        hoy = pl.read_parquet(gold / "grupos.parquet",
                              columns=["fuente", "id_fuente", "grupo_id"])
        print(f"   {tabla_ayer.name}: {ayer.height} productos, "
              f"{ayer['grupo_id'].n_unique()} grupos")
        claves = [f"{f}:{i}" for f, i in zip(hoy["fuente"].to_list(),
                                             [str(x) for x in hoy["id_fuente"].to_list()],
                                             strict=True)]
        esperado = dict(zip(claves, hoy["grupo_id"].to_list(), strict=True))
        apuntado = dict(zip(ayer["clave"].to_list(), ayer["grupo_id"].to_list(), strict=True))
        iguales = sum(1 for k, v in esperado.items() if apuntado.get(k) == v)
        print(f"   cuadra con los grupos de hoy en {iguales} de {len(esperado)} productos")
        if iguales != len(esperado):
            fallos += 1
            print("   FALLO: la tabla de ayer no cuadra con los grupos de hoy")

    print("\n== compartir contigo mismo no te quita la lista")    # **El fallo que encontro la puerta de las funciones el 28 de septiembre de 2026.** Escribir
    # tu propio usuario en «Compartir con quien ya tiene cuenta» actualizaba tu fila de
    # `lista_acceso` a `escribe`: la lista dejaba de ser tuya sin decirlo (403 al invitar y al
    # borrarla, y la tarjeta de Compartir desaparecia de la pantalla, o sea sin forma de
    # volver). Se mira aqui porque esto **es lo unico que ejecuta el SQL de verdad**: las
    # pruebas de `tests/` sustituyen PostgreSQL a proposito.
    mio = almacen.crea_usuario("mismo-dueno", "Mismo Dueno", "clave-de-prueba-123")
    mi_lista = almacen.crea_lista(mio["id"], "La mia", True)
    main.app.dependency_overrides[main.usuario_actual] = lambda: mio
    r = cliente.post(f"/api/listas/{mi_lista['id']}/compartir",
                     json={"usuario": "mismo-dueno", "papel": "escribe"})
    print(f"   POST /compartir con mi propio usuario -> {r.status_code} {r.json()}")
    if r.status_code != 200 or r.json().get("papel") != "dueno":
        fallos += 1
        print("   FALLO: compartir con el dueno le cambia el papel")
    with almacen.cursor() as cur:
        cur.execute("SELECT papel FROM lista_acceso WHERE lista_id = %s AND usuario_id = %s",
                    (mi_lista["id"], mio["id"]))
        papel = cur.fetchone()["papel"]
    if papel != "dueno":
        fallos += 1
        print(f"   FALLO: en la base mi papel es {papel!r}, no «dueno»")
    r = cliente.post(f"/api/listas/{mi_lista['id']}/invitacion",
                     json={"papel": "escribe", "usos": 1, "dias": 7})
    print(f"   y sigo pudiendo invitar -> {r.status_code}")
    if r.status_code != 201:
        fallos += 1
        print("   FALLO: despues de compartir conmigo mismo ya no puedo invitar")
    r = cliente.delete(f"/api/listas/{mi_lista['id']}")
    print(f"   y sigo pudiendo borrarla -> {r.status_code}")
    if r.status_code != 200:
        fallos += 1
        print("   FALLO: despues de compartir conmigo mismo ya no puedo borrar mi lista")
    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    with almacen.cursor() as cur:
        cur.execute("DELETE FROM usuario WHERE usuario = 'mismo-dueno'")

    print("\n== darse de baja: DELETE /api/yo")
    quien_se_va = almacen.crea_usuario("se-va", "Se va", "clave-de-prueba-123")
    suya = almacen.crea_lista(quien_se_va["id"], "Su casa", True)
    almacen.anade_linea(str(suya["id"]), quien_se_va["id"], str(uuid.uuid4()),
                        "Leche entera", grupo_id=int(filas[0][0]))
    # Y una linea suya en la lista de la otra persona: esa es la que tiene que sobrevivir.
    almacen.anade_linea(str(lista["id"]), quien_se_va["id"], str(uuid.uuid4()),
                        "Pan de molde", grupo_id=int(filas[1][0]))
    antes_en_la_otra = len(almacen.lineas_de(str(lista["id"])))
    main.app.dependency_overrides[main.usuario_actual] = lambda: quien_se_va
    r = cliente.delete("/api/yo")
    print(f"   DELETE /api/yo -> {r.status_code}  "
          f"{r.json() if r.status_code == 200 else r.text[:150]}")
    if r.status_code != 200:
        fallos += 1
        print("   FALLO: no se ha podido dar de baja")
    else:
        print(f"   listas borradas: {r.json().get('listas_borradas')}  "
              f"lineas conservadas: {r.json().get('lineas_conservadas')}")
    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    if any(x["id"] == str(suya["id"]) for x in almacen.listas_de(quien_se_va["id"])):
        fallos += 1
        print("   FALLO: la lista propia sigue ahi despues de la baja")
    with almacen.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM usuario WHERE usuario = 'se-va'")
        if cur.fetchone()["n"]:
            fallos += 1
            print("   FALLO: la cuenta sigue existiendo")
    despues = almacen.lineas_de(str(lista["id"]))
    mia = next((x for x in despues if x["nombre_visto"] == "Pan de molde"), None)
    print(f"   en la lista de la otra persona: {antes_en_la_otra} -> {len(despues)} lineas, "
          f"la suya con autor={mia['anadido_por'] if mia else 'NO ESTA'}")
    if mia is None or mia["anadido_por"] is not None:
        fallos += 1
        print("   FALLO: la linea que dejo en la lista de otro no se ha conservado sin autor")

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

    # ------------------------------------ cerrar la compra (tarea 10) --------------------
    # **Lo que este boton no puede hacer mal es llevarse lo que no se cogio.** Se prueba con
    # dos lineas de verdad en PostgreSQL: una marcada (va al carro y sale de la lista) y otra
    # sin marcar (se queda). Y con una **sin precio**, que es el caso de una linea que apunta a
    # otro producto: se guarda en la compra con su precio en NULL y se cuenta aparte, porque
    # tirarla borraria de la compra algo que si se compro y contarla como cero mentiria en el
    # total.
    print("\n== cerrar la compra: lo del carro se guarda y sale, lo demas se queda")
    dentro = almacen.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()),
                                 "Leche entera", grupo_id=None, producto_id="dia:74397")
    fuera = almacen.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()),
                                "Pan que no me llevo", grupo_id=None, producto_id="dia:74397")
    almacen.cambia_linea(str(lista["id"]), dentro["id"], str(yo["id"]), en_carrito=True)
    # **Las lineas que de verdad iban marcadas, contadas antes de pulsar.** La compra tiene
    # que llevarse exactamente estas. Se cuentan aqui en vez de comparar con un numero escrito
    # a mano, que ata la prueba al estado en que estaba la lista el dia que se escribio.
    iban_en_el_carro = {str(x["id"]) for x in almacen.lineas_de(str(lista["id"]))
                      if x.get("en_carrito")}
    if str(dentro["id"]) not in iban_en_el_carro:
        fallos += 1
        print("   FALLO: la linea marcada no cuenta como que va en el carro")
    r = cliente.post(f"/api/listas/{lista['id']}/cerrar")
    hecho = r.json() if r.status_code == 200 else {}
    print(f"   POST /cerrar -> {r.status_code}  {hecho}")
    if r.status_code != 200:
        fallos += 1
        print("   FALLO: no se ha podido cerrar la compra")
    vivos = {str(x["id"]) for x in almacen.lineas_de(str(lista["id"]))}
    if str(dentro["id"]) in vivos:
        fallos += 1
        print("   FALLO: la linea que iba en el carro sigue en la lista")
    if str(fuera["id"]) not in vivos:
        fallos += 1
        print("   FALLO: se ha llevado por delante la linea que no se cogio")
    # **La compra, por su identificador.** No la primera de la lista: la que se acaba de
    # cerrar, que es la que el cierre devolvio.
    guardadas = almacen.compras_de(str(lista["id"]))
    guardada = next((c for c in guardadas
                    if str(c.get("compra_id")) == str(hecho.get("compra_id"))), None)
    if guardada is None:
        fallos += 1
        print(f"   FALLO: la compra {hecho.get('compra_id')} no ha quedado guardada")
    elif guardada["lineas"] != len(iban_en_el_carro):
        fallos += 1
        print(f"   FALLO: la compra dice {guardada['lineas']} lineas y en el carro iban"
              f" {len(iban_en_el_carro)}")
    else:
        print(f"   y queda guardada con su identificador: {guardada['lineas']} lineas, "
              f"{guardada['total_cent']} cent, {guardada['sin_precio']} sin precio")
    # Y sin nada en el carro, el boton lo dice en vez de inventar una compra vacia (409).
    r = cliente.post(f"/api/listas/{lista['id']}/cerrar")
    print(f"   y con el carro vacio -> {r.status_code} {r.json().get('detail')!r}")
    if r.status_code != 409:
        fallos += 1
        print("   FALLO: ha cerrado una compra sin nada en el carro")

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

    # == dos cuentas: aislamiento y autorizacion, con almacenamiento real ===============
    print("\n== dos cuentas: lo de uno no lo ve el otro, y la autorizacion es de quien la toma")
    otro = almacen.crea_usuario("la-otra", "La otra", "clave-de-prueba-123")
    # Una linea **con su producto pedido**, para poder confirmar QUE se acepta: un si sin producto no se
    # puede honrar, y la base lo rechaza desde la migracion 012.
    mia = almacen.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()),
                              "Leche entera", grupo_id=None, producto_id="dia:74397")
    r = cliente.post(f"/api/listas/{lista['id']}/lineas/{mia['id']}/autorizar",
                     params={"producto": "dia:74397", "cadena": "dia"})
    print(f"   {yo['usuario']} confirma su sustitucion -> {r.status_code}")
    if r.status_code != 200:
        fallos += 1
        print("   FALLO: no se pudo confirmar la sustitucion")
    # **Y se recarga la lista**: lo confirmado tiene que volver con su producto y su cadena.
    r = cliente.get(f"/api/listas/{lista['id']}")
    cuerpo = r.json() if r.status_code == 200 else {}
    recargada = next((x for x in cuerpo.get("lineas", []) if str(x["id"]) == str(mia["id"])), None)
    if recargada is None:
        fallos += 1
        print("   FALLO: la linea no vuelve al recargar la lista")
    elif not recargada.get("autorizado") or recargada.get("autorizado_producto") != "dia:74397" \
            or recargada.get("autorizado_cadena") != "dia":
        fallos += 1
        print(f"   FALLO: lo confirmado no vuelve entero al recargar ({recargada.get('autorizado_producto')},"
              f" {recargada.get('autorizado_cadena')})")
    else:
        print("   y al recargar vuelve entero: autorizado por dia:74397 en dia")
    # **La otra cuenta**, contra la misma linea: 404 y no 403, que diria que existe.
    main.app.dependency_overrides[main.usuario_actual] = lambda: otro
    r = cliente.post(f"/api/listas/{lista['id']}/lineas/{mia['id']}/autorizar",
                     params={"producto": "dia:1", "cadena": "dia"})
    print(f"   {otro['usuario']} intenta autorizar la linea de {yo['usuario']} -> {r.status_code}")
    if r.status_code != 404:
        fallos += 1
        print("   FALLO: a la otra cuenta se le contesta otra cosa que 404, o ha podido tocar lo ajeno")
    # Y lo de `yo` sigue como estaba.
    main.app.dependency_overrides[main.usuario_actual] = lambda: yo
    autorizadas = almacen.autorizacion_de(str(lista["id"]))
    if (autorizadas.get(str(mia["id"])) or {}).get("producto") != "dia:74397":
        fallos += 1
        print("   FALLO: el intento ajeno ha cambiado lo que autorizo el dueno de la linea")
    else:
        print("   y lo de la primera cuenta sigue igual despues del intento ajeno")

    # == la revocacion: el mismo boton, al reves ==========================================
    # **Confirmar y revocar van por la misma puerta** (`autorizado: bool = Query(default=True)`),
    # que es lo correcto: una sola ruta para decir si y no, con el estado en la base.
    print("\n== y se puede revocar: la linea vuelve a pedir confirmacion")
    # **Sobre una linea PROPIA, no sobre `mia`.** Dos guiones comparten esta base a proposito, y
    # `prueba_copia` comprueba al final que la confirmacion de `mia` sobrevive al volcado y a la
    # restauracion: revocarla aqui la dejaba vacia y la restauracion salia en rojo **por mi causa**.
    # Un escenario no puede consumir lo que otra prueba verifica. Medido el 13 de octubre de 2026.
    revocable = almacen.anade_linea(str(lista["id"]), str(yo["id"]), str(uuid.uuid4()),
                                    "Leche semidesnatada", grupo_id=None, producto_id="dia:74398")
    cliente.post(f"/api/listas/{lista['id']}/lineas/{revocable['id']}/autorizar",
                 params={"producto": "dia:74398", "cadena": "dia"})
    r = cliente.get(f"/api/listas/{lista['id']}")
    cuerpo = r.json() if r.status_code == 200 else {}
    antes = next((x for x in cuerpo.get("lineas", []) if str(x["id"]) == str(revocable["id"])), {})
    print(f"   la segunda linea queda confirmada: {bool(antes.get('autorizado'))}")
    if not antes.get("autorizado"):
        fallos += 1
        print("   FALLO: la segunda linea no se confirmo, asi que no hay nada que revocar")

    r = cliente.post(f"/api/listas/{lista['id']}/lineas/{revocable['id']}/autorizar",
                     params={"producto": "dia:74398", "cadena": "dia", "autorizado": "false"})
    print(f"   {yo['usuario']} revoca su sustitucion -> {r.status_code}")
    if r.status_code != 200:
        fallos += 1
        print("   FALLO: no se pudo revocar la sustitucion")
    r = cliente.get(f"/api/listas/{lista['id']}")
    cuerpo = r.json() if r.status_code == 200 else {}
    revocada = next((x for x in cuerpo.get("lineas", []) if str(x["id"]) == str(revocable["id"])),
                    None)
    if revocada is None:
        fallos += 1
        print("   FALLO: la linea desaparece de la lista al revocar, en vez de pedir confirmacion")
    elif revocada.get("autorizado"):
        fallos += 1
        print(f"   FALLO: sigue autorizada despues de revocar "
              f"({revocada.get('autorizado_producto')})")
    else:
        print("   y al recargar vuelve a pedir confirmacion, como antes de confirmarla")

    # == la alternativa: aparece cuando el motor la propone, y no cuando no la tiene ======
    # **Con datos controlados**, para que no dependa del catalogo de esta manana: un producto que
    # existe tiene que dar candidatos; uno que no existe, ninguno. Si el motor inventara una
    # alternativa para algo que no conoce, la pantalla ofreceria un cambio que no puede honrar.
    print("\n== la alternativa, con datos controlados")
    from plataforma.api import cesta

    pide = cesta.Peticion(None, "dia:74397", 1, "Leche entera")
    hay = cesta._candidatos([pide], cesta._fecha_de_hoy())
    alternativas = [k for k in hay if k[-1] == "alternativa"]
    print(f"   con un producto que existe: {len(hay)} candidatos, {len(alternativas)} alternativas")
    if not hay:
        fallos += 1
        print("   FALLO: un producto del catalogo no da ningun candidato")
    inventada = cesta.Peticion(None, "dia:no-existe-12345", 1, "Inventado")
    nada = cesta._candidatos([inventada], cesta._fecha_de_hoy())
    print(f"   con un producto que no existe: {len(nada)} candidatos")
    if nada:
        fallos += 1
        print("   FALLO: el motor propone algo para un producto que no existe en el catalogo")
    # == el coste: lo que la lista decia y lo que se guardo ==============================
    # **La invariante del dueno:** lo mostrado y lo cobrado tienen que coincidir. Se lee la estimacion y se
    # compara con el total que quedo guardado en la compra. Y se dice **si hubo oferta**, porque un empate de
    # una linea suelta pasaria por comprobacion sin serlo.
    print("\n== el coste: lo que la lista decia y lo que se guardo")
    vistas = almacen.lineas_de(str(lista["id"]))
    if vistas:
        print(f"   (quedan {len(vistas)} lineas vivas; la compra ya esta cerrada)")
    guardadas = almacen.compras_de(str(lista["id"]), limite=1)
    if not guardadas:
        fallos += 1
        print("   FALLO: no hay compra guardada que comparar")
    else:
        la_compra = guardadas[0]
        suyas = almacen.lineas_de_compra(str(la_compra["compra_id"]))
        suma_unitaria = sum(int(x["precio_cent"] or 0) * int(x["cantidad"]) for x in suyas)
        con_oferta = suma_unitaria != int(la_compra["total_cent"])
        print(f"   compra {la_compra['compra_id']}: {la_compra['lineas']} lineas, "
              f"total {la_compra['total_cent']} cent, sin precio {la_compra['sin_precio']}")
        print(f"   suma de unitario x cantidad: {suma_unitaria} cent  |  "
              f"{'HAY OFERTA aplicada' if con_oferta else 'sin oferta en estas lineas'}")
        # La invariante que si se puede comprobar aqui: el total guardado no puede ser **mayor** que la suma de
        # unitarios -- una oferta nunca sube el precio -- ni quedar por debajo de cero.
        if int(la_compra["total_cent"]) > suma_unitaria:
            fallos += 1
            print("   FALLO: la compra guardada cuesta mas que la suma de sus precios unitarios")
        if int(la_compra["total_cent"]) < 0:
            fallos += 1
            print("   FALLO: un total negativo")
        if not con_oferta:
            print("   (sin oferta en estas lineas: esta comprobacion no distingue el reparto, y lo digo)")

    # == el recorrido real del coste: estimacion, cierre e historico ======================
    # **La oferta es obligatoria.** No se espera a que el catalogo del dia traiga una: se busca un producto con
    # `3x2` y, si no hay ninguno, **falla** -- un escenario sin oferta no demuestra nada del reparto.
    print("\n== el coste, de punta a punta: estimacion, cierre e historico")
    from plataforma.api import cesta as _cesta

    con_oferta = _cesta.conexion().execute(
        "SELECT fuente || ':' || id_fuente, precio_cent, promo_txt FROM grupos "
        "WHERE promo_txt = '3x2' AND precio_cent > 0 LIMIT 1").fetchall()
    if not con_oferta:
        fallos += 1
        print("   FALLO: no hay ningun producto con 3x2 en el catalogo, y el escenario con oferta es obligatorio")
    else:
        pid, unitario, promo = con_oferta[0][0], int(con_oferta[0][1]), con_oferta[0][2]
        print(f"   producto de prueba: {pid} a {unitario} cent, oferta {promo}")
        mias = cliente.post("/api/listas", json={"nombre": "coste 3x2"}).json()
        la_lista = str(mias["id"])
        tres = almacen.anade_linea(la_lista, str(yo["id"]), str(uuid.uuid4()), "Prueba 3x2",
                                   grupo_id=None, producto_id=pid, cantidad=3)
        almacen.cambia_linea(la_lista, tres["id"], str(yo["id"]), en_carrito=True)
        # **La estimacion, sobre LAS LINEAS DEL CARRITO.** No sobre la lista entera: si quedara algo pendiente,
        # la comparacion seria contra un numero que no se cierra.
        carrito = [x for x in almacen.lineas_de(la_lista) if x.get("en_carrito")]
        antes = _cesta.estimacion(carrito)["total_cent"]
        partes = _cesta.coste_por_linea(carrito)
        suma_partes = sum(int(v.get("coste_cent") or 0) for v in partes.values())
        print(f"   estimacion del carrito: {antes} cent  |  suma de las partes: {suma_partes} cent")
        respuesta = cliente.post(f"/api/listas/{la_lista}/cerrar").json()
        print(f"   respuesta del cierre: {respuesta}")
        guardadas = almacen.compras_de(la_lista, limite=5)
        mia = next((c for c in guardadas if str(c["compra_id"]) == str(respuesta.get("compra_id"))), None)
        if mia is None:
            fallos += 1
            print(f"   FALLO: la compra {respuesta.get('compra_id')} no aparece en el historico")
        else:
            suyas = almacen.lineas_de_compra(str(mia["compra_id"]))
            # Total: estimacion, respuesta e historico, los tres el mismo numero.
            for etiqueta, valor in (("respuesta", respuesta.get("total_cent")),
                                    ("historico", mia["total_cent"])):
                if int(valor) != int(antes):
                    fallos += 1
                    print(f"   FALLO: la estimacion dijo {antes} y {etiqueta} dice {valor}")
            # Por linea: identidad y cantidad de cada una, y que las partes sumen el total guardado.
            if len(suyas) != len(carrito):
                fallos += 1
                print(f"   FALLO: se guardaron {len(suyas)} lineas y en el carrito iban {len(carrito)}")
            for guardada in suyas:
                print(f"   guardada: {guardada['nombre']} x{guardada['cantidad']} "
                      f"a {guardada['precio_cent']} cent en {guardada['cadena']}")
            if suma_partes != int(mia["total_cent"]):
                fallos += 1
                print(f"   FALLO: las partes suman {suma_partes} y el total guardado es {mia['total_cent']}")
            if int(antes) >= sum(int(x["precio_cent"] or 0) * int(x["cantidad"]) for x in suyas):
                fallos += 1
                print("   FALLO: el escenario no aplico la oferta: es obligatorio que la aplique")

    almacen.para()
    print(f"\n== {'TODO BIEN' if not fallos else f'{fallos} FALLO(S)'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())