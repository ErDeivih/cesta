# Cesta — backlog vivo

Escrito el **4 de noviembre de 2026**, a partir de lo **medido** en esta sesión, no de lo
que dice un documento. El backlog histórico y las fichas largas siguen en
`docs/BACKLOG.md` (17/09/2026) y en `docs/SUPERAPP-EJECUCION-2026-10-18.md`: son
contexto y evidencia, no estado.

Regla del protocolo: **nunca menos de 5 tareas listas**, y una tarea bloqueada no para la
sesión — se marca y se sigue con la siguiente.

---

## El estado, en una línea

El catálogo son **52.982 productos** (medido hoy) y la comparación **existe**. Dos fotos, con su
denominador, porque no son lo mismo: en la de las 14:30, **8.864 grupos** con precio en 2+ cadenas
(22,9 % de 38.682 comparables); medido sobre el día con `precio_comparable` e **importe no nulo**,
**8.829 de 39.115 grupos** del 4/11 tenían 2+ cadenas (22,6 %; contando también las 760 filas del
día sin importe salen 8.851 de 39.837, que es la cifra que se citó antes). La cobertura dejó de ser un
rumor de un solo sitio: desde el 4/11 **las cinco cadenas de catálogo declaran su día, medido
sobre su bronce** (`data/cobertura/`), y `GET /api/estado` enseña las seis. Lo que se cae es
**la automatización**: la tarea `Cesta diaria` apunta a `F:\aprendizaje\scrap`, que ya no
existe tras el movimiento de hoy. El detalle y el arreglo (hace falta administrador), en
`docs/COBERTURA-DIARIA-2026-11-04.md` §11 y en la tarea 12 de aquí.

---

## Las tareas

### 1. Recuperar el día de Alcampo y que un folleto no cueste un día de precios — **hecho (04/11)**

- **Por qué**: el 4/11 Alcampo trajo **23.416 productos con 0 errores** y su bronze no se
  escribió: el control de cobertura vio `Folletos y Promociones: 1472 -> 727` y tiró la
  captura entera. El folleto de la campaña no es una estantería; las otras 15 ramas de
  comida **subieron** (Frescos +6 %, Perfumería +10 %, Droguería +15 %, Bebé +38 %).
- **Qué se ha hecho**: `core/cobertura.py` separa lo que **avisa** (`revisa`) de lo que
  **veta** (`que_vetan`); las ramas de folleto van en `RAMAS_DE_CAMPANA` y no vetan. Los
  cinco colectores usan la misma regla. Una rama de estantería hundida **sigue vetando**
  (el caso Frescos del 18/09/2026 está como prueba de regresión).
- **Cómo se sabe que está bien**: `tests/test_cobertura_honesta_20261104.py` (8 pruebas) y
  el día recuperado desde el crudo con `uv run python -m projects.cesta.reprocesar
  --fuente alcampo --fecha 2026-11-04` → **23.416 productos** en bronze y **23.405** en gold.
- **Siguiente comando**: `uv run python -m projects.cesta.cobertura_diaria`

### 2. La vara de la cobertura la fija un día atípico — **pendiente, decisión de política (nivel 2)**

- **Por qué**: la referencia es el **máximo de 30 días**. Alcampo hizo **28.022** el
  17/10/2026 cuando lo normal era 22.800–24.300, y desde entonces **toda** captura sale
  «corta»: la de hoy son 23.416 contra 28.022 = 83,6 %, aunque sea **+2,8 % sobre ayer**.
  Un aviso que salta todos los días deja de ser un aviso.
- **Qué falta decidir**: o se cambia la referencia a un percentil (p90 sigue cazando la
  bajada lenta del caso Alcampo y deja de cazar un día suelto), o se marca el día atípico
  como tal y se informa. **No se ha cambiado el umbral por cuenta propia**: bajar una
  guarda de seguridad es decisión de producto, y debilitarla a escondidas es peor que el
  ruido.
