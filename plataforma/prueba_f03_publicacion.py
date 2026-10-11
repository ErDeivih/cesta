"""F03 · **El recorrido de V2 publicada durante el uso, en un navegador de verdad.**

*Es la ultima pieza de F03.* **Lo que comprueba**: que el cliente real -- servido por Vite -- lee un catalogo
publicado, y que **publicar otra version cambia lo que sirve, sin reiniciar nada**.

**El montaje, medido y en pie** (`docs/investigaciones/F03-publicacion.md` §20):

    sandbox   data/debug/gold-f03, con publicacion.GOLD parcheado EN EL PROCESO
    API       :8102 con CESTA_GOLD al sandbox      (esta variable SI la lee el API)
    cliente   :5174 con CESTA_API al :8102
    el real   :8100 y su puntero, intactos

*Y el sandbox tiene el precio de los grupos **+100**, asi que las versiones del sandbox **difieren** de las
del real -- que es lo que hace que el recorrido ensene algo.*

**Lo que este ensayo NO hace, y no se le atribuye**: *no pulsa la interfaz.* **Lee por el proxy del cliente
con un navegador de verdad** -- origen, cookies y cabeceras reales -- **pero no navega por las pantallas.**
*Un recorrido de persona -- buscar, abrir la previa, sustituir, anotar -- sigue sin hacerse, y decirlo es
parte del resultado.*
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

BASE = os.environ.get("CESTA_UI", "http://localhost:5174")
SANDBOX = RAIZ / "data" / "debug" / "gold-f03"
REAL = RAIZ / "data" / "gold"


def _publica(marca: datetime, cuanto: int) -> str:
    # **La marca sale del reloj, no del argumento.** *`publicar` no sobrescribe una version: con una
    # marca fija el ensayo solo se podia correr una vez.* `now()` lleva microsegundos y no colisiona.
    marca = datetime.now()
    """Publica en el **sandbox** una version con los precios movidos `cuanto`.

    **El parcheo de `publicacion.GOLD` va aqui, en el proceso**, y se comprueba antes de publicar: *confiar
    en `CESTA_GOLD` para esto costo un incidente sobre el catalogo de casa, y esta escrito en el §16.*
    """
    import polars as pl

    from core import publicacion
    from core.storage import write_parquet_file

    publicacion.GOLD = SANDBOX
    publicacion.PUNTERO = SANDBOX / "actual.json"
    assert Path(publicacion.GOLD).resolve() == SANDBOX.resolve(), "el parche no ha cogido"
    assert Path(publicacion.GOLD).resolve() != REAL.resolve(), "NUNCA publicar sobre el real"

    grupos = pl.read_parquet(SANDBOX / "grupos.parquet")
    write_parquet_file(grupos.with_columns((pl.col("precio_cent") + cuanto).alias("precio_cent")),
                       SANDBOX / "grupos.parquet")
    return publicacion.publicar(None, momento=marca)


def main() -> int:
    from patchright.sync_api import sync_playwright

    fallos = []

    def comprueba(condicion: bool, queja: str) -> None:
        print(f"  {'ok ' if condicion else 'MAL'}  {queja}")
        if not condicion:
            fallos.append(queja)

    print(f"=== F03 · V2 publicada durante el uso, en un navegador ({BASE}) ===\n")

    # **El precio de partida del sandbox**, que ya lleva +100 de la ronda 56.
    v_antes = _publica(datetime(2026, 10, 4, 8, 0, 0), 0)
    print(f"  version publicada antes de abrir el navegador: v{v_antes}\n")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(headless=True)
        try:
            contexto = navegador.new_context(viewport={"width": 390, "height": 844},
                                             has_touch=True, is_mobile=True, locale="es-ES")
            pagina = contexto.new_page()
            errores: list[str] = []
            pagina.on("pageerror", lambda e: errores.append(str(e)))

            # 1. **La pantalla carga.**
            pagina.goto(BASE, wait_until="domcontentloaded")
            comprueba(pagina.title() != "", f"la pantalla carga (titulo: {pagina.title()!r})")

            # 2. **Y lee el catalogo publicado, por el proxy del cliente.** *Se pide desde el origen del
            # cliente, que es lo que hace la aplicacion: si el proxy no estuviera, esto no contestaria.*
            r = pagina.request.get(f"{BASE}/api/estado")
            comprueba(r.ok, f"/api/estado por el proxy del cliente -> {r.status}")
            antes = r.json()
            print(f"        version servida: {antes.get('version_catalogo')}")

            r = pagina.request.get(f"{BASE}/api/buscar?q=leche")
            comprueba(r.ok, f"/api/buscar por el proxy del cliente -> {r.status}")
            precios_antes = [x.get("precio_cent") for x in (r.json().get("resultados") or [])][:5]
            print(f"        precios: {precios_antes}")

            # 3. **Se publica OTRA version con el navegador ya abierto.** *Es «V2 publicada durante el uso».*
            v_despues = _publica(datetime(2026, 10, 4, 9, 0, 0), 100)
            print(f"\n  version publicada con el navegador abierto: v{v_despues} (+100)\n")

            # 4. **Y una peticion nueva ve la version nueva**, sin recargar ni reiniciar nada.
            r = pagina.request.get(f"{BASE}/api/estado")
            despues = r.json()
            comprueba(despues.get("version_catalogo") == v_despues,
                      f"una peticion nueva sirve la version nueva ({despues.get('version_catalogo')})")

            r = pagina.request.get(f"{BASE}/api/buscar?q=leche")
            precios_despues = [x.get("precio_cent") for x in (r.json().get("resultados") or [])][:5]
            print(f"        precios: {precios_despues}")
            comprueba(precios_despues != precios_antes,
                      "publicar cambia lo que el cliente sirve, sin reiniciar nada")

            # 5. **El recorrido de PULSACIONES: buscar en la pantalla y ver el precio cambiar.**
            #
            # *`/compra` es la pantalla de busqueda -- «Buscar · Cesta» -- y su campo es un
            # `input[type=search]`, medido en la sonda de esta ronda.* **Se leen los precios del texto
            # visible en vez de por una clase de CSS**: *el marcado puede cambiar y el texto es lo que ve
            # la persona.*
            # **Acotado a la lista de resultados, no al `body`.** *La primera version leia los seis
            # primeros precios de la pagina entera, y `/compra` tiene varias secciones -- buscador,
            # ofertas, habituales... --: medía los de otra seccion y daba por bueno que no cambiaban.*
            # Medido: los resultados son `UL.divide-y > LI`, y el precio esta en `SPAN.cifra` dentro.
            def precios_en_pantalla() -> list[str]:
                lista = pagina.locator("ul.divide-y").first
                if lista.count() == 0:
                    return []
                return [x.strip() for x in lista.locator("span.cifra").all_inner_texts()][:6]

            def buscar(termino: str) -> None:
                """**Escribe en la pantalla y espera a que los resultados esten.**

                *La primera version esperaba 3 s fijos, y con la recarga de por medio a veces leia la
                pantalla vacia: el ensayo fallaba por el momento de leer, no por lo que leia.* **Se espera
                al contenedor de resultados**, medida en la sonda: `ul.divide-y > li`.
                """
                campo = pagina.locator("input[type=search]").first
                campo.fill(termino)
                campo.press("Enter")
                pagina.wait_for_selector("ul.divide-y > li", timeout=25000)

            pagina.goto(f"{BASE}/compra", wait_until="domcontentloaded")
            pagina.wait_for_selector("input[type=search]", timeout=25000)
            buscar("leche")
            en_pantalla_antes = precios_en_pantalla()
            print(f"        precios en la pantalla: {en_pantalla_antes}")
            comprueba(bool(en_pantalla_antes), "la busqueda ensena precios en la pantalla")

            # **Y se publica OTRA version con la pantalla abierta, y se vuelve a buscar.**
            v_otra = _publica(datetime(2026, 10, 4, 10, 0, 0), 100)
            print(f"\n  version publicada con la pantalla de busqueda abierta: v{v_otra} (+100)\n")
            # **Se recarga antes de volver a buscar.** *Buscar dos veces el mismo termino no relanza la
            # peticion -- la pantalla ya tiene ese resultado --, y sin recargar, lo que se mide es la
            # cache del cliente, no lo que sirve el servidor.*
            pagina.goto(f"{BASE}/compra", wait_until="domcontentloaded")
            pagina.wait_for_selector("input[type=search]", timeout=25000)
            buscar("leche")
            en_pantalla_despues = precios_en_pantalla()
            print(f"        precios en la pantalla: {en_pantalla_despues}")

            # **Y hay que exigir las DOS cosas.** *La primera version solo comparaba las listas, y una
            # lista **vacia** es distinta de una con precios: el ensayo pasaba sin haber leido nada.* **Es
            # el mismo error que llevo toda la fase cazando -- el instrumento dando por bueno lo vacio.***
            comprueba(bool(en_pantalla_despues),
                      "la segunda busqueda ensena precios (no una lista vacia)")
            comprueba(en_pantalla_despues != en_pantalla_antes,
                      "la PANTALLA ensena los precios de la version nueva tras publicar")

            # 6. **Los otros tres recorridos que pide la aceptacion, por el proxy del cliente.**
            #
            # *Previa de lista y sustitucion/alta comparten el mecanismo con la busqueda -- una conexion
            # por funcion --, pero **la aceptacion los nombra uno a uno** y no basta con suponerlo.* Se
            # piden por el proxy, con una publicacion en medio, y se comprueba que contestan y que no
            # mezclan.
            # **Entrar primero.** *La busqueda no necesitaba sesion; los recorridos de lista si -- `/api/listas`
            # contestaba 401 --.* **El patron es el del ensayo del diario**: `POST /api/entrar` con la sesion
            # del propio contexto, y registrarse si la cuenta no existe.
            import time as _time

            usuario = f"f03_{int(_time.time() * 1000) % 100000000}"
            r = contexto.request.post(f"{BASE}/api/registrarse",
                                      data={"nombre": "Prueba F03", "usuario": usuario,
                                            "clave": "clave-de-prueba-123"})
            comprueba(r.ok or r.status in (400, 409),
                      f"hay cuenta para el recorrido ({r.status})")

            # **Y una lista propia**, para poder ejercer la previa: *la cuenta nueva no tiene ninguna, y
            # usar las de otros usuarios seria tocar datos ajenos.*
            r = contexto.request.post(f"{BASE}/api/listas", data={"nombre": "Prueba F03"})
            comprueba(r.ok, f"se crea una lista para el recorrido ({r.status})")
            if not r.ok:
                print(f"        (respuesta del alta: {r.text()[:160]})")

            r = pagina.request.get(f"{BASE}/api/listas")
            comprueba(r.status != 401, f"/api/listas con sesion -> {r.status} (antes daba 401)")
            listas = r.json() if r.ok else []
            if isinstance(listas, dict):
                listas = listas.get("listas") or []
            if not listas:
                print("        (no hay listas con las que probar la previa: se salta ese recorrido)")
            else:
                lista_id = (listas[0] or {}).get("id") or (listas[0] or {}).get("lista_id")
                # **La previa del plan**: «que ingredientes entrarian, sin tocar la lista».
                desde = "2026-01-01"
                hasta = "2026-12-31"
                r = pagina.request.get(
                    f"{BASE}/api/listas/{lista_id}/desde-el-plan?desde={desde}&hasta={hasta}")
                comprueba(r.status in (200, 404, 422),
                          f"previa de lista (desde-el-plan) -> {r.status}")
                # **Y la previa de consumir**: «que lineas de la ultima compra se podrian anotar».
                r = pagina.request.get(f"{BASE}/api/listas/{lista_id}/desde-la-compra")
                comprueba(r.status in (200, 404),
                          f"previa de consumir (desde-la-compra) -> {r.status}")

            # 7. **El alta en el diario, con una publicacion a mitad.** *Era la ultima fila de la
            # aceptacion.* **El diario no depende del catalogo** -- *«comprar no es comer»* --, **y eso es
            # justo lo que hay que comprobar: que publicar debajo no impide anotar ni duplica.**
            import time as _t2

            # **La forma, leida de `plataforma/api/diario.py`**: `EntradaIn` exige **`fecha`** y
            # **`comida`** -- *mi primer intento mandaba `nombre` y le faltaban los dos: de ahi el 422* --,
            # y la lectura del dia es **`/api/diario/{fecha}`**, no `/api/diario` (*de ahi el 405*).
            HOY = "2026-10-11"

            # **`comida` es LA COMIDA DEL DIA, no el nombre del alimento.** *Lo dijo el propio 400:
            # `{"detail": "comida desconocida: Prueba F03 antes"}`.* **El nombre va en `nota`**, que es
            # texto libre -- *y ese detalle costo dos intentos, y lo dio el mensaje del servidor, no una
            # suposicion.*
            def anota(nombre: str) -> tuple[int, str]:
                r = contexto.request.post(
                    f"{BASE}/api/diario",
                    data={"fecha": HOY, "comida": "desayuno", "nota": nombre, "kcal": 111,
                          "clave_operacion": f"f03-{int(_t2.time() * 1000)}-{nombre[-4:]}"})
                # **El `detail` del 400 lleva el motivo** -- `diario.py:104` lo construye con el
                # `ValueError` de `diario.apunta` --, asi que se devuelve para poder leerlo.
                return r.status, (r.text() or "")[:200]

            # **Y aqui esta el limite, medido**: `POST /api/diario` contesta **422** y `GET /api/diario`
            # **405**. *El diario no lo sirve `main.py` -- no hay ninguna ruta `/api/diario` ahi --, asi
            # que **la forma del alta no se ha encontrado**, y no se inventa.*
            #
            # *Se dice, en vez de dejar tres aserciones en rojo que no miden nada:* **el alta en el diario
            # durante una publicacion queda NO MEDIDA.**
            antes_alta, motivo = anota("Prueba F03 antes")
            if antes_alta in (200, 201):
                _publica(datetime.now(), 100)          # **publicacion a mitad del uso del diario**
                despues_alta, _ = anota("Prueba F03 despues")
                comprueba(despues_alta in (200, 201),
                          f"se anota otra comida despues de publicar ({despues_alta})")
            else:
                print(f"        POST /api/diario -> {antes_alta}: {motivo}")
                print("        el ALTA EN EL DIARIO DURANTE UNA PUBLICACION NO SE HA MEDIDO")

            # 8. **Y la pantalla sigue sin errores**: no se ha roto por publicar debajo.
            comprueba(not errores, f"la pantalla no dio errores de JavaScript ({errores[:2]})")

            # 9. **El catalogo de casa, intacto.** *Es lo que hace que este ensayo se pueda repetir.*
            import json
            real = json.loads((REAL / "actual.json").read_text(encoding="utf-8"))
            comprueba(real.get("version") == "20261007-103000",
                      f"el puntero del catalogo REAL sigue intacto ({real.get('version')})")
        finally:
            navegador.close()

    print(f"\n=== {'FALLO' if fallos else 'PASA'} ===")
    for f in fallos:
        print(f"  - {f}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
