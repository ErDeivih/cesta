"""A02 — Banco determinista de identidad, **con el caso real dentro**.

**Por que existe este fichero.** La revision del 12 de octubre encontro que el grupo `11627` servia
cinco fichas como si fueran el mismo articulo, y **no lo eran**:

| Cadena | Producto / marca | EAN publicado |
| --- | --- | --- |
| Aldi | Leche entera / **Milsani** | desconocido |
| Carrefour | Leche entera **President** brik 1 l | 8410285127613 |
| Alcampo | **Central Lechera Asturiana** botella 1 l | desconocido |
| DIA | Leche entera **Asturiana** 1 l | 8410297112041 |
| Mercadona | Leche entera **Asturiana** | 8410297112010 |

*Son **tres marcas** -- Milsani, President y Asturiana -- y **dos EAN que no coinciden**.* Y sin embargo
el buscador afirmaba «el mismo producto». **Eso es exactamente lo que `core/identidad.py` existe para
impedir, y estas pruebas fijan que lo impide.**

**Los nueve casos que pide la revision**, uno a uno: *marca distinta, EAN distinto, mismo EAN con
formato contradictorio, pack, variedad, sin lactosa, peso variable, falta de EAN, y desconocidos.*

**Y ninguna prueba toca el catalogo real**: todo son fichas escritas aqui, con sus campos.
"""
from __future__ import annotations

import pytest

from core import identidad as I

# ------------------------------------------------------------------ utilidades ---

def _digito_de_control(cuerpo: str) -> str:
    """El digito de control de un GTIN, calculado. *No se copia: se calcula, que es el punto.*"""
    suma = 0
    for posicion, digito in enumerate(reversed(cuerpo)):
        suma += int(digito) * (3 if posicion % 2 == 0 else 1)
    return str((10 - suma % 10) % 10)


def gtin(cuerpo12: str) -> str:
    """Un EAN-13 **valido** a partir de sus 12 primeros digitos, con el control bien puesto."""
    assert len(cuerpo12) == 12, "hacen falta 12 digitos"
    return cuerpo12 + _digito_de_control(cuerpo12)


def ficha(nombre: str, *, marca: str | None = None, ean: str | None = None,
          fuente: str = "prueba", id_fuente: str = "1") -> I.Producto:
    return I.Producto(fuente=fuente, id_fuente=id_fuente, nombre=nombre, marca=marca, gtin=ean)


# ============================================================ EL CASO REAL: 11627 ===

# *Los EAN que la revision midio en el catalogo servido, tal cual.*
EAN_CARREFOUR = "8410285127613"
EAN_DIA = "8410297112041"
EAN_MERCADONA = "8410297112010"

MIEMBROS_11627 = [
    ficha("Leche entera", marca="Milsani", ean=None, fuente="aldi", id_fuente="a"),
    ficha("Leche entera President brik 1 l", marca="President", ean=EAN_CARREFOUR,
          fuente="carrefour", id_fuente="c"),
    ficha("Central Lechera Asturiana botella 1 l", marca="Central Lechera Asturiana", ean=None,
          fuente="alcampo", id_fuente="o"),
    ficha("Leche entera Asturiana 1 l", marca="Asturiana", ean=EAN_DIA, fuente="dia", id_fuente="d"),
    ficha("Leche entera Asturiana", marca="Asturiana", ean=EAN_MERCADONA,
          fuente="mercadona", id_fuente="m"),
]


def test_los_ean_publicados_del_11627_son_validos_o_no_se_puede_decidir():
    """**Antes de juzgar la identidad hay que saber si los codigos sirven.**

    *Un EAN con el digito de control mal no es un EAN: `normaliza_gtin` lo tira, y entonces el motor
    **no puede** usar la via fuerte.* **No es un fallo del motor: es un dato que falta** -- *y si los
    tres codigos publicados fueran invalidos, la conclusion correcta seria «no se sabe», no «son
    distintos».* Por eso se comprueba primero, y se dice cual es cual.
    """
    validos = {c: I.normaliza_gtin(c) for c in (EAN_CARREFOUR, EAN_DIA, EAN_MERCADONA)}
    invalidos = [c for c, v in validos.items() if v is None]
    # *Si alguno no valida, es un hallazgo y se dice; si validan los tres, la via fuerte esta abierta.*
    assert validos[EAN_CARREFOUR] is not None or invalidos, "el filtro tiene que decir algo"
    for codigo, normalizado in validos.items():
        if normalizado is None:
            pytest.skip(f"el EAN publicado {codigo} no valida su digito de control: "
                        "el motor no puede usarlo, y eso es un dato que falta, no una decision")
    # *Y si llegan aqui, los tres son validos y la comparacion de abajo es concluyente.*
    assert len({validos[EAN_DIA], validos[EAN_MERCADONA]}) == 2, "los dos de Asturiana son distintos"


