"""¿Este producto es cesta familiar? Una sola funcion para todo el proyecto.

**Por que existe.** Hoy el catalogo tiene 53.139 productos y el 5 de octubre de 2026 se midio
que **245 de Alcampo son bazar** -- fundas de sofa, aviones de juguete -- dentro de un proyecto
que va de la lista de la compra de una familia. Eso no es solo ruido: ensucia las comparaciones,
gasta peticiones (y el WAF de Alcampo no esta para regalar), y hace que una rama de decoracion
pueda tumbar la captura de alimentos. El contrato es
`docs/CESTA-DATOS-Y-COMPARACION.md` seccion 1; la politica esta en `core/datos/alcance.yml`,
versionada con el codigo, y esto la aplica.

    from core.alcance import clasificar_alcance
    d = clasificar_alcance("Funda elastica para sofa de 3 plazas", "Hogar y Decoracion > Textil hogar")
    d.estado    # 'excluido'
    d.motivo    # 'muebles, decoracion y textil duradero'
    d.regla_id  # 'prod-muebles-decoracion'

**Las tres decisiones que importan, y por que:**

1. **Se compara por palabras completas, nunca por trozos.** En este proyecto ya paso: los
   pañales acabaron en panaderia porque "panales" contiene "pan". Aqui un termino de dos palabras
   ("papel higienico") se busca como frase y uno de una palabra ("panal") tiene que ser una
   palabra entera: `pantalon` no es `pan` ni `panal`, y `cuaderno` no es `papel higienico`.
2. **En la categoria manda el segmento mas especifico.** Se recorre la ruta de la hoja hacia la
   rama y decide el primer segmento que reconoce: asi "Folleto y Promociones > Renueva la
   decoracion de tu hogar" se excluye por `decoracion` (la hoja) y no se salva por `promociones`
   (la rama) -- que es justo el agujero por el que se colaban los productos de bazar en las
   capturas.
3. **El producto puede ganar a la categoria, y solo para excluir.** Un televisor dentro de
   "Promociones" sigue siendo un televisor; pero un alimento dentro de "Promociones" no se
   excluye por estar en promociones: se queda en `revisar` si no hay nada mejor, que es una
   decision, no un descarte.

Y lo que **no** hace: no adivina. Si no hay regla que lo coja, el estado es `revisar` con el
motivo escrito. Un producto sin clasificar no entra en una recomendacion automatica.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

POLITICA = Path(__file__).resolve().parent / "datos" / "alcance.yml"

INCLUIDO, EXCLUIDO, REVISAR = "incluido", "excluido", "revisar"


@dataclass(frozen=True)
class DecisionAlcance:
    """Lo que devuelve `clasificar_alcance`. Todo con su motivo y su regla."""

    estado: str
    familia_id: str | None
    motivo: str
    regla_id: str
    version_politica: int
    evidencias: dict = field(default_factory=dict)

    @property
    def entra(self) -> bool:
        """¿Se guarda y se compara? `revisar` no entra: se queda para que alguien lo mire."""
        return self.estado == INCLUIDO

    def __str__(self) -> str:
        return f"{self.estado:9} {self.regla_id:32} {self.motivo}"


def _sin_tildes(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in plano if not unicodedata.combining(c)).lower()


def _palabras(texto: str) -> list[str]:
    """Las palabras de un texto, sin tildes y sin separadores raros.

    `congelados-y-helados/pizzas` -> ['congelados', 'y', 'helados', 'pizzas']
    """
    return [p for p in re.split(r"[^a-z0-9ñ]+", _sin_tildes(texto)) if p]


def _segmentos(ruta: str) -> list[str]:
    """Los trozos de una ruta de categoria, de la hoja a la rama.

    `"Hogar y Decoracion > Textil hogar > Fundas de sofa"` -> la hoja primero, porque es la que
    mas sabe de este producto. Ver la decision 2 de la cabecera.
    """
    trozos = [t for t in re.split(r"[>/]", ruta or "") if t.strip()]
    return list(reversed(trozos))


def _raiz(palabra: str) -> str:
    """La palabra sin su marca de plural. **Solo para comparar**, nunca para mostrar.

    Medido el 6 de octubre de 2026 con el banco de verdad: la politica tiene los terminos en
    singular y las cadenas nombran sus pasillos en plural, asi que **"pescado" no casaba con
    "pescados-y-mariscos"**, ni "golosina" con "golosinas", ni "gato" con "gatos". Eran 16 fichas
    de comida esperando en `revisar` por una "s" -- y no se veia, porque el sintoma era "sin
    clasificacion suficiente".

    Se corta la "s" (y "es") solo en palabras de mas de tres letras: asi "pan" no se convierte en
    "pa" ni "mes" en "me". No es un lematizador ni pretende serlo: es quitar el plural, que es lo
    unico que hace falta aqui.
    """
    # **Solo la "s".** Quitar "-es" daba "carn" para "carnes", y entonces no casaba con el termino
    # "carne": el arreglo fallaba justo en las palabras que acaban en "-es". Se vio en las pruebas.
    if len(palabra) > 3 and palabra.endswith("s"):
        return palabra[:-1]
    return palabra


def _casa(termino: str, _texto: str, palabras: list[str]) -> bool:
    """¿Estan TODAS las palabras del termino entre las del texto?

    **Por palabras, y el termino tambien se parte en palabras.** Un termino de la politica como
    `papel-de-cocina` casa con el segmento `Papel de cocina`; antes no casaba: se comparaba el
    termino entero contra una sola palabra, asi que **todos los terminos con guion de la politica
    --`cuidado-de-la-ropa`, `higiene-bucal`, `moda-infantil`-- no casaban nunca, en silencio**. Se
    descubrio con la ejecucion seca del 5 de octubre de 2026, viendo que el suavizante de Aldi
    seguia saliendo por una regla de moda.

    Y sigue sin casar por trozos: `panal` no esta en `pantalon` (la leccion de los pañales en
    panaderia). El texto entero no hace falta y ya no se usa: lo que importa son sus palabras.
    """
    propias = [p for p in re.split(r"[^a-z0-9ñ]+", _sin_tildes(termino)) if p]
    if not propias:
        return False
    # **Por raiz, en los dos lados**: la politica dice "pescado" y la cadena "pescados". Ver `_raiz`.
    raices = [_raiz(p) for p in palabras]
    if len(propias) == 1:
        return _raiz(propias[0]) in raices
    # **Contigua y en orden.** Un termino de varias palabras es una *frase*, y exigir solo que
    # esten todas las palabras en cualquier orden lo convertia en otra cosa: "cubo de basura"
    # casaba con "Bolsa de basura para cubo alto". Se descubrio el 6 de octubre de 2026 con tres
    # falsos descartes reales en el catalogo (una bolsa de basura, un absorbeolores y una barrita).
    largo = len(propias)
    propias_raiz = [_raiz(p) for p in propias]
    return any(raices[i:i + largo] == propias_raiz for i in range(len(raices) - largo + 1))


@lru_cache(maxsize=1)
def politica() -> dict:
    """La politica cargada. Cacheada: se lee una vez por proceso."""
    return yaml.safe_load(POLITICA.read_text(encoding="utf-8"))


def version() -> int:
    return int(politica().get("version", 0))


@lru_cache(maxsize=300_000)
def _clasifica_memorizada(nombre: str, categoria: str) -> DecisionAlcance:
    """`clasificar_alcance` sin contexto y memorizada. Ver `_clasifica`."""
    return _clasifica(nombre, categoria, None)


def clasificar_alcance(nombre: str | None, categoria: str | None = None,
                       contexto: dict | None = None) -> DecisionAlcance:
    """El estado de un producto. Sin contexto, el resultado se memoriza.

    Clasificar el catalogo son decenas de miles de llamadas, y 30 dias de capturas mas de un
    millon: el mismo par (nombre, categoria) se repite dia tras dia, asi que la cache es lo que
    hace que el control de cobertura tarde segundos y no minutos. Con `contexto` se calcula sin
    memorizar (el contexto es un diccionario y no se puede usar como clave).

    **No modificar las evidencias de lo que devuelve**: son las del cache.
    """
    if contexto is None:
        return _clasifica_memorizada(nombre or "", categoria or "")
    return _clasifica(nombre, categoria, contexto)


def _inclusion_que_gana(pol: dict, regla_id: str, nombre: str, palabras_nombre: list[str],
                        ev: dict, ver: int) -> DecisionAlcance | None:
    """Si la politica declara que una inclusion le gana a **esa** exclusion, la devuelve.

    Existe por un fallo medido con el banco de verdad el 6 de octubre de 2026: la excepcion estaba
    solo en el paso de la categoria, y hay exclusiones que se resuelven antes, en el del producto,
    asi que no llegaba a mirarse. Tenerlo en un solo sitio es lo que evita que la politica sepa
    cosas distintas segun por donde pase la ficha.
    """
    for regla in pol.get("incluye_producto", []):
        if regla_id not in (regla.get("gana_a_exclusion") or []):
            continue
        for termino in regla["terminos"]:
            if _casa(termino, nombre, palabras_nombre):
                return DecisionAlcance(INCLUIDO, regla.get("familia"), regla["motivo"],
                                       regla["id"], ver,
                                       {**ev, "termino": termino, "gana_a": regla_id})
    return None


def _clasifica(nombre: str | None, categoria: str | None,
               contexto: dict | None) -> DecisionAlcance:
    """El estado de un producto dentro del catalogo familiar.

    `nombre` es el titulo tal y como lo publica la cadena y `categoria` su ruta de categoria
    (`"Frescos > Carne > Pollo"`). `contexto` es para lo que la politica no ve --cadena, si es
    promocion, si viene de una lista-- y queda guardado en `evidencias` para poder auditar la
    decision.
    """
    pol = politica()
    ver = version()
    nombre = nombre or ""
    categoria = categoria or ""
    palabras_nombre = _palabras(nombre)
    ev = {"nombre": nombre, "categoria": categoria, **(contexto or {})}

    # 1. El producto puede excluirse aunque su categoria diga otra cosa.
    for regla in pol.get("excluye_producto", []):
        for termino in regla["terminos"]:
            if _casa(termino, nombre, palabras_nombre):
                # Antes de excluir: **¿la politica declara que algo le gana a esta exclusion?**
                # (lo desechable le gana a los duraderos; una hierba fresca, a la regla de jardin).
                excepcion = _inclusion_que_gana(pol, regla["id"], nombre, palabras_nombre, ev, ver)
                if excepcion is not None:
                    return excepcion
                return DecisionAlcance(EXCLUIDO, None, regla["motivo"], regla["id"], ver,
                                       {**ev, "termino": termino})

    # 2. La categoria: se miran TODOS los segmentos de la ruta y gana la regla de prioridad mas
    #    alta; a igualdad, el segmento mas especifico (el que mas sabe de este producto).
    #
    #    Esto empezo siendo "gana el segmento mas profundo" y estaba mal, y se vio con una prueba
    #    de aceptacion: "Mascotas > Perros > Alimentacion" salia como `despensa`, porque la hoja
    #    ("Alimentacion") pesaba mas que la rama ("Mascotas"). Con prioridad, la familia concreta
    #    (20) manda sobre el pasillo generico, y el bazar escondido en una rama de promociones
    #    (30 contra 1) sigue saliendo. Ver el comentario de cabecera de `core/datos/alcance.yml`.
    candidatas: list[tuple[int, int, DecisionAlcance]] = []
    for profundidad, segmento in enumerate(_segmentos(categoria)):
        palabras_seg = _palabras(segmento)
        for regla in pol.get("reglas_categoria", []):
            if any(_casa(t, segmento, palabras_seg) for t in regla["segmentos"]):
                candidatas.append((
                    int(regla.get("prioridad", 5)), profundidad,
                    DecisionAlcance(regla["estado"], regla.get("familia"), regla["motivo"],
                                    regla["id"], ver, {**ev, "segmento": segmento})))
        for regla in pol.get("revisar_categoria", []):
            if any(_casa(t, segmento, palabras_seg) for t in regla["segmentos"]):
                candidatas.append((
                    int(regla.get("prioridad", 1)), profundidad,
                    DecisionAlcance(REVISAR, None, regla["motivo"], regla["id"], ver,
                                    {**ev, "segmento": segmento})))
    if candidatas:
        # Lo mas prioritario primero; y si empatan, lo mas especifico (mayor profundidad).
        _, _, ganadora = max(candidatas, key=lambda c: (c[0], c[1]))
        # Una categoria mixta no descarta el producto, pero tampoco decide: si no hay una regla
        # mejor, se sigue hacia el producto, y si tampoco, se revisa.
        if not (ganadora.estado == REVISAR and ganadora.regla_id == "rev-mixtas"):
            # **Una inclusion de producto puede ganarle a una exclusion de categoria, pero solo
            # si la politica lo declara regla a regla** (`gana_a_exclusion`). No se generaliza
            # --"un juguete que mencione comida podria entrar por error" (ampliacion del 6 de
            # octubre de 2026)--: es "esta comida concreta le gana a esta exclusion concreta".
            # El caso que lo exige es real: la barrita proteica de Aldi llega con la categoria
            # "parafarmacia" y nada mas, y es comida de reposicion.
            if ganadora.estado == EXCLUIDO:
                excepcion = _inclusion_que_gana(pol, ganadora.regla_id, nombre, palabras_nombre,
                                                ev, ver)
                if excepcion is not None:
                    return excepcion
            return ganadora

    # 3. El producto, para incluir (papel higienico, arena de gato, pañales...).
    for regla in pol.get("incluye_producto", []):
        for termino in regla["terminos"]:
            if _casa(termino, nombre, palabras_nombre):
                return DecisionAlcance(INCLUIDO, regla.get("familia"), regla["motivo"],
                                       regla["id"], ver, {**ev, "termino": termino})

    # 4. Y si no hay nada claro, se dice: revisar.
    return DecisionAlcance(REVISAR, None, "sin clasificacion suficiente: lo mira una persona",
                           "sin-regla", ver, ev)


def familias() -> dict:
    return politica().get("familias", {})


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__.split("\n\n")[0])
        print(f"\nPolitica version {version()}, {len(familias())} familias:")
        for fid, desc in familias().items():
            print(f"  {fid:20} {desc}")
        print("\nUso:  uv run python -m core.alcance \"<nombre>\" [\"<categoria>\"]")
        raise SystemExit(0)

    print(clasificar_alcance(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
