"""¿Falta media tienda? Comparar la captura de hoy con la ultima buena, por rama.

El fallo que obliga a escribir esto
-----------------------------------
El 18 de septiembre de 2026, Alcampo entrego 20.571 productos en vez de 23.573 y
la ejecucion se dio por **completa, con cero errores**. El bronze se escribio, el
pipeline lo proceso y el catalogo del dia salio a la app.

Faltaba la rama **Frescos entera**: 2.646 productos el dia anterior, 91 ese dia.
Fruta, verdura, carne y pescado, que es justo donde mas se notan las diferencias
de precio entre supermercados y la mitad de la razon de ser de esta aplicacion.

Nadie se entero hasta que alguien comparo los dos dias a mano.

Por que los controles que ya habia no lo vieron
-----------------------------------------------
Habia tres, y los tres miran el **total**:

    check_drift          aviso en el log, no decide nada
    MERMA_ACEPTABLE      solo se aplica si la ejecucion ya se dio por parcial
    errores == 0         no hubo ni un error: nadie fallo, simplemente no se pidio

Un total puede bajar un 13 % por mil razones normales. Lo que no es normal es que
una rama con 2.646 productos se quede en 91 **mientras las demas siguen igual**.
El total lo esconde; la rama lo grita.

Como se usa
-----------
    caidas = cobertura.revisa(df, "alcampo")
    if caidas:
        # la ejecucion no esta completa por mucho que no haya habido errores
"""
from __future__ import annotations

from collections import Counter

import polars as pl

from core import alcance, config

# Una rama tiene que ser lo bastante grande para que su desaparicion signifique
# algo. Por debajo de esto, que un dia no salga es ruido normal del catalogo.
#
# Es RELATIVO al tamano del catalogo, y eso importa: con un minimo fijo de 100,
# el control era inerte en Aldi -- 2.065 productos repartidos en 100 categorias,
# ninguna llega a 100 -- y tambien en cualquier prueba pequena. Se probo con un
# catalogo de mentira de 60 productos al que se le quitaba una rama de 24 (el
# 40 %) y el control no decia nada.
#
# Ahora vigila cualquier rama que sea el 2 % del catalogo, con suelo de 20
# productos (por debajo de eso es ruido de verdad) y techo de 100 (por encima no
# hace falta ser mas estricto: en Alcampo el 2 % son 471 y perder 100 productos
# de una rama ya merece mirarlo).
MINIMO_RELATIVO = 0.02
MINIMO_SUELO = 20
MINIMO_TECHO = 100


def minimo_para_vigilar(total: int) -> int:
    return max(MINIMO_SUELO, min(MINIMO_TECHO, int(total * MINIMO_RELATIVO)))

# Cuanto puede encoger una rama sin que salte la alarma. La mitad es mucho, y
# aun asi el caso real de Alcampo perdio el 96,6 % de la suya.
CAIDA_MAXIMA = 0.5


def _rama(categoria: str | None, fuente: str) -> str:
    """El primer nivel de la categoria, como lo escribe cada cadena."""
    if not categoria:
        return "(sin categoria)"
    if fuente == "alcampo":            # "Frescos > Pescaderia > ..."
        return categoria.split(" > ")[0].strip()
    if fuente == "dia":                # "https://www.dia.es/congelados-y-helados/..."
        trozos = [t for t in categoria.split("/") if t]
        return trozos[2] if len(trozos) > 2 else categoria
    return categoria.split("/")[0].strip()


def solo_cesta_familiar(df: pl.DataFrame) -> pl.DataFrame:
    """Quita las filas que la politica de alcance excluye (`core/alcance.py`).

    **Esto es lo que desbloquea una captura entera.** El 5 de octubre de 2026 el colector de
    Alcampo rechazo 23.859 productos con 0 errores porque una rama de decoracion venia hundida
    ("Hogar y Decoracion: 133 -> 31"). Esa rama es bazar, y con el contrato ni se pide: el
    contrato lo dice con estas palabras, *"una rama excluida nunca veta una captura incluida"*.

    **`revisar` se queda.** Lo que se quita es lo excluido; un producto sin clasificar puede ser
    perfectamente comida (media despensa de Alcampo sale en `revisar`), y callarlo seria peor que
    el ruido que ahorra.
    """
    if df.is_empty() or "categoria" not in df.columns:
        return df
    nombres = (df["nombre"].to_list() if "nombre" in df.columns else [""] * df.height)
    categorias = df["categoria"].to_list()
    excluida = [alcance.clasificar_alcance(n, c).estado == alcance.EXCLUIDO
                for n, c in zip(nombres, categorias, strict=False)]
    if not any(excluida):
        return df
    return df.filter(~pl.Series("excluida", excluida))


