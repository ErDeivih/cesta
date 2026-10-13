# B03 · **Estado y siguiente paso**: la region esta en la vista, y la comparacion no la mira

*(13 de octubre de 2026. **Se iba a llevar la region a la pantalla, y se para donde hay que parar.**)*

## 1. Lo que hay, medido

```
la vista diario:  [... 'region' ...]   ¿expone region? True
  lidl 77 filas, 77 con region · las otras cinco, 0
```

**Y la API no la usa en ninguna parte:**

```
git grep -n "region" -- plataforma/api/catalogo.py plataforma/api/cesta.py
  -> NINGUNA coincidencia
```

> **Asi que el dato esta en la vista y **ningun endpoint lo mira**.** *Que es, otra vez, la misma forma de
> hueco que este paquete lleva encontrando:* *el `grupo_id` que se nombraba y no se leia, el
> `por_que_no_se_compara` que se probaba y no se llamaba, y ahora la region que se propaga y no se usa.*

## 2. Y el sitio donde importa es **la comparacion**

`plataforma/api/cesta.py:509`, `donde_comprar`, con su consulta en la 176:

```python
filas += con.execute(f"""
    SELECT grupo_id, NULL, fuente, fuente || ':' || id_fuente, nombre,
           precio_cent, precio_unidad_cent, comparacion_fiable, ean, marca
      FROM grupos
     WHERE grupo_id IN (...) AND precio_cent > 0
""", grupos).fetchall()
```

> **Y ahi es donde la region tiene algo que decir**: *un precio de Lidl de Madrid y uno de Alcampo de la
> peninsula **no son comparables sin mas** -- y hoy la comparacion los trata igual, **porque no mira la
> zona**.*
>
> **Y no es un detalle de presentacion**: *comparar zonas distintas y elegir «la mas barata» da un ganador que
> **puede no existir** -- porque ese precio no es de donde compra quien lo lee.*

## 3. Y por que **no** se hace en esta ronda

**La consulta devuelve una tupla posicional**, y **los campos se leen por indice aguas abajo**
(`f[3]`, `f[4]`…). *Anadir `region` al `SELECT` **desplaza todos los indices siguientes** o **exige tocar cada
lectura**.*

**Y eso es una cadena de sitios en la funcion mas central del paquete** -- *la que decide en que tienda
comprar.*

> **Un cambio a medias aqui no rompe una pantalla: rompe la comparacion de precios.** *Y las pruebas del
> paquete cubren `donde_comprar`, pero **no cubririan una lectura de indice desplazada** si el campo que se
> corre es de otro tipo compatible.* *Es exactamente la clase de fallo silencioso que esta fase lleva cazando.*

**Asi que se para aqui, y se deja dicho** -- *que es lo que se hizo con la captura de Alcampo, y por el mismo
motivo: **medir primero, y no empezar lo que no se puede terminar bien.***

## 4. Y el siguiente paso, con su forma exacta

  1. **Anadir `region` a las dos consultas de `donde_comprar`** *-- y **a la vez** arreglar los indices*
     *aguas abajo, o pasarlas a `SELECT` con nombres.*
  2. **Y decidir que hace la comparacion con la zona**, que es la decision de verdad y tiene tres opciones:
     - **comparar solo dentro de la misma zona** *-- y decir cuando no hay con quien comparar;*
     - **comparar y avisar** *-- «este precio es de otra zona»;*
     - **no comparar las que no declaran zona** *-- que hoy serian cinco de seis, y dejaria la comparacion vacia.*
  3. **Y su prueba**: *un caso con dos zonas distintas, y que la respuesta diga **que** hizo y **por que**.*
     *Que es la forma de probar de todo este paquete.*

> **Y la opcion 2.a es la que el plan pide**, leida con cuidado: *«permite comparar precios validos de articulos
> observados **sin presentar ausencias de captura como indisponibilidad**».* **Comparar zonas distintas como si
> fueran la misma es presentar una ausencia -- la de la zona -- como si no importara.**

## 5. Y el estado de B03, entero

```
captura acotada                          HECHO
bronze con la zona acreditada            HECHO (79 de 79 con region)
cobertura por campo y contador visible   HECHO
bronze -> silver -> gold                 HECHO (6 cadenas, historico rehecho)
la vista expone la region                HECHO (77 de 77 en Lidl)
/api/estado como sexta fuente            HECHO (HTTP, con su cobertura)
la pantalla ensena la cobertura          HECHO
Y CORRE EN LA PASADA DIARIA              HECHO (con su tabla de argumentos)
club capturado como condicion            PROBADO
fechas                                   PROBADO
nutricion ausente y dicha                PROBADO
ausencias dichas                         PROBADO
LA ZONA EN LA COMPARACION                PENDIENTE -- con su decision
```

*Y lo que queda de B03 es eso: **una decision sobre como comparar zonas distintas**, y su prueba.*
*Todo lo demas esta hecho, medido y comprobado por HTTP.*
