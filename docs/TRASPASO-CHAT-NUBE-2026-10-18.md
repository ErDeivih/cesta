# Traspaso de Cesta a un chat nuevo en la nube

Fecha de preparación: 18/10/2026. Revisión local observada: `27d87d0`.
Este documento es contexto de continuidad, no una certificación completa del software.

## Mensaje de David y propósito del nuevo chat

Quiero tener este chat en la nube para seguir el proyecto también desde el móvil.
Necesito que entiendas el repositorio y su estado real para ayudar a desarrollarlo,
revisar el trabajo de otros agentes y mantener una dirección de producto coherente.
No quiero ejercer de mensajero entre modelos ni recibir una microtarea por turno:
hay una especificación completa que se debe ejecutar por entregas funcionales.

Primero comprueba qué acceso tienes. La ruta de mi PC Windows es
`F:\aprendizaje\scrap`; no es accesible desde un chat cloud por conocer su nombre.
Si no hay repositorio conectado o adjunto, dilo y trabaja sobre los documentos
facilitados sin fingir haber inspeccionado código. Solicita una única entrega
agrupada de lo necesario. No afirmes que un agente externo sigue trabajando por
ver «objetivo activo» en un resumen: el control del proceso está en su herramienta.

## 1. Qué estamos construyendo

El repositorio `scrap` nació como una fábrica local de datos web. Su producto
principal es **Cesta**, una superapp doméstica con tres espacios separados:

1. Compra: productos, búsqueda, comparación exacta de precios, favoritos, listas,
   modo tienda, promociones, reparto de compra y gasto/histórico.
2. Recetas: recetario, edición/importación, plan semanal, ingredientes, raciones,
   envío a lista, cocina y despensa.
3. Calorías: diario personal, porciones realmente consumidas, alimentos/recetas,
   nutrición, previsiones y tendencias.

Comparten datos y puentes explícitos, no un dashboard que lo mezcle todo. Queremos
una web profesional y una experiencia móvil responsive/PWA. No hay app nativa
ni publicación en tiendas acreditadas. «Única y reconocida» es una aspiración de
producto; el código puede acreditar utilidad y calidad, no prometer popularidad.

La diferencia propuesta es conectar la semana completa: qué cocinar, cuánto se
necesita, qué hay en casa, qué envases comprar, dónde, con qué condiciones, qué
sobra y qué porción comió cada persona. Cada cifra debe poder explicarse.

Soy David, estoy aprendiendo ingeniería y ciencia de datos. Necesito documentación
didáctica sobre extracción, limpieza, capas, bases, unidades, matching, algoritmos,
promociones, evaluación y gráficas, con ejemplos reproducibles y límites reales.

## 2. Alcance comercial y reglas fundamentales

- Supermercados de España: Mercadona, DIA, Aldi, Alcampo, Carrefour y Lidl.
- Núcleo: comida/bebidas/frescos, higiene, limpieza, bebé, mascotas y consumibles
  domésticos. Reutilizables cotidianos pueden tener sección optativa. No bazar
  de televisores, muebles o grandes electrodomésticos.
- **Artículo exacto no es familia ni alternativa.** Marca, variante, sabor, pack,
  presentación y cantidad importan. El mismo nombre no prueba identidad.
- Una alternativa barata necesita aceptación explícita y revocable. Sin dato no
  se afirma identidad ni diferencia; las relaciones tienen estado desconocido.
- Identidad, comparabilidad del precio y elegibilidad de la oferta son decisiones
  separadas. No restar €/kg de €/ud ni neto de escurrido sin base acreditada.
- Club, fechas, región/canal y cantidades afectan al coste final. No presentar
  cesta parcial como ganadora por omitir lo que falta.
- Ausencia en una captura no demuestra agotado ni retirado. Lidl parcial puede
  aportar ofertas válidas, pero no se presenta como catálogo completo.
- Compra, plan, preparación y consumo son eventos distintos. Comprar no registra
  automáticamente calorías ni que toda la familia se comió todos los envases.
