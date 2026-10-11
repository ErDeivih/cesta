"""F09 / `R02`: **la fuente permitida** -- el mecanismo, y que rechaza lo no declarado.

*El modulo `core/importar_receta.py` explica por que la lista empieza vacia: **nada esta permitido hasta que se
declare**, porque un importador que acepta cualquier URL no tiene politica de fuentes, tiene la politica de que
todo vale escrita en ningun sitio.*

**Y estas pruebas fijan las dos mitades**: *que **lo no declarado se rechaza con un motivo**, y que **cuando se
declara, se permite** -- sin lo segundo, un modulo que rechaza todo pasaria por bueno.*
"""
from __future__ import annotations

from core import importar_receta


def test_la_lista_empieza_vacia_y_se_puede_leer():
    """**La decision esta tomada y es visible.** *Una politica que no se puede leer no se puede revisar.*"""
    assert importar_receta.fuentes_permitidas() == {}, (
        "la lista empieza vacia a proposito: ver el docstring del modulo")


def test_una_web_no_declarada_se_rechaza_y_dice_cual():
    """**La mitad que no se puede equivocar.** *Sin esto, el importador aceptaria cualquier sitio.*"""
    p = importar_receta.comprueba_fuente("https://recetas.example.com/tortilla")

    assert not p.permitida, "una fuente no declarada no puede estar permitida"
    assert "no esta declarada" in p.motivo, p.motivo
    assert p.host == "recetas.example.com", "y el motivo dice cual, para poder declararla"


def test_declararla_la_permite_y_guarda_el_porque():
    """**La otra mitad, y la que hace que la lista sirva.** *Si declarar no cambiara nada, el mecanismo
    estaria roto en el otro sentido y las pruebas de arriba pasarian igual.*
    """
    importar_receta.FUENTES["recetas.example.com"] = "prueba de la fase 2"
    try:
        p = importar_receta.comprueba_fuente("https://recetas.example.com/tortilla")
        assert p.permitida, p.motivo
        assert p.host == "recetas.example.com"
        assert p.razon_declarada == "prueba de la fase 2", "y la razon viaja con el permiso"
    finally:
        # **Se deja la lista como estaba.** *Una prueba no puede cambiar la politica del proyecto.*
        del importar_receta.FUENTES["recetas.example.com"]


def test_el_host_no_distingue_mayusculas():
    """*Una direccion con mayusculas es la misma direccion.*"""
    importar_receta.FUENTES["recetas.example.com"] = "prueba"
    try:
        assert importar_receta.comprueba_fuente("https://RECETAS.Example.COM/x").permitida
    finally:
        del importar_receta.FUENTES["recetas.example.com"]


def test_un_esquema_que_no_vale_se_rechaza_por_su_nombre():
    """**`ftp` no es una pagina web, y `javascript:` menos.** *Y el motivo lo dice, en vez de «no vale».*"""
    for url, esquema in (
        ("ftp://recetas.example.com/x", "ftp"),
        ("javascript:alert(1)", "javascript"),
    ):
        p = importar_receta.comprueba_fuente(url)
        assert not p.permitida, url
        assert "esquema" in p.motivo, p.motivo
        assert esquema in p.motivo, f"el motivo tiene que nombrar el esquema: {p.motivo}"


def test_una_direccion_vacia_o_a_medias_no_es_una_direccion():
    """*«No es una direccion» y «la fuente no esta declarada» son **problemas distintos**, y se arreglan
    distinto: **uno se corrige, el otro se decide**.*
    """
    for url in (None, "", "   ", "https://"):
        p = importar_receta.comprueba_fuente(url)
        assert not p.permitida, f"«{url}» no puede estar permitida"
        assert "no esta declarada" not in p.motivo, (
            f"«{url}» no es un problema de politica, es una direccion que no vale: {p.motivo}")


def test_el_archivo_local_se_admite_con_ruta():
    """**El criterio dice «URL/archivo»**, asi que un `file://` con ruta se admite -- *y **sin** ruta no, porque
    un `file://` pelado no es un archivo.*
    """
    con_ruta = importar_receta.comprueba_fuente("file:///tmp/receta.html")
    assert con_ruta.permitida, con_ruta.motivo

    sin_ruta = importar_receta.comprueba_fuente("file://")
    assert not sin_ruta.permitida, "un file:// sin ruta no es un archivo"
    assert "sin ruta" in sin_ruta.motivo, sin_ruta.motivo


