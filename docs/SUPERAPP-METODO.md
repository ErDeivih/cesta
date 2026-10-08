# Método de trabajo y punto de continuación

Escrito el 9 de octubre de 2026, al cerrar la ronda 21 del objetivo. Existe porque **cinco veces** en
esta sesión un parche ha fallado sobre un texto que **sí existía**: lo he comprobado leyendo el fichero
después, y las líneas estaban ahí, literalmente. El problema no es lo que creo recordar; es el método de
parchear. Este documento fija lo que funciona, para no volver a perder rondas en lo mismo.

## Lo que NO funciona

- **Anclar un parche sobre un fragmento multilínea** y sustituirlo. Ha fallado cinco veces, y en las
  últimas dos el texto ancla estaba **comprobado en el fichero** antes de escribir el script.
- **Pasar código con comillas, acentos o acentos graves a `python -c` desde PowerShell.** Tres variantes
  del mismo muro: comillas dentro de cadenas, el terminador de un *here-string* dentro de un bloque `if`,
  y un acento grave en un docstring (que PowerShell lee como escape).
- **Mensajes de commit multilínea con `-m`.** PowerShell los parte.

## Lo que SÍ funciona

1. **Escribir el fichero entero** con la herramienta de ficheros. Sin anclajes no hay nada que pueda no
   coincidir. Es lo que ha funcionado siempre que se ha hecho: `core/diario.py`, `core/recetas.py`,
   `plataforma/api/recetas.py`, `AvisoIdentidad.tsx`, `RecetaDetalle.tsx`.
2. **Leer antes de reescribir**: leer el fichero entero y devolverlo completo con los cambios. Una ronda
   por fichero si hace falta.
3. **Editar por números de línea** cuando el fichero es ajeno o grande: leer, comprobar el contenido de
   esas líneas exactas, y borrar o insertar por índice, como se hizo con el bloque duplicado de
   `tipos.ts`.
4. **Mensajes de commit a un fichero con `git commit -F`**, y el *here-string* **en el nivel de arriba**
   del script, nunca dentro de un `if`.
5. **Pruebas nuevas en fichero aparte** antes que tocar pruebas existentes: `write` y listo.

## Dónde queda el trabajo

**Condición 3 — pantallas y comportamiento persistente. En curso.**

| pieza | estado |
|---|---|
| Detalle por receta leyendo la receta persistida, con **404 real** y selector de versión | **hecho** (ronda 18, commit `9549818`) |
| **Cálculo de raciones, servidor** | **hecho y probado**: `?raciones=6` escala, devuelve `raciones` y `raciones_receta`, y marca `escalada`. `core/recetas.escala`, 6 pruebas (ronda 19, `b2d7e72`) |
| **Cálculo de raciones, pantalla** | **FALTA**: el control para elegir raciones en `RecetaDetalle.tsx` y el parámetro en `useReceta` dentro de `api/recetas.ts` |
| Formulario de edición desde el detalle | falta: el cliente (`useCambiarReceta`) y el servidor (crea versión nueva) ya están |
| Errores al archivar y plan modificable | falta |
| S09: cobertura por nutriente y tendencias **con huecos en vez de ceros** | falta |
| S09: la versión del diario como **enlace verificado o instantánea con procedencia** | falta |

**Cómo hacer la pieza que falta, con el método de arriba:** leer `plataforma/web/app/src/api/recetas.ts`
entero y **reescribirlo** con `useReceta(id, version, raciones)` y `raciones` en su `queryKey`; y hacer lo
mismo con `plataforma/web/app/src/paginas/RecetaDetalle.tsx`, añadiendo el campo de raciones (**16 px
mínimo**, el contrato de móvil lo vigila), pasándolo al gancho y enseñando **las dos cifras** cuando esté
escalada (`data.escalada`, `data.raciones_receta`).

## Lo que sigue abierto de antes

- **Condición 2, D, segunda mitad**: comprobar que la fecha de cada precio **pertenece** a la versión del
  catálogo. La versión ya se informa en `/api/estado` (ronda 17).
- **La persistencia** de la autorización de sustitución en la línea: necesita **PostgreSQL** levantado, y
  se levanta cuando toque esa pieza.
- **La comprobación en navegador** (`uv run python -m plataforma.prueba_suite`), que no se ha pasado desde
  el aislamiento por usuario: necesita el servidor de desarrollo.
- **Condición 4**: puentes idempotentes con vista previa, gráficas con medida/cobertura/universo, y el
  ensayo integral con **dos cuentas y copia de seguridad restaurada**.

## Recordatorio de las reglas que han salvado rondas

- Antes de commitear: `uv run pytest -q` y `uv run ruff check .`. Después, si se tocó el frontend:
  `npx tsc --noEmit` y `npm run build`.
- **Mirar antes de suponer.** Casi todas las rondas perdidas fueron por anclar sobre un recuerdo.
- Un rojo no significa que el código esté mal: **dos veces** el que estaba mal era la prueba.
- Las pruebas que **leen el código** (colores, títulos, móvil, montaje, imagen) han cazado **cinco**
  fallos silenciosos en esta sesión. No se borran.
