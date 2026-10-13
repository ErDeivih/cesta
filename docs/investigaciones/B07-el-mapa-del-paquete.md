# B07 · **El mapa del paquete** -- el criterio, y donde mirar

*(13 de octubre de 2026. **Lo siguiente por el plan. Con el metodo que ya ha funcionado dos veces.**)*

## 1. El criterio, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:283`:

> **B07 · Recetas: contenido, versiones y cocina**
>
> *Editor con **cantidades/unidades, raciones, pasos, tiempos, etiquetas, foto propia, fuente y vinculos de
> articulo**. **Importacion manual/archivo con preview**; **URL solo fuentes revisadas, guardas
> SSRF/redirecciones/tamano/timeout y atribucion**. **Plan con varias comidas por dia, repetir/duplicar semana y
> raciones por ocurrencia**. **Cocina recuperable, pasos/temporizadores y preparado/pendiente, SIN declarar
> consumo**. **Aceptar cinco recetas con datos, edicion, version, importacion permitida, cocina, recarga y cambios
> de semana**; **no cerrar por entrar a cinco rutas vacias**.*

## 2. Y desglosado, son seis cosas -- y la ultima es la aceptacion

```
1) EL EDITOR DE RECETA            -- cantidades/unidades · raciones · pasos · tiempos · etiquetas
                                     · foto PROPIA · fuente · vinculos de articulo
2) LA IMPORTACION                 -- manual / archivo, CON PREVIEW
                                     *** y por URL: SOLO FUENTES REVISADAS, con guardas
                                     SSRF / redirecciones / tamano / timeout, Y ATRIBUCION ***
3) EL PLAN                        -- varias comidas por dia · repetir/duplicar semana
                                     · raciones POR OCURRENCIA
4) LA COCINA                      -- recuperable · pasos y temporizadores · preparado/pendiente
                                     *** «SIN DECLARAR CONSUMO» ***
5) Y LA VERSION                    -- (esta en el titulo: «contenido, VERSIONES y cocina»)
6) Y LA ACEPTACION                -- *** CINCO RECETAS CON DATOS, edicion, version, importacion
                                     permitida, cocina, recarga y cambios de semana ***
                                     *** y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS ***
```

> *** Y hay dos frases que el plan subraya, y las dos son de la misma familia que lo ya leido: ***
>
>   - *** «SIN DECLARAR CONSUMO» *** *-- *que es **la restriccion del propietario** («compra no es consumo») **y
>     ahora aplicada a la cocina**: **cocinar no es comer**.* *Y ya se vio, en B05, que `core/diario.py` «rechaza
>     `compra` a proposito» -- *asi que **es de esperar que `cocina.py` haga lo mismo con la receta**.*
>   - *** «NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS» *** *-- *que es **literalmente la instruccion del
>     propietario**: «**no consideres terminado lo que solo abrio una pantalla vacia**».* *** Y el plan la pone
>     como **condicion de aceptacion del paquete**: **las cinco recetas tienen que tener DATOS**.* ***

## 3. Y donde mirar, medido

```
$ git grep -ln "receta|cocina|raciones" -- core/

  core/alcance.py     core/atributos.py    core/cocina.py        core/datos/alcance.yml
  core/datos/secciones.yml                 core/despensa.py      core/diario.py
  core/gasto.py       core/importar_receta.py                    core/normalize.py
```

> **Y hay dos nombres que prometen, y son el sitio por donde empezar:**
>
>   - **`core/cocina.py`** *-- *el titulo del paquete acaba en **«y cocina»**, y **ahi esta el fichero**;*
>   - **`core/importar_receta.py`** *-- *y la importacion es **la clausula con mas guardas** (SSRF, redirecciones,
>     tamano, timeout, atribucion), **y tiene su modulo**.*
>
> *** Y `core/despensa.py` esta en la lista y ya se leyo su tabla (B05), asi que sirve de contraste. ***
>
> *** Y nada mas se dice: no se ha abierto ninguno. ***

## 4. Y el orden de trabajo, el de B05 y B06

```
  1) ls de la zona                          (hecho: los diez ficheros)
  2) LEER el fichero que el titulo nombra:  *** `core/cocina.py` ***
     -- «...y cocina» es el final del titulo, y `cocina` es su nombre
  3) LOS NOMBRES DE LOS ENSAYOS             -- `git grep -l "receta\|cocina" tests/`
  4) COMPARAR los que hacen lo mismo         -- y aqui hay algo que comparar: `despensa.py` y `cocina.py`
                                                son hermanos (los dos son «lo que hay / lo que se hace»)
  5) y grep al final, con las palabras del codigo

  Y NO DECIR NUNCA: «no existe», «y nada mas», «hay que construirlo», «ya esta» sin su cita
```

> *** Y el paso (4) es nuevo y prometedor: *** *`core/despensa.py` y `core/cocina.py` **suenan a la misma
> familia** -- *«lo que hay en casa» y «lo que se esta haciendo» --* **y compararlos es lo que encontro que Lidl
> era el unico de los seis sin `log_run`.***
>
> *** Y el paso (3) es el que mas informa: los nombres de los ensayos son la documentacion que no miente. ***
