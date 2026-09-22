"""Audita el mapa de secciones: ¿hay productos en el pasillo equivocado?

Por que existe
--------------
`core/datos/secciones.yml` se genero automaticamente por palabras clave, y el
generador buscaba las palabras **sin limites de palabra y sin acentos**. Eso
deja errores que nadie ve, porque una seccion mal puesta no da ningun error:
sale una pantalla bonita con el producto en el pasillo de al lado.

Medido el 20 de septiembre de 2026, con el mapa tal y como estaba:

    "Bebé > Pañales y toallitas"          -> panaderia    (panales -> "pan")
    "Campañas > Nuestra seleccion de vinos" -> panaderia  (campanas -> "pan")
    "Congelados > Patatas, croquetas..."  -> frutas-verduras
    "mascotas/perro-snacks-y-cuidado"     -> aperitivos   (snacks del perro)
    "Alimentacion > Aperitivos, aceitunas y frutos secos" -> despensa

El ultimo dejaba a Alcampo con **cero productos en la seccion aperitivos**,
teniendo 658. Entre todas, 1.070 productos en el pasillo equivocado, y ademas
`desayuno-dulces` hacia de cajon de sastre: 254 utensilios de limpieza, 172
desodorantes y 120 protectores solares vivian ahi.

Que comprueba
-------------
Dos cosas objetivas, sin opinar sobre el producto:

1. **La rama manda.** Si la clave empieza por una rama que nombra una seccion
   sin ambiguedad (`Congelados > ...`, `mascotas/...`, `drogueria-y-limpieza/...`),
   la seccion tiene que ser esa. Las excepciones se declaran aqui y se ven.

2. **Una seccion vacia en una cadena que si la tiene.** Si cuatro cadenas
   tienen aperitivos y una tiene cero, o falta la rama o esta mal mapeada.

Lo que NO comprueba: si "pescado congelado" debe ir a `congelados` o a
`pescaderia`. Eso es una decision de producto, no un fallo, y esta escrita en
docs/SECCIONES.md. Lo unico que importa es que **todas las cadenas hagan lo
mismo**, y de eso se encarga `convenios_incoherentes`.

    uv run python -m projects.cesta.auditar_secciones
"""
from __future__ import annotations

import argparse
import collections
import re
import unicodedata
from datetime import date
from pathlib import Path

import polars as pl

from core import config
from core.secciones import FICHERO, ORDEN, _mapa, clave_de, seccion_de

# La rama de la que cuelga la clave y la seccion que implica sin discusion.
RAMAS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^congelados(\b|-y-helados\b)"), "congelados"),
    (re.compile(r"^mascotas\b"), "mascotas"),
    (re.compile(r"^drogueria(\b|-y-limpieza\b)|^limpieza-y-hogar\b"), "droguería-limpieza"),
    (re.compile(r"^perfumeria\b|^higiene-y-cuidado"), "higiene-belleza"),
)

# Excepciones declaradas: comida de verdad colgando de una rama que no es de
# comida. Se escriben aqui para que se vean, no para que desaparezcan.
EXCEPCIONES = re.compile(
    r"alimentacion|conservacion-de-alimentos|Conservación de Alimentos", re.I)

# El convenio del congelado: un congelado va al pasillo de su producto fresco,
# no al de "congelados". El pescado congelado con el pescado, la verdura
# congelada con la verdura. Asi el precio del salmon se compara con el del
# salmon, que es para lo que existe todo esto.
#
# **No es un fallo, es una decision de producto**, y por eso sale en su propio
# apartado. Lo unico que si es un fallo es aplicarlo a medias: si una cadena
# manda su marisco congelado a `pescaderia` y otra a `congelados`, los dos
# precios dejan de encontrarse. La auditoria mira eso.
CONGELADO = re.compile(r"^congelados(\b|-y-helados\b)")
ESPEJO: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"pescad|marisc|surimi"), "pescaderia"),
    (re.compile(r"verdura|hortaliza"), "frutas-verduras"),
    (re.compile(r"\bcarne|pollo|jacobo|nugget|empanado"), "carniceria"),
    (re.compile(r"pizza|masa|churro|reposteria|panaderia"), "panaderia"),
    (re.compile(r"arroz|arroces|pasta"), "despensa"),
)


def _pela(texto: str) -> str:
    """Sin acentos y en minusculas, que es como compara el generador."""
    plano = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in plano if not unicodedata.combining(c)).lower()


