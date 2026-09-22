from core import runlog


def test_deriva_compara_con_la_ejecucion_buena_anterior(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("tienda", 100, 0, 1.0)

    assert runlog.check_drift("tienda", 50) == (
        "[DERIVA] tienda: 50 filas hoy vs 100 la ultima vez"
    )


def test_deriva_ignora_ejecuciones_fallidas(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("tienda", 100, 0, 1.0)
    runlog.log_run("tienda", 3, 1, 1.0)

    assert runlog.check_drift("tienda", 95) is None


def test_una_captura_con_errores_tolerados_cuenta_como_buena(tmp_path, monkeypatch):
    """Lo que decide si una captura sirve de referencia es el colector.

    Carrefour da por buena una ejecucion con 4 categorias rotas de 653 y escribe
    su bronze. Si aqui se contase como mala por tener errores, su deriva no se
    vigilaria nunca -- que es lo que paso durante 19 ejecuciones.
    """
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("carrefour", 16559, 4, 1.0, completa=True)

    assert runlog.check_drift("carrefour", 11613) == (
        "[DERIVA] carrefour: 11613 filas hoy vs 16559 la ultima vez"
    )


def test_una_captura_que_el_colector_rechaza_no_sirve_de_referencia(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("carrefour", 16559, 0, 1.0, completa=True)
    runlog.log_run("carrefour", 11613, 376, 1.0, completa=False)

    assert runlog.check_drift("carrefour", 16500) is None


def test_sin_ninguna_captura_buena_el_control_lo_dice(tmp_path, monkeypatch):
    """Callar cuando no hay con que comparar es peor que no tener control."""
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("carrefour", 16433, 14, 1.0, completa=False)
    runlog.log_run("carrefour", 16486, 5, 1.0, completa=False)

    aviso = runlog.check_drift("carrefour", 11613)
    assert aviso is not None
    assert "SIN REFERENCIA" in aviso
    assert "2 ejecuciones anteriores" in aviso


def test_la_primera_vez_de_una_cadena_no_avisa_de_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "LOG", tmp_path / "runs.csv")
    runlog.log_run("otra", 100, 0, 1.0, completa=True)

    assert runlog.check_drift("nueva", 500) is None
