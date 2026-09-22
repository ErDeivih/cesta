# PROMPT para la sesión nueva (copiar y pegar tal cual)

> Este fichero es el traspaso de contexto. El prompt de abajo es **autosuficiente**:
> pégalo en un chat nuevo. El detalle técnico completo está en
> `F:\aprendizaje\scrap\docs\PLAN-UI-MATCHING.md`.

---

## PROMPT

```text
Eres un agente de desarrollo trabajando EN LOCAL sobre el proyecto `F:\aprendizaje\scrap`
(en Windows, con PowerShell). Escribe y responde SIEMPRE en español.

## Misión (encargo del dueño, ya decidido — no lo cuestiones, ejecútalo)

1. Rehacer la interfaz de la plataforma: **migrar a un stack especializado**
   (Vite + React + TypeScript; el HTML pelado actual se abandona). Mejorar
   funcionalidades, datos y gráficas de producto, y los tipos de filtros.
2. Construir la **comparación de productos entre cadenas**: elegir un producto
   general y ver las alternativas de cada cadena, con pesos.
3. **Arreglar el matching**: hoy muchos productos están mal asociados.
   **No habrá validación humana NUNCA**: tiene que ser un programa/algoritmo
   totalmente automático, con métricas y explicabilidad. Se valoran algoritmos
   avanzados y que el sistema **aprenda** con cada ejecución.
4. El orden da igual: hay que hacer **todo**.

## Lee esto ANTES de tocar código (en este orden)

1. `F:\aprendizaje\scrap\docs\PLAN-UI-MATCHING.md` ← el plan maestro del encargo:
   diagnóstico, algoritmo recomendado (Splink/EM + embeddings + asignación
   húngara + LightGBM + Outlines), modelo de datos, pantallas, fases y métricas.
2. Documentos del propio repo que contienen decisiones del dueño (si chocan con
   el plan, ganan ellos; avísame):
   `README.md`, `COMANDOS.md`,
   `docs/`: AUDITORIA, MODELO, DATOS, COMPETENCIA, CADENAS, PARIDAD,
   PARIDAD-CAMPOS, PANTALLAS, USABILIDAD, UX-MOVIL, DASHBOARD, CIFRAS,
   PRECIO-POR-UNIDAD, API, APP, FASES, OPERACION, BACKLOG (54 KB), PLAN.
3. El código: `plataforma/api/main.py`, `plataforma/web/index.html`,
   `projects/cesta/pipeline.py`, `core/normalize.py`, `core/schemas.py`,
   `core/derive.py`, y lo que exista de matching (busca `match`, `equivalen`,
   `paridad`, `competencia`).

## Entorno y cómo se ejecuta

- Gestor de paquetes: **uv**. Usa `uv run ...` (hay `pyproject.toml` y `uv.lock`).
- Almacén de datos: **DuckDB** en `data/warehouse.duckdb`; capas
  `data/raw|bronze|silver|gold` (~10,9 GB, 64.000 ficheros).
- Backend: FastAPI en `plataforma/api/main.py`; front actual:
  `plataforma/web/index.html`; hay `plataforma/docker-compose.yml` y `.env`.
- **Ollama** está instalado en la máquina (para el LLM local de los casos ambiguos).
- La GPU es una GTX 1660 SUPER de **6 GB** y **la comparten otros proyectos**:
  antes de usarla para embeddings/entrenamiento, mira si hay un cerrojo en
  `%TEMP%\vozstudio_motor.lock` y respétalo (hay una cola compartida de GPU).
- Hay una **tarea diaria de Windows** a las 06:00 que ejecuta `ejecutar.bat`
  (schtasks "Cesta diaria"). **No la rompas.**

## Leyes del proyecto (README §Reglas) — no se tocan

1. El crudo se guarda siempre y **no se toca nunca**; reprocesar debe costar minutos.
2. `fetch` / `parse` / `load` separados; `parse` es puro y testable **sin red**.
3. Idempotencia: reejecutar el mismo día no duplica filas.
4. Escalera de acceso: API interna → httpx → curl_cffi → Patchright → pagar.
5. Ritmo conservador por dominio, reintentos y pausas. **Cero datos personales.**
6. Ningún campo se queda vacío: nativo, derivado, externo o inferido.

## Cómo quiero que trabajes

- **Por fases** (las del plan). En cada fase: implementar → **tests pytest** →
  actualizar `docs/` y `BACKLOG.md` → decirme el resultado con **números**.
- **Evidencia, no opiniones**: si dices que el matching mejora, enséñame las
  métricas antes/después (precisión/recall sobre el tope que marca el EAN,
  nº de grupos con ≥2 cadenas, conflictos de asignación, estabilidad).
- Cada par emparejado debe guardar **por qué** (features + método) y ser
  **versionado**; nunca sobrescribir la ejecución anterior.
- Nada de validación humana ni pantallas de aprobar/rechazar.
- Antes de decisiones irreversibles o de mucho coste (migrar el front, tocar
  `core/fetch.py`, cambiar el contrato de la API), **pregúntame** y espera.
- Respuestas **cortas**: resultado primero, sin repetir lo que ya se ve en el
  código, tablas mejor que párrafos.
- No mezcles este proyecto con otros del equipo (por ejemplo
  `E:\Libros\VozStudio`, que es de audiolibros).

## Primer entregable que quiero de ti

**Fase 0 — Diagnóstico con números.** Sin reescribir nada todavía:
1. Cuántos productos y grupos hay hoy, cuántos grupos con ≥2 cadenas, cuántos
   pares con EAN coincidente (el tope de calidad alcanzable).
2. Cuántos pares asociados tienen unidad canónica distinta, o precio por unidad
   que difiere más de un 60 % (sospechosos), y 20 ejemplos concretos de malas
   asociaciones (con nombre, cadena y motivo).
3. Qué hace hoy el matching, archivo y función, y por qué falla.
4. Propuesta de las tablas nuevas (§6 del plan) y del orden de implementación,
   con lo que hay que decidir de mi parte (si algo).

Entrega eso como informe (y como `docs/DIAGNOSTICO-MATCHING.md`), y espera mi OK
para empezar la Fase 1.
```

---

## Notas para el dueño (no hace falta pegarlas)

- El plan completo está en `docs/PLAN-UI-MATCHING.md`; este prompt solo lo apunta.
- Si la sesión nueva se pierde en detalles, pídele lo mismo que aquí: **números
  antes/después** y que respete el **BACKLOG** y la **paridad** ya documentadas.
- El punto que más va a mejorar el matching no es el clasificador, sino
  **prohibir comparar cosas de distinta unidad/categoría y resolver la asignación
  con el algoritmo húngaro**, además de usar el **EAN** como verdad de referencia.