- **Ya hecho, sin cambiar el umbral**: el veredicto dice **de qué fecha** es la vara y
  **cuánto cambió** contra la captura anterior (`referencia_fecha`, `vs_anterior_pct`).
- **Cómo se sabe que está bien**: `pytest tests/test_cobertura_diaria.py
  tests/test_cobertura_honesta_20261104.py` y el informe deja de inducir a error.

### 3. Lidl de verdad: 91 productos no son una cadena — **pendiente, con llamada real antes de escribir**

- **Por qué**: Lidl aporta **91 productos** y **52 grupos** de 8.864 comparables: 0,6 %.
  `data/cobertura/lidl-*.json` dice lo que es — «ofertas semanales parciales», no catálogo.
  La especificación (M16) pide **cobertura demostrada**, no un número.
- **Qué hay que hacer**: **una** llamada real a la vía que `docs/COLECTORES.md` §4.5 deja
  anotada (`stores.lidlplus.com`, `offers.lidlplus.com`). Si solo da las ofertas de la
  semana, se escribe y se cierra el asunto; si da surtido, se abre colector. **No se
  escribe código antes de esa llamada** (es la lección de `docs/LIDL.md`).
- **Cómo se sabe que está bien**: fichero con la respuesta y su fecha, y una decisión
  escrita con el número de productos que aporta de verdad.

### 4. Sandbox de PostgreSQL: las 50 pruebas de base siguen sin correr — **pendiente, bloquea el dictamen**

- **Por qué**: el stack está arriba (`cesta-db-1` sana) pero **esa es la base de casa**
  (`127.0.0.1:5432`, usuarios, listas, diario) y la especificación prohíbe restaurar sobre
  ella. Las **50 pruebas** que necesitan PostgreSQL — y con ellas el **cierre de compras de
  dos listas** de §8 — no se pueden dar por verdes sin un entorno desechable.
- **Qué hay que hacer**: M00 tal y como está escrito: PostgreSQL propio en loopback, puerto
  libre, **marcador de pertenencia**, DSN verificado en cada subproceso, y `CESTA_POSTGRES`
  apuntando ahí. Nunca matar «el proceso del puerto».
- **Cómo se sabe que está bien**: `CESTA_POSTGRES=<sandbox> pytest -q` → 2.149 recogidas,
  0 saltos por base, y el escenario §8 de dos listas en verde.

### 5. Que la cobertura medida llegue a la API y a la pantalla — **hecho (04/11)**

- **Por qué**: ya viajaba en el manifiesto (`cobertura_medida`), pero `/api/estado` solo decía
  `al_dia: true/false` por cadena. La persona que mira la app no podía ver que Alcampo trajo
  23.416 de 23.416 productos y que Carrefour dejó 3 días de 30.
- **Qué se ha hecho**: (a) cada cadena de catálogo **declara su cobertura medida** en
  `data/cobertura/<fuente>-<fecha>.json` —filas, referencia y su fecha, %, huecos, veredicto y
  novedad del día—, y la API ya servía esa carpeta: no hizo falta tocar el endpoint;
  (b) pantalla viva `Ajustes.tsx` con la tarjeta «Frescura y cobertura de los precios», una
  fila por cadena («catálogo diario · 4272 filas · 98,9 % de su referencia del 5 oct · 71
  precios cambiados»); (c) `Cabecera.tsx` resultó **código muerto** (lo sustituyó `Suite.tsx`)
  y no se tocó: la pieza que se entregó es la de la pantalla viva.
- **Cómo se sabe que está bien**: `GET http://127.0.0.1:8080/api/estado` devuelve `cobertura`
  para las 6 cadenas (medido el 4/11); `npm run tipos` limpio, `npm test` 376/376,
  `npm run test:componentes` 24/24 (incluye `Ajustes.test.tsx`), build servido en `:8080`.

### 6. Corregir la ficha del agente, que daba el estado al revés — **hecho (04/11)**

