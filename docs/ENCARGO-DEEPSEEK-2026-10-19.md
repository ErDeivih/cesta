# Encargo al agente: Cesta, de producto interno a app comercializable

**Fecha:** 19/10/2026. **Estado del repo:** la app **ya existe y funciona**; esto no es un proyecto
nuevo. Hay que continuarla, no reescribirla.

---

## 0. Antes de nada: dónde está la app

* El código vive en **`F:\aprendizaje\scrap`**. El frontend está en `plataforma/web/app`, la API en
  `plataforma/api`, el núcleo en `core/`, las pruebas en `tests/` y la web de aprendizaje en
  `plataforma/web/aprende`.
* **Arranca en `http://localhost:8080`** (contenedor `cesta-web-1`, que sirve
  `plataforma/web/dist`). La API es `cesta-api-1`; la base, `cesta-db-1`.
* **El build se hace en `plataforma/web/app` con `npm run build`, y el `outDir` es
  `plataforma/web/dist`** — no `dist`. Si construyes y no ves el cambio, estás mirando otra carpeta.
* **La suite está en verde**: `uv run pytest -q tests/` con `CESTA_POSTGRES` a una base **propia**.
  Hay **2 125 pruebas que pasan**, 17 saltan con motivo escrito.
* **Guarda que no se toca**: `facylf-postgres` (5433), la base de casa (5432) y las pruebas
  compartidas de 5434. **No commitees** `core/datos/secciones.yml`, `docs/CIFRAS.md`,
  `docs/SUPERAPP-CONTROL-*.md` ni `docs/SUPERAPP-GOAL-ACTUAL.md`.

> **Aviso sobre otra copia.** Existe un informe de auditoría hecho en **otro espacio de trabajo**
> (`/workspace/cesta-superapp`, rama `codex/auditoria-producto-ux-ci`) con documentos
> `docs/AUDITORIA-PRODUCTO-UX-CI-2026-10-19.md`, `docs/ui/MARCA-Y-EXPERIENCIA.md` y un
> `docs/ENCARGO-DEEPSEEK-2026-10-19.md`. **Ese trabajo NO está en este repositorio**: aquí sólo hay
> `master`, y esos ficheros no existen. Este documento es el encargo **de esta copia**, con lo que se
> midió aquí. Si quieres reunificar, hay que traer la rama o volver a aplicar los cambios mirándolos
> uno a uno; **no des por hecho que están**.

---

## 1. Lo que ya está hecho en esta copia (19/10/2026)

| | |
|---|---|
| **Marca** | `public/icono.svg` propio (una cesta tejida, no un carrito genérico), `public/site.webmanifest`, `<title>`, descripción, `og:`, `apple-touch-icon`. **Servido y verificado por HTTP**: `/icono.svg` → `image/svg+xml`, `/site.webmanifest` → `application/manifest+json`. |
| **M06 · cotización** | `cesta.cotiza()` firma la previa con un sello que incluye cantidades, tienda elegida, precios, promociones, producto efectivo **y la versión del catálogo**. |
| **M06 · confirmación** | `POST /cerrar` exige `sello_esperado`; si no coincide devuelve **409 con la previa nueva y sin escribir**. Sin sello, cierra pero marca `confirmado: false` y `estimado_cent: null`. |
| **M06 · procedencia** | La respuesta lleva `procedencia_importe: "calculado"`. |
| **M06 · tienda ausente** | Si la tienda elegida no tiene oferta, la línea sale **sin precio, con `motivo` y con `alternativas` separadas** — nunca se cambia de tienda en silencio. |
| **M06 · viaje** | `viaje_cent`/`neto_cent` son `null` salvo que alguien dé el coste: cero introducido es cero conocido. |
| **M07 · medida** | `core/banco_identidad.py`: precisión **sobre pares evaluables** (`null` si no hay), con `predicciones`, `evaluables`, `sin_etiqueta` y `cobertura_anotacion`. Desconocido no es negativo. |
| **Prueba HTTP real** | `scripts/aceptacion_m06_cierre.py` mide la cadena entera contra servidor y base de verdad, **TODO BIEN** en 9 comprobaciones. |

---

## 2. Lo que hay que hacer, por prioridad

### P0 — Dinero y confianza (sin esto no es comercializable)

1. **Cierre concurrente e idempotencia.** *Hoy `almacen.cierra_compra` relee líneas después de
   comprobarlas, y un reintento puede crear otra compra.* Hace falta: cerrar dentro de una
   transacción que bloquee la lista, y una clave de idempotencia que devuelva la compra ya hecha en
   vez de crear otra. **Prueba**: dos cierres simultáneos → **una** compra; reintento → la misma.
2. **Procedencia histórica del importe.** *El importe guardado es `calculado` (catálogo), no
   `pagado`.* El histórico tiene que distinguir **calculado / declarado por la persona / acreditado
   por recibo**, y no llamar «gasto pagado» a una suma inferida. Los históricos viejos se conservan
   como **desconocidos**, sin reescritura masiva.
3. **Aislamiento entre cuentas.** *Ya está medido que B no ve las listas ni las recetas de A
   (`/api/listas/<de A>` → 404).* Falta **barrer todos los endpoints** con dos cuentas y comprobar
   que ninguno filtra: favoritos, avisos, despensa, diario, plan, compras, invitaciones, preferencias.
   **Prueba**: por cada ruta, la cuenta B recibe 403/404 y **nunca** datos de A.

### P1 — Que la app se pueda publicar sin sorpresas

