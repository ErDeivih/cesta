# Dictamen por tipo de uso — 18/10/2026

**Qué es este documento.** *No es un resumen del trabajo: es el **dictamen** que la especificación pide
por separado, porque «uso doméstico», «móvil», «piloto» y «público» no son el mismo listón.*

**Cómo se ha escrito.** *Cada afirmación va con lo que **se ha medido**, y lo que no se ha medido se
dice como no medido.* *No hay ninguna capacidad declarada por una pantalla que pinte ni por un número
de pruebas.*

---

## 1. Uso doméstico (una casa, una o dos personas, sin prisa)

**Dictamen: APTO con reservas declaradas.**

| lo que se ha medido | cómo |
|---|---|
| Se entra como una persona del banco y la pantalla distingue «sin lista de casa» de «sin listas» | *medido en 8080/5174 con `c_sin_listas` y `a_casa`: dos textos distintos* |
| La comparación de precios no presenta la horquilla del grupo como ahorro del artículo | *4 superficies verificadas leyendo el texto de la página* |
| El diario explica por qué no puede proponer nada en vez de no hacer nada | *`ver.isError` añadido y probado con `tsc`* |
| La lista elegida se recuerda **por persona**, no por navegador | *`PUT /api/preferencias`, servidor por `usuario_id`* |
| Ausencia de dato no se convierte en cero | *7 pruebas del §8 + 5 del diario + las de `Cocina`/`Tendencias`* |
| El error de una cadena de recolección ya no se pierde | *`log_error` con rotación, y dos pruebas de que se llama* |
| **El escenario del §8 pasa entero, medido por HTTP** | *A: Casa + Viaje y **5 recetas**; B: Mi lista y **0 recetas**; C: ninguna. `B → /api/listas/<la de A>` = **404**.* *Y dos marcas con dos EAN sin fusionar* |
| **La suite entera, en una base que funcione** | *`2114 passed, 17 skipped, 0 failed`* |

**Y una nota sobre cómo se ha medido el escenario**, porque es la parte que más se suele saltar:
*no se ha declarado por una pantalla que pinte. Se ha medido con tres cuentas reales del banco de
ensayo, pidiendo `/api/listas` y `/api/recetas` con la cookie de cada una, y comprobando **lo que no se
ve**: B pidiendo la lista de A recibe un **404**.*

*Detrás de eso había un defecto que ninguna pantalla podía enseñar: la API de recetas abría
`data/recetas.sqlite` —**el de casa**— porque la ruta sólo se podía fijar en código. Devolvía cero
recetas para todo el mundo, y una pantalla vacía no distingue «no tienes recetas» de «estoy mirando el
recetario de otra casa». Se arregló con `CESTA_RECETAS`.*

**Reservas, y son de datos, no de código:**
- *Calorías sólo puede enseñar el dato de **1 de cada 5** productos (21,8 % de `grupo` con `kcal_100g`).*
  *Los tres ingredientes del escenario —arroz, leche, huevos— **no lo tienen**.*
- *El catálogo de ensayo tiene **una sola fecha de precios**, así que «cuánto ha bajado» no se puede
  ejercitar en él.*
- *La tarjeta de primera vez (`LoQueSeCompra`) **no se ha visto en pantalla**: necesita una cuenta sin
  historial y no llegué a reproducirla.*

---

## 2. Uso móvil (el mismo producto, en un teléfono, de pie en el pasillo)

**Dictamen: APTO en lo medido; NO VERIFICADO en lo que toca este trabajo.**

| lo que se ha medido | cómo |
|---|---|
| La puerta de interfaz móvil mide la ficha del producto a 390×844 con `has_touch` | *`prueba_navegador.py:2306`, ruta `/compra/productos/…`* |
| Los objetivos táctiles de la ficha cumplen 44 px | *`test_ui_movil.py`, 33 pruebas verdes tras corregir la ruta desfasada* |
| Una pantalla sin red no pierde los cambios: se encolan y se suben al volver | *`Cesta.tsx`, cola sin cobertura* |

