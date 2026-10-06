"""Lidl: ofertas conocidas de su pagina publica, con cobertura parcial dicha por delante.

**Que es y que no es.** Esto NO es el catalogo de Lidl. Es una lectura de su pagina publica de
ofertas semanales (`/c/ofertas-semanales/...`), que publica un numero acotado de fichas con precios
por region. Por eso:

  - se llama **ofertas conocidas**, y el nombre lo dice el propio fichero de cobertura que escribe;
  - no se declara a Lidl ganador de una cesta si le faltan productos;
  - la ausencia de un producto en la campana **no** es que se haya retirado.

**Lo que respeta, y por que.**

  - **robots.txt primero**, y una sola pagina. Sin API movil, sin login, sin rastrear bricolaje.
  - **El EAN no se inventa.** La ficha trae `ians` e identificadores internos; ninguno es un EAN
    comprobado, asi que `ean` va vacio. Un codigo inventado envenena las comparaciones (T03).
  - **El precio tachado no es el precio.** Lo que se cobra va en `precio_cent` y el anterior en
    `precio_anterior_nativo_cent`: confundirlos seria anunciar una bajada que no existe.
  - **La region se resuelve antes de mirar el precio** (`regionsV2[region].regionPriceId`), y el
    precio del club de Lidl se conserva como lo que es: una condicion, no el precio general.
  - **El estado de la region no es stock.** No hay stock en esta fuente y no se finge.

**No esta en la tarea de las 06:00, a proposito.** La ampliacion lo pide asi: *"pasar una captura
acotada antes de anadirlo a la tarea diaria"*. Se ejecuta a mano y no puede romper la pasada diaria.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

import polars as pl

from core import alcance, config, peticiones
from core.fetch import Fetcher
from core.schemas import ESQUEMA_BRONZE
from core.storage import save_raw, write_parquet
from projects.cesta.sondear_lidl import URL, extraer, precios_region

FUENTE = "lidl"
REGION_POR_DEFECTO = "28"        # la unica observada; no es la zona del hogar de nadie
COBERTURA = "ofertas_semanales_parcial"


def _centimos(valor) -> int | None:
    """A centimos enteros, y None si no hay un numero que se pueda creer."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if numero < 0:
        return None
    return round(numero * 100)      # round de un argumento ya da un entero


def _precio_de(precios: dict | None) -> tuple[int | None, int | None, bool]:
    """(lo que se cobra, el anterior, si hay precio de club) a partir de lo observado.

    Se lee `currentPrice` como lo que se cobra y `oldPrice`/`strikethroughPrice` como el anterior.
    Si lo unico que hay es el precio del club, se cobra ese **y se dice** que es de club: no se
    presenta como el precio general.
    """
    if not isinstance(precios, dict):
        return None, None, False
    club = bool(precios.get("currentLidlPlusPrice"))
    actual = precios.get("currentPrice") or precios.get("currentLidlPlusPrice") or {}
    anterior = precios.get("oldPrice") or precios.get("strikethroughPrice") or {}
    precio = _centimos((actual or {}).get("price", {}).get("price")
                       if isinstance(actual, dict) else None)
    viejo = _centimos((anterior or {}).get("price", {}).get("price")
                      if isinstance(anterior, dict) else None)
    return precio, viejo, club


def a_registro(oferta: dict, region: str) -> dict:
    """Una ficha de Lidl a una fila de bronze. Lo que no se sabe, se deja vacio y no se rellena."""
    precios = precios_region(oferta, region)
    precio, anterior, club = _precio_de(precios.get("precios"))
    cantidad = oferta.get("basePrice") or {}
    marca = oferta.get("brand") or {}
    return {
        "fuente": FUENTE,
        "id_fuente": f"{oferta.get('productId')}-{oferta.get('variantId') or 'sin-variante'}",
        "nombre": oferta.get("fullTitle") or oferta.get("title"),
        "marca": marca.get("name") if isinstance(marca, dict) else marca,
        # **Nunca se inventa un EAN**: `ians` es un identificador interno, no un codigo de barras
        # comprobado, y meterlo aqui envenenaria las comparaciones.
        "ean": None,
        "formato_txt": cantidad.get("text") if isinstance(cantidad, dict) else None,
        "precio_cent": precio,
        "precio_anterior_nativo_cent": anterior,
        "unidad_ref_nativa": "EUR/ud" if club else None,
        "categoria": oferta.get("campaignName") or oferta.get("category"),
        "url": oferta.get("canonicalUrl"),
        # Publicado no es lo mismo que en stock: esta fuente no dice stock, y no se finge.
        "disponible": True,
        "capturado_en": datetime.now(timezone.utc),
    }


