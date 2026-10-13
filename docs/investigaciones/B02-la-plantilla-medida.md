# B02 · **La plantilla, medida**: cinco lineas, y donde van

*(13 de octubre de 2026. **El ultimo dato que faltaba para que el cambio sea mecanico.**)*

## 1. La plantilla, entera

`projects/cesta/collectors/lidl.py:278-285` -- *cinco lineas, y **donde** van:*

```python
write_parquet(marco, "bronze", FUENTE)
# El fichero de cobertura: lo que la aplicacion tiene que poder ensenar junto al dato.
destino = config.DATA / "cobertura"
destino.mkdir(parents=True, exist_ok=True)
(destino / f"{FUENTE}-{resumen['fecha']}.json").write_text(
    json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"  bronze escrito y cobertura declarada en data/cobertura/{FUENTE}-"
      f"{resumen['fecha']}.json")
```

> **Y fijate en las tres cosas que dicen las cinco lineas:**
>
>   1. **va justo despues de `write_parquet`** *-- o sea, **despues de escribir el bronze**;*
>   2. **esta dentro de la rama de `--escribir`** *-- porque abajo, en el `else`, dice «sin `--escribir`: **no se
>      ha tocado bronze ni la cobertura del dia**». *O sea: **la cobertura no se escribe si no se escribe el
>      bronze** -- que es lo correcto: **no se declara una captura que no se guardo**;*
>   3. **y `resumen` es un `dict` que ya se construye** *-- el colector **lo tiene hecho antes de llegar aqui**,
>      para imprimirlo: `print(f"  ofertas conocidas ({resumen['cobertura']})...")`.*

## 2. Y entonces el cambio en Carrefour y Alcampo es esto

```
1) CONSTRUIR UN `resumen` -- un dict, con los campos del de Lidl que se puedan llenar:
     fuente · cobertura · url · fecha
     fichas_leidas / productos_padre / guardados     <- el bronze los dice
     fuera_de_alcance · en_revision                  <- a 0 si no aplica
     con_precio / precios_con_vigencia_comprobada     <- si aplica
     aviso                                            <- LO IMPORTANTE: que es y que no es
     Y LOS TRES QUE B02 ANADE, QUE LOS DOS YA CUENTAN:
       reintentos / vueltas · bloqueadas · por_que_fallan
     Y EL TIEMPO, que es lo unico que no se mide

2) Y ESCRIBIRLO con las CINCO LINEAS de arriba, en el mismo sitio:
     justo despues de `write_parquet`, y dentro de la rama de escritura.
```

> **Y lo unico que hay que decidir es el campo `cobertura`, que es el que dice QUE ES lo capturado** *-- y que en
> Lidl vale **`ofertas_semanales_parcial`**.* **Para Alcampo y Carrefour seria `catalogo_entero`** -- *porque
> **si** lo cataloga entero, que es lo que `/api/estado` ya dice de los dos.*
>
> *Y ese campo **es el que hace que la app pueda decir «esto es todo» o «esto es parte»** -- que es el problema
> que B03 resolvio para Lidl y que estos dos no tienen, **porque si cataloga entero**.*

## 3. Y con esto B02 no tiene ninguna incognita, y se puede escribir

```
LA FORMA:      las cinco lineas de lidl.py:278-285
EL SITIO:      justo despues de write_parquet, dentro de la rama de escritura
LOS CAMPOS:    los trece de Lidl, mas reintentos/bloqueadas/por_que_fallan, mas el tiempo
EL VALOR CLAVE: `cobertura` = "catalogo_entero" para los dos
Y LO QUE FALTA: los FIXTURES, y la decision del navegador (que es del propietario)
```

*O sea: **el trabajo de B02 es rellenar un `dict` y escribir cinco lineas en dos ficheros.*** *Y eso se sabe
**porque se leyo**, no porque se supusiera.*

## 4. Y el resumen honesto de estas nueve rondas

**Nueve rondas, ninguna linea de codigo, y cinco correcciones de mis propias conclusiones.** *Y al final el
trabajo es: **un `dict` y cinco lineas en dos sitios**.*

> *Eso no hace buenas a las nueve rondas.* *Hace **buena a la ultima** -- y **malas a las cinco primeras**, que
> dijeron «no existe nada», «hay que construirlo» y «falta la distincion».*
>
> **Y lo que las separa no es el esfuerzo: es que las ultimas cuatro miraron y las primeras seis buscaron.**
> *Que es todo lo que hay que aprender de B02.*
