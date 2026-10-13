# B03 · **Lidl ya corre en la pasada diaria.** Una tabla, y la prueba de que hace falta

*(13 de octubre de 2026. **El cambio es de tres lineas, y la prueba de que sirve es una salida comparada.**)*

## 1. El cambio

*En `projects/cesta/run.py`, al lado de `ORDEN`:*

```python
# **Los que tienen CLI propia, y con que argumentos se les llama en la pasada diaria.**
ARGUMENTOS: dict[str, list[str]] = {"lidl": ["--web", "--escribir"]}
```

*Y en la llamada:*

```python
bien = mod.main(ARGUMENTOS[nombre]) == 0 if nombre in ARGUMENTOS else mod.main() == 0
```

### Y **solo se le pasan a quien los espera**, que es la mitad del asunto

*Las firmas de los seis, leidas:*

```
carrefour   def main() -> int                                  <- sin argumentos
aldi        def main() -> int                                  <- sin argumentos
alcampo     def main() -> int                                  <- sin argumentos
dia         def main(detalles_max: int | None = None) -> int
mercadona   def main(detalles_max: int | None = None) -> int
lidl        def main(argv: list[str] | None = None) -> int     <- argv
```

> **Llamar `main(args)` a los seis habria roto tres.** *`carrefour`, `aldi` y `alcampo` no aceptan
> argumentos.* **De ahi que sea una tabla de los que la tienen, y no un cambio en la llamada.** *Que es la
> diferencia entre tocar un colector y tocar la ingesta de la casa.*

## 2. Y la prueba de que la tabla hace falta: dos salidas, comparadas

```
--- SIN la tabla: lo que hacia run.py antes ---
  SystemExit(2)          <- «one of the arguments --html --web is required»
  Y ESTO ES LO QUE RECOGIA EL except, dejando el dia sin Lidl

--- CON la tabla: lo que hace run.py ahora ---
  region acreditada por nombre: CP 28001 -> «Madrid» (region 28)
  ofertas conocidas de Lidl (ofertas_semanales_parcial): 79 guardadas de 79 fichas leidas,
                                                         0 fuera de alcance, 0 en revision
  devolvio 0             <- el colector CORRE
```

> **`SystemExit(2)` contra `0`.** *No es una descripcion de lo que deberia pasar: son las dos salidas, medidas,
> de la misma llamada con y sin la tabla.* **Y la de arriba es la que llevaba pasando cada dia desde que Lidl
> entro en `ORDEN`.**

## 3. Y `--region` no va en la tabla, a proposito

**`--region` no se le pasa, y no es un olvido**: *el colector **la acredita desde `config.CODIGO_POSTAL`***
-- *que es lo que se arreglo en la ronda 25* -- **y si no la puede acreditar, sale con 1 y su motivo.**

**Y entonces la precaucion de `run.py` es la correcta**: *se avisa, el dia sigue, y las otras cinco se
publican.* **La prueba esta en la ronda 25**: *con `SCRAP_CP=38001` (Tenerife) el colector dijo
`region_desconocida`, explico por que, y **salio con 1 sin escribir**.*

> **O sea que el `except SystemExit` que hoy deja a Lidl fuera **sigue siendo necesario***: *ahora es la red
> para un caso que se dice, no el agujero por el que se cae siempre.*

## 4. Y el orden que el colector pedia, respetado

*Su docstring decia:*

> *«No esta en la tarea de las 06:00, a proposito. La ampliacion lo pide asi: **"pasar una captura acotada
> antes de anadirlo a la tarea diaria"**.»*

**Y ese orden se ha seguido, en este orden:**

```
la captura acotada                       HECHA (ronda 22: 79 fichas, las 79 con precio regional)
el bronze publicado con su zona          HECHO (ronda 26)
el recorrido hasta la pantalla           COMPROBADO (rondas 33-38)
y AHORA el horario                       HECHO (esta ronda)
```

> **Y no al reves.** *Meterlo en las 06:00 antes de saber que captura y que escribe habria metido un
> desconocido en el camino diario.*

## 5. Y lo que queda de B03

```
captura acotada                          HECHO
bronze con la zona acreditada            HECHO
cobertura por campo y contador visible   HECHO
bronze -> silver -> gold                 HECHO
/api/estado como sexta fuente            HECHO (HTTP)
la pantalla la ensena                    HECHO
Y CORRE EN LA PASADA DIARIA              HECHO (esta ronda)
```

  - **region/club/fechas/nutricion/ausencias probadas EN EL RECORRIDO** *-- el bronze trae la region y las
    condiciones; falta comprobar que llegan hasta la pantalla.*
  - **y Alcampo**, cuya zona sigue clavada en «peninsula».

*Y una cosa que conviene decir: **la proxima pasada de las 06:00 es la prueba de verdad**.* *Lo que hay medido
es que el colector corre con esos argumentos y devuelve 0; que la tarea lo lance a su hora es lo que
confirmara que el ciclo entero esta cerrado.*