- **Por qué**: `AGENTE.md` decía «cobertura diaria: **solo Lidl**, 21 días». Medido: Mercadona
  32 días, Aldi 32, Carrefour 31, DIA 29, Alcampo 21, Lidl 21 (ventana desde el 1/10). El error
  venía de leer `cobertura_declarada`, donde solo escribía Lidl.
- **Qué se ha hecho**: la tabla está corregida con fecha de medición; y desde hoy la raíz del
  problema está cerrada: **las 5 cadenas de catálogo escriben su declaración**, así que
  `cobertura_declarada` ya no puede leerse como «solo Lidl».
- **Cómo se sabe que está bien**: `docs/COBERTURA-DIARIA-2026-11-04.md` §1 reconcilia las
  cifras con `AGENTE.md` y `CIFRAS.md`, y la medida se repite con el script de la tarea 11.

### 7. Carrefour: 3 días de 30 sin captura y un error de catálogo crónico — **pendiente, diagnóstico barato**

- **Por qué**: hoy trae **16.782** (99,9 % de su referencia) y **1 error**: `HTTP 520` en
  `cat32482101` (congelados/comidas del mundo), que ya se reintentó sin éxito. En la ventana
  de 30 días le faltan 3. El 18/10 fue la resistencia de Cloudflare, ya documentada.
- **Qué hay que hacer**: decidir si esa categoría está **rota en origen** (marcarla, como
  `ROTAS_EN_ORIGEN`) o si es transitoria; y que un día sin captura **se diga** en el estado
  de la cadena.
- **Cómo se sabe que está bien**: el resumen del día nombra la categoría y el estado de la
  cadena no la cuenta como catálogo.

### 8. 47 categorías nuevas sin mapear a pasillo — **pendiente, XS**

- **Por qué**: el resumen diario lo dice todos los días («categorías nuevas, sin mapear: 47»)
  y hay **197 claves de Alcampo** esperando decisión a mano en «Folletos y Promociones >
  Turrones y dulces Navideños». Sin sección, esos productos caen al final de la lista.
- **Qué hay que hacer**: pasarlas por `auditar_secciones` y aplicar las que tengan rama
  clara; las demás, con decisión escrita.
- **Cómo se sabe que está bien**: el resumen deja de contarlas y la lista de la compra sigue
  teniendo pasillos.

### 9. La CI no se ha ejecutado nunca en remoto — **pendiente, decisión de nivel 3**

- **Por qué**: el repositorio se trabaja en local; los tres trabajos están leídos del YAML,
  no ejecutados. «La CI pasa» es hoy una afirmación de documento.
- **Qué falta**: decidir si se sube el repositorio y se deja correr, o se ejecuta el mismo
  YAML en local con `act` (dependencia nueva → nivel 2/3).
- **Cómo se sabe que está bien**: un run real con su enlace, o la decisión de no tener CI
  remota escrita y el comando local que la sustituye.

### 10. Los dos cierres a la vez de M06 — **bloqueada por la tarea 4**

- **Por qué**: «dos cierres concurrentes pueden crear dos compras» sigue abierto en el
  servidor, y es el único motivo del NO APTO del piloto.
- **Qué hay que hacer**: prueba HTTP real sobre sandbox (no dobles) y serialización en la
  transacción; el reintento no puede crear otra compra.
- **Cómo se sabe que está bien**: la prueba falla con el código de antes y pasa con el de
  después, y la fila se escribe una sola vez.

### 11. Demostrar que el ciclo produce datos nuevos, con auditoría reproducible — **hecho (04/11)**

- **Por qué**: la petición era «demuestra que produce datos nuevos todos los días», y hasta
  hoy eso se afirmaba de memoria: no había un instrumento que midiera presencia, novedad y
  frescura por cadena y día, ni una comprobación de que las declaraciones dicen lo mismo que
  el bronce.
