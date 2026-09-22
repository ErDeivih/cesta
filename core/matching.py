"""Emparejar el mismo producto entre cadenas cuando no hay codigo de barras.

Tres niveles, de mas seguro a mas util:

  identico    mismo EAN. Sin discusion, pero solo cubre marca nacional: un
              Hacendado y un Dia Vegecampo nunca compartiran codigo aunque sean
              el mismo litro de leche, y esa es justo la comparacion que
              interesa.
  equivalente mismo tipo de producto y mismo formato, distinta marca. Es lo que
              construye la cesta comparable.
  calidad     dentro de un grupo equivalente, ordenar por composicion.

El emparejador por nombre se mide, no se opina: los pares que YA sabemos ciertos
por EAN se usan como respuestas correctas, escondiendo el EAN al algoritmo.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from core.normalize import nombre_limpio

# Palabras que no distinguen un producto de otro y solo generan parecido falso.
RUIDO = {
    "de", "del", "la", "el", "los", "las", "con", "sin", "y", "e", "al", "a",
    "en", "para", "por", "un", "una", "su", "lo",
    "producto", "articulo", "unidad", "unidades", "aprox", "aproximado",
    "peso", "aproximadamente", "surtido", "seleccion", "calidad", "extra",
    "nuevo", "nueva", "clasico", "clasica", "original", "especial",
}

# Un numero suelto suele ser grado, porcentaje o formato ya extraido.
_SOLO_DIGITOS = re.compile(r"^\d+$")


def raiz(palabra: str) -> str:
    """Plural fuera. 'alubias'->'alubia', 'lentejas'->'lenteja'.

    Sin esto, "Alubia morada Luengo" de Carrefour y "Alubias moradas Luengo" de
    DIA no comparten NI UNA palabra, y son el mismo bote. Es el fallo mas comun
    entre cadenas: cada una escribe el producto en singular o en plural.
    """
    if len(palabra) > 4 and palabra.endswith(("es", "as", "os")):
        return palabra[:-1]
    if len(palabra) > 3 and palabra.endswith("s"):
        return palabra[:-1]
    return palabra


def tokens_sin_marca(nombre: str, marca: str | None = None) -> frozenset[str]:
    """Las palabras del nombre quitando la marca. Es la comparacion entre marcas.

    "Leche entera Hacendado" y "Leche entera Carrefour" no comparten la palabra
    que mas pesa, precisamente porque son el mismo producto de dos marcas
    distintas. Quitando la marca queda lo que de verdad describe el producto.
    """
    limpio = nombre_limpio(nombre or "", marca or None)
    return frozenset(
        raiz(p) for p in limpio.split()
        if len(p) > 2 and p not in RUIDO and not _SOLO_DIGITOS.match(p))


def tokens(nombre: str, marca: str | None = None) -> frozenset[str]:
    """Palabras significativas, con la marca incluida como una palabra mas.

    La marca NO se quita. Quitarla dejaba sin ninguna palabra a productos cuyo
    nombre es solo la marca y el tamano ("Fairy 654 ml" en DIA), y esos quedaban
    fuera de todo grupo. Como palabra, en cambio, la marca es de las que mas
    distinguen, y el IDF ya se encarga de darle el peso que merece.
    """
    limpio = nombre_limpio(nombre or "", None)
    palabras = list(limpio.split())
    if marca:
        palabras.extend(nombre_limpio(str(marca), None).split())
    return frozenset(
        raiz(p) for p in palabras
        if len(p) > 2 and p not in RUIDO and not _SOLO_DIGITOS.match(p)
    )


def trigramas(nombre: str, marca: str | None = None) -> frozenset[str]:
    """Trozos de tres letras del nombre, sin espacios.

    Existe por un fallo concreto: Carrefour escribe "Galleta chocowafer Milka" y
    DIA "Galletas choco wafer chocolate con leche Milka". Como palabras no
    comparten casi nada; como trozos de tres letras son casi el mismo texto. Lo
    mismo pasa con "Tosta Rica" frente a "Tostarica". Partir por espacios da por
    hecho que las dos cadenas ponen el espacio en el mismo sitio, y no lo hacen.
    """
    t = nombre_limpio(nombre or "", None)
    if marca:
        t += " " + nombre_limpio(str(marca), None)
    t = t.replace(" ", "")
    if len(t) < 3:
        return frozenset()
    return frozenset(t[i:i + 3] for i in range(len(t) - 2))


# Cuanto valen las letras frente a las palabras. Multiplica el Dice de trigramas,
# y el resultado compite con el parecido por palabras: gana el mayor.
#
# Se bajo a 0,80 el 22 de septiembre de 2026 persiguiendo los grupos por familia
# ("todas las cervezas" en un mismo grupo), y **se volvio a 0,85 midiendo**. Los
# numeros, sobre el mismo catalogo:
#
#                           aciertos   enlaces   >200 %   productos comparables
#     0,85 (lo que vale)      65 %     22.702      448          23.047
#     0,80 (probado)          64 %     22.679      449          23.039
#
# Un punto de acierto y 23 enlaces, para nada: la tasa de grupos anchos hasta
# empeora. El motivo es aritmetico y conviene tenerlo escrito, porque el error es
# facil de repetir: para que un puente lo sostenga el trigrama **estando el liston
# en 0,55**, su Dice tiene que ser al menos 0,55 / 0,85 = 0,647; bajando a 0,80 el
# corte pasa a 0,6875, asi que solo caen los puentes que estan en esa banda
# estrecha, que son pocos. Bajar el peso **no apaga el canal**, solo lo desplaza
# un poco, y de paso se lleva por delante aciertos que si dependian de el.
#
# El caso que justifica los trigramas y que hay que seguir protegiendo:
#     "Galleta chocowafer Milka"  <->  "Galletas choco wafer Milka"
#     "Tosta Rica"  <->  "Tostarica"
#
# Lo que de verdad cierra los puentes no es bajar esto: es que un enlace flojo no
# pueda pegar dos grupos (`UMBRAL_UNION`, que ya esta) y, mas alla, un freno a
# nivel de grupo. Ver docs/DIAGNOSTICO-MATCHING.md §16.
PESO_TRIGRAMAS = 0.85


def dice(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def idf(documentos: list[frozenset[str]]) -> dict[str, float]:
    """Peso de cada palabra: 'piquillo' distingue mucho mas que 'leche'."""
    n = len(documentos) or 1
    frecuencia = Counter()
    for d in documentos:
        frecuencia.update(d)
    return {p: math.log(n / (1 + c)) + 1.0 for p, c in frecuencia.items()}


def parecido(a: frozenset[str], b: frozenset[str], pesos: dict[str, float]) -> float:
    """Dice ponderado por IDF. 1.0 = las mismas palabras significativas.

    Dice y no Jaccard porque los nombres tienen longitudes muy distintas segun la
    cadena: "Fairy 654 ml" contra "Lavavajillas a mano ultra poder Fairy 654 ml".
    Jaccard castiga esa asimetria hasta hacerla indistinguible del ruido; Dice
    reconoce que todo lo que dice el corto lo dice tambien el largo.

    Esta es la version con un diccionario de pesos comun a todo. La que se usa de
    verdad al emparejar es `parecido_de_par`, que ademas mira el pasillo.
    """
    if not a or not b:
        return 0.0
    comun = sum(pesos.get(p, 1.0) for p in a & b)
    total = sum(pesos.get(p, 1.0) for p in a) + sum(pesos.get(p, 1.0) for p in b)
    return 2 * comun / total if total else 0.0


def pesos_por_pasillo(docs: list[frozenset[str]],
                      secciones: list[str | None]) -> tuple[list[dict], list[float]]:
    """El peso de cada palabra **en cada producto**: el menor entre el catalogo y su pasillo.

    Se escribio el 22 de septiembre de 2026 para arreglar los grupos por familia
    ("todas las cervezas" en un grupo de 97 productos) y **no se usa**, porque la
    medicion dijo que no arregla nada: con esto el grupo mayor baja de 97 a 80 y
    la tasa de grupos anchos hasta empeora un poco (6,28 % a 6,38 %). Se queda
    aqui, con sus pruebas, porque la idea es buena y el motivo de que no funcione
    esta medido: los puentes que sostienen esos grupos los abre el **canal de
    trigramas**, no el de palabras. Ver `enlaces.parejo`.

    Lo que hace, cuando se use: dentro de un pasillo, "cerveza" sale en cientos de
    productos y se queda sin peso, que es lo correcto; y "leffe" o "rambler"
    siguen pesando igual, porque tambien son raras en su pasillo. Devuelve, por
    producto, su vector de pesos y el total ya sumado (que hace falta en el
    denominador del Dice).
    """
    globales = idf(docs)
    por_seccion: dict[str, list[frozenset[str]]] = defaultdict(list)
    for s, d in zip(secciones, docs, strict=True):
        por_seccion[s or "?"].append(d)
    locales = {s: idf(lista) for s, lista in por_seccion.items()}
    vectores: list[dict] = []
    totales: list[float] = []
    for s, d in zip(secciones, docs, strict=True):
        local = locales[s or "?"]
        v = {p: min(globales.get(p, 1.0), local.get(p, 1.0)) for p in d}
        vectores.append(v)
        totales.append(sum(v.values()))
    return vectores, totales


def parecido_de_par(vi: dict, vj: dict, ti: float, tj: float) -> float:
    """El Dice ponderado de dos productos ya con sus vectores de pesos.

    La palabra compartida cuenta por el **menor** de los dos pesos: si "cerveza"
    pesa poco en un pasillo, no puede servir para unir dos productos por el otro.
    Compañero de `pesos_por_pasillo`; hoy no se usa al emparejar, por lo mismo.
    """
    if not vi or not vj:
        return 0.0
    if len(vi) > len(vj):
        vi, vj = vj, vi
    comun = 0.0
    for p, w in vi.items():
        w2 = vj.get(p)
        if w2 is not None:
            comun += w if w < w2 else w2
    total = ti + tj
    return 2 * comun / total if total else 0.0


def bloque(cantidad: float | None, unidad: str | None) -> tuple:
    """Clave de bloqueo: solo se comparan productos del mismo formato.

    Sin esto habria que comparar 34.000 productos contra 34.000. Y ademas es
    correcto: un litro de leche no es equivalente a un brik de 200 ml, por mucho
    que el nombre sea identico.
    """
    if cantidad is None or not unidad:
        return ("?",)
    return (unidad, round(float(cantidad), 3))


class Union:
    """Union-find. Un grupo es un conjunto de productos enlazados entre si."""

    def __init__(self) -> None:
        self.padre: dict[int, int] = {}

    def raiz_de(self, x: int) -> int:
        self.padre.setdefault(x, x)
        while self.padre[x] != x:
            self.padre[x] = self.padre[self.padre[x]]
            x = self.padre[x]
        return x

    def une(self, a: int, b: int) -> None:
        ra, rb = self.raiz_de(a), self.raiz_de(b)
        if ra != rb:
            self.padre[rb] = ra


def _ean(valor) -> str | None:
    if valor is None:
        return None
    d = re.sub(r"\D", "", str(valor)).lstrip("0")
    return d if len(d) >= 8 else None


# Segunda pasada, para los productos que el bloqueo por formato no puede juntar.
# Medido el 8 sep sobre los 1.767 pares ciertos: 579 caen en bloques distintos, y
# no por poco -- 334 porque a alguno de los dos no se le pudo leer el formato, 274
# porque una cadena lo vende por unidades y la otra al peso, y 239 porque los
# numeros no coinciden (un pack frente a la pieza suelta). Ahi el formato no puede
# decidir, asi que decide el nombre, pero con un liston mucho mas alto: si no se
# puede comprobar el tamano, mas vale exigir que el nombre sea casi el mismo.
UMBRAL_SIN_FORMATO = 0.82
# Palabras lo bastante raras como para que valga la pena mirar quien mas las usa.
# "leche" la dicen miles de productos y no sirve para buscar; "chocowafer", si.
MIN_IDF_ANCLA = 4.0
MAX_CANDIDATOS_POR_PALABRA = 200


# Solo estas seis columnas se usan para emparejar. El resto del catalogo (hoy 34
# columnas: sellos, nutricion, certificados, descripcion...) no interviene.
#
# Pasar los diccionarios completos costaba tiempo de verdad. El emparejador
# recorre 16,7 millones de pares candidatos y en cada uno hace varias busquedas
# en el diccionario de las dos filas. Con 17 columnas tardaba 79 s; al crecer el
# contrato a 34, el mismo trabajo se fue por encima de 115 s sin que cambiara ni
# una linea del algoritmo: diccionarios mas grandes, peor localidad de cache.
# Quedarse con lo justo devuelve el tiempo y, sobre todo, deja de empeorar cada
# vez que se conquista un dato nuevo a una cadena.
# Unidades cuyo precio por unidad significa lo mismo en dos cadenas. "ud" no
# esta, y no por descuido: cada cadena cuenta una cosa distinta con esa palabra
# (Mercadona llama "1 ud" a un paquete de seis rollos y publica el precio por
# rollo). Medido el 7 de septiembre sobre 4.780 grupos: en kg y litro la
# diferencia mediana entre la mas barata y la mas cara es del 12 %; en "ud", del
# 24 %, con 128 de sus 550 grupos dando diferencias imposibles.
UNIDADES_FIABLES = ("kg", "l", "m")

CAMPOS_PARA_EMPAREJAR = ("fuente", "nombre", "marca", "cantidad", "unidad_canon", "ean",
                         "precio_unidad_cent", "precio_comparable")

# Un par cuyo precio por unidad se lleva mas de 30 veces no es el mismo producto,
# ni siquiera entre marcas. El 30 no es inventado: es `FACTOR_INCREIBLE`, el
# umbral con el que el proyecto YA marca un grupo como dudoso y se niega a dar
# cifra de ahorro (core/comparacion.py, docs/PRECIO-POR-UNIDAD.md:114-141). Por
# debajo de 30 el ahorro es real -- hay 28x comprobados -- asi que vetar antes
# seria borrar aciertos: el plan nuevo proponia cortar al 60 %, y medido el 22 de
# septiembre eso habria marcado 3.191 de 17.789 enlaces, o sea la mitad del valor
# del comparador. Este veto es **condicional**: solo actua cuando los dos precios
# son comparables y el formato es de fiar, y nunca sobre un par con el mismo EAN.
FACTOR_PRECIO_IMPOSIBLE = 30.0
PRECIO_MINIMO_CENT = 5


def precio_imposible(a: dict, b: dict) -> bool:
    """¿Los dos precios por unidad se llevan tanto que no pueden ser el mismo producto?

    Todo lo que hace falta para que esta pregunta tenga sentido se comprueba
    antes de contestarla: misma unidad (comparar EUR/kg con EUR/lavado no dice
    nada), precio en los dos lados, que la cadena no lo haya marcado como no
    comparable, y que el formato no sea un relleno.
    """
    ua, ub = a.get("unidad_canon"), b.get("unidad_canon")
    if not ua or ua != ub or ua not in UNIDADES_FIABLES:
        return False
    if a.get("precio_comparable") is False or b.get("precio_comparable") is False:
        return False
    pa, pb = a.get("precio_unidad_cent"), b.get("precio_unidad_cent")
    if not pa or not pb or min(pa, pb) < PRECIO_MINIMO_CENT:
        return False
    return max(pa, pb) / min(pa, pb) > FACTOR_PRECIO_IMPOSIBLE


def adelgaza(filas: list[dict]) -> list[dict]:
    """Las filas con solo lo que mira el emparejador, en el mismo orden."""
    return [{c: f.get(c) for c in CAMPOS_PARA_EMPAREJAR} for f in filas]


def nivel(a: dict, b: dict) -> str:
    """identico | equivalente. La distincion que pedia el proyecto.

    Mismo EAN es el mismo producto y no se discute. Distinta marca con el mismo
    formato es el equivalente de otra marca, que es justo lo que hay que comparar
    cuando las cadenas venden marca blanca y no comparten codigo de barras.

    La marca decide **solo cuando no hay codigos que comparar**. Antes decidia
    siempre, y eso hacia que el propio codigo llamara "identico" a dos productos
    con codigos de barras distintos por el hecho de compartir marca: medido el 22
    de septiembre, de los 1.475 enlaces marcados 'identico' con EAN en los dos
    lados, solo 1.033 (el 70 %) compartian codigo. La etiqueta mentia en el 30 %
    de los casos comprobables, y quien la leyera para decidir se equivocaba.
    """
    ea, eb = _ean(a.get("ean")), _ean(b.get("ean"))
    if ea and eb:
        return "identico" if ea == eb else "equivalente"
    ma, mb = _marca(a.get("marca")), _marca(b.get("marca"))
    return "identico" if ma and ma == mb else "equivalente"


def _asignacion_1a1(candidatos: list[tuple[int, int, float]],
                    umbral: float) -> list[tuple[int, int, float]]:
    """Asignacion optima 1-a-1 entre dos listas de productos (algoritmo hungaro).

    `candidatos` son (izquierda, derecha, puntuacion) de DOS cadenas distintas
    dentro de un mismo bloque. Devuelve el subconjunto que maximiza la suma de
    puntuaciones sin repetir ningun producto de ningun lado.

    Es el cambio que mas arregla del emparejador, y por una razon tonta: con "el
    mejor de cada uno" (lo que habia hasta el 22 de septiembre) cada producto
    elige por su cuenta, asi que dos productos de Mercadona pueden elegir al
    mismo de Lidl y uno de los dos se queda sin pareja **teniendo una igual de
    buena al lado**. Medido ese dia: 137 de los 701 pares ciertos que se
    escapaban se perdian exactamente asi, el 20 %. Con componentes conexas el
    problema es el contrario (todo se junta en un grupo enorme); con eleccion
    mutua, este. La asignacion optima resuelve los dos: nadie roba la pareja de
    nadie y nadie se queda con dos.

    El hungaro es O(n^3) y aqui n es el tamano de un bloque por par de cadenas,
    casi siempre menos de cien, asi que no hace falta ni numpy ni scipy -- dos
    dependencias de decenas de megas para esto -- y se escribe a mano y se prueba
    con casos de respuesta conocida (ver `tests/test_matching.py`).
    """
    izquierda = sorted({i for i, _j, _s in candidatos})
    derecha = sorted({j for _i, j, _s in candidatos})
    if not izquierda or not derecha:
        return []
    # El algoritmo pide filas <= columnas; si no, se da la vuelta.
    vuelta = len(izquierda) > len(derecha)
    if vuelta:
        izquierda, derecha = derecha, izquierda
        candidatos = [(j, i, s) for i, j, s in candidatos]

    fila = {x: k for k, x in enumerate(izquierda)}
    columna = {x: k for k, x in enumerate(derecha)}
    n, m = len(izquierda), len(derecha)
    # Lo que se maximiza es la **ganancia por encima del liston**, no el parecido
    # a secas. Con el parecido a secas el reparto prefiere dos parejas mediocres
    # (0,56 + 0,56 = 1,12) a una buena y un hueco (0,90). Medido el 22 de
    # septiembre al probarlo: 23 % mas de enlaces y 694 grupos comparables menos,
    # porque los pares flojos desplazaban a los buenos y ademas fundian grupos
    # entre si. Con la ganancia, un par de 0,90 vale 0,35 y dos de 0,56 valen
    # 0,02: gana el bueno, que es lo que se quiere.
    score = [[0.0] * m for _ in range(n)]
    for i, j, s in candidatos:
        score[fila[i]][columna[j]] = max(0.0, s - umbral)
    bruto = {(fila[i], columna[j]): s for i, j, s in candidatos}

    # Hungaro con potenciales (Kuhn-Munkres). Se maximiza, asi que el coste es
    # -score, y un hueco sin candidato vale 0: nunca compensa ocupar con un cero
    # una columna que otro podia usar con nota.
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    pareja = [0] * (m + 1)          # que fila ocupa cada columna (1-based)
    camino = [0] * (m + 1)
    for i in range(1, n + 1):
        pareja[0] = i
        j0 = 0
        minv = [float("inf")] * (m + 1)
        usado = [False] * (m + 1)
        while True:
            usado[j0] = True
            i0 = pareja[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, m + 1):
                if usado[j]:
                    continue
                cur = -score[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    camino[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(m + 1):
                if usado[j]:
                    u[pareja[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if pareja[j0] == 0:
                break
        while j0:
            j1 = camino[j0]
            pareja[j0] = pareja[j1]
            j0 = j1

    salida = []
    for j in range(1, m + 1):
        if pareja[j] == 0:
            continue
        a, b = izquierda[pareja[j] - 1], derecha[j - 1]
        s = bruto.get((pareja[j] - 1, j - 1))
        if s is not None and s >= umbral:
            salida.append((b, a, s) if vuelta else (a, b, s))
    return salida


def enlaces(filas_completas: list[dict], umbral: float = 0.55,
            usar_ean: bool = True,
            usar_vectores: bool = True) -> list[tuple[int, int, float, str]]:
    """Pares (i, j, parecido, motivo) del mismo producto en cadenas distintas.

    Dos pasos, y los dos importan:

    1. **Quien puede ser pareja de quien** (bloqueo): mismo formato y alguna
       palabra en comun. Comparar los 52.000 productos entre si serian 1.400
       millones de pares.
    2. **Quien se queda con quien** (asignacion): dentro de cada bloque y de cada
       par de cadenas, el reparto 1-a-1 que maximiza la suma de parecidos, con el
       algoritmo hungaro. Ver `_asignacion_1a1`.

    `filas` necesita: fuente, nombre, marca, cantidad, unidad_canon, ean.
    Con `usar_ean=False` se ignora el codigo de barras. Es el modo con el que se
    mide el emparejador contra los pares que ya sabemos ciertos.

    Lo primero que hace es quedarse con esas seis columnas y tirar el resto: ver
    `adelgaza`. El orden y los indices no cambian, asi que los pares que devuelve
    siguen apuntando a las filas originales.
    """
    filas = adelgaza(filas_completas)
    docs = [tokens(f.get("nombre") or "", f.get("marca")) for f in filas]
    # Los mismos nombres SIN la marca. Hacen falta para lo que este proyecto
    # existe: comparar el Hacendado con el Carrefour. Con la marca dentro, dos
    # productos identicos de marca distinta nunca llegan al liston, porque
    # justo la palabra que mas pesa es la que no comparten. Solo se usan cuando
    # el formato ya coincide, que es lo que impide que esto junte cualquier cosa.
    sin_marca = [tokens_sin_marca(f.get("nombre") or "", f.get("marca"))
                 for f in filas]
    tris = [trigramas(f.get("nombre") or "", f.get("marca")) for f in filas]
    pesos = idf(docs)
    pesos_sin_marca = idf(sin_marca)

    def equivalente(i: int, j: int) -> float:
        """Parecido ignorando la marca. Solo vale dentro del mismo formato."""
        return parecido(sin_marca[i], sin_marca[j], pesos_sin_marca)

    def parejo(i: int, j: int) -> float:
        """Lo que mas se parezcan por palabras o por letras, lo que gane.

        Las palabras distinguen mejor cuando las dos cadenas escriben igual; las
        letras salvan los casos en que una junta lo que la otra separa
        ("Galleta chocowafer Milka" contra "Galletas choco wafer Milka", "Tosta
        Rica" contra "Tostarica"). Por eso las letras se descuentan: tambien
        acercan cosas que solo se parecen por fuera.

        **Este max() es el que sostiene los grupos por familia**, y el numero que
        lo gobierna es PESO_TRIGRAMAS. Ver su comentario.
        """
        return max(parecido(docs[i], docs[j], pesos),
                   PESO_TRIGRAMAS * dice(tris[i], tris[j]))

    salida: list[tuple[int, int, float, str]] = []
    if usar_ean:
        por_ean: dict[str, list[int]] = defaultdict(list)
        for i, f in enumerate(filas):
            e = _ean(f.get("ean"))
            if e:
                por_ean[e].append(i)
        for indices in por_ean.values():
            for j in indices[1:]:
                salida.append((indices[0], j, 1.0, "ean"))

    # Candidatos agrupados por (bloque, cadena A, cadena B) con A < B, que es
    # justo la unidad sobre la que se resuelve la asignacion: un reparto 1-a-1
    # por cada par de cadenas dentro de cada formato.
    canales: dict[str, dict[tuple, list[tuple[int, int, float]]]] = {
        "marca": defaultdict(list), "equivalente": defaultdict(list),
        "vector": defaultdict(list)}
    por_bloque: dict[tuple, list[int]] = defaultdict(list)
    for i, f in enumerate(filas):
        if docs[i]:
            por_bloque[bloque(f.get("cantidad"), f.get("unidad_canon"))].append(i)

    for clave, indices in por_bloque.items():
        if clave == ("?",) or len(indices) < 2:
            continue
        candidatos: dict[str, list[int]] = defaultdict(list)
        for i in indices:
            for p in docs[i]:
                candidatos[p].append(i)
        vistos: set[tuple[int, int]] = set()
        for lista in candidatos.values():
            if len(lista) > 400:      # palabra demasiado comun en este bloque
                continue
            for pos, i in enumerate(lista):
                for j in lista[pos + 1:]:
                    if filas[i]["fuente"] == filas[j]["fuente"]:
                        continue
                    par = (i, j) if i < j else (j, i)
                    if par in vistos:
                        continue
                    vistos.add(par)
                    # Se guarda el candidato, no la decision: la decision la
                    # toma la asignacion optima, junta y por pares de cadenas.
                    # Dos canales separados, no uno. Con uno solo, el mejor
                    # candidato de un Hacendado pasaba a ser el Carrefour
                    # equivalente y se perdia el Hacendado identico de la otra
                    # cadena: medido el 7 de septiembre, el acierto caia del
                    # 53 % al 43 %. Cada canal reparte por su cuenta.
                    x, y = i, j
                    if filas[x]["fuente"] > filas[y]["fuente"]:
                        x, y = y, x
                    # Veto de precio, condicional (ver `precio_imposible`): un
                    # bote de 1 L a 2 EUR no es el de 400 mL a 3, ni pareciendose
                    # el nombre. Nunca se aplica a los pares con el mismo EAN: ahi
                    # el codigo manda y la diferencia de precio es un hallazgo.
                    if precio_imposible(filas[x], filas[y]):
                        continue
                    grupo = (clave, filas[x]["fuente"], filas[y]["fuente"])
                    s = parejo(x, y)
                    if s >= umbral:
                        canales["marca"][grupo].append((x, y, s))
                    if _marca(filas[x].get("marca")) != _marca(filas[y].get("marca")):
                        e = equivalente(x, y)
                        if e >= umbral:
                            canales["equivalente"][grupo].append((x, y, e))

    # Canal 3: los embeddings (Fase 3). **Proponen, no deciden.** Un par que solo
    # los vectores acercan entra por el mismo reparto 1-a-1 y pasa por los mismos
    # frenos que los demas; va el ultimo, asi que lo que el nombre ya sostiene
    # manda. Medido en `docs/DIAGNOSTICO-MATCHING.md` §22: precision 0,90 con
    # recall 0,89 en el umbral 0,76, contra los negativos dificiles.
    #
    # Se apaga con `usar_vectores=False`, y ese interruptor existe por un motivo
    # concreto: `--medir` llama con `usar_ean=False` para medir el emparejador por
    # nombre, asi que si esto fuera con `usar_ean` **la medida nunca podria ver el
    # canal nuevo**, y no habria forma de contestar la unica pregunta que importa:
    # ¿sube o no sube el recall? Con el interruptor aparte, se mide con y sin.
    #
    # Si no hay vectores cacheados, esto no hace nada y el emparejador funciona
    # igual que antes: la Fase 3 es una mejora, no un requisito.
    if usar_vectores:
        from core import embeddings

        vectores = embeddings.carga()
        if vectores:
            for i, j, s in embeddings.candidatos(filas_completas, vectores):
                x, y = i, j
                if filas[x]["fuente"] > filas[y]["fuente"]:
                    x, y = y, x
                if precio_imposible(filas[x], filas[y]):
                    continue
                clave = bloque(filas[x].get("cantidad"), filas[x].get("unidad_canon"))
                canales["vector"][(clave, filas[x]["fuente"],
                                   filas[y]["fuente"])].append((x, y, s))

    emitidos: set[tuple[int, int]] = set()
    ocupados_todos: set[tuple[int, str]] = set()

    def emitir(x, y, s, ocupados):
        """Acepta un par si ninguno de los dos ya tiene pareja en esa cadena.

        `ocupados` es **por canal**, no global, y eso es a proposito: un producto
        puede tener a la vez su identico en la otra cadena y su equivalente de
        otra marca. Es lo que el proyecto midio el 7 de septiembre -- con una
        sola eleccion el acierto caia del 53 % al 43 % -- y lo que fija
        `test_un_equivalente_no_puede_robarle_el_sitio_al_identico`.
        """
        if (x, y) in emitidos:
            return
        if (x, filas[y]["fuente"]) in ocupados or (y, filas[x]["fuente"]) in ocupados:
            return
        emitidos.add((x, y))
        ocupados.add((x, filas[y]["fuente"]))
        ocupados.add((y, filas[x]["fuente"]))
        ocupados_todos.add((x, filas[y]["fuente"]))
        ocupados_todos.add((y, filas[x]["fuente"]))
        if x > y:
            x, y = y, x
        salida.append((x, y, s, nivel(filas[x], filas[y])))

    # Canal 1 (con la marca dentro) y canal 2 (sin la marca, entre marcas
    # distintas). Cada canal reparte por su cuenta; lo que ya esta emitido no se
    # repite, pero un producto si puede salir en los dos.
    for canal in ("marca", "equivalente", "vector"):
        ocupados: set[tuple[int, str]] = set()
        # `sorted` no sobra: iterar un diccionario cuyas claves llevan texto
        # depende del hash seed del proceso. Pero **no basta**: medido el 22 de
        # septiembre, con esto puesto, dos procesos del mismo dia siguen dando
        # 22.702 y 22.705 enlaces (3 de 22.700, un 0,013 %). No cambian los
        # grupos ni las metricas (7.923 contra 7.925), asi que no se ha seguido
        # cazando, pero queda anotado: el plan pide medir la estabilidad entre
        # ejecuciones y, mientras quede baile, la medida tiene un suelo de ruido.
        for _grupo, candidatos in sorted(canales[canal].items()):
            for x, y, s in _asignacion_1a1(candidatos, umbral):
                emitir(x, y, s, ocupados)

    # Segunda pasada: sin bloque y con el liston alto, para lo que el formato no
    # puede juntar (un pack frente a la pieza suelta, una cadena que no publica
    # tamano). Solo se miran productos que comparten alguna palabra rara, y solo
    # si las unidades no se contradicen: comparar un kilo con un litro no lleva
    # a nada.
    ancla: dict[str, list[int]] = defaultdict(list)
    for i, doc in enumerate(docs):
        for p in doc:
            if pesos.get(p, 0.0) >= MIN_IDF_ANCLA:
                ancla[p].append(i)
    sueltos: dict[tuple, list[tuple[int, int, float]]] = defaultdict(list)
    vistos_sueltos: set[tuple[int, int]] = set()
    for lista in ancla.values():
        if len(lista) > MAX_CANDIDATOS_POR_PALABRA:
            continue
        for pos, i in enumerate(lista):
            for j in lista[pos + 1:]:
                if filas[i]["fuente"] == filas[j]["fuente"]:
                    continue
                par = (i, j) if i < j else (j, i)
                if par in vistos_sueltos:
                    continue
                vistos_sueltos.add(par)
                ui, uj = filas[i].get("unidad_canon"), filas[j].get("unidad_canon")
                if ui and uj and ui != uj:
                    continue
                s = parejo(i, j)
                if s < UMBRAL_SIN_FORMATO:
                    continue
                x, y = i, j
                if filas[x]["fuente"] > filas[y]["fuente"]:
                    x, y = y, x
                if precio_imposible(filas[x], filas[y]):
                    continue
                sueltos[(None, filas[x]["fuente"], filas[y]["fuente"])].append(
                    (x, y, s))
    for _grupo, candidatos in sorted(sueltos.items()):
        # Un enlace con formato comprobado siempre gana a uno sin comprobar,
        # aunque el nombre del segundo se parezca mas: por eso esta pasada va
        # despues y respeta lo que ya esta ocupado.
        for x, y, s in _asignacion_1a1(candidatos, UMBRAL_SIN_FORMATO):
            emitir(x, y, s, ocupados_todos)
    return salida


def _marca(valor) -> str:
    return nombre_limpio(str(valor or ""), None).strip()


# Un enlace por debajo de esto todavia puede meter a un producto suelto en un
# grupo, pero **no puede pegar dos grupos que ya existen**. Es el freno contra el
# grupo monstruo.
#
# Por que hace falta. Un grupo es lo que queda conectado, y eso se propaga. Y no
# se propaga por muchos enlaces flojos, sino por **uno solo**: mirando por dentro
# el grupo 92 (97 productos, 181 enlaces internos), el parecido mediano es 1,00 y
# lo que lo sostenia eran un par de puentes de 0,55:
#
#     0.55  MAHOU Cerveza tostada 0,0% lata      <-> Cerveza tostada Saer Brau 0,0
#     0.55  Cerveza tostada Saer Brau 0,0        <-> Cerveza tostada 0,0% Mahou
#     0.58  Agua mineral con gas Perrier 1 l     <-> Agua mineral con gas Vichy 1 L
#     0.66  SAN PELLEGRINO agua con gas 1 l      <-> Agua mineral Font Vella 1 l
#
# Cada puente une dos racimos correctos por su equivalente de marca blanca, y asi
# acaban juntos "todas las cervezas tostadas" o "todas las aguas".
#
# Se probaron dos reglas, medidas sobre los 22.702 enlaces del 22 de septiembre
# (grupo mayor / grupos comparables / productos comparables / grupos de 5 cadenas
# / error demostrable / grupos con mas del 200 % / calidad asignada):
#
#   sin freno                  329 / 6.589 / 23.049 / 271 / 935 / 7,5 % / 14.610
#   A: 0,80 no pega grupos      97 / 7.925 / 23.047 / 201 / 900 / 6,4 % / 12.996
#   B: 0,80 flojo solo sueltos  85 / 8.499 / 20.176 /  69 / 422 / 3,7 % /  5.546
#
# B frena el error a la mitad y los grupos anchos a la mitad, **pero hunde la
# letra de calidad de 12.996 productos a 5.546**, porque casi todos los grupos se
# quedan en pareja y la letra pide tres comparables. La letra de calidad es una
# funcion que se usa: no se cambia por una mejora en un indicador indirecto. Se
# queda A.
UMBRAL_UNION = 0.80


# Un enlace flojo tampoco puede **crear un grupo ancho**.
#
# Es el freno que sale de la medicion del 22 de septiembre, no de una intuicion:
# mirando los 448 grupos con mas del 200 % de dispersion, resulta que
#
#   - los sostenidos por un enlace FUERTE son ahorros de verdad, y son la razon
#     de ser del comparador: "Agua Dia 5 L" a 13,6 c/l contra "Solan de Cabras"
#     a 53,8 (enlace 0,74), "Chocolate blanco Hacendado" contra "Toblerone"
#     (enlace 1,00), "Chalupa sal lavavajillas" contra "Finish" (0,77);
#   - los sostenidos por un enlace FLOJO son los errores: "Cerveza sin alcohol
#     Aldi" con "Budweiser" (0,55, 97 productos), aguas "Cortes" con "Pedras"
#     (0,58), cafes "Carrefour Classic" con "Saula" (0,60).
#
# Medido: de los 448 anchos, 222 cuelgan de un enlace por debajo de 0,60, y en
# los estrechos eso solo pasa en el 25 %. El ancho no discrimina; el cuello de
# botella si. De ahi esta regla, que es la unica que separa las dos cosas: **un
# enlace flojo puede unir, mientras no haga que el grupo se vuelva ancho.**
#
# No se aplica a los pares de dos: los dos casos posibles (un acierto con un
# ahorro grande, o un error) son igual de frecuentes ahi, y quitar los pares
# costaria la mitad del comparador.
#
# Medido el 22 de septiembre sobre los 22.705 enlaces (grupos comparables /
# productos comparables / grupos anchos / de esos, los que cuelgan de un enlace
# flojo / bien sostenidos / productos con letra de calidad):
#
#     sin este freno   7.924 / 23.048 / 448 / 222 / 226 / 12.997
#     con el freno     7.997 / 22.696 / 261 /  66 / 195 / 12.322
#
# Los grupos anchos bajan de 448 a 261, pero lo que importa es la cuarta columna:
# **los sospechosos caen de 222 a 66, un 70 %**, y se conservan 195 de los 226
# ahorros de verdad. Cuesta un 1,5 % de productos comparables y un 5 % de la
# letra de calidad, y a cambio quita dos tercios de los errores que la propia
# medicion habia senalado. Es la primera palanca de toda esta investigacion que
# mueve el numero que hay que mover.
ANCHO_MAXIMO = 3.0


def _rango_de(precios, i):
    """(unidad, precio) de un producto, si su precio sirve para comparar."""
    if not precios:
        return None
    u, p = precios[i]
    return (u, p) if u and p and u in UNIDADES_FIABLES else None


def _se_hace_ancho(a: dict, b: dict) -> bool:
    """¿Unir estos dos rangos deja un grupo con el mas caro a mas del triple?

    Se mide **por unidad**: mezclar los euros por kilo de uno con los euros por
    litro de otro no dice nada, y hacerlo convertiria en "ancho" cualquier grupo
    que mezcle peso y volumen.
    """
    for unidad, (lo_a, hi_a) in a.items():
        if unidad not in b:
            continue
        lo_b, hi_b = b[unidad]
        lo, hi = min(lo_a, lo_b), max(hi_a, hi_b)
        if lo > 0 and hi / lo > ANCHO_MAXIMO:
            return True
    return False


def agrupar_enlaces(enlaces_: list[tuple], n: int,
                    umbral_union: float = UMBRAL_UNION,
                    precios: list | None = None) -> list[int]:
    """Id de grupo por producto, con el freno contra el grupo monstruo.

    Los enlaces se recorren de mas parecido a menos, que es lo que hace que el
    nucleo bueno de cada grupo se forme primero y los puentes flojos se queden
    fuera: cuando un enlace de 0,55 llega, los dos racimos que uniria ya existen.

    `precios` es, por producto, `(unidad_canon, precio_unidad_cent)`; con eso se
    aplica ademas el freno de ANCHO_MAXIMO. Sin el, solo se aplica el de union.
    """
    padre = list(range(n))
    tamano = [1] * n
    # Rango de precio por unidad de cada componente, por unidad de medida.
    rango: list[dict] = [{} for _ in range(n)]
    if precios:
        for i in range(n):
            par = _rango_de(precios, i)
            if par:
                rango[i][par[0]] = (par[1], par[1])

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for e in sorted(enlaces_, key=lambda x: -x[2]):
        i, j, s = e[0], e[1], e[2]
        ri, rj = raiz(i), raiz(j)
        if ri == rj:
            continue
        if s < umbral_union:
            if tamano[ri] > 1 and tamano[rj] > 1:
                continue
            # Un enlace flojo puede unir, mientras no haga el grupo ancho. Los
            # pares de dos no se tocan: ahi no hay nada que juzgar todavia.
            if (precios and tamano[ri] + tamano[rj] > 2
                    and _se_hace_ancho(rango[ri], rango[rj])):
                continue
        padre[rj] = ri
        tamano[ri] += tamano[rj]
        if precios:
            for unidad, (lo, hi) in rango[rj].items():
                if unidad in rango[ri]:
                    lo0, hi0 = rango[ri][unidad]
                    rango[ri][unidad] = (min(lo, lo0), max(hi, hi0))
                else:
                    rango[ri][unidad] = (lo, hi)

    renombre: dict[int, int] = {}
    salida = []
    for i in range(n):
        salida.append(renombre.setdefault(raiz(i), len(renombre)))
    return salida


def agrupar(filas: list[dict], umbral: float = 0.55,
            usar_ean: bool = True) -> list[int]:
    """Id de grupo por fila, a partir de los enlaces ya repartidos 1-a-1."""
    return agrupar_enlaces(
        enlaces(filas, umbral=umbral, usar_ean=usar_ean), len(filas),
        precios=[(f.get("unidad_canon"), f.get("precio_unidad_cent"))
                 for f in filas])
