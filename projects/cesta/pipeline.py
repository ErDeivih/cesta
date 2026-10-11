"""bronze -> silver -> gold. Se ejecuta despues de los colectores.

silver: normaliza formatos y unidades, deja todo comparable en EUR/kg, EUR/L, EUR/ud.
gold:   aplica core.derive sobre el historico completo y deja una tabla por dia
        y un resumen por producto para la interfaz.

Todo se recalcula entero cada dia: es barato y elimina una clase entera de bugs.
"""
from __future__ import annotations

import contextlib
import re
from datetime import date

import duckdb
import polars as pl

from core import alcohol, config, derive, promos, secciones, sellos
from core.normalize import (
    CANONICAS,
    SUELO_REFERENCIA_CENT,  # noqa: F401  (se reexporta: lo usan las pruebas)
    _sin_tildes,
    lecturas_referencia,
    nombre_limpio,
    normaliza_referencia,
    parse_formato,
    referencia_publicable,
)
from core.storage import write_parquet, write_parquet_file

# "pack 6 x 1 L", "pack 24 x 33 cl": cuantas unidades van dentro.
_PACK_EN_NOMBRE = re.compile(r"pack\s*(\d+)\s*[x\u00d7]", re.IGNORECASE)


def _referencia_que_cuadra(lecturas, precio, cantidad, unidad):
    """¿Alguna lectura de la referencia de la cadena confirma este formato?

    Es el freno que impide que el nombre decida solo: "lavadora 9 kg" no cuadra
    con su propio precio por kilo ni de lejos, asi que se cae sola. Devuelve la
    lectura que cuadra, o None.
    """
    if not cantidad or not unidad or not precio:
        return None
    for cand, u in lecturas:
        if u == unidad and cand > 0 and abs(precio / cantidad - cand) / cand < 0.05:
            return (cand, u)
    return None


def _cargar_bronze() -> pl.DataFrame | None:
    """Une todos los parquet de bronze aunque tengan columnas distintas.

    Pasa siempre: una cadena nueva trae una columna que las viejas no tenian, o al
    reves. Leerlos de golpe falla con 'did not find column X'. Se leen uno a uno y
    se unen por nombre, rellenando con nulos lo que falte.
    """
    ficheros = sorted(config.BRONZE.rglob("*.parquet"))
    if not ficheros:
        return None
    trozos = []
    for f in ficheros:
        df = pl.read_parquet(f)
        # las particiones estilo Hive van en la ruta, no dentro del fichero
        partes = {p.split("=", 1)[0]: p.split("=", 1)[1]
                  for p in f.parts if "=" in p}
        for k, v in partes.items():
            if k not in df.columns:
                df = df.with_columns(pl.lit(v).alias(k))
        trozos.append(df)
    return pl.concat(trozos, how="diagonal_relaxed")


def cantidad_para_el_precio(cantidad: pl.Expr, escurrido: pl.Expr) -> pl.Expr:
    """Por que cantidad se divide el precio para sacar el precio por unidad.

    **El peso escurrido manda cuando la cadena lo publica.** Arreglo del 26 de septiembre de
    2026, y va con la medicion delante porque la primera version de esta nota decia lo
    contrario de lo que dicen los datos (`projects.cesta.auditar_escurrido` la reproduce
    entera).

    El caso que lo enseño, la ventresca de atun claro: Mercadona declara 111 g (el neto, con
    el aceite) y aparte dice que el escurrido son 78 g; las otras cadenas venden la misma
    lata declarando 73 g. Dividiendo por lo declarado, la de Mercadona salia a 2.973 c/kg
    contra 4.233, 4.274 y 4.781 de las otras: **parecia la mas barata sin serlo**. Dividiendo
    por el escurrido sale a 4.231 c/kg, que es donde estan las demas.

    Lo que se gana, medido en los 17 grupos de conserva donde Mercadona publica escurrido y
    hay al menos dos cadenas mas vendiendo lo mismo por kilo, comparando el precio por kilo
    de Mercadona contra la mediana de las otras:

        dividiendo por lo declarado   mediana 0,606   1 de 17 dentro del mas-menos 20 %
        dividiendo por el escurrido   mediana 0,990  12 de 17 dentro del mas-menos 20 %

    Lo que cuesta, y se dice aqui para que no sorprenda: el precio de referencia que publica
    Mercadona se calcula sobre **lo declarado**, no sobre el escurrido (en 142 de esos 179
    productos), asi que este arreglo nos aleja de su propia ficha: coincidir con ella pasa del
    98,4 % al 95,4 % al 2 %. Las otras cuatro cadenas no se mueven. Se acepta porque la ficha
    de una cadena es coherente consigo misma y no comparable entre cadenas, que es justo para
    lo que sirve este proyecto.

    Y el limite: la base no es uniforme en todas las cadenas. En las sardinas, Mercadona
    declara 85 g con 65 g escurridos y la competencia declara 85-90 g, asi que ahi normalizar
    solo a Mercadona se pasa de frenada (5 de esos 17 grupos siguen fuera del 20 %). Para
    arreglarlo habria que saber la base de cada cadena rival, y eso no lo publica nadie.

    Se usa el escurrido solo si es mayor que cero y menor que el 98 % de lo declarado: asi un
    valor raro no puede inflar un precio por unidad.
    """
    return (pl.when(escurrido.is_not_null()
                    & (escurrido > 0)
                    & cantidad.is_not_null()
                    & (escurrido < cantidad * 1000 * 0.98))
              .then(escurrido / 1000.0)
              .otherwise(cantidad))