def por_rama(df: pl.DataFrame, fuente: str, *, solo_alcance: bool = True) -> dict[str, int]:
    """Cuantos productos hay en cada rama. De la cesta familiar, salvo que se pida todo."""
    if "categoria" not in df.columns or df.is_empty():
        return {}
    if solo_alcance:
        df = solo_cesta_familiar(df)
    return dict(Counter(_rama(c, fuente) for c in df["categoria"].to_list()))


def _ultimo_bronze(fuente: str) -> pl.DataFrame | None:
    partes = sorted((config.DATA / "bronze" / f"fuente={fuente}").glob(
        "fecha=*/part.parquet"))
    if not partes:
        return None
    try:
        return pl.read_parquet(partes[-1])
    except Exception:  # noqa: BLE001
        return None


def particiones_bronze() -> set[tuple[str, str]]:
    """Los pares (cadena, fecha) que hay escritos en bronze, ahora mismo.

    Un solo sitio que sepa como esta puesto bronze en disco. Lo usan dos
    controles distintos -- el de la ejecucion diaria y el del resumen -- y la
    experiencia dice que la misma regla escrita en dos sitios acaba siendo dos
    reglas distintas.
    """
    raiz = config.DATA / "bronze"
    return {
        (parte.parent.parent.name.split("=", 1)[1],
         parte.parent.name.split("=", 1)[1])
        for parte in raiz.glob("fuente=*/fecha=*/*.parquet")
        if "=" in parte.parent.name and "=" in parte.parent.parent.name
    }


def apartados() -> dict[tuple[str, str], str]:
    """Particiones de bronze que alguien aparto a mano, y por que.

    `docs/OPERACION.md` dice que un bronze malo se **aparta, no se borra**:

        mv data/bronze/fuente=alcampo/fecha=2026-09-18 \
           data/debug/descartados/alcampo-2026-09-18-sin-frescos

    El motivo va en el nombre de la carpeta. Esto lo lee de vuelta, para que los
    controles sepan distinguir "esto lo apartaste tu, y ahi esta" de "esto ha
    desaparecido y no hay rastro". Son dos situaciones muy distintas y durante un
    dia entero se confundieron: el 18 de septiembre de 2026 se dio por perdido un
    bronze que estaba entero en `data/debug/descartados`, apartado a proposito esa
    misma manana por venir sin la rama Frescos.

    Devuelve {(cadena, fecha): motivo}.
    """
    raiz = config.DATA / "debug" / "descartados"
    fuera = {}
    if not raiz.exists():
        return fuera
    for carpeta in raiz.glob("*"):
        if not carpeta.is_dir():
            continue
        # <cadena>-<aaaa-mm-dd>-<motivo con guiones>
        trozos = carpeta.name.split("-")
        if len(trozos) < 4:
            continue
        fuente, anio, mes, dia = trozos[0], trozos[1], trozos[2], trozos[3]
        fecha = f"{anio}-{mes}-{dia}"
        if not (anio.isdigit() and mes.isdigit() and dia.isdigit()):
            continue
        motivo = "-".join(trozos[4:]) or "sin motivo apuntado"
        fuera[(fuente, fecha)] = motivo.replace("-", " ")
    return fuera


def sin_bronze(fuentes: list[str], dia: str) -> list[str]:
    """De las cadenas que dicen haber ido bien, cuales no dejaron bronze.

    El 18 de septiembre de 2026 el colector de Alcampo termino con 20.571
    productos y cero errores a las 08:26, y a las 08:52 la carpeta
    `bronze/fuente=alcampo/fecha=2026-09-18` ya no estaba. El pipeline siguio con
    la instantanea del dia anterior, el resumen dijo trece dias acumulados tan
    tranquilo, y en gold quedaron 20.559 filas de un dia sin bronze. Aquel caso
    resulto ser un apartado a proposito -- estaba entero en
    `data/debug/descartados` --, pero eso se supo un dia despues, y lo que quedo
    claro es lo otro: **nada en el sistema se entero de que la carpeta ya no
    estaba**, ni para bien ni para mal.

    Esto se mira **antes** del pipeline, que es cuando todavia sirve de algo: el
    crudo del dia sigue en disco y `reprocesar --fuente X --fecha Y` lo arregla en
    un minuto.

    Una cadena que se nego a escribir a proposito -- porque el control de
    cobertura vio media tienda desaparecida -- ya devuelve error, asi que no llega
    aqui: esta lista es solo para las que dijeron que todo habia ido bien.
    """
    hay = particiones_bronze()
    return [f for f in fuentes if (f, dia) not in hay]


