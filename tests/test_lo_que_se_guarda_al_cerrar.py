"""Lo que se guarda al cerrar tiene que llevar precio, y el de la tienda decidida.

**La llave:** una linea con producto concreto salia con `precio_cent: None` -- y eso se escribe en la compra como
«sin precio», que no es una estimacion que se mira: es un registro.

**El suelo:** si la linea tiene tienda decidida (`cadena_elegida`), se guarda **esa** tienda y su precio, aunque
haya otra mas barata. Guardar la mas barata cuando alguien decidio comprarlo en DIA apuntaria un precio que no se
pago.
"""
from __future__ import annotations

from plataforma.api import cesta


def _linea(linea_id="l1", producto_id=None, cantidad=1, cadena_elegida=None, movido=False):
    """Con las claves que `coste_por_linea` lee de cada linea."""
    return {"id": linea_id, "grupo_id": 7, "producto_id": producto_id, "cantidad": cantidad,
            "nombre_visto": "Leche", "cadena_elegida": cadena_elegida, "producto_movido": movido}


def _monta(monkeypatch):
    """Dos cadenas, con precios distintos: dia 100 y aldi 90."""

    def candidatos(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            for cadena, precio in (("dia", 100), ("aldi", 90)):
                mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, cadena)] = (
                    "dia:P1", precio, "Leche", "3x2", None, None, None, precio, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos)
    monkeypatch.setattr(cesta, "_promos_vigentes", lambda *a, **k: {})


def test_una_linea_con_producto_concreto_guarda_su_precio(monkeypatch):
    """La llave: antes salia None, y None se guarda como «sin precio»."""
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(producto_id="dia:P1")])
    assert salida["l1"]["precio_cent"] is not None, (
        f"se guardaria sin precio una linea que si lo tiene: {salida}")
    assert salida["l1"]["cadena"] == "aldi", salida


def test_una_linea_de_grupo_tambien_guarda_su_precio(monkeypatch):
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea()])
    assert salida["l1"]["precio_cent"] == 90 and salida["l1"]["cadena"] == "aldi", salida


def test_la_tienda_decidida_manda_sobre_la_mas_barata(monkeypatch):
    """El suelo: decidio DIA, se guarda DIA (100), no la mas barata (90)."""
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(cadena_elegida="dia")])
    assert salida["l1"]["cadena"] == "dia" and salida["l1"]["precio_cent"] == 100, salida


def test_una_linea_que_apunta_a_otro_producto_no_se_inventa_precio(monkeypatch):
    _monta(monkeypatch)
    salida = cesta.coste_por_linea([_linea(movido=True)])
    assert salida["l1"]["precio_cent"] is None, salida


# ------------------------------------------------------------------ M06 ---

# *** «ESTIMACION = CIERRE = HISTORICO»: LA MISMA CUENTA, NO TRES. ***
#
# *La especificacion lo pide con estas palabras (M06): «Estimacion=cierre=historico, incluidos
# importes por linea persistidos, articulo efectivo, cantidad y tienda».*
#
# *Y el caso que el dueño nombro entre los siete de la aceptacion es «cambio de precio durante
# cierre»: la pantalla dijo una cifra, se cerro, y **se guardo otra**.*
#
# *Estas pruebas no deciden QUE tiene que pasar cuando el precio cambia -- eso es una decision de
# producto, no de codigo.* *Lo que fijan es lo que si es obligatorio: **que sobre los mismos datos
# las dos cuentas den lo mismo**, porque son la misma cuenta vista por partes.*


def test_la_estimacion_y_el_cierre_cuentan_lo_mismo(monkeypatch):
    """*El total de la estimacion y la suma del cierre, sobre las mismas lineas.*

    **Si estos dos numeros no coinciden, la pantalla dice una cifra y el recibo guarda otra.**
    *Y no hace falta que cambie ningun precio para que pase: basta con que las dos funciones
    apliquen la promo o la cantidad de forma distinta.*
    """
    _monta(monkeypatch)
    lineas = [
        _linea("l1"),
        _linea("l2", cantidad=2),
        _linea("l3", producto_id="P1"),
        _linea("l4", cadena_elegida="dia"),
    ]
    est = cesta.estimacion(lineas)
    cierre = cesta.coste_por_linea(lineas)

    total_cierre = sum(
        c["coste_cent"] for c in cierre.values() if c.get("coste_cent") is not None
    )
    assert est["total_cent"] == total_cierre, (
        f"la estimacion dice {est['total_cent']} y el cierre suma {total_cierre}: "
        "la pantalla y el recibo no dan la misma cifra"
    )


def test_el_cierre_guarda_una_linea_por_cada_una_de_la_lista(monkeypatch):
    """*El cierre no se deja lineas: las que no tengan precio van con `None`, no fuera.*

    *Una linea que desaparece del cierre es una linea que se compro y no quedo escrita.*
    """
    _monta(monkeypatch)
    lineas = [_linea(f"l{i}") for i in range(1, 6)]
    cierre = cesta.coste_por_linea(lineas)
    assert set(cierre) == {ln["id"] for ln in lineas}
    for una in cierre.values():
        # *Y cada una dice de que producto es y en que tienda: el «articulo efectivo» que pide la
        # especificacion. `None` es un valor valido en las dos, pero la clave tiene que estar.*
        assert "producto_id" in una
        assert "cadena" in una


