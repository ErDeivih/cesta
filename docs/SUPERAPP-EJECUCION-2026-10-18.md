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

### M00 / 18/10/2026 / en curso (guardas y manifiesto hechos; siembra pendiente)

**Capacidad y alcance.** Comando de banco de ensayo propio con manifiesto:
`uv run python -m plataforma.ensayo {guardas|prepara|estado|limpia}` en
`plataforma/ensayo.py`.

**Caso reproducido antes.** No habia ningun comando que rechazara un DSN protegido
antes de escribir: los ensayos se hacian a mano contra 5434, que el encargo prohibe
como destino de restauracion.

**Cambio y contrato.** Tres guardas que se comprueban **antes** de cualquier DDL:
puerto 5432/5433/5434 prohibido; el nombre de la base tiene que empezar por
`cesta_ensayo_`; solo loopback. Y el contenedor tiene que empezar por `cesta-ensayo-`
y no existir ya. El manifiesto anota nombre, **id** de contenedor, DSN, directorio y
SQLite; la limpieza **solo** borra lo anotado, comprueba que el id sigue siendo el
mismo nombre, y no mata procesos ajenos ni borra directorios sin el marcador
`.cesta-ensayo`.

**Comandos ejecutados + exit codes.**
- `uv run python -m plataforma.ensayo guardas` -> **exit 0**, 8 casos, 0 con veredicto
  equivocado: casa 5432, facylf 5433, ensayos 5434, base llamada `cesta`, fuera de
  loopback, no-PostgreSQL, puerto no numerico -> **rechazados**; un ensayo valido ->
  aceptado.
- `data/ensayo` **no existe** despues de correr las guardas: **no se escribio nada**.
- `uv run ruff check plataforma/ensayo.py` -> limpio.

**Que NO se ha probado.** La siembra (usuarios A/B, listas con y sin casa, 5 recetas,
despensa, ofertas, avisos) **no esta hecha**: faltan los contratos de recetas,
despensa y ofertas de ensayo. Por tanto el criterio «dos ejecuciones reproducen el
mismo escenario» **no esta cumplido**. `prepara` y `limpia` no se han ejecutado
todavia contra Docker.

**Siguiente comando concreto.**
`uv run python -m plataforma.ensayo prepara propio` y despues
`uv run python -m plataforma.ensayo limpia propio`, para probar las otras dos
aceptaciones de M00 (limpieza no toca recursos ajenos; se conoce cada proceso creado).

