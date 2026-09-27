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
| sistema de diseño | `.stitch/DESIGN.md` subido al proyecto (`upload_design_md`) |
| pantalla 1 | «Cesta · Pantalla Principal» — `projects/15743377346721964880/screens/bc1fef6dd2c94961a94a22b7263f5c8c` |
| guion de esa pantalla | `data/debug/prompt_inicio.txt` (las cuatro preguntas de la barra (a), los datos reales y las reglas del proyecto) |

La generación tarda minutos: la llamada se corta a los 60 s por defecto y el script ya usa 900 s.
Si aun así se corta, la pantalla puede estar generándose: se comprueba con `screens` antes de
repetir, porque repetir crea otra.

## Lo que sigue

1. Bajar el HTML y la captura de cada pantalla (`downloadUrl` de `get_screen`) y **revisar que
   cumple las restricciones**: ni un `<script>` ni un `style="…"` en línea, ni fuentes ni imágenes
   remotas.
2. Generar las demás pantallas clave, en este orden: resultados de búsqueda con las cinco cadenas,
   ficha de grupo con la curva de precios, lista con reparto por tiendas, dónde comprar, avisos, y
   la portada del sitio de documentación.
3. Traducirlas al código del proyecto (`plataforma/web/app`, React + Tailwind; y
   `plataforma/aprende.py` para el sitio de docs), sin romper la CSP.
4. Medir cada cambio con `plataforma.prueba_produccion`, `plataforma.prueba_navegador` y `pytest`.
   La barra (a) de los quince segundos la cierra el dueño.
