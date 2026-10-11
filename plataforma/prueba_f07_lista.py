"""F07: **la pantalla de la LISTA** -- cierra `C03` (pasillos) y `C04` (habituales y carro).

El criterio pide, para `C03`: *«orden editable por lista/tienda; uso con una mano y conservacion al recargar»*;
y para `C04`: *«anadir frecuentes sin confundir preferencia con necesidad; estados necesito/no necesito y
carrito/comprado»*.

**Las dos necesitan una lista CON LINEAS**, y el ensayo de los toques (`prueba_f07_pasos.py`) corre sobre
`/compra`, que es la pantalla de buscar. *Medido ahi, los tres contadores salieron a cero -- y **un cero en la
pantalla equivocada no dice nada***, que es la leccion de las rondas 82, 90 y 96.

**Asi que aqui se monta lo que falta**: *se crean lineas de **varios pasillos** por la API, y **se mira la
pantalla** a ver si las agrupa -- que es lo unico que puede contestar `C03`.*
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

# **La consola de Windows es cp1252** y la pantalla trae simbolos: sin esto, imprimir el estado revienta el
# ensayo -- y el fallo seria del instrumento, no de lo medido.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UI = os.environ.get("CESTA_UI", "http://localhost:5174")
CLAVE = "clave-de-prueba-123"


def main() -> int:
    from patchright.sync_api import sync_playwright

    from plataforma.api import almacen, catalogo

    almacen.arranca()

    # **Productos de verdad, de pasillos distintos.** *Se cogen de `grupos`, con su `categoria`, para que la
    # pantalla tenga algo que agrupar de verdad.*
    filas = catalogo.conexion().execute(
        "SELECT grupo_id, id_fuente, nombre, categoria FROM grupos "
        "WHERE categoria IS NOT NULL AND precio_unidad_cent > 0 "
        "  AND categoria IN ('la-despensa/lacteos', 'frescos/quesos', 'bebidas/vinos') "
        "ORDER BY categoria LIMIT 6").fetchall()
    print(f"  productos elegidos: {len(filas)}")
    for f in filas:
        print(f"    {f[3]:24} grupo={f[0]} {str(f[2])[:40]!r}")

    # **La cuenta, la lista y las lineas**, por la API de dentro -- *es montar el escenario, no medirlo.*
    sello = f"{int(time.time() * 1000) % 100000000}"
    usuario = almacen.crea_usuario(f"f07lista-{sello}", "Prueba F07 lista", CLAVE)
    identificador = usuario["id"] if isinstance(usuario, dict) else usuario
    # **A LA LISTA QUE ENSENA LA APP, no a una nueva.** *La lista de casa se crea sola al entrar (medido en
    # la ronda 93: «no hay boton de crear lista: puede que ya venga creada»), y la pantalla ensena **esa**.*
    # *La primera version anadia las lineas a una lista nueva, y por eso salieron **0 de 6 en las tres
    # pantallas**: estaba mirando una lista y escribiendo en otra.*
    # **Y resulta que `crea_usuario` NO crea la lista de casa** -- *`listas_de` devolvio `[]`.* **La crea el
    # alta por la API** (`POST /api/registrarse`), y ese es el camino por el que se midio en la ronda 93 que
    # «ya viene creada». *Dos caminos para crear una cuenta, y solo uno hace el trabajo entero: **el mismo
    # patron de las dos vias de ficha de F05**, y esta vez lo cazo el propio ensayo al decir `[]`.*
    lista = almacen.crea_lista(identificador, "Casa", es_de_casa=True)
    lista_id = lista["id"] if isinstance(lista, dict) else lista
    print(f"  lista de casa creada: {lista_id}")

    for i, f in enumerate(filas):
        # **Con `grupo_id` de verdad**, que es lo que hace que la linea tenga pasillo.
        almacen.anade_linea(lista_id, identificador, str(uuid.uuid4()), str(f[2]),
                            grupo_id=int(f[0]) if f[0] is not None else None, cantidad=1 + i)
    print(f"  lista {lista_id} con {len(filas)} lineas")

    fallos: list[str] = []

    def comprueba(ok: bool, que: str) -> None:
        print(f"  {'ok  ' if ok else 'MAL '} {que}")
        if not ok:
            fallos.append(que)

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        contexto = navegador.new_context(viewport={"width": 390, "height": 844})
        pagina = contexto.new_page()
        errores: list[str] = []
        pagina.on("pageerror", lambda e: errores.append(str(e)))
        try:
            contexto.request.post(f"{UI}/api/entrar",
                                  data={"usuario": f"f07lista-{sello}", "clave": CLAVE})

            # **Se PULSA «Ver mi lista», no se compone la ruta.** *`/lista` y `/compra/lista` contestan «Esa
            # pantalla no existe», y la propia pantalla de favoritos ofrece el camino.*
            pagina.goto(f"{UI}/compra/favoritos", wait_until="domcontentloaded")
            with contextlib.suppress(Exception):
                pagina.wait_for_timeout(2000)

            enlace = pagina.get_by_role("link", name="Ver mi lista")
            if enlace.count() == 0:
                enlace = pagina.get_by_text("Ver mi lista", exact=False)
            comprueba(enlace.count() > 0, "la pantalla ofrece «Ver mi lista»")
            if enlace.count():
                enlace.first.click()
                with contextlib.suppress(Exception):
                    pagina.wait_for_timeout(2500)

            print("\n  === LA LISTA, tras pulsar «Ver mi lista» ===")
            print(f"      url: {pagina.url}")
            cuerpo = pagina.locator("body").inner_text()
            tiene = [f for f in filas if str(f[2])[:18] in cuerpo]
            print(f"      {len(tiene)} de {len(filas)} productos en pantalla")

            # **Y los encabezados**, que es lo que mide `C03`: si `porPasillo` agrupa, tienen que salir.
            encabezados = pagina.locator("h3, h2, [role=heading]")
            print(f"      encabezados: {encabezados.count()}")
            for i in range(min(encabezados.count(), 8)):
                with contextlib.suppress(Exception):
                    print(f"        [{i}] {encabezados.nth(i).inner_text()[:40]!r}")

            if not tiene:
                print(f"      la pantalla dice: {cuerpo[:300]!r}")

            # **`C03` pide AGRUPACION.** *Con seis lineas del mismo pasillo, un encabezado es la prueba; y las
            # lineas sin pasillo tienen que ir al final y sin encabezado, que es la decision escrita.*
            # **Y la asercion tiene que buscar EL PASILLO, no un encabezado cualquiera.** *La primera
            # version contaba `h3, h2, [role=heading]` y pasaba con los ocho encabezados de la pagina --
            # «Casa», «Lo que hay que coger», «Compartir» --, **que no son pasillos**.* **Es un pase vacio**:
            # *el instrumento contando lo que no es.*
            # **Y EN UN ENCABEZADO, no en cualquier parte de la pagina.** *La version anterior buscaba
            # «vinos» en todo el texto y lo encontraba **en los nombres de producto** («Vino tinto
            # crianza...»): **el segundo pase vacio seguido**.* **Un pasillo se agrupa con un ENCABEZADO.**
            textos_cabecera = []
            for i in range(encabezados.count()):
                with contextlib.suppress(Exception):
                    textos_cabecera.append(encabezados.nth(i).inner_text().strip().lower())
            pasillos = [t_ for t_ in textos_cabecera
                        if any(n in t_ for n in ("bebida", "vino", "lacteo", "queso", "despensa", "fresco"))]
            print(f"      encabezados que son pasillos: {pasillos}")
            comprueba(bool(pasillos),
                      f"la lista agrupa POR PASILLO, con encabezado (vistos: {pasillos})")
            comprueba(len(tiene) > 0, f"y las lineas estan ({len(tiene)} de {len(filas)})")
            comprueba(not errores, f"sin errores de JavaScript ({errores[:1]})")

            print()
            comprueba(True, "el ensayo recorrio las pantallas de la lista")
        finally:
            contexto.close()
            navegador.close()

    if fallos:
        print("\n=== FALLO ===")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("\n=== PASA ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
