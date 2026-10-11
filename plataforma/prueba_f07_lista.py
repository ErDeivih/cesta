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
        "SELECT id_fuente, nombre, categoria FROM grupos "
        "WHERE categoria IS NOT NULL AND precio_unidad_cent > 0 "
        "  AND categoria IN ('la-despensa/lacteos', 'frescos/quesos', 'bebidas/vinos') "
        "ORDER BY categoria LIMIT 6").fetchall()
    print(f"  productos elegidos: {len(filas)}")
    for f in filas:
        print(f"    {f[2]:24} {str(f[1])[:44]!r}")

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
        almacen.anade_linea(lista_id, identificador, str(uuid.uuid4()), str(f[1]),
                            grupo_id=None, cantidad=1 + i)
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

            # **La pantalla de la lista.** *`/compra` es la de buscar; la lista vive en la misma app, asi que
            # se prueban las dos y se dice cual tiene las lineas.*
            # **Las rutas, de la portada**: «Compra: Buscar, la lista, favoritos y lo que gastas». *La primera
            # version probaba `/lista`, que no existe («Esa pantalla no existe»).*
            for ruta in ("/compra/lista", "/compra", "/compra/favoritos", "/"):
                pagina.goto(f"{UI}{ruta}", wait_until="domcontentloaded")
                with contextlib.suppress(Exception):
                    pagina.wait_for_timeout(2500)
                cuerpo = pagina.locator("body").inner_text()
                tiene = [f for f in filas if str(f[1])[:18] in cuerpo]
                print(f"\n  --- {ruta}: {len(tiene)} de {len(filas)} productos en pantalla")
                if not tiene:
                    print(f"      la pantalla dice: {cuerpo[:300]!r}")
                if tiene:
                    print(f"      encabezados: {pagina.locator('h3, h2, [role=heading]').count()}")
                    for i in range(min(pagina.locator("h3, h2, [role=heading]").count(), 8)):
                        with contextlib.suppress(Exception):
                            print(f"        [{i}] {pagina.locator('h3, h2, [role=heading]').nth(i).inner_text()[:36]!r}")
                    # **Y las palabras de C04**, que es lo otro que hay que ver.
                    bajo = cuerpo.lower()
                    for palabra in ("lo de siempre", "habitual", "en el carro", "carrito", "comprado"):
                        if palabra in bajo:
                            print(f"      la pantalla dice {palabra!r}")
                    comprueba(not errores, f"sin errores de JavaScript en {ruta} ({errores[:1]})")
                    break

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
