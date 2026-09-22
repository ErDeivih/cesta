# Del scrapeo al producto — plan de trabajo

Version completa y navegable publicada como artifact: "Del scrapeo al producto".
Este fichero es el resumen operativo que vive con el codigo.

## Las tres reglas

1. Guarda siempre el crudo (HTML/JSON exacto, gzip, con URL, timestamp y status).
   Cambiar el parser y reprocesar 3 anios debe costar 5 minutos.
2. El valor esta en el tiempo, no en la foto. El foso es el historico y solo se
   construye ejecutando a diario desde hoy, aunque el modelo aun sea feo.
3. Empieza estrecho: 40 productos reales en 3 cadenas funcionando a diario
   valen mas que 200.000 SKUs que se rompen el segundo martes.

## Escalera de acceso (sube un peldanio solo cuando el anterior falle)

| # | Tecnica | Cuando |
|---|---------|--------|
| 0 | API interna de la propia web (DevTools > Network > Fetch/XHR) | siempre lo primero; resuelve >50% de los casos |
| 1 | httpx + selectolax | HTML sin proteccion |
| 2 | curl_cffi (impersonate="chrome131") | bloqueo por huella TLS/JA3; ~12% -> ~80% de exito |
| 3 | Playwright / Patchright / Camoufox | SPAs, login, deteccion dura (~85-92%) |
| 4 | Proxies residenciales o API de scraping | decision economica, ultimo recurso |

Selenium no aparece: Playwright lo sustituye en todo.
Busca tambien: sitemap.xml, robots.txt, JSON-LD (schema.org), __NEXT_DATA__,
endpoints GraphQL, version movil / API de la app.

## Stack

uv · curl_cffi · selectolax · Playwright/Patchright · Pydantic v2 + Pandera ·
Polars · Parquet particionado (Hive) · DuckDB · dlt (3+ fuentes) ·
dbt-duckdb (cuando las transformaciones no quepan en la cabeza) ·
cron -> GitHub Actions -> Prefect/Dagster.

LLM para extraer: que el LLM ESCRIBA el selector, no que lea cada fila.
En produccion solo donde el dato es texto libre.

## Flujo de datos

raw (inmutable, gzip) -> bronze (parquet 1:1, tipado) -> silver (normalizado:
precio en centimos, EUR/kg y EUR/L, promociones, marcas canonicas) ->
gold (series, equivalencias entre cadenas, cesta optima, indice personal).

Anatomia de todo colector: fetch(url) -> RawResponse ; parse(raw) -> [Record]
(puro y testeable, sin red) ; load(records) -> None (idempotente y validado).

Observabilidad: run log por ejecucion + alerta de deriva (filas vs ayer, % de
nulos). Vale mas que el propio scraper.

## Proyecto 1: cesta multi-supermercado — 6 semanas

1. core/ + Mercadona a Parquet + cron diario
2. 2a y 3a cadena + run log + alerta de deriva
3. Capa silver: unidades normalizadas, promos, precio efectivo
4. Matching: EAN -> blocking -> rapidfuzz -> embeddings -> cola de revision
5. Panel Streamlit + alertas Telegram + cesta optima (PuLP/OR-Tools)
6. Anomalias de precio, indice personal, decidir version publica

Mercadona: /api/categories/ , /api/categories/<id>/ , /api/products/<id>/ ,
PUT /api/postal-codes/actions/change-pc/ para fijar almacen (los precios varian
por almacen). Resto de cadenas: DevTools > copiar como cURL > traducir a curl_cffi.

## Ideas (indice)

Personales: A1 cesta multi-super · A2 radar de electronica · A3 vivienda por
barrio · A4 valoracion de coche usado · A5 mercado laboral · A6 PVPC/luz (API
oficial ESIOS) · A7 vigilante de segunda mano.

Publicables: B1 observatorio abierto de precios · B2 buscador de nicho por
unidad util (EUR/dosis, EUR/lavado) · B3 dataset abierto + API · B4 bot Telegram /
newsletter · B5 radar de BOE, subvenciones y licitaciones.

## Legal (Espana/UE), reglas de oro

Rate limit 1-3 req/s. User-Agent identificable con contacto si publicas.
Respeta robots.txt. CERO datos personales (RGPD). Publica agregados y derivados,
nunca volcados del catalogo ajeno (derecho sui generis de bases de datos).
Si alguien pide que pares, paras.
