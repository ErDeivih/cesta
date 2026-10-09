# Retorno de Docker: qué se ejecuta, en qué orden, y qué significa si falla

Fecha: 11 de octubre de 2026. Escrito **con el motor caído**, para que el primer día que arranque no se
gaste ni una ronda decidiendo por dónde empezar.

## La premisa, medida y no supuesta

**La suite está entera en verde con el motor caído: `1.540 passed`, y `pytest -rs` no lista ni un solo
`SKIPPED`.** Así que no hay una capa de pruebas escondida detrás de Docker: las que nombran PostgreSQL
**corren hoy y usan dobles**, que es como el encargo dice que se cerró el trabajo de coste.

De ahí la división que ordena todo lo de abajo:

| | qué demuestra | estado |
|---|---|---|
| **los dobles** | **la lógica**: agrupación, reparto, elección efectiva, identidad por línea, la invariante del coste | **probado hoy, 1.540 pruebas** |
| **PostgreSQL de verdad** | **la fontanería**: `importe_cent` NULL en las filas viejas, una transacción que no deja nada a medias, una restauración que cuadra al céntimo, los tipos y las restricciones | **sin verificar** |

**Lo segundo no se puede sustituir por lo primero**, y por eso estas comprobaciones existen.

## Antes de empezar

```
docker ps                              # ¿responde?
Test-Path \\.\pipe\dockerDesktopLinuxEngine
Test-NetConnection 127.0.0.1 -Port 5434 -WarningAction SilentlyContinue
```

Si los tres fallan, **no hay retorno**: parar aquí y no gastar la ronda. **Y no volver a comprobarlo más de
una vez por ronda**: en esta sesión se comprobó tres veces en una sola ronda y no cambió nada.

Y una regla que no se salta: **lo destructivo, contra el entorno desechable y con datos controlados**, nunca
contra el catálogo real. El catálogo real sólo para la comprobación **adicional** del 3×2.

## Los siete pasos, en orden

### 1. La suite sigue verde, y ahora con motor

```
uv run pytest -q
```

**Qué se espera**: `1.540 passed`. **Qué significa si falla**: una prueba que hoy pasa con dobles **depende
de verdad de PostgreSQL** y no lo sabíamos. Es el hallazgo más importante posible, y va antes que todo lo
demás.

### 2. La migración 013, que está escrita y nunca se ha ejecutado

`plataforma/sql/013_el_importe_final_de_cada_linea.sql` añade `importe_cent` por línea de compra.

**Qué comprobar**: que la columna existe, que **las filas antiguas quedan en NULL** (desconocido, **no
reconstruido**: reconstruirlo sería inventar importes que nadie guardó) y que las nuevas lo escriben.

**Qué significa si falla**: la migración se escribió contra una idea del esquema, no contra el esquema. Hay
que verlo **antes** de aplicar nada a datos que importen.

### 3. Las cuatro comprobaciones ordenadas del encargo

1. **Restauración**: guardar una compra, copiar, restaurar, y exigir que **los importes sean los mismos
   antes y después**; además producto efectivo, cantidad y tienda. **Y que las líneas con importe conocido
   sumen exactamente el total.**
2. **Datos desconocidos**: una línea **sin precio** mantiene `importe_cent` **NULL**; una línea **realmente
   gratuita** guarda **0**; y **si hay importes desconocidos, el total se identifica como PARCIAL**.
3. **Transacción**: **provocar un fallo al guardar una línea** y comprobar que **no queda ni compra ni
   líneas a medias**.
4. **3×2 con datos controlados** en el entorno desechable: una línea de tres y dos líneas de una y dos, y
   **las dos persisten exactamente 200 céntimos en total**. El catálogo real, sólo para la comprobación
   adicional.

### 4. El escenario determinista de las cuatro superficies

Ya escrito, con sus casos de **confirmación**, **revocación** y **desaparición de la alternativa**.

### 5. Los recorridos de punta a punta — el criterio de cierre del encargo

```
uv run python plataforma/prueba_navegador.py       # 1.856 líneas: navegador
uv run python plataforma/prueba_e2e.py             # 650 líneas, PostgreSQL en 5434
uv run python plataforma/prueba_copia.py           # 124 líneas, restauración en 5435
```

Las tres aplicaciones: **Compra**, **Recetas** y **Calorías**. Es lo que el encargo llama *«se puede
recorrer de punta a punta»*, y **ninguna lectura de código lo sustituye**.

### 6. El estado de la publicación

```
GET /api/estado
```

Se puede y se debe comprobar **en proceso, con `TestClient`, sin servidor**: ya se hizo el 11 de octubre y
devolvió `version_catalogo: 20261009-122845` y `vigencia_precio: {comprobable: True, coherente: True}`.

**Lo que hay que vigilar aquí**: que la coherencia siga siendo cierta, y **que la versión publicada avance**
cuando el pipeline corra. Si no avanza, la publicación no se está cerrando.

### 7. Lo que el encargo deja a decisión de producto, no técnica

**¿El lector de datos debe leer la versión publicada en lugar de los ficheros sueltos?**

Es correcto por la lógica de S01 —*una versión entera o ninguna*— y **cambia lo que ve el usuario**: el
11 de octubre los ficheros sueltos eran **más nuevos** (12:35) que la publicación (12:28), así que
adoptarlo significaría enseñar la última publicación **completa** en vez del último fichero escrito.

**No se decide solo.** Va con su medición delante y con la respuesta de quien manda en el producto.

## Y lo que **no** hay que hacer al volver

- **No** volver a comprobar Docker más de una vez por ronda.
- **No** dar por cerrada ninguna condición con las pruebas de dobles **más** una lectura de código: el
  encargo pide **evidencia de ejecución**.
- **No** ejecutar `prueba_produccion.py` (557 líneas) sin leerlo antes: el encargo avisa de que las pruebas
  de producción y navegador **pueden crear cuentas o modificar datos**, y hay que usar **entorno de ensayo
  separado**.
- **No** commitear `core/datos/secciones.yml`: lo modifica la ingesta y hay que preservar sus cambios.