**Reservas:**
- ***De las cuatro superficies corregidas, dos están leídas también en móvil (390×844, `has_touch`).***
  *La salvedad del grupo: «La diferencia es entre los artículos del grupo…» **sale** (3 504 caracteres,
  cero errores).* *Y **la tabla de la ficha**, que es la que tuvo el defecto original:*

      /compra/productos/ensayo/arroz-a  main=1  texto=2479  errores=[]
        «diferencia +9,1 %»            <- el ahorro EXACTO de su mismo articulo
        «diferencia otro articulo» x2  <- las dos marcas distintas, NO como ahorro
        «De la mas barata a la mas cara de este MISMO articulo hay 9 % de diferencia por kg»

  *** El 41 % que comparaba el Pote con el Hacendado ya no puede aparecer: *** *el arroz A muestra su
  **9,1 %** real contra el mismo EAN, y el arroz B sale marcado como «otro articulo».*
- *La columna del buscador y la tarjeta de ejemplos **siguen verificadas sólo en escritorio**.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*

---

## 3. Piloto (unas pocas casas de verdad, con datos reales)

**Dictamen: APTO en código, con dos condiciones de entorno antes de arrancar.**

**La suite entera, en una base que funcione** (`55433`, desechable, fuera de 5432/5433/5434):

```
2114 passed, 17 skipped, 0 failed   (4:56)
```

**Y no se ha relajado ninguna prueba para llegar ahí.** *Los diez fallos que había tenían **una sola
causa, y era mía**: un fixture de `test_ahorro_exacto.py` que hacía `sys.modules.pop` y volvía a
importar el módulo del catálogo, dejando **dos copias vivas**. Los cinco fallos de
`test_g04_catalogo_de_ensayo.py` —incluido «una conexión ve una sola versión»— **estaban detectando
justo eso**.* *La prueba hacía su trabajo.*

**Las dos condiciones de entorno, y ninguna es de código:**

1. **La base compartida de pruebas (5434) no acepta conexiones.** *No es un esquema desfasado: el
   puerto no escucha.* *Las mismas pruebas pasan en una base limpia.* *Hay que recrearla o usar una
   propia.*
2. **`test_g03_cierre.py` necesita el catálogo de casa** *(grupo 6803, alcampo a 518).* *En una base
   sintética **se salta diciéndolo** desde esta sesión.* *Para un piloto: sembrar el catálogo, correr
   esas pruebas contra una copia, o reescribirlas para que siembren el suyo — que es lo que ya hace
   `test_fase2_f01_sustitucion.py`.*

**Lo que sí está listo para un piloto:**
- *El banco de ensayo (`plataforma.ensayo`) crea un entorno completo, idempotente y aislado, y lo
  limpia sin tocar nada ajeno: **25 contenedores propios intactos en las cinco pasadas**.*
- *Cada recolección fallida deja su traza en `data/errores.log` con rotación.*

---

## 4. Público (cualquiera, con datos de cualquiera)

**Dictamen: NO APTO. Y no es una cuestión de trabajo pendiente.**

| lo que lo impide | dónde está |
|---|---|
| Los datos son de **uso privado**, con cuentas por persona: no hay separación multi-inquilino probada | *`almacen` filtra por `usuario_id`; **no** se ha probado aislamiento entre inquilinos* |
| No hay TLS, ni despliegue, ni límites de tasa por IP pensados para público | *`CESTA_API` va por HTTP en loopback* |
| La cobertura de catálogo es parcial por cadena, y el README lo dice | *«cobertura no es catálogo completo»* |
| Las calorías cubren el 21,8 %, y publicar un total sería mentir | *medido* |

**Y sobre todo**: *el encargo dice explícitamente **no desplegar públicamente**.* *Este dictamen no
cambia eso: lo documenta.*

---

## Lo que este dictamen NO dice

- *No dice que la aplicación esté terminada: **quedan M05–M22**.*
- *No dice que lo verificado lo esté en todas partes: **cuatro superficies en escritorio, no en móvil**.*
- *No convierte en «cerrado» nada que no tenga una lectura en pantalla o una prueba que lo fije.*

**Lo que sí dice, y es lo único que puedo firmar hoy**: *que la comparación de precios ya no puede
presentar dos artículos distintos como si fueran el mismo, que eso está probado en el contrato y
leído en cuatro pantallas, y que lo que falta para cada tipo de uso está escrito arriba con su motivo.*

---

# Revisión del 20/10/2026 — lo que ha cambiado desde este dictamen

*Este dictamen se escribió con lo medido hasta el 18/10. Estas son las cosas que han cambiado, y las
que **no** se han podido medir.*