- **Qué se ha hecho**: `scripts/auditar_cobertura_diaria.py` (ventana configurable; por
  cadena y día: partición de bronce, filas bronce/gold, mtime, pasada en `runs.csv` y novedad
  sobre bronce —nuevos/cambiados/desaparecen— con la misma cuenta sobre gold al lado);
  `--exigir-dias N` para usarlo como puerta estricta (sin la bandera mide y sale 0: un hueco
  ya conocido no puede gritar todos los días). Evidencia en
  `docs/COBERTURA-DIARIA-2026-11-04.md` (tablas de 30 días y novedad de los últimos 7) y CSV
  en `data/debug/auditoria-cobertura/` (fuera de git), perfilado y verificado con
  `data_profile`/`data_verify` (unicidad `(fuente,fecha)`, sin nulos en claves; reportKeys en
  la doc).
- **Cómo se sabe que está bien**: el script corre de punta a punta; `verificar_evidencia.py`
  comprueba que la novedad sobre bronce del 4/11 coincide con las 5 declaraciones; `pytest` y
  `ruff` en verde. El resultado honesto: **128 días-cadena con captura, 124 con novedad ≠ 0,
  128/128 escritos el mismo día**; los 4 días idénticos son de Aldi.
- **Límite**: la auditoría mide el dato, no la causa de cada hueco (tarea 13).

### 12. La automatización diaria apuntaba a la ruta vieja — **hecho (04/11, 19:18)**

- **Por qué**: el proyecto se movió de `F:\aprendizaje\scrap` a `F:\Proyectos\cesta` el 4/11
  (commit `b8425ae`, 14:20). La tarea del Programador `Cesta diaria` seguía apuntando a
  `F:\aprendizaje\scrap\ejecutar.bat`, que **ya no existe**: última ejecución 4/11 15:31 con
  `0x80070003` (`ERROR_PATH_NOT_FOUND`). `ejecutar.bat` es portable (`cd /d "%~dp0"`); lo que
  estaba mal era solo el registro de la tarea.
- **Qué se ha hecho**: David la re-registró como administrador
  (`powershell -ExecutionPolicy Bypass -File F:\Proyectos\cesta\registrar-tarea.ps1`), que el
  agente no podía (`Set-ScheduledTask` → «Acceso denegado»).
- **Cómo se sabe que está bien (medido 4/11, 19:18)**: acción `F:\Proyectos\cesta\ejecutar.bat`
  con directorio `F:\Proyectos\cesta`, 3 disparadores (diario 06:00, al arrancar, al iniciar
  sesión), `State Ready`, `NextRunTime 2026-11-05 06:00`; y un disparo manual
  (`Start-ScheduledTask`) terminó con **`LastTaskResult 0`** en 8 s (el día ya estaba hecho, así
  que `ejecutar.bat` salió al instante sin red). La próxima pasada real es la del 5/11 por la
  mañana.

### 13. Alcampo: 14 de los 35 días desde el 1/10 sin precio — **pendiente, diagnóstico**

- **Por qué**: en la ventana de 30 días Alcampo tiene **20/30** capturas (la peor de las
  cinco); en todo el histórico hay **3 días con pasada buena y sin partición** (Alcampo
  18/09, 02/10 y 05/10: «trajo y no escribió») y **8 de los 15 días con pasada fallida** en la
  ventana son suyos. El 4/11 se recuperó del crudo (tarea 1), pero los días 27–29/10 no.
- **Qué hay que hacer**: separar por día «no capturó» (red/WAF) de «capturó y la guarda vetó»
  (bronce existe, no se escribió) leyendo `data/ejecuciones.log`; si el crudo de esos días
  sigue en `data/raw/`, recuperarlos con `reprocesar` como se hizo el 4/11.
- **Cómo se sabe que está bien**: el veredicto de la cadena dice el motivo del día que falta,
  no solo que falta, y los días recuperables están en gold.

### 14. Retención de las declaraciones de cobertura — **pendiente, XS**

- **Por qué**: `data/cobertura/` crece ~5 ficheros/día (~1 KB cada uno) y el manifiesto los
  lista todos (~1,8 MB al año). Hoy es aceptable y no se borra nada sin decisión escrita
  (`DECISIONES.md` §5), pero conviene decidirlo antes de que crezca.
