import polars as pl

from projects.cesta.auditar_identidad import medir


def test_auditoria_separa_identidad_formato_y_grupos_de_una_sola_cadena(tmp_path):
    gold = tmp_path / "gold"
    gold.mkdir()
    filas = [
        # Un grupo multicadena con identidad y formato consistentes.
        (1, "dia", "8410297112041", 1.0),
        (1, "carrefour", "8410297112041", 1.0),
        # Otro con distinto codigo y formato.
        (2, "dia", "8410297112041", 1.0),
        (2, "mercadona", "8410297113666", 6.0),
        # Este no es multicadena y no debe inflar los contadores anteriores.
        (3, "dia", "8410297112041", 1.0),
        (3, "dia", "8410297113666", 6.0),
    ]
    df = pl.DataFrame([
        {"grupo_id": gid, "fuente": fuente, "ean": ean, "cantidad": cantidad,
         "unidad_canon": "l", "cantidad_fiable": True, "nombre": "Leche",
         "calidad_origen": "sin_datos"}
        for gid, fuente, ean, cantidad in filas
    ])
    ruta = gold / "grupos.parquet"
    df.write_parquet(ruta)
    antes = ruta.read_bytes()

    informe = medir(tmp_path)

    assert informe["productos"] == 6
    assert informe["grupos_multicadena"] == 2
    assert informe["grupos_multicadena_con_varios_ean"] == 1
    assert informe["grupos_multicadena_con_varios_formatos_fiables"] == 1
    assert informe["particiones"] == {"bronze": {}, "silver": {}}
    assert ruta.read_bytes() == antes
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == [
        "gold", "gold/grupos.parquet"]
