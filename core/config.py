"""Ajustes del proyecto. Todo lo que cambia sin tocar codigo vive aqui."""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("SCRAP_DATA", RAIZ / "data"))

RAW = DATA / "raw"
BRONZE = DATA / "bronze"
SILVER = DATA / "silver"
GOLD = DATA / "gold"
EXTERNO = DATA / "externo"
DEBUG = DATA / "debug"
WAREHOUSE = DATA / "warehouse.duckdb"
ZONA_HORARIA = ZoneInfo(os.environ.get("SCRAP_TZ", "Europe/Madrid"))

for d in (RAW, BRONZE, SILVER, GOLD, EXTERNO, DEBUG):
    d.mkdir(parents=True, exist_ok=True)

# tu zona: fija el almacen de Mercadona y el ambito de Aldi
CODIGO_POSTAL = os.environ.get("SCRAP_CP", "28001")
ALDI_SCOPE = os.environ.get("SCRAP_ALDI_SCOPE", "es_pen")   # es_pen | es_bal | es_can
MERCADONA_DETALLES_POR_DIA = int(os.environ.get("SCRAP_MERCADONA_DETALLES", "100"))
# Cuantas fichas de producto de DIA se piden como minimo cada dia, y el tope
# duro. La ficha es de donde salen el EAN, los ingredientes, los alergenos, la
# tabla nutricional y la caducidad: un producto sin ficha esta en el catalogo
# pero medio ciego.
#
# Era un 100 fijo, y eso hace que el sistema se quede atras para siempre en
# cuanto la cadena crece mas rapido: el 18 de septiembre de 2026 DIA aparecio con
# 459 productos nuevos, se pidieron 100 fichas y quedaron 374 pendientes. Al dia
# siguiente habria vuelto a haber nuevos, y la cola nunca baja.
#
# Ahora se pide lo que falte, con un tope. A una peticion por segundo, 400 fichas
# son menos de siete minutos de mas en una tarea que ya dura trece: en una
# ejecucion nocturna eso no le importa a nadie, y a cambio el catalogo no
# arrastra una deuda que crece sola.
DIA_DETALLES_POR_DIA = int(os.environ.get("SCRAP_DIA_DETALLES", "100"))
DIA_DETALLES_TOPE = int(os.environ.get("SCRAP_DIA_DETALLES_TOPE", "400"))

# Cuantos dias de crudo se conservan. Medido el 7 sep: una pasada completa deja
# 338 MB de crudo, casi todo de Carrefour (252 MB de HTML). A ese ritmo son 123 GB
# al ano, y el disco tiene 158 GB libres: sin limpiar, en poco mas de un ano las
# ejecuciones empiezan a fallar por falta de sitio, de madrugada y sin nadie
# mirando. El crudo es una cache para reanudar el dia y para reprocesar si cambia
# un parser; bronze guarda lo mismo ya tipado y ocupa mil veces menos. Treinta
# dias cubren de sobra los dos usos. A 0 se desactiva la limpieza.
DIAS_RAW = int(os.environ.get("SCRAP_DIAS_RAW", "30"))

# ritmo por cadena, en peticiones por segundo
RITMO = {
    "mercadona": 2.0,
    "aldi": 2.0,
    # AWS WAF: una cada 4 s evitaba el corte que se veia a 1/s, pero el 8 sep el
    # reto escalo a pedir un clic humano tras siete cortes. Menos presion es la
    # unica palanca que queda del lado del codigo: a una cada 6,7 s el recorrido
    # entero pasa de unos 27 a unos 45 minutos de trabajo real, que en una tarea
    # nocturna no le importa a nadie.
    "alcampo": 0.15,
    "dia": 1.0,          # Akamai: sin prisa
    "carrefour": 1.0,    # el Crawl-delay 60 de robots.txt solo es para TwengaBot,
    # **Lidl estaba sin declarar.** `ficha_lidl.descarga` usaba `RITMO.get("lidl", 1.0)`,
    # asi que su ritmo era un valor por defecto que nadie habia elegido ni podia revisar.
    # Declarado con el mismo 1.0 que se estaba aplicando: **no cambia lo que pasa, cambia
    # que se pueda ver y discutir.**
    "lidl": 1.0,
}

# Alcampo protege su catalogo con AWS WAF: sin la cookie aws-waf-token las paginas
# llegan con un reto de JavaScript en vez de datos. Ver core/waf.py.
# Se excluyen por el primer tramo de su ruta, sin tildes y en minusculas.
# Alcampo es un hipermercado y publica online toda su tienda. Medido el 8 sep:
# de sus 37.019 productos, solo el 33 % era comida, y su rama mas grande no era
# "Alimentacion" sino "Hogar y Decoracion". Ese bazar costaba la mayor parte de
# los 45 minutos del recorrido y solo uno de cada cinco productos de Alcampo
# encontraba con quien compararse, porque las demas cadenas no venden cortinas.
#
# El criterio para quedarse es "se consume y se repone": comida, bebida, higiene,
# limpieza, parafarmacia, bebe y mascotas. Se va lo que se compra una vez y dura
# anos. Asi el surtido de Alcampo queda comparable con el de Carrefour, del que
# ya solo recorremos /supermercado/.
#
# Se comparan por el primer tramo de la ruta, sin tildes y en minusculas.
RAMAS_EXCLUIDAS_ALCAMPO: set[str] = {
    "hogar y decoracion",      # 4.146 productos
    "papeleria",               # 1.587
    "tecnologia",              # 1.323
    "bricolaje",               # 1.108
    "electrodomesticos",       #   890
    "juguetes",                #   649
    "libros",                  #   599
    "jardin y terraza",        #   540
    "textil",                  #   523
    "automovil",               #   486
    "deportes y maletas",      #   164
}

# *Aqui vivia `RETENCION_RAW_DIAS = 0`, con el comentario «0 = para siempre», y **no la leia
# nadie**: la poda usa `DIAS_RAW`, mas arriba. Quien abriera este fichero para saber cuanto crudo se
# guarda leia «para siempre» y se lo creia, con `limpiar.py` tirando a los 30 dias.* Una constante
# muerta que se lee como politica es peor que no tenerla.


def ahora_local() -> datetime:
    """Hora operativa del proyecto, independiente de la zona del proceso."""
    return datetime.now(ZONA_HORARIA)


def hoy_local() -> date:
    return ahora_local().date()
