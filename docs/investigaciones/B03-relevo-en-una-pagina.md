# B03 · **Relevo de B03 en una pagina** -- lo que esta hecho, lo que queda, y por donde empezar

*(13 de octubre de 2026. **Escrito para que quien continue no tenga que leer 47 documentos.** El detalle esta en
`docs/SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md`, entrada de B03.)*

## 1. Lo que esta HECHO y comprobado

```
captura acotada de Lidl              79 fichas, 74 productos padre
bronze                              region 79 de 79 · + cobertura y contador por campo
silver                              region 79 de 79
gold (precio_diario.parquet)        region 77 de 77, HISTORICO REHECHO (38 dias)
la vista diario                     region 77 de 77
/api/estado                         Lidl como sexta fuente, con su cobertura
la pantalla (Cabecera.tsx)          ensena la cobertura
Y CORRE EN LA PASADA DIARIA         run.py, con su tabla de argumentos
club de Lidl                        capturado como condicion, no como precio
fechas de vigencia                  probadas
nutricion ausente                   dicha, no inventada
ausencias                           dichas, no presentadas como indisponibilidad
```

**Y el ambito regional, medido en cada parada** -- *Web -> bronze -> silver -> gold -> vista -> API* --, no
«acreditado en el colector».

## 2. Lo que queda, y son DOS cosas

```
(1) QUE `donde_comprar` HAGA ALGO CON LA ZONA CUANDO LA RECIBA.
    -> Decision escrita (ronda 63): comparar solo dentro de la misma zona, y decir cuando no hay
       con quien. Opcion alternativa: comparar avisando.
    -> Estado: `donde_comprar` YA LA PIDE (`f952c80`), y solo si existe. No hace nada con ella.

(2) QUE `grupos.parquet` TRAIGA `region`.
    -> El emparejador ya la escribe (`27756cd`, `7f0b72d`). El fichero PUBLICADO es de antes.
    -> Se consigue rehaciendo el emparejamiento; y entonces (1) se activa solo.
```

**Y NO HAY QUE TOCAR la guarda del emparejamiento.** *Se quedo como estaba, y es lo correcto.*

## 3. Y lo que hay que saber ANTES de tocar la zona, que es lo que costo cuarenta rondas

**Tres cosas que se dieron por hechas y eran falsas. Las tres, midiendo:**

> **a) La condicion de la zona NO hace falta.** *La invariante de la cadena **ya separa** los dos precios de un
> mismo producto en dos zonas -- porque son dos productos de la misma cadena. Probado:
> `tests/test_b03_la_zona_separa.py`, y **la prueba pasa sin ninguna condicion nueva**.*
>
> **b) La direccion NO es «anadir una condicion», y menos «relajar la que hay».** *Relajarla fue el error de las
> rondas 83-89, y se revirtio (`0206c2a`): con la invariante relajada, **dos zonas del mismo producto se
> JUNTABAN** -- lo contrario de lo que B03 quiere.*
>
> **c) El sitio NO era `donde_comprar`.** *Ni la guarda, ni `_asignacion_1a1`. **Son SIETE sitios**, y el que
> impone la regla -- **`ocupados`, en `emitir`** -- no estaba en ninguno de los tres planes.*

## 4. Por donde empezar, si se retoma (1)

**Lo unico que falta es una decision de presentacion, no de emparejamiento:**

  *`grupos` ya tiene los precios agrupados por la invariante de la cadena. Cuando `grupos.parquet` traiga
  `region`, cada fila sabra de que zona es.*

  **Y entonces `donde_comprar` tiene que decidir UNA cosa:** *si dos precios de zonas distintas pueden competir
  por el mismo puesto, o no.*

  **La decision esta escrita desde la ronda 63, con la respuesta del propietario delante** -- *«que dependa de la
  region que elija el usuario»* --, **y dice: que el precio que se elija sea de la zona del usuario, y que se
  diga cuando no haya con quien comparar.**

## 5. Y las puertas, que estan verdes

```
ruff check .        limpio
pytest -q           2025 pasan, 0 fallan, 0 se saltan
npm test            74 pasan, 0 fallan
npx tsc --noEmit    exit 0
```

*Y los ficheros del propietario, sin tocar: `core/datos/secciones.yml`, `docs/CIFRAS.md`,
`docs/SUPERAPP-EJECUCION.md`, `docs/SUPERAPP-ESTADO.md`, `docs/SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`.*
*Y `docs/SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md` se actualiza pero **no se commitea**: es suyo.*
