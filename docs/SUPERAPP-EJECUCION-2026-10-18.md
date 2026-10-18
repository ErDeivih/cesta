# Ejecución de la especificación maestra

Contrato: [especificación maestra](SUPERAPP-ESPECIFICACION-MAESTRA-2026-10-18.md).
Preparado el 18/10/2026 por GPT; revisión inspeccionada `5204e2b`.
Esto es una cola de trabajo, no una certificación de carencias ni una activación
del bucle de DeepSeek. No copiar aquí las bitácoras antiguas.

## Punto de continuación

Primero M00: comprobar entorno y guardas. Después cerrar M01 completo, incluida
la tabla de cadenas que conserva la comparación entre artículos distintos.
M02 autoriza dependencias gratuitas de desarrollo: ESLint/hooks y tests de componentes.
Luego M03/M04 y la semana completa. No esperar otra respuesta de David para R1–R4.

Foto de datos: API `20261018-131107`, cinco cadenas del 18 y Carrefour del 17.
`runs.csv`: Carrefour del 18 rechazado (0 filas, 1 error); no equivale a reparación.
No lanzar otra ingesta sin verificar tarea/lock. Los cierres B00–B16 anteriores
son antecedentes y se reutilizan, no se copian como evidencias nuevas.

## Cola y criterio de seguimiento

Todos comienzan **por auditar**, no «sin implementar». Si ya están resueltos,
aportar aceptación reproducible y pasar al siguiente. Máximo dos en curso.

| ID | Entrega | Estado inicial | Dependencia principal |
| --- | --- | --- | --- |
| M00 | Sandbox y guardas | Por auditar | Ninguna |
| M01 | Comparación en todas las superficies | Defecto de tabla conocido | M00 para ensayo |
| M02 | Hooks, componentes y recuperación | Dependencias no declaradas | M00 |
| M03 | Compra al diario y selector | Pendiente reconocido | M00 |
| M04 | API, caché y publicación | Por auditar | M01–M03 |
| M05 | Compra cotidiana completa | Por auditar | R0 |
| M06 | Coste/promociones/optimización | Por auditar | M01/M04 |
| M07 | Identidad automática evaluada | Por auditar | M01/M04 |
| M08 | Favoritos/avisos/ahorro | Por auditar | M05/M06 |
| M09 | Recetario y editor | Por auditar | R0 |
| M10 | Plan semanal y propuesta | Por auditar | M09 |
| M11 | Necesidades/envases/despensa | Por auditar | M06/M09/M10 |
| M12 | Cocina y aprovechamiento | Por auditar | M09/M11 |
| M13 | Diario personal completo | Por auditar | M03/M09 |
| M14 | Gráficas verificables | Por auditar | M06/M11/M13 |
| M15 | PWA/offline/sincronización | Por auditar | R0/M05 |
| M16 | Ingestas y ampliación Lidl | Carrefour falla el 18; Lidl parcial | M00; independiente |
| M17 | Fichas ricas/nutrición/historial | Por auditar | M16 para red; offline independiente |
| M18 | Estado/observabilidad/operación | Por auditar | M16/M17 |
| M19 | Seguridad/copia/privacidad | Por auditar | M00; revisar incrementalmente |
| M20 | Rendimiento y calidad percibida | Por auditar | Recorridos con datos |
| M21 | Aprender y documentación | Índice web incompleto | Independiente; cierre tras cambios |
| M22 | Release candidate y dictamen | No verificado globalmente | Criterios finales |

Estados permitidos: por auditar / en curso / implementado sin verificar /
verificado con alcance / limitado por fuente / bloqueado externo. Un bloqueo
no convierte lo implementado en verificado. No inventar porcentajes de avance.

## Formato para cada entrega cerrada

Copiar solo al cerrar un paquete funcional, no por cada edición:

```
ID / revisión / fecha:
Capacidad y alcance:
Caso reproducido antes (si era defecto):
Cambio y contrato compartido:
Comandos ejecutados + exit codes + resultados:
Prueba de componente/HTTP/navegador y datos usados:
Versión realmente servida, si se comprobó:
Evidencia visual revisada (qué demuestra):
Limitaciones y qué NO se ha probado:
Siguiente ID + comando concreto:
```

Resultados heredados, recuentos de tests y capturas sin revisar no se presentan
como ejecución propia. No editar `docs/CIFRAS.md` manualmente para aparentar una
cifra vigente; si se genera, registrar proceso y preservar modificaciones ajenas.

## Bloqueos externos

Ninguno confirmado por esta preparación. Al encontrar uno: capacidad, evidencia,
decisión mínima requerida, trabajo independiente siguiente. No preguntar por
colores, instalación de dependencias de test o cambios normales de implementación.

---

## Estado por entrega

### M00 / 18/10/2026 / en curso (sandbox verificado; siembra pendiente)

**Capacidad y alcance.** Banco de ensayo propio en `plataforma/ensayo.py`:
`uv run python -m plataforma.ensayo {guardas|prepara|estado|limpia}`.

**Caso reproducido antes.** No habia comando que rechazara un DSN protegido antes de
escribir; los ensayos se hacian a mano sobre 5434, que el encargo prohibe.

**Cambio y contrato.** Guardas antes de cualquier DDL: puertos 5432/5433/5434
prohibidos; la base empieza por `cesta_ensayo_`; solo loopback; contenedor con
prefijo `cesta-ensayo-` y no existente. Manifiesto con nombre, **id completo** de
contenedor, DSN, directorio y SQLite. `limpia` solo borra lo anotado, comprueba que el
id sigue siendo el mismo nombre, no mata procesos y no borra directorios sin el
marcador `.cesta-ensayo`.

**Comandos ejecutados + exit codes + resultados.**
- `... ensayo guardas` -> **exit 0**. 8 casos, 0 con veredicto equivocado. Rechazados:
  casa 5432, facylf 5433, ensayos 5434, base llamada `cesta`, fuera de loopback,
  no-PostgreSQL, puerto no numerico. Aceptado: un ensayo valido. `data/ensayo` **no
  se creo**: no se escribio nada.
- `... ensayo prepara propio` -> **exit 0**. Contenedor `cesta-ensayo-propio`
  (id `73b35193...`), DSN en 55432, manifiesto escrito con los seis campos.
  `estado` lo vio `running`.
- `... ensayo limpia propio` -> **exit 0**. Borrados contenedor, directorio y
  manifiesto.
- **Recursos ajenos, contados antes y despues: 25 y 25; ninguno falta.** Incluidos
  `cesta-db-1` (5432) y `facylf-postgres` (5433). El contenedor propio ya no esta.
- `uv run ruff check plataforma/ensayo.py` -> limpio.

**Aceptacion de M00, criterio por criterio.** rechaza DSN protegido sin escribir:
**cumplido** (8/8 y nada creado) · limpieza no toca recursos ajenos: **cumplido**
(25/25) · se conoce cada proceso creado: **cumplido para el contenedor** (id completo
en el manifiesto) · **dos ejecuciones reproducen el mismo escenario: NO cumplido**.

**Que NO se ha probado.** La siembra -- usuarios A/B, listas con y sin casa, 5
recetas, despensa, ofertas y avisos -- **no esta hecha**. Faltan los contratos de
recetas, despensa y ofertas de ensayo; la API de usuarios y listas si esta localizada
(`crea_usuario`, `crea_lista`, `crea_alerta`, `guarda_preferencia`). No se inventan
esos contratos para aparentar cierre.

**Siguiente ID + comando concreto.** M00 sigue abierto: contrato de recetas/despensa
de ensayo y `... ensayo siembra propio`, dos veces, comparando el resultado.
Despues M01, que ya tiene su defecto localizado: la tabla de `Producto.tsx`.