def a_silver(df: pl.DataFrame) -> pl.DataFrame:
    """Deja todo comparable: cantidad, unidad canonica y precio por unidad.

    Decision importante, tomada tras revisar los datos reales del 6 sep:
    el precio por unidad **lo calculamos siempre nosotros**, no lo copiamos de la
    cadena. Mercadona publica `bulk_price` en la unidad de su etiqueta de estante,
    que es EUR/lavado en los detergentes, EUR/recambio en las cuchillas y EUR/kg en
    las especias. Mezclar esas unidades en una sola columna es la forma silenciosa
    de comparar peras con manzanas: un EUR/100 g junto a un EUR/kg da un error de
    10x que nadie ve. Lo suyo se conserva aparte, como dato informativo.

    Nada de `iter_rows` sobre el frame entero: ademas de lento, convierte la columna
    de fecha con zona horaria a objetos de Python y en Windows eso mata el proceso.
    """
    formatos = df["formato_txt"].fill_null("").to_list()
    nombres = df["nombre"].fill_null("").to_list()
    fuentes = df["fuente"].fill_null("").to_list()
    precios = df["precio_cent"].to_list()
    precios_ref = df["precio_ref_nativo_cent"].to_list()
    unidades_ref = df["unidad_ref_nativa"].to_list()
    marcas = (df["marca"].fill_null("").to_list()
              if "marca" in df.columns else [""] * len(df))

    cantidades, unidades, packs, limpios, formatos_validos = [], [], [], [], []
    refs_cent, refs_unidad = [], []
    # De donde salio el formato de cada producto. Es lo que permite que el
    # emparejador distinga un "1 ud" que la cadena declara de un "1 ud" que
    # pusimos nosotros porque no sabemos el tamano: los dos valen 1, pero uno es
    # un dato y el otro es una ausencia disfrazada. Ver docs/DIAGNOSTICO-MATCHING.md §6.
    fiables: list[bool] = []
    # strict: las siete listas salen del mismo DataFrame. Si alguna vez no
    # midieran lo mismo, seria un fallo grave y silencioso (cada producto con el
    # precio del siguiente). Mejor que reviente.
    for fuente, fmt, nom, mar, precio, precio_ref, unidad_ref in zip(
            fuentes, formatos, nombres, marcas, precios, precios_ref,
            unidades_ref, strict=True):
        # El nombre contiene especificaciones que no son el formato comercial:
        # "5G" no son 5 gramos y "lavadora 9 kg" no pesa 9 kg. Por eso se analiza
        # primero el campo de formato.
        cant, uni, pack = parse_formato(fmt)
        lecturas = lecturas_referencia(fuente, precio_ref, unidad_ref)
        ref_cent, ref_uni = lecturas[0] if lecturas else (None, None)
        # La etiqueta de la referencia segun la cadena, para poder decir si la
        # contradiccion viene de ahi.
        ref_uni_nativa = None
        if ref_cent is not None and unidad_ref:
            ref_uni_nativa = normaliza_referencia(fuente, precio_ref, unidad_ref)[1]

        # Carrefour no publica campo de formato en NINGUNO de sus 16.560
        # productos: el tamano solo esta en el nombre. Dejarlo asi significaba
        # 4.032 productos sin cantidad (3.921 medidos antes de arreglar las
        # lecturas de la referencia), y sin cantidad no hay bloque de comparacion
        # ni emparejamiento posible.
        # Se recurre al nombre solo como ultimo recurso y solo si la propia
        # cadena lo confirma. Antes exigia que la unidad del nombre coincidiera
        # con la etiqueta de la cadena, y eso dejaba fuera todo lo que trae
        # "100ml": un desodorante de 50 ml a 2,49 EUR publica 4,98, que es el
        # precio del litro, pero leido como si fuera por litro no cuadra con
        # nada. Con las dos lecturas (ver `lecturas_referencia`) si cuadra.
        # El nombre como ultimo recurso, en dos casos: cuando la cadena no
        # publica formato, y cuando publica uno que **su propio precio no
        # confirma** mientras el nombre si.
        #
        # El segundo caso se midio el 22 de septiembre de 2026: DIA vende fruta,
        # verdura, carne y pescado **al peso** y publica formato_txt "1 kg" como
        # relleno, con la cantidad real en el nombre. "Filete 1o de vacuno
        # Seleccion de Dia 450 g aprox." quedaba como un kilo a 8,64 EUR, o sea
        # 8,64 EUR/kg, cuando su propia etiqueta dice 19,19 EUR/kg -- y el nombre
        # lo confirma al centimo: 8,64 / 0,45 = 19,20. Son 109 productos, y de
        # aqui salia el peor grupo ancho del diagnostico (§14: "unos filetes de
        # dorada de 300 g aprox. como 1 g").
        #
        # Se exigen las dos condiciones a la vez: la referencia de la cadena NO
        # confirma el formato que trae, y SI confirma el del nombre. Con una sola,
        # cualquier producto con el precio redondeado cambiaria de tamano.
        if (cant is None
                or (precio and uni and lecturas
                    and not _referencia_que_cuadra(lecturas, precio, cant, uni))):
            cant_n, uni_n, pack_n = parse_formato(nom)
            if _referencia_que_cuadra(lecturas, precio, cant_n, uni_n):
                cant, uni, pack = cant_n, uni_n, pack_n
        # La cadena se contradice consigo misma. DIA publica "Detergente liquido
        # Dia Super Paco 61 lavados" con formato_txt "61 l" -- 61 litros de
        # detergente en un bote de tres -- y su propia referencia de precio en
        # "lavado". Medido el 22 de septiembre: 33 productos asi (lavados, dosis,
        # capsulas) con cantidades de 30 a 69 "litros" que envenenaban el precio
        # por unidad y el bloque de comparacion. El precio lo confirma: 7,14 EUR
        # / 61 = 0,117 y su etiqueta dice 0,12 EUR por lavado. Se cambia la
        # unidad SOLO cuando el nombre dice el mismo numero en unidades y la
        # referencia de la cadena es por unidad.
        if (cant and uni in ("kg", "l") and precio and ref_uni_nativa == "ud"
                and ref_cent):
            cant_n, uni_n, _pack_n = parse_formato(nom)
            if (uni_n == "ud" and cant_n is not None
                    and abs(cant_n - cant) < 1e-6
                    and abs(precio / cant - ref_cent) / ref_cent < 0.05):
                uni = "ud"

        # Ya con el formato resuelto, se elige la lectura de la referencia que
        # cuadra con el. Si no cuadra ninguna se queda la primera, que para una
        # etiqueta de 100 es la de por 100 (154 de 173 medidas en Aldi).
        con_formato = _referencia_que_cuadra(lecturas, precio, cant, uni)
        if con_formato:
            ref_cent, ref_uni = con_formato
        # **Y si no se ha podido verificar y el valor es imposible, no se publica.** El respaldo por
        # cadena acierta casi siempre, pero en los productos sin formato con el que comprobar deja
        # pasar lecturas equivocadas: 1.524 filas medidas con precios por unidad de 2 a 19 centimos.
        elif not referencia_publicable(ref_cent, ref_uni):
            ref_cent, ref_uni = None, None

        # El formato dice el tamano de UNA unidad y el nombre dice cuantas van
        # dentro. DIA publica "Cerveza El Aguila pack 24 x 33 cl" con
        # formato_txt "33 cl": nos quedaba 64,73 EUR/l cuando su propia web dice
        # 2,70. Son 211 productos (183 de DIA, 25 de Alcampo, 3 de Carrefour) y
        # el error es de hasta 24 veces, asi que en una comparacion cantan.
        # Como en la regla de Carrefour de arriba, el nombre no decide solo: se
        # multiplica unicamente si al hacerlo el precio por unidad cuadra con el
        # que publica la propia cadena.
        if cant and uni and pack == 1 and precio and ref_cent and uni == ref_uni:
            en_el_nombre = _PACK_EN_NOMBRE.search(_sin_tildes(nom.lower()))
            if en_el_nombre:
                n = int(en_el_nombre.group(1))
                if 1 < n <= 48:
                    candidato = precio / (cant * n)
                    if abs(candidato - ref_cent) / ref_cent < 0.05:
                        cant, pack = round(cant * n, 6), n

        # La etiqueta de Aldi no dice siempre lo mismo: su "100-g"/"100-ml" es de
        # verdad por 100 en 154 de 173 productos, pero en 16 ya viene por kilo o
        # litro. Aqui habia un apaño solo para Aldi; ahora lo resuelve
        # `lecturas_referencia` + `cuadra` para las cinco cadenas, que es donde
        # estaba el error de verdad (Carrefour 1.816 productos, DIA 532,
        # Mercadona 504). No se borra el conocimiento: se cita en
        # `core/normalize.lecturas_referencia`.

        # Error real observado en Aldi: "350 kg" para un bizcocho de 350 g. Solo
        # se corrige cuando la referencia nativa confirma exactamente el factor 1000.
        if (fuente == "aldi" and uni == "kg" and cant is not None and cant >= 100
                and precio and ref_cent and ref_uni == "kg"):
            candidato = precio / (cant / 1000)
            if abs(candidato - ref_cent) / ref_cent < 0.1:
                cant /= 1000
        # Fiable = sabemos el tamano de verdad: lo publica la cadena o su propia
        # referencia de precio lo confirma. Lo que no llega aqui es lo que luego
        # se rellena con un "1 ud" de relleno, y ese no se puede usar ni para
        # bloquear ni para comparar precios por unidad.
        fiables.append(cant is not None and cant > 0 and uni is not None)
        cantidades.append(cant)
        unidades.append(uni)
        packs.append(pack)
        formatos_validos.append(cant is not None and cant > 0 and uni is not None)
        limpios.append(nombre_limpio(nom, mar or None))
        refs_cent.append(ref_cent)
        refs_unidad.append(ref_uni)

    # Los sellos que la cadena NO declara pero escribe en el nombre del producto.
    # Aqui y no en cada colector porque vale igual para las cinco: el nombre es
    # la unica columna que todas publican al 100 %. Medido el 17 de septiembre,
    # anade 1.358 sellos, y 990 de ellos son "sin azucar", que practicamente
    # ninguna cadena etiqueta aunque lo ponga en letras grandes en el envase.
    #
    # Se guarda de donde sale cada sello (`sellos_origen`) porque no valen lo
    # mismo: un certificado tiene una auditoria detras, una etiqueta la pone la
    # cadena, y el nombre del producto es marketing. En la ficha se puede decir
    # "lo pone en el nombre" en vez de dar a entender que esta certificado.
    declarados = df["sellos"].to_list() if "sellos" in df.columns else [None] * len(df)
    tiene_cert = (df["certificados"].to_list() if "certificados" in df.columns
                  else [None] * len(df))
    sellos_finales, sellos_origen = [], []
    for nombre, declarado, cert in zip(nombres, declarados, tiene_cert, strict=True):
        del_nombre = sellos.de_prosa(nombre)
        juntos = set((declarado or "").split(",")) | set((del_nombre or "").split(","))
        juntos.discard("")
        if not juntos:
            sellos_finales.append(None)
            sellos_origen.append(None)
            continue
        sellos_finales.append(",".join(sorted(juntos)))
        if declarado and del_nombre and set(del_nombre.split(",")) - set(declarado.split(",")):
            sellos_origen.append("mixto")
        elif declarado:
            sellos_origen.append("certificado" if cert else "etiqueta")
        else:
            sellos_origen.append("nombre")

    # Si lleva alcohol. Solo Alcampo y Mercadona lo declaran (1.589 y 223); las
    # otras tres cadenas, nada. Un filtro "sin alcohol" que fallara en tres de
    # cinco devolveria vino a quien no bebe, asi que se deduce del nombre y de la
    # categoria para todas. Ver core/alcohol.py: es un filtro de EXCLUSION, y en
    # esos pasarse es molesto pero quedarse corto es lo peligroso, justo al
    # contrario que en los sellos.
    declara = (df["es_alcohol"].to_list() if "es_alcohol" in df.columns
               else [None] * len(df))
    grados = (df["grado_alcohol"].to_list() if "grado_alcohol" in df.columns
              else [None] * len(df))
    categorias = (df["categoria"].fill_null("").to_list()
                  if "categoria" in df.columns else [""] * len(df))
    alcoholes = [bool(d) or alcohol.deduce(nom, cat, gr)
                 for nom, cat, d, gr in zip(nombres, categorias, declara, grados,
                                            strict=True)]

    out = df.with_columns([
        pl.Series("es_alcohol", alcoholes, dtype=pl.Boolean),
        pl.Series("sellos", sellos_finales, dtype=pl.Utf8),
        pl.Series("sellos_origen", sellos_origen, dtype=pl.Utf8),
        pl.Series("cantidad", cantidades, dtype=pl.Float64),
        pl.Series("unidad_canon", unidades, dtype=pl.Utf8),
        # Lo que declara la cadena manda sobre lo que deducimos del formato.
        # Ver core/schemas.py: nuestra deduccion se equivocaba en el 87 % de los
        # packs de Mercadona.
        pl.Series("unidades_pack", packs, dtype=pl.Int32),
        pl.Series("nombre_limpio", limpios, dtype=pl.Utf8),
        pl.Series("precio_ref_canon_cent", refs_cent, dtype=pl.Float64),
        pl.Series("unidad_ref_canon", refs_unidad, dtype=pl.Utf8),
        pl.Series("formato_parseado", formatos_validos, dtype=pl.Boolean),
        pl.Series("cantidad_fiable", fiables, dtype=pl.Boolean),
    ])

    if "unidades_envase" in out.columns:
        out = out.with_columns(
            pl.coalesce([pl.col("unidades_envase"), pl.col("unidades_pack")])
              .alias("unidades_pack"))

    # Peso variable: si la cadena lo declara, su "precio total" puede ser un
    # artefacto (Mercadona lo da como el precio de 99 kg). El unico dato bueno es
    # el precio por kilo de su etiqueta.
    sin_tamano = ~pl.col("formato_parseado")
    peso_variable = pl.col("peso_variable").fill_null(False)
    con_ref = (pl.col("unidad_ref_canon").is_not_null()
               & pl.col("precio_ref_canon_cent").is_not_null())
    articulo = sin_tamano & ~peso_variable & ~con_ref
    out = out.with_columns([
        pl.when(peso_variable).then(pl.lit(None, dtype=pl.Int64))
          .otherwise(pl.col("precio_cent").cast(pl.Int64))
          .alias("precio_cent"),
        pl.when(~sin_tamano).then(pl.col("unidad_canon"))
          .when(con_ref).then(pl.col("unidad_ref_canon"))
          .otherwise(pl.lit("ud")).alias("unidad_canon"),
        pl.when(articulo).then(pl.lit(1.0)).otherwise(pl.col("cantidad"))
          .alias("cantidad"),
    ])

    # Precio por unidad: derivado si hay formato fiable; nativo para peso variable
    # o formato ausente; precio del articulo cuando no existe referencia.
    # La columna del escurrido puede no venir (bronze de antes de que se leyera ese campo)
    # y una prueba pequena construye su marco sin ella: se pregunta antes, no se revienta.
    escurrido = (pl.col("peso_escurrido_g") if "peso_escurrido_g" in out.columns
                 else pl.lit(None, dtype=pl.Int32))
    cantidad_precio = cantidad_para_el_precio(pl.col("cantidad"), escurrido)
    out = out.with_columns([
        pl.when(~sin_tamano & pl.col("precio_cent").is_not_null())
          .then((pl.col("precio_cent") / cantidad_precio).round(4))
          .when(con_ref).then(pl.col("precio_ref_canon_cent"))
          .otherwise(pl.col("precio_cent").cast(pl.Float64))
          .alias("precio_unidad_cent"),
        pl.when(~sin_tamano).then(pl.lit("derivado"))
          .when(con_ref).then(pl.lit("nativo"))
          .otherwise(pl.lit("articulo"))
          .alias("proc_precio_unidad"),
    ])

    # La condicion para creerle a la cadena en vez de a nuestro calculo.
    CORRIGE = (pl.col("factor_ref") >= 2.0) & pl.col("unidades_inferidas").is_null()

    # discrepancia con la etiqueta de la cadena: senala los formatos que mienten
    # ("1 ud" que en realidad son 3 recambios o 23 toallitas)
    ref = pl.col("precio_ref_canon_cent")
    out = out.with_columns([
        pl.when(ref.is_not_null() & (ref > 0) & pl.col("precio_unidad_cent").is_not_null()
                & (pl.col("unidad_canon") == pl.col("unidad_ref_canon")))
          .then(((pl.col("precio_unidad_cent") - ref).abs() / ref).round(3))
          .alias("desviacion_ref"),
        # El factor entre los dos, mirado en las dos direcciones. `desviacion_ref`
        # divide siempre por el de la cadena, asi que cuando el equivocado es el
        # NUESTRO y se queda mil veces corto, la desviacion se queda pegada al
        # 0,999 y no pasa de 1 por mucho que el error sea de tres ordenes de
        # magnitud. Paso de verdad: el azafran de Alcampo, "0,400 gr." leido como
        # 0,4 kg, daba 6,67 EUR/kg frente a los 6.875 EUR/kg de su propia
        # etiqueta, y la desviacion valia 0,999. Un cociente no tiene ese sesgo.
        pl.when(ref.is_not_null() & (ref > 0) & (pl.col("precio_unidad_cent") > 0)
                & (pl.col("unidad_canon") == pl.col("unidad_ref_canon")))
          .then(pl.max_horizontal(pl.col("precio_unidad_cent"), ref)
                / pl.min_horizontal(pl.col("precio_unidad_cent"), ref))
          .alias("factor_ref"),
    ]).with_columns([
        # si la cadena dice "1 ud" y su precio por referencia es mucho menor,
        # el envase trae mas piezas de las declaradas: las recuperamos
        pl.when((pl.col("unidad_ref_canon") == "ud") & (pl.col("cantidad") == 1)
                & ref.is_not_null() & (ref > 0)
                & (pl.col("precio_cent").cast(pl.Float64) / ref > 1.5))
          .then((pl.col("precio_cent").cast(pl.Float64) / ref).round(0).cast(pl.Int32))
          .alias("unidades_inferidas"),
    ])

    # Cuando nuestro precio por unidad y el de la cadena hablan de la MISMA
    # unidad y se llevan un factor de dos o mas, uno de los dos esta mal. Y no
    # hay forma fiable de saber cual.
    #
    # Revisadas las 220 filas del 17 de septiembre de 2026, una a una, aparecen
    # errores en las dos direcciones:
    #
    #   nos equivocamos NOSOTROS
    #     "Conchitas Jumpers 95 g"    DIA publica 0,095 **g** en su ficha (se
    #                                 comieron el kilo) -> 15.263 EUR/kg. Su
    #                                 etiqueta dice 15,26, que es la buena.
    #     "Platano 850 g aprox"       cantidad leida 0,001 kg -> 2.540 EUR/kg.
    #
    #   se equivoca LA CADENA
    #     "Barrita proteica, pack de 3 x 40 g, 3,49 EUR"  Aldi dice 0,03 EUR/kg.
    #                                 Con eso el pack costaria 0,004 EUR; la
    #                                 misma barrita suelta dice 31,25 EUR/kg.
    #     "Hierbas provenzales 20 g, 0,77 EUR"   Aldi dice 481,30 EUR/kg cuando
    #                                 lo correcto es 38,50.
    #     "Panuelos, pack de 30, 2,95 EUR"       Aldi dice 0,01 EUR/unidad.
    #
    # Se probo decidir por plausibilidad -- que la cantidad implicita sea un
    # tamano de envase creible -- y no se sostiene: un tarro de azafran de 0,4 g
    # es tan raro como un error, y da igual de "implausible" que el fallo de Aldi.
    #
    # Asi que **no se elige ganador: la fila se aparta de las comparaciones**.
    # Sigue teniendo su precio total, sigue saliendo en la busqueda y se puede
    # anadir a la lista; lo que no hace es decidir donde sale mas barato algo,
    # porque para eso hay que estar seguro. Son 72 filas de 52.002 (0,14 %).
    #
    # OJO CON EL ORDEN: va DESPUES de `unidades_inferidas`. El caso "1 ud a
    # 14,90 EUR con etiqueta de 4,97 EUR/ud" son tres recambios en el envase, y
    # "el envase trae tres" es mejor explicacion que "alguien se equivoco": de
    # las 220 filas, 148 eran eso.
    out = out.with_columns([
        pl.when(CORRIGE).then(pl.lit("en_disputa"))
          .otherwise(pl.col("proc_precio_unidad")).alias("proc_precio_unidad"),
    ])

    # controles de calidad: apartar solo lo imposible, nunca lo raro pero cierto
    valido = (pl.col("precio_unidad_cent").is_not_null()
              & (pl.col("precio_unidad_cent") > 0)
              & pl.col("unidad_canon").is_not_null()
              # Y tampoco lo que la propia cadena contradice por un factor de dos
              # o mas: ahi no sabemos quien tiene razon.
              & (pl.col("proc_precio_unidad") != "en_disputa"))
    malos = out.filter(~valido)
    if len(malos):
        print(f"  aviso: {len(malos)} filas sin precio por unidad utilizable")
        malos.write_parquet(config.DEBUG / f"sin_precio_unidad_{config.hoy_local()}.parquet")

    out = out.with_columns(valido.alias("precio_comparable"))
    out = _marca_ofertas_de_tarjeta(out)
    out = _anota_seccion(out)

    raros = out.filter(~pl.col("unidad_canon").is_in(list(CANONICAS)))
    if len(raros):
        print(f"  aviso: {len(raros)} filas con unidad no canonica "
              f"({sorted(set(raros['unidad_canon'].to_list()))})")

    disputa = out.filter(pl.col("proc_precio_unidad") == "en_disputa").height
    if disputa:
        print(f"  {disputa} filas donde nuestro precio por unidad y el de la cadena "
              f"se llevan x2 o mas: no se comparan, no se sabe quien tiene razon")
    discrepan = out.filter(pl.col("desviacion_ref") > 0.05).height
    if discrepan:
        print(f"  info: {discrepan} filas ({discrepan * 100 // len(out)}%) donde nuestro "
              f"precio por unidad difiere del de la cadena: formatos por dosis o packs")
    return out