def _raiz(clave: str) -> str:
    return _pela(clave.split(">")[0].split("/")[0].strip())


# Claves que mezclan cosas de varios pasillos y se quedan en `congelados` a
# proposito: no hay un fresco al que reflejarlas. Declararlas aqui es lo
# honesto; forzarlas a un pasillo seria elegir por sorteo.
MIXTAS = frozenset({
    ("alcampo", "Congelados > Repostería, hielo y bolsas isotérmicas"),
    ("alcampo", "Congelados > Tartas, postres y fruta congelada"),
})


def _espejo_de(clave: str) -> str | None:
    """A que pasillo fresco le toca a este congelado, si es que le toca alguno."""
    hoja = _pela(clave.split(">")[-1].split("/")[-1])
    for patron, seccion in ESPEJO:
        if patron.search(hoja):
            return seccion
    return None


def contradice_su_rama(mapa: dict[tuple[str, str], str]) -> list[tuple[str, str, str, str]]:
    """(cadena, clave, seccion que dice, seccion que pide su rama).

    Los congelados que siguen el convenio del espejo no salen aqui: para eso
    esta `convenio_del_congelado`.
    """
    fuera = []
    for (fuente, clave), seccion in sorted(mapa.items()):
        if EXCEPCIONES.search(clave) or (fuente, clave) in DISIDENCIA_OK:
            continue
        raiz = _raiz(clave)
        if CONGELADO.search(raiz) and (seccion == _espejo_de(clave)
                                       or (fuente, clave) in MIXTAS):
            continue
        for patron, esperada in RAMAS:
            if patron.search(raiz) and seccion != esperada:
                fuera.append((fuente, clave, seccion, esperada))
            if patron.search(raiz):
                break
    return fuera


def convenio_del_congelado(mapa: dict[tuple[str, str], str]) -> list[tuple[str, str, str, str]]:
    """Los congelados que van al pasillo de su fresco, y si lo hacen todos igual.

    Devuelve (cadena, clave, seccion que dice, seccion del espejo). Cuando las
    dos coinciden, el convenio se esta aplicando; cuando no, hay una cadena
    saliendose y sus precios no se encuentran con los de las demas.
    """
    fuera = []
    for (fuente, clave), seccion in sorted(mapa.items()):
        if not CONGELADO.search(_raiz(clave)) or (fuente, clave) in MIXTAS:
            continue
        espejo = _espejo_de(clave)
        if espejo:
            fuera.append((fuente, clave, seccion, espejo))
    return fuera


# Cadenas que de verdad no tienen esa seccion. Mercadona no vende
# parafarmacia: sus cremas y su pasta de dientes estan en "Cuidado facial y
# corporal", que es higiene-belleza. No es un hueco, es su surtido.
NO_LA_TIENEN = frozenset({
    ("mercadona", "parafarmacia"),
    # Ni Dia ni Mercadona venden bazar por internet.
    ("dia", "hogar"),
    ("mercadona", "hogar"),
    # Aldi y Mercadona no tienen una rama de "ofertas" o "campañas" en su
    # arbol: sus promociones van marcadas sobre el producto, en su pasillo.
    ("aldi", "promociones"),
    ("mercadona", "promociones"),
})


