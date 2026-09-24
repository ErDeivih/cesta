"""Darse de baja, y las dos cosas que salieron al ponerlo.

La interfaz nueva gano el boton el 24 de septiembre de 2026 (paridad con la vieja:
`app.js:1571-1603`). Al comprobarlo de punta a punta salieron **dos fallos de verdad** y un
tercero de la propia prueba, y los tres estan aqui escritos porque los tres se pueden repetir:

1. **La linea que alguien anadio a una lista ajena desaparecia de la pantalla cuando esa
   persona se daba de baja.** La fila seguia en la base (con `anadido_por` a NULL, que es lo
   que promete `borrar_usuario` en `plataforma/sql/003_mas_de_dos.sql`: *"las lineas en listas
   ajenas pierden el autor pero no desaparecen"*), pero `almacen.lineas_de` hacia
   `JOIN usuario` en el autor, asi que **no la devolvia**: la otra persona veia su compra
   menguada sin saber por que. Medido: 4 lineas en la lista, se da de baja quien anadio una,
   y la pantalla ensena 3. Arreglado con `LEFT JOIN`, como ya estaba el de `tachado_por`.

2. **La pantalla de ajustes sin sesion era un callejon sin salida.** Decia «Entra para
   cambiar tus ajustes» y **no habia ni un enlace ni un boton** (lo tenia apuntado
   `docs/DISENO.md` §3.4). Quien llegue ahi sin sesion -- un marcador, un enlace de otro
   sitio -- se queda mirando una frase. Ahora dice donde se entra, como la de favoritos.

3. **La prueba de punta a punta elegia los grupos de prueba sin desempate.** `ORDER BY
   cadenas DESC LIMIT 3` deja que DuckDB devuelva cualquiera de los empatados, y cayo en uno
   cuyo precio no estaba en su minimo de 90 dias: la alerta no saltaba y la prueba parecia un
   fallo de la aplicacion. Ahora se eligen por lo cerca que estan de su minimo, con `grupo_id`
   de desempate, que es lo que la prueba necesita para poder afirmar que la alerta salta.
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app" / "src"
ALMACEN = RAIZ / "plataforma" / "api" / "almacen.py"
E2E = RAIZ / "plataforma" / "prueba_e2e.py"


def test_una_linea_sin_autor_se_sigue_viendo():
    """`LEFT JOIN` en el autor: la baja de quien la anadio no puede vaciar la lista de otro."""
    almacen = ALMACEN.read_text(encoding="utf-8")
    bloque = almacen[almacen.index("def lineas_de("):]
    bloque = bloque[:bloque.index("def anade_linea(")]
    assert "LEFT JOIN usuario qa ON qa.id = li.anadido_por" in bloque, (
        "el autor de una linea vuelve a ser un JOIN: la linea de quien se dio de baja "
        "desaparece de la pantalla aunque la fila siga en la base")
    assert "JOIN usuario qa ON" in bloque and "LEFT JOIN usuario qa ON" in bloque, (
        "el join del autor tiene que ser LEFT")
    assert "no la devolvia" in bloque or "desaparecia" in bloque, (
        "el porque tiene que estar escrito donde se lee, no solo en el commit")


def test_la_baja_se_confirma_escribiendo_el_usuario():
    """No se puede deshacer, asi que no basta con un boton: hay que escribir tu usuario.

    Lo hacia asi la interfaz vieja y la razon sigue siendo la misma (`app.js:1573-1574`):
    un boton de "¿seguro?" se pulsa sin leer.
    """
    ajustes = (APP / "paginas" / "Ajustes.tsx").read_text(encoding="utf-8")
    assert "borrarme" in ajustes and "from '../api/cesta'" in ajustes, \
        "los ajustes no llaman a darse de baja"
    assert "variante=\"peligro\"" in ajustes, \
        "el boton de la baja tiene que verse distinto de los demas"
    assert "texto.trim() !== quien" in ajustes, (
        "el boton no comprueba que se haya escrito el propio usuario")
    assert "Quiero darme de baja" in ajustes and "No, déjalo" in ajustes, (
        "hacen falta los dos pasos: pedirlo y poder arrepentirse antes")

    cesta = (APP / "api" / "cesta.ts").read_text(encoding="utf-8")
    assert "export async function borrarme(" in cesta, \
        "no hay llamada a DELETE /api/yo"
    assert "'/yo', 'DELETE'" in cesta, "la llamada no es un DELETE a /yo"


def test_los_ajustes_sin_sesion_dicen_por_donde_se_entra():
    """Un cartel sin puerta es un callejon sin salida (`docs/DISENO.md` §3.4)."""
    ajustes = (APP / "paginas" / "Ajustes.tsx").read_text(encoding="utf-8")
    sin_sesion = ajustes[ajustes.index("Entra para cambiar tus ajustes"):]
    sin_sesion = sin_sesion[:sin_sesion.index("const cadenas")]
    assert "to=\"/cesta\"" in sin_sesion, \
        "la pantalla de ajustes sin sesion no dice por donde se entra"
    assert "Se entra desde" in sin_sesion, "y no lo dice con palabras"


def test_la_prueba_de_punta_a_punta_elige_los_grupos_con_desempate():
    """Elegirlos por numero de cadenas dejaba que la prueba dependiera del azar.

    Y el azar no es teorico: el 24 de septiembre de 2026 la prueba se puso roja ella sola
    porque habia caido en un grupo cuyo precio no estaba en su minimo de 90 dias.
    """
    e2e = E2E.read_text(encoding="utf-8")
    assert "ORDER BY (c.precio - c.minimo) ASC, c.grupo_id" in e2e, (
        "los grupos de prueba vuelven a elegirse sin criterio ni desempate")
    assert "arg_max(min_90d_cent, fecha)" in e2e, (
        "el minimo de 90 dias tiene que leerse como lo lee la aplicacion")
    assert "DELETE /api/yo" in e2e and "lineas_conservadas" in e2e, (
        "la prueba no comprueba la baja ni lo que sobrevive a ella")
