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
    """
    if not a or not b:
        return 0.0
    comun = sum(pesos.get(p, 1.0) for p in a & b)
    total = sum(pesos.get(p, 1.0) for p in a) + sum(pesos.get(p, 1.0) for p in b)
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
CAMPOS_PARA_EMPAREJAR = ("fuente", "nombre", "marca", "cantidad", "unidad_canon", "ean")


def adelgaza(filas: list[dict]) -> list[dict]:
    """Las filas con solo lo que mira el emparejador, en el mismo orden."""
    return [{c: f.get(c) for c in CAMPOS_PARA_EMPAREJAR} for f in filas]


def enlaces(filas_completas: list[dict], umbral: float = 0.55,
            usar_ean: bool = True) -> list[tuple[int, int, float, str]]:
    """Pares (i, j, parecido, motivo) del mismo producto en cadenas distintas.

    Se exige **eleccion mutua**: j tiene que ser el mejor candidato de i en su
    cadena, y i el mejor de j en la suya. Sin esa condicion el emparejamiento se
    propaga en cadena -- A se parece a B, B a C, C a D -- y acaba metiendo tres
    mil productos en el mismo grupo. Medido: con componentes conexas la precision
    caia por debajo del 1%; con eleccion mutua sube a dos digitos altos.

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
        letras salvan los casos en que una junta lo que la otra separa. Las letras
        se descuentan un poco porque tambien acercan cosas que solo se parecen por
        fuera ("aceite de oliva" y "aceite de coco" comparten mucho trozo).
        """
        return max(parecido(docs[i], docs[j], pesos),
                   0.85 * dice(tris[i], tris[j]))

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

    # Mejor candidato de cada producto en cada otra cadena, dentro de su bloque.
    mejor: dict[tuple[int, str], tuple[float, int]] = {}
    mejor_eq: dict[tuple[int, str], tuple[float, int]] = {}
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
                    # Dos elecciones separadas, no una. Con una sola, el mejor
                    # candidato de un Hacendado pasaba a ser el Carrefour
                    # equivalente y se perdia el Hacendado identico de la otra
                    # cadena: medido, el acierto caia del 53 % al 43 %. Cada
                    # producto elige lo mejor de cada clase.
                    s = parejo(i, j)
                    if s >= umbral:
                        for a, b in ((i, j), (j, i)):
                            clave_a = (a, filas[b]["fuente"])
                            if s > mejor.get(clave_a, (0.0, -1))[0]:
                                mejor[clave_a] = (s, b)
                    if _marca(filas[i].get("marca")) != _marca(filas[j].get("marca")):
                        e = equivalente(i, j)
                        if e >= umbral:
                            for a, b in ((i, j), (j, i)):
                                clave_a = (a, filas[b]["fuente"])
                                if e > mejor_eq.get(clave_a, (0.0, -1))[0]:
                                    mejor_eq[clave_a] = (e, b)

    # Segunda pasada: mismo procedimiento, pero sin bloque y con el liston alto.
    # Solo se miran productos que comparten alguna palabra rara, y solo si las
    # unidades no se contradicen: comparar un kilo con un litro no lleva a nada.
    ancla: dict[str, list[int]] = defaultdict(list)
    for i, doc in enumerate(docs):
        for p in doc:
            if pesos.get(p, 0.0) >= MIN_IDF_ANCLA:
                ancla[p].append(i)
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
                for a, b in ((i, j), (j, i)):
                    clave_a = (a, filas[b]["fuente"])
                    # Un enlace con formato comprobado siempre gana a uno sin
                    # comprobar, aunque el nombre del segundo se parezca mas.
                    if clave_a not in mejor:
                        mejor[clave_a] = (s, b)

    emitidos: set[tuple[int, int]] = set()
    for (i, _cadena), (s, j) in mejor.items():
        if mejor.get((j, filas[i]["fuente"]), (0.0, -1))[1] == i and i < j:
            emitidos.add((i, j))
            salida.append((i, j, s, nivel(filas[i], filas[j])))
    for (i, _cadena), (e, j) in mejor_eq.items():
        if (mejor_eq.get((j, filas[i]["fuente"]), (0.0, -1))[1] == i and i < j
                and (i, j) not in emitidos):
            salida.append((i, j, e, "equivalente"))
    return salida


def _marca(valor) -> str:
    return nombre_limpio(str(valor or ""), None).strip()


def nivel(a: dict, b: dict) -> str:
    """identico | equivalente. La distincion que pedia el proyecto.

    Misma marca y mismo formato es el mismo producto; distinta marca y mismo
    formato es el equivalente de otra marca, que es justo lo que hay que comparar
    cuando las cadenas venden marca blanca y no comparten codigo de barras.
    """
    ea, eb = _ean(a.get("ean")), _ean(b.get("ean"))
    if ea and eb and ea == eb:
        return "identico"
    ma, mb = _marca(a.get("marca")), _marca(b.get("marca"))
    return "identico" if ma and ma == mb else "equivalente"


def agrupar(filas: list[dict], umbral: float = 0.55,
            usar_ean: bool = True) -> list[int]:
    """Id de grupo por fila, a partir de los enlaces mutuos."""
    u = Union()
    for i in range(len(filas)):
        u.raiz_de(i)
    for i, j, _, _ in enlaces(filas, umbral=umbral, usar_ean=usar_ean):
        u.une(i, j)
    renombre: dict[int, int] = {}
    return [renombre.setdefault(u.raiz_de(i), len(renombre))
            for i in range(len(filas))]
