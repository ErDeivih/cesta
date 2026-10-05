# El muro: todo lo que hay que hacer, en orden

Este es el tablero de trabajo del encargo **Cesta familiar**. Se actualiza **en cada entrega**: un
paquete no se marca hecho por escribir la propuesta, sino cuando pasa sus pruebas de aceptación y
el documento de resultado va en el mismo commit que el código.

- **Contrato completo:** `docs/CESTA-PLAN-DE-IMPLEMENTACION.md` (decisiones cerradas y flujo).
- **Cómo se hace:** `docs/CESTA-DATOS-Y-COMPARACION.md` (dato) y
  `docs/CESTA-APLICACION-Y-GRAFICAS.md` (pantallas).
- **Detalle y aceptación de cada paquete:** `docs/CESTA-TAREAS-Y-ACEPTACION.md` (T01–T10).
- **De dónde sale todo esto:** `docs/AUDITORIA-CESTA-2026-10-05.md`.
- **Reglas de la casa:** `docs/TRASPASO-CHATGPT.md` §6 (todo número medido y con fecha, documentos
  en el mismo commit que el código, un instrumento que no puede medir tiene que decirlo).

Leyenda: `PENDIENTE` · `EN CURSO` · `HECHO` (código + pruebas + resultado medido) · `BLOQUEADO`.

---

## Lo que ya está comprobado y de dónde partimos

Medido el 5 de octubre de 2026 con `uv run python -m projects.cesta.auditar_identidad` (instrumento
de solo lectura, con prueba propia en `tests/test_auditar_identidad.py`):

| hecho | número |
|---|---:|
| productos en el catalogo | 53.139 |
| grupos multicadena | 8.812 |
| grupos multicadena con **varios EAN** | 2.276 |
| grupos multicadena con **varios formatos fiables** | 593 |
| productos de Alcampo en ramas excluidas (bazar, juguetes...) | 245 |
| columnas que faltan en gold para trazabilidad | `disponible`, `capturado_en`, `tienda_id` |

**Lo que esto significa, dicho claro: «grupo comparable» hoy no quiere decir «producto idéntico».**
La app puede presentar como ahorro el cambio de una marca por otra, y el plan existe para que deje
de hacerlo. Los fallos concretos que se vieron: Asturiana entera 6×1 l comparada con Celta entera
6×1 l; al añadir desde una ficha se guarda el grupo de alternativas y no el artículo exacto; el
optimizador admite precios de Alcampo del 1 de octubre estando configurado un límite de tres días;
el gasto archivado es estimado y se presenta como compra; las ventanas «30/90 días» cuentan
observaciones y no días; una caída de «Hogar y Decoración» puede bloquear la aceptación de
alimentarios nuevos.

---

## El muro

### Entrega E1 — Catálogo familiar

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T01** | Política familiar y presupuesto de extracción (`core/alcance.py`, `core/datos/alcance.yml`, los cinco colectores, `reprocesar.py`, `cobertura.py`, `run.py`) | — | el bazar sale del catálogo y del recorrido; se piden menos cosas y con motivo; informe por fuente de incluidos/excluidos/pendientes | **EN CURSO** — política v1, clasificador, 19 pruebas de aceptación y ejecución seca funcionando. Medido sobre los 53.139 productos de hoy: **47.570 entran, 3.162 salen (6,0 %), 2.407 a revisar** (Alcampo 7,2 % fuera · Carrefour 6,9 % · Aldi 2,8 % · Mercadona 2,3 % · DIA 2,0 %). **Una rama excluida ya no veta una captura incluida** (`core/cobertura.py` filtra lo excluido antes de comparar ramas, con `revisar` dentro): es el arreglo que devuelve a Alcampo su captura. Falta aplicarlo dentro de los colectores --para no pedir bazar-- y el informe de peticiones |

### Entrega E2 — Identidad y ofertas

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T02** | Oferta trazable y publicación consistente (`schemas.py`, `storage.py`, `pipeline.py`, `emparejar.py`, `catalogo.py`, `cifras.py`, `cobertura_diaria.py`) | T01 | cada precio de pantalla se puede rastrear hasta su observación; captura real, zona, tienda, disponibilidad, retirada, versión; publicación por manifiesto atómico | **PENDIENTE** |
| **T03** | Identidad y banco de referencia por familias (`core/identidad.py`, `atributos.py`, `matching.py`, `equivalencias.py`, `emparejar.py` + banco de casos) | T01–T02 | «artículo exacto» / «familia» / «alternativa» son cosas distintas; banco de 390 pares (30 por familia); **cero falsos idénticos en los casos obligatorios** | **PENDIENTE** |

### Entrega E3 — Lista fiel a la elección

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T04** | Migración de listas, favoritos y alertas (migración nueva después de la 010, `almacen.py`, `main.py`, `alertas.py`, `vigilante.py`, `catalogo.py`) | T03 | añadir desde una ficha guarda **ese** artículo; las alternativas se piden; ninguna alerta dispara por una bajada de otra marca; listas, favoritos y compras se conservan | **PENDIENTE** |

