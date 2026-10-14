# Cierre del 14/10/2026 · **las cinco puertas, verdes** -- y lo que queda

## 1. Las cinco puertas

```
*** `uv run ruff check .` ***   *** All checks passed! *** ✓
*** `uv run pytest -q` ***      *** 2.049 passed · 0 failed · 0 errors · 17 skipped in 200 s *** ✓✓✓
*** `npm test` ***              *** 81 pass · 0 fail *** ✓✓✓
*** `npx --no-install tsc --noEmit` ***  *** exit 0 *** ✓✓✓
*** `npm run build` ***         *** built in 32.62s · exit 0 *** ✓✓✓
```

*Y **el frontend no se ha tocado** en toda la tanda: *81 antes, 81 ahora.* *Lo que subio fue Python:*
*2.033 (ronda 302) -> **2.049**, *con los ensayos de los dos puentes, del ensayo de restauracion y del respaldo.*

## 2. *** Y el ultimo rojo no era del codigo, era del ensayo ***

```
*** el unico fallo ***  *** `test_fase2_f05_ficha_mercadona.py::test_contra_el_crudo_real` *** *
  *-- *decia «ingredientes sospechosamente cortos», *y **yo lo lei como «9 ingredientes»** ⚠️ *
  *-- *y `len()` de una cadena son *** CARACTERES ***: *eran **9 caracteres***
*** lo que era ***  *la ficha `3915` es *** una Granada ***, y su `ingredientes` es *** `"Granadas."` *** *
  *-- *y **es una ficha COMPLETA**: *una granada es una granada* · *y `allergens` es `x99`, *que el
  lector **extrajo bien***
*** -> el umbral confundia «**ficha corta**» con «**ficha rota**», *y **cualquier producto de un solo
  ingrediente lo rompia*** **
*** el arreglo ***  *el umbral se mantiene, *y **se perdona UN caso**: *cuando el ingrediente **es el
  producto*** *-- *y nada mas* *
*** y comprobado caso a caso ***  *`Granada->Granadas.` pasa · `Nata->Nata.` pasa ·
  *** `Nata->'x'` FALLA *** · *** `Tarta->Harina'` FALLA *** · *una ficha larga pasa* ✓
```

> *** El ultimo rojo **no se tapo ni se relajo**: *se **entendio**. *Y **el ensayo sigue cazando
> exactamente lo que existe para cazar** -- *que es **la unica forma de arreglar un vigilante.** *

## 3. El complemento del 14/10, punto por punto

```
*** (1) LOS ENVASES ***  *** cerrado en LOS DOS PUENTES ***, *medido en vivo, *y **cada uno con su
   regresion, que falla sin el arreglo** *
     *plan  -> 3.800 g de un envase de 1.000 g -> **4 envases**, 200 g de sobrante, `cantidad = 4`* ✓
     *receta -> 2.800 g -> **3 envases**, `cantidad = 3`, *y el `producto_id` conservado* ✓
   *-- *y la causa era **un contrato, no un calculo**: *`previa_compra` **es pura a proposito**, *
   *exige el tamaño puesto en el ingrediente, *y quien lo ponia **solo lo hacia al leer una receta***

*** (2) EL INGREDIENTE SIN CATALOGO ***  *entra como **«pendiente de identificar»**, *
   *`envases = None`, *y **la nota lo dice** -- *sin inventar* ✓

*** (3) LIDL ***  *las **tres salidas mudas** registran ya (con sus dos regresiones), *
   *y **el ciclo real**: *`lidl` **79 filas · 0 errores · 146,9 s · ok=True**, *`LastTaskResult: 0`* ✓
   *-- *y **publicado**: *79 productos en `gold` (`v20261014-130958`), *con *** `region='28'` *** *
      *y con **precio, cantidad y unidad** *(-- o sea: **comparables**)*