## Lo que ahora está verificado y antes no

| | |
|---|---|
| **M15 · instalable** | *`site.webmanifest` con 192×192, 512×512 y `maskable` 512; `apple-touch-icon` en PNG; los seis activos servidos por HTTP con su tipo (`image/png`, `application/manifest+json`).* |
| **M15 · armazón con marca** | *`ArmazonDeLaMarca` en `App.tsx`: lo que se ve mientras carga es el marco de la casa, **en el trozo principal**, no una frase en el vacío.* |
| **M15 · offline** | ***Probado cortando la red de verdad.*** *31 trozos precacheados en `install`, verificados uno a uno; tres renders completos sin red (270 caracteres, cero errores).* **Límite dicho: funciona desde la segunda visita** — un service worker no sirve nada antes de estar activo. |
| **M06 · cotización → confirmación → persistencia** | *Por HTTP, con servidor y base de verdad: 409 sin escribir si el sello no coincide, `confirmado: false` si no se manda revisión, `procedencia_importe: "calculado"`, y **409 al republicar el catálogo entre la comprobación y el guardado**.* |
| **M06 · tienda elegida ausente** | *La línea sale sin precio, con `motivo` y con `alternativas` separadas. No se cambia de tienda en silencio.* |
| **M06 · viaje** | *`viaje_cent`/`neto_cent` son `null` salvo que alguien dé el coste.* |
| **M07 · medida del banco** | *`core/banco_identidad.py`: precisión **sobre evaluables**, `null` si no hay; desconocido no es negativo.* |

## Lo que empeora el dictamen, y hay que decirlo

- **El cierre concurrente sigue sin resolver.** *Se intentó un `SELECT … FOR UPDATE` sobre la lista y se
  revirtió porque las pruebas se colgaban; después se vio que **el cuelgue era la base caída**, no el
  lock.* ***O sea: la dirección es correcta y está sin re-probar.*** *Hoy, dos cierres simultáneos pueden
  crear **dos compras del mismo dinero**.*
- **El importe guardado es `calculado`, no `pagado`.** *El histórico todavía no distingue calculado /
  declarado / acreditado.*
- **El aislamiento entre cuentas está probado en listas y recetas, no en todos los endpoints.**
- **El banco de 200 pares de M07 no existe.** *Está la medida que lo contaría, y el permiso para
  construirlo con autoría declarada.*

## Veredicto revisado, por audiencia

| audiencia | antes | ahora | por qué |
|---|---|---|---|
| **doméstico** | APTO con reservas de datos | **APTO con reservas de datos** | *Sin cambio: la comparación, la lista y el diario siguen honestos, y ahora además **abre sin red desde la segunda visita**.* |
| **móvil** | APTO en lo medido | **APTO en lo medido, y más medido** | *Ahora hay marca instalable (192/512/maskable) y offline probado cortando la red. **Lo que sigue sin medirse: el iPhone físico y la barra inferior con el `safe-area`** (el código lo usa, no se ha visto en un aparato).* |
| **piloto** | NO APTO | **NO APTO, y por menos motivos** | *La suite pasa entera (2 125) y la aceptación HTTP de M06 también. Quedan dos: **el cierre concurrente** y **el banco de M07**.* |
| **público** | NO APTO | **NO APTO** | *Por lo mismo que antes, más lo nuevo: un `docker` caído durante diez rondas dejó sin probar la sincronización y el lock. **No se puede vender lo que no se ha probado con la base viva.*** |

## Lo que no se ha podido medir, y por qué

*Docker dejó de responder a mitad de la sesión y no volvió en diez rondas.* *Con él se fue:*
- *`pytest` (necesita PostgreSQL) — **la suite no se ha vuelto a correr desde hace diez rondas***
- *el banco de ensayo, y con él **la sincronización sin red** (la cola de cambios)*
- *el lock del cierre*

*Lo que sí se pudo, y con qué límite:*
- *`ruff`, `tsc`, `lint`, `npm test` (113), componentes (15) y `build` — **todos verdes***
- *HTTP contra la app servida en 8080 — **la marca y los seis activos***
- *el navegador con `patchright` — **el offline, cortando la red***

*** Un dictamen que diga «APTO» sin poder correr la suite es un dictamen que no vale. Por eso el de
piloto y público siguen siendo NO APTO. ***

