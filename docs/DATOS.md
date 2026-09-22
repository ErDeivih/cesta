# Cesta — que es todo esto y por que esta montado asi

Escrito el 16 de septiembre de 2026, para explicar en castellano las palabras que
salen por todas partes en este proyecto: parquet, DuckDB, raw, bronze, silver,
gold. No son modas: cada una resuelve un problema concreto que aparece cuando
guardas precios todos los dias.

---

## 1. El problema de fondo

Todos los dias bajan **52.575 precios** de cinco supermercados. En un ano son
19 millones de filas. Y hay dos cosas que van a pasar seguro:

1. **Nos vamos a equivocar leyendo algo.** Ya ha pasado cuatro veces esta semana:
   el precio por kilo de Alcampo, la marca de Aldi, los packs de DIA, las ofertas
   de Carrefour. Cuando lo descubres, necesitas poder **rehacer el pasado** sin
   volver a pedirle nada a nadie.
2. **Las webs van a cambiar.** Un campo se renombra, un JSON cambia de forma, una
   cadena mete un WAF. Lo que ayer funcionaba hoy devuelve otra cosa.

Casi todo lo que sigue es la respuesta a esas dos frases.

---

## 2. Parquet: por que no CSV

Un CSV guarda los datos **por filas**: todo lo del producto 1, luego todo lo del
producto 2. Un parquet los guarda **por columnas**: todos los precios juntos,
todos los nombres juntos.

Suena a detalle tecnico y cambia todo:

- **Ocupa mucho menos.** En una columna de precios todos los valores se parecen,
  y eso se comprime muy bien. Nuestros nueve dias de precios ocupan 4 MB en
  parquet; en CSV serian mas de 40.
- **Leer una columna no cuesta leer las demas.** Para calcular el precio medio
  por cadena solo hace falta leer dos columnas de las cuarenta. En un CSV hay
  que leer el fichero entero.
- **Guarda los tipos.** Un CSV no sabe si `007` es un numero o un texto, y ahi se
  pierden los ceros de un codigo de barras. Un parquet lo sabe.
- **Tiene estadisticas dentro.** Cada trozo del fichero sabe su minimo y su
  maximo, asi que una consulta puede saltarse trozos enteros sin abrirlos.

**Particiones.** Los ficheros viven en carpetas cuyo nombre es un dato:

    data/silver/fuente=alcampo/fecha=2026-09-16/part.parquet

`fuente` y `fecha` no estan dentro del fichero: **son la ruta**. Cuando pides
"solo Alcampo del dia 16", el motor ni abre las demas carpetas. Se llama
particionado de Hive y es la diferencia entre una consulta de medio segundo y una
de treinta.

---

## 3. DuckDB: una base de datos que no es un servidor

Lo normal seria montar PostgreSQL, meter los 19 millones de filas dentro y
consultarlas. DuckDB hace otra cosa: **es una libreria**, no un servicio. No se
instala, no se arranca, no tiene contrasena. Se importa y ya esta.

Y lo importante: **consulta los parquet donde estan, sin copiarlos**.

    SELECT fuente, median(precio_unidad_cent)
    FROM read_parquet('data/gold/grupos.parquet')
    GROUP BY fuente

Eso es SQL de toda la vida contra un fichero suelto. No hay que cargar nada ni
mantener indices. Es lo que se ha usado para todas las cifras de estos
documentos.

**Por que encaja aqui:** nuestras preguntas son de las que leen mucho y escriben
nada ("la mediana por cadena", "cuantos productos cambiaron de precio"). DuckDB
esta hecho exactamente para eso — es columnar, como el parquet — y va del orden
de cien veces mas rapido que PostgreSQL en esas consultas.

**Por que NO lo usamos para todo:** DuckDB es malo con muchas escrituras a la
vez. Cuando tu madre y tu tachais cosas de la lista a la vez, eso es PostgreSQL.
De ahi que en `DESPLIEGUE.md` haya dos motores: **DuckDB para lo que se lee,
PostgreSQL para lo que se escribe.** No es indecision, es que son problemas
distintos.

---

## 4. Las cuatro capas: raw, bronze, silver, gold

Esto se llama *arquitectura medallion* y es una convencion, no una ley. La idea
es que **cada capa hace una sola cosa** y se puede rehacer desde la anterior.

### raw — lo que dijo la web, sin tocar

    data/raw/fuente=alcampo/fecha=2026-09-16/<hash>.json.gz

La respuesta HTTP tal cual, comprimida. No se interpreta, no se limpia, no se
arregla. Solo se guarda.

**Es la capa mas importante y la que mas gente se salta.** Es lo que permite
decir "el precio por kilo de Alcampo estaba mal desde el dia 6" y **arreglar los
diez dias sin volver a pedir nada**. Sin raw, un fallo de lectura es una perdida
permanente de datos.

El precio es el sitio: 338 MB al dia. Por eso `limpiar.py` borra lo de mas de 30
dias — bronze en adelante ya es permanente y ocupa mil veces menos.