*** (4) LA RESTAURACION ***  *** las TRES patas, dentro del ensayo *** *
   *** PostgreSQL ***  *`lista_linea 346 · usuario 73 · lista 257 · compra 97 · lista_acceso 272`* ✓
   *** las SQLite ***  *`recetas`: abre, `integrity_check` ok, plan 7, receta 5, version 5* ✓
   *** el diario ***   *`sin_copia`, *y **se dice** *(-- se crea al primer apunte)* ✓
   *-- *en **destino nuevo y desechable**, *con guardas (nombre, puerto libre, `Up`, base vacia), *
   *y **limpiandose solo** -- *sin tocar **5432, 5433 ni 5434*** ✓✓✓
```

## 4. *** Y lo que salio por el camino, que no estaba en el complemento ***

```
*** EL RESPALDO, QUE NO EXISTIA *** *
  `respaldar.bat` **fallaba siempre**: *buscaba la palabra «running» y **Docker dejo de decirla**;
  *`data\respaldos` **no existia** *(-- la carpeta la crea el guion --); *y **no cubria las dos SQLite**,
  *que el compose dice que **son lo que la casa ha escrito** y que **`robocopy data\raw` no ve**.*
  *** -> ahora respalda las tres cosas que no se regeneran, con `VACUUM INTO` y sello de tiempo*** ✓

*** EL ARRANQUE QUE ADOPTA SU VOLUMEN *** *
  *la API se reconstruyo y **«Recetas» dejo de poder guardar**: *`attempt to write a readonly database`*
  *-- *y **no era el disco**: *el volumen era de `root` y la API corre como `cesta`; *y **la causa de
  fondo** es que *el `chown` de la imagen **no llega al volumen**, que **se monta despues***.*
  *** -> `entrar-api.sh`: adopta `/app/data` como `root` y **baja a `cesta`**; *si el `chown` falla,
  **se para** en vez de seguir como `root*** ✓ *(-- y `uvicorn` corre con `Uid: 10001` --)*

*** Y SIETE FALLOS que los propios instrumentos se encontraron a si mismos *** *
  *el `Created` que no se comprobaba · el `docker rm -f` que se bloquea · el `Up` que no se miraba ·
  la conexion antes de que la base atienda · **una limpieza que se puede saltar** · *la guarda que
  solo estaba escrita* · *y **el umbral que confundia ficha corta con ficha rota*** *
```

## 5. *** Y lo que queda: UNA decision, y es del propietario ***

```
*** ¿LA LISTA **SUMA** O **SUSTITUYE**? *** *
  *Hoy `uuid5(lista_id|clave)` con `ON CONFLICT DO UPDATE` **reemplaza** -- *así que **dos operaciones
  legitimas del mismo producto se pisan.** *
*** y el proyecto **ya respondio que suman**, y lo dejo escrito ***, en el diario: *
  *** «Dos comidas legitimas llevan claves distintas *** y se registran las dos ***» *** *
  *-- *o sea: **la identidad es la OPERACION**, no el producto*
  *-- *y `traspaso` **ya construye su clave como operacion**: *`propietario|receta|version|semana`*
*** -> si la respuesta es «la misma regla», *el cambio es concreto: **meter la operacion en la clave de
  la linea**, *y **la idempotencia sigue intacta** (reintentar **la misma** operacion da el mismo id)* *
```

## 6. Y el estado de la casa

```
*** la ingesta ***  *terminada (`LastTaskResult: 0`), *las **seis fuentes**, *`lidl` con `ok=True`* ✓
*** casa (5432) ***  *** healthy *** · *** facylf (5433) *** *** healthy *** *y sin tocar* ✓
*** la API ***  *** healthy ***, *con el codigo de hoy y **sin privilegios** (`Uid 10001`)* ✓
*** la base de pruebas (5434) ***  *** levantada ***, *y **es `--rm`**: *su comando esta en
  `docs/BACKLOG.md:1909`* ✓
*** y no queda nada mio colgando *** ✓
```
