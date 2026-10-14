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

**Si esta en la tarea de las 06:00, y esto es un cambio de criterio.** *Antes decia aqui, y era verdad
entonces: «no esta en la tarea de las 06:00, a proposito... se ejecuta a mano y no puede romper la pasada
diaria».* **Y ya no: `run.py:40` lo tiene en `ORDEN`, y `run.py:234` usa `ORDEN` como la lista de fuentes
de la pasada diaria** -- *asi que **si corre a las 06:00**, y **lo que lo protege ya no es la ausencia,
sino el PRESUPUESTO**: `LIMITE_POR_EJECUCION` en `fichas_lidl.py`, y el `--limite` del lanzador.*

*Y esa es la forma del proyecto: **una proteccion que se quita se sustituye por otra, y la frase que la
describia se corrige en el mismo cambio.** La que habia aqui se quedo atras, y por eso se reescribe.*
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import polars as pl

from core import alcance, config, peticiones
from core.fetch import Fetcher
from core.runlog import log_run
from core.schemas import ESQUEMA_BRONZE
from core.storage import save_raw, write_parquet
from projects.cesta.sondear_lidl import (
    URL,
    extraer,
    precios_region,
    region_del_cp,
    regiones_del_html,
)

FUENTE = "lidl"
# **Y la region sale de la zona del usuario, que YA existe en `config`.** *`REGION_POR_DEFECTO` era
# «28», y su propio comentario decia lo que era: **«la unica observada; no es la zona del hogar de
# nadie»**.* **Elegirla habria publicado precios de una zona que no es la de quien los lee.**
#
# *Y `config.CODIGO_POSTAL` («tu zona», en sus palabras) ya fija el almacen de Mercadona y el ambito
# de Aldi.* **Asi que la zona es UNA, y es la del usuario.**
#
# *Pero un CP no es un id de `regionsV2`, y el plan prohibe suponerlo.* **Asi que se acredita por el
# nombre que la propia fuente publica** (`region_del_cp`), y **si no casa, no hay region y no se
# publica** -- *no se elige «la mas parecida».*
COBERTURA = "ofertas_semanales_parcial"