# Disidencias legitimas: la hoja de verdad pertenece a otro pasillo aunque su
# rama diga otra cosa. La conserva de pescado va con el pescado, la bolleria
# con el pan. Declararlas es lo que permite que el resto salte.
DISIDENCIA_OK = frozenset({
    ("alcampo", "Alimentación > Panadería, Harina y Masas"),
    ("alcampo", "Alimentación > Conservas de pescado"),
    ("alcampo", "Alimentación > Aperitivos, aceitunas y frutos secos"),
    ("alcampo", "Campañas > Nuestra selección de vinos"),
    ("alcampo", "Campañas > Chollos en bazar"),
    ("alcampo", "Desayuno y Merienda > Bollería y Pastelería"),
    ("alcampo", "Desayuno y Merienda > Cereales y Barritas"),
    ("alcampo", "Desayuno y Merienda > Azúcar, miel y otros edulcorantes"),
    ("alcampo", "Bebé > Alimentación Infantil"),
    ("alcampo", "Sin Gluten / Sin Lactosa, Nutrición deportiva y Funcional > "
                "Semillas y otros cereales"),
    ("alcampo", "Sin Gluten / Sin Lactosa, Nutrición deportiva y Funcional > "
                "Dietéticos Sin Azúcares añadidos"),
    ("dia", "aperitivos-y-frutos-secos/frutas-deshidratadas"),
    ("dia", "infantil/leches-y-papillas"),
    ("dia", "infantil/yogures-y-postres"),
    ("dia", "platos-preparados-y-pizzas/ensaladas-y-bowls"),
    ("dia", "platos-preparados-y-pizzas/gazpachos-y-salmorejos"),
    ("dia", "platos-preparados-y-pizzas/tortillas-y-empanadas"),
    # Carrefour cuelga la papeleria y el bazar de "drogueria y limpieza". Un
    # boligrafo no es un producto de limpieza: van a `hogar`, y esta declarado
    # porque contradice su rama a proposito.
    ("carrefour", "drogueria-y-limpieza/papeleria"),
    ("carrefour", "drogueria-y-limpieza/papeleria/boligrafos-y-correctores"),
    ("carrefour", "drogueria-y-limpieza/papeleria/marcadores"),
    ("carrefour", "drogueria-y-limpieza/papeleria/folios-y-papeles-especiales"),
    ("carrefour", "drogueria-y-limpieza/bazar/pegamentos-y-siliconas"),
    ("carrefour", "drogueria-y-limpieza/bazar/herramientas"),
})


def _padre_de(clave: str) -> str | None:
    """El nivel inmediatamente por encima de la hoja, si lo hay."""
    for sep in (" > ", "/"):
        if sep in clave:
            return sep.join(clave.split(sep)[:-1])
    return None


def _rama_de(clave: str) -> str | None:
    if ">" in clave:
        return clave.split(">")[0].strip()
    return clave.split("/")[0] if "/" in clave else None


def disidentes_de_su_rama(mapa: dict[tuple[str, str], str], minimo: int = 5,
                          mayoria: float = 0.7) -> list[tuple[str, str, str, str]]:
    """La hoja que se sale de lo que hace el resto de su rama.

    Es la regla que mas fallos encuentra y la que menos opina: no hace falta
    saber que es un "vermouth" para ver que **once hojas de
    `cervezas-vinos-y-licores/` van a bebidas y tres no**.

    Encontro 20 claves de golpe el 20 de septiembre de 2026, entre ellas siete
    de la rama de higiene de Carrefour que vivian en `desayuno-dulces`
    (desodorantes, aftershave, limpiadores de protesis) y los zumos de Alcampo,
    que estaban en `frutas-verduras`.
    """
    ramas: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter)
    hojas: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)
    for (fuente, clave), seccion in mapa.items():
        rama = _rama_de(clave)
        if not rama:
            continue
        ramas[(fuente, rama)][seccion] += 1
        hojas[(fuente, rama)].append((clave, seccion))
    fuera = []
    for k, cuenta in sorted(ramas.items()):
        total = sum(cuenta.values())
        manda, n = cuenta.most_common(1)[0]
        if total < minimo or n / total < mayoria:
            continue
        for clave, seccion in sorted(hojas[k]):
            if seccion != manda and (k[0], clave) not in DISIDENCIA_OK:
                fuera.append((k[0], clave, seccion, manda))
    return fuera


def secciones_vacias(conteo: dict[str, collections.Counter],
                     minimo_ajenas: int = 3) -> list[tuple[str, str]]:
    """Secciones con cero productos en una cadena y con productos en las demas.

    `minimo_ajenas` evita acusar a nadie por una seccion que casi nadie usa:
    `hogar` la tiene una sola cadena, y eso no es un fallo.
    """
    fuera = []
    for seccion in ORDEN:
        con = [f for f, c in conteo.items() if c.get(seccion, 0) > 0]
        if len(con) < minimo_ajenas:
            continue
        for fuente in conteo:
            if (conteo[fuente].get(seccion, 0) == 0
                    and (fuente, seccion) not in NO_LA_TIENEN):
                fuera.append((fuente, seccion))
    return fuera


