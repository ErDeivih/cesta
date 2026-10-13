# B02 · **Donde va la medida**: el fichero de cobertura, que B03 ya estreno

*(13 de octubre de 2026. **La pregunta que habia que hacer primero -- «¿que hay?» -- y esta vez se hizo antes de
concluir.**)*

## 1. La pregunta, y por que esta vez si

*Las seis rondas anteriores de B02 fueron conclusiones antes de leer. **Asi que esta empieza por la pregunta que
las habria evitado todas: «¿que hay?»** -- y se contesta **mirando**, no buscando con mis palabras.*

## 2. Lo que hay: los colectores guardan dos cosas, y ninguna es una medida

```
projects/cesta/collectors/alcampo.py y carrefour.py:
    write_parquet    4 veces   -- bronze (y silver)
    save_raw         4 veces   -- el crudo
    (y nada mas)

core/storage.py:
    save_raw(source, key, body)              -- el crudo, en `data/crudo/`
    write_parquet(df, layer, source, day)     -- bronze/silver, en `data/<capa>/`
    write_parquet_file(df, path)
    load_raw_bytes / load_raw_reciente / load_raw
```

> **Dos cosas: lo que se descargo y lo que se entendio.** *Y **ninguna de las dos es una medida de la pasada**.*
>
> *Lo que los colectores **cuentan** -- reintentos, bloqueadas, `_por_que_fallan`, `truncadas`, `errores` -- **se
> imprime por pantalla y se pierde.*** **Que es exactamente lo que B02 pide arreglar.**

## 3. Y el sitio donde va YA EXISTE, y lo estreno B03

```
data/cobertura/lidl-2026-10-13.json
```

*El fichero de cobertura de Lidl, de la ronda 43 de esta sesion, con:*
`cobertura`, `region`, `fichas_leidas`, `productos_padre`, `guardados`, `fuera_de_alcance`,
`en_revision`, `con_precio`, `precios_con_vigencia_comprobada`, y su `aviso`.

> **O sea: hay una convencion -- `data/cobertura/<fuente>-<dia>.json` --, tiene campos, tiene precedente, y
> **hoy solo la usa una de las seis fuentes**.*
>
> **Asi que B02, en su parte principal, NO es inventar donde va la medida: es ESCRIBIR LA COBERTURA DE LOS
> OTROS.** *Y la de Carrefour y Alcampo tiene **mas que poner** que la de Lidl, porque **ya cuentan reintentos,
> bloqueadas y por que fallan** -- *solo que a la pantalla.*

## 4. Y esto hace que B02 sea, otra vez, mas pequeno

```
LO QUE HAY:      data/cobertura/<fuente>-<dia>.json   (la convencion, con un usuario: Lidl)
LO QUE FALTA:    que Carrefour y Alcampo escriban el suyo, con lo que YA cuentan:
                   - requests efectivos      (los dos los hacen, y no los cuentan)
                   - reintentos y vueltas    (VUELTAS_DE_RESCATE, renovaciones)
                   - bloqueadas              (ESTADOS_DE_BLOQUEO, RetoWAF)
                   - motivo de cada reintento (_por_que_fallan -- YA EXISTE)
                   - productos unicos        (bronze lo dice)
                   - tiempo                  (no se mide)
                 + los FIXTURES en tests/fixtures/ (la carpeta esta y vacia)
                 + y la decision del navegador, que es del propietario
```

> **Y de las cuatro cosas que el plan pide **medir**, dos ya se calculan y se tiran, una se calcula sola
> (`productos unicos`, que es el bronze) **y solo una no se mide: el tiempo**.*
>
> ***Eso es B02: sacar a un fichero lo que ya se cuenta, y cronometrar.*** *Que es una tarde, no un paquete de
> seis rondas.*

## 5. Y la leccion, que ya esta escrita seis veces y ahora tiene una forma mejor

**Las rondas 105 a 110 costaron seis, y esta costo una.** *La diferencia no fue pensar mejor: fue **hacer la
pregunta barata primero**.*

> **La pregunta era «¿que hay?», y su herramienta era `ls` -- no `grep`.** *Porque `grep` contesta lo que le
> preguntas, **y `ls` te dice que preguntas hay**.*
>
> *Y hay una tercera, que es la que ha dado la respuesta de verdad:* **`git grep` sobre lo que ESCRIBEN los
> colectores, en vez de sobre lo que YO creia que deberian escribir.** *Se busco `save_raw` y `write_parquet` --
> **los nombres que usa el proyecto** -- y salio a la primera.*
>
> ***Buscar con los nombres del codigo, y mirar antes de buscar: eso es todo el metodo.*** *Y estas siete rondas
> son la diferencia entre no hacerlo y hacerlo.*