- **Qué hay que hacer**: decidir si se conservan (histórico de declaraciones) o se poda a N
  días, y si el manifiesto lleva solo las del día + un resumen. Es decisión de producto.
- **Cómo se sabe que está bien**: el tamaño del manifiesto queda acotado y la declaración del
  día sigue estando.

### 15. Que falte una declaración se note — **pendiente, S**

- **Por qué**: la API y el manifiesto leen `data/cobertura/`; si una cadena no declara (por
  ejemplo, porque la pasada se saltó el paso), la cadena sale sin `cobertura` y **nadie
  avisa**: volvería a parecer «solo Lidl».
- **Qué hay que hacer**: en el cierre del día, comprobar que hay declaración para las 6
  cadenas y avisar si falta; y/o que `scripts/auditar_cobertura_diaria.py --exigir-declaracion`
  lo compruebe.
- **Cómo se sabe que está bien**: una prueba con el directorio sin el fichero de una cadena
  falla con el nombre de la cadena.

---

### 16. Métricas de Cesta para el panel de David — **hecho (04/11)**

- **Por qué**: David necesita más datos de Cesta en su panel, y la métrica que dice si el
  producto sirve no es «cuántos productos hay» sino **cuántos se pueden comparar hoy**.
- **Qué se ha hecho**: `projects/cesta/metricas.py` escribe `metricas-cesta.json` en la raíz
  (por cadena `hoy` y `dias`, `ultima_ejecucion` en hora local, `comparables_con_precio`,
  `en_varias_cadenas` y `dias_historial`), y `run.py` lo reescribe al cerrar cada pasada.
  Hoy: **8.829 de 39.115** comparables con precio están en 2+ cadenas (22,6 %), 59 días de
  historial. Definiciones en `DECISIONES.md` §6 (incluye por qué no se cuentan las 760 filas
  del día sin importe).
- **Cómo se sabe que está bien**: `pytest tests/test_metricas_panel.py` (4 pruebas: misma
  fecha para las dos cifras, sin datos no inventa, JSON atómico y enganche en `run.py`).

## Lo que está verde de verdad (medido el 04/11/2026, 17:39)

| Qué | Cómo se ha medido |
|---|---|
| Catálogo 52.982 · 8.875 grupos · 2.551.307 filas de histórico | `data/gold/*` + `docs/CIFRAS.md` reescrito por la pasada |
| Comparación real: **8.829 el mismo día 4/11** (22,6 % de 39.115 comparables con importe; 8.851/39.837 contando filas sin importe). La foto de las 14:30 de `AGENTE.md` decía 8.864, que es otra medida y otro momento | consulta a `gold/grupos.parquet` + `precio_diario.parquet` |
| Cobertura diaria de 5 cadenas, con novedad medida: 128 días-cadena con captura en 30 días, 124 con novedad ≠ 0, 128/128 escritos el mismo día | `scripts/auditar_cobertura_diaria.py` + `docs/COBERTURA-DIARIA-2026-11-04.md` |
| Las 5 cadenas declaran su cobertura medida; el manifiesto pasa de 21 a 26 entradas declaradas | `data/cobertura/*.json` + `core/manifiesto.py` |
| La API sirve cobertura para 6 cadenas | `GET /api/estado` → bloque `cobertura` en las 6 |
| Publicación coherente | `GET /api/estado` → `vigencia_precio.coherente: true` |
| Stack arriba (db/api/web sanos) | `docker ps` |
| Métricas del panel publicadas y reescritas por la pasada | `metricas-cesta.json` + `pytest tests/test_metricas_panel.py` |
| Guarda de cobertura con pruebas | `pytest tests/test_cobertura.py tests/test_cobertura_honesta_20261104.py tests/test_cobertura_declarada_20261104.py` |
| App de consumo lista para aprobar: sistema de diseño + 2 artboards móviles con datos reales | `check`=0 en `designs/cesta-app-design-system` y `designs/cesta-app`; 92 parejas AA sin fallos; investigación y viabilidad en `INVESTIGACION-APP.md` y `docs/DATOS-APP-2026-11-04.md` |