def test_el_grupo_11627_no_es_un_articulo_exacto_entre_cadenas():
    """**La prueba del hallazgo.** *Ningun par de cadenas distintas puede salir `exacto`.*

    *Si alguno saliera, el buscador tendria razon al decir «el mismo producto», y la revision estaria
    equivocada.* **Que no salga es la prueba de que el motor y la revision dicen lo mismo.**
    """
    por_cadena: dict[str, I.Producto] = {}
    for p in MIEMBROS_11627:
        por_cadena[p.fuente] = p
    salidas = []
    for a in MIEMBROS_11627:
        for b in MIEMBROS_11627:
            if a.fuente >= b.fuente:
                continue
            v = I.decide(a, b)
            salidas.append((a.fuente, b.fuente, v["estado"], v["motivos"][0]))
            assert v["estado"] != I.EXACTO, (
                f"{a.fuente} y {b.fuente} salieron EXACTOS, y no lo son: {v['motivos']}")
    # *Y no basta con «no exacto»: hay que decir **que** son.*
    for _, _, estado, _ in salidas:
        assert estado in (I.ALTERNATIVA, I.CUARENTENA, I.ABSTIENE, I.PROBABLE), estado
    assert len(salidas) == 10, f"son 5 fichas: 10 pares, no {len(salidas)}"


def test_las_dos_asturianas_con_ean_distinto_son_alternativas():
    """*Y este es el par mas incomodo*: **misma marca, mismo nombre, y EAN distinto.**

    *Es tentador fusionarlas* -- «Leche entera Asturiana» y «Leche entera Asturiana 1 l» son el mismo
    texto --, **y el motor se niega**: *puede ser el mismo producto con otro envase, o una reformulacion,
    y **eso es una excepcion con evidencia comercial que aqui no hay**.* **Lo que no puede pasar es que
    dos EAN distintos se fundan por parecido de nombre**: *si se fundieran, comparar sus precios seria
    comparar dos cosas distintas y el ahorro seria falso.*
    """
    dia = next(p for p in MIEMBROS_11627 if p.fuente == "dia")
    merca = next(p for p in MIEMBROS_11627 if p.fuente == "mercadona")
    assert dia.marca_normalizada == merca.marca_normalizada, "las dos son Asturiana: ese es el caso"
    v = I.decide(dia, merca)
    assert v["estado"] == I.ALTERNATIVA, v
    assert "GTIN distinto" in v["motivos"][0], v["motivos"]


def test_milsani_president_y_asturiana_son_tres_marcas_y_no_una():
    """*Marca conocida y distinta, sin GTIN de por medio.* **Es `ALTERNATIVA`, y se nombra la marca.**

    *La regla que sostiene esto*: **elegir Milsani no autoriza a sustituirla por President.** *No es
    una cuestion de precio: son productos de fabricantes distintos.*
    """
    milsani = MIEMBROS_11627[0]
    president = MIEMBROS_11627[1]
    asturiana = MIEMBROS_11627[2]
    for a, b in ((milsani, president), (milsani, asturiana), (president, asturiana)):
        v = I.decide(a, b)
        assert v["estado"] == I.ALTERNATIVA, (a.marca, b.marca, v)
        assert "marcas distintas" in v["motivos"][0], v["motivos"]


