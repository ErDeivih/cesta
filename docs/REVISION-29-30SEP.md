# Revisión de la ingesta: 29 y 30 de septiembre de 2026

Lo que sigue es la revisión de dos pasadas completas -- la de ayer y la de hoy -- con lo que
se ha mirado, lo que estaba mal y lo que se ha hecho. **No es un resumen del registro**: el
registro ya cuenta lo que pasa. Aquí van las cosas que el registro no dice: qué se ha
comprobado por fuera, qué no se puede comprobar, y qué decisiones quedan.

## 0. Con qué se ha mirado

```powershell
uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-28
uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-29
uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-30
uv run python data/debug/precios_alcampo.py     # la comprobación de precios de Alcampo
```

Y el registro de las dos pasadas (`data/ejecuciones.log`), el histórico de `gold` por cadena y
día, y la comprobación de precios publicados que corre al final de cada pasada.

## 1. Ayer, 29 de septiembre: cerró bien

| cadena | productos | errores | tiempo |
|---|---:|---:|---:|
| Aldi | 2.126 | 0 | 91 s |
| Mercadona | 4.335 | 0 | 101 s |
| DIA | 5.723 | 0 | 654 s |
| Carrefour | 16.529 | 4 | 5.633 s |
| Alcampo | 23.635 | 0 | 6.381 s |

`silver` 52.348 filas · `gold` 1.135.124 filas (24 días) · `51825 de 52348` productos
conservan el número de ayer · `emparejar: hecho en 440s` · **`=== todo correcto ===`**.

**`verificar_ingesta` del 29: `problemas: 0`**, y cada diferencia tenía explicación:

- **Alcampo**: 23.635 declarados, 23.635 en bronze, 0 que falten, 0 que sobren. Con un aviso
  honesto: **27 respuestas al tope de la API (300)**, o sea que puede estar cortada a trozos y
  se mira con las búsquedas (que es lo que pasó: la captura quedó por debajo de la última buena
  y se recorrieron los términos del buscador; un término dio HTTP 405, `espumadera`).
- **Carrefour**: 11 declarados que no están, **todos con explicación** (7 en el texto de la
  página pero fuera de la rejilla -- recomendaciones --, 4 solo en páginas sin rejilla).
  Y 1.238 enlaces «sin su id»: el enlace lo da la cadena y se comprueba en vivo.
- **Aldi**: 4 sin precio en su propia API (están en el sitemap y no traen precio).
- **DIA**: 3 categorías del sitemap sin pedir (404 de la cadena o un alias del mismo código).

**Carrefour necesitó rescate**: 25 bloqueos seguidos al empezar, el registro dijo «el bloqueo es
total, no una categoría» y las 655 categorías pasaron al rescate, que rescató **651** y dejó 4
rotas **en el propio Carrefour** (3 con HTTP 500 y 1 con HTTP 520, declaradas con su fecha de
origen: `papeleria/colorear` desde el 8 de septiembre, `papeleria/archivadores`,
`papeleria/pequeno-accesorio` y `congelados/…/resto-del-mundo` desde el 20).

**La comprobación de precios publicados** (mira una muestra al azar y la compara con la ficha de
la cadena): aldi 8/8, dia 8/8, mercadona 8/8, carrefour 7/8 (una «no aparece»: unas almendras
bio a 2,89 € cuya página enseña 0.00/0.90/0.99/1.05/1.10/1.12 -- huele a página de variantes) y
**alcampo 0/8** con «8 sin comprobar: es la conexion, no el dato». Eso era un problema, y es el
apartado 3.1.

## 2. Hoy, 30 de septiembre

| cadena | productos | errores | tiempo |
|---|---:|---:|---:|
| Aldi | 2.059 | 0 | 65 s |
| Mercadona | 4.325 | 0 | 96 s |
| DIA | 5.702 | 0 | 626 s |
| Carrefour | 16.522 | 4 | **3.360 s** |
| Alcampo | 23.859 | 0 | 6.384 s |

