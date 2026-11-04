# Cesta — backlog vivo

Escrito el **4 de noviembre de 2026**, a partir de lo **medido** en esta sesión, no de lo
que dice un documento. El backlog histórico y las fichas largas siguen en
`docs/BACKLOG.md` (17/09/2026) y en `docs/SUPERAPP-EJECUCION-2026-10-18.md`: son
contexto y evidencia, no estado.

Regla del protocolo: **nunca menos de 5 tareas listas**, y una tarea bloqueada no para la
sesión — se marca y se sigue con la siguiente.

---

## El estado, en una línea

El catálogo son **52.342 productos** y la comparación **existe**: **8.864 grupos** tienen
precio en **2 o más cadenas** (22,9 % de los 38.682 comparables). Lo que se cae es la
**cobertura diaria de una cadena**, y la ficha del agente lo contaba al revés («solo Lidl,
21 días»).

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

### 5. Que la cobertura medida llegue a la API y a la pantalla — **pendiente (M18), barato**

- **Por qué**: ya viaja en el manifiesto (`cobertura_medida`), pero `/api/estado` solo dice
  `al_dia: true/false` por cadena. La persona que mira la app no puede ver que Alcampo trajo
  23.416 de 23.416 productos y que Carrefour dejó 3 días de 30.
- **Qué hay que hacer**: exponer `cobertura_medida` en `/api/estado` y enseñarlo en
  **Ajustes → Fuentes** (frescura por cadena), sin mezclarlo con diagnóstico técnico.
- **Cómo se sabe que está bien**: prueba de contrato de la respuesta y del componente; la
  pantalla dice la fecha de la referencia, no solo «al día».

### 6. Corregir la ficha del agente, que daba el estado al revés — **pendiente, 10 minutos**

- **Por qué**: `AGENTE.md` dice «cobertura diaria: **solo Lidl**, 21 días». Medido: Mercadona
  32 días, Aldi 32, Carrefour 31, DIA 29, Alcampo 20 (hoy 21), Lidl 21. El error venía de
  leer `cobertura_declarada`, donde solo escribe Lidl.
- **Qué hay que hacer**: sustituir la tabla por las cifras medidas y enlazar este backlog.
- **Cómo se sabe que está bien**: ninguna cifra de `AGENTE.md` sin fecha de medición ni
  fuente.

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

---

## Lo que está verde de verdad (medido el 04/11/2026, 14:30)

| Qué | Cómo se ha medido |
|---|---|
| Catálogo 52.342 · 8.897 grupos · 2.527.902 filas de histórico, 59 días | `data/gold/*` + `docs/CIFRAS.md` reescrito por la pasada |
| Comparación real: 8.864 grupos en 2+ cadenas | consulta a `gold/grupos.parquet` |
| Publicación coherente | `GET /api/estado` → `vigencia_precio.coherente: true` |
| Stack arriba (db/api/web sanos) | `docker ps` |
| Guarda de cobertura con pruebas | `pytest tests/test_cobertura.py tests/test_cobertura_honesta_20261104.py` |

**Lo que solo lo dice un documento**: que la CI pasa; que M08–M22 están verificados con
datos (hay página, cliente y ruta, pero la aceptación con datos necesita la tarea 4); y
—hasta hoy— la cobertura de las cinco cadenas, que no viajaba con lo publicado.