# ---------------------------------------------------------------------------------------------
# El borrador: la previa, que no escribe
# ---------------------------------------------------------------------------------------------


def _permitida(host: str = "recetas.example.com"):
    """*Declara una fuente y devuelve una funcion que la retira.* **Una prueba no cambia la politica.**"""
    importar_receta.FUENTES[host] = "prueba de la fase 2"
    return lambda: importar_receta.FUENTES.pop(host, None)


def test_sin_fuente_permitida_no_hay_borrador():
    """**La comprobacion va primero, y si falla no se construye nada.** *No un borrador a medias: `None`, y el
    motivo -- que es lo que permite decir «no puedo importar de ahi» en vez de enseñar una receta vacia.*
    """
    permiso, b = importar_receta.borrador("https://recetas.example.com/tortilla", {"nombre": "Tortilla"})

    assert not permiso.permitida and b is None, "sin permiso no puede salir un borrador"
    assert "no esta declarada" in permiso.motivo


def test_el_borrador_guarda_la_fuente():
    """**El criterio lo pide por su nombre** -- *«previa, **fuente**, unidades...» --, y es lo que hace que la
    receta se pueda **volver a comprobar** dentro de un ano.*
    """
    quitar = _permitida()
    try:
        _, b = importar_receta.borrador("https://recetas.example.com/tortilla",
                                        {"nombre": "Tortilla", "raciones": 2})
        assert b is not None and b.fuente == "https://recetas.example.com/tortilla", b
        assert b.nombre == "Tortilla" and b.raciones == 2
    finally:
        quitar()


def test_sin_nombre_no_hay_receta_que_previsualizar():
    """*No se inventa «Receta importada»*: **una receta sin nombre en una lista es una fila que nadie sabe que
    es.**
    """
    quitar = _permitida()
    try:
        permiso, b = importar_receta.borrador("https://recetas.example.com/x", {"raciones": 2})
        assert b is None, "sin nombre no hay borrador"
        assert "sin nombre" in permiso.motivo, permiso.motivo
    finally:
        quitar()


def test_las_raciones_que_faltan_se_dicen_y_no_se_inventan():
    """*Y las raciones son al menos una, como en `core.recetas.crear`.* **Se dice y se pone una**, en vez de
    dejar el campo en `None` y que reviente al guardar.*
    """
    quitar = _permitida()
    try:
        _, b = importar_receta.borrador("https://recetas.example.com/x", {"nombre": "Tortilla"})
        assert b is not None and b.raciones == 1, b
        assert any("raciones" in f for f in b.faltantes), b.faltantes
    finally:
        quitar()


def test_un_ingrediente_sin_texto_no_entra_y_se_nombra():
    """**La misma regla de `core.recetas._ingredientes_para_guardar`.** *No se le inventa un texto, y **no se
    tira en silencio**: se cuenta en `faltantes`, que es lo que la pantalla puede enseñar.*
    """
    quitar = _permitida()
    try:
        _, b = importar_receta.borrador("https://recetas.example.com/x", {
            "nombre": "Tortilla", "raciones": 2,
            "ingredientes": [{"texto": "patata", "cantidad": 300, "unidad": "g"},
                             {"cantidad": 2}, {"texto": ""}],
        })
        assert b is not None, "el borrador tiene que salir: hay un ingrediente bueno"
        assert [i["texto"] for i in b.ingredientes] == ["patata"], b.ingredientes
        assert len(b.faltantes) == 2, f"los dos malos tienen que contarse: {b.faltantes}"
    finally:
        quitar()


def test_el_borrador_no_escribe_ni_tiene_id():
    """**Lo que hace que se pueda mirar, corregir y tirar sin dejar rastro.** *`core.recetas.crear` escribe; esto
    **no** -- y por eso `Borrador` no tiene `id` ni version, **porque no es una receta**.*
    """
    quitar = _permitida()
    try:
        _, b = importar_receta.borrador("https://recetas.example.com/x", {"nombre": "Tortilla"})
        assert not hasattr(b, "id"), "un borrador no tiene id: no esta en ninguna base"
        assert not hasattr(b, "version"), "ni version"
        # **Y `crear` no se ha llamado**: el modulo **no importa** `core.recetas`.
        import importlib
        import sys as _sys
        importlib.reload(_sys.modules["core.importar_receta"])
        mod = _sys.modules["core.importar_receta"]
        assert not hasattr(mod, "recetas"), (
            "el modulo del borrador no puede tener la puerta que escribe")
    finally:
        quitar()
