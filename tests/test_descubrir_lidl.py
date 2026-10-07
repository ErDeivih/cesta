"""El descubridor de Lidl: direcciones, no alimentos. Y no excluir comida por un slug.

Lo que se fija, que son justo las tres cosas que se pueden hacer mal con buena intencion: que el
recuento sean direcciones y se diga, que un alimento no se excluya por como se llame su URL, y que
una direccion del sitemap no se trate como prueba de que la pagina vive.
"""
from __future__ import annotations

from projects.cesta import descubrir_lidl as lidl

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.lidl.es/p/sondey-galletas-rellenas/p11000174</loc></url>
  <url><loc>https://www.lidl.es/p/leche-entera-1-l/p10012345</loc></url>
  <url><loc>https://www.lidl.es/p/taladro-percutor-750-w/p10099999</loc></url>
  <url><loc>https://www.lidl.es/p/queso-curado-cuña/p11000777</loc></url>
  <url><loc>https://www.lidl.es/h/lacteos-quesos-y-huevos/h10095761</loc></url>
  <url><loc>https://www.lidl.es/c/alimentacion/s10068374</loc></url>
  <url><loc>https://www.lidl.es/p/leche-entera-1-l/p10012345</loc></url>
</urlset>
"""


def test_lee_las_direcciones_sin_repetir():
    urls = lidl.urls_de_sitemap(SITEMAP)
    assert len(urls) == 6, "la repetida no puede contar dos veces"
    assert urls[0].endswith("p11000174")


def test_solo_las_fichas_de_producto_cuentan_como_tales():
    urls = lidl.urls_de_sitemap(SITEMAP)
    fichas = [u for u in urls if lidl.desglosa(u)]
    assert len(fichas) == 4, "las de categoria y editorial no son fichas"
    assert lidl.desglosa(urls[4]) is None


def test_el_recuento_son_direcciones_y_lo_dice():
    """6.622 URLs no son 6.622 alimentos: el informe tiene que decirlo el mismo."""
    datos = lidl.informe(lidl.urls_de_sitemap(SITEMAP))
    assert datos["cuenta"]["urls"] == 6
    assert datos["cuenta"]["fichas"] == 4
    assert datos["cuenta"]["identificadores"] == 4
    assert "no alimentos" in datos["aviso"] or "no son 6.622 alimentos" in datos["aviso"]
    assert datos["cobertura"] == "catalogo_publico_descubierto"


def test_un_alimento_no_se_excluye_por_su_direccion():
    """Excluir comida por un slug es el error caro: lo que no esta claro va a revision."""
    for url in ("https://www.lidl.es/p/queso-curado-cuña/p11000777",
                "https://www.lidl.es/p/sondey-galletas-rellenas/p11000174",
                "https://www.lidl.es/p/leche-entera-1-l/p10012345"):
        estado, _ = lidl.clasifica(url)
        assert estado != "excluido", f"{url} no puede quedar excluida por su slug"
    # El caso concreto que lo destapo, con su causa: sin tildes, "cuña" es "cuna", y habia una regla
    # de cunas de bebe con la palabra suelta. Tercera vez que esta trampa aparece en el proyecto.


def test_el_bazar_inequivoco_no_gasta_detalle():
    estado, regla = lidl.clasifica("https://www.lidl.es/p/taladro-percutor-750-w/p10099999")
    assert estado == "excluido"
    assert regla


def test_una_categoria_no_es_una_ficha_y_no_se_clasifica_como_producto():
    estado, motivo = lidl.clasifica("https://www.lidl.es/h/lacteos-quesos-y-huevos/h10095761")
    assert estado == "no_es_ficha" and motivo


def test_lo_descubierto_entra_en_la_cola_y_el_bazar_no(tmp_path):
    """El puente que faltaba: el informe se convierte en trabajo, y el bazar no genera trabajo.

    Entran incluidos y a revision (los segundos son candidatos: no se sabe, hay que mirar). Los
    excluidos por bazar inequivoco se cuentan pero no se registran: apuntarlos seria dejar pedidos
    de fichas que no se van a pedir.
    """
    from core import inventario

    con = inventario.conecta(tmp_path / "inventario.sqlite")
    datos = lidl.informe(lidl.urls_de_sitemap(SITEMAP))
    altas = lidl.registra_en_inventario(con, datos)
    registradas = con.execute("SELECT count(*) FROM fichas").fetchone()[0]
    assert altas["excluido_no_registrado"] == 1
    assert registradas == datos["cuenta"]["incluidas"] + datos["cuenta"].get("revision", 0)
    # Idempotente: volver a pasar no duplica ni una fila.
    lidl.registra_en_inventario(con, datos)
    assert con.execute("SELECT count(*) FROM fichas").fetchone()[0] == registradas
    # Y con evidencia: se sabe de donde salio cada ficha.
    assert con.execute("SELECT count(*) FROM fichas WHERE evidencia IS NOT NULL").fetchone()[0] > 0