4. **CI de verdad.** *Hoy `.github/workflows` sólo tiene un job diario y un keepalive.* Hace falta un
   workflow que en cada push corra: `ruff`, `pytest` con PostgreSQL de servicio, `npm ci`,
   `npm test`, `npm run test:componentes`, `tsc --noEmit`, `npm run build` y la aceptación HTTP.
   **Y que `npm ci` funcione** de verdad (hay `package-lock.json`; comprobar que no está desfasado).
5. **Importación y ficheros del servidor.** *`almacen.py:154` ejecuta SQL leído de un fichero y
   `main.py:462` lee un JSON por ruta.* Comprobar que **ninguna ruta viene del cliente** (path
   traversal) y que las guardas de base de datos son las mismas en todos los sitios.
6. **CSP y cabeceras.** Revisar que el `icono.svg` y el manifiesto entran con la CSP de Caddy, y que
   no hace falta abrir nada.

### P2 — Producto: que sea una app, no cuatro pantallas

7. **El recorrido de una semana, entero.** *La diferenciación no es el icono: es resolver una semana
   de comida con cuentas claras.* Hoy hay Lista, Plan, Diario, Cocina y Despensa; lo que falta es que
   **se sientan una sola cosa**: del plan semanal salen las necesidades, de ahí la lista, de la lista
   la compra con su precio, y del diario lo que de verdad se comió.
   *Criterio de aceptación:* con una persona y una semana, se puede ir de «qué cocino» a «qué compro
   y cuánto cuesta» **sin salir de la app** y sin teclear nada dos veces.
8. **Simplificar la navegación.** *Hay cinco espacios y la cabecera lleva a Favoritos, Ajustes y
   Salir.* Decidir **tres espacios** (Compra, Recetas, Calorías) y dejar el resto dentro, con una
   barra inferior en móvil que no tape el pulgar.
9. **Estados vacíos que enseñan.** *Una pantalla vacía no distingue «no tienes nada» de «estoy
   mirando otro sitio».* Cada vacío debe decir **qué hacer ahora** con un botón que lo haga.

### P3 — Marca

10. **Identidad visual completa.** Ya hay símbolo, manifiesto y título. Falta: iconos PNG 192/512 para
    Android, una imagen `og:image` propia, y una **paleta documentada** (los tokens ya existen:
    `papel`, `tinta-fuerte`, `tinta-suave`, `bien`, `aviso`, `borde`). *Nada de Material ni de
    Tailwind por defecto en lo visible: los tokens son la marca.*
11. **Voz.** Los textos ya son honestos («no lo sé», «sin comparación fiable no hay ahorro que dar»).
    Mantener esa voz: **decir lo que no se sabe** es parte de la marca, no un defecto.

---

## 3. Reglas de trabajo (aprendidas en esta sesión, y no son opcionales)

* **Un cambio sin defecto demostrado no se hace.** Si no puedes medir el fallo antes, no toques.
* **Marcar cada cosa como IMPLEMENTADO / VERIFICADO / LIMITADO.** Nunca decir «hecho» por una prueba
  que compara dos funciones con el mismo supuesto equivocado.
* **`null` no es `0`.** Ni en precisión, ni en diferencias, ni en importes.
* **Volcar la FORMA y el TEXTO entero antes de afirmar que algo falta.** Un filtro que no encuentra
  algo puede estar mal escrito; el texto completo, no. *En esta sesión hubo tres diagnósticos falsos
  por esto.*
* **Finales de línea.** Muchos ficheros son CRLF. Comprobar el conteo antes y después de escribir;
  un `write_text` con `newline="\n"` convierte el fichero entero y sale un `git diff` de mil líneas.
* **Insertar, no borrar.** Un `del lineas[k-1]` se llevó por delante el cierre de un `raise`.
* **El `outDir` del build es `plataforma/web/dist`.**
* **`producto_id` es `fuente:id_fuente`** (`ensayo:arroz-a`), **no el EAN**. El EAN es otro campo.
  *Con el EAN, cero candidatos y cero precio.*
* **El gold del ensayo está fechado el 1 de enero y la ventana de validez es de 3 días**: en el banco
  hace falta `CESTA_DIAS_PRECIO` abierto para que sus precios cuenten.
* **No cierres un paquete por un número.** «7 de 7» ya resultó falso una vez.

---

## 4. Cómo comprobar que no has roto nada

```powershell
cd F:\aprendizaje\scrap
# 1) la base, propia y desechable (nunca 5432/5433/5434)
docker run --rm -d --name cesta-prueba-propia -e POSTGRES_PASSWORD=prueba `
  -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta_propia -p 127.0.0.1:55433:5432 postgres:16-alpine
$env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:55433/cesta_propia'

uv run ruff check .                              # limpio
uv run pytest -q tests/                          # 2125 pasan, 17 saltan
uv run python -m plataforma.comprueba_documentos  # TODO BIEN
uv run python scripts/aceptacion_m06_cierre.py   # TODO BIEN (servidor y base de verdad)
uv run python -m scripts.auditar_cierre_y_banco_20261018   # los cuatro casos correctos

cd plataforma\web\app
npx --no-install tsc --noEmit && npm run lint && npm test && npm run test:componentes && npm run build
```

**Y después, a mano:** abrir `http://localhost:8080` y mirar la pantalla. *Una cosa que compila y
pasa las pruebas puede seguir sin verse.*

---

## 5. Lo que NO hay que hacer

* No reescribir la app desde cero: **funciona y tiene 2 125 pruebas**.
* No tocar `facylf`, la base de casa ni las pruebas compartidas, ni desplegar públicamente.
* No commitear los ficheros del propietario que están sin seguimiento.
* No dar por hecho que el trabajo de la otra copia está aquí.
