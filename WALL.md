# WALL — cesta (superapp de compra)

Copiado del bloque 7 de `F:\EspacioCodigo\_flujo-dsh\MAPA-DE-OBJETIVOS.md` el **2026-11-05**.
Esta es la lista de casillas de la app de consumo. Se marca aquí al terminar, y no se para
hasta agotar el bloque.

**Objetivo final**: comparar precios de verdad entre cadenas y ayudar a comprar mejor.

**Terminado cuando**: digo mi compra habitual y me dice dónde comprar y qué me ahorro.

## Casillas

- [x] Ficha de producto (precio, €/kg, historial, alternativas). **Hecho 5/11** (ruta `/compra/productos/:fuente/:idFuente`; `logica/juicio.ts` con la ventana real y pruebas rojo→verde).
- [x] Comparar mi cesta. **Hecho 5/11** (`/compra/listas/:listaId/comparar`; corona solo la cadena que cuenta todas las líneas y no resta ofertas condicionadas).
- [x] Favoritos, lista de la compra. **Hecho 5/11** (vista de lista con precio estimado y precio por línea; favoritos con rango real de historial).
- [x] Calculadora de calorías con pautas de salud. **Hecho 6/11; fuentes verificadas 8/11** (pantalla de objetivo/comidas + `/calorias/pautas`: Mifflin + actividad, objetivo mantener/perder/ganar con su por qué, macros con rangos y pautas de fibra, azúcar, sal, agua, fruta/verdura y alcohol con fuente y enlace; suelo de seguridad y aviso médico; sin prescribir). Las ocho fuentes oficiales se comprobaron de nuevo: HTTP 200 y fecha coincidente (`docs/CALORIAS-PAUTAS-2026-11-06.md` §7).
- [x] Recetas (establecidas y de usuario). **Hecho 5/11** (listado con recetario/archivadas y detalle con coste por ingrediente cuando hay precios; no hay semilla de recetas «establecidas» en la API).
- [x] Ofertas con su tipo y si exigen club del súper. **Hecho 6/11** (`/compra/ofertas` + `GET /api/ofertas`: tipo, condición y club; sin precio final inventado).
- [x] Integración con las apps de los supermercados. **Hecho 6/11; ampliado 8/11; en espera de David para el mapeo automático y una exportación RGPD real, con límites**: no hay API de consumidor en las seis cadenas; la vía lícita es la importación manual (texto, CSV o JSON, pegado o subido), el vínculo revisable de cada línea al catálogo (también «buscar coincidencias en todas») y la exportación de la lista a CSV/texto. Sin credenciales ni login automatizado (`docs/INTEGRACION-APPS-SUPERS-2026-11-06.md`). 31 pruebas de importación/exportación/relleno pasan.
- [x] Aprender de las listas: rellenar sola, recomendar, sugerir otro sitio. **Hecho 6/11; verificado 8/11** («Rellenar de una vez» con previa y confirmación, «la siguiente» por el orden de la API, y comparar al lado; sin inventar frecuencias). Las 7 pruebas de `Mosaico` pasan.

## Hecho antes de esta lista (no estaba en el bloque, pero sostiene las casillas)

- [x] Sistema de diseño «Cesta App» aprobado por David (2026-11-05) e implementado en la app:
      38 colores en claro/oscuro, tipografía, espaciado, radios, sombras y movimiento 120/220 ms.
- [x] Portada nueva en `/` con esos tokens (buscador, «Mi cesta», «Se han movido», pasillos y
      barra Compra/Recetas/Calorías), con sus cuatro estados y sin textos de desarrollador (§8).
- [x] Ingesta del 5/11 cerrada sola y vigilada: 6 cadenas, gold `20261105-123941`, y
      `scripts/vigilar_ingesta.py` enganchado a `ejecutar.bat` (avisa solo si hay fallo).
- [x] **Vigilante con programación propia** (7/11): tarea «Cesta vigilante» diaria a las 08:00,
      14:00 y 20:00 y al iniciar sesión, con **margen de arranque hasta las 08:00** (antes no
      avisa de que falte), porque si el Programador no lanza la recolección el vigilante del `.bat`
      tampoco corría. Deja `INGESTA-DETENIDA.txt`, `vigilante.log`, JSON y refresca el panel.
      Primera ejecución real verificada 07/11 11:48:59 con resultado 0 (día en curso).

## Artboards **aprobados** por David (2026-11-05, 20:16)