### bronze — lo mismo, pero en tabla

Una fila por producto, **las mismas 29 columnas para las cinco cadenas**. Aqui
solo pasa una cosa: traducir el vocabulario de cada web al nuestro.
`packSizeDescription` de Alcampo, `salesUnit` de Aldi y `quantity_per_unit` de
DIA acaban los tres en `formato_txt`.

Lo que **no** pasa: ni limpiar, ni calcular, ni descartar. Si una cadena manda
"350 kg" para un bizcocho, en bronze pone 350 kg.

El contrato esta en `core/schemas.py` y es fijo: si una cadena empieza a mandar
un campo nuevo, o entra en el contrato para todas, o no entra.

### silver — el dato ya utilizable

Aqui se hacen las cuentas, y todas con la misma disciplina: **una correccion solo
se aplica si algo independiente la confirma.**

- `parse_formato` convierte "Pack 6 x 1 L" en (6 litros, pack de 6).
- Las unidades acaban en kg, l, ud o m. Siempre las mismas cuatro.
- Se calcula `precio_unidad_cent` **nosotros**, sin fiarnos del suyo.
- Y se compara con el suyo: `desviacion_ref` mide en cuanto discrepamos. Ahi es
  donde canta un formato mal leido.

Los tres arreglos de esta semana viven aqui o justo antes, y los tres siguen la
misma regla. El de los packs de DIA es el ejemplo: el nombre dice "pack 24 x 33
cl" y el formato dice "33 cl", pero **solo se multiplica si al hacerlo el precio
cuadra al 5 % con el que publica DIA**. De 211 candidatos se corrigieron 110; los
101 que no cuadran se quedaron como estaban.

Eso es lo que separa un dato de una suposicion.

### gold — lo que responde preguntas

Silver contesta "cuanto vale este producto". Gold contesta "cual es mas barato",
que es otra cosa y es la que importa.

    grupos.parquet          el catalogo con su grupo, su calidad y su nutricion
    enlaces.parquet         los pares identico / equivalente entre cadenas
    precio_diario.parquet   una fila por producto y dia: el historico
    precio_derivado.parquet lo anterior + variacion, minimos, maximos, promos
    resumen.parquet         el estado de hoy de cada producto

Aqui vive el emparejador, que es la pieza dificil: decidir que el "Aceite de
oliva virgen extra Hacendado 1 L" de Mercadona y el "ACEITE DE OLIVA V.E.
PRODUCTO ALCAMPO botella 1 l." de Alcampo son la misma cosa. Sin codigo de
barras acierta el **57 %** de los pares conocidos, y esa cifra se mide cada vez
que se toca algo: `emparejar --medir` esconde el EAN a proposito y cuenta.

---

## 5. Por que las capas se pagan solas

El dia 15 descubrimos que Alcampo llevaba desde el dia 6 sin precio por kilo.
Con esta estructura, arreglarlo fue:

    1. cambiar cuatro lineas del colector
    2. volver a leer raw
    3. reconstruir bronze, silver y gold

**Cero peticiones a Alcampo.** Diez dias de datos arreglados en minutos. Sin la
capa raw habrian sido diez dias perdidos, o diez dias de volver a scrapear a
traves de un WAF que ya nos tiene fichados.

Esa es toda la justificacion. Lo demas es vocabulario.

---

## 6. El proyecto entero, de una pieza

    LAS WEBS
       │  colectores: un fichero por cadena, cada uno con sus manias
       │  (Mercadona API abierta · DIA tras Akamai · Carrefour tras Cloudflare
       │   Alcampo tras AWS WAF, con Chrome de verdad · Aldi a pelo)
       ▼
    RAW          la respuesta sin tocar, 30 dias, 338 MB/dia
       ▼
    BRONZE       29 columnas iguales para todos, 1:1 con lo que dijeron
       ▼
    SILVER       unidades canonicas, precio por kilo, formatos resueltos
       ▼
    GOLD         grupos, enlaces, historico, calidad, nutricion
       │
       ├──> la API (FastAPI + DuckDB)  ──> la app y el panel
       └──> PostgreSQL                 ──> listas, favoritos, cuentas

Y atravesandolo todo, tres reglas que no se negocian:

**Cada valor viaja con como se obtuvo.** `calidad_origen` dice si la letra salio
de leer ingredientes o de ordenar por precio. `proc_precio_unidad` dice como se
calculo el precio por unidad. Esto no es burocracia: sin ello, el estudio de
marca blanca del 15 de septiembre habria salido publicado al reves.

**Cada numero lleva su fecha.** Las cadenas no refrescan todas el mismo dia. Un
precio de hace tres dias se ensena, pero no decide en que tienda comprar.

**Un fallo se arregla con una prueba, no con un parche.** Cada uno de los cuatro
de esta semana dejo pruebas detras. Son 24 nuevas y su trabajo es que el fallo no
pueda volver sin que alguien se entere.