`silver` **52.467** filas · `gold` **1.187.367** filas (25 días) · `51754 de 52467` productos
conservan el número de ayer · `emparejar: hecho en 445s` · **`=== todo correcto ===`** ·
`cadenas: 5 | todas de hoy`.

**Carrefour tardó casi la mitad que ayer** (3.360 s contra 5.633 s) y eso no es una mejora
nuestra: es que hoy **no hubo bloqueo total** -- ayer hubo 25 HTTP 403 seguidos al arrancar y
todo el catálogo pasó por el rescate, con su espera de 120 s y su ritmo lento. Es el mismo
catálogo por dos caminos, y el tiempo depende de la cadena, no del colector.

Contadores del día: **30 avisos de WAF, 10 renovaciones de sesión, 0 bloqueos totales, 8 errores
HTTP** (los mismos cuatro productos de Carrefour que su web tiene rotos, más los reintentos).
Alcampo volvió a ir por la escalera de cookies (hasta 10 intentos en una misma categoría) y
terminó con **23.859 productos** y 0 errores de catálogo.

**Y la comprobación de precios publicados, la primera pasada con el arreglo del 403**: alcampo
**5/8 coinciden** (antes 0/8 «no se pudo»), aldi 8/8, dia 8/8, mercadona 8/8 y carrefour 6/8 con
2 «no se pudo» (la red, no el dato). **Ningún producto con el precio mal**: los tres de Alcampo
que no coinciden son el punto ciego del WAF, y ahora se cuenta como tal.

Y **1 aviso saltó hoy** (el primero en tres días), y las categorías nuevas sin mapear bajaron de
13 a **8**.

## 3. Los problemas que sí había

### 3.1 La comprobación de precios de Alcampo no comprobaba nada · **arreglado**

El resumen diario decía, desde el 27 de septiembre:

    alcampo    0/8 coinciden  (8 no se pudo)
    8 sin comprobar: es la conexion, no el dato.

`verificar_precios` distingue `reto` (el WAF: punto ciego, y se dice) de `no se pudo` (la red), y
los ocho caían en «no se pudo» **sin haber visto el reto**: la sesión cacheada ya no valía para
las fichas y Alcampo contestaba **403**. Llamarlo «la conexión» tapaba que el precio de la cadena
que es **el 45 % del catálogo** (23.635 de 52.348 productos) llevaba tres días sin comprobarse
contra su propia página.

Un 403 en una cadena con WAF es el WAF, no la red (un 403 en las demás sigue siendo un fallo de
red, y hay una prueba para cada caso). Medido con `data/debug/precios_alcampo.py`: con la sesión
fresca, los ocho productos contestan `reto` (AWS WAF), que es el estado honesto.

**Lo que sigue sin poder comprobarse**: el precio de Alcampo contra su web mientras su WAF no
deje leer una ficha. La diferencia es que ahora se dice como lo que es -- un punto ciego del
instrumento -- y no como un problema de conexión.

### 3.2 La pantalla de favoritos prometía un orden que no hacía · **arreglado**

No es ingesta, pero salió en la misma revisión y es del mismo tipo: la API decía, en su propio
docstring, «ordenados por lo que ha cambiado y no alfabéticamente», y lo que hacía era devolver
los favoritos **en el orden en que se añadieron**, con el precio de hoy y sin decir si había
cambiado. Ahora el cambio lo mide `movimientos.cambios_de_grupos`, la pantalla tiene su selector
de ventana (7/30/90 días) y lo que **no se puede comparar se dice con su motivo** (`sin
historico`, `cambio de formato`, `ya no esta en el catalogo`) en vez de contar un 0 %.

### 3.3 La cohorte de 1,00 € de Alcampo sigue ahí · **decisión del dueño** (N31)

| fecha | productos a 1,00 € exactos | % del catálogo de Alcampo |
|---|---:|---:|
| 2026-09-21 | 1.241 | 5,22 % |
| 2026-09-25 | 1.296 | 5,42 % |
| 2026-09-27 | 1.292 | 5,36 % |
| 2026-09-29 | 1.287 | 5,45 % |

