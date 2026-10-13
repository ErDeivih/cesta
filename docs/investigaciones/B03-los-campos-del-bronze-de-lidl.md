# B03 · **Los campos del bronze de Lidl**, uno por uno -- lo que trae y lo que no

*(13 de octubre de 2026. **La aceptacion de B03 pide probar «region/club/fechas/nutricion/ausencias». Aqui
esta cada uno, medido sobre el bronze de hoy.**)*

## 1. El bronze, y lo que trae

```
data/bronze/fuente=lidl/fecha=2026-10-13/part.parquet     54 columnas, 79 filas
```

### Y las cinco cosas que la aceptacion nombra

| lo que pide | lo que hay | |
|---|---|---|
| **region** | **NO HAY NINGUNA COLUMNA DE REGION** | ✗ *ver abajo* |
| **club** | `promo_club` en **79 de 79**, y su texto | ✓ **y bien** |
| **fechas** | `promo_hasta` en **77**, y `capturado_en` y `fecha` | ✓ |
| **nutricion** | `nutricion` y `nutricion_por` con **0 valores** | ✓ *ausencia dicha, no rellenada* |
| **ausencias** | `precio_cent` en **77 de 79** | ✓ *y los 2 que faltan se ven* |

## 2. El club: **capturado como condicion, que es lo que el colector prometia**

*Su docstring decia: «el precio del club de Lidl se conserva como lo que es: **una condicion, no el precio
general**». Y medido:*

```
  'Naranja mesa'                 promo=True  promo_txt='Precio condicionado a Lidl Plus'  promo_club=True
  'QUALITE SUISSE Pepino granel'  promo=True  promo_txt='Precio condicionado a Lidl Plus'  promo_club=True
  'Pomelo'                        promo=True  promo_txt='Precio condicionado a Lidl Plus'  promo_club=True
```

> **«Precio condicionado a Lidl Plus».** *No es «este es el precio»: es **una condicion que hay que
> cumplir**.* **Y el campo `promo_club` lo dice aparte, asi que quien lea el dato puede decidir si la cumple
> o no** -- *en vez de que la app le ensene un precio que no puede pagar.*

**Y los campos estan separados, que es la mitad del trabajo**: *`precio_cent` (lo que se cobra),
`precio_anterior_nativo_cent` (el tachado, en **39**), `promo`, `promo_txt`, `promo_club`,
`promo_solo_online` (vacio), `promo_unidades_minimas`.* **El tachado no es el precio, y estan en columnas
distintas.**

## 3. La nutricion: **cero, y eso es un dato, no un hueco**

```
nutricion        con valor = 0
nutricion_por    con valor = 0
```

**Lidl no publica nutricion en su campana de ofertas**, *o al menos no en estas 79 fichas.* **Y por eso
`nutricion` va vacia.**

> **Y esto importa para el plan, que dice «no inventes calorias».** *Lidl no aporta calorias a la aplicacion
> **porque no las publica** -- y eso es una limitacion de la fuente, **no un fallo de la captura**.*
>
> **Y la distincion es la de toda esta fase**: *un cero callado se leeria como «estos productos tienen 0
> kcal»; **una columna vacia, con la cobertura al lado, se lee como «no se sabe»**.*

## 4. Y `ean` vacio, que es la promesa del colector, comprobada

```
ean    con valor = 0     de 79
```

*Su docstring:* **«El EAN no se inventa. La ficha trae `ians` e identificadores internos; ninguno es un EAN
comprobado, asi que `ean` va vacio. Un codigo inventado envenena las comparaciones (T03).»**

> **79 de 79 vacios.** *La promesa, medida.* **Y por eso una ficha de Lidl no puede emparejarse con las
> otras cadenas por codigo de barras** -- *que es una limitacion real, y esta dicha en vez de rellenada.*

## 5. Y lo que **falta**, que es una cosa: **la region**

```
columnas con 'region': NINGUNA
```

**La region se uso para RESOLVER el precio** *-- el colector acredito `28` desde el CP y pidio los precios de
esa region* --, **y no se guarda en ninguna columna.**

> **Asi que un precio de Lidl esta en el bronze SIN DECIR DE QUE ZONA ES.** *Y eso es exactamente lo que
> B03 pide demostrar: el **ambito regional**.*
>
> **Y no es un detalle contable**: *la aplicacion puede comparar un precio de Lidl de Madrid con uno de
> Alcampo de la peninsula, **y presentarlos como comparables cuando no lo son** -- que es la misma clase de
> mentira que el `77` sin su cobertura.*
>
> **Lo bueno es que la region SI se conoce**: *esta en `data/cobertura/lidl-2026-10-13.json`, con
> `"region": 28`.* **Lo que falta es que viaje con cada fila** -- *que es lo que hace falta para poder decir,
> por linea, de que zona es el precio.*

## 6. Asi que de B03 queda una cosa concreta, y el resto esta probado

```
captura acotada                          HECHO
bronze con la zona acreditada            HECHO (la zona se acredito: 28, desde el CP)
cobertura por campo y contador visible   HECHO
bronze -> silver -> gold                 HECHO
/api/estado como sexta fuente            HECHO (HTTP)
la pantalla la ensena                    HECHO
Y CORRE EN LA PASADA DIARIA              HECHO
club capturado como condicion            PROBADO (promo_club + «Precio condicionado a Lidl Plus»)
fechas                                   PROBADO (promo_hasta, capturado_en, fecha)
nutricion ausente y dicha                PROBADO (0 valores, y la cobertura lo explica)
ausencias dichas                         PROBADO (77 de 79 con precio)
LA REGION EN CADA FILA                   PENDIENTE, y es lo unico
```

*Y decirlo asi es lo que permite seguir*: **no queda «probar el ambito regional» como una tarea difusa, queda
**una columna** -- y el dato para llenarla ya esta en la cobertura.**
