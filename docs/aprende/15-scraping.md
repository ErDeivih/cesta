---
seccion: Ingeniería de datos
resumen: Cómo se recoge el dato de cinco webs distintas, qué es un WAF, por qué el crudo es sagrado y cómo se detecta un fallo silencioso.
en_una_frase: Cinco webs, cinco trucos: el dato se recoge guardando el crudo primero, respetando el ritmo y desconfiando del silencio.
---

# 15 · Scraping: traer el dato de cinco webs distintas

Este capítulo es el que faltaba para entender de dónde sale todo lo demás. Scraping no es «bajar
HTML»: es **un sistema** con un cliente HTTP que se comporta como un navegador, una caché que
permite reprocesar sin volver a golpear la web, controles que detectan cuando falta media tienda,
y una capa de datos detrás que hace el resto del trabajo posible.

## 1. Los cinco casos son cinco problemas distintos

No hay dos cadenas iguales, y eso es lo primero que aprende quien hace scraping de verdad:

| cadena | cómo se recoge | lo que tiene de particular |
|---|---|---|
| **Mercadona** | API JSON pública (`/api/categories/`, `/api/products/<id>/`) | el precio **depende del almacén**: hay que fijar el código postal antes de recorrer nada |
| **Aldi** | sitemap oficial de productos + API por lotes (`pds/<ids>?scope=es_pen`) | la API regala el €/kg ya calculado, el precio tachado y hasta el `validUntil` |
| **Carrefour** | sitemap + catálogo SSR con `window.__INITIAL_STATE__`, de 24 en 24 | el `Crawl-delay: 60` de su `robots.txt` es de **TwengaBot**, no de `User-agent: *` |
| **DIA** | catálogo paginado + maestro incremental por SKU (de ahí sale el **EAN**) | protección **Akamai**: ritmo lento y huella de navegador real |
| **Alcampo** | API interna + árbol de categorías recursivo | **AWS WAF** y un catálogo que se trunca: hay que bajar a las ramas hijas y barrer 600 términos de búsqueda al día (de 5.153, que rotan en ~9 días) |

Tres lecciones que se sacan de esa tabla:

1. **Lee la fuente antes de programar.** Aldi publica un sitemap y una API por lotes; recorrer su
   menú a mano es perder el tiempo. Mercadona tiene API; parsear su HTML sería un error.
2. **El `robots.txt` hay que leerlo con cuidado.** Un `Crawl-delay` puede ser de otro bot
   (`TwengaBot`) y no aplicarte; y al contrario, lo que parece permitido puede estar protegido
   técnicamente (Akamai, WAF). Está documentado en `docs/RECON.md`.
3. **Cada protección pide una respuesta distinta**: ritmo, huella, navegador… pero **nunca**
   resolver un CAPTCHA ni usar proxies residenciales: en este proyecto son reglas, no opiniones.

## 2. Un solo cliente HTTP, con memoria

Todo pasa por `core/fetch.py`, y eso no es una manía de orden: es lo que permite tener **una**
política de ritmo, **una** de reintentos y **una** de guardado del crudo.

    huella          curl_cffi impersonando Chrome (`impersonate="chrome131"`)
    reintentos      con retroceso, y solo para lo que se puede reintentar
    ritmo           una espera entre peticiones, por dominio
    crudo           **cada respuesta se guarda en disco antes de parsearla**

Guardar el crudo antes de parsear es la decisión más importante de todo el scraping, y su motivo
es práctico: **cuando el parser está mal, se arregla y se reprocesa desde el disco, sin volver a
pedirle nada a la web**. Reprocesar cuesta minutos; volver a rastrear cinco webs cuesta una hora
y te expone otra vez a que te limiten.

El volumen de esa caché, medido hoy:

    data/raw        72.426 ficheros   2.874,6 MB   (lo que devolvio la web, tal cual)
    por pasada          ~338 MB                     (lo que ocupa un dia de captura)

## 3. Un WAF no se «salta»: se pasa una vez y se reutiliza

Alcampo protege su catálogo con **AWS WAF**. Sin sesión, las páginas llegan con un reto de
JavaScript (`window.gokuProps`) en vez de datos. Un cliente HTTP no puede ejecutar ese reto: hace
falta un navegador de verdad. Y aquí está el diseño que funciona:

    un navegador AL DIA, no uno por pagina

El navegador resuelve el reto una vez, deja cookies que valen horas, y **esas cookies se reutilizan
desde el cliente HTTP plano** (`core/waf.py`). Dos detalles que costaron un intento fallido cada
uno:

- **Se valida por resultado, no por el nombre de la cookie.** Da igual cómo se llame el testigo:
  lo que se comprueba es que una **página de categoría real** llegue con datos. Buscar
  `aws-waf-token` a ciegas fallaba aunque la sesión ya fuese buena.
- **Se copia también el User-Agent.** El testigo de AWS WAF va atado al agente que lo obtuvo:
  mandarlo con otro agente lo invalida.

