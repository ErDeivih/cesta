# scrap — fabrica de datos web

Monorepo de proyectos de scraping recurrente -> limpieza -> modelado -> producto.
Proyecto 1: **cesta**, comparador de precios de supermercado.

Estado real y hoja de ruta: [docs/AUDITORIA.md](docs/AUDITORIA.md). Hoy hay tres
colectores ejecutables; DIA, Carrefour, Lidl, matching e interfaz siguen pendientes.

## Empezar (fase 1: todo local)

    uv sync
    uv run python -m projects.cesta.run --solo mercadona   # prueba una cadena
    uv run python -m projects.cesta.run                    # todas + pipeline

Tarea diaria en Windows (una vez, PowerShell como administrador):

    schtasks /create /tn "Cesta diaria" /tr "F:\aprendizaje\scrap\ejecutar.bat" ^
             /sc daily /st 06:00 /rl highest

Consultar el resultado:

    uv run python -c "import duckdb;print(duckdb.connect('data/warehouse.duckdb').sql('select * from resumen limit 20'))"

Buscar productos sin escribir SQL:

    uv run python -m projects.cesta.search "aceite de oliva"
    uv run python -m projects.cesta.search iphone --fuente alcampo
    uv run python -m projects.cesta.search leche --marca hacendado

## Estructura

    core/                libreria comun
      config.py          rutas, codigo postal, ritmo por cadena
      fetch.py           curl_cffi + rate limit + reintentos + backoff
      state.py           extractor de objetos JS embebidos en HTML
      normalize.py       formatos -> cantidad + unidad canonica (kg / l / ud)
      storage.py         raw gzip inmutable + parquet particionado
      derive.py          campos derivados del historico (Polars)
      off.py             Open Food Facts via volcado Parquet + DuckDB
      runlog.py          metricas por ejecucion + deteccion de deriva
      schemas.py         contratos Pydantic
    projects/cesta/
      collectors/        mercadona, aldi, alcampo, dia, carrefour
      pipeline.py        bronze -> silver -> gold
      run.py             orquestador local
      config.yml         tu lista de la compra
    data/                fuera de git. raw -> bronze -> silver -> gold
    docs/                PLAN, RECON, APP, PARIDAD, OPERACION, PATCHRIGHT

## Reglas

1. El crudo se guarda siempre y no se toca nunca. Reprocesar debe costar minutos.
2. `fetch` / `parse` / `load` separados. `parse` es puro y testeable sin red.
3. Idempotencia: reejecutar el mismo dia no duplica filas.
4. Escalera de acceso: API interna -> httpx -> curl_cffi -> Patchright -> pagar.
5. Ritmo conservador por dominio, con reintentos y pausas. Cero datos personales.
6. Ningun campo se queda vacio: nativo, derivado, externo o inferido, pero siempre algo.
