"""El vigilante de la ingesta: que la cadena diaria diga sola si ha ido bien.

**Por que existe.** El punto 3 del encargo de David es «la ingesta sigue sola y sin errores;
avisos si falla». Hasta hoy, saberlo exigia abrir nueve sitios y saberse sus formatos:

  - `data/runs.csv` -- una fila por pasada, con el `ok` **que decide el colector**;
  - `data/ultima_ejecucion.txt` -- el ultimo dia que **llego a cerrarse**;
  - `data/ejecucion_en_curso.txt` -- la marca que `run.py` deja al empezar y borra al final;
  - `data/bronze/fuente=<cadena>/fecha=<dia>/` -- la captura del dia;
  - `data/gold/precio_diario.parquet` y `data/gold/actual.json` -- lo que hay publicado;
  - `data/cobertura/<cadena>-<dia>.json` -- lo que cada cadena declara de su dia;
  - `data/avisos.json` y `metricas-cesta.json` -- los avisos de la cadena y el panel.

Todo estaba escrito y **nada lo leia junto**, asi que la pregunta «¿sigue sola?» se contestaba
abriendo ficheros a mano, que es exactamente lo que un dia no se hace.

Esto lo lee junto, no sale a la red y no toca nada de la cadena: **solo lectura local** mas su
propio `data/avisos_ingesta.json`.

    .\\.venv\\Scripts\\python.exe -m scripts.vigilar_ingesta
    .\\.venv\\Scripts\\python.exe -m scripts.vigilar_ingesta --json
    .\\.venv\\Scripts\\python.exe -m scripts.vigilar_ingesta --fecha 2026-11-04

Sale **0 si todo esta bien y 1 si hay algun aviso o algun fallo**. Y si no puede mirar --ni
`runs.csv`, ni bronce, ni gold-- el informe es un **fallo**, nunca un 0: un vigilante que
aprueba en silencio cuando no tiene con que comparar es peor que no tener vigilante.

**Las reglas no se copian.** «Filas contra su referencia» es `veredicto` de
`projects.cesta.cobertura_diaria` -- su ventana de 30 dias y su 90 % --, y **que cadenas se
comparan asi lo dice `cobertura_diaria.FUENTES`**: las cinco de catalogo. Lidl declara un
alcance parcial (82-110 ofertas semanales) y su serie no se puede leer contra un maximo; por
eso se vigila igual (pasada, ok, bronce, gold) pero sin comparacion de filas. Si el dia sale
«corta», se dice «corta»: bajar el liston aqui seria repetir el fallo que ese modulo cuenta.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
from contextlib import suppress
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from core import config
from projects.cesta.cobertura_diaria import FUENTES as CADENAS_CON_REFERENCIA
from projects.cesta.cobertura_diaria import veredicto

#: Las seis que dejan fila en `runs.csv`, **en el orden de `run.ORDEN`** (no se importa `run`:
#: ese modulo arrastra los seis colectores y la cadena entera).
ORDEN = ("carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl")

#: La ventana de la referencia. Es la de `cobertura_diaria`, escrita aqui para que el informe
#: diga con cuantos dias compara; la cuenta la hace `veredicto`.
DIAS_DE_VENTANA = 30

#: Una marca de ejecucion de hoy con mas horas que esto ya no es «va por el principio»: es una
#: pasada que se quedo a medias. La cadena entera tarda ~90 minutos; seis horas dan aire.
HORAS_DE_UNA_PASADA = 6

FICHERO = "avisos_ingesta.json"

AVISO = "aviso"
FALLO = "fallo"


# ------------------------------------------------------------------------------- leer ---


def _json(ruta: Path) -> dict | None:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _texto(ruta: Path) -> str | None:
    try:
        return ruta.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _dia(fecha: str | dt.date | None) -> dt.date | None:
    if fecha is None or isinstance(fecha, dt.date):
        return fecha
    return dt.date.fromisoformat(str(fecha))


def pasadas(datos: Path) -> list[dict]:
    """Las filas de `data/runs.csv`, con el `ts` ya leido y ordenadas por hora.

    El `ts` va en **UTC** y el dia de la captura es **local** (una pasada a las 00:30 de Madrid
    es el dia anterior en UTC); aqui solo se guarda el instante, la conversion la hace
    `pasada_del_dia` con la zona del proyecto. Una fila ilegible se salta: un CSV a medio
    escribir no puede tumbar el informe, pero tampoco puede inventarse una pasada.
    """
    ruta = datos / "runs.csv"
    if not ruta.is_file():
        return []
    salida: list[dict] = []
    try:
        with ruta.open(encoding="utf-8", newline="") as fh:
            for fila in csv.DictReader(fh):
                try:
                    cuando = dt.datetime.fromisoformat(str(fila["ts"]))
                    if cuando.tzinfo is None:
                        cuando = cuando.replace(tzinfo=dt.timezone.utc)
                    n = int(fila["filas"])
                    errores = int(fila["errores"])
                except (KeyError, TypeError, ValueError):
                    continue
                salida.append({
                    "ts": str(fila["ts"]),
                    "cuando": cuando,
                    "fuente": str(fila.get("fuente") or "").strip(),
                    "filas": n, "errores": errores,
                    "ok": str(fila.get("ok", "")).strip().lower() in {"true", "1"},
                })
    except OSError:
        return []
    salida.sort(key=lambda p: p["cuando"])
    return salida


def pasada_del_dia(lista: list[dict], fuente: str, dia: dt.date, zona) -> dict | None:
    """La **ultima** pasada de esa cadena ese dia (en hora de Madrid), o `None`.

    La ultima y no la primera: un dia con reintentos interesa como acabo, no como empezo.
    """
    del_dia = [p for p in lista
               if p["fuente"] == fuente and p["cuando"].astimezone(zona).date() == dia]
    return del_dia[-1] if del_dia else None


def bronce(datos: Path) -> dict[str, dict[str, dict]]:
    """`{cadena: {fecha: {"filas", "ficheros", "escrita"}}}` leido de `data/bronze/`.

    Se leen los **metadatos** de cada parquet (`num_rows`), no las filas: treinta dias de seis
    cadenas son ~180 ficheros y asi son milisegundos. Una particion **sin parquet no es un dia**
    (es una captura que se nego a escribir), y un parquet ilegible se salta en vez de contar
    cero: contar cero seria decir «trajo nada», que es otra cosa.
    """
    salida: dict[str, dict[str, dict]] = {}
    base = datos / "bronze"
    if not base.is_dir():
        return salida
    for carpeta in sorted(base.glob("fuente=*")):
        fuente = carpeta.name.split("=", 1)[1]
        serie: dict[str, dict] = {}
        for parte in sorted(carpeta.glob("fecha=*")):
            ficheros = sorted(parte.glob("*.parquet"))
            if not ficheros:
                continue
            filas = 0
            escritas: list[float] = []
            for fichero in ficheros:
                try:
                    filas += pq.ParquetFile(fichero).metadata.num_rows
                    escritas.append(fichero.stat().st_mtime)
                except Exception:  # noqa: BLE001  (a medio escribir no invalida el dia)
                    continue
            if not escritas:
                continue
            serie[parte.name.split("=", 1)[1]] = {
                "filas": filas,
                "ficheros": len(escritas),
                "escrita": dt.datetime.fromtimestamp(max(escritas)).isoformat(timespec="seconds"),
            }
        if serie:
            salida[fuente] = serie
    return salida


def fechas_de_gold(datos: Path) -> dict[str, str] | None:
    """`{cadena: ultima fecha en gold}`, o `None` si no hay `precio_diario.parquet`.

    `None` y `{}` no son lo mismo: `None` es «no hay nada publicado» (fallo), `{}` seria «hay
    fichero y no tiene ni una fila» (tambien fallo, pero se distingue en el texto). Se lee con
    duckdb la columna `fecha` nada mas: 34 MB de parquet no se traen a Python para un maximo.
    """
    ruta = datos / "gold" / "precio_diario.parquet"
    if not ruta.is_file():
        return None
    con = duckdb.connect()
    try:
        con.execute("SET enable_progress_bar=false")
        comillas = ruta.as_posix().replace("'", "''")
        filas = con.execute(
            f"SELECT fuente, max(fecha) FROM read_parquet('{comillas}') GROUP BY 1").fetchall()
    except Exception:  # noqa: BLE001  (un parquet ilegible es «no se pudo leer», no «no hay»)
        return None
    finally:
        con.close()
    return {str(fuente): str(ultima) for fuente, ultima in filas if fuente is not None}


def marca_de_pasada(datos: Path, dia: dt.date, ahora: dt.datetime) -> dict | None:
    """La marca de `data/ejecucion_en_curso.txt`, interpretada: ¿pasada viva o muerta?

    `run.py` escribe la marca al empezar y la borra solo al terminar entero; si el proceso
    muere, se queda. La siguiente pasada lo dice **en el log**, que es donde nadie mira: este
    chequeo lo saca al informe.

    Reglas, y por que:

      - marca de un dia **anterior**: esa pasada no termino (seguro, no hace falta reloj);
      - marca de **hoy con hora**: se compara con el reloj **solo si se esta mirando el dia de
        hoy**; con mas de `HORAS_DE_UNA_PASADA` se da por muerta, y si se esta reconstruyendo un
        dia pasado se da por viva (no hay reloj con el que compararla sin inventarselo);
      - marca de hoy **sin hora** (o sin fecha legible): se da por viva, y si no se puede leer
        se dice igual, porque una marca que nadie entiende es una marca que nadie mira.
    """
    texto = _texto(datos / "ejecucion_en_curso.txt")
    if not texto:
        return None
    base = {"texto": texto[:40], "fecha": None, "en_curso": True, "a_medias": False}
    try:
        fecha_marca = dt.date.fromisoformat(texto.split(" ", 1)[0])
    except ValueError:
        return {**base, "en_curso": False, "a_medias": True}
    if fecha_marca != dia:
        return {**base, "fecha": fecha_marca, "en_curso": False, "a_medias": fecha_marca < dia}
    horas = None
    if ahora.date() == dia:
        try:
            inicio = dt.datetime.fromisoformat(texto.replace(" ", "T"))
        except ValueError:
            inicio = None
        if inicio is not None:
            horas = (ahora.replace(tzinfo=None) - inicio).total_seconds() / 3600.0
    en_curso = horas is None or horas <= HORAS_DE_UNA_PASADA
    return {**base, "fecha": fecha_marca, "en_curso": en_curso,
            "a_medias": not en_curso, "horas": horas}


# ----------------------------------------------------------------------------- juzgar ---


def vigila(datos: Path | str | None = None, fecha: str | dt.date | None = None,
           ahora: dt.datetime | None = None) -> dict:
    """El informe entero, como diccionario. Es lo que se imprime y lo que se deja en disco.

    `datos` y `fecha` se pueden pasar para probar el vigilante con datos sinteticos y un dia
    fijo; sin ellos mira `config.DATA` y el dia de hoy en Madrid.
    """
    datos = Path(datos) if datos is not None else config.DATA
    zona = config.ZONA_HORARIA
    ahora = ahora or dt.datetime.now(zona)
    dia = _dia(fecha) or ahora.astimezone(zona).date()
    iso = dia.isoformat()

    avisos: list[dict] = []

    def apunta(codigo: str, gravedad: str, texto: str, cadena: str | None = None) -> None:
        avisos.append({"codigo": codigo, "gravedad": gravedad, "cadena": cadena,
                       "texto": texto})

    marca = marca_de_pasada(datos, dia, ahora)
    en_curso = bool(marca and marca["en_curso"])

    lista = pasadas(datos)
    capturas = bronce(datos)
    series = {fuente: {f: cap["filas"] for f, cap in serie.items()}
              for fuente, serie in capturas.items()}
    gold = fechas_de_gold(datos)
    gold_max = max(gold.values()) if gold else None
    actual = _json(datos / "gold" / "actual.json")

    declaradas = sorted(
        fuente for fuente in ORDEN
        if (datos / "cobertura" / f"{fuente}-{iso}.json").is_file())

    cadenas: list[dict] = []
    for fuente in ORDEN:
        motivos: list[dict] = []

        # **`motivos` y `fuente` van atados como valores por defecto a proposito**: sin eso, el
        # cierre se queda mirando la variable del bucle y ruff lo avisa (B023) porque la ficha
        # que se guarda acabaria contando los motivos de otra cadena. Con el valor atado, cada
        # vuelta tiene su lista y su nombre.
        def mal(codigo: str, gravedad: str, texto: str,
                motivos: list[dict] = motivos, fuente: str = fuente) -> None:
            motivos.append({"codigo": codigo, "gravedad": gravedad})
            apunta(codigo, gravedad, texto, fuente)

        pasada = pasada_del_dia(lista, fuente, dia, zona)
        captura = capturas.get(fuente, {}).get(iso)
        gold_de_la_cadena = (gold or {}).get(fuente)

        # 1. La pasada del dia, y si el colector la dio por buena. `ok` no es «cero errores»:
        #    es lo que el colector decide (Carrefour tolera cuatro o cinco categorias rotas y
        #    su dia es correcto). Aqui se lee, no se reinterpreta.
        if pasada is None:
            if en_curso:
                mal("en_curso", AVISO,
                    f"la pasada del {iso} empezo el {marca['texto']} y aun no ha llegado a esta "
                    f"cadena")
            else:
                mal("sin_pasada", FALLO,
                    f"no hay pasada del {iso} en data/runs.csv: esta cadena no corrio")
        elif not pasada["ok"]:
            mal("pasada_no_ok", FALLO,
                f"la pasada del {pasada['cuando'].astimezone(zona):%H:%M} no acabo bien: "
                f"{pasada['filas']} filas, {pasada['errores']} errores, ok=False")
        elif pasada["filas"] <= 0:
            mal("pasada_sin_filas", FALLO,
                f"la pasada del {pasada['cuando'].astimezone(zona):%H:%M} acabo bien con cero "
                f"filas")

        # 2. La particion de bronce del dia. Solo se exige si la cadena consta como corrida: si
        #    no hay ni pasada, la ausencia de bronce es la misma cosa contada dos veces, y un
        #    informe que dice dos veces lo mismo se deja de leer.
        if captura is None and pasada is not None:
            mal("sin_bronce", FALLO,
                f"no hay particion de bronce del {iso} con parquet: la captura no quedo en disco")

        # 3. Las filas contra su referencia, con la regla de `cobertura_diaria` tal cual. Las
        #    ausencias no se repiten aqui: ya las dicen los dos chequeos de arriba.
        referencia = None
        if fuente in CADENAS_CON_REFERENCIA:
            referencia = veredicto(series.get(fuente, {}), iso, dias=DIAS_DE_VENTANA)
            if referencia["veredicto"] == "corta":
                mal("captura_corta", AVISO,
                    f"{_cifra(referencia['filas'])} filas contra "
                    f"{_cifra(referencia['referencia'])} de referencia "
                    f"(la vara es del {referencia['referencia_fecha']}, "
                    f"{referencia['pct']} %): la captura se quedo corta")

        # 4. Que su precio haya llegado al gold publicado. Una cadena que captura y no aparece
        #    en gold es una cadena que no se puede comparar, aunque su dia sea perfecto.
        if gold is not None:
            if gold_de_la_cadena is None:
                mal("cadena_sin_gold", FALLO,
                    "no tiene ni una fecha en gold/precio_diario.parquet")
            elif gold_max is not None and gold_de_la_cadena < gold_max:
                mal("cadena_gold_atrasada", AVISO,
                    f"su ultimo precio en gold es del {gold_de_la_cadena} y el de la version "
                    f"publicada del {gold_max}")

        if any(m["gravedad"] == FALLO for m in motivos):
            estado = FALLO
        elif motivos:
            estado = AVISO
        else:
            estado = "ok"

        cadenas.append({
            "fuente": fuente,
            "estado": estado,
            "pasada": None if pasada is None else {
                "ts": pasada["ts"],
                "hora_local": pasada["cuando"].astimezone(zona).strftime("%H:%M"),
                "filas": pasada["filas"], "errores": pasada["errores"], "ok": pasada["ok"],
            },
            "bronce": None if captura is None else dict(captura),
            "referencia": referencia,
            "gold": gold_de_la_cadena,
            "motivos": [m["codigo"] for m in motivos],
        })

    # --- lo del dia entero, que no es de ninguna cadena -----------------------

    if gold is None:
        apunta("sin_gold", FALLO,
               "no existe (o no se puede leer) data/gold/precio_diario.parquet: no hay nada "
               "publicado que mirar")
    elif not gold:
        apunta("sin_gold", FALLO,
               "data/gold/precio_diario.parquet no tiene ni una fila: no hay nada publicado")
    elif gold_max is None or gold_max < iso:
        if en_curso:
            apunta("gold_pendiente", AVISO,
                   f"gold sigue en el {gold_max}: la pasada del {iso} aun no ha publicado")
        else:
            apunta("gold_atrasado", FALLO,
                   f"gold sigue en el {gold_max} y la pasada de hoy ya cerro: no se ha publicado "
                   f"el dia")

    if actual is None:
        apunta("sin_version", AVISO,
               "no se puede leer data/gold/actual.json: no se sabe que version esta publicada")

    faltan = [fuente for fuente in ORDEN if fuente not in declaradas]
    if faltan:
        apunta("cobertura_sin_declarar", AVISO,
               f"falta la cobertura declarada del {iso} de {len(faltan)} cadena(s): "
               f"{', '.join(faltan)}"
               + (" (se declara al cerrar la pasada)" if en_curso else ""))

    ultima = _texto(datos / "ultima_ejecucion.txt")
    if not ultima:
        apunta("sin_dia_cerrado", AVISO,
               "no hay data/ultima_ejecucion.txt: no consta ningun dia que llegara a cerrarse")
    else:
        try:
            fecha_ultima = dt.date.fromisoformat(ultima[:10])
        except ValueError:
            fecha_ultima = None
            apunta("marca_ilegible", AVISO,
                   f"data/ultima_ejecucion.txt dice '{ultima[:40]}', que no es una fecha")
        if fecha_ultima is not None and fecha_ultima < dia - dt.timedelta(days=1):
            apunta("cadena_parada", AVISO,
                   f"la ultima pasada que llego a cerrarse es del {fecha_ultima}: "
                   f"{(dia - fecha_ultima).days} dias sin cerrar un dia entero")

    if marca is not None and marca["a_medias"]:
        apunta("pasada_a_medias", AVISO,
               f"la pasada que empezo el {marca['texto']} no llego a terminar: run.py lo dice "
               f"solo en el log de la siguiente")

    nota = _json(datos / "avisos.json")
    if nota is None:
        apunta("avisos_sin_mirar", AVISO,
               "no hay nota de avisos (data/avisos.json): los avisos de la cadena no se miraron")
    elif nota.get("error"):
        apunta("avisos_sin_mirar", AVISO,
               f"los avisos de la cadena no se pudieron mirar: {nota['error']}")
    else:
        cuando_nota = str(nota.get("cuando", ""))[:10]
        if cuando_nota and cuando_nota < iso:
            apunta("avisos_de_ayer", AVISO,
                   f"los avisos de la cadena son del {cuando_nota}: los del {iso} no se han "
                   f"mirado"
                   + (" (se miran al cerrar la pasada)" if en_curso else ""))

    metricas = _json(datos.parent / "metricas-cesta.json")
    if metricas is not None:
        fecha_metricas = str(metricas.get("fecha_datos", ""))[:10]
        if fecha_metricas and fecha_metricas < (dia - dt.timedelta(days=1)).isoformat():
            apunta("metricas_atrasadas", AVISO,
                   f"metricas-cesta.json es del {fecha_metricas}: el panel no se ha reescrito")

    if any(a["gravedad"] == FALLO for a in avisos):
        estado = FALLO
    elif avisos:
        estado = AVISO
    else:
        estado = "ok"

    return {
        "fecha": iso,
        "estado": estado,
        "generado": ahora.astimezone(zona).isoformat(timespec="seconds"),
        "en_curso": en_curso,
        "cadenas": cadenas,
        "avisos": avisos,
        "gold": {"fecha_max": gold_max,
                 "version": None if actual is None else actual.get("version"),
                 "publicado_en": None if actual is None else actual.get("publicado_en")},
        "cobertura": {"declaradas": declaradas, "faltan": faltan},
    }


# ----------------------------------------------------------------------------- contar ---


def _cifra(n: int | None) -> str:
    """Miles con punto, como el resto de los informes del proyecto (52.701, no 52701)."""
    return "--" if n is None else f"{n:,}".replace(",", ".")


def _estado_en_llano(informe: dict) -> str:
    return f"{informe['estado'].upper()}"


def informe_en_llano(informe: dict) -> list[str]:
    """El informe de pantalla: **✓ o ✗ por cadena y el motivo debajo**. Sin adornos.

    La marca de la cadena es ✓ cuando no hay nada que decir y ✗ cuando hay algo, y cada motivo
    lleva su gravedad escrita (`aviso` o `fallo`) para no tener que adivinarla por el simbolo.
    """
    lineas: list[str] = []
    lineas.append(f"vigilante de la ingesta - {informe['fecha']} "
                  f"({informe['generado'][11:16]}, Europe/Madrid)")
    if informe["en_curso"]:
        lineas.append(f"  la pasada del {informe['fecha']} esta en marcha: lo que aun no ha "
                      'llegado se lee como "en curso", no como "no vino"')
    lineas.append("")
    cabecera = (f"  {'':<1} {'CADENA':<11}{'PASA':>6}{'FILAS':>9}{'BRONCE':>9}   "
                f"{'REFERENCIA':<16}GOLD")
    lineas.append(cabecera)
    for ficha in informe["cadenas"]:
        marca = "✓" if ficha["estado"] == "ok" else "✗"
        pasada = ficha["pasada"]
        hora = pasada["hora_local"] if pasada else "--"
        filas = _cifra(pasada["filas"]) if pasada else "--"
        captura = ficha["bronce"]
        bronce = _cifra(captura["filas"]) if captura else "--"
        referencia = ficha["referencia"]
        if ficha["pasada"] is None and informe["en_curso"]:
            ref = "en curso"
        elif referencia is None:
            ref = "alcance parcial"
        elif referencia["veredicto"] == "sin datos":
            ref = "sin datos"
        else:
            ref = (f"{_cifra(referencia['referencia'])} ({referencia['pct']} %)"
                   if referencia["referencia"] else "sin referencia")
        gold = ficha["gold"] or "--"
        lineas.append(f"  {marca} {ficha['fuente']:<11}{hora:>6}{filas:>9}{bronce:>9}   "
                      f"{ref:<16}{gold}")
        for aviso in informe["avisos"]:
            if aviso["cadena"] == ficha["fuente"]:
                lineas.append(f"        ✗ [{aviso['codigo']}] {aviso['gravedad']}: "
                              f"{aviso['texto']}")

    lineas.append("")
    lineas.append("  EL DIA")
    del_dia = [a for a in informe["avisos"] if a["cadena"] is None]
    if informe["gold"]["fecha_max"]:
        version = informe["gold"]["version"] or "version desconocida"
        marca = "✓" if informe["gold"]["fecha_max"] >= informe["fecha"] else "✗"
        lineas.append(f"  {marca} gold: precio_diario hasta el {informe['gold']['fecha_max']}, "
                      f"publicada la {version}")
    for aviso in del_dia:
        lineas.append(f"        ✗ [{aviso['codigo']}] {aviso['gravedad']}: {aviso['texto']}")
    if not del_dia and informe["gold"]["fecha_max"]:
        lineas.append("  ✓ nada del dia se queda sin decir")

    avisos = informe["avisos"]
    fallos = sum(1 for a in avisos if a["gravedad"] == FALLO)
    lineas.append("")
    if avisos:
        lineas.append(f"  ESTADO: {_estado_en_llano(informe)} - {len(avisos)} aviso(s), "
                      f"{fallos} fallo(s)")
        if fallos:
            lineas.append("  Un fallo es algo que deberia haber pasado y no paso. Se mira primero "
                          "lo que nombra la cadena y despues data/ejecuciones.log de hoy.")
        else:
            lineas.append("  Todo lo que se esperaba esta, pero algo no cuadra: se lee el motivo "
                          "de cada linea.")
    else:
        lineas.append("  ESTADO: OK - las seis cadenas, el bronce, el gold y la cobertura del dia "
                      "estan donde tienen que estar")
    return lineas


# ---------------------------------------------------------------------------- escribir ---


def escribe(datos: Path, informe: dict) -> Path | None:
    """Deja `data/avisos_ingesta.json` (temporal y renombrado atomico), o `None` si no puede.

    Un fichero a medias se leeria como un informe valido, y este fichero lo va a leer gente y
    ganchos: se escribe entero o no se escribe. Un fallo al escribir **no se calla**: quien
    llama lo convierte en aviso.
    """
    ruta = datos / FICHERO
    temporal = ruta.with_suffix(".json.tmp")
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporal, ruta)
    except OSError as exc:
        # Por **stderr**, no por stdout: con `--json` la salida es el propio JSON y una linea
        # suelta delante la dejaria ilegible justo cuando algo va mal.
        print(f"[vigilante] no he podido dejar el informe en {ruta}: {exc}", file=sys.stderr)
        with suppress(OSError):
            temporal.unlink(missing_ok=True)
        return None
    return ruta


def _utf8() -> None:
    """Que ✓ y ✗ salgan bien en una consola de Windows sin UTF-8 configurado."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigure = getattr(flujo, "reconfigure", None)
        if reconfigure is None:
            continue
        with suppress(ValueError, OSError):
            reconfigure(encoding="utf-8", errors="replace")


