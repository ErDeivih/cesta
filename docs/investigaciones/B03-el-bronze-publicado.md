# B03 · **El bronze de Lidl, publicado.** Con la zona acreditada y la cobertura declarada

*(13 de octubre de 2026. **El paso que el colector pedia antes de entrar en las 06:00, y que ya esta
hecho.**)*

## 1. Se comprobo que nadie estaba trabajando, y despues se escribio

*La tarea `Cesta diaria` estaba en `Ready` y el `runlock` libre.* **Y eso importa**, porque el propio colector
avisa de lo que escribir significa:

> *«**Escribir es una decision, no un descuido.** La pasada diaria descubre las cadenas, asi que **un bronze
> de Lidl la haria lanzar este colector sola**, con cobertura parcial.»*

**O sea: escribir el bronze es la segunda mitad del punto 189 de G09.** *Lidl pasa de «esta en `ORDEN`» a
«la pasada diaria lo ejecuta».*

## 2. Y salio, con la region acreditada

```
$ uv run python -m collectors.lidl --web --escribir
  region acreditada por nombre: CP 28001 -> «Madrid» (region 28)
  ofertas conocidas de Lidl (ofertas_semanales_parcial): 79 guardadas de 79 fichas leidas,
                                                         0 fuera de alcance, 0 en revision
  bronze escrito y cobertura declarada en data/cobertura/lidl-2026-10-13.json
  exit: 0
```

*Y escribio cuatro cosas:*

```
data/bronze/fuente=lidl/fecha=2026-10-13/part.parquet     23,8 KB   <- EL BRONZE
data/cobertura/lidl-2026-10-13.json                        0,5 KB   <- lo que la UI tiene que ensenar
data/peticiones/lidl-2026-10-13.json                                <- el contador
data/raw/fuente=lidl/fecha=2026-10-13/....json.gz          94,2 KB  <- el crudo
```

## 3. Y la cobertura, que es la pieza que hace que esto no mienta

```json
{
  "fuente": "lidl",
  "cobertura": "ofertas_semanales_parcial",
  "url": "https://www.lidl.es/c/ofertas-semanales/a10089449",
  "region": 28,
  "fecha": "2026-10-13",
  "fichas_leidas": 79,  "productos_padre": 74,  "guardados": 79,
  "fuera_de_alcance": 0,  "en_revision": 0,
  "con_precio": 77,
  "precios_con_vigencia_comprobada": true,
  "aviso": "ofertas conocidas de Lidl, no su catalogo completo: no certifica stock, ni identidad de
             producto, ni que un producto ausente se haya retirado"
}
```

**Y ahi estan, uno por uno, los cuatro campos que la aceptacion de B03 pide:**

  - **`region: 28`** -- *el ambito regional, **dicho en el fichero**.* *No hay que suponerlo: se lee.*
  - **`fichas_leidas`, `guardados`, `fuera_de_alcance`, `en_revision`** -- *la cobertura por campo y el
    contador visible.*
  - **`con_precio: 77` de 79** -- **dos fichas sin precio, y se ven.** *Un 77/79 dicho es un dato; un
    «79 guardadas» sin el 77 seria una promesa.*
  - **`precios_con_vigencia_comprobada: true`** -- *que es lo que el colector exige para publicar* (linea 236:
    *«no se publica: no hay precios regionales con vigencia comprobada»*).
  - **y el `aviso`** -- *«no certifica stock, ni identidad, ni que un producto ausente se haya retirado»*:
    **las tres cosas que B03 pide marcar como desconocidas en vez de ausentes.**

## 4. Y lo que esto cierra, y lo que abre

**Cerrado:**

  - **la captura acotada** -- *hecha, y ahora escrita.*
  - **el ambito regional** -- *acreditado por nombre desde `config.CODIGO_POSTAL`, y escrito en la
    cobertura.*
  - **la cobertura por campo y el contador** -- *escritos.*
  - **el veto global** -- *Lidl ya no esta vetado: tiene bronze de hoy.*
  - **y la segunda mitad del punto 189** -- *el bronze hace que la pasada diaria lo ejecute sola.*

**Abierto:**

  - **bronze -> silver -> gold -> API -> UI**: *el bronze existe; el recorrido hasta la pantalla, no.*
  - **region/club/fechas/nutricion/ausencias probadas** *en el recorrido, no solo en el bronze.*
  - **la comparacion**: *«permitir candidatos observados, vigentes y de identidad acreditada»* -- *y para eso
    el silver tiene que llevarlo.*
  - **y la pregunta del propietario**: *si Carrefour, DIA y Alcampo publican precio por zona.*

## 5. Y una cosa que se ha visto y conviene decir

*Hay un `data/lidl-sitemap.xml` en el proyecto.* **Y el plan avisa por su nombre**: *«no lo declares completo
por tener un sitemap»*. **Un sitemap es un indice de rutas, no un catalogo con precios.** *Lo que hay hoy es
**79 fichas con precio, region y fecha**, que es otra cosa -- y es la que cuenta.*
