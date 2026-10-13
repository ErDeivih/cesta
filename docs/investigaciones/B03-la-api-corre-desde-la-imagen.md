# B03 · **La API corre desde la imagen**, no desde el repo -- y eso cambia que significa «probado»

*(13 de octubre de 2026. **Se intentaba ver la cobertura de Lidl en `/api/estado`, y no salia. La causa no
era la ruta: era que el codigo que responde no es el del repositorio.**)*

## 1. Lo medido

```
$ docker exec cesta-api-1 grep -c '_cobertura' /app/plataforma/api/main.py
0

$ docker inspect cesta-api-1 --format '{{range .Mounts}}{{.Source}} => {{.Destination}} ({{.Mode}}){{end}}'
F:\aprendizaje\scrap\data => /datos (ro)
```

> **Cero apariciones de `_cobertura`** -- *que es la funcion que acabo de anadir* --, **y el unico montaje es
> `data`.** *Asi que `plataforma/api/` **no** esta montado: **va dentro de la imagen**, y por eso el
> contenedor ejecuta el codigo de cuando se construyo.*
>
> **Reiniciarlo no cambia el codigo.** *Y por eso la cobertura no salia: **la funcion no estaba dentro.***

## 2. Y esto tiene una consecuencia que va mas alla de esta ronda

**Todo lo que se ha dado por «probado» contra `localhost:8080` en esta sesion hay que revisarlo:**

  - **El cambio del `aviso` en `en_tienda`** (ronda 31) *esta en el repositorio y **pasa las pruebas**, pero
    **no lo sirve el contenedor**.* **Asi que el veto de Lidl, en la API que responde, SIGUE PUESTO.** ✗
  - **Y la cobertura** (esta ronda): *escrita y no servida.*

> **Y esto es exactamente la distincion que el encargo pide no confundir**: *«no consideres terminado lo que
> solo abrio una pantalla vacia».* **Aqui es al reves y es igual de grave: algo que *pasa las pruebas* y *no
> llega al usuario*.** *La suite prueba el codigo del repo; **el usuario habla con la imagen**.*

**Y explica, de paso, algo que se dio por bueno sin serlo**: *en la ronda 35 se atribuyo a la cache que Lidl
apareciera tras reiniciar.* **Eso si era la cache** -- *el gold lo lee en caliente* --, *pero el `aviso` y la
cobertura **no salen por reiniciar: salen por reconstruir**.*

## 3. Lo que hay que hacer, y no es un atajo

**Reconstruir la imagen de la API:**

```
cd plataforma && docker compose build api && docker compose up -d api
```

*Y despues volver a comprobar las tres cosas:*

  1. **que `lidl` sigue apareciendo** *como sexta fuente* -- *eso ya esta.*
  2. **que su `cobertura` sale** *con `ofertas_semanales_parcial` y `con_precio 77 de 79`.*
  3. **y que `en_tienda` admite `lidl`** *de verdad, por HTTP y no solo en las pruebas.*

> **Y esto **no** es una perdida de tiempo: es la diferencia entre «el codigo esta escrito» y «la aplicacion lo
> hace».** *Y las tres se pueden comprobar con una peticion, que es lo que las hace afirmaciones y no
> expectativas.*

## 4. Y lo que queda dicho para el resto del plan

**Cualquier cambio en `plataforma/` necesita reconstruir para llegar al usuario.** *Los cambios en `core/` y en
`projects/` tambien, si el contenedor los importa desde dentro.* **Solo `data/` entra en caliente.**

*Asi que cuando el plan dice «bronze -> silver -> gold -> API -> UI», **el paso de API no se cierra con un
commit**: se cierra con una respuesta HTTP que traiga el dato. Y eso hay que hacerlo **despues de reconstruir**.*