Añadidos al canvas `designs/cesta-app` (10 tableros en total). David los valida **antes** de
implementar cada pantalla:

- [x] Lista de la compra (`Lista.dc.html`): productos con cantidad, precio estimado 10,70 €.
- [x] Favoritos (`Favoritos.dc.html`): 3 guardados, rango de su historial de 60/59 días.
- [x] Comparar mi cesta (`Comparar.dc.html`): Alcampo 7,19 € gana con 3 de 3; DIA 10,16 y
      Carrefour 10,97; Mercadona/Aldi/Lidl incompletos.
- [x] Recetas, listado (`Recetas.dc.html`): recetario y «mis recetas».
- [x] Receta y coste (`Receta.dc.html`): tortilla, 5,32 € (1,33 €/ración) con ingredientes.
- [x] Calorías (`Calorias.dc.html`): 1.075 de 2.200 kcal y las tres comidas del día.
- [x] Ofertas (`Ofertas.dc.html`): tipo y condición de club en 5 ofertas reales.
- [x] Tu perfil (`Perfil.dc.html`): cadena habitual, dieta, alérgenos, objetivo y avisos.

## Notas de trabajo

- Orden acordado por David (2026-11-05): ficha → comparar mi cesta → lista → favoritos →
  recetas → calorías → ofertas → perfil → apps de supers → aprender de las listas.
- Lo que se puede enseñar ya: portada en `http://127.0.0.1:8080/`.
- Reglas: `DOCTRINA-CALIDAD.md` §8 en todas las pantallas, sin GitHub Actions, push selectivo,
  `data/` fuera de git y `resumen:` en `ESTADO-AGENTE.md`.

## Verificación de ingesta del 06/11/2026

- [x] La tarea de Windows «Cesta diaria» está habilitada y su último resultado fue 0. Publicación de la pasada: `20261106-123403` (commit `d885a7f`).
- [x] La verificación y el vigilante pasaron 31 pruebas con datos sintéticos. Ante fallo, el vigilante genera el parte local y devuelve un código distinto de cero.
- [x] Comprobación independiente: tarea «Cesta vigilante» (08:00, 14:00, 20:00 y al iniciar sesión) que ejecuta `ejecutar-vigilante.bat` aunque la recolección no haya arrancado; deja `data/INGESTA-DETENIDA.txt`, log y JSON, y refresca el panel.

## Verificación de ingesta del 07/11/2026

- [x] El vigilante arrancó **antes de las 08:00 sin avisar** de que faltara: margen de arranque en el código y prueba 05:00 (aviso) / 09:00 (fallo).
- [x] Su primera ejecución programada se verificó con un disparador temporal a las **13:20**: la tarea se lanzó, terminó con resultado **1** y dejó `data/INGESTA-DETENIDA.txt` a las 13:25:02.
- [x] **El aviso era correcto**: la pasada del 7/11 terminó con Alcampo `ok=False` y sin partición de bronce, y no se publicó el gold. No fue un fallo del vigilante.
- [x] **Recolección relanzada el 7/11 a las 14:22** (`ejecutar.bat --forzar`): seis bronces escritos y gold **20261107-143704** publicado. Por cadena: Carrefour 16.811/1 error · DIA 5.704/0 · Mercadona 4.280/0 · Aldi 2.826/0 · **Alcampo 22.834/0** (captura corta, 81,5 % de la referencia del 17/10, aviso) · Lidl 91/0. Diagnóstico en `docs/DIAGNOSTICO-ALCAMPO-2026-11-07.md`: fue AWS WAF, no selector; el crudo cacheado permitió recuperar el día.

## Verificación de ingesta del 08/11/2026

- [x] Recolección completa lanzada a las 15:12 (`--forzar`): Carrefour 16.816/1, DIA 5.686/0, Mercadona 4.286/0, Aldi 2.824/0, Lidl 91/0.
- [x] Alcampo cayó otra vez (navegador cerrado durante el WAF, `TargetClosedError`). El crudo parcial quedó en `data/raw`.
- [x] **Recuperado desde el crudo** con `scripts/recuperar_alcampo.py`: 23.313 productos, 0 errores, bronce 1,46 MB; gold **20261108-175843** publicado (2.760.653 filas, 63 días).
- [x] Vigilante: 1 aviso (captura corta de Alcampo, 83,2 %), 0 fallos; `INGESTA-DETENIDA.txt` retirado.
- [x] Automatizado: el vigilante llama al recuperador tras el primer fallo, con marca diaria para no repetir; 6 pruebas.
