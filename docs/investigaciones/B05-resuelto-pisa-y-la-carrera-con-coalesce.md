# B05 · **Resuelto: `PISA`** -- y la carrera de los dos moviles esta resuelta con `COALESCE`

*(13 de octubre de 2026. **Novena ronda de B05. Y cierra la ultima pregunta abierta.**)*

## 1. `anade_linea`, literal (`almacen.py:368`)

```python
def anade_linea(lista_id, usuario_id, linea_id, nombre, grupo_id=None, producto_id=None,
                cantidad=1, nota=None, cadena_elegida=None) -> dict:
    """El id lo trae el movil. Si llega dos veces, NO SE DUPLICA: SE ACTUALIZA.

    La tienda elegida se actualiza con `COALESCE`: subir otra vez una linea que se
    anadio sin tienda **no puede borrar** la tienda que se eligio despues en otro
    movil. Y al reves si funciona: ponerla es ponerla.
    """
    with cursor() as cur:
        cur.execute("""
            INSERT INTO lista_linea (id, lista_id, grupo_id, producto_id, nombre_visto,
                                     cantidad, nota, anadido_por, cadena_elegida)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
               SET cantidad = EXCLUDED.cantidad, nota = EXCLUDED.nota,
                   cadena_elegida = COALESCE(EXCLUDED.cadena_elegida,
                                             lista_linea.cadena_elegida),
                   borrado_en = NULL, tocado_en = now()
            RETURNING id, grupo_id, producto_id, nombre_visto, cantidad, nota, cadena_elegida
        """, (...))
        return dict(cur.fetchone(), id=linea_id)
```

## 2. Y las tres preguntas de la ronda 136 quedan contestadas

```
¿PISA, IGNORA O LEVANTA?   ->  *** PISA. ***  `ON CONFLICT (id) DO UPDATE`.
                               No ignora (no dice «ya estaba») ni levanta (no da error).
                               *** Y PISA CON EL CONTENIDO NUEVO: `cantidad` y `nota` se sobrescriben. ***

¿Y LA CARRERA DE DOS MOVILES?  ->  *** RESUELTA, Y ESTA ESCRITA EN EL DOCSTRING: ***
                               «subir otra vez una linea que se anadio sin tienda NO PUEDE BORRAR la
                               tienda que se eligio despues en otro movil».
                               *** Y se resuelve con `COALESCE(EXCLUDED.cadena_elegida,
                               lista_linea.cadena_elegida)`: si lo que llega es NULL, SE QUEDA LO QUE HABIA. ***

¿Y SI LA LINEA ESTABA BORRADA?  ->  `borrado_en = NULL`. *** Volver a subirla la RESUCITA. ***
                                    *Que es «deshacer» -- y el DDL lo pedia con sus dos razones.*
```

## 3. Y `COALESCE` es la pieza que hay que subrayar

**`cadena_elegida = COALESCE(EXCLUDED.cadena_elegida, lista_linea.cadena_elegida)`** *-- y el docstring dice **por
que**, y **dice los dos sentidos**:*

>   - *«subir otra vez una linea que **se anadio sin tienda** no puede **borrar** la tienda que se eligio despues
>     en otro movil»* -- *si llega `NULL`, **se queda lo que habia**;*
>   - *«**y al reves si funciona: ponerla es ponerla**»* -- *si llega una tienda, **se pone**.*

> *** O sea: ***
>
>   - **`cantidad` y `nota` se SOBRESCRIBEN** *-- porque son **el contenido de la operacion que se repite**;*
>   - **`cadena_elegida` se PRESERVA si no llega** *-- porque **es una decision posterior, de otra persona y otro
>     movil**, que **la operacion que se repite no tiene por que conocer**.*
>
> *** Y esa distincion -- **que se pisa y que se conserva** -- es exactamente la clase de decision que hay que
> razonar, y esta razonada en el docstring con los dos casos. ***
>
> *Que es **la misma doctrina del `NULL` de la despensa**: «no llega» y «llega vacio» son **dos cosas distintas**,
> y **por eso hace falta `COALESCE` y no un `SET` a pelo**.*
>
> *** Y es la cuarta vez en esta sesion que el proyecto resuelve un caso dificil distinguiendo «no se sabe» de
> «es cero». ***

## 4. Y B05 queda **leido entero**, y sin preguntas abiertas

```
  1) RECIBO Y HUELLA               HECHO -- Operacion + clave() + id_de_linea()   + 8 ensayos (g12)
  2) CONFLICTO, NO EXITO FICTICIO  HECHO -- `id uuid PRIMARY KEY` + `ON CONFLICT ... DO UPDATE`
  3) CONCURRENCIA Y MEDIA LISTA    HECHO -- `borrado_en` (el DDL) + `COALESCE` (la carrera, en el docstring)
  4) RESERVAS DE DESPENSA          HECHO -- `017_la_despensa.sql`, la regla EN EL DDL  + 9 ensayos (f11)
  5) CALCULO INCREMENTAL DEL PLAN  HECHO -- la previa y quitar del plan               + 11 ensayos
  6) DESTINO DISTINTO              HECHO -- B04 (`014_la_linea_sin_destino.sql`)
```

> *** Y las tres preguntas que quedaban en el aire estan contestadas con el codigo delante: ***
> **pisa**, **y con el contenido nuevo**, **y la carrera se resuelve con `COALESCE`**, **y una linea borrada
> resucita**.
>
> *Nueve rondas, y **B05 pasa de «leido» a «comprobado en los sitios donde se decide»** -- *sin haber escrito una
> linea, y **sin una sola afirmacion que no se pueda ir a ver**.*
