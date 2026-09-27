# Stitch, conectado a este proyecto

**Proyecto de Stitch:** `15743377346721964880` («Cesta - comparador de supermercados», privado),
creado el 27 de septiembre de 2026. Endpoint MCP: `https://stitch.googleapis.com/mcp`, con cabecera
`X-Goog-Api-Key` (la clave **no** se escribe aquí: se lee de `data/debug/stitch_key.txt`, que está
ignorada por git, o de `STITCH_API_KEY`).

## Cómo se llama, sin depender del cliente MCP del arnés

`data/debug/stitch.py` habla el protocolo a mano (JSON-RPC sobre HTTP), así que Stitch se puede usar
aunque el arnés no haya cargado su cliente de MCP:

    uv run python data/debug/stitch.py tools                       # qué herramientas hay
    uv run python data/debug/stitch.py screens 15743377346721964880
    uv run python data/debug/stitch.py gen <proyecto> MOBILE data/debug/prompt_inicio.txt
    uv run python data/debug/stitch.py screen projects/…/screens/…

El `projectId` que esperan las herramientas es **el número a secas** (`15743377346721964880`), no
`projects/15743377346721964880`: con la forma larga contestan «Request contains an invalid
argument», que no dice qué argumento.

## Lo que ya está hecho

| paso | resultado |
|---|---|
| sistema de diseño | `.stitch/DESIGN.md` subido al proyecto (`upload_design_md`), y el sistema de diseño creado a partir de él (`assets/bddbedcd3f074baca033d6e85b9d8e94`, «Functional Utility») |
| pantalla 1 | «Cesta · Pantalla Principal» — `projects/15743377346721964880/screens/bc1fef6dd2c94961a94a22b7263f5c8c` |
| pantalla 2 | «Cesta · Resultados de Búsqueda (Leche Entera)» — `projects/15743377346721964880/screens/7d0a3de8285b4ec3bd63325264fe6bca` |
| pantalla 3 | «Portada · Aprender datos con un proyecto de verdad» — `projects/15743377346721964880/screens/bdbf0a85b5aa465395902e4bd4bcad1b` |
| pantalla 4 | «Cesta · Ficha de Producto (Leche Entera)» — `projects/15743377346721964880/screens/a344f64aeb8543218120b87e39f2b33b` |
| los guiones | `.stitch/prompts/01-inicio.txt`, `02-resultados.txt`, `03-portada-docs.txt` y `04-ficha-grupo.txt`: **versionados**, porque el guion es la procedencia del diseño. Dicen quién usa la pantalla, qué datos reales tiene que enseñar y las reglas del proyecto (cifras en ancho fijo, 44 px, 109/57 px, tokens) |
| **portadas al código** | `plataforma/web/app/src/paginas/Inicio.tsx` (el 27 sep 2026, en `/`), `componentes/TablaResultados.tsx` + `paginas/Buscar.tsx` (resultados, el 27 sep) y `paginas/Grupo.tsx` (la ficha, el 27 sep). Portadas **a mano**: el HTML de Stitch trae `cdn.tailwindcss.com` y dos `<script>`, y la CSP de Caddy no lo permite (ver `docs/PANTALLAS.md`) |

La pantalla 2 salió con `deviceType: DESKTOP` aunque se pidió `MOBILE`, y la 1 con un lienzo de
512 x 410: **el aparato que se pide no es el que se recibe**. Se usa como referencia de
composición, no como medida; las medidas (390 x 844, cabecera de 109 px, barra de 57 px) las
comprueba `prueba_navegador.py` sobre la aplicación de verdad.

La generación tarda minutos: la llamada se corta a los 60 s por defecto y el script ya usa 900 s.
Si aun así se corta, la pantalla puede estar generándose: se comprueba con `screens` antes de
repetir, porque repetir crea otra.

## Lo que sigue

1. Bajar el HTML y la captura de cada pantalla (`downloadUrl` de `get_screen`) y **revisar que
   cumple las restricciones**: ni un `<script>` ni un `style="…"` en línea, ni fuentes ni imágenes
   remotas. La de la pantalla 1 **no las cumple**: sirve de referencia visual, no de código.
2. Generar las demás pantallas clave, en este orden: resultados de búsqueda con las cinco cadenas,
   ficha de grupo con la curva de precios, lista con reparto por tiendas, dónde comprar, avisos, y
   la portada del sitio de documentación.
3. Traducirlas al código del proyecto (`plataforma/web/app`, React + Tailwind; y
   `plataforma/aprende.py` para el sitio de docs), sin romper la CSP. La traducción es **a mano**:
   se copia la composición, no el HTML.
4. Medir cada cambio con `plataforma.prueba_produccion`, `plataforma.prueba_navegador` y `pytest`.
   La barra (a) de los quince segundos la cierra el dueño.