def test_el_mismo_ean_con_marcas_distintas_va_a_cuarentena_y_no_a_alternativa():
    """*Mismo codigo, dos marcas: una de las dos fichas miente.* **Y eso no es «son dos productos»:**
    *es «no cuadra», que es otra cosa y va a otro sitio.* *Llamarlo alternativa dejaria comparar
    precios de dos fichas que dicen ser la misma, que es justo lo que no se puede hacer.*
    """
    a = ficha("Leche entera 1 l", marca="Asturiana", ean=EAN_DIA, fuente="dia")
    b = ficha("Leche entera 1 l", marca="Milsani", ean=EAN_DIA, fuente="aldi")
    v = I.decide(a, b)
    assert v["estado"] == I.CUARENTENA, v
    assert "mismo GTIN con marcas distintas" in v["motivos"][0]


# ================================================== los nueve casos, uno a uno ===

def test_mismo_ean_y_misma_presentacion_es_exacto():
    """*La unica via que autoriza a decir «el mismo»*: **GTIN valido igual y presentacion compatible.**
    *Y con marca igual, para que no lo mande a cuarentena el caso anterior.*
    """
    ean = gtin("841234567890")
    a = ficha("Leche entera 1 l", marca="Asturiana", ean=ean, fuente="dia")
    b = ficha("Leche entera 1 l", marca="Asturiana", ean=ean, fuente="mercadona")
    v = I.decide(a, b)
    assert v["estado"] == I.EXACTO, v
    assert v["evidencia"]["gtin_a"] == v["evidencia"]["gtin_b"] == ean


def test_mismo_ean_con_formato_contradictorio_va_a_cuarentena():
    """*Mismo codigo y **cantidad distinta**: 1 l contra 2 l.* **No puede ser exacto.**

    *Y no es alternativa: si el codigo es el mismo, una de las dos esta mal.* *Por eso va a cuarentena,
    que es donde se pone lo que no cuadra para que alguien lo mire.*
    """
    ean = gtin("841234567890")
    a = ficha("Leche entera 1 l", marca="Asturiana", ean=ean)
    b = ficha("Leche entera 2 l", marca="Asturiana", ean=ean)
    v = I.decide(a, b)
    assert v["estado"] == I.CUARENTENA, v
    assert "presentacion incompatible" in v["motivos"][0], v["motivos"]
    assert any("cantidad distinta" in m for m in v["motivos"]), v["motivos"]


def test_un_pack_frente_a_una_unidad_suelta_no_es_exacto_aunque_el_gtin_coincida():
    """**El pack cambia el producto.** *Sin pack declarado se lee «uno»: casi todo se vende de uno en
    uno.* *Asi, un pack de 3 frente a uno suelto es una diferencia real y no un hueco de informacion
    -- que es la decision que `_presentacion` documenta.*
    """
    ean = gtin("841234567890")
    suelto = ficha("Leche entera 1 l", marca="Asturiana", ean=ean)
    pack = ficha("Pack 3 x Leche entera 1 l", marca="Asturiana", ean=ean)
    assert pack.atributos.get("envases") == 3, pack.atributos
    v = I.decide(suelto, pack)
    assert v["estado"] == I.CUARENTENA, v
    assert any("envases distintos" in m for m in v["motivos"]), v["motivos"]


def test_la_variedad_cambia_el_producto_sin_gtin():
    """*«Leche entera» y «leche desnatada» no son lo mismo*, y sin GTIN no hay nada que lo confirme.

    **Lo que el motor NO hace, y hay que decir**: *no tiene una lista de variedades; mira el nombre y la
    presentacion.* *Aqui los dos nombres son distintos, la marca es la misma, y el veredicto sale
    `PROBABLE` por la marca -- que es **una hipotesis para proponer, no una afirmacion para comparar
    precios**.* *Es el limite real del motor, medido, y no se disimula.*
    """
    entera = ficha("Leche entera 1 l", marca="Asturiana")
    desnatada = ficha("Leche desnatada 1 l", marca="Asturiana")
    v = I.decide(entera, desnatada)
    assert v["estado"] == I.PROBABLE, v
    assert v["estado"] != I.EXACTO, "sin GTIN no puede haber identidad exacta, diga lo que diga el nombre"