- Desconocido no es cero. No inventar nutrición, densidad, cantidades, precios,
  alérgenos, coste de viaje ni objetivos médicos.
- Precio estimado por catálogo no demuestra dinero pagado en caja. Hay que
  distinguir importes calculados, declarados o acreditados y su procedencia.
- Recetas privadas por defecto; diario personal y permisos por sesión. Compartir
  listas del hogar no autoriza a ver nutrición privada de otro usuario.

## 3. Stack y mapa del repositorio

Todo se desarrolla inicialmente en local para evitar gastos.

- Python con `uv`; HTTP/parser con httpx, curl_cffi, selectolax y Patchright para
  navegación cuando corresponde, sin evasión de restricciones de acceso.
- Pydantic para contratos; Polars/PyArrow/Parquet para procesado; DuckDB para
  consultas analíticas. SQLite para estado privado de recetas/diario según módulos;
  PostgreSQL para cuentas, listas, compras y demás estado de la plataforma.
- API FastAPI, frontend React + TypeScript + Vite + Tailwind 3; TanStack Query/Table
  y uPlot. Node 24 se ha usado para pruebas TS con strip-types.
- Ya se han añadido ESLint/hooks, Vitest, jsdom y Testing Library. No seguir diciendo
  que no hay herramientas de componentes: revisar `package.json` actual.
- Docker Compose: PostgreSQL 16, API y Caddy. Web habitual `http://localhost:8080`;
  API tras `/api`. Código local nuevo no implica imagen o bundle servido nuevo.
- dbt-duckdb figura entre dependencias opcionales. No afirmar que dbt/Dagster son
  la orquestación actual sin comprobarlo: el runner diario es Python/local.

Rutas importantes del repositorio:

| Ruta | Responsabilidad |
| --- | --- |
| `core/` | Fetch, normalización, contratos, calidad, identidad, nutrición, recetas, diario, despensa y operaciones |
| `projects/cesta/collectors/` | Los seis colectores |
| `projects/cesta/run.py` | Runner diario, control de ejecución y cadenas |
| `projects/cesta/pipeline.py` | Construcción de capas y artefactos analíticos |
| `data/` | Raw, capas, publicaciones, registros y datos locales; mayoritariamente fuera de git |
| `plataforma/api/` | FastAPI, catálogo, identidad/coste, listas, recetas, diario y permisos |
| `plataforma/sql/` | Migraciones PostgreSQL |
| `plataforma/web/app/src/` | Interfaz actual; `App.tsx` rutas, `componentes/Suite.tsx` navegación servida |
| `plataforma/web/app/src/logica/` | Cálculos puros y contratos del cliente |
| `plataforma/web/app/tests/` | Pruebas del frontend |
| `plataforma/ensayo.py` | Entornos de ensayo aislados y guardas |
| `tests/`, `scripts/aceptacion_*.py` | Tests Python y aceptaciones |
| `docs/aprende/` | Material didáctico existente |

Cadena conceptual: fuente web → raw preservado → bronze → silver normalizada →
gold/derivados publicados por versión → API → interfaz. La frescura del precio y
la antigüedad de ingredientes/detalles se deben controlar por separado.

## 4. Documentación que manda

Leer primero, completos:

1. `docs/SUPERAPP-GOAL-ACTUAL.md`.
2. `docs/SUPERAPP-ESPECIFICACION-MAESTRA-2026-10-18.md`.
3. `docs/SUPERAPP-EJECUCION-2026-10-18.md`.

La especificación define **23 paquetes M00–M22**, pantallas, contratos, pruebas y
criterios de entrega. Los documentos contienen entradas sucesivas: revisar fechas,
commits y últimas correcciones; el primer bloque del estado puede haberse quedado
atrás. Si se contradice la máquina, manda evidencia actual identificada.

Complementos: `docs/DICTAMEN.md`, `docs/ui/DIRECCION.md`,
`docs/ui/VERSION-SERVIDA.md`, `docs/ui/COMO-SE-MIDE.md`, `docs/LIDL.md`,
`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md` y `docs/aprende/`.
El plan B00–B16 es antecedente, no sustituye M00–M22.