def _anota_seccion(out: pl.DataFrame) -> pl.DataFrame:
    """La seccion comun del producto, a partir de la categoria de su cadena.

    `core/secciones.py` llevaba desde el 17 de septiembre de 2026 con las 849
    claves mapeadas **y sin que nadie lo llamase**: la seccion no se escribia en
    ningun sitio, asi que no cruzaba a gold y por tanto no existia (regla 2). El
    modulo entero era codigo muerto y la pantalla de pasillos no podia hacerse.

    Se calcula aqui, una vez al dia, y viaja con el producto. `categoria` ya
    estaba en el contrato; lo que faltaba era traducirla a algo comun a las
    cinco cadenas, que es justo lo que hace que "leche" de Mercadona y de Dia
    esten en el mismo pasillo.
    """
    if "categoria" not in out.columns:
        return out.with_columns(pl.lit(None, dtype=pl.Utf8).alias("seccion"))
    fuentes = out["fuente"].fill_null("").to_list()
    categorias = out["categoria"].to_list()
    valores = [secciones.seccion_de(f, c)
               for f, c in zip(fuentes, categorias, strict=True)]
    out = out.with_columns(pl.Series("seccion", valores, dtype=pl.Utf8))

    # **Y se hereda por grupo.** Si un miembro del grupo tiene seccion y otro no, se le pasa: es el mismo
    # producto, asi que va al mismo pasillo. Es lo que recoge a los que llegan **sin categoria** -- 149
    # productos de Aldi el 9 de octubre -- y a los que su cadena emite con la categoria rota (DIA, que la manda
    # como URL). Sin esto, un producto que el resto del grupo tiene colocado se queda sin pasillo.
    #
    # Va aqui y no en el emparejador porque aqui esta el resultado ya con `grupo_id`: una pasada, sin tocar los
    # enlaces.
    if "grupo_id" not in out.columns:
        return out
    heredable = (out.filter(pl.col("seccion").is_not_null())
                    .group_by("grupo_id")
                    .agg(pl.col("seccion").first().alias("_heredada")))
    return (out.join(heredable, on="grupo_id", how="left")
               .with_columns(pl.coalesce(["seccion", "_heredada"]).alias("seccion"))
               .drop("_heredada"))