def revisa(df: pl.DataFrame, fuente: str, *,
           minimo: int | None = None,
           caida: float = CAIDA_MAXIMA) -> list[str]:
    """Ramas que se han hundido respecto al ultimo bronze bueno.

    Devuelve una lista de frases listas para imprimir, vacia si todo bien. No
    decide nada: quien llama es el que sabe si eso justifica no guardar.
    Para decidir, `que_vetan`.
    """
    return [frase for _, frase in caidas(df, fuente, minimo=minimo, caida=caida)]


# --- ramas que no son estanteria -------------------------------------------
#
# **El 4 de noviembre de 2026 el control de cobertura tiro el dia entero de Alcampo.**
# Trajo 23.416 productos con cero errores y no se guardo ni uno: la rama "Folletos y
# Promociones" habia pasado de 1472 a 727 (-51 %). Pero esa rama **no es una estanteria**,
# es el folleto de la campana de la semana: su contenido lo pone la campana, y cuando una
# termina, se queda a la mitad. Ese dia las otras quince ramas de comida **subieron**
# (Frescos +6 %, Perfumeria +10 %, Drogueria +15 %, Bebe +38 %) y el total fue mayor que
# el de ayer. Se conservo la captura anterior y el dia se perdio: el que hace once de
# treinta que le faltan a Alcampo en la ventana.
#
# **La excepcion es de la rama y de la cadena, y esta escrita**, no deducida: un hundimiento
# de verdad -- Frescos, que es el caso del 18 de septiembre de 2026 -- sigue vetando la
# captura entera. Lo que cambia es que un folleto que rota ya no cuesta los precios del dia.
RAMAS_DE_CAMPANA: dict[str, frozenset[str]] = {
    "alcampo": frozenset({"Folletos y Promociones"}),
}


def es_de_campana(rama: str, fuente: str) -> bool:
    """¿Esta rama es un folleto de campana y no una estanteria del catalogo?"""
    return rama in RAMAS_DE_CAMPANA.get(fuente, frozenset())


def caidas(df: pl.DataFrame, fuente: str, *,
           minimo: int | None = None,
           caida: float = CAIDA_MAXIMA) -> list[tuple[str, str]]:
    """`[(rama, frase)]` de las ramas hundidas, con la rama aparte para poder decidir.

    La frase es la misma que devolvia `revisa`, para que los registros no cambien.
    """
    anterior = _ultimo_bronze(fuente)
    if anterior is None or anterior.is_empty():
        return []                       # primera captura: no hay con que comparar
    antes = por_rama(anterior, fuente)
    ahora = por_rama(df, fuente)
    if not antes:
        return []
    if minimo is None:
        minimo = minimo_para_vigilar(len(anterior))
    salida = []
    for rama, n_antes in sorted(antes.items(), key=lambda x: -x[1]):
        if n_antes < minimo:
            continue
        n_ahora = ahora.get(rama, 0)
        if n_ahora < n_antes * (1 - caida):
            perdido = 100 * (1 - n_ahora / n_antes)
            salida.append((rama, f"{rama}: {n_antes} -> {n_ahora} ({perdido:.0f}% menos)"))
    return salida


def que_vetan(df: pl.DataFrame, fuente: str, *,
              minimo: int | None = None,
              caida: float = CAIDA_MAXIMA) -> list[str]:
    """Las frases de las ramas que **si** justifican no guardar la captura.

    Es `caidas` menos las ramas de campana (`RAMAS_DE_CAMPANA`). Lo que veta es una
    estanteria hundida; un folleto que rota se cuenta pero no veta.
    """
    return [frase for rama, frase in caidas(df, fuente, minimo=minimo, caida=caida)
            if not es_de_campana(rama, fuente)]

