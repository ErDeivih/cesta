# Alcance — la app de consumo de Cesta

Escrito el 2026-11-04 por indicación de David. **La ingesta ya está**: 5–6 cadenas con cobertura diaria y comparación real. Ahora toca **el producto que usa la gente**.

## Qué hay que construir

Una aplicación **visualmente atractiva**, para el consumidor de a pie, hecha sobre los datos que ya tenemos. Que quien la abra piense «esto me sirve» y se quede.

## 1. Aspecto

David lo pidió claro: **colores vivos y claros**, no un panel de administración gris.

- Paleta con personalidad, contraste AA calculado (no estimado).
- Espaciado y tipografía con escala, no tamaños inventados por pantalla.
- Animación de 120–220 ms con propósito, respetando `prefers-reduced-motion`.
- **Móvil primero**: se usa de pie en el supermercado, con una mano.
- Estados por pantalla: vacío, cargando, error y sin permiso.

Y antes de la primera pantalla: **sistema de diseño** (`claude-design-system`) y **artboards** (`claude-design`) para que David lo vea y lo apruebe.

## 2. Funcionalidades, cada una estudiada antes

Cada función se estudia **con referencias reales** antes de construirla: qué hacen las apps del sector (Soysuper, Idealo, CamelCamelCamel, las apps de Lidl y Mercadona, Yuka para el etiquetado), qué funciona y qué no. Se deja escrito en `INVESTIGACION-APP.md` con enlace y fecha.

Funciones candidatas (ordenar por valor, no hacer todas):

- **Comparar mi cesta**: lo que compro habitualmente y dónde me sale mejor esta semana.
- **Comparación por kg/litro**, que es la única honesta con los tamaños actuales.
- **Historial de precio** por producto: mínimo, máximo, media y si ahora está caro o barato.
- **Alternativas más baratas** del mismo grupo comparable.
- **Etiquetado**: Nutri-Score, sellos, certificados y aditivos, con búsqueda y filtros.
- **Recetas** con coste real de los ingredientes.
- **Calorías** de lo que compro.
- **Avisos** de bajadas de precio de mi lista.
- **Mi despensa** y la lista de la compra que se genera sola.

## 3. Cómo se construye

- Sobre los datos que ya existen: catálogo, comparables, histórico de precios, etiquetado y nutrición.
- **No se inventa ningún dato**: si una función necesita un dato que no tenemos, se dice y se decide si se ingesta o no se hace.
- Pruebas de flujo, no de detalle.
- Usar los plugins y skills instalados: sistema de diseño, artboards, `claude-dashboard` para las gráficas de precio, `data_profile`/`data_clean`/`data_verify` antes de fiarse de una serie.

## 4. Lo que no se hace ahora

- Backend nuevo: se usa el que hay.
- Compras reales o pago: es comparador, no tienda.
- Datos personales de terceros.

## Orden de valor

1. **Que se vea bien** (sistema de diseño + portada + una pantalla de producto).
2. **Comparar mi cesta** (la función que engancha).
3. **Historial de precio** (la que da confianza).
4. **Etiquetado y recetas** (las que diferencian).
5. Avisos y despensa.

## Reglas

- Sin GitHub Actions. Push selectivo.
- No romper el stack (`plataforma/docker-compose.yml`, proyecto `cesta`).
- `data/` fuera de git.
- Cada pantalla con sus cuatro estados y con prueba de flujo.
- Añadir `resumen:` en lenguaje llano a `ESTADO-AGENTE.md`.

---

## 5. Ampliación del 2026-11-05 (David)

La app tiene buena pinta; se amplía el alcance. **Manda `DOCTRINA-CALIDAD.md` §8: la interfaz no habla de cómo está hecha** (fuera detalles técnicos, explicaciones de cálculos, pies de producto, métricas de relleno, avisos internos y textos de relleno). Antes de dar una pantalla por buena, cada texto se juzga con «¿esto le sirve al cliente para decidir o actuar?».

**Orden de trabajo:**

1. **Que funcione todo lo que ya hay, sin errores.** Primero auditar la app actual (rutas, API, flujos, estados) y arreglar lo roto; y quitar de la interfaz los textos de desarrollador.
2. **Funciones nuevas** (pensadas como conjunto, no pantallas sueltas):
   - **Favoritos** de productos.
   - **Lista de la compra**.
   - **Calculadora de calorías diarias** con pautas de salud según menús (sin prescribir: se enseña lo que la persona registra y se explican las referencias, nunca objetivos de salud impuestos).
   - **Recetas**: establecidas y **creadas por el usuario**.
   - Seguir haciendo pantallas y pensando el producto entero.
3. **Ingesta sin vigilancia**: el scrapeo sigue solo y sin errores; **avisos si falla** (no depender de que alguien mire).
4. **Ofertas con detalle**: tipo de oferta (descuento, 2x1, precio club…), si exige ser **miembro del club** del supermercado, y todo lo que influya en **dónde conviene comprar**. Eso cambia la recomendación.
5. **Cuentas de las apps de los supers**: investigar qué permiten de verdad (API, exportación, importación manual) para mejorar la experiencia con compras y preferencias. Documentar límites; **nunca pedir credenciales**.
6. **Aprender de las listas**: leer las listas para aprender qué compra la persona, sugerir la siguiente, **rellenar sola** con lo que más se repite y **sugerir comprar en otro sitio** cuando convenga. Siempre a favor del usuario.
7. **Investigación** de competencia para todo esto, en `INVESTIGACION-APP.md` con fuentes y fecha.
