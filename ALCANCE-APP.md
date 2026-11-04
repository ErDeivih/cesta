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