def _marca_ofertas_de_tarjeta(out: pl.DataFrame) -> pl.DataFrame:
    """`promo_club` y `promo_solo_online`, leidos del texto de la promocion.

    El descuento de tarjeta **no baja lo que pagas en caja**, y esa regla lleva
    escrita desde el principio. Lo que no estaba es aplicada a todos: solo DIA
    publica un campo (`only_club_dia`), asi que solo DIA tenia `promo_club`
    puesto. Medido el 18 de septiembre de 2026 sobre el catalogo entero:

        alcampo    573 promociones que dicen "acum en tu tarjeta"
        carrefour  869 promociones que dicen "Acumula"
        dia        198 ya marcadas por su API
        ---------------------------------------------------------------
        1.244 ofertas de tarjeta contadas como rebajas de verdad

    Ejemplos literales de las que se colaban: "Club Alcampo 2ª unidad -50% acum
    en tu tarjeta", "2x1 Acumula". Se anunciaban en la app como oferta y en el
    ticket no bajaban un centimo.

    `core/promos.py` ya sabia leerlo -- `Mecanica.acumulable`, y `Mecanica.util`
    ya las excluye del calculo de la cesta --, pero la **columna** que mira la
    busqueda no se rellenaba. El conocimiento estaba y no llegaba al sitio donde
    se usa: es el mismo patron de siempre, un dato que no cruza la frontera.

    Donde la cadena lo declara manda la cadena; donde no, manda el texto.

    Lo mismo, y por la misma razon, con **`promo_solo_online`**: un descuento que
    solo existe comprando por internet no baja el ticket de la tienda. Medido el
    19 de septiembre de 2026: **397 promociones de Alcampo** lo dicen en su propio
    texto ("Cupon 1€ descuento. Solo Online.") y hasta entonces entraban en el
    total de la cesta como si fueran a bajarlo.

    Y son solo las que se leen. Carrefour lo dice en `badge.description` y DIA en
    `headband_promotion`, dos campos que todavia no pedimos (backlog N17 y N18):
    ahi hay 76 y 106 mas esperando.
    """
    if "promo_txt" not in out.columns:
        return out
    nativo = (out["promo_club"].fill_null(False).to_list()
              if "promo_club" in out.columns else [False] * len(out))
    textos = out["promo_txt"].fill_null("").to_list()
    leidas = [promos.lee(txt) if txt else None for txt in textos]
    club = [bool(n) or (m is not None and m.acumulable)
            for n, m in zip(nativo, leidas, strict=True)]
    online = [m is not None and m.solo_online for m in leidas]
    return out.with_columns([
        pl.Series("promo_club", club, dtype=pl.Boolean),
        pl.Series("promo_solo_online", online, dtype=pl.Boolean),
    ])