### Entrega E4 — Presupuesto correcto

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T05** | Selector único de ofertas elegibles (`cesta.py`, `catalogo.py`, `movimientos.py`, alertas) | T02–T04 | una oferta del día 1 no decide una cesta del día 5; fuera lo retirado, sin stock o sin zona; cada descarte explicado | **PENDIENTE** |
| **T06** | Cantidades, promociones y optimización (`core/promos.py`, `api/cesta.py`, preferencias) | T05 | los 11 casos de la tabla del contrato dan el resultado exacto; paquetes y unidades comparados por desembolso real; nada de dobles descuentos | **PENDIENTE** |

### Entrega E5 — Compra y gastos

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T07** | Compra confirmada e histórico familiar (migración nueva, `almacen.cierra_compra`, `main.cerrar_compra`, `cesta.coste_por_linea`, interfaz de cierre) | T04 y T06 | el importe confirmado y el estimado son series distintas; lo antiguo queda etiquetado como estimado; cierre idempotente | **PENDIENTE** |

### Entrega E6 — Experiencia final

| | paquete | depende de | qué se ve cuando está | estado |
|---|---|---|---|---|
| **T08** | Interfaz cotidiana (`App.tsx`, Inicio, Buscar, Producto, Grupo, Favoritos, Cesta, `BotonAnadirACesta`...) | T04–T07 | cuatro rutas y los recorridos del contrato; etiquetas que no prometen identidad sin prueba; capturas en móvil y escritorio de todos los estados; probado por una persona ajena | **PENDIENTE** |
| **T09** | Gráficas correctas (`derive.py`, `api/analisis.py`, movimientos, consultas de gasto, componentes) | T02, T03, T07 | ventanas de calendario de verdad, series por identidad, episodios; gasto confirmado ≠ estimado ≠ contrafactual; cada céntimo rastreable | **PENDIENTE** |
| **T10** | Verificación diaria y entrega operativa (`run.py`, `ejecutar.bat`, verificadores, documentación) | todas | métricas por fuente, inyección de fallos (bloqueo, categoría vacía, corte de publicación), y una fuente sin dato aceptado **no** se llama correcta | **PENDIENTE** |

---

## Reglas de ejecución (del contrato, y no se saltan)

1. Comprobar Git y procesos activos antes de tocar nada; preservar los cambios del dueño
   (`core/datos/secciones.yml` y `docs/CIFRAS.md` están modificados a propósito y no entran en
   commits de tareas).
2. Línea base de pruebas primero. Desarrollar contra **copia** de datos y base de pruebas: no se
   lanza la pasada de horas para probar una regla de identidad.
3. Una entrega es código + migración (si toca) + pruebas + resultado **medido**. Nada de marcar un
   paquete por escribir la propuesta.
4. No publicar gold con otro esquema sin probar todos sus consumidores y el adaptador antiguo.
5. Probar rollback y compatibilidad de listas y compras antes de cualquier corte de versión.
6. Cerrar cada paquete con la plantilla de `CESTA-TAREAS-Y-ACEPTACION.md` §«Plantilla obligatoria»:
   estado, archivos, qué cambia para la persona, pruebas y resultado, métricas antes/después **con
   fecha**, compatibilidad y recuperación, y pendientes con condición concreta.

---

## Preguntas al dueño (contestadas antes de empezar a fondo)

1. **Dónde está la frontera del «consumible».** El contrato incluye alimentación, frescos, bebidas,
   limpieza, higiene, bebé, mascotas y consumibles domésticos, y excluye el bazar duradero. Los
   casos que quiero que confirmes, porque deciden qué se deja de pedir el primer día: **bombillas,
   pilas, bolsas de basura, papel de cocina, papel higiénico, servilletas, insecticidas, ambientadores,
   cubos y bayetas, menaje barato (vasos, fiambreras), juguetes de mascota, arena de gato, comida de
   mascota**.
2. **Qué va primero dentro de E2**: infraestructura (T02: trazabilidad y publicación por versiones)
   o identidad (T03: que la comparación sea del mismo producto). El plan los pone en ese orden; si
   prefieres ver antes el arreglo de las comparaciones, se cambia el orden y T02 pasa después.
3. **Cuánto puedo cambiar el aspecto.** T08 pide una navegación y unos recorridos nuevos. ¿Mantengo
   el lenguaje visual actual y sólo arreglo flujos y etiquetas, o puedo rediseñar pantallas? Y si
   rediseño, ¿sigo usando Stitch para las pantallas nuevas (la clave nunca entra en el repositorio)?

---

## Bitácora

| fecha | qué se hizo |
|---|---|
| 2026-10-05 | **T01, primera mitad**: politica de alcance, clasificador y ejecucion seca. Tres rondas de medicion (11,8 % -> 9,0 % -> **6,0 % fuera**), con un fallo del emparejador encontrado por el camino (los terminos con guion no casaban). Y la regla "una rama excluida no veta una captura incluida", que es lo que desbloquea Alcampo |
| 2026-10-05 | muro creado; auditoría de ChatGPT verificada en esta máquina (los 6 números y el instrumento, con su prueba) |