def sin_mapear(dia: str | None = None) -> list[tuple[str, str, int, str | None]]:
    """Categorias que aparecen en el bronze y no estan en el mapa.

    Devuelve (cadena, clave, cuantos productos, seccion propuesta). La
    propuesta sale de **lo que hace el resto de su rama**, que es la misma regla
    con la que se auditan las que ya estan: si las seis hojas de
    `frescos/charcuteria/` van a carniceria, la septima tambien.

    Hace falta porque las cadenas abren ramas nuevas cada semana y nadie se
    entera: el 21 de septiembre de 2026 Carrefour trajo 24 productos en 16
    categorias que no existian el dia anterior -- sandias y melones, fiambre de
    pavo, bolleria tradicional -- y se quedaron sin pasillo, o sea al final de
    la lista y fuera de la pantalla de secciones.
    """
    mapa = _mapa()
    # El padre **inmediato**, no la rama de primer nivel. En Carrefour `frescos`
    # abarca carniceria, pescaderia y fruteria a la vez, asi que no manda nada;
    # `frescos/charcuteria` si: sus seis hojas van todas a carniceria.
    ramas: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter)
    for (fuente, clave), seccion in mapa.items():
        for nivel in (_padre_de(clave), _rama_de(clave)):
            if nivel:
                ramas[(fuente, nivel)][seccion] += 1

    fuera = []
    for (fuente, clave), n in sorted(_cuantos_por_clave(dia).items(),
                                     key=lambda kv: -kv[1]):
        if (fuente, clave) in mapa:
            continue
        # Lo primero, lo mas fuerte: si el padre **esta mapeado**, la hoja
        # hereda su seccion. `frescos/charcuteria` va a carniceria, asi que
        # `frescos/charcuteria/bacon-y-panceta` tambien. No hace falta preguntar
        # a los hermanos cuando el padre ya ha contestado.
        propuesta = mapa.get((fuente, _padre_de(clave) or ""))
        if propuesta is None:
            cuenta = None
            for nivel in (_padre_de(clave), _rama_de(clave)):
                if nivel and ramas.get((fuente, nivel)):
                    cuenta = ramas[(fuente, nivel)]
                    break
            if cuenta:
                manda, veces = cuenta.most_common(1)[0]
                # Solo se propone cuando la rama es clara. Media rama diciendo
                # una cosa y media otra no es una propuesta, es una moneda al
                # aire, y una seccion puesta a ojo es lo que trajo a los
                # pañales a la panaderia.
                if veces / sum(cuenta.values()) >= 0.7:
                    propuesta = manda
        fuera.append((fuente, clave, n, propuesta))
    return fuera


def _conteo_del_dia(dia: str | None) -> dict[str, collections.Counter]:
    """Cuantos productos cae en cada seccion, por cadena, en el ultimo bronze."""
    raiz = Path(config.DATA) / "bronze"
    conteo: dict[str, collections.Counter] = {}
    for carpeta in sorted(raiz.glob("fuente=*")):
        fuente = carpeta.name.split("=", 1)[1]
        dias = sorted(carpeta.glob("fecha=*"))
        if dia:
            dias = [d for d in dias if d.name.endswith(dia)]
        if not dias:
            continue
        df = pl.read_parquet(dias[-1] / "part.parquet", columns=["categoria"])
        c: collections.Counter = collections.Counter()
        for categoria in df["categoria"].to_list():
            c[seccion_de(fuente, categoria)] += 1
        conteo[fuente] = c
    return conteo


def _cuantos_por_clave(dia: str | None) -> collections.Counter:
    raiz = Path(config.DATA) / "bronze"
    cuenta: collections.Counter = collections.Counter()
    for carpeta in sorted(raiz.glob("fuente=*")):
        fuente = carpeta.name.split("=", 1)[1]
        dias = sorted(carpeta.glob("fecha=*"))
        if dia:
            dias = [d for d in dias if d.name.endswith(dia)]
        if not dias:
            continue
        df = pl.read_parquet(dias[-1] / "part.parquet", columns=["categoria"])
        for categoria in df["categoria"].to_list():
            clave = clave_de(fuente, categoria)
            if clave:
                cuenta[(fuente, clave)] += 1
    return cuenta