**Lo que solo lo dice un documento**: que la CI pasa; que M08–M22 están verificados con
datos (hay página, cliente y ruta, pero la aceptación con datos necesita la tarea 4); y el
**futuro** de la cobertura diaria —el dato de hoy es real y el reloj que lo produce ya está
re-registrado y probado (tarea 12), con la próxima pasada automática el 5/11 a las 06:00—.

### 17. Los avisos de cobertura no llegan a la pantalla — **pendiente, XS**

- **Por qué**: `Ajustes` pinta «catálogo diario · filas capturadas · % de su referencia ·
  precios cambiados», pero **no** el veredicto (`corta`) ni los huecos (`11 de 30`). La regla de
  `logica/cobertura.ts` es no pintar códigos, y es correcta; el efecto es que Alcampo se lee
  «83,6 % de su referencia del 17 oct» sin decir que su captura es corta.
- **Qué hay que hacer**: añadir el veredicto y los huecos en palabras (p. ej. «captura corta»,
  «faltan 11 de 30 días»), sin códigos crudos y sin inventar cifras si faltan campos.
- **Cómo se sabe que está bien**: prueba de `textoCobertura` con veredicto y sin él, y la
  tarjeta de Ajustes mostrando «corta» para Alcampo.

### 18. App de consumo: aprobar sistema de diseño y artboards — **pendiente de aprobación (David)**

- **Por qué**: `ALCANCE-APP.md` pide que el aspecto se apruebe antes de la primera pantalla.
- **Qué hay**: sistema «Cesta App» (tokens claro/oscuro, Fraunces/IBM Plex reales, escalas de
  espaciado/radio/movimiento, 92 parejas de contraste AA medidas) y canvas «Cesta App —
  artboards» con Portada y Producto móviles 390×844 sobre datos reales. Investigación en
  `INVESTIGACION-APP.md` y viabilidad medida en `docs/DATOS-APP-2026-11-04.md`.
  `check`=0 en los dos artefactos y `ds-sync` al día.
- **Qué falta**: que David abra las dos páginas y diga sí o qué cambia (paleta, densidad,
  navegación de tres destinos frente a los seis actuales). Sin ese sí no se escribe la pantalla.
- **Cómo se sabe que está bien**: aprobación explícita en el chat con los cambios pedidos.

### 19. App: portada y ficha de producto sobre los tokens — **pendiente, depende de 18**

- **Por qué**: es el primer corte de valor («que se vea bien»). Los artboards ya fijan la
  dirección; ahora va código real con datos reales y sus cuatro estados.
- **Qué hay que hacer**: implementar en `plataforma/web/app` la portada y la ficha de producto
  con los tokens aprobados, comparación por cadena/€/kg, historial con la ventana real de 59
  días (nunca «90 días») y las cifras honestas de cobertura (8.066 comparables de verdad).
- **Cómo se sabe que está bien**: pruebas de flujo (portada → producto → comparación), sin scroll
  horizontal a 390 px, contraste del sistema y estados vacío/cargando/error.

### 20. Datos que faltan para las funciones limitadas — **pendiente, decisión de producto**

- **Por qué**: no hay **aditivos** (ninguna columna; solo E-xxx en texto en el 31 % de las
  listas) ni **recetario real** (242 recetas de prueba, 0/242 con coste, 4/473 ingredientes con
  producto inexistente). Sin eso, «Yuka» y «recetas con coste real» no se pueden hacer sin
  inventar.
- **Qué falta decidir**: si se ingesta un recetario con licencia y se mapea ingrediente→producto,
  y si se busca una fuente de aditivos (nueva ingesta, no derivada). Mientras, la app enseña
  Nutri-Score/sellos/certificados y deja recetas-coste fuera.
- **Cómo se sabe que está bien**: decisión escrita y, si se ingesta, cobertura medida con
  `data_profile`/`data_verify` antes de publicar la función.
