"""La extensión tiene que reconocer las URL que de verdad guardamos.

La extensión saca el identificador del producto **de la URL** de la tienda, y no
del DOM: un selector CSS ajeno se rompe cada dos semanas y ataría la extensión a
cómo pinta su página el supermercado. La URL es el único contrato estable que
tienen.

Eso deja un riesgo: que el patrón deje de casar y la extensión se quede muda sin
que nadie se entere. Aquí se comprueba contra las URL reales del último bronze,
que es la única forma de que un cambio de formato en una cadena salga a la luz
el día que pasa y no el día que alguien lo prueba a mano.

El 21 de septiembre de 2026 esta prueba habría cazado en el acto lo de Alcampo:
guardábamos el `productId` (un UUID) donde la URL pública lleva el
`retailerProductId`, y el patrón de la extensión pide dígitos.
"""
import re
from pathlib import Path

import polars as pl
import pytest

from core import config

FUENTE = Path(__file__).resolve().parents[1] / "extension" / "contenido.js"

# Los patrones tal y como están escritos en contenido.js. Se leen del fichero en
# vez de copiarlos: una regla escrita en dos sitios acaba siendo dos reglas.
_LINEA = re.compile(r"\{cadena:\s*'(\w+)',\s*patron:\s*/(.+?)/\}")


def patrones() -> dict[str, re.Pattern]:
    texto = FUENTE.read_text(encoding="utf-8")
    fuera = {}
    for cadena, patron in _LINEA.findall(texto):
        # JS y Python escriben estas expresiones igual; sólo cambia el envoltorio.
        fuera[cadena] = re.compile(patron)
    return fuera


def test_hay_un_patron_por_cadena():
    assert set(patrones()) == {"carrefour", "dia", "aldi", "mercadona", "alcampo"}


@pytest.mark.parametrize(("cadena", "url", "espera"), [
    ("carrefour",
     "https://www.carrefour.es/supermercado/bitter-carrefour-sensation/R-521028123/p",
     "521028123"),
    ("dia", "https://www.dia.es/aceites-salsas-y-especias/ketchup/p/49608", "49608"),
    ("aldi", "https://www.aldi.es/p/champu-reparador-279705", "279705"),
    ("mercadona",
     "https://tienda.mercadona.es/product/13294/gel-bano-granada", "13294"),
    ("alcampo", "https://www.compraonline.alcampo.es/products/181786", "181786"),
])
def test_saca_el_identificador_de_una_url_de_verdad(cadena, url, espera):
    m = patrones()[cadena].search(url)
    assert m and m.group(1) == espera


def test_la_url_vieja_de_alcampo_no_cuela():
    """La que dio 404 durante quince días: un UUID donde va el número.

    Si alguien vuelve a poner el `productId` en la columna `url`, el patrón no
    casa y la prueba de abajo se pone roja. Esa es toda la gracia.
    """
    uuid = "https://www.compraonline.alcampo.es/products/72bccb32-c2f9-4735-90c7-501a89eaed7a"
    assert patrones()["alcampo"].search(uuid) is None


# El día en que se arregló la URL de una cadena. El bronze anterior a esa fecha
# la lleva mal **a sabiendas**, así que comprobarlo no dice nada nuevo: sólo
# repetiría un fallo ya arreglado hasta que pase la siguiente captura.
#
# Se declara con su fecha en vez de callar la cadena entera: así la prueba
# vuelve sola en cuanto hay datos nuevos, y no hay que acordarse de quitar nada.
ARREGLADAS = {
    # Guardábamos el `productId` (un UUID) donde la URL pública lleva el
    # `retailerProductId`. Los 23.776 enlaces daban 404.
    "alcampo": "2026-09-22",
}


def _ultimo_bronze(fuente: str) -> tuple[pl.DataFrame, str] | None:
    carpeta = config.DATA / "bronze" / f"fuente={fuente}"
    dias = sorted(carpeta.glob("fecha=*")) if carpeta.exists() else []
    if not dias:
        return None
    dia = dias[-1].name.split("=", 1)[1]
    return pl.read_parquet(dias[-1] / "part.parquet", columns=["url"]), dia


@pytest.mark.parametrize("cadena",
                         ["carrefour", "dia", "aldi", "mercadona", "alcampo"])
def test_el_patron_casa_con_las_urls_que_guardamos_hoy(cadena):
    """Contra el bronze de verdad. Si no hay bronze, no se inventa un veredicto."""
    hay = _ultimo_bronze(cadena)
    if hay is None or not hay[0].height:
        pytest.skip(f"no hay bronze de {cadena} en esta maquina")
    df, dia = hay
    desde = ARREGLADAS.get(cadena)
    if desde and dia < desde:
        pytest.skip(f"el bronze de {cadena} es del {dia}, anterior al arreglo "
                    f"de su URL ({desde}); se comprueba con la siguiente captura")
    patron = patrones()[cadena]
    urls = [u for u in df["url"].to_list() if u]
    if not urls:
        pytest.skip(f"el bronze de {cadena} no trae URL")
    fallan = [u for u in urls[:400] if not patron.search(u)]
    assert not fallan, (
        f"{len(fallan)} de {min(len(urls), 400)} URL de {cadena} no las reconoce "
        f"la extension. La primera: {fallan[0]}")
