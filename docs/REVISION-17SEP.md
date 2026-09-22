# Cesta — revision del proyecto, 17 de septiembre de 2026

Repaso completo buscando fallos, no cosmetica. Salieron **seis**, dos de ellos
serios. Todos corregidos, con su prueba.

---

## 1. La app se quedaba congelada en silencio  · GRAVE

**El fallo.** `plataforma/api/catalogo.py` construye una tabla `buscable` que es
una **copia** del catalogo, hecha al abrir la conexion de cada hilo. Y
`fecha_de_gold()` estaba envuelta en `@lru_cache(maxsize=1)`.

Habia una funcion `reiniciar()` para invalidar las dos cosas, y **nadie la
llamaba nunca**.

**Lo que pasaba.** El pipeline reescribe `grupos.parquet` una vez al dia. Desde
ese momento:

- cada hilo seguia sirviendo el catalogo del dia que arranco, para siempre
- `fecha_de_gold()` devolvia la fecha vieja, congelada
- y como la cache del panel se indexa por esa fecha, **el panel tampoco se
  refrescaba nunca**

Solo se arreglaba reiniciando el contenedor. Nadie se habria dado cuenta: la
interfaz habria seguido ensenando precios, con su fecha correcta al lado. Habria
sido un dato viejo bien etiquetado, que es la forma mas dificil de detectar un
fallo.

**El arreglo.** Se mira la fecha de modificacion de `grupos.parquet`. Si ha
cambiado, se cierra la conexion del hilo y se rehace. `fecha_de_gold()` se guarda
junto a ese sello en vez de en una cache eterna.

**Las pruebas.** `tests/test_catalogo.py`: se escribe un gold de mentira con un
producto, se consulta, se anade un segundo producto, se toca el fichero, y se
comprueba que la siguiente consulta lo ve **sin reiniciar nada**.

---

## 2. "1 cadenas · 1 productos" en pantalla  · VISIBLE

**El fallo.** La busqueda marcaba como comparable todo lo que tuviera
`grupo_id`, y tenia una rama para los productos sin grupo.

Pero **`grupo_id` nunca es null**: el emparejador se lo pone a todo, y **32.486
grupos son de un solo producto**. Asi que:

- la rama de "productos sueltos" era codigo muerto que no devolvia nada
- un producto solo en su grupo salia con el sello de comparable puesto
- y la interfaz pintaba literalmente **"1 cadenas · 1 productos"**

**El arreglo.** Lo que hace comparable a un grupo es tener **dos cadenas o mas**,
no tener identificador. Se quita la rama muerta y se calcula bien.

**Las pruebas.** Dos en `tests/test_catalogo.py`: un producto solo no es
comparable y su ahorro es cero; dos cadenas en el mismo grupo si lo son, con el
ahorro bien calculado.

---

## 3. Doce cifras caducadas en once documentos

**El fallo.** La virtud de estos documentos es que cada decision lleva al lado el
numero que la sostiene. El problema es que los datos cambian todos los dias, y
una cifra que fue cierta en septiembre y ya no lo es **es peor que no poner
ninguna**, porque nadie la vuelve a comprobar.

Estaban desfasadas, entre otras: el tamano del catalogo (52.575 → 51.781), los
grupos comparables (6.448 → 6.448), el historico (405.739 → 560.640), los
aciertos del emparejador (53,7 % → 57 %).

Y una no era un numero sino un concepto equivocado: "31.853 productos no estan en
ningun grupo", que describia un comportamiento que el codigo ya no tenia (ver el
punto 2).

**El arreglo.** Corregidas las doce. Y, para que no vuelva a pasar,
`projects/cesta/verificar_docs.py`: compara los numeros escritos con los datos
de hoy y avisa. **Se ejecuta solo, al final de cada dia**, enganchado a `run.py`.
No arregla nada ni hace fallar el dia: avisa.

---

## 4. Un respaldo que estaba documentado y no existia

**El fallo.** Cuatro documentos decian "el unico volumen que hay que respaldar es
el de PostgreSQL". No habia nada que lo respaldara.

Eso es peor que no decirlo: da una sensacion de seguridad que no se corresponde
con nada. Si se pierde ese volumen se pierden las cuentas, las listas y los
favoritos — lo unico que no se puede regenerar, porque gold sale de raw y raw
sale de las webs.

**El arreglo.** `plataforma/respaldar.bat`:

    respaldar.bat                       guarda uno nuevo, comprimido
    respaldar.bat restaurar <fichero>   lo devuelve, pidiendo confirmacion

Comprueba que el fichero no salga vacio (un respaldo de cero bytes es un
respaldo que no lo es), borra los de mas de 30 dias, y `data/respaldos/` va al
`.gitignore` porque contiene las cuentas.

---

## 5. Once avisos de estilo repartidos por el proyecto

**El fallo.** `ruff check .` daba 24 avisos. Un verificador que siempre da
errores es un verificador que nadie lee.

**El arreglo.** Los 24 a cero:

- imports sin usar y mal ordenados: quitados
- tres `zip()` sin `strict=True`: puestos. En los tres, las listas salen del
  mismo DataFrame o del mismo cursor, asi que una desincronizacion daria **cada
  producto con el precio del siguiente**, en silencio. Mejor que reviente.
- un `lambda` asignado a variable, en `collectors/dia.py`: convertido en funcion,
  que se lee mejor y sale con nombre en los traceback
- dos `except Exception` deliberados: documentados con su motivo
- `with` anidados en pruebas: se ignoran a proposito en `pyproject.toml`, porque
  ahi anidar se lee mejor que una linea de 120 caracteres

---

## 6. El proyecto no esta en git  · PENDIENTE, decision de David

No hay repositorio. Hoy se han tocado veinte ficheros y **no hay forma de ver
que cambio ni de volver atras**. El `.gitignore` existe desde el 7 de septiembre,
lo cual sugiere que la intencion estaba.

Esto no lo arreglo por mi cuenta porque cambia como se trabaja. Pero conviene,
y el `.gitignore` ya excluye lo que no debe subir: `data/`, `.env`, `.venv/` y
ahora `data/respaldos/`.

    git init && git add . && git commit -m "Cesta: fabrica de datos y plataforma"

---

## Estado al terminar

    203 pruebas en verde     (13 nuevas hoy)
    ruff check .             limpio, por primera vez
    verificar_docs           los numeros de los documentos cuadran

**Lo que no se ha podido comprobar** y sigue pendiente de una ejecucion de David:

- La plataforma **nunca se ha levantado con Docker**. Todo lo probado aqui son
  las piezas por separado y la API contra gold real, sin PostgreSQL.
- `sondear_fichas.py` sigue sin lanzarse: desde aqui no hay salida a esos
  dominios. Es la tarea que mas puede desbloquear por lo poco que cuesta.
- El escaner necesita **HTTPS**, y con Tailscale en `http://` no funcionara.
  Hay que comprobarlo antes de programarlo (`BACKLOG.md` tarea 8).