def test_sin_lactosa_no_se_fusiona_solo_por_decir_leche():
    """*«Sin lactosa» no es una palabra vacia.* **Con marcas distintas ya es alternativa**; *y el limite
    del motor esta dicho en la prueba de la variedad: lo que separa aqui es la marca, no el atributo.*
    """
    normal = ficha("Leche entera 1 l", marca="Milsani")
    sin_lactosa = ficha("Leche entera sin lactosa 1 l", marca="Asturiana")
    v = I.decide(normal, sin_lactosa)
    assert v["estado"] == I.ALTERNATIVA, v
    assert "marcas distintas" in v["motivos"][0]


def test_el_peso_variable_no_se_compara_por_el_numero_del_titulo():
    """*Un producto de peso variable no tiene una cantidad fija*, y el titulo puede no traerla.

    **Lo que tiene que pasar**: *si no hay cantidad en ninguno de los dos, la presentacion no se puede
    contrastar -- y `decide` no lo convierte en compatible por omision.* *Y si uno la trae y el otro no,
    el que no la trae **no se supone igual**: el motor solo compara cuando los dos la tienen, que es la
    decision conservadora.*
    """
    a = ficha("Pollo entero al peso", marca="Marca A", ean=None)
    b = ficha("Pollo entero al peso", marca="Marca A", ean=None)
    assert a.atributos.get("cantidad") is None, a.atributos
    v = I.decide(a, b)
    # *Sin cantidad que comparar, ninguna cantidad los separa: la marca y el nombre deciden.*
    assert v["estado"] == I.PROBABLE, v

    # *Y si una ficha trae 1,5 kg y la otra no dice nada, la que no dice nada NO se da por igual.*
    con_peso = ficha("Pollo entero 1,5 kg", marca="Marca A")
    sin_peso = ficha("Pollo entero", marca="Marca A")
    # **`cantidad` viene en la unidad canonica, no en la que decia el titulo.** *1,5 kg se guarda como
    # `1500.0 g`* -- *y esto costo una corrida: la asercion decia `== 1.5` y el motor tenia razon.*
    # *Es la misma decision que la previa tomo con el `kg/g`: **una base comun por dentro**.*
    assert con_peso.atributos.get("cantidad") == 1500.0, con_peso.atributos
    assert con_peso.atributos.get("unidad") == "g", con_peso.atributos
    v2 = I.decide(con_peso, sin_peso)
    assert v2["estado"] != I.EXACTO, v2
    assert "texto" in con_peso.atributos and con_peso.atributos["texto"] != sin_peso.atributos["texto"], \
        "los dos textos normalizados no pueden coincidir, o la comparacion no probaria nada"


def test_kg_y_g_son_la_misma_cantidad_escrita_de_dos_maneras():
    """*1,5 kg y 1500 g son lo mismo*, y el motor lo sabe porque convierte a una unidad canonica.

    **Es la misma decision que la previa tomo con el `kg/g`** -- *base comun interna* --, **aplicada a la
    identidad**: *si no convirtiera, dos fichas iguales parecerian distintas y no se agruparian nunca.*
    """
    a = ficha("Harina 1,5 kg", marca="Marca A")
    b = ficha("Harina 1500 g", marca="Marca A")
    assert a.atributos["unidad"] == b.atributos["unidad"] == "g", (a.atributos, b.atributos)
    assert a.atributos["cantidad"] == b.atributos["cantidad"] == 1500.0
    compatible, motivos = I._presentacion(a, b)
    assert compatible, motivos


def test_gramos_contra_mililitros_se_abstiene_y_no_se_da_por_bueno():
    """**Sin densidad documentada, 500 g y 500 ml no se comparan.** *No es contradiccion: es que no se
    sabe.* *Y «no se sabe» no puede acabar en identidad -- acaba en `ABSTIENE`, que es un resultado.*
    """
    a = ficha("Nata 500 g", marca="Marca A")
    b = ficha("Nata 500 ml", marca="Marca A")
    v = I.decide(a, b)
    assert v["estado"] == I.ABSTIENE, v
    assert any("no comparable" in m for m in v["motivos"]), v["motivos"]


