"""F06 (fase 2): **hasta donde llega el `umbral`**, decidido con los folletos delante.

Por que existe
--------------
F06 pide *«garantias y limites del algoritmo publicados»*, y el `umbral` era el limite sin decidir:
`Mecanica.coste` lo aplica **por producto**, y su propio comentario lo escribe como «5 EUR dto comprando
20 EUR» -- que se lee como una regla del ticket.

**La evidencia, medida el 13 de octubre de 2026** sobre los **236** textos distintos de oferta del
silver: **3** son de umbral, y los tres nombran una **marca o familia**:

    "5 EUR DTO COMPRANDO 15 EUR PRODUCTOS PASCUAL"
    "5 EUR dto. comprando 20 EUR en Nestle Cafes. Exclusivo Online."
    "5 EUR dto. comprando 15 EUR en PepsiCo. Exclusivo Online."

*No es el ticket entero, y **no es un producto**.* **Dos de los tres son `solo_online` y no restan**, asi
que la exposicion viva es **1 texto de 236 (0,4 %)**.

La decision
-----------
**Se deja como esta, por producto, y se publica.** *La lectura del motor **subestima** el descuento
--cobra de mas--, que es el lado conservador del error.* Cerrarlo pide un concepto de marca o familia que
el motor no tiene, y con un texto vivo de 236 no compensa inventarlo.

**Lo que estas pruebas impiden es lo contrario**: que alguien lo aplique al ticket entero y el comparador
empiece a prometer descuentos que no existen. *Ese error no es conservador: es mentir sobre lo que se
paga.*
"""
from __future__ import annotations

from core.promos import lee as lee_promo
from plataforma.api import cesta

# Los tres textos de umbral que hay de verdad en el catalogo.
PASCUAL = "5 EUR DTO COMPRANDO 15 EUR PRODUCTOS PASCUAL"
NESTLE = "5 EUR dto. comprando 20 EUR en Nestle Cafes. Exclusivo Online."
PEPSICO = "5 EUR dto. comprando 15 EUR en PepsiCo. Exclusivo Online."


def test_los_tres_textos_del_catalogo_se_leen_como_umbral():
    """*Si el parser dejara de reconocerlos, el limite cambiaria sin que nadie se enterara.*"""
    for texto, euros, compra in ((PASCUAL, 5, 15), (NESTLE, 5, 20), (PEPSICO, 5, 15)):
        m = lee_promo(texto)
        assert m.tipo == "umbral", f"{texto!r} se lee como {m.tipo!r}"
        assert (m.a, m.b) == (euros, compra), f"{texto!r} -> {(m.a, m.b)}"


def test_los_dos_de_solo_online_no_bajan_el_ticket():
    """**Dos de los tres son online, y ese dinero no se paga en la tienda.**

    *De 236 textos de oferta, esto deja la exposicion viva del umbral en **uno**.*
    """
    for texto in (NESTLE, PEPSICO):
        m = lee_promo(texto)
        assert m.solo_online is True, f"{texto!r} tendria que excluirse por online"
        assert m.util is False, "y no puede contar para el total de una cesta que se compra a pie"
        # 3 x 8,00 EUR son 24,00: con el umbral de 20 restarian 5,00, y por online **no resta nada**.
        assert m.coste(3, 800) == 2400, f"y el coste no baja: {texto!r}"


def test_el_umbral_por_marca_se_aplica_por_producto_y_eso_es_conservador():
    """**La decision, con su propiedad.** *No se afirma que sea exacto: se afirma de que lado cae.*

    **Dos lineas de productos DISTINTOS**, 12,00 EUR cada una, con el texto de Pascual. El motor cobra
    **24,00** -- ninguna linea llega a 15 EUR por su cuenta --, y leerlo por marca daria **19,00**.

    *El motor cobra de mas, nunca de menos.* **Y lo que esta prueba impide es el error contrario**:
    aplicarlo al ticket entero haria que el comparador prometiera descuentos que no existen.
    """
    assert lee_promo(PASCUAL).tipo == "umbral"

    # Cada linea, por su cuenta: 2 x 6,00 = 12,00, que no llega a los 15,00 del umbral.
    por_producto = cesta._coste_para(2, 600, PASCUAL) + cesta._coste_para(2, 600, PASCUAL)
    assert por_producto == 2400, "el motor no aplica el umbral a ninguna de las dos"

    # **Lo que daria leerlo por marca o por ticket**: 24,00 cruzan los 15,00 una vez.
    subtotal = 2400
    veces = subtotal // (lee_promo(PASCUAL).b * 100)
    por_marca = subtotal - veces * lee_promo(PASCUAL).a * 100
    assert por_marca == 1900

    assert por_producto >= por_marca, (
        f"la lectura del motor tiene que ser la conservadora: {por_producto} >= {por_marca}")


def test_lo_que_va_a_la_tarjeta_no_baja_el_ticket():
    """*`acumulable` se ensena y no se resta: ese dinero no se descuenta en caja.*

    Es la misma regla que la de online, y por la misma razon: **un comparador que lo reste miente sobre
    lo que se paga hoy.**
    """
    m = lee_promo("Club Alcampo 15 % dto acum en tu tarjeta")
    assert m.acumulable is True, f"tendria que reconocerse como acumulable: {m}"
    assert m.util is False
    assert m.coste(3, 1000) == 3000, "30,00 EUR de compra, y no baja nada"