IMPORTANTE: al preparar este traspaso, la especificación maestra está **sin
seguimiento en git** y el goal tiene cambios locales. Un clon remoto puede no
contener el encargo vigente: hay que adjuntar esos documentos o sincronizarlos
con autorización, no asumir que el nuevo chat ya los recibe.

## 5. Lo que existe y los últimos errores corregidos

Hay mucha implementación, no un prototipo vacío: pantallas de las tres apps,
listas compartidas, recetas/versiones, plan, cocina, diario, motor de coste,
colectores y numerosas pruebas. Pero abrir rutas no acredita el recorrido entero.

Problemas importantes descubiertos en revisiones recientes:

- La ficha quedaba en blanco porque un `useMemo` se ejecutaba después de retornos
  condicionales. Corregido en `67c0348`; después se instalaron las reglas de hooks
  y las herramientas de componentes. No volver a usar una regex como sustituto.
- Se comparaba azafrán Pote de DIA con Hacendado de Mercadona como mismo producto.
  EAN/identidad, alternativas y bases de precio se fueron separando.
- La API no enviaba EAN en `producto`; estaba en `grupo.productos`. Un filtro
  aparentemente seguro eliminaba todas las coincidencias. Ahora se resuelve el
  miembro por fuente/id y hay que verificar el contrato real.
- 0,4 g se presentaban como «0 kg». Corregido el formato de cantidades pequeñas.
- Diferencias de €/kg se anunciaban como euros ahorrados por envase. Se separaron
  magnitudes y se auditó el uso de estadísticas del grupo en pantallas.
- Estimación y cierre discrepaban al ignorar la tienda elegida. Después se detectó
  que una tienda sin oferta se cambiaba por otra silenciosamente: se corrigió para
  conservar ausencia/motivo y ofrecer alternativas sin elegirlas.
- Había un viaje fijo de 1,50 EUR no introducido por la persona. Se retiró como
  default; viaje/neto desconocidos son null y cero introducido es cero conocido.
- El medidor de identidad convertía `None` en negativo; después incluía los
  desconocidos en el denominador de precisión. Ambos defectos se corrigieron.

No trasladar estas frases al nuevo chat como fallos todos vigentes: son contexto
de por qué los contratos actuales son estrictos. Comprobar su estado antes de tocar.

## 6. Estado MÁS RECIENTE: avances posteriores al último resumen pegado

HEAD observado: **`27d87d0`**. Hay cambios posteriores a `758cec8`:

- `6fba6f0`: precisión sobre pares evaluables; cotización del carrito y no toda la
  lista; cliente de cierre con sello y campos nullable alineados. Añade
  `scripts/aceptacion_m06_cierre.py`.
- `b979e87`: registra aceptación por HTTP de cotización → confirmación → persistencia.
- `ed7d539`: corrección de una prueba de rutas y suite declarada en verde.
- `99bdafe`: sello con versión de catálogo y uso de `por_linea` de la cotización
  en el cierre, evitando otro cálculo de precios; ampliación del ensayo de publicación.
- `27d87d0`: documenta el estado y límites de esa entrega.

El seguimiento declara que la aceptación HTTP pasa: GET entrega sello, sello
incorrecto da 409 sin compra escrita, sello correcto confirma y conserva total,
publicación nueva invalida la previa y devuelve otro sello. El modo sin sello se
conserva como cierre no confirmado. No describirlo como protección obligatoria de
toda llamada ni presentar ese modo como confirmación de una previa.

Estas afirmaciones proceden de código/commits y del seguimiento de DeepSeek;
**GPT no ha reejecutado esa aceptación HTTP ni toda la suite al preparar el traspaso**.
El último resultado global declarado es 2.125 Python, 17 skipped, 0 fallos; recuentos
frontend anteriores: 113 Node y 15 componentes. Repetir lo relevante antes de
usar cifras como evidencia actual. Un skip debe tener razón y alcance.

Siguen pendientes explícitos de M06:

1. Serializar cierres y cambios concurrentes dentro de la transacción y asegurar
   que un reintento no crea otra compra. El almacén aún relee líneas.
2. Prueba de componente de la UI mostrando 409 y pidiendo reconfirmación.
3. Verificar procedencia del importe de extremo a extremo: que la respuesta diga
   «calculado» no demuestra por sí sola una migración/persistencia histórica completa.
4. Auditar que el ensayo de publicación realmente cubra cada ventana de carrera
   que afirma; no elevar su resumen a garantía sin leer el escenario.

## 7. Fuentes y estado de ingestas

Hay una tarea Windows «Cesta diaria», runner con lock, logs y publicación versionada.
No lanzar otra captura sin comprobar actividad real. Conservar último válido si
falla una fuente, con fechas y cobertura explícitas.

Último `runs.csv` leído del 18/10:

| Fuente | Filas | Errores | Aceptada |
| --- | ---: | ---: | --- |
| Lidl | 79 | 0 | Sí, cobertura parcial |
| Carrefour | 0 | 1 | No |
| Aldi | 2695 | 0 | Sí |
| Mercadona | 4215 | 0 | Sí |
| DIA | 5757 | 0 | Sí |
| Alcampo | 22802 | 0 | Sí |

Son filas de ejecución, no necesariamente productos distintos del catálogo final.
Foto anterior de API del mismo día: publicación `20261018-131107`, Carrefour con
datos del 17 y las demás del 18. No se ha vuelto a consultar ese endpoint en esta
preparación. Catálogo aceptado, precio fresco y catálogo completo son tres cosas.

Lidl está integrado en el runner, pero la captura actual es de ofertas semanales,
no todo el surtido. Debe ampliarse respetando acceso público, región, IAN/EAN y
campañas; no usar «tantos como Aldi» como medida artificial de completitud.
Carrefour del 18 es un caso real pendiente de diagnóstico/revisión de recuperación.

Queremos detalles ricos de todos los artículos dentro de alcance, también
históricos: ingredientes, alérgenos, nutrientes y base, presentación, pesos,
conservación, origen y especificaciones. Cola incremental por nuevos/cambiados/TTL,
no descargar todas las fichas estables cada madrugada ni inventar campos ausentes.

## 8. Hoja de ruta que NO se debe reducir a microarreglos

| Paquetes | Entrega |
| --- | --- |
| M00–M04 | Sandbox, comparación, tests reales, puente diario y contratos/publicación |
| M05–M08 | Compra, coste/promociones, identidad automática y favoritos/avisos |
| M09–M13 | Recetario, plan, necesidades/envases, cocina/despensa y diario |
| M14–M18 | Gráficas, PWA/offline, ingestas/Lidl, fichas ricas y operación |
| M19–M22 | Seguridad/copias, rendimiento, aprendizaje y release candidate |

Muchos módulos ya existen. «No iniciado» en una aceptación no significa que haya
que rehacer toda la capacidad. Auditar, reutilizar y cerrar sus huecos.

**M07:** construir al menos 200 pares estratificados de identidad, con snapshots,
autoría y evidencia; separar ajuste/evaluación, desconocidos y pseudoetiquetas.
El agente está autorizado a anotarlos con procedencia declarada. No necesita
esperar una nueva autorización humana ni usar la salida del motor como verdad.
Si no hay evidencia suficiente, marcar desconocido, mostrar déficit y continuar.

## 9. Escenario de aceptación principal

Cinco recetas de dos raciones, dos personas y dos listas. R1=150 g arroz seco;
R2=200 g del mismo arroz; R3=500 ml leche; R4=0,5 l de la misma leche; R5=3 huevos.

- Arroz: 350 g requeridos, despensa confirmada 100 g, déficit 250 g; comprar un
  envase de 1 kg deja 750 g de ese envase tras cubrirlo.
- Leche: 1 l, una botella. Huevos: un pack de seis, sobran tres.
- Cambiar raciones de una ocurrencia escala solo esa ocurrencia; marcas distintas
  no se consolidan sin permiso; ingrediente sin catálogo permanece pendiente.
