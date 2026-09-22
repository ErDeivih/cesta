"""¿El precio que publicamos es el que pone la web? Se comprueba, no se supone.

Por que existe
--------------
Todos los controles de este proyecto miran **hacia dentro**: que el bronze tenga
filas, que no falte una rama, que el precio por unidad cuadre con el de la
cadena, que las cifras de los documentos sigan siendo ciertas. Ninguno sale a la
calle a mirar si lo que guardamos es lo que la tienda pone en pantalla.

Y eso es justo lo unico que le da credibilidad al sistema entero. Un catalogo
internamente coherente con un error de lectura sistematico es un catalogo
coherentemente equivocado, y no hay control interno que lo vea.

El 21 de septiembre de 2026 se hizo a mano, abriendo cinco productos al azar en
un navegador. Los cinco precios coincidian **y los cinco precios por unidad
tambien**. Pero dos de los enlaces de Alcampo daban 404: la URL publica lleva el
`retailerProductId` y nosotros guardabamos el `productId`, un UUID interno. Los
23.776 enlaces de Alcampo estaban rotos y llevaban quince dias asi, porque el
precio estaba bien y un enlace roto solo se nota cuando una persona lo pulsa.

Esa comprobacion no puede depender de que alguien se acuerde de hacerla.

Por que NO reutiliza el lector del colector
-------------------------------------------
Seria comodo volver a llamar al parser de cada cadena, y no valdria para nada:
el mismo codigo sobre la misma fuente siempre esta de acuerdo consigo mismo. Un
control que no puede discrepar no es un control.

Asi que aqui el precio se lee **como lo lee una persona**: se baja la pagina del
producto y se busca la cifra con simbolo de euro en el texto, con los patrones
de `sondear_cadena` (que ya saben de espacios duros, `&euro;` y `&#8364;`). La
pregunta es la que haria cualquiera: *¿aparece nuestro precio en su pagina?*

Que puede contestar cada producto
---------------------------------
    coincide      nuestro precio esta en su pagina
    no aparece    la pagina carga y nuestro precio no esta en ella
    404           el enlace que publicamos no lleva a ninguna parte
    sin precio    la pagina no ensena ningun precio (login, agotado, region)
    no se pudo    la peticion fallo; no dice nada del dato, solo de la red

**No hay umbral de aprobado.** Cada producto cuyo precio no cuadre con el de su
pagina (`no aparece`, `404`) sale con su nombre, su URL y las dos cifras, para
que se pueda mirar uno por uno, y el codigo de salida es cuantos son. Un
porcentaje "aceptable" de precios mal es exactamente lo que no queremos poder
decir.

Los otros dos estados **no cuentan como fallo y no salen uno a uno**, porque no
dicen nada del dato: `sin precio` (la pagina no ensena ninguno: agotado, login,
otra region) y `no se pudo` (la peticion fallo: eso es la red). Salen en el
recuento de su cadena, y los de red en una sola linea. Si contaran, un dia de
red mala daria el mismo aviso que un dia de precios malos, y el aviso dejaria de
significar nada.

    uv run python -m projects.cesta.verificar_precios --por-cadena 8
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass

import polars as pl

from core import config
from core.fetch import Fetcher, HTTPStatusError
from projects.cesta.sondear_cadena import PRECIO

# Mercadona no ensena precios en el HTML: su tienda es una aplicacion que los
# pide aparte, y la pagina desnuda no trae ninguna cifra. Su ficha publica en
# JSON si, y es la misma que ve el navegador.
API_PRODUCTO = {
    "mercadona": "https://tienda.mercadona.es/api/products/{id}/",
}


@dataclass
class Veredicto:
    fuente: str
    id_fuente: str
    nombre: str
    url: str
    nuestro_cent: int
    estado: str                    # coincide | no aparece | 404 | sin precio | no se pudo
    visto: list[int]               # los precios que se leyeron en su pagina
    detalle: str = ""

    @property
    def bien(self) -> bool:
        return self.estado == "coincide"


def precios_en(cuerpo: bytes) -> list[int]:
    """Todas las cifras con simbolo de euro de la pagina, en centimos."""
    vistos = []
    for m in PRECIO.finditer(cuerpo):
        try:
            vistos.append(round(float(m.group(1).decode().replace(",", ".")) * 100))
        except ValueError:
            continue
    return vistos


def _precio_de_json(cuerpo: bytes) -> list[int]:
    """Los `unit_price` de una ficha en JSON, sin importar como venga anidada."""
    import json
    import re
    try:
        json.loads(cuerpo)
    except ValueError:
        return []
    fuera = []
    for m in re.finditer(rb'"unit_price"\s*:\s*"?(\d+[.,]\d{2})"?', cuerpo):
        fuera.append(round(float(m.group(1).decode().replace(",", ".")) * 100))
    return fuera


def url_de(fila: dict) -> str:
    """La direccion que se va a pedir para este producto.

    Nada de `.format` sobre la URL guardada: una URL con una llave dentro
    (`{` o `}`, que las hay en parametros de campana) reventaria el formateo y
    tiraria la comprobacion entera por un caracter.
    """
    plantilla = API_PRODUCTO.get(fila["fuente"])
    if plantilla:
        return plantilla.format(id=str(fila["id_fuente"]))
    return fila["url"]


def comprueba(fila: dict, f: Fetcher) -> Veredicto:
    fuente, id_fuente = fila["fuente"], str(fila["id_fuente"])
    url = url_de(fila)
    v = Veredicto(fuente, id_fuente, fila["nombre"] or "", url,
                  int(fila["precio_cent"]), "no se pudo", [])
    try:
        r = f.get(url, retries=2)
    except HTTPStatusError as exc:
        v.estado = "404" if exc.status == 404 else "no se pudo"
        v.detalle = f"HTTP {exc.status}"
        return v
    except Exception as exc:  # noqa: BLE001
        v.detalle = str(exc)[:80]
        return v

    v.visto = _precio_de_json(r.body) or precios_en(r.body)
    if not v.visto:
        v.estado = "sin precio"
    elif v.nuestro_cent in v.visto:
        v.estado = "coincide"
    else:
        v.estado = "no aparece"
    return v


def muestra(dia: str | None = None, por_cadena: int = 8,
            semilla: int | None = None) -> list[dict]:
    """Productos al azar del ultimo bronze de cada cadena.

    Al azar **de verdad**: elegir los raros encontraria mas fallos y no diria
    nada del catalogo, que es lo que se quiere saber.
    """
    azar = random.Random(semilla)
    raiz = config.DATA / "bronze"
    filas: list[dict] = []
    for carpeta in sorted(raiz.glob("fuente=*")):
        dias = sorted(carpeta.glob("fecha=*"))
        if dia:
            dias = [d for d in dias if d.name.endswith(dia)]
        if not dias:
            continue
        df = pl.read_parquet(dias[-1] / "part.parquet",
                             columns=["fuente", "id_fuente", "nombre",
                                      "precio_cent", "url"])
        df = df.filter(pl.col("precio_cent").is_not_null()
                       & (pl.col("precio_cent") > 0)
                       & pl.col("url").is_not_null())
        if not df.height:
            continue
        indices = azar.sample(range(df.height), min(por_cadena, df.height))
        filas.extend(df.row(i, named=True) for i in indices)
    return filas


def informe(veredictos: list[Veredicto]) -> int:
    """Lo imprime y devuelve cuantos NO coinciden."""
    por_cadena: dict[str, list[Veredicto]] = {}
    for v in veredictos:
        por_cadena.setdefault(v.fuente, []).append(v)

    print("  precio publicado contra precio guardado:")
    for fuente, vs in sorted(por_cadena.items()):
        bien = sum(v.bien for v in vs)
        resto = [f"{sum(1 for v in vs if v.estado == e)} {e}"
                 for e in ("no aparece", "404", "sin precio", "no se pudo")
                 if any(v.estado == e for v in vs)]
        cola = f"  ({', '.join(resto)})" if resto else ""
        print(f"    {fuente:<10} {bien}/{len(vs)} coinciden{cola}")

    # No todo lo que no coincide acusa al dato, y mezclarlo es lo que entierra el
    # aviso de verdad. Una peticion que fallo habla de la red; una pagina sin
    # precio (agotado, login, otra region) habla de la pagina. Quince productos
    # diciendo "no hubo red" tapan el dia siguiente, que si tiene algo que
    # contar. Asi que solo `no aparece` y `404` cuentan como fallo y salen uno a
    # uno: son los dos unicos estados en los que el numero guardado y el
    # publicado no cuadran.
    #
    # El recuento de los demas no se pierde: sale en la linea de cada cadena.
    malos = [v for v in veredictos if v.estado in ("no aparece", "404")]
    sin_red = [v for v in veredictos if v.estado == "no se pudo"]
    if sin_red:
        print(f"  {len(sin_red)} sin comprobar: es la conexion, no el dato.")
    if malos:
        print("  los que no coinciden, uno por uno:")
        for v in malos:
            visto = (", ".join(f"{c / 100:.2f}" for c in sorted(set(v.visto))[:6])
                     or v.detalle or "nada")
            print(f"    [{v.estado}] {v.fuente} {v.id_fuente} "
                  f"{v.nombre[:44]}: nuestro {v.nuestro_cent / 100:.2f} EUR, "
                  f"en su pagina {visto}")
            print(f"        {v.url}")
    return len(malos)


# Esto corre al final de la ejecucion diaria, detras de tres horas de scraping.
# Si se colgara, se colgaria **despues** de que el dato ya este guardado, pero
# dejaria la tarea abierta y el aviso de "no termino" saltaria manana sin que
# hubiera pasado nada. Con un presupuesto de tiempo, lo peor que puede pasar es
# que compruebe menos productos y lo diga.
PRESUPUESTO_S = 240


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--por-cadena", type=int, default=8,
                    help="cuantos productos mirar de cada cadena (8 por defecto)")
    ap.add_argument("--dia", help="fecha del bronze (por defecto, el ultimo)")
    ap.add_argument("--semilla", type=int, help="para repetir la misma muestra")
    ap.add_argument("--presupuesto", type=int, default=PRESUPUESTO_S,
                    help="segundos como mucho (240 por defecto)")
    a = ap.parse_args(argv)

    filas = muestra(a.dia, a.por_cadena, a.semilla)
    if not filas:
        print("  precios: no hay bronze con precios y URL; no se comprueba nada")
        return 0

    t0 = time.monotonic()
    veredictos = []
    for fila in filas:
        if time.monotonic() - t0 > a.presupuesto:
            print(f"  precios: se acabo el tiempo ({a.presupuesto}s); "
                  f"comprobados {len(veredictos)} de {len(filas)}")
            break
        # Un fetcher por producto y despacio: son ocho peticiones por cadena al
        # dia, y no hay ninguna prisa en una comprobacion.
        f = Fetcher(rate_per_sec=0.5)
        veredictos.append(comprueba(fila, f))
    if not veredictos:
        return 0
    return informe(veredictos)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