def _tirar_silver_posterior(fuente: str, dia) -> None:
    """Borra el silver de esa cadena con fecha posterior a la que se acaba de escribir.

    Un silver mas nuevo que su bronze solo puede venir de una captura que despues
    se descarto, y el emparejador coge **el silver mas reciente de cada cadena**:
    con uno huerfano por medio, trabaja con un catalogo que ya nadie considera
    bueno y no hay forma de notarlo.

    Paso el 18 de septiembre de 2026: se aparto el bronze de Alcampo por venir sin
    la rama Frescos, se rehizo el pipeline -- que escribio el silver bueno bajo la
    fecha del bronze, la del 17 -- y el emparejador siguio usando el silver roto
    del 18 que habia quedado ahi. El catalogo salio otra vez sin frescos.
    """
    carpeta = config.SILVER / f"fuente={fuente}"
    if not carpeta.exists():
        return
    for parte in sorted(carpeta.glob("fecha=*")):
        try:
            suya = date.fromisoformat(parte.name.split("=", 1)[1])
        except ValueError:
            continue
        if suya <= dia:
            continue
        for fichero in parte.glob("*"):
            with contextlib.suppress(OSError):
                fichero.unlink()
        try:
            parte.rmdir()
            print(f"  se tira el silver huerfano de {fuente} {parte.name}: "
                  f"su bronze ya no esta")
        except OSError:
            pass


