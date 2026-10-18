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
- ***De las cuatro superficies corregidas, una está leída también en móvil.*** *La salvedad del grupo
  se ha leído a **390×844 con `has_touch`**: «La diferencia es entre los artículos del grupo…» **sale**,
  y la página mide 3 504 caracteres sin un error de JavaScript.* *Las otras tres (tabla de la ficha,
  columna del buscador, tarjeta de ejemplos) **siguen verificadas sólo en escritorio**.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*

---

## 3. Piloto (unas pocas casas de verdad, con datos reales)

**Dictamen: NO APTO todavía, y por dos motivos concretos.**

1. **El esquema de la base compartida de pruebas está desfasado.** *13 pruebas de integración fallan en
   5434 y **pasan en una base limpia** (`55433`, desechable).* *Un piloto con una base sin migrar
   fallaría igual.*
2. **Una prueba de cierre depende del orden.** *`test_g03_cierre.py` pasa sola (se salta) y falla en
   compañía.* *Limpiar `dependency_overrides` antes del `yield` **empeora** (de 1 a 3 fallos): el
   arreglo es entender qué estado comparte, y eso no está hecho.*

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
