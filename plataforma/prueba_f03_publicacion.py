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

            # 5. **Y la pantalla sigue sin errores**: no se ha roto por publicar debajo.
            comprueba(not errores, f"la pantalla no dio errores de JavaScript ({errores[:2]})")

            # 6. **El catalogo de casa, intacto.** *Es lo que hace que este ensayo se pueda repetir.*
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