Y una regla del proyecto que se cumple siempre: **si el bloqueo es explícito, se para**. No se
resuelven CAPTCHAs, ni a mano ni automatizado; no hay proxies residenciales; y el ritmo se baja
cuando la web da señales de estar sufriendo (`docs/COMPETENCIA.md`, `docs/CADENAS.md`).

## 4. El crudo es sagrado; el bronze, más

Las capas tienen una jerarquía de irreversibilidad que conviene tener clara:

    raw      lo que devolvio la web. Se puede tirar cuando caduca: se puede volver a pedir.
    bronze   parquet tipado del dia. NO se tira: si se pierde, no se puede reconstruir sin
             volver a rastrear.
    silver   limpio y normalizado. Reconstruible desde bronze.
    gold     lo que ve la aplicacion. Reconstruible desde silver.

Esa jerarquía está escrita en el código (`core/storage.py`) por una razón concreta: **el 18 de
septiembre de 2026 alguien pasó un día entero creyendo que una partición de bronze se había
borrado sola**. Resultó que la habían apartado a mano, a propósito y bien, pero la conjetura duró
porque nada en el código decía qué se puede tirar y qué no. Ahora lo dice.

## 5. El fallo que no da error: cobertura

Este es el apartado más importante del capítulo, y sale de un caso real y caro.

**El 18 de septiembre de 2026, Alcampo entregó 20.571 productos en vez de 23.573.** La ejecución se
dio por **completa, con cero errores**. El bronze se escribió, el pipeline lo procesó y el catálogo
del día salió a la aplicación. Lo que faltaba era **la rama Frescos entera**: 2.646 productos el
día anterior, 91 ese día. Fruta, verdura, carne y pescado: justo donde más se notan las
diferencias de precio entre supermercados.

Y los tres controles que había **miraban el total**:

    check_drift        aviso en el log, no decide nada
    MERMA_ACEPTABLE    solo se aplica si la ejecucion ya se dio por parcial
    errores == 0       no hubo ni un error: nadie fallo, simplemente no se pidio

De ahí nació `core/cobertura.py`, que compara la captura de hoy con la última buena **rama por
rama**, no en total. Es la diferencia entre «hoy hay menos productos» (que puede ser normal) y «hoy
falta una categoría entera» (que no lo es nunca).

> **La lección:** en scraping, lo peligroso no es el error, es el éxito incompleto. Un sistema que
> falla ruidosamente se arregla en una mañana; uno que entrega dos tercios del catálogo sin decir
> nada puede tirar meses de análisis.

## 6. El registro de ejecuciones, que vale más que el scraper

`core/runlog.py` apunta **una fila por ejecución y cadena** (`ts, fuente, filas, errores, segundos,
ok`, en `data/runs.csv`, con un candado porque las cinco cadenas corren en paralelo). Sobre ese
fichero se hace la detección de deriva: si una cadena entrega de repente la mitad de filas que su
media de siete días, salta el aviso.

El comentario del módulo lo dice sin rodeos: *«una fila por ejecución + detección de deriva. Vale
más que el propio scraper»*. Es cierto, y es contraintuitivo: el código que trae el dato se
reescribe cada semana; el registro que dice **cuánto trajo y si salió bien** es lo que permite
saber que algo va mal antes de que se note en el análisis.

## 7. Cómo se añade una cadena nueva

El procedimiento está en `docs/COLECTORES.md` §4, y el orden importa:

1. **Sondear antes de escribir el colector** (`projects/cesta/sondear_cadena.py`): qué URLs
   responden, si hay API o solo HTML, qué campos trae cada ficha, si hay `robots.txt` y qué dice.
2. **Escribir el colector** contra el **esquema de bronze** (`core/schemas.py`), no contra lo que
   salga: si un campo no se puede rellenar, se deja vacío y se documenta (nunca se inventa).
3. **Medir la cobertura** desde el primer día, rama por rama.
4. **Añadirlo al registro** de ejecuciones con su nombre, y comprobar que la primera pasada
   completa cuadra con lo que trajo el sondeo.

Y una comprobación que ya ha salvado más de una vez: `projects/cesta/auditar_crudo.py` compara las
filas que el colector dice haber leído con las que acabaron en bronze. Un descuadre ahí es una
pérdida silenciosa, y se caza antes que en el análisis.

## 8. Lo que un proyecto así deja de aprender

- **El scraping es ingeniería de sistemas, no parseo.** Cliente, caché, ritmo, sesión, registro y
  validación: es lo mismo que hay detrás de cualquier integración con una API ajena.
- **Guardar el crudo te da el derecho a equivocarte** en el parser, que es lo que más se equivoca.
- **El silencio es el enemigo**: los controles tienen que mirar la forma del dato (rama, cadena,
  día), no solo el total.
- **Respetar al de enfrente es parte del diseño** (ritmo, `robots.txt`, nada de CAPTCHAs ni
  proxies), y no resta capacidades: aquí se recogen cinco catálogos al día con un PC de casa.
- Y la que más se repite en todo este material: **mide lo que traes, no lo que crees que traes**.