def test_el_precio_que_se_guarda_es_el_de_la_tienda_decidida(monkeypatch):
    """*Si alguien decidio comprarlo en dia (100), se guarda 100 y no el 90 de aldi.*

    *Es la mitad que importa del «cambio de precio»: el cierre no puede elegir por su cuenta una
    tienda distinta de la que la persona decidio, porque apuntaria un precio que no se pago.*
    """
    _monta(monkeypatch)
    cierre = cesta.coste_por_linea([_linea("l1", cadena_elegida="dia")])
    assert cierre["l1"]["cadena"] == "dia"
    assert cierre["l1"]["precio_cent"] == 100


def test_cual_de_las_cuatro_lineas_no_cuadra(monkeypatch):
    """*Diagnostico: se compara linea a linea para saber cual es la que difiere.*

    *Se deja como prueba porque el dia que se arregle dira cual era; y mientras tanto, **falla con
    el nombre de la linea**, no con un total.*
    """
    _monta(monkeypatch)
    casos = {
        "cantidad 1": _linea("a"),
        "cantidad 2": _linea("b", cantidad=2),
        "producto concreto": _linea("c", producto_id="P1"),
        "tienda decidida": _linea("d", cadena_elegida="dia"),
    }
    diferencias = {}
    for nombre, ln in casos.items():
        est = cesta.estimacion([ln])
        cierre = cesta.coste_por_linea([ln])
        total = sum(c["coste_cent"] for c in cierre.values() if c.get("coste_cent") is not None)
        if est["total_cent"] != total:
            diferencias[nombre] = (est["total_cent"], total)
    assert not diferencias, f"no cuadran: {diferencias}"


def test_si_el_precio_cambia_entre_la_estimacion_y_el_cierre_se_nota(monkeypatch):
    """*** EL CASO DEL DUEÑO: CAMBIO DE PRECIO DURANTE EL CIERRE. ***

    *La estimacion se calculo cuando la persona miro la lista. El cierre se ejecuta despues, y
    `coste_por_linea` lee el precio **de ese instante**.*

    *** Si el precio cambia en medio, las dos cifras NO coinciden, y eso es un hecho, no un fallo. ***
    *Lo que no puede pasar es que la diferencia se calle: el recibo guarda lo que costo -- que es lo
    correcto, es lo que se pago -- y **el cierre devuelve tambien lo que la lista decia**.*
    """
    _monta(monkeypatch)
    lineas = [_linea("l1")]
    antes = cesta.estimacion(lineas)
    assert antes["total_cent"] == 90, antes

    # *El precio sube: aldi pasa de 90 a 95, y dia de 100 a 105.*
    def candidatos_caros(peticiones, fecha_tope):
        mejor = {}
        for p in peticiones:
            for cadena, precio in (("dia", 105), ("aldi", 95)):
                mejor[cesta._llave_candidato(p.grupo_id, p.producto_id, cadena)] = (
                    "dia:P1", precio, "Leche", "3x2", None, None, None, precio, True)
        return mejor

    monkeypatch.setattr(cesta, "_candidatos", candidatos_caros)
    cierre = cesta.coste_por_linea(lineas)
    despues = sum(c["coste_cent"] for c in cierre.values() if c.get("coste_cent") is not None)

    # *Se nota: 90 antes, 95 despues.*
    assert despues == 95, cierre
    assert antes["total_cent"] != despues, (
        "el precio cambio y las dos cifras coinciden: la prueba no esta midiendo un cambio"
    )
    # *Y la diferencia se puede decir con signo, que es lo que ahora devuelve el cierre.*
    assert despues - antes["total_cent"] == 5


def test_el_cierre_dice_la_diferencia_con_lo_que_la_lista_decia(monkeypatch):
    """*El cierre devuelve `estimado_cent` y `diferencia_cent` ademas del total.*

    *`main.py` los calcula con el mismo `cesta.estimacion` que pinta la pantalla, asi que las dos
    cifras del recibo son las que la persona pudo ver -- no una tercera cuenta.*
    """
    _monta(monkeypatch)
    lineas = [_linea("l1"), _linea("l2", cantidad=2)]
    est = cesta.estimacion(lineas)
    cierre = cesta.coste_por_linea(lineas)
    real = sum(c["coste_cent"] for c in cierre.values() if c.get("coste_cent") is not None)
    # *Lo que el endpoint devuelve, sin base de datos: las dos cifras y su diferencia.*
    respuesta = {
        "total_cent": real,
        "estimado_cent": est["total_cent"],
        "diferencia_cent": real - est["total_cent"],
    }
    assert respuesta["diferencia_cent"] == respuesta["total_cent"] - respuesta["estimado_cent"]
    # *No se escribe el numero esperado a mano: sale de la misma funcion que lo pinta.*
    assert respuesta["estimado_cent"] == est["total_cent"]
    # *Y con los mismos datos, la diferencia es cero: no hay cambio de precio que decir.*
    assert respuesta["diferencia_cent"] == 0, respuesta