**Nueve días seguidos** con ~1.290 productos (el 5,4 % de su catálogo) exactamente a 1,00 €, en
categorías que no tienen nada que ver (helados, maquillaje, menaje). No es un fallo de lectura:
Alcampo **publica** ese precio, con su `unitPrice` coherente (0,18 €/100 ml = 1,00 €/560 ml),
`available: true` y ninguna promoción declarada; y pasa todos los filtros estrictos del proyecto.
Lo que no se puede decidir desde aquí es si es una campaña o un precio de relleno: eso es abrir
una ficha y mirarla, y es la pregunta 1 de N31 (`docs/BACKLOG.md`).

### 3.4 La cobertura de Alcampo depende de hasta dónde deje llegar el WAF

| fecha | productos |
|---|---:|
| 2026-09-23 | 23.830 |
| **2026-09-24** | **28.958** |
| 2026-09-25 | 23.912 |
| 2026-09-26 | 23.920 |
| 2026-09-29 | 23.623 |
| 2026-09-30 | 23.859 |

El 24 de septiembre la captura llegó a **540 categorías** y entregó 28.977 productos; los demás
días se queda entre 23.600 y 24.700. No es un error -- es que ese día el WAF no cortó -- pero
conviene tenerlo escrito: **comparar el catálogo de Alcampo entre dos días tiene un margen de
±10 % que no viene del mercado**. La guarda de cobertura (`core/cobertura.py`) impide escribir un
catálogo degradado, y con un día alto por delante el listón para «degradado» sube con él.

### 3.5 Lo que es de las cadenas, no nuestro

- **Carrefour**: 4 categorías con HTTP 500/520 sostenidos desde el 8 y el 20 de septiembre. Se
  declaran, no se cuentan como fallo propio, y no se reintentan indefinidamente. Hoy además
  **22 categorías que la cadena sirve desde su padre** (su listado es el de la rama).
- **DIA**: 2-3 categorías del sitemap que devuelven 404 o son alias de otra (hoy 2).
- **Aldi**: hoy **67 productos en su sitemap sin precio en su API** (ayer 4). Medido con los
  nombres: cámara de videovigilancia, bombillas LED, alicates, un juego de llaves de vaso, un
  libro con sonidos, kéfir -- o sea **los no alimentarios de la semana de oferta**, que Aldi
  publica en el sitemap pero no en su API de precios. Van rotando con las semanas, y por eso unos
  días son 4 y otros 67. No es un fallo del colector: la diferencia entre «declarado» y
  «guardado» es exactamente lo que este verificador existe para explicar.
- **Aldi, y esto es estable**: ~140 filas al día en bronze **sin precio**, y son las mismas
  cuatro categorías (verduras 77, frutas 51, alguna más): fruta y verdura que se vende a peso y
  no tiene precio fijo. Lleva así los cuatro días que se han mirado.

## 4. Lo que no se ha podido comprobar

- **El precio de Alcampo contra su ficha** (el WAF): se dice como punto ciego. Ver 3.1.
- **Los 1.238 enlaces de Carrefour «sin su id»**: la cadena no publica el identificador en el
  enlace; se comprueba en vivo al abrir los 8 productos de la muestra, y coinciden.
- **El 1,00 € de Alcampo**: ver 3.3.

## 5. Lo que queda por decidir

1. **El 1,00 € de Alcampo** (N31, pregunta 1): ¿es campaña o relleno? Se cierra abriendo una
   ficha a mano.
2. **La ventana de los favoritos**: 7 días es la pregunta de la compra; 30 y 90 ya se pueden
   pedir porque hay 24 capturas. Decidir si la de 90 se queda.
3. **El margen de Alcampo**: si el ±10 % de cobertura por el WAF importa para las comparaciones
   del índice, hay que decidir si se filtra por un mínimo de categorías vistas.
