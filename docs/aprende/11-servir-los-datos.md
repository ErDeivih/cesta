---
seccion: Ingeniería de datos
resumen: API, PostgreSQL, migraciones, Caddy y la puerta del despliegue.
---

# 11 · Servir los datos: API, PostgreSQL, migraciones y despliegue

Un análisis que se queda en un notebook no sirve a nadie. Este capítulo es el de la última
milla: cómo se sirve lo que se ha calculado, cómo se guarda lo que escribe la gente, y cómo se
comprueba que **lo que se sirve** es lo que se cree.

## 1. Las dos mitades: leer y escribir

La decisión estructural del proyecto, y la que más simplifica todo lo demás:

    LEER     DuckDB sobre Parquet en `gold`. Un catalogo que cambia una vez al dia.
    ESCRIBIR PostgreSQL. Cuentas, listas de la compra, avisos, favoritos, invitaciones.

Son dos cosas con requisitos opuestos. Lo que se lee es grande, columnar, de solo lectura y se
recalcula entero cada mañana; lo que se escribe es pequeño, relacional, transaccional y no se
puede perder. Mezclarlas (meter el catálogo en PostgreSQL, o los usuarios en un fichero) sale
caro en las dos direcciones: el catálogo no necesita transacciones y las listas no necesitan
columnas.

Y hay una tercera pieza que casi nadie pone al principio y aquí está desde el día uno: **gold es
de solo lectura para la API** (montado `:ro` en el contenedor). Si el scraper falla un día, la
API sigue sirviendo lo de ayer y **lo dice** (la fecha del dato va en la cabecera).

## 2. La superficie: 38 endpoints

Medido hoy sobre el esquema que publica la propia aplicación:

    endpoints            38
    sin sesion           23    buscar, grupos, fichas, indices, panel, escaner por EAN
    con sesion           15    listas, lineas, compartir, invitar, avisos, favoritos, yo

Que dos tercios sean públicos no es un descuido: **mirar precios no requiere cuenta**. La sesión
hace falta para lo que es de alguien (su lista) o para lo que cuesta dinero en la base (escribir).
Es la misma decisión de producto que el «entra para ver tu lista» de la interfaz.

## 3. Lo que la API dice cuando no puede contestar

Esta es la parte que distingue una API honesta, y los tres casos están medidos:

**Sin sesión, no inventa un «tuyo».** `GET /api/bajadas?solo_mios=true` sin cookie responde el
catálogo **con `solo_mios: false`**: el campo dice lo que el servidor ha hecho, no lo que le han
pedido. Poniendo lo que pidió el cliente, la interfaz enseñaba sesenta bajadas del catálogo bajo
el título «Lo tuyo que ha bajado». **Lo encontró la verificación de punta a punta** contra un
PostgreSQL de verdad, porque la prueba unitaria miraba los grupos que llegaban al SQL y no este
campo.

**Una ruta que no existe no es un fallo.** `GET /api/panel/matching` puede contestar 404 si la
imagen que corre es anterior: la pantalla lo trata como «esa ruta no está en el servidor que me
atiende», no como un error rojo. Un 404 no se reintenta (repetirlo no lo va a crear).

**Y lo que no se sabe, se dice.** El «precio de siempre» puede ser `null` (pocas observaciones), y
entonces la frase no se inventa: hay pantallas que **callan** en vez de decir algo falso
(capítulos 03 y 05). En la API eso son campos `null` explícitos, nunca ceros de relleno.

## 4. Los datos de las personas: cuentas, sesiones e invitaciones

    contrasenas      Argon2id (nunca se guarda la clave, ni su hash reversible)
    sesion           cookie HttpOnly, SameSite, 30 dias
    invitaciones     codigo en la barra de direcciones (no se guarda), caduca,
                     maximo 3 enlaces vivos por lista (el cuarto responde 409)
    altas            limite de 10 por hora

Todas esas reglas están en el servidor, no en la interfaz: el límite de altas protege la base, el
máximo de invitaciones evita acumular enlaces vivos, y el código de invitación **vive en la URL**
a propósito (un enlace caducado guardado en la aplicación se aplicaría solo la próxima vez que
alguien la abra, que es peor que no tenerlo).

Y la baja de cuenta: `DELETE /api/yo` borra la persona y **conserva sus líneas** en listas ajenas
(el autor queda a `NULL`, y el `LEFT JOIN` de la lectura es lo que hace que la línea no
desaparezca de la pantalla). Ese detalle se encontró dando de baja una cuenta en un navegador:
la lista pasó de 4 líneas a 3, y la fila seguía en la base.

## 5. Migraciones: cambiar el esquema sin romper el pasado