def aplica(nuevas: list[tuple[str, str, int, str | None]]) -> int:
    """Escribe las propuestas claras en `secciones.yml`, en su cadena.

    Las que no tienen propuesta no se tocan: una seccion puesta a ojo es
    exactamente lo que trajo a los pañales a la panaderia.
    """
    por_cadena: dict[str, list[tuple[str, str]]] = {}
    for fuente, clave, _n, propuesta in nuevas:
        if propuesta:
            por_cadena.setdefault(fuente, []).append((clave, propuesta))
    if not por_cadena:
        return 0
    lineas = FICHERO.read_text(encoding="utf-8").splitlines()
    salida, fuente_actual, puestas = [], None, 0
    hoy = date.today().isoformat()
    for linea in lineas:
        cabecera = re.fullmatch(r"  (\w+):", linea.split("#")[0].rstrip())
        if cabecera and fuente_actual in por_cadena:
            for clave, seccion in por_cadena.pop(fuente_actual):
                salida.append(f'    "{clave}": {seccion}'.ljust(70) + f" # nueva {hoy}")
                puestas += 1
        if cabecera:
            fuente_actual = cabecera.group(1)
        salida.append(linea)
    for clave, seccion in por_cadena.pop(fuente_actual, []):
        salida.append(f'    "{clave}": {seccion}'.ljust(70) + f" # nueva {hoy}")
        puestas += 1
    FICHERO.write_text("\n".join(salida) + "\n", encoding="utf-8")
    _mapa.cache_clear()
    return puestas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dia", help="fecha del bronze a mirar (por defecto, el ultimo)")
    ap.add_argument("--aplicar", action="store_true",
                    help="escribe en secciones.yml las propuestas claras")
    args = ap.parse_args(argv)

    mapa = _mapa()
    cuenta = _cuantos_por_clave(args.dia)

    malas = contradice_su_rama(mapa)
    print(f"=== claves cuya seccion contradice su propia rama: {len(malas)}")
    total = 0
    for fuente, clave, dice, pide in sorted(
            malas, key=lambda x: -cuenta.get((x[0], x[1]), 0)):
        n = cuenta.get((fuente, clave), 0)
        total += n
        print(f"  {n:>5}  {fuente:<10} {clave[:52]:<52} {dice:>18} -> {pide}")
    print(f"  {total} productos afectados hoy")

    convenio = convenio_del_congelado(mapa)
    rotas = [c for c in convenio if c[2] != c[3]]
    print(f"\n=== convenio del congelado: {len(convenio)} claves, "
          f"{len(convenio) - len(rotas)} lo siguen")
    if rotas:
        print("  las que se salen (sus precios no se encuentran con los demas):")
        for fuente, clave, dice, espejo in rotas:
            n = cuenta.get((fuente, clave), 0)
            print(f"  {n:>5}  {fuente:<10} {clave[:52]:<52} {dice:>18} -> {espejo}")

    disidentes = disidentes_de_su_rama(mapa)
    print(f"\n=== hojas que se salen de lo que hace su rama: {len(disidentes)}")
    for fuente, clave, dice, manda in sorted(
            disidentes, key=lambda x: -cuenta.get((x[0], x[1]), 0)):
        n = cuenta.get((fuente, clave), 0)
        print(f"  {n:>5}  {fuente:<10} {clave[-52:]:<52} {dice:>18} "
              f"(su rama: {manda})")

    conteo = _conteo_del_dia(args.dia)
    vacias = secciones_vacias(conteo)
    print(f"\n=== secciones vacias en una cadena y llenas en las demas: {len(vacias)}")
    for fuente, seccion in vacias:
        otras = sum(c.get(seccion, 0) for f, c in conteo.items() if f != fuente)
        print(f"  {fuente:<10} {seccion:<22} 0 aqui, {otras} en las demas")

    sin = {f: c.get(None, 0) for f, c in conteo.items() if c.get(None, 0)}
    if sin:
        print("\n=== productos sin seccion (salen al final de la lista):")
        for fuente, n in sorted(sin.items(), key=lambda kv: -kv[1]):
            print(f"  {fuente:<10} {n}")

    nuevas = sin_mapear(args.dia)
    if nuevas:
        print(f"\n=== categorias nuevas, sin mapear todavia: {len(nuevas)}")
        print("  (la propuesta sale de lo que hace el resto de su rama)")
        for fuente, clave, n, propuesta in nuevas:
            print(f"  {n:>4}  {fuente:<10} {clave[:56]:<56} "
                  f"-> {propuesta or 'A MANO: su rama no es clara'}")
        if args.aplicar:
            puestas = aplica(nuevas)
            print(f"  {puestas} claves anadidas a {FICHERO.name}; "
                  f"las que no tienen propuesta hay que ponerlas a mano")

    return 1 if malas or vacias or rotas or disidentes else 0


if __name__ == "__main__":
    raise SystemExit(main())