- Nutrición sintética: arroz 360 kcal/100g, leche 60 kcal/100ml, huevos 80 kcal/ud.
  Preparaciones 2100 kcal; una ración de cada una 1050, no toda la dieta semanal.
  Una ración R1=270 kcal; media=135.
- Comprar no genera entradas de diario. Confirmar consumo sí, con snapshot,
  permisos, recarga e idempotencia. Proteína conocida no desaparece por faltar kcal.

También: 3x2 de tres envases a 100 céntimos =200, aunque se reparta en líneas 1+2;
ofertas de club/vencidas/otra región; coste por envase frente a ingrediente usado;
publicación durante uso; offline; cuenta B no ve lo privado de A.

## 10. Precauciones y forma de trabajar

- Preservar cambios ajenos. En el árbol hay modificaciones locales en secciones,
  CIFRAS, controles y goal; documentos/scripts nuevos sin seguimiento. No resetear,
  restaurar con checkout ni hacer `git add .` para limpiar el árbol.
- No tocar facylf ni su PostgreSQL 5433; casa 5432 y ensayos compartidos 5434 no
  son destinos de restauración. Usar sandbox propio con nombre/puerto/DSN verificados.
- No pagar, publicar internet, abrir puertos externos ni subir datos/credenciales.
  No reutilizar tokens pegados en el historial. No enviar diagnósticos privados.
- No reset/prune de Docker ni borrado de volúmenes. El 14/10 se reparó un arranque
  de Docker reiniciando WSL y apartando solo su carpeta de socket temporal; no fue
  una reparación de datos. Estado del motor se comprueba al retomar, no se supone.
- Las dependencias gratuitas de desarrollo y cambios normales del repositorio
  están autorizados. No preguntar cada vez que haya que añadir un test o selector.
- Mantener stack y diseño propios: marfil/papel, bosque/terracota y tipografías
  locales. No reescribir app/framework por una preferencia estética.
- Unidades/pruebas/compilación no sustituyen HTTP con datos, componente montado,
  navegación y revisión visual. «No hay errores consola» no prueba que haya ficha.
- No hacer una ronda de bitácora por cada línea. Estado corto, evidencia y siguiente
  comando. Si hay bloqueo externo, continuar tareas independientes de M00–M22.

## 11. Comandos orientativos, no órdenes de ejecutar todo a ciegas

Desde raíz:

```powershell
git status --short
git log -5 --oneline
uv run ruff check .
uv run pytest -q
uv run python -m plataforma.comprueba_documentos
uv run python -m scripts.auditar_cierre_y_banco_20261018
```

Frontend, desde `plataforma/web/app`:

```powershell
npm run lint
npm run tipos
npm test
npm run test:componentes
npm run build
```

Consultar primero `plataforma/ensayo.py`, instrucciones del repo y los scripts de
aceptación antes de arrancar entornos o ensayos HTTP. No ejecutar un ejemplo viejo
contra 5434 ni usar los datos domésticos como fixture. No duplicar ingesta diaria.

## 12. Qué debe recibir un chat realmente alojado en la nube

Este traspaso + especificación maestra + estado de ejecución + goal actualizado.
Para analizar código: repositorio conectado o copia de fuentes actual, con commit
y cambios locales relevantes identificados. Para reproducir parsers: pocas muestras
raw autorizadas/anonimizadas, no toda la carpeta data.

Excluir `.env`, cookies, tokens, perfiles del navegador, bases privadas, copias,
diarios nutricionales reales, node_modules y .venv. No subir automáticamente nada
por el mero hecho de preparar este resumen. Si el chat solo tiene este documento,
debe distinguir información recibida de evidencia que él mismo haya comprobado.

Primera acción recomendada: verificar acceso y revisión; leer los tres documentos
vigentes y últimas entradas; terminar concurrencia/reconfirmación de M06; construir
M07; continuar el programa amplio. El objetivo sigue siendo la superapp completa,
no convertir el cierre de compra en una investigación indefinida.