Siete ficheros `plataforma/sql/00N_*.sql`, aplicados **todos, en orden, en cada arranque** de la
API (`almacen.migra()`). La regla que hace que esto sea seguro es que sean **idempotentes**:
`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `DROP CONSTRAINT IF EXISTS`.

Dos lecciones de aquí, y las dos son clásicas:

1. **Una migración vieja puede resucitar algo que ya no quieres.** `001` creaba un índice único
   sobre `es_de_casa` (una sola lista de casa por persona). Años después, con listas de casa
   creadas por la interfaz nueva, ese `CREATE INDEX IF NOT EXISTS` volvía a crearlo en cada
   arranque… y **la API no arrancaba con dos listas de casa**. Se quitó de `001` y se dejó en una
   migración nueva. Lo encontró la prueba de punta a punta, no una revisión.
2. **Una restricción nueva puede romper un borrado.** El `CHECK` de coherencia del tachado
   (`tachado_por` y `tachado_en` juntos) impedía `DELETE FROM usuario`: al borrar la persona, el
   `ON DELETE SET NULL` dejaba `tachado_por` a nulo con `tachado_en` puesto, y el `CHECK`
   saltaba. La migración `007` lo arregló. Se descubrió dándose de baja.

De ahí una práctica: **antes de aplicar una migración en producción, contar las filas que la
harían fallar** (`SELECT count(*) ...` de la condición que rompe). Se hizo: 0 filas, y después se
aplicó.

## 6. Un solo origen: Caddy

La interfaz y la API se sirven **por el mismo origen** (`:8080`), así que no hay CORS, las
cookies no se pierden entre puertos y la política de seguridad se puede apretar de verdad:

    Content-Security-Policy: default-src 'self'; img-src 'self' https: data:; script-src 'self'
    try_files {path} /index.html      (una sola pagina: las rutas del front no son ficheros)

Dos consecuencias que se aprendieron desplegando (capítulo 12): `script-src 'self'` **prohíbe los
scripts en línea**, así que el buscador del material de aprendizaje tuvo que mudarse a un fichero;
y el `try_files` hace que **cualquier ruta desconocida devuelva la aplicación**, que es lo que se
quiere para una SPA pero hay que saberlo al depurar.

## 7. Medir la API: el andamio engaña

Los números que valen, medidos **contra el servidor de verdad** (la prueba de punta a punta, con
PostgreSQL y Caddy):

    abrir la pantalla de avisos   47 ms en frio (gold recien cambiado) y 9-16 ms en caliente

Y los mismos números medidos con `TestClient` (el andamio de pruebas, en el mismo proceso):

    GET /api/salud   (no hace nada)   frio 477 ms   caliente 451 ms
    GET /api/estado                   frio 539 ms   caliente 508 ms
    GET /api/buscar?q=leche           frio 509 ms   caliente 517 ms

**Un endpoint que no hace nada tarda 450 ms**: el andamio se come todo. Cualquier medida de
latencia hecha con `TestClient` mide el andamio, y por eso las cifras de este proyecto salen del
e2e y de `prueba_produccion`. (Esta es la primera lección del capítulo 12, con números frescos.)

## 8. La puerta del despliegue

Antes de dar por bueno un despliegue, tres comprobaciones, y cada una mira algo distinto:

    uv run pytest -q                                    las reglas de casa (unitarias)
    uv run python -m plataforma.prueba_e2e              el SQL de verdad, contra PostgreSQL
    uv run python -m plataforma.prueba_produccion       **lo que se sirve**: el paquete
                                                        compilado, el CSP de Caddy, la base
                                                        de casa, con una cuenta que crea y borra

La tercera existe por un fallo concreto que las otras dos no podían ver: la API del contenedor
devolvía **500** en un endpoint porque importaba, dentro de una función, un módulo que arrastra
`polars` — que no está en su imagen. La prueba estática de la imagen no lo veía (mira solo los
imports de arriba) y la puerta del navegador tampoco (corría contra el servidor local, donde
`polars` sí está). **Un `TODO BIEN` en desarrollo con la producción rota es el peor resultado
posible**: parece una garantía y no lo es.

## 9. Lo que se aprende en este capítulo

- Separar **leer** (columnar, de solo lectura, recalculado a diario) de **escribir** (relacional,
  transaccional, pequeño) simplifica las dos mitades.
- Una API honesta **dice lo que ha hecho**, no lo que le han pedido (`solo_mios: false`), y
  distingue «no lo sé» de «cero».
- Las migraciones se aplican en orden y en cada arranque: **idempotencia o dolor**.
- Toda restricción nueva hay que probarla contra los borrados y las actualizaciones, no solo
  contra las inserciones.
- Un solo origen quita CORS, problemas de cookies y facilita una política de seguridad estricta
  (que a su vez prohíbe scripts en línea: hay que diseñar con eso).
- **Mide la latencia contra el servidor, no contra el andamio**: un endpoint vacío tarda 450 ms
  con `TestClient`.
- Y la comprobación que cierra el círculo: lo que se sirve, en producción, con sus cabeceras.