def _serie(silver: pl.DataFrame, fecha_por_defecto: str) -> pl.DataFrame:
    """Las cinco columnas que forman la serie de precios, con su fecha."""
    columnas = ["fuente", "id_fuente", "precio_cent", "precio_unidad_cent",
                "unidad_canon"]
    tiene_fecha = "fecha" in silver.columns
    serie = silver.filter(pl.col("precio_comparable")).select(
        columnas + (["fecha"] if tiene_fecha else []))
    return serie.with_columns([
        (pl.col("fuente") + ":" + pl.col("id_fuente")).alias("producto_id"),
        (pl.col("fecha").cast(pl.Utf8) if tiene_fecha
         else pl.lit(fecha_por_defecto)).alias("fecha"),
    ])


def _derivados(serie: pl.DataFrame) -> None:
    """Recalcula los tres parquet que salen de la serie de precios."""
    enriquecido = derive.enriquecer(serie)
    write_parquet_file(enriquecido, config.GOLD / "precio_derivado.parquet")
    write_parquet_file(derive.resumen_producto(enriquecido),
                       config.GOLD / "resumen.parquet")
    write_parquet_file(derive.duracion_tipica_promo(enriquecido),
                       config.GOLD / "promos_por_cadena.parquet")


def rehacer_historico() -> int:
    """Reconstruye `gold/precio_diario.parquet` entero, dia a dia, desde bronze.

    Hasta el 18 de septiembre de 2026 no existia forma de hacer esto, y se vio
    probando la cadena entera sobre una copia limpia: con el mismo bronze de
    siempre (575.000 filas, trece dias en disco), el gold reconstruido salio con
    **dos dias y 52.000 filas**. La razon es que `main()` se queda a proposito
    con la instantanea mas reciente de cada cadena y la **anade** al historico;
    el historico, por tanto, solo vive en ese parquet. Bronze guardaba todos los
    dias y nadie los volvia a leer nunca.

    Eso convertia un fichero de gold en el unico ejemplar de la serie de
    precios: si se corrompe o se borra, se pierde la historia entera aunque el
    crudo y el bronze esten intactos. Con esto, gold vuelve a ser lo que decia
    ser, algo que se puede tirar y recalcular.
    """
    bronze = _cargar_bronze()
    if bronze is None or bronze.is_empty():
        print("no hay nada en bronze: no hay historico que rehacer.")
        return 1
    if "fecha" not in bronze.columns:
        print("el bronze no trae fecha: no se puede reconstruir por dias.")
        return 1

    bronze = bronze.with_columns(pl.col("fecha").cast(pl.Utf8))
    dias = sorted(bronze.select(["fuente", "fecha"]).unique()
                  .iter_rows(), key=lambda r: (r[1], r[0]))
    print(f"rehaciendo historico: {len(dias)} instantaneas de cadena y dia")

    trozos = []
    for fuente, dia in dias:
        trozo = bronze.filter((pl.col("fuente") == fuente) & (pl.col("fecha") == dia))
        try:
            serie = _serie(a_silver(trozo), dia)
        except Exception as exc:  # noqa: BLE001
            # Un dia ilegible no puede llevarse por delante los otros doce.
            print(f"  {fuente:10} {dia}  SALTADO: {exc}")
            continue
        print(f"  {fuente:10} {dia}  {len(serie)} filas")
        trozos.append(serie)

    if not trozos:
        print("ninguna instantanea se pudo reconstruir.")
        return 1
    entero = pl.concat(trozos, how="diagonal_relaxed").unique(
        subset=["fuente", "id_fuente", "fecha"], keep="last")
    write_parquet_file(entero, config.GOLD / "precio_diario.parquet")
    _derivados(entero)
    print(f"historico rehecho: {len(entero)} filas, "
          f"{entero['fecha'].n_unique()} dias, "
          f"{entero['fuente'].n_unique()} cadenas")
    return 0