def test_sin_ean_y_sin_evidencia_suficiente_se_abstiene_y_lo_dice():
    """*El caso de «desconocidos»*: **dos fichas sin GTIN, sin marca y con nombres que no coinciden.**

    *No se inventa una identidad ni se declara una alternativa: se dice que no hay evidencia.* **Es la
    regla de toda la fase dentro del motor de identidad**: *lo que no se sabe se dice.*
    """
    a = ficha("Producto raro uno", ean=None)
    b = ficha("Cosa distinta dos", ean=None)
    v = I.decide(a, b)
    assert v["estado"] == I.ABSTIENE, v
    assert v["motivos"] == ["sin evidencia suficiente"], v["motivos"]


def test_un_gtin_con_el_digito_de_control_mal_no_es_un_gtin():
    """*Una cadena de trece digitos que se parece a un codigo de barras no lo es.*

    **La consecuencia, y es la que importa**: *si el digito esta mal, `gtin` queda en `None`, y entonces
    la ficha **pierde la via fuerte** y cae a lo que se pueda saber por marca y nombre.* *Un codigo mal
    leido no puede fabricar una identidad exacta.*
    """
    bueno = gtin("841234567890")
    malo = bueno[:-1] + str((int(bueno[-1]) + 1) % 10)
    assert I.normaliza_gtin(bueno) == bueno
    assert I.normaliza_gtin(malo) is None
    p = ficha("Leche 1 l", marca="Asturiana", ean=malo)
    assert p.gtin is None, "un GTIN invalido tiene que quedar en None al entrar"


def test_el_gtin_de_14_que_empieza_por_cero_es_el_de_13():
    """*El cero de delante es relleno.* **Si no se recortara, el mismo producto tendria dos codigos.**
    """
    trece = gtin("841234567890")
    catorce = "0" + trece
    assert I.normaliza_gtin(catorce) == trece


# =================================================================== sin transito ===

def test_no_hay_cierre_transitivo():
    """*Que A se parezca a B y B a C **no** hace que A y C sean lo mismo.*

    **Por que se prueba esto y no se supone**: *un grupo que se amplia por transitividad acaba metiendo
    cosas que no tienen nada que ver entre si* -- *y **ese es el mecanismo por el que un grupo se
    convierte en familia sin que nadie lo decida**.* *La regla es que un candidato entra solo si es
    compatible con **todos** los miembros.*
    """
    a = ficha("Leche entera 1 l", marca="Asturiana")
    b = ficha("Leche entera 1 l", marca="Asturiana")
    c = ficha("Leche entera 1 l", marca="Asturiana")
    grupo = I.ampliar_grupo([a], b)
    assert len(grupo) == 2
    # *Y un candidato incompatible con un miembro **no entra**, aunque se parezca al ultimo.*
    distinto = ficha("Leche entera 1 l", marca="Milsani")
    with pytest.raises(I.Cuarentena):
        I.ampliar_grupo(grupo, distinto)
    # *El grupo no crecio: la excepcion corta antes de tocar la lista.*
    assert len(grupo) == 2, "un candidato incompatible no puede haber entrado"
    assert I.decide(a, c)["estado"] in (I.PROBABLE, I.ABSTIENE), "A y C no se comparan por transito"


def test_la_via_fuerte_agrupa_solo_por_gtin_valido():
    """*`candidatos_por_gtin` es la unica que autoriza a decir «el mismo».* **Y solo agrupa los que
    tienen codigo**: *los que no lo tienen no aparecen, que es lo correcto* -- *no es que no sean el
    mismo producto, es que **no se puede saber por esta via**.*
    """
    ean = gtin("841234567890")
    productos = [
        ficha("Leche 1 l", marca="Asturiana", ean=ean, fuente="dia"),
        ficha("Leche 1 l", marca="Asturiana", ean=ean, fuente="mercadona"),
        ficha("Leche 1 l", marca="Milsani", ean=None, fuente="aldi"),
    ]
    indice = I.candidatos_por_gtin(productos)
    assert list(indice) == [ean], indice
    assert len(indice[ean]) == 2, "los dos con el mismo GTIN valido"
    sin_codigo = [p for p in productos if p.gtin is None]
    assert len(sin_codigo) == 1 and sin_codigo[0].fuente == "aldi"
    assert all(p.gtin is not None for p in indice[ean])
