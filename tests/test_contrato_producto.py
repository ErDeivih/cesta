"""*** LO QUE `/api/producto` MANDA DE VERDAD, Y LO QUE EL TIPO PROMETE. ***

*M04 pide «auditar respuesta real frente a tipos TS» y «eliminar tipos que prometen campos que no
viajan».* *Aqui esta la diferencia, medida:*

    el objeto `producto` de /api/producto tiene **13 claves** (el 18/10/2026)
    el tipo `Producto` de `tipos.ts` declara **mas de 60**

*Y esa diferencia ya costo una ronda entera: el filtro de la ficha leia `producto.ean`, que **no
existe**, y por eso rechazaba hasta las coincidencias exactas.* *El defecto se disfrazo de
arreglo: la frase incorrecta desaparecia porque desaparecia **todo**.*

*** Esta prueba fija el contrato real ***: *si el servidor añade o quita un campo, se entera.*
*Y si alguien vuelve a leer `ean` de `producto`, aqui esta escrito por que no esta.*
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_el_objeto_producto_declara_su_contrato_real() -> None:
    """*Las 13 claves, escritas, para que un cambio no pase inadvertido.*

    *No se comprueba contra el servidor porque eso seria una prueba de integracion y necesita
    banco; se comprueba contra el **fixture capturado**, que es el contrato congelado.*
    """
    import json

    fixture = RAIZ / "plataforma" / "web" / "app" / "src" / "pruebas" / "fixtures" / "producto-147509.json"
    assert fixture.exists(), "falta el fixture capturado de /api/producto"
    d = json.loads(fixture.read_text(encoding="utf-8"))

    producto = d["producto"]
    esperadas = {
        "producto_id", "fuente", "grupo_id", "nombre", "marca", "cantidad", "unidad",
        "precio_cent", "precio_unidad_cent", "comparable", "nutriscore",
        "peso_escurrido_g", "precio_por_escurrido",
    }
    assert set(producto) == esperadas, (
        "el contrato de `producto` ha cambiado: "
        f"sobran {sorted(set(producto) - esperadas)}, faltan {sorted(esperadas - set(producto))}"
    )


def test_producto_NO_trae_ean_y_el_grupo_si() -> None:
    """*** La diferencia que costo una ronda. *** *El EAN esta en el miembro del grupo.*

    *Si algun dia `producto` trae `ean`, esta prueba falla y **hay que quitar el rodeo**: el
    comentario de `Producto.tsx` que explica por que se lee de `miembro` dejaria de ser cierto.*
    """
    import json

    fixture = RAIZ / "plataforma" / "web" / "app" / "src" / "pruebas" / "fixtures" / "producto-147509.json"
    d = json.loads(fixture.read_text(encoding="utf-8"))

    assert "ean" not in d["producto"], (
        "`producto` ahora trae ean: revisar Producto.tsx, que lo lee de `miembro` a proposito"
    )
    productos = d["grupo"]["productos"]
    assert productos, "el grupo tiene que traer sus ofertas"
    assert all("ean" in p for p in productos), "las entradas del grupo tienen que traer su ean"


def test_el_tipo_producto_promete_mas_de_lo_que_viaja() -> None:
    """*Y se deja escrito, porque es el motivo de la prueba anterior.*

    *No se arregla aqui: separar el tipo del objeto `producto` del tipo de una entrada del grupo es
    un cambio de contrato con seis pantallas detras, y va en M04 con su prueba por superficie.*
    *Lo que si se hace es **impedir que empeore en silencio**: el dia que alguien lea un campo del
    `producto` que no viaja, no habra una prueba que lo diga -- salvo esta, que documenta cuales
    viajan.*
    """
    tipos = (RAIZ / "plataforma" / "web" / "app" / "src" / "tipos.ts").read_text(encoding="utf-8")
    inicio = tipos.find("export interface Producto {")
    assert inicio > 0
    fin = tipos.find("\n}", inicio)
    cuerpo = tipos[inicio:fin]
    # *El tipo declara `ean`, y el objeto de /api/producto no lo trae.*
    assert "ean:" in cuerpo, "si el tipo deja de declarar ean, revisar el comentario de esta prueba"