def a_gold(silver_hoy: pl.DataFrame, fecha_snapshot=None) -> None:
    """Une el dia de hoy al historico y calcula los campos derivados."""
    hoy = str(fecha_snapshot or config.hoy_local())
    serie = _serie(silver_hoy, hoy)

    hist_path = config.GOLD / "precio_diario.parquet"
    if hist_path.exists():
        hist = pl.read_parquet(hist_path).with_columns(
            pl.col("fecha").cast(pl.Utf8))
        # Idempotencia por cadena y dia: reejecutar solo reemplaza lo que trae esta
        # pasada. Antes borraba TODA la fecha, asi que recalcular con una sola
        # cadena tiraba las instantaneas de las demas de ese mismo dia.
        nuevas = serie.select(["fuente", "fecha"]).unique()
        hist = hist.join(nuevas, on=["fuente", "fecha"], how="anti")
        serie = pl.concat([hist, serie], how="diagonal_relaxed")
    write_parquet_file(serie, hist_path)
    _derivados(serie)
    print(f"  gold: {len(serie)} filas de historico, "
          f"{serie['fecha'].n_unique()} dias acumulados")


def registrar_vistas() -> None:
    """Deja el warehouse listo para consultar con SQL desde cualquier sitio."""
    con = duckdb.connect(str(config.WAREHOUSE))
    silver_glob = config.SILVER / "**/*.parquet"
    if any(config.SILVER.rglob("*.parquet")):
        con.execute(f"CREATE OR REPLACE VIEW producto_historico AS "
                    f"SELECT * FROM read_parquet('{silver_glob}', union_by_name=true)")
        con.execute("""CREATE OR REPLACE VIEW producto AS
                    SELECT * EXCLUDE (_orden) FROM (
                        SELECT *, row_number() OVER (
                            PARTITION BY fuente, id_fuente
                            ORDER BY capturado_en DESC NULLS LAST
                        ) AS _orden
                        FROM producto_historico
                    ) WHERE _orden = 1""")
    for nombre, ruta in [
        ("precio_diario", config.GOLD / "precio_diario.parquet"),
        ("precio_derivado", config.GOLD / "precio_derivado.parquet"),
        ("resumen", config.GOLD / "resumen.parquet"),
    ]:
        if list(ruta.parent.glob(ruta.name)) or ruta.exists():
            con.execute(f"CREATE OR REPLACE VIEW {nombre} AS "
                        f"SELECT * FROM read_parquet('{ruta}', union_by_name=true)")
    con.close()