def captura(html: str, region: str, hoy: date | None = None) -> tuple[pl.DataFrame, dict]:
    """De HTML a (bronze, resumen de cobertura). Aplica el alcance y cuenta lo que no se guarda."""
    ofertas = extraer(html)
    filas, fuera, revision = [], 0, 0
    for oferta in ofertas:
        registro = a_registro(oferta, region)
        decision = alcance.clasificar_alcance(registro["nombre"], registro["categoria"])
        if decision.estado == alcance.EXCLUIDO:
            fuera += 1
            peticiones.evita(FUENTE)
            continue
        if decision.estado == alcance.REVISAR:
            revision += 1
        filas.append(registro)
    marco = pl.DataFrame(filas, schema=ESQUEMA_BRONZE) if filas else pl.DataFrame(
        schema=ESQUEMA_BRONZE)
    resumen = {
        "fuente": FUENTE,
        "cobertura": COBERTURA,
        "url": URL,
        "region": region,
        "fecha": (hoy or date.today()).isoformat(),
        "fichas_leidas": len(ofertas),
        "productos_padre": len({str(o["productId"]) for o in ofertas}),
        "guardados": marco.height,
        "fuera_de_alcance": fuera,
        "en_revision": revision,
        # Lo que hay que ensenar en la aplicacion, con estas palabras y no otras.
        "aviso": ("ofertas conocidas de Lidl, no su catalogo completo: no certifica stock, ni "
                  "identidad de producto, ni que un producto ausente se haya retirado"),
    }
    return marco, resumen


def _robots_permite(f: Fetcher) -> bool:
    """Primero la politica publicada de la propia web: si no lo permite, no se pide."""
    respuesta = f.get("https://www.lidl.es/robots.txt")
    reglas = RobotFileParser()
    reglas.parse(respuesta.body.decode("utf-8", "replace").splitlines())
    return reglas.can_fetch("CestaResearch", URL)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    entrada = ap.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--html", type=Path, help="HTML ya guardado: sin red, para pruebas")
    entrada.add_argument("--web", action="store_true", help="robots.txt y una pagina publica")
    ap.add_argument("--escribir", action="store_true",
                    help="escribir bronze y la cobertura; sin esta bandera no se toca el pipeline")
    ap.add_argument("--region", default=REGION_POR_DEFECTO,
                    help="identificador de region observado en regionsV2 (no un codigo postal)")
    a = ap.parse_args(argv)

    if a.web:
        peticiones.registra_al_salir(FUENTE)
        f = Fetcher(rate_per_sec=config.RITMO.get(FUENTE, 1.0))
        if not _robots_permite(f):
            print("  la politica publicada de la web no permite esa ruta: no se pide")
            return 1
        respuesta = f.get(URL)
        save_raw(FUENTE, "ofertas-semanales", respuesta.body)
        html = respuesta.body.decode("utf-8", "replace")
    else:
        html = a.html.read_text(encoding="utf-8")

    marco, resumen = captura(html, a.region)
    print(f"  ofertas conocidas de Lidl ({resumen['cobertura']}): {marco.height} guardadas de "
          f"{resumen['fichas_leidas']} fichas leidas, {resumen['fuera_de_alcance']} fuera de "
          f"alcance, {resumen['en_revision']} en revision")
    print(f"  {resumen['aviso']}")
    # **Escribir es una decision, no un descuido.** La pasada diaria descubre las cadenas, asi que
    # un bronze de Lidl la haria lanzar este colector sola, con cobertura parcial. Ver la cabecera.
    if a.escribir:
        write_parquet(marco, "bronze", FUENTE)
        # El fichero de cobertura: lo que la aplicacion tiene que poder ensenar junto al dato.
        destino = config.DATA / "cobertura"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / f"{FUENTE}-{resumen['fecha']}.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  bronze escrito y cobertura declarada en data/cobertura/{FUENTE}-"
              f"{resumen['fecha']}.json")
    else:
        print("  (sin --escribir: no se ha tocado bronze ni la cobertura del dia)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
