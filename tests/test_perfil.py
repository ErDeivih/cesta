"""El perfil aprobado: lo que se pinta y, sobre todo, **lo que se deja fuera**.

El 6 de noviembre de 2026 se rehizo `paginas/Ajustes.tsx` como el artboard
`designs/cesta-app/project/Perfil.dc.html`. Estas comprobaciones miran el código fuente
porque son decisiones de producto que no dependen de un render:

- **La cobertura del catálogo ya no está en el perfil.** Es diagnóstico (§8) y su sitio es
  `/panel`. Se fue con su tarjeta, su import y su consulta de estado; aquí solo se vigila
  que no vuelvan.
- **Cada control que se pinta tiene una clave real donde guardarse.** El artboard también
  enseñaba «Dieta» y «Alérgenos», y no se pintan: no hay preferencia que los guarde ni
  pantalla que los lea, y un control así finge. Las tres que sí van tienen su clave.
- **El objetivo es el que lee la gráfica** (`objetivo:<fecha>`), no un 2.200 de adorno. Se
  cambia en Calorías —donde se ve el día entero— y el perfil solo lo enseña y lleva allí.
"""
from __future__ import annotations

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app" / "src"
AJUSTES = APP / "paginas" / "Ajustes.tsx"


def test_el_perfil_no_ensena_el_estado_del_catalogo():
    """Fuera la tarjeta de frescura y cobertura: es una herramienta de administración (§8).

    *Se quedó durante la primera versión de la app porque `Ajustes` era la única pantalla
    «de configuración» y allí cabía todo. El artboard aprobado no la trae, y la regla de
    David es que la app de consumo no enseña métricas de administración.*
    """
    ajustes = AJUSTES.read_text(encoding="utf-8")
    for viejo in (
        "Frescura y cobertura",   # el título de la tarjeta
        "textoCobertura",         # la frase de la medición, cadena a cadena
        "useEstado",              # la consulta que traía la cobertura
        "catálogo diario",        # un código de cobertura convertido en texto
    ):
        assert viejo not in ajustes, (
            f"«{viejo}» vuelve a estar en el perfil: la cobertura del catálogo es "
            f"diagnóstico y vive en /panel, no en una pantalla de consumo")


def test_cada_preferencia_que_se_pinta_tiene_su_clave():
    """Lo que se puede tocar se guarda; lo que no, no se pinta.

    *Las claves son las que ya lee la aplicación:* `cadenas_cerca` (buscador y panel),
    `objetivo:<fecha>` (Calorías y Tendencias) y los tres avisos, que se guardan como
    preferencias de la cuenta con el mismo `guardarPreferencia` de siempre. El objetivo es
    la única que no se escribe aquí: se enseña y se cambia en Calorías, que es donde se ve
    el día entero.
    """
    ajustes = AJUSTES.read_text(encoding="utf-8")
    assert "cadenas_cerca" in ajustes, "la cadena habitual no guarda en la preferencia de siempre"
    assert "objetivo:" in ajustes, "el objetivo no usa la clave que leen Calorías y Tendencias"
    assert 'to="/calorias"' in ajustes, "el objetivo no lleva a la pantalla donde se cambia"
    for clave in (
        "avisos_bajadas_favoritos",
        "avisos_ofertas_club",
        "avisos_lista_compartida",
    ):
        assert clave in ajustes, f"el aviso {clave} no tiene dónde guardarse"
    assert "guardarPreferencia(" in ajustes, "no se guarda ninguna preferencia"