def _centimos(valor) -> int | None:
    """A centimos enteros, y None si no hay un numero que se pueda creer."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if isinstance(valor, bool) or not math.isfinite(numero) or numero < 0:
        return None
    return round(numero * 100)      # round de un argumento ya da un entero


def _detalle_precio(valor) -> dict:
    """La web usa currentPrice.price numerico y club.price.price; aceptar ambos."""
    if not isinstance(valor, dict):
        return {}
    while isinstance(valor.get("price"), dict):
        valor = valor["price"]
    return valor


def _fecha(valor):
    if not isinstance(valor, str):
        return None
    try:
        d = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except ValueError:
        return None


def _seleccion(precios, instante=None):
    if not isinstance(precios, dict):
        return {}, False
    for clave, club in (("currentPrice", False), ("currentLidlPlusPrice", True)):
        p = _detalle_precio(precios.get(clave))
        if _centimos(p.get("price")) is None:
            continue
        if instante is not None:
            inicio, fin = _fecha(p.get("startDate")), _fecha(p.get("endDate"))
            exclusivo = _fecha(p.get("endDateExclusive"))
            # Fechas rotas no habilitan una oferta. Sin fechas queda pendiente, no vigente.
            if not inicio or not (fin or exclusivo) or instante < inicio:
                continue
            if (exclusivo and instante >= exclusivo) or (fin and instante > fin):
                continue
        return p, club
    return {}, False


def _precio_de(precios: dict | None) -> tuple[int | None, int | None, bool]:
    """(lo que se cobra, el anterior, si hay precio de club) a partir de lo observado.

    Se lee `currentPrice` como lo que se cobra y `oldPrice`/`strikethroughPrice` como el anterior.
    Si lo unico que hay es el precio del club, se cobra ese **y se dice** que es de club: no se
    presenta como el precio general.
    """
    if not isinstance(precios, dict):
        return None, None, False
    actual, club = _seleccion(precios)
    anterior = actual.get("oldPrice", (actual.get("discount") or {}).get("deletedPrice"))
    if anterior is None:
        anterior = precios.get("oldPrice", precios.get("strikethroughPrice"))
    if isinstance(anterior, dict):
        anterior = _detalle_precio(anterior).get("price")
    precio = _centimos(actual.get("price"))
    viejo = _centimos(anterior)
    return precio, viejo, club


def a_registro(oferta: dict, region: str, instante: datetime | None = None) -> dict:
    """Una ficha de Lidl a una fila de bronze. Lo que no se sabe, se deja vacio y no se rellena."""
    precios = precios_region(oferta, region)
    precio, anterior, club = _precio_de(precios.get("precios"))
    detalle, club_elegible = _seleccion(precios.get("precios"), instante)
    if instante is not None:
        precio = _centimos(detalle.get("price"))
        club = club_elegible
        # El anterior debe pertenecer a la oferta elegida, no a otra vencida.
        anterior = _centimos(detalle.get("oldPrice", (detalle.get("discount") or {}).get("deletedPrice")))
    cantidad = detalle.get("packaging") or oferta.get("basePrice") or {}
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
        "promo_club": club,
        "promo": bool(club or detalle.get("discount")),
        "promo_txt": "Precio condicionado a Lidl Plus" if club else None,
        "promo_hasta": _fecha(detalle.get("endDateExclusive") or detalle.get("endDate")),
        "categoria": ((oferta.get("keyfacts") or {}).get("wonCategoryPrimary")
                      or oferta.get("campaignName") or
                      (oferta.get("category") if isinstance(oferta.get("category"), str) else None)),
        "url": urljoin("https://www.lidl.es", oferta.get("canonicalUrl") or ""),
        "imagen": oferta.get("image"),
        # Publicado no es lo mismo que en stock: esta fuente no dice stock, y no se finge.
        "disponible": None,
        # **Y la zona, que es de la que es este precio.** *Antes se usaba para resolverlo y no se
        # guardaba*, asi que 79 precios de Madrid estaban en bronze **sin decir que lo eran** --
        # y sin eso, dos precios de zonas distintas se pueden comparar como si fueran el mismo.
        #
        # *Se guarda el identificador de `regionsV2`* (hoy `"28"`), **que es el mismo que declara
        # la cobertura del dia** -- asi que un precio y su zona se atan por el mismo numero.
        "region": str(region),
        "capturado_en": instante or datetime.now(timezone.utc),
    }


def captura(html: str, region: str, hoy: date | None = None,
            instante: datetime | None = None) -> tuple[pl.DataFrame, dict]:
    """De HTML a (bronze, resumen de cobertura). Aplica el alcance y cuenta lo que no se guarda."""
    ofertas = extraer(html)
    filas, fuera, revision = [], 0, 0
    for oferta in ofertas:
        registro = a_registro(oferta, region, instante)
        decision = alcance.clasificar_alcance(registro["nombre"], registro["categoria"])
        if decision.estado == alcance.EXCLUIDO:
            fuera += 1
            # La respuesta ya se descargo: excluir una fila no evita una peticion.
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
        "con_precio": marco["precio_cent"].count(),
        "precios_con_vigencia_comprobada": instante is not None,
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
    ap.add_argument("--region", default=None,
                    help="identificador de region observado en regionsV2; si no se da, se "
                         "acredita desde config.CODIGO_POSTAL por el nombre publicado")
    a = ap.parse_args(argv)
    t0 = time.monotonic()
    errores = 0


    if a.web:
        peticiones.registra_al_salir(FUENTE)
        f = Fetcher(rate_per_sec=config.RITMO.get(FUENTE, 1.0))
        if not _robots_permite(f):
            print("  la politica publicada de la web no permite esa ruta: no se pide")
            log_run(FUENTE, 0, 1, time.monotonic() - t0)
            return 1
        # **Y si la peticion falla, se REGISTRA.** *Sin esto, una excepcion de red salia por el
        # `traceback` **sin tocar `runs.csv`**, y la ausencia de fila volvia a confundirse con «no se
        # ejecuto» -- *que es exactamente lo que el complemento del 14/10 senala.*
        #
        # *La causa va al `traceback` y a la salida estandar, que va a `data/ejecuciones.log`; *y el CSV
        # se queda con lo que si cabe: **que hubo intento y que no salio bien.** *
        try:
            respuesta = f.get(URL)
            save_raw(FUENTE, "ofertas-semanales", respuesta.body)
            html = respuesta.body.decode("utf-8", "replace")
        except Exception as fallo:  # noqa: BLE001  <- *a proposito: cualquier fallo de red se registra.*
            print(f"  la peticion fallo: {type(fallo).__name__}: {fallo}")
            log_run(FUENTE, 0, 1, time.monotonic() - t0, completa=False)
            return 1
    else:
        html = a.html.read_text(encoding="utf-8")

    # **La region: la del usuario, acreditada por el nombre que la fuente publica.**
    #
    # *Si se paso `--region`, se respeta -- es una eleccion explicita.* **Y si no, sale de
    # `config.CODIGO_POSTAL`** («tu zona»), *acreditando la correspondencia por el nombre -- porque un
    # codigo postal NO es un id de `regionsV2`, y suponerlo es lo que el plan prohibe.*
    region = a.region
    acreditacion = None
    if region is None:
        acreditacion = region_del_cp(config.CODIGO_POSTAL, regiones_del_html(html))
        if acreditacion["estado"] != "acreditada":
            print(f"  sin region acreditada para el CP {config.CODIGO_POSTAL}: "
                  f"{acreditacion['estado']} -- {acreditacion.get('motivo')}")
            print("  no se elige «la mas parecida»: se dice y se para. "
                  "Pasa --region=<id> si sabes cual, o cambia SCRAP_CP")
            # **Y se REGISTRA, que es lo que faltaba.** *Esta salida imprimia la causa y **retornaba 1
            # sin tocar `runs.csv`**, asi que **la ausencia de fila no se podia distinguir de «no se
            # ejecuto»**: *quien mirara el CSV veria que Lidl no aparece y **no sabria si fallo o si
            # nunca corrio.** *
            #
            # *Y el complemento del 14/10 lo dice con estas palabras: «ausencia de fila puede ser
            # ejecucion fallida sin telemetria, **no ausencia de ejecucion**». *
            #
            # *La causa **no cabe en el CSV** -- tiene seis columnas y ninguna es un motivo --, pero
            # **si sale por la salida estandar**, que va a `data/ejecuciones.log`: *las dos lineas de
            # arriba lo dicen, y ahora **el CSV dice que hubo intento.** *
            #
            # *Y `errores=1` con `completa=False`: **no es una captura buena**, y no puede servir de
            # referencia a `check_drift`.*
            log_run(FUENTE, 0, 1, time.monotonic() - t0, completa=False)
            return 1
        region = acreditacion["region"]
        print(f"  region acreditada por nombre: CP {config.CODIGO_POSTAL} -> "
              f"«{acreditacion['nombre']}» (region {region})")

    # **Y el parseo, igual.** *Una pagina que cambia de forma revienta en `captura`, y sin esto se
    # llevaba por delante la fila del CSV.* *Una fuente que falla **dejando rastro** se puede arreglar;
    # una que falla **callando** parece que no corre.*
    try:
        marco, resumen = captura(html, region, instante=datetime.now(timezone.utc))
    except Exception as fallo:  # noqa: BLE001
        print(f"  el parseo fallo: {type(fallo).__name__}: {fallo}")
        log_run(FUENTE, 0, 1, time.monotonic() - t0, completa=False)
        return 1
    print(f"  ofertas conocidas de Lidl ({resumen['cobertura']}): {marco.height} guardadas de "
          f"{resumen['fichas_leidas']} fichas leidas, {resumen['fuera_de_alcance']} fuera de "
          f"alcance, {resumen['en_revision']} en revision")
    print(f"  {resumen['aviso']}")
    # **Escribir es una decision, no un descuido.** La pasada diaria descubre las cadenas, asi que
    # un bronze de Lidl la haria lanzar este colector sola, con cobertura parcial. Ver la cabecera.
    if a.escribir:
        if not resumen["con_precio"]:
            print("  no se publica: no hay precios regionales con vigencia comprobada")
            log_run(FUENTE, 0, 1, time.monotonic() - t0)
            return 1
        write_parquet(marco, "bronze", FUENTE)
        # El fichero de cobertura: lo que la aplicacion tiene que poder ensenar junto al dato.
        destino = config.DATA / "cobertura"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / f"{FUENTE}-{resumen['fecha']}.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  bronze escrito y cobertura declarada en data/cobertura/{FUENTE}-"
              f"{resumen['fecha']}.json")
        # **El veredicto: NO es «errores == 0».** En Alcampo es `not detener and errores == 0`,
        # y `detener` es su juicio. El de Lidl es: se leyeron las ofertas y sus precios
        # traen vigencia comprobada. Y se apunta **solo si se escribio**: una pasada sin
        # `--escribir` no es una captura, y apuntarla diria que Lidl salio bien sin haber
        # guardado nada.
        completa = bool(resumen.get("precios_con_vigencia_comprobada")) and errores == 0
        log_run(FUENTE, marco.height, errores, time.monotonic() - t0, completa)
    else:
        print("  (sin --escribir: no se ha tocado bronze ni la cobertura del dia)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