def main(*, publicar: bool = True) -> int:
    """La pasada del dia.

    **`publicar=False` es lo que usa el ciclo**: la publicacion tiene que ir **al final de todo
    lo que escribe gold** -- el emparejador incluido --, y eso no lo sabe la pasada sola. *Una
    pasada suelta, en cambio, si publica: es lo que hace `python -m projects.cesta.pipeline`.*
    """
    print("pipeline: cargando bronze...")
    bronze = _cargar_bronze()
    if bronze is None or bronze.is_empty():
        print("  no hay nada en bronze todavia: ningun colector ha escrito.")
        print("  prueba primero:  uv run python -m projects.cesta.collectors.mercadona")
        return 1
    print(f"  {len(bronze)} filas, {bronze['fuente'].n_unique()} cadenas")

    fecha_proceso = config.hoy_local()
    if "fecha" in bronze.columns:
        # Cada cadena aporta su instantanea MAS RECIENTE, no solo las de hoy.
        # Antes se filtraba por una unica fecha global: el dia que solo corria DIA,
        # las otras cuatro desaparecian de silver y de la busqueda, aunque su
        # bronze estuviera intacto en disco.
        bronze = bronze.with_columns(pl.col("fecha").cast(pl.Utf8))
        ultimas = bronze.group_by("fuente").agg(pl.col("fecha").max())
        hoy = bronze.join(ultimas, on=["fuente", "fecha"], how="semi")
        for fila in ultimas.sort("fuente").iter_rows(named=True):
            marca = "" if fila["fecha"] == str(fecha_proceso) else "  <- de otro dia"
            print(f"    {fila['fuente']:10} {fila['fecha']}{marca}")
    else:
        hoy = bronze

    silver = a_silver(hoy)
    for fuente in silver["fuente"].unique():
        trozo = silver.filter(pl.col("fuente") == fuente)
        dia = (date.fromisoformat(trozo["fecha"][0])
               if "fecha" in trozo.columns else fecha_proceso)
        write_parquet(trozo, "silver", fuente, day=dia)
        _tirar_silver_posterior(fuente, dia)
    print(f"  silver: {len(silver)} filas de {silver['fuente'].n_unique()} cadenas")

    a_gold(silver, fecha_proceso)
    registrar_vistas()
    # **Las cifras, aqui tambien.** `docs/CIFRAS.md` promete que lo reescribe la pasada del dia, y
    # solo lo hacia `run.py`: una pasada de `pipeline` a secas (o `--rehacer-historico`) dejaba el
    # documento una pasada por detras del gold, con la comprobacion de documentos dando avisos de
    # cifras caducadas por algo que no era un error de nadie. Medido el 27 de septiembre de 2026:
    # CIFRAS.md era de las 16:10 y `precio_diario.parquet` de las 17:16.
    #
    # Un fallo aqui **no puede tumbar el pipeline**: el dato ya esta escrito y las cifras son
    # documentacion.
    try:
        from projects.cesta import cifras
        cifras.main()
    except Exception as exc:  # noqa: BLE001
        print(f"  cifras: no se pudo reescribir CIFRAS.md ({type(exc).__name__}: {exc})")
    # **Y el sitio del material, que era lo unico que no se regeneraba solo.** `aprende.py` se
    # corria a mano, asi que lo que se lee en `/aprende` era tan fresco como la ultima vez que
    # alguien se acordara de generarlo: medido el 27 de septiembre de 2026, el sitio montado era
    # de **tres dias antes** que los documentos que sirve, con las tablas y los parrafos viejos.
    # El sitio no inventa contenido: lo convierte del markdown, asi que dejarlo atras es contar
    # algo que ya no es verdad.
    #
    # Como el resto de lo que va al final: **un fallo aqui no puede tumbar el pipeline** -- el
    # dato ya esta escrito y el material es documentacion --. Y si falta el extra de docs,
    # `genera` lo dice y devuelve -1 en vez de reventar (`aprende.FALTA_EXTRA`).
    try:
        from plataforma import aprende
        aprende.main([])
    except Exception as exc:  # noqa: BLE001
        print(f"  material: no se pudo regenerar /aprende ({type(exc).__name__}: {exc})")
    # **Y se publica lo que se acaba de escribir.** Sin esto, gold se reescribe en su sitio y el
    # puntero se queda en la ultima version que alguien publico a proposito: el 13 de octubre de
    # 2026 eso dejo `data/gold` en el 8 y `actual.json` en el 7, y `/api/estado` lo declaro
    # incoherente -- con razon. Adoptar los ficheros sueltos es justo el caso para el que
    # `publicar()` acepta no recibir marcos.
    #
    # Va al final y con su `try`, como el resto de esta cola: si no se puede publicar, el dato ya
    # esta escrito y el puntero se queda donde estaba, que deja la incoherencia **visible**.
    if not publicar:
        # **El ciclo publica al final.** *Aqui no: el emparejador todavia no ha corrido, y publicar
        # antes deja fuera `grupos.parquet` y `enlaces.parquet`.*
        print("  publicacion: se deja para el final del ciclo")
        print("pipeline: hecho")
        return 0
    try:
        from core import publicacion

        publicacion.publicar()
    except Exception as exc:  # noqa: BLE001
        print(f"  publicacion: no se pudo publicar ({type(exc).__name__}: {exc})")
        # **Y se dice en el codigo de salida.** *El dato esta escrito y el puntero se queda donde
        # estaba, que deja la incoherencia **visible** en `/api/estado` -- pero solo si alguien la
        # mira.* Devolver 0 aqui era decir que el dia estaba hecho cuando **la version del dia no se
        # publico**: medido el 13 de octubre de 2026, este `try` se tragaba el fallo y `main()`
        # devolvia 0. *Y quien llama, `run.py`, tampoco miraba el resultado.* Las dos cosas arregladas.
        print("pipeline: el dato esta escrito, pero la version NO se ha publicado")
        return 1
    print("pipeline: hecho")
    return 0


if __name__ == "__main__":
    import sys
    if "--rehacer-historico" in sys.argv:
        raise SystemExit(rehacer_historico())
    raise SystemExit(main())