def _di(texto: str = "") -> None:
    try:
        print(texto)
    except UnicodeEncodeError:
        print(texto.encode("ascii", "replace").decode("ascii"))


def main(argv: list[str] | None = None) -> int:
    """`argv` explicito para poder colgarlo de la cadena diaria sin leer `sys.argv`.

    Mismo motivo que en `cobertura_diaria.main`: un argumento que `argparse` no conozca lanza
    `SystemExit`, que no es una `Exception` y se llevaria por delante la pasada entera.
    """
    ap = argparse.ArgumentParser(description="Dice si la ingesta diaria sigue sola y sin fallos.")
    ap.add_argument("--datos", help="carpeta de datos a mirar (por defecto, data/)")
    ap.add_argument("--fecha", help="dia a mirar, AAAA-MM-DD (por defecto, hoy en Madrid)")
    ap.add_argument("--json", action="store_true", help="sacar el informe en JSON por stdout")
    a = ap.parse_args(argv)

    try:
        dia = _dia(a.fecha)
    except ValueError:
        ap.error(f"--fecha no es una fecha: {a.fecha!r}")

    datos = Path(a.datos) if a.datos else config.DATA
    _utf8()
    informe = vigila(datos=datos, fecha=dia)

    # El fichero se escribe **antes** de decidir el codigo: si no se puede dejar, eso es un
    # aviso mas y el dia no puede salir 0 con el informe sin escribir.
    ruta = escribe(datos, informe)
    if ruta is None:
        informe["avisos"].append({
            "codigo": "informe_sin_escribir", "gravedad": AVISO, "cadena": None,
            "texto": f"no se ha podido dejar {FICHERO} en {datos}: el informe solo esta en "
                     f"pantalla"})
        if informe["estado"] == "ok":
            informe["estado"] = AVISO

    if a.json:
        _di(json.dumps(informe, ensure_ascii=False, indent=1))
    else:
        for linea in informe_en_llano(informe):
            _di(linea)
        if ruta is not None:
            _di("")
            _di(f"  informe dejado en {ruta}")
    return 0 if informe["estado"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